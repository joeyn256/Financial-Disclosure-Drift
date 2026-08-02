# TEMPLATE — Milestone 3 Request Budget

**This file is a blank template. It records no approved budget and no live run.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to state, route by route, exactly how many requests **one acquisition window** intends
to place, how many it could physically place in the worst case, the maximum it could newly store,
the rate-limiter spacing floor and elapsed-time factors, and the exact integer above which it must
stop — and to carry the owner's explicit approval of those numbers.

**One budget per window.** The **M3.2A** budget is constructed at M3.1B and approved at Gate F. The
**M3.2B** budget is derived **after** M3.2A freezes its bootstrap objects, and is approved separately.
**Neither approval covers the other window.**
**Phase:** M3.1B → M3.2A · then between the windows → M3.2B
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§§15–16, as narrowly corrected by
[Decision 028](../../Decisions/decision_028_m3_1_readiness_corrections.md) §§7, 10
(**accepted — owner approved 2026-08-01**), and further by
[Decision 029](../../Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md) §§7–8
(**accepted — owner approved 2026-08-02**), which is controlling for the per-route `A_reachable`
witness and for the corrected full-index count;
[Decision 013](../../Decisions/decision_013_pilot_selection_mechanics.md) §1;
[Decision 007](../../Decisions/decision_007_sec_universe.md);
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) §15.
**Completion token contribution:** a signed budget is a Gate F exit condition for
`M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`.

---

## 0. Handling

- **The completed copy is PRIVATE evidence.** It lives in the owner-controlled private evidence root,
  never in the repository. Only its type, phase, status, SHA-256, and reference identifier go into
  [`evidence_index.md`](evidence_index.md).
- **Non-secret content even so.** It contains counts, route names, and hashes only.
- **Never record** the SEC identity, any credential, any absolute personal path, or any response body.
- **No invented integers.** Every count is produced by the zero-request planning command or written
  `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`.
- **Immutable once signed.** A change requires a new dated copy and a new approval.

## 1. Identification

| Field | Value |
|---|---|
| Budget document version | `_______` |
| **Acquisition window** | `M3.2A` / `M3.2B` — **exactly one** |
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
| Index-plan policy version | `_______` (M3.1 implementation: `quarterly-index-instances/2.0`) |
| Request-plan schema version | `_______` |
| Already-satisfied instances in the catalog (cache hits) | `_______` |

## 3. Route-by-route planned count

One row per registered route. **Every route appears, including routes planning zero.**

| `source_id` | Host | Planned unique logical requests | Max physical attempts | Max new raw objects | Basis |
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

**Rows belonging to the other window read `n/a — other window`, not `0`.** M3.2A budgets the seven
bootstrap routes; M3.2B budgets `sec_submissions_historical` and `sec_submissions_entity` only.

**A route planning zero still gets a filled row, not an omitted one, and still needs its
independently tested `A_reachable` in §4.1** (Decision 029 §4.1). An explicitly empty approved
operator calendar-evidence manifest lawfully yields
`U(sec_edgar_calendar_announcement) = 0`; a **missing or unconfirmed** manifest leaves `U` undefined,
which is not zero and blocks approval.

**The `sec_full_index_company` count is the count after catalog-satisfied exclusion**
(Decision 029 §8): `q = |required_index_keys − already_satisfied_index_keys|`, **not** the bare
`|required_closed_quarters(coverage, as_of, include_open_quarter)|`. Record both, and record which
one the plan used.

**Any cell still reading `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` blocks approval.** For
M3.2A the zero-request dry run resolves it. For M3.2B it is resolved by **deriving** the count from
the frozen M3.2A objects — never by estimating it.

### 3.1 For an M3.2B budget only — derivation provenance

| Field | Value |
|---|---|
| Frozen bootstrap object identities the derivation used | `_______` |
| Historical-file references enumerated from the frozen bulk-submissions object | `____` |
| Entity reconciliation set size, and how it was determined | `_______` |
| Transport confirmed disabled during derivation | `YES` / `NO` |
| Derivation reproduces from the same frozen objects | `YES` / `NO` |

## 4. The eight budget quantities

| Quantity | Value | Derivation |
|---|---:|---|
| Planned unique logical requests | `____` | `Σ U(route)` from §3 |
| Maximum physical attempts | `____` | `Σ ( U(route) × A_reachable(route) )` from §4.1 — **never a single asserted multiplier** |
| Expected successful responses | `____` | logical requests expected to classify `proceed` |
| Expected cache hits | `____` | instances already satisfied and therefore excluded before planning; **reported, not subtracted again** |
| Expected not-modified responses | `____` | conditional re-validations expected to return `304` |
| Expected governed non-success responses | `____` | expected `retry` + `retry_after` + `cooldown` + `fail` + `quarantine` |
| Maximum new raw objects | `____` | equals planned unique logical requests; `304`, duplicates, terminal failures, and quarantine can lower actual, but are not assumed in the maximum |
| Rate-limiter spacing floor | `____` | `max(0, maximum physical attempts − 1) ÷ requests_per_second`; a minimum floor, not a maximum or prediction |

### 4.1 `A_reachable` per route — derived, not asserted

**`A_reachable(route)` is the maximum reachable physical attempts for that route, derived from the
implemented response-policy state machine and independently tested against its worst reachable path.**
It is **never** assumed to be the sum of the retry, redirect, and cooldown bounds — those mechanisms
interact inside one loop, and the composition is a property of the code, not of arithmetic.

The tested value is the transport attempt count observed from **one realizable full-path witness per
route** — a single `SecClient.fetch()` execution driven to its worst reachable path (Decision 029 §7,
`offline_rehearsal_spec.md` §6.9). Three separately measured terms added together are **not** a
witness. **Every route enumerated in §3 gets a row here, including routes planning zero**; a zero
`U(route)` never waives the witness.

| `source_id` | `A_reachable` | Derived from | Full-path witness reference | Zero-redirect actively proved |
|---|---:|---|---|---|
| `_______` | `____` | `_______` | `_______` | `YES` / `NO` / `n/a — route accepts hops` |

| Field | Value |
|---|---|
| Method used to derive `A_reachable` | `_______` |
| Independent worst-reachable-path test passed | `YES` / `NO` |
| Derived bound agrees with the tested bound | `YES` / `NO` |

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

**No contingency allowance exists, and none may be added.**

The v0.1 10% contingency is withdrawn. It existed only because v0.1 tried to acquire, in one window,
requests whose count depended on an object it had not yet retrieved. **The two-window split removes
that cause**: M3.2A's count is derivable before access, and M3.2B's is derived from frozen evidence.
A budget that needs slack is a budget whose inputs are not yet frozen — which is a signal to split,
not to pad.

| Field | Value |
|---|---|
| Contingency applied | **none — prohibited** |
| Confirmed no padding of any kind | `YES` / `NO` |

## 7. Hard request ceiling

```
HARD_REQUEST_CEILING(window) = Σ_over_routes_in_window ( U(route) × A_reachable(route) )
```

| Field | Value |
|---|---|
| Computed ceiling for **this window** | `____` |
| **Approved ceiling (exact integer)** | `____` |
| Ceiling behaviour | The run **refuses the attempt that would exceed** this value — it stops before, never after |
| Equality behaviour | A complete run may finish exactly at the ceiling; equality with work remaining yields `stopped_at_ceiling`, refuses `C+1`, and records `SEC_REQUEST_CEILING_EXHAUSTED` |
| May the ceiling be raised mid-window? | **No.** Raising it requires stopping, re-planning, and a new owner approval |
| Does this ceiling bind the other window? | **No.** Each window carries its own |

## 8. Rate-limiter spacing floor and elapsed-time factors

**This section does not claim a maximum duration.** Transfers, timeouts, `Retry-After`, and cooldowns
can lengthen the run beyond the limiter-imposed spacing floor.

| Field | Value |
|---|---|
| Limiter-imposed floor (seconds) | `____` |
| Expected transfer component (seconds) | `____` |
| Basis for the transfer component | `_______` |
| Expected timeout contribution (seconds) | `____` |
| Expected `Retry-After` contribution (seconds) | `____` |
| Expected cooldown contribution (seconds) | `____` |
| Operational elapsed estimate (not a bound) | `____` |

## 9. Pass/fail

| Check | Result | Note |
|---|---|---|
| Exactly one window named in §1 | `PASS` / `FAIL` | `_______` |
| Every route listed; other-window rows marked `n/a — other window` | `PASS` / `FAIL` | `_______` |
| No cell reads `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` | `PASS` / `FAIL` | `_______` |
| No count is a guess; each has a stated basis | `PASS` / `FAIL` | `_______` |
| **`A_reachable` derived per route and independently tested**, for **every** route in §3 including any planning zero | `PASS` / `FAIL` | `_______` |
| Max physical attempts equals `Σ ( U(route) × A_reachable(route) )` | `PASS` / `FAIL` | `_______` |
| Maximum new raw objects equals planned unique logical requests | `PASS` / `FAIL` | `_______` |
| Cache hits were excluded before planning and not subtracted again | `PASS` / `FAIL` | `_______` |
| **No contingency or padding applied** | `PASS` / `FAIL` | `_______` |
| Two dry runs produced identical plan hashes | `PASS` / `FAIL` | `_______` |
| For M3.2B: counts derived from the frozen M3.2A objects | `PASS` / `FAIL` / `N/A` | `_______` |
| Ceiling computed from the stated formula | `PASS` / `FAIL` | `_______` |
| No secret, identity, or personal path in this document | `PASS` / `FAIL` | `_______` |
| Completed copy stored privately; only its digest indexed publicly | `PASS` / `FAIL` | `_______` |

## 10. Blockers

| # | Blocker | Severity | Resolution required | Resolved |
|---|---|---|---|---|
| 1 | `_______` | `_______` | `_______` | `_______` |

**Any unresolved blocker prevents approval.**

## 11. Owner approval

> I approve, for the **acquisition window**, phase, and repository baseline named in §1, exactly
> these two integers:
>
> **Planned unique logical requests:** `____`
> **Hard request ceiling:** `____`
>
> This approval applies to this exact budget document, this exact window, and this exact
> request-plan hash. It does **not** transfer to the other acquisition window, a re-planned budget, a
> changed coverage window, a changed as-of date, or a different plan hash. **Network enablement is
> authorized only for the command named in the governing contract, only for this window, and only
> under these numbers.**

| Field | Value |
|---|---|
| Owner name | `_______` |
| Date (UTC) | `_______` |
| Decision | `APPROVED` / `REJECTED` |
| If rejected, reason | `_______` |
| Signature or recorded acceptance reference | `_______` |
