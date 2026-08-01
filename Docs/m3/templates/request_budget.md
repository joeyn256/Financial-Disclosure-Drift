# TEMPLATE — Milestone 3 Request Budget

**This file is a blank template. It records no approved budget and no live run.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to state, route by route, exactly how many requests a network-capable phase intends to
place, how many it could physically place in the worst case, what it will store, how long it will
take, and the exact integer above which it must stop — and to carry the owner's explicit approval of
those numbers.
**Phase:** M3.1B (constructed) → M3.2 (executed under it)
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§§15–16; [Decision 013](../../Decisions/decision_013_pilot_selection_mechanics.md) §1;
[Decision 007](../../Decisions/decision_007_sec_universe.md);
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) §15.
**Completion token contribution:** a signed budget is a Gate F exit condition for
`M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`.

---

## 0. Handling

- **Non-secret document.** It contains counts, route names, and hashes only.
- **Never record** the SEC identity, any credential, any absolute personal path, or any response body.
- **No invented integers.** Every count is produced by the zero-request planning command or written
  `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`.
- **Immutable once signed.** A change requires a new dated copy and a new approval.

## 1. Identification

| Field | Value |
|---|---|
| Budget document version | `_______` |
| Phase | `_______` |
| Owner | `_______` |
| Date prepared (UTC) | `_______` |
| Prepared by (session / model / effort) | `_______` |
| Repository baseline commit | `_______` |
| Baseline tag | `_______` |
| Governing contract | `_______` |
| **Request-plan hash (`request_plan_sha256`)** | `_______` |
| Second dry-run plan hash (must be identical) | `_______` |
| Plan file (relative path) | `_______` |

## 2. Plan inputs — every value explicit, nothing from the clock

| Input | Value |
|---|---|
| `coverage_start` | `_______` |
| `coverage_end` | `_______` |
| `as_of_date` | `_______` |
| `include_open_quarter` | `_______` |
| `--calendar-year` | `_______` |
| Calendar-evidence manifest version | `_______` |
| Calendar-evidence entry count | `_______` |
| Reconciliation set (for `sec_submissions_entity`) | `_______` |
| `requests_per_second` | `_______` |
| `burst` | `_______` |
| `max_transient_retries` | `_______` |
| `MAX_REDIRECT_DEPTH` | `_______` |
| Source registry version | `_______` |
| Already-satisfied instances in the catalog (cache hits) | `_______` |

## 3. Route-by-route planned count

One row per registered route. **Every route appears, including routes planning zero.**

| `source_id` | Host | Planned unique logical requests | Max physical attempts | Expected raw objects | Basis |
|---|---|---:|---:|---:|---|
| `sec_bulk_submissions` | `www.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_company_tickers_exchange` | `www.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_company_tickers` | `www.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_sic_code_list` | `www.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_edgar_filing_calendar` | `www.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_edgar_calendar_announcement` | `www.sec.gov` / `data.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_full_index_company` | `www.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_submissions_historical` | `data.sec.gov` | `____` | `____` | `____` | `_______` |
| `sec_submissions_entity` | `data.sec.gov` | `____` | `____` | `____` | `_______` |
| **TOTAL** | | `____` | `____` | `____` | |

**Any cell still reading `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` blocks approval.**
The dry run resolves it, or the budget is not ready.

## 4. The eight budget quantities

| Quantity | Value | Derivation |
|---|---:|---|
| Planned unique logical requests | `____` | `Σ U(route)` from §3 |
| Maximum physical attempts | `____` | `planned × A_max`, `A_max = 1 + MAX_REDIRECT_DEPTH + max_transient_retries + 1` |
| Expected successful responses | `____` | logical requests expected to classify `proceed` |
| Expected cache hits | `____` | instances already satisfied and therefore **not** planned |
| Expected not-modified responses | `____` | conditional re-validations expected to return `304` |
| Expected governed non-success responses | `____` | expected `retry` + `retry_after` + `cooldown` + `fail` + `quarantine` |
| Maximum raw objects | `____` | planned − not-modified − cache hits − duplicate bodies |
| Maximum elapsed acquisition window | `____` | limiter floor `(attempts − 1) ÷ requests_per_second`, plus the stated transfer component |

**`A_max` used:** `____`  **Value of `MAX_REDIRECT_DEPTH`:** `____`
**Value of `max_transient_retries`:** `____`

## 5. Retry allowance

| Field | Value |
|---|---|
| Maximum transient retries per logical request | `____` |
| Backoff base (seconds) | `____` |
| Backoff ceiling (seconds) | `____` |
| Cooldown duration (seconds) | `____` |
| Controlled post-cooldown requests permitted | `____` (accepted value: 1) |
| Maximum cooldowns before terminal | `____` (accepted value: 1) |

## 6. Contingency

| Field | Value |
|---|---|
| Contingency rate | `____` |
| Contingency, in physical attempts | `____` |
| **Exactly what the contingency covers** | `_______` |
| **What it does not cover** | everything else. It is not general slack |

## 7. Hard request ceiling

```
HARD_REQUEST_CEILING = ceil( (1 + contingency_rate) × maximum_physical_attempts )
```

| Field | Value |
|---|---|
| Computed ceiling | `____` |
| **Approved ceiling (exact integer)** | `____` |
| Ceiling behaviour | The run **refuses the attempt that would exceed** this value |
| May the ceiling be raised mid-run? | **No.** Raising it requires stopping, re-planning, and a new approval |

## 8. Expected elapsed acquisition window

| Field | Value |
|---|---|
| Limiter-imposed floor (seconds) | `____` |
| Stated transfer component (seconds) | `____` |
| Basis for the transfer component | `_______` |
| Total expected window | `____` |
| Window on one cooldown | `____` (add the cooldown duration) |

## 9. Pass/fail

| Check | Result | Note |
|---|---|---|
| Every route listed, including zero-count routes | `PASS` / `FAIL` | `_______` |
| No cell reads `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` | `PASS` / `FAIL` | `_______` |
| No count is a guess; each has a stated basis | `PASS` / `FAIL` | `_______` |
| Max physical attempts equals `planned × A_max` | `PASS` / `FAIL` | `_______` |
| Two dry runs produced identical plan hashes | `PASS` / `FAIL` | `_______` |
| Ceiling computed from the stated formula | `PASS` / `FAIL` | `_______` |
| No secret, identity, or personal path in this document | `PASS` / `FAIL` | `_______` |

## 10. Blockers

| # | Blocker | Severity | Resolution required | Resolved |
|---|---|---|---|---|
| 1 | `_______` | `_______` | `_______` | `_______` |

**Any unresolved blocker prevents approval.**

## 11. Owner approval

> I approve, for the phase and repository baseline named in §1, exactly these two integers:
>
> **Planned unique logical requests:** `____`
> **Hard request ceiling:** `____`
>
> This approval applies to this exact budget document and this exact request-plan hash. It does not
> transfer to a re-planned budget, a changed coverage window, a changed as-of date, or a different
> plan hash. **Network enablement is authorized only for the command named in the governing
> contract, and only under these numbers.**

| Field | Value |
|---|---|
| Owner name | `_______` |
| Date (UTC) | `_______` |
| Decision | `APPROVED` / `REJECTED` |
| If rejected, reason | `_______` |
| Signature or recorded acceptance reference | `_______` |
