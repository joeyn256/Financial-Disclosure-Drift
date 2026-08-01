# TEMPLATE — Gate F Checklist (network containment and controlled-live readiness)

**This file is a blank template. Gate F has not been run and has not passed.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to record, item by item, that the project is ready to place its first SEC request — and
that it has not placed one yet.
**Phase:** M3.1B
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§§6, 8, 15–16; [Decision 024](../../Decisions/decision_024_m2_m3_boundary_governance.md) §5.2 (the
S7 row); [`milestone_2_3_pilot_selection_plan.md`](../../../Milestones/milestone_2_3_pilot_selection_plan.md)
§11 Gate F; [`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) phase M3.1.
**Completion token:** on a full pass,
`M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`.

---

## 0. Handling

- **The completed copy is PRIVATE evidence.** It lives in the owner-controlled private evidence root,
  never in the repository. Only its type, phase, status, SHA-256, and reference identifier go into
  [`evidence_index.md`](evidence_index.md).
- **Non-secret content even so.** Counts, route names, hashes, and outcomes only.
- **Never record** the SEC identity value, any credential, any absolute personal path, or any
  response body.
- **Every item is `PASS`, `FAIL`, or `N/A` with a reason.** There is no `PARTIAL` and no `UNKNOWN`
  that passes.
- **Immutable once signed.** A change requires a new dated copy.

## 1. Identification

| Field | Value |
|---|---|
| Phase | M3.1B |
| Owner | `_______` |
| Date (UTC) | `_______` |
| Operator | `_______` |
| Repository baseline commit | `_______` |
| Baseline tag | `_______` |
| Governing contract | `_______` |
| Migration chain head | `_______` |
| **Request-plan hash** | `_______` |
| Request-budget document reference | `_______` |

## 2. Prerequisite state

| # | Item | Result | Evidence |
|---|---|---|---|
| 2.1 | Branch is `main` and `HEAD == origin/main` | `PASS`/`FAIL` | `make context` output |
| 2.2 | Working tree clean; nothing staged, modified, or untracked | `PASS`/`FAIL` | `git status --short --untracked-files=all` |
| 2.3 | Migration chain contiguous through `0013`, nothing beyond | `PASS`/`FAIL` | `make context` |
| 2.4 | Full suite green at the phase-entry baseline | `PASS`/`FAIL` | suite counts |
| 2.5 | Bounded M3.1 contract exists, accepted, with exact paths | `PASS`/`FAIL` | contract path |
| 2.6 | Explicit owner authorization to begin M3.1 recorded | `PASS`/`FAIL` | reference |

## 3. Offline rehearsal (M3.1A)

| # | Item | Result | Evidence |
|---|---|---|---|
| 3.1 | **The complete ACQUISITION rehearsal passed** | `PASS`/`FAIL` | rehearsal evidence reference |
| 3.2 | All twelve scenarios **A1–A12** implemented and executed; none skipped or `xfail`ed | `PASS`/`FAIL` | scenario matrix |
| 3.3 | Every observed reason code equals its expected registered code | `PASS`/`FAIL` | matrix |
| 3.4 | No socket was opened, asserted rather than assumed | `PASS`/`FAIL` | assertion reference |
| 3.5 | Interruption scenarios recovered with duplicate prevention proven | `PASS`/`FAIL` | A11 |
| 3.6 | Route allowlist and denylist enforced at the boundary | `PASS`/`FAIL` | A6 |
| 3.7 | **Receipt non-contamination proof holds** — every governed value byte-identical with receipts disabled, enabled, and varied | `PASS`/`FAIL` | A12 |
| 3.8 | Prohibited-field scan proven non-vacuous by a positive control | `PASS`/`FAIL` | A12 |
| 3.9 | **Every rehearsal receipt reports actual network counts of `0`**, with simulated totals in the evidence report | `PASS`/`FAIL` | A1–A12 |
| 3.10 | **`A_reachable` derived per route and independently tested** against the worst reachable path | `PASS`/`FAIL` | A2, A4, A6 |
| 3.11 | **No snapshot, selection, reserve, sealing, manifest, or root scenario was rehearsed here** — those are M3.3A | `PASS`/`FAIL` | scenario matrix |
| 3.12 | `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` recorded | `PASS`/`FAIL` | reference |

## 4. SEC identity

| # | Item | Result | Evidence |
|---|---|---|---|
| 4.1 | The `[sec]` extra is installed | `PASS`/`FAIL` | version string only |
| 4.2 | **SEC identity validates at the boundary** | `PASS`/`FAIL` | `SEC contact identity: valid; value not displayed` |
| 4.3 | **The identity value was never printed, echoed, pasted, or written anywhere** | `PASS`/`FAIL` | operator attestation |
| 4.4 | No identity appears in any log, artifact, receipt, or this document | `PASS`/`FAIL` | scan result |

## 5. Network containment

| # | Item | Result | Evidence |
|---|---|---|---|
| 5.1 | **Network defaults to disabled** in the effective configuration | `PASS`/`FAIL` | `network: disabled (safe default)` |
| 5.2 | CompanyFacts disabled | `PASS`/`FAIL` | `companyfacts: disabled` |
| 5.3 | The Frames API is prohibited and unreachable | `PASS`/`FAIL` | policy reference |
| 5.4 | **An explicit live flag is required** — no command sends without it | `PASS`/`FAIL` | interface reference |
| 5.5 | Ordinary and offline imports pull in no HTTP client | `PASS`/`FAIL` | `test_no_network.py`, `test_optional_dependencies.py` |
| 5.6 | **Zero physical attempts occurred in this phase** | `PASS`/`FAIL` | receipts show `actual_physical_attempt_count = 0` |

## 6. Route allowlist

Every registered source, with its exact permitted host and path family, asserted.

| # | `source_id` | Host asserted | Path family asserted | Result |
|---|---|---|---|---|
| 6.1 | `sec_bulk_submissions` | `_______` | exact path | `PASS`/`FAIL` |
| 6.2 | `sec_company_tickers_exchange` | `_______` | exact path | `PASS`/`FAIL` |
| 6.3 | `sec_company_tickers` | `_______` | exact path | `PASS`/`FAIL` |
| 6.4 | `sec_sic_code_list` | `_______` | exact path | `PASS`/`FAIL` |
| 6.5 | `sec_edgar_filing_calendar` | `_______` | exact paths | `PASS`/`FAIL` |
| 6.6 | `sec_edgar_calendar_announcement` | `_______` | manifest-exact only | `PASS`/`FAIL` |
| 6.7 | `sec_full_index_company` | `_______` | pattern | `PASS`/`FAIL` |
| 6.8 | `sec_submissions_entity` | `_______` | pattern | `PASS`/`FAIL` |
| 6.9 | `sec_submissions_historical` | `_______` | pattern | `PASS`/`FAIL` |
| 6.10 | **Only `GET` is permitted** | — | — | `PASS`/`FAIL` |
| 6.11 | **Only `www.sec.gov` and `data.sec.gov` are permitted** | — | — | `PASS`/`FAIL` |

## 7. Route denylist

Each family asserted refused, with a representative probe path that is rejected.

| # | Denied family | Result | Evidence |
|---|---|---|---|
| 7.1 | Accession archive paths (`/Archives/edgar/data/`) | `PASS`/`FAIL` | `_______` |
| 7.2 | Accession index (`-index.htm`) | `PASS`/`FAIL` | `_______` |
| 7.3 | Filing-document suffixes (`.txt`, `.htm`, `.xml`, `.xsd`) | `PASS`/`FAIL` | `_______` |
| 7.4 | Primary documents | `PASS`/`FAIL` | `_______` |
| 7.5 | Complete submissions and SGML headers | `PASS`/`FAIL` | `_______` |
| 7.6 | Exhibits | `PASS`/`FAIL` | `_______` |
| 7.7 | Inline XBRL, XBRL instances, taxonomies | `PASS`/`FAIL` | `_______` |
| 7.8 | **CompanyFacts** | `PASS`/`FAIL` | `_______` |
| 7.9 | **Frames API** | `PASS`/`FAIL` | `_______` |
| 7.10 | Any non-SEC host | `PASS`/`FAIL` | `_______` |
| 7.11 | Any financial-outcome source | `PASS`/`FAIL` | `_______` |
| 7.12 | Scheme downgrade, user-info, unexpected port, fragment, relative segment | `PASS`/`FAIL` | `_______` |

## 8. Zero-request dry runs

| # | Item | Result | Evidence |
|---|---|---|---|
| 8.1 | First dry run completed with **zero** requests | `PASS`/`FAIL` | receipt |
| 8.2 | Second dry run completed with **zero** requests | `PASS`/`FAIL` | receipt |
| 8.3 | **The two plan hashes are identical** | `PASS`/`FAIL` | both values |
| 8.4 | The two plan outputs are byte-identical | `PASS`/`FAIL` | `diff` empty |
| 8.5 | The plan reads no value from the system clock | `PASS`/`FAIL` | all inputs explicit |
| 8.6 | The plan is deterministically ordered | `PASS`/`FAIL` | ordering assertion |
| 8.7 | No transport was constructed | `PASS`/`FAIL` | `_______` |

**First plan hash:** `_______`
**Second plan hash:** `_______`

## 9. Request budget and ceiling

| # | Item | Result | Evidence |
|---|---|---|---|
| 9.1 | Every route has a planned count with a stated basis | `PASS`/`FAIL` | budget §3 |
| 9.2 | **No cell reads `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`** | `PASS`/`FAIL` | budget §3 |
| 9.3 | Maximum physical attempts equals `Σ ( U(route) × A_reachable(route) )` | `PASS`/`FAIL` | budget §4 |
| 9.3a | **`A_reachable` derived from the implemented state machine and independently tested** | `PASS`/`FAIL` | budget §4.1 |
| 9.3b | **No contingency or padding applied** | `PASS`/`FAIL` | budget §6 |
| 9.4 | Expected raw-object count stated | `PASS`/`FAIL` | budget §4 |
| 9.5 | Expected request-class totals stated where derivable | `PASS`/`FAIL` | budget §4 |
| 9.6 | Expected elapsed window stated | `PASS`/`FAIL` | budget §8 |
| 9.7 | **Hard ceiling computed from the stated formula** | `PASS`/`FAIL` | budget §7 |
| 9.8 | **Stop-before-overflow behaviour asserted**, not stop-after | `PASS`/`FAIL` | rehearsal A5 |

**Acquisition window budgeted:** `M3.2A`
**Planned unique logical requests:** `____`  **Hard ceiling:** `____`

**This Gate F approves the M3.2A window only.** The M3.2B budget does not exist yet — it is derived
after M3.2A freezes its bootstrap objects and is approved separately.

## 10. Policy versions in force

| Version | Value |
|---|---|
| Source registry | `_______` |
| Quota policy | `_______` |
| Joint selector policy | `_______` |
| Replacement signature policy | `_______` |
| Manifest hash policy | `_______` |
| Selection input schema | `_______` |
| Parser versions | `_______` |

## 11. Leakage attestation

| # | Item | Result |
|---|---|---|
| 11.1 | No outcome value was read | `PASS`/`FAIL` |
| 11.2 | No filing text was read | `PASS`/`FAIL` |
| 11.3 | No external corpus was consulted | `PASS`/`FAIL` |
| 11.4 | No pilot membership or stratification informed anything | `PASS`/`FAIL` |
| 11.5 | The exact read set for this phase is stated below | `PASS`/`FAIL` |

**Exact read set:** `_______`

## 12. `CURRENT_PLANNER_DISCREPANCY` — must be resolved before Gate F passes

Decision 013 §1 states that coverage extends through the **closed 2026 Q2** quarter. The accepted
planner classifies 2026 Q2 as the **provisional open quarter** and, with `include_open_quarter =
false`, **excludes** it.

| # | Item | Result | Evidence |
|---|---|---|---|
| 12.1 | The discrepancy was diagnosed and its cause identified | `PASS`/`FAIL` | `_______` |
| 12.2 | **Resolved** — the planner agrees with Decision 013 §1, **or** a new owner-approved decision changed that authority | `PASS`/`FAIL` | `_______` |
| 12.3 | **Decision 013 was not silently changed** to accommodate the planner | `PASS`/`FAIL` | `_______` |
| 12.4 | The request plan's required-quarter set matches accepted authority | `PASS`/`FAIL` | `_______` |

**Gate F cannot pass while 12.2 is `FAIL`.** A request plan that disagrees with the accepted coverage
cutoff is not a plan a budget can be approved against.

## 13. Operator readiness acknowledgement

> I have read the operator runbook end to end. I understand which commands exist and which are
> labelled `PLANNED — NOT YET IMPLEMENTED`. I understand that the identity is never printed, that a
> planned command is never typed, and that the stop rule applies at the first mismatch.

| Field | Value |
|---|---|
| Operator | `_______` |
| Date (UTC) | `_______` |
| Acknowledged | `YES` / `NO` |

## 14. Blockers

| # | Blocker | Severity | Resolution required | Resolved |
|---|---|---|---|---|
| 1 | `_______` | `_______` | `_______` | `_______` |

**Any `FAIL`, any `UNKNOWN`, or any unresolved blocker means Gate F does not pass.**

## 15. Owner sign-off

> I confirm that every item above is `PASS` or a justified `N/A`, that no live SEC request has been
> placed, that the `CURRENT_PLANNER_DISCREPANCY` is resolved, and that the **M3.2A** request budget
> and hard ceiling recorded in the referenced budget document are approved as exact integers.
>
> **This sign-off authorizes network enablement only for the command named in the governing M3.2
> contract, only under the approved M3.2A budget and ceiling, and only for the M3.2A window.** It
> does **not** authorize M3.2B, whose plan does not yet exist and whose budget requires a separate
> owner approval after the M3.2A objects are frozen.

| Field | Value |
|---|---|
| Owner | `_______` |
| Date (UTC) | `_______` |
| Gate F result | `PASS` / `FAIL` |
| Completion token recorded | `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` / not recorded |
| Signature or recorded acceptance reference | `_______` |
