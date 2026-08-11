# Decision 062 — M3.2 Terminal-Failure Continuation and SIC Endpoint-Drift Remediation

**Date:** 2026-08-11
**Status:** ACCEPTED — OWNER REMEDIATION RULINGS 2026-08-11
**Authority classification:** `M3_2_TERMINAL_FAILURE_AND_SIC_ENDPOINT_REMEDIATION_ACCEPTED`
**Type:** Owner **remediation** record with an accompanying implementation. It records the owner's
rulings on the terminal, non-interrupted failure of the **T6** clean carry-in M3.2A invocation, and
on the external SEC endpoint drift that caused it. It is **offline governance, implementation, and
private-state repair only.**

**Grants no live authority.** No SEC request was made, no network switch changed, no CompanyFacts
access was opened, no continuation was executed, no M3.2B work was authorized, and **Gate H is not
passed and is not claimed.** The next authorized action is a fresh independent review of this
remediation, **not** live execution (§14).

**Amends:** nothing in place. Decisions 001–061 remain **byte-unchanged**.
**Narrowly supersedes:** exactly two current-state statements, and nothing else.

1. That `OWNER_M3_2_T6_CLEAN_CARRY_IN_CONTROLLED_ACQUISITION_EXECUTION_PACKET` is the next authorized
   action — in [Decision 061](decision_061_m3_2a_clean_carry_in_live_invocation_authorization.md),
   [`decision_registry.md`](decision_registry.md), and
   [`Milestones/STATUS.md`](../../Milestones/STATUS.md). That packet was issued and its invocation
   performed (§1).
2. That the M3.2A window's live source registry is `m2.2-source-registry/1.0` and its live SIC source
   is the `/corpfin/…` exact path — in
   [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §6,
   [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md) §12, and
   the registry. Superseded **for the single named `sec_sic_code_list` identity only** (§5); every
   other route in that boundary, and the boundary itself, is untouched.

Every superseded statement was accurate when written and is preserved as historical. The accepted
contract is **not edited by this record**: the packet governing this remediation authorized
documentation, template, decision-record, registry, and status updates, and did not authorize a
contract edit. The §6 registry-version statement is therefore superseded here rather than rewritten
there, and reconciling the contract text is left as an owner act.
**Preserves unchanged:** the cumulative M3.2A ceiling **801**; the frozen predecessor plan at SHA-256
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; the accepted 70-quarter coverage,
as-of date, calendar year, and evidence manifest; every route's `A_reachable`; the consumed carry-in
authority and its `ops_checkpoints` burn; the historical run's permanent non-resumability; and every
leakage, filing-body, and CompanyFacts/Frames prohibition.

---

## 1. Accepted entry state

The `OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET` of
[Decision 061](decision_061_m3_2a_clean_carry_in_live_invocation_authorization.md) was followed by
its execution packet, and the one authorized **T6** clean carry-in M3.2A invocation was performed on
2026-08-11. It ended **terminally and non-successfully**:

| Fact | Value |
|---|---|
| Run | `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44` |
| Receipt | `runs/m3_2a_clean_carry_in/execution_receipt.json` |
| Receipt SHA-256 | `0278c857d7816a79907068513fe09d5b78fc3973ba415149fbc9d73605b5359c` |
| Receipt id | `37dd811497d4a57e8b911917ed6c0426a22f443c3ddd5aeba8d4da3e076f6a7c` |
| `completion_status` | `failed` |
| `reason_code` | `SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY` |
| Planned / actual logical requests | 75 / 75 |
| Satisfied / failed | 74 / 1 |
| Physical attempts this run | 75 |
| Historical carried forward | 1 |
| **Cumulative consumed** | **76 of 801** |
| Raw objects stored | 74 |
| Carry-in authority | permanently consumed |

The single failed logical retrieval is `sec_sic_code_list`. SEC returned `301` from the registered
exact path to a target outside the route's structured path policy, and the policy layer refused to
follow it — correctly, and exactly as designed.

| | Exact path |
|---|---|
| Retired | `/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list` |
| Successor | `/search-filings/standard-industrial-classification-sic-code-list` |

## 2. Owner acceptance of the prior stop

`M3_2_DECISION_062_PRE_REMEDIATION_STOP_OWNER_ACCEPTED`.

The prior session stopped correctly under its packet. That stop is accepted. It does **not** establish
that M3.2 is permanently unrecoverable.

## 3. Ruling — terminal, non-interrupted failure is recoverable evidence

`M3_2_TERMINAL_FAIL_CLOSED_RECEIPT_RECOVERY_ELIGIBILITY_OWNER_RULING`.

The governing live-failure rule covers interrupted, killed, crashed, failed, gate-stopped,
ceiling-stopped, uncertain, and otherwise non-successful operations alike. The recovery
implementation must therefore not make `SAFE` eligibility **structurally impossible** merely because
a terminal failed or gate-stopped receipt correctly lacks an `interruption_state`.

**No interruption state is fabricated or added to the immutable T6 receipt.** Instead condition
**8.2** is generalized from *"the interruption state is established"* to:

> **The terminal or interruption state is established, not guessed.**

- *Interrupted receipt.* The accepted interruption-state evidence is required exactly as before.
- *Terminal, non-interrupted failed or gate-stopped receipt.* 8.2 may be met when **all ten** hold:
  1. the receipt is valid and immutable;
  2. `completion_status` is terminal and non-successful;
  3. a **registered** reason code is present;
  4. the run row is terminal and agrees with the receipt;
  5. the started and completed facts are present;
  6. the durable attempt count resolves;
  7. no uncertain commit exists;
  8. no orphan, row-without-object, or partial ambiguity exists;
  9. the predecessor chain resolves;
  10. catalog integrity passes.

**This is not a relaxation for uncertainty.** The terminal path demands *more* evidence than the
interruption path. `UNDETERMINED` remains a hard stop, and a receiptless, crashed, killed, or
genuinely uncertain state gains nothing from this path.

Implemented in `src/disclosure_drift/m3/recovery.py` (`establish_terminal_state`) and recorded in
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md) §8.

## 4. Authority — audit projection rebuild

`M3_2_T6_AUDIT_PROJECTION_REBUILD_OWNER_AUTHORIZED`.

Observed before remediation: **76** authoritative SQLite observations, **1** audit-projection row,
**75** observations with `projected_to_audit = 0`. The projection is a **valid prefix** — it is
behind, not wrong.

The existing deterministic recovery action `rebuild-projection` is authorized against the T6
operational state. Before mutation, verify: receipt identity; catalog integrity; the observed
projection mismatch exactly; zero unresolved recovery state; zero `.part`; no acquisition process
running; network disabled. Then rerun `recovery-state`.

SQLite remains authoritative. The receipt, raw objects, lineage, attempt accounting, run status, and
the failed SIC observation are **not** altered.

## 5. Ruling — source-registry successor

`M3_2_SIC_ENDPOINT_SUCCESSOR_PLAN_OWNER_RULING`.

Historical source-registry identity **`m2.2-source-registry/1.0`** is preserved: every receipt, plan,
and observation written under it remains a valid record of the registry that was live at the time,
and none is rewritten. It is retained as the named constant
`M22_SOURCE_REGISTRY_VERSION_HISTORICAL`.

The live registry becomes **`m2.2-source-registry/1.1`**, differing in exactly one registration
field: `sec_sic_code_list`'s exact path is **replaced** — not carried alongside — with
`/search-filings/standard-industrial-classification-sic-code-list`.

Unchanged for that route: host `www.sec.gov`, GET, `source_id`, source class, expected content HTML,
parser id and version semantics, redirect policy, retry policy, rate limit, filing-body guards, and
the CompanyFacts/Frames prohibitions. Because the family stays a **single exact path**, the route
admits no in-family redirect target and its derived **`A_reachable` remains 6**.

Ten security tests are required and implemented in `tests/unit/test_sec_http_client.py`: the new
exact path allowed; the old exact path no longer live-authorized; arbitrary `/search-filings`
siblings refused; prefix and suffix variants refused; non-SEC host refused; non-GET refused (a SEC
request carries no method field — GET is structural); filing-body routes refused; CompanyFacts and
Frames refused; a redirect away from the new exact path still fail-closed; and the original redirect
negative controls remain non-vacuous (a lawful in-family hop on the calendar route is still
followed).

## 6. Ruling — plan transition, and the withdrawn standalone plan requirement

`M3_2_STANDALONE_ONE_OBJECT_PLAN_REQUIREMENT_WITHDRAWN`.

The prior packet's requirement for an independent one-request repair plan is **withdrawn**. The
ordinary planner is not to be made to emit a single request.

Two deterministic **offline** successor full-window plans are produced after the registry
correction. The successor retains all original M3.2A inputs and all original logical request
identities except exactly one substitution:

| | Old | New |
|---|---|---|
| Logical request | `sec_sic_code_list` + retired exact normalized URL + unchanged parameters | `sec_sic_code_list` + successor exact normalized URL + unchanged parameters |

Required and verified: 75 logical requests on both sides; the identical 70-quarter set; identical
coverage, as-of, calendar year, and manifest; identical rate and retry policy; identical route
counts; identical `A_reachable` values; maximum physical attempts **801**; approved global ceiling
**801**; no contingency. The two successor outputs are **byte-identical**, and the successor plan
SHA differs from `19be7bdc…`.

**Why the plan document changed shape.** A plan document named routes and counts; it never named
URLs. The concrete logical request identities a plan authorizes are determined only by the plan
*together with* a source-registry version, so under the original schema an endpoint correction moved
a request identity while leaving the plan hash untouched — two materially different request sets
claiming one approved identity. The plan schema therefore gains exactly one field,
`source_registry_version`, as **`m3-request-plan/1.1`**. Documents of `m3-request-plan/1.0` are
still read and rendered **byte-exactly**, which is what keeps the Gate F artifact `19be7bdc…`
reproducible.

| Plan | SHA-256 |
|---|---|
| Predecessor (`m3-request-plan/1.0`, registry `1.0`) | `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` |
| Successor (`m3-request-plan/1.1`, registry `1.1`) | `f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a` |

## 7. Ruling — predecessor → successor plan transition

The accepted recovery implementation required an unchanged plan hash. The **minimum bounded**
owner-governed successor-plan mechanism is added for this exact external endpoint-drift case. It
must **not** become a general "resume with another plan" capability.

A transition is permitted only when **all seventeen** hold:

1. an explicit accepted owner decision names both plan hashes;
2. the same M3.2 window;
3. the same coverage, as-of, and calendar inputs;
4. the same route counts;
5. the same approved global ceiling;
6. the same `A_reachable` values;
7. the same maximum physical attempt budget;
8. all request identities match except an explicitly named finite substitution set;
9. for Decision 062 the substitution set size **must equal exactly 1**;
10. the substituted source **must equal** `sec_sic_code_list`;
11. the old URL **must equal** the Decision 062 retired path;
12. the new URL **must equal** the Decision 062 successor path;
13. parameters **must be unchanged**;
14. the predecessor receipt **must record** `m2.2-source-registry/1.0`;
15. the successor run **must record** `m2.2-source-registry/1.1`;
16. **no satisfied request may change identity**;
17. **no new route may be introduced**.

Any mismatch **refuses**. Implemented as `verify_plan_transition` in
`src/disclosure_drift/m3/acquisition.py`, producing a `PlanTransitionAuthority` whose constructor
re-checks the frozen Decision 062 constants, so a hand-built authority cannot widen the transition.
It is never inferred: the operator names the predecessor with
`--plan-transition-predecessor`, which is refused in receiptless mode and refused on `m3 acquire`
without `--resume-from`. Non-vacuity and mutation tests prove that a second substitution, a route
change, a parameter change, a ceiling or budget change, a quarter or input change, an arbitrary URL,
and the reverse direction are each rejected.

## 8. Ruling — the old failed SIC observation

`M3_2_SIC_OLD_IDENTITY_SUPERSESSION_OWNER_RULING`.

The committed old-path failed SIC observation
(`d8df1c00b5444f76ad275c02b132989e`, `outcome = failed`, HTTP `301`, no stored object) is **valid
immutable historical failure evidence**. It must remain stored; it is never rewritten, never
deleted, never marked successful, and never satisfies the successor SIC request.

When the owner-approved predecessor → successor transition is evaluated, that one failed old
identity is classified **`SUPERSEDED_BY_OWNER_APPROVED_ENDPOINT_DRIFT`**. It is therefore **not** an
arbitrary blocking out-of-plan observation, **not** a satisfied successor request, **not** evidence
to delete, and **not** authority for general out-of-plan tolerance.

The exception is valid **only** when every identity field matches Decision 062's single exact
substitution. Any unrelated out-of-plan observation — including a different observation on the same
route — remains blocking. Implemented as `superseded_out_of_plan_observation`; the superseded
identity is reported under `RequestReconciliation.superseded_out_of_plan` rather than removed from
view.

## 9. Continuation semantics

The intended future mechanism remains `m3 acquire --resume-from`, meaning a **new run**, never reuse
of the predecessor run id. It must preserve the T6 failed run unchanged; name the predecessor
receipt; carry cumulative consumed **76**; use the successor full-window plan; enforce the global
ceiling **801**; reconcile the 74 unchanged successful identities as already satisfied; classify the
old failed SIC identity only through the §8 supersession rule; produce `continuation.remaining`
**exactly 1**, on source **exactly** `sec_sic_code_list`, at **exactly** the successor URL; and issue
**zero** requests for the 74 satisfied identities.

**No live execution occurs under this record.** All of the above is proved offline against the real
catalog read-only, and against disposable copies for mutation tests.

## 10. `census_index_instances` — root cause and end-state

**Observation.** 70 successful `sec_full_index_company` observations exist; `census_index_instances`
holds **0** rows.

**Root cause, and it is not a T6 defect.** That relation is written **only** by the M2.3 census
index-retrieval lifecycle (`sec/census_orchestrator.py`). An M3.2 acquisition run never reaches it,
by design: M3.2 acquires metadata objects and **parses none of them**, so it records each planned
request's terminal state in `census_plan_sources` with `parser_state = 'not_started'`.
`census_index_instances` carries `parse_usable`, `reconciled`, and `satisfied`, and its own reuse
check verifies a `census_parser_runs` lineage row — all parse and reconciliation facts this stage may
not manufacture. A **successful** M3.2 window leaves the table empty too; that is asserted as an
executable fact.

**Consequently no implementation change is made for this finding.** Populating the relation from an
M3.2 finalization step would make M3.2 a parsing stage — architecture redesign rather than a bounded
correction — which §10 of the governing packet directs to **stop** rather than build. **No request is
re-issued because of this finding.**

**End-state proof, offline, from stored evidence only.** All 70 required closed-quarter instances map
1:1 to committed T6 observations; all 70 stored objects are present and their recorded
`stored_sha256` re-verifies; all are `stored_new` at HTTP 200 under `company-idx/1.0`; and the real
`company-idx` parser parses the stored bytes and yields records. The instance states are therefore
derivable with **zero additional SEC requests**, by the already-accepted M2.3 lifecycle, whenever a
stage contract authorizes running it.

**Corollary.** The empty table cannot cause a re-request. The planner's already-satisfied exclusion
reads this relation, and reading zero reproduces the accepted `expected_cache_hits = 0` — which is
what makes the successor plan's quarter set identical to the predecessor's. The continuation
remainder is computed from reconciliation over `census_source_observations`, where all 70 index
retrievals are satisfied.

## 11. T6 tmux and sentinel residue

The T6 acquisition child is terminal, its receipt exists, its run row is terminal `failed`, and its
pane was dead with status 4. A residual tmux server existing only because `remain-on-exit` preserved
a dead pane is **not** a live acquisition executor.

After preserving required diagnostic output, retirement is authorized for the `fdd-m32-t6` tmux
session and server, the T6 executor sentinel, and disposable supervisor scratch artifacts that are
not governed evidence. **Preserved:** the invocation log where it is governed evidence, exit status,
completion marker, receipt, carry-in, catalog, raw objects, lineage, and any private evidence needed
for review. **When uncertain, preserve.**

## 12. Cumulative accounting

| Quantity | Value |
|---|---|
| Historical seed | 1 |
| T6 physical attempts | 75 |
| **Cumulative consumed** | **76** |
| Approved global ceiling | **801** |
| Remaining headroom | 725 |
| Remaining logical requests | **1** |
| Worst-case remaining attempts | 6 |

No zero-baseline start is ever lawful. The ceiling is never raised, shadowed, made additive, or
reset.

## 13. What this record does **not** do

- It grants **no** live SEC authority and enables **no** network switch. Tracked
  `network.enabled`, `network.m3_acquire_enabled`, and CompanyFacts remain `false`.
- It does **not** execute a continuation, and it authorizes **no** M3.2B work.
- It does **not** pass Gate H and makes no Gate H claim.
- It does **not** reissue, replace, or duplicate the consumed carry-in authority; burn-before-wire
  is preserved exactly.
- It does **not** resume, reopen, or reuse the historical run
  `m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0`, which remains permanently non-resumable,
  `UNDETERMINED`, and receiptless.
- It does **not** alter the T6 receipt, the raw objects, the lineage, the attempt accounting, the run
  status, or the failed SIC observation.
- It creates **no** migration and **no** new table, column, constraint, or reason code.

## 14. Next authorized action

**`FRESH INDEPENDENT DECISION 062 REMEDIATION REVIEW`** — not live execution.

A later, separate owner instrument is required before any continuation invocation. M3.2 is **not**
complete, and live readiness is **not** claimed.
