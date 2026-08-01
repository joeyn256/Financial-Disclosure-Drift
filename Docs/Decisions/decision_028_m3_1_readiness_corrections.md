# Decision 028 — Milestone 3.1 Readiness Corrections and Owner Rulings

**Date:** 2026-08-01  
**Status:** PROPOSED — PENDING INDEPENDENT REREVIEW AND OWNER ACCEPTANCE  
**Type:** Bounded Milestone 3 operational-governance correction. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, S5 or S6 identity, hash preimage, migration byte, or publication
boundary. It authorizes no implementation and no network access.  
**Narrowly supersedes on acceptance:** only the affected operational-planning language in
[Decision 027](decision_027_m3_master_plan_and_operational_readiness.md) concerning the M3-L12
classification, A1–A12 scenario expectations, execution-receipt schema, request-budget arithmetic,
ceiling equality, recovery inspection, and M3-L11 protection.  
**Amends:** nothing. In particular, [Decision 013](decision_013_pilot_selection_mechanics.md) and
[Decision 024](decision_024_m2_m3_boundary_governance.md) remain unchanged and controlling for the
research cutoff and the M2 → M3 phase boundary respectively.  
**Related:** Decisions 009, 013, 024, 026, and 027;
[`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md);
[`Docs/m3/`](../m3/operator_runbook.md).  
**Governs on acceptance:** the bounded correction required for the independent M3 master-plan
rereview to pass, and the exact owner rulings a future M3.1 contract must implement.

---

## 1. Why this record is required

The independent rereview required by Decision 027 §§23–24 did not pass. It found that the accepted
planning package correctly stopped on the planner/authority disagreement, but incorrectly treated
that disagreement as an unresolved methodological choice and left several operational rules
internally inconsistent.

The focused architecture review and the subsequent planning reconciliation agree on the central
facts:

1. the 2026 Q2 disagreement is an inherited implementation defect, not a reason to change Decision
   013;
2. the exact-quarter-end classification must receive a new policy version;
3. A5 and A11 need registered terminal reason codes;
4. A1–A12 must be corrected before they can be accepted as the required rehearsal matrix;
5. execution receipts need a v2 schema before any receipt exists;
6. cache-hit, raw-object, elapsed-time, and ceiling-equality language must be corrected; and
7. M3-L11 needs an implementation protection, not only a procedural warning.

Decision 027 §24 forbids drafting the M3.1 contract until the rereview passes. This record therefore
corrects governance and planning **only**. It does not create that contract and does not implement
any ruling below.

## 2. Verified baseline

Verified live before this draft was prepared:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit | `c91af082c85b3a096218e2316ff9328f92a8a4d8` |
| Subject | `Correct Milestone 3 planning rereview findings` |
| `HEAD == origin/main` | yes |
| Working tree | clean at draft start |
| Migration chain | contiguous through `0013`; no migration is proposed here |
| Active implementation contract | none |
| Implementation authorization | `NO` |
| Network authorization | `NO` |

The baseline commit already contains the bounded Decision 027 v0.2 documentation corrections. Any
status text calling those corrections “uncommitted” is stale and is corrected by this package.

## 3. Authority and nonchange rulings

1. **Decision 013 §1 remains byte-for-byte unchanged.** Its accepted `2026-06-30` as-of cutoff and
   requirement to cover the closed 2026 Q2 quarter control.
2. **Decision 024 remains the phase-map authority.** This record adds no phase, removes none, and
   changes no phase's network permission.
3. **Milestones 0–2 remain formally closed.** Correcting an inherited implementation defect under a
   future M3.1 contract does not reopen or retag Milestone 2 and does not rewrite a historical v1
   plan hash.
4. **Decisions 021–023 and accepted S5/S6 identities remain unchanged.** Receipts remain operational
   evidence outside every governed identity.
5. **No request count is frozen here.** Correct counts are produced only by the corrected planner
   from explicit inputs.

## 4. M3-L12 is an inherited implementation defect

The planner's module contract says a quarter whose end is on or before `as_of_date` is closed. Its
implementation instead checks “quarter containing `as_of_date`” first. On an exact quarter end,
both predicates are true and the current branch order returns the wrong result.

The controlling total order is:

```text
if quarter_start > as_of_date:
    not_planned
elif quarter_end <= as_of_date:
    required_closed_quarter
else:
    provisional_open_quarter
```

Consequences:

- on `2026-06-30`, 2026 Q2 is `required_closed_quarter`;
- no provisional quarter exists when the as-of date is exactly a quarter end;
- on an interior date, the containing quarter remains provisional;
- a quarter beginning after the as-of date remains unplanned; and
- `include_open_quarter` affects only a genuinely open quarter.

The implementation must set:

```text
INDEX_PLAN_POLICY_VERSION = "quarterly-index-instances/2.0"
```

`CoverageWindow` must reject any caller-supplied policy version that differs from that executable
constant. New v2 behaviour must never be labelled v1. Historical v1 plan records and hashes remain
historical and are never rewritten. No migration is required: future plans carry v2 alongside any
historical v1 rows already present.

M3-L12 remains active until the correction, boundary tests, full validation, independent M3.1
acceptance, and committed checkpoint all exist. Its classification changes from “owner ruling
pending” to **“owner ruling recorded; implementation pending.”** Gate F remains blocked meanwhile.

## 5. The corrected A1–A12 matrix is the only acceptable matrix

All twelve scenarios remain mandatory, with no skip, `xfail`, conditional disablement, or scenario
substitution. The matrix as written in Decision 027 v0.2 is rejected where it conflicts with the
following expectations; the corrected detailed matrix in
[`offline_rehearsal_spec.md`](../m3/offline_rehearsal_spec.md) controls operationally.

| Scenario | Authoritative correction |
|---|---|
| **A1** | First storage is `stored_new` with no mutation reason. `SOURCE_CONTENT_UPDATED` applies only to a later changed living source. One observation and one object per logical request. A manifest-resolved announcement route may lawfully have zero instances when its manifest is empty. |
| **A2** | `503,503,200` is one logical request, three simulated physical attempts, one observation and one object, with no terminal reason. |
| **A3** | A usable delta-seconds `Retry-After` is honoured exactly; an unusable HTTP-date enters aggregate cooldown. Success has no terminal reason. |
| **A4** | A second `403` or block page terminates with `SEC_BLOCK_PAGE`; a second unqualified `429` terminates with `SEC_RETRIES_EXHAUSTED`. The client must supply that fallback rather than return a terminal failure with no code. |
| **A5** | Place exactly `C` simulated attempts, refuse `C+1`, emit `SEC_REQUEST_CEILING_EXHAUSTED`, preserve committed work, and leave the remainder unattempted. Completing all work exactly at `C` succeeds. |
| **A6** | Invalid initial routes are refused before transport. A redirect violation necessarily follows the preceding response, but the next hop is refused before it is followed and before any write. Manifest gating is tested with a lawful empty manifest rather than a fabricated retrievable entry. |
| **A7** | Unknown fields are retained and recorded with `PARSER_SCHEMA_DRIFT_OBSERVED`; otherwise lawful records continue. |
| **A8** | Preserve the raw observation and atomically persist parser-failure, structural, quarantine, and drift evidence. Admit no invalid, defaulted, coerced, or silently dropped normalized row. Valid siblings may remain recorded, but the parser run is failed/incomplete. Policy-failure evidence is not rolled back; only a fault in the evidence transaction rolls back that transaction. |
| **A9a** | A second byte-identical `200` creates one object and two immutable observations; the second is `unchanged_content` with `SOURCE_CONTENT_UNCHANGED`. |
| **A9b** | A valid `304` creates one object and two observations; the second is `reused_snapshot` with `SOURCE_SNAPSHOT_REUSED`. |
| **A10** | Living change: `SOURCE_CONTENT_UPDATED`; closed dated artifact: `SOURCE_DATED_ARTIFACT_CHANGED`; immutable identity: `SOURCE_IMMUTABLE_IDENTITY_MUTATED`; explained dated correction: `SOURCE_CONTENT_UPDATED` plus `SOURCE_CORRECTION_EXPLAINED`. `REMOTE_CONTENT_CHANGED` is a lower-layer observation and not the final SnapshotStore verdict. |
| **A11** | Generic interruption: `SEC_ACQUISITION_INTERRUPTED`; real partial transfer: `RAW_PARTIAL_DOWNLOAD`; verified orphan adoption: `RecoveryEvent(action_taken="adopted_verified")`; unproven orphan quarantine: `RAW_FILE_CHECKSUM_MISMATCH`; projection deficiency: `AUDIT_PROJECTION_INCOMPLETE`. Inspection is read-only and reports `UNSAFE` until deterministic repair has run, then `SAFE`. |
| **A12** | Receipt-v2 allowlist, a positive contaminated control, zero actual network counts in non-live modes, and byte-identical acquisition plus accepted S5/S6 identities with receipts disabled, enabled, and varied. |

## 6. Two new registered reason codes

The future M3.1 contract must add exactly these codes to the central registry, with no alias:

| Code | Category | Blocks release | Manual review | Meaning |
|---|---|---:|---:|---|
| `SEC_REQUEST_CEILING_EXHAUSTED` | `integrity` | `true` | `false` | Planned work remains, but the next physical attempt would exceed the exact owner-approved ceiling. |
| `SEC_ACQUISITION_INTERRUPTED` | `integrity` | `true` | `false` | Acquisition was interrupted and no narrower registered reason applies. |

Both codes cite this decision. `SEC_RETRIES_EXHAUSTED` remains distinct: it means a single logical
retrieval exhausted response-policy retries, not that the window-wide physical-attempt ceiling was
consumed. `RAW_PARTIAL_DOWNLOAD` remains specific to an actual partial transfer.

## 7. Ceiling equality and stop-before-overflow

The hard invariant is:

```text
actual_physical_attempt_count <= approved_request_ceiling
```

Before every physical attempt, the acquisition driver checks whether placing that attempt would
make the cumulative count exceed the ceiling. If so, it refuses the attempt. Therefore:

- a complete run ending exactly at the ceiling succeeds;
- equality plus remaining planned work yields `stopped_at_ceiling` and
  `SEC_REQUEST_CEILING_EXHAUSTED`;
- attempt `C+1` is never placed and the counter remains `C`;
- Gate H requires both `actual <= ceiling` **and** a complete, reconciled plan;
- no ceiling is raised during a running window; and
- a resume carries consumed attempts forward. If the proven worst-case remainder does not fit in
  the remaining headroom, the run stops for re-planning and a new exact approval rather than
  silently enlarging the active ceiling.

Every phrase requiring actual attempts to be “strictly below” the ceiling, declaring that reaching
the ceiling is inherently a failure, or requiring A5's attempts to be below `C` is superseded.

## 8. A11 phase ownership and recovery safety

M3.1 owns:

- a read-only `m3 recovery-state` inspection surface;
- its offline rehearsal against injected interruption states; and
- proof that inspection itself performs no write.

M3.2 owns real repair application, adoption/quarantine, and resume. The M3.1 inspector may report
what deterministic action is required, but it must never call the mutating
`observation_catalog.reconcile()` path or any equivalent writer.

`SAFE` means the state is already safe to resume. A state needing repair is `UNSAFE` until that
repair has been applied and a fresh read-only inspection returns `SAFE`. `UNDETERMINED` remains a
hard stop requiring an owner ruling.

## 9. Execution receipts are version 2.0 before the first receipt exists

The accepted schema for implementation is:

```text
m3-execution-receipt/2.0
```

The change is major because field classifications and meanings change. No v1 receipt exists, so no
migration, rewrite, or compatibility shim is required.

Required v2 corrections:

1. `acquisition_window` is required in `dry_run` and `live`.
2. `approved_request_ceiling` is `live` only. The two Gate F dry runs occur before owner approval
   and must not claim an approval that does not yet exist.
3. Add `index_plan_policy_version` and `request_plan_schema_version` to `dry_run` and `live`.
4. Add live-only `remaining_planned_logical_request_count` when
   `completion_status = "stopped_at_ceiling"`.
5. Remove `gate_f_outcome` and `gate_h_outcome`. Those gates conclude after the command receipt is
   immutable and belong in their checklists, not in a receipt.
6. Simulated request, response, and object counts remain exclusive to private rehearsal evidence.
7. The one receipt integrity identity remains `receipt_id`; no second digest is added.

Accounting validation compares the physical-attempt count to an approved ceiling only in `live`
mode, where that field exists.

## 10. Request-budget arithmetic

Already-satisfied catalog instances are excluded before the logical-request plan is formed. They are
reported as cache hits for operator reconciliation but are **not** subtracted a second time.

For each window:

```text
planned_unique_logical_requests
  = count(distinct approved request identities not already satisfied)

maximum_physical_attempts
  = sum_over_routes(planned_unique_logical_requests(route) * A_reachable(route))

maximum_new_raw_objects
  = planned_unique_logical_requests

rate_limiter_spacing_floor_seconds
  = max(0, maximum_physical_attempts - 1) / requests_per_second
```

`maximum_new_raw_objects` is an upper bound: each planned logical request can create at most one new
terminal object. A `304`, duplicate body, terminal failure, or quarantine lowers the actual count;
none may be assumed when computing the maximum. Cache hits are already outside the plan.

The rate-limiter expression is a **minimum spacing floor**, not a maximum or a prediction. Transfer
time, timeouts, `Retry-After`, and cooldowns can lengthen elapsed time. The request budget records
that floor and the operational factors separately; it must not label their sum a proven maximum.

## 11. M3-L11 protection

The future M3.1 contract must authorize and test all three layers together:

1. add exactly `/.m3-private-evidence` to the repository-root `.gitignore`;
2. make repository hygiene fail on any file, directory, or symlink at that reserved in-checkout
   path even though Git ignores it; and
3. make every M3 evidence-output CLI reject a resolved evidence root that is equal to, inside, or
   an ancestor of the repository checkout. Symlink resolution must not bypass this check.

The canonical operational evidence root remains owner-controlled and outside the checkout. M3-L11
closes only after the implementation, adversarial path tests, full validation, independent M3.1
acceptance, and committed checkpoint exist.

## 12. Future implementation boundary

This record authorizes no implementation. Once the master-plan rereview passes, a separate M3.1
contract may name the exact paths required for:

- the planner v2 correction and boundary tests;
- the two reason codes and registry tests;
- the narrow second-cooldown fallback and its tests;
- the cumulative physical-attempt ceiling gate required by §7, taking an explicit ceiling argument on
  the acquisition/retrieval surface, refusing the attempt that would exceed it, and its tests — this
  is the production path A5 exercises and the seam its ceiling substitution injects at;
- the M3.1 rehearsal, request-plan, receipt-v2, and read-only recovery surfaces;
- M3-L11 ignore, hygiene, CLI, and adversarial path tests; and
- the documentation consequences of those implementation changes.

Any edit to an inherited M2 implementation path is a forward M3.1 correction to a defect that blocks
Gate F. It does not reopen an accepted M2 contract, rewrite an M2 tag, or relax an M2 invariant.

## 13. Required independent rereview

Before this record may be accepted and before an M3.1 contract may be drafted, a fresh Opus Max
reviewer that authored none of this correction package must verify at least:

1. Decision 013 and Decision 024 are unchanged;
2. the quarter total order and policy-version boundary are internally complete;
3. A1–A12 are executable against existing or explicitly future M3.1 production paths;
4. every expected reason code exists now or is explicitly authorized for the future contract;
5. receipt v2 field timing is possible and non-contaminating;
6. request-budget quantities are not double-counted or mislabelled;
7. ceiling equality and recovery rules fail closed;
8. M3-L11 cannot be bypassed with an ignored path, ancestor root, or symlink;
9. no implementation or network authority is accidentally granted; and
10. all status and navigation claims match the live repository.

The required outcome is:

```text
INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS
```

Anything else returns the package for bounded correction and another fresh review.

## 14. Acceptance and checkpoint sequence

If §13 passes, the sequence is:

1. record owner acceptance of this decision and the corrected A1–A12 matrix;
2. run the documentation and repository validation gates;
3. create one governance-only commit and push to `main`; **no tag**;
4. in a separate fresh session, draft the bounded M3.1 contract with exact paths;
5. independently review and accept that contract; and only then
6. issue explicit M3.1 implementation authorization under all five Decision 024 §8 conditions.

## 15. Current outcome and next action

This draft records no formal accepted outcome yet. The next authorized action is:

```text
INDEPENDENT_M3_MASTER_PLAN_REREVIEW_OF_DECISION_028_PACKAGE
```

## 16. Negative confirmations

Verified true for this correction package:

- no production code, test, migration, configuration, or `.gitignore` byte is changed;
- Decision 013 is unchanged;
- no M3.1 contract is created or drafted;
- implementation authorization remains `NO`;
- no transport is constructed and no SEC request is placed;
- no live metadata, filing body, CompanyFacts value, Frames value, filing text, or outcome value is
  read;
- no real snapshot, selection, reserve, manifest, root approval, or publication is created; and
- no tag is created, moved, or proposed for this checkpoint.
