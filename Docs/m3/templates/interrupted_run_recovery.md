# TEMPLATE — Interrupted-Run Recovery Checklist

**This file is a blank template. No run has been interrupted, because no run has occurred.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to establish, before anything is resumed, exactly where a run stopped, what committed,
what did not, and whether resuming is provably safe — and to prove that resuming will not duplicate a
substantive write.
**Phase:** M3.2 primarily; M3.3 for an interrupted selection or manifest construction.
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md);
[Decision 009](../../Decisions/decision_009_raw_data_governance.md);
[Decision 021](../../Decisions/decision_021_m23_s6_manifest_construction.md) §15.5 (the append-once
and identity guarantee);
[`milestone_2_3_pilot_selection_plan.md`](../../../Milestones/milestone_2_3_pilot_selection_plan.md)
§12 (rollback);
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) §11.

---

## 0. Handling

- **The completed copy is PRIVATE evidence.** It lives in the owner-controlled private evidence root,
  never in the repository. Only its type, phase, status, SHA-256, and reference identifier go into
  [`evidence_index.md`](evidence_index.md).
- **Non-secret content even so.** Identities, counts, states, and reason codes only.
- **Never record** the SEC identity, any credential, any absolute personal path, or any response
  body.
- **Nothing is deleted during recovery.** Rollback never means deleting evidence.
- **`UNDETERMINED` is a stop condition, not a judgement call.**

## 1. Identification

| Field | Value |
|---|---|
| Recovery record ID | `_______` |
| Phase | `_______` |
| Owner | `_______` |
| Date (UTC) | `_______` |
| Operator | `_______` |
| Interrupted run identifier | `_______` |
| Repository baseline commit | `_______` |
| Governing contract | `_______` |
| Acquisition window | `M3.2A` / `M3.2B` / `n/a` |
| Approved request-plan hash **for that window** | `_______` |
| Approved hard ceiling **for that window** | `____` |

## 2. Last successful receipt

| Field | Value |
|---|---|
| **Last successful `receipt_id`** | `_______` |
| Its `command_name` and `command_version` | `_______` |
| Its `completion_status` | `_______` |
| Its `started_at_utc` / `completed_at_utc` | `_______` |
| Its `actual_logical_request_count` | `____` |
| Its `actual_physical_attempt_count` | `____` |
| Its `raw_object_count` | `____` |
| Its `schema_drift_outcome` | `_______` |
| Its `recovery_predecessor_receipt_id`, if any | `_______` |
| **Is the full receipt chain resolvable back to the first attempt?** | `YES` / `NO` |

**A broken chain means `UNDETERMINED`.** Do not reconstruct a missing receipt from memory.

## 3. Interruption point

| Field | Value |
|---|---|
| **Interruption state** | `before_raw_store_write` / `after_raw_store_write_before_catalog_commit` / `after_catalog_commit` / `during_selection` / `during_manifest_write` |
| How the interruption state was established | `_______` |
| Cause, as far as it is known | `_______` |
| Was a terminating receipt written? | `YES` / `NO` |
| Terminating receipt ID | `_______` |
| Reason code recorded | `_______` |
| Last logical request identity attempted | `_______` |
| Was it `SIGINT`, a crash, a power loss, a network drop, or a deliberate stop? | `_______` |

## 4. Database state

| # | Item | Observed | Expected |
|---|---|---|---|
| 4.1 | Catalog reachable, single-writer lease acquirable | `_______` | yes |
| 4.2 | `quick_check` | `_______` | `ok` |
| 4.3 | `integrity_check` | `_______` | `ok` |
| 4.4 | `foreign_key_check` violations | `____` | `0` |
| 4.5 | Migration chain head | `_______` | `_______` |
| 4.6 | Migration checksums verified | `_______` | verified |
| 4.7 | Uncommitted transaction present? | `_______` | none |
| 4.8 | Source-observation rows committed | `____` | `_______` |
| 4.9 | Parsed source records committed | `____` | `_______` |
| 4.10 | Unresolved recovery events | `____` | `0` |
| 4.11 | Audit projection consistent with SQLite? | `_______` | consistent, or rebuildable |
| 4.12 | For an interrupted selection: `run_state` | `_______` | `_______` |
| 4.13 | For an interrupted selection: `selection_result_sha256` sealed? | `_______` | `_______` |
| 4.14 | For an interrupted manifest write: manifest row present? | `_______` | `_______` |

## 5. Raw-store state

| # | Item | Observed | Expected |
|---|---|---|---|
| 5.1 | Total content-addressed objects | `____` | `_______` |
| 5.2 | Objects verifying against `content_sha256` | `____` | all |
| 5.3 | Objects **failing** verification | `____` | `0` |
| 5.4 | Objects with a `.lineage.json` sibling | `____` | all |
| 5.5 | **Orphans** — object present, no committed row | `____` | `_______` |
| 5.6 | Orphans that verify and may be adopted | `____` | `_______` |
| 5.7 | Orphans that do not verify and must be quarantined | `____` | `_______` |
| 5.8 | Quarantined objects | `____` | `_______` |
| 5.9 | **Rows with no object** — the dangerous direction | `____` | **`0`** |

**Any row without its object is a stop condition**, not a recovery case.

## 6. Partial-file state

| # | Item | Observed | Expected |
|---|---|---|---|
| 6.1 | `.part` files present | `____` | `_______` |
| 6.2 | Each `.part` file's logical request identity | `_______` | — |
| 6.3 | Was any `.part` file treated as complete? | `_______` | **never** |
| 6.4 | Disposition of each `.part` file | quarantined / removed as a never-promoted temporary / `_______` | `_______` |
| 6.5 | Any partially written manifest document? | `_______` | none surviving |
| 6.6 | Any pre-existing artifact at a content-derived path? | `_______` | see limitation **D023-O3** |

## 7. Request-count state

| Field | Value |
|---|---:|
| Physical attempts consumed before the interruption | `____` |
| Approved hard ceiling **for this window** | `____` |
| **Remaining ceiling headroom** | `____` |
| Logical requests completed | `____` |
| Logical requests remaining in the plan | `____` |
| Maximum physical attempts the remainder could consume | `____` |
| **Does the remainder fit inside the remaining headroom?** | `YES` / `NO` |

**If `NO`, the resume requires a new owner-approved ceiling** and is not authorized under the old
one. **A ceiling is never increased during a running window** — a resume that needs more headroom is
a stop, a re-plan, and a fresh approval.

## 8. Safe-resume determination

| # | Condition | Result |
|---|---|---|
| 8.1 | The receipt chain resolves completely | `MET` / `NOT MET` |
| 8.2 | The interruption state is established, not guessed | `MET` / `NOT MET` |
| 8.3 | The catalog passes quick, integrity, and foreign-key checks | `MET` / `NOT MET` |
| 8.4 | No row exists without its object | `MET` / `NOT MET` |
| 8.5 | Every orphan is adopted or quarantined | `MET` / `NOT MET` |
| 8.6 | No `.part` file was treated as complete | `MET` / `NOT MET` |
| 8.7 | The audit projection is consistent or has been rebuilt from SQLite | `MET` / `NOT MET` |
| 8.8 | The remainder fits inside the remaining ceiling headroom | `MET` / `NOT MET` |
| 8.9 | No unresolved schema-drift incident is open | `MET` / `NOT MET` |
| 8.10 | The plan hash is unchanged | `MET` / `NOT MET` |
| 8.11 | For a selection: the accepted lifecycle guards leave exactly one lawful next state | `MET` / `NOT MET` / `N/A` |

| Field | Value |
|---|---|
| **Determination** | `SAFE` / `UNSAFE` / `UNDETERMINED` |
| Basis | `_______` |

- **`SAFE`** — every condition `MET`. Resume is authorized under §10.
- **`UNSAFE`** — a condition is `NOT MET` and the cause is known. Correct it, then re-run this
  checklist.
- **`UNDETERMINED`** — it cannot be established whether a write committed. **Stop. Do not resume.
  Refer for an owner ruling.**

## 9. Duplicate-prevention proof

Complete **before** resuming. A resume without this proof is not authorized.

| # | Proof | Result | Evidence |
|---|---|---|---|
| 9.1 | Every already-committed logical request is identifiable by its request identity | `PROVEN` / `NOT PROVEN` | `_______` |
| 9.2 | The resumed plan **excludes** every already-committed logical request | `PROVEN` / `NOT PROVEN` | `_______` |
| 9.3 | A byte-identical body would reconcile to the existing object rather than create a second | `PROVEN` / `NOT PROVEN` | rehearsal A9 |
| 9.4 | A differing body would become a **new observation**, never an overwrite | `PROVEN` / `NOT PROVEN` | rehearsal A10 |
| 9.5 | An adopted orphan does not produce a second object or a second row | `PROVEN` / `NOT PROVEN` | rehearsal A11(b) |
| 9.6 | Re-running an already-committed retrieval issues **zero** requests | `PROVEN` / `NOT PROVEN` | rehearsal A11(d) |
| 9.7 | For a selection: an identical restatement is idempotent and a differing one is refused | `PROVEN` / `NOT PROVEN` / `N/A` | accepted guards |
| 9.8 | The final state after resume equals the state an uninterrupted run would have produced | `PROVEN` / `NOT PROVEN` | rehearsal A11(d) |

## 10. Resume authorization and execution

| Field | Value |
|---|---|
| Resume authorized by | `_______` |
| Authorization date (UTC) | `_______` |
| Resume command | `_______` |
| **Predecessor receipt ID passed to the resume** | `_______` |
| Consumed count carried forward | `____` |
| Ceiling in force for the resume | `____` (must equal the original unless re-approved) |
| Plan hash in force | `_______` |

## 11. Resumed receipt

| Field | Value |
|---|---|
| **Resumed `receipt_id`** | `_______` |
| `recovery_predecessor_receipt_id` | `_______` |
| `consumed_request_count_carried_forward` | `____` |
| `completion_status` | `_______` |
| `actual_logical_request_count` | `____` |
| `actual_physical_attempt_count` | `____` |
| Cumulative physical attempts across the chain | `____` |
| **Cumulative attempts below the approved ceiling?** | `YES` / `NO` |

## 12. Final reconciliation

| # | Item | Result |
|---|---|---|
| 12.1 | Total logical requests across the chain equals the plan | `PASS`/`FAIL` |
| 12.2 | **No duplicate substantive write occurred** | `PASS`/`FAIL` |
| 12.3 | Raw-object count reconciles with the budget | `PASS`/`FAIL` |
| 12.4 | Zero `.part` files remain | `PASS`/`FAIL` |
| 12.5 | Zero orphans remain unadopted and unquarantined | `PASS`/`FAIL` |
| 12.6 | Catalog integrity and foreign-key checks pass | `PASS`/`FAIL` |
| 12.7 | Audit projection matches SQLite | `PASS`/`FAIL` |
| 12.8 | The receipt chain is complete and resolvable | `PASS`/`FAIL` |
| 12.9 | **Nothing was deleted during recovery** | `PASS`/`FAIL` |
| 12.10 | Gate H reflects the reconciled totals | `PASS`/`FAIL` |

## 13. Sign-off

| Field | Value |
|---|---|
| Owner | `_______` |
| Date (UTC) | `_______` |
| Recovery outcome | `RESUMED_AND_RECONCILED` / `NOT_RESUMED_REFERRED` / `NEW_RUN_REQUIRED` |
| Resulting limitation ID, if any | `_______` |
| Signature or recorded acceptance reference | `_______` |
