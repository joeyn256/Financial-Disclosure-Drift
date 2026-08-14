# Decision 070 — M3.3-I/R Implementation and Rehearsal Authorization

```text
STATUS: ACCEPTED — OWNER M3.3-I/R IMPLEMENTATION + REHEARSAL AUTHORIZATION
DATE: 2026-08-13
OWNER: Sol/GPT
OUTCOME: M3_3_I_R_IMPLEMENTATION_AND_REHEARSAL_OWNER_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION: YES — M3.3-I/R ONLY
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This is the owner's bounded M3.3-I/R implementation-and-rehearsal authorization.** It is the
separate implementation packet that accepted
[Decision 069](decision_069_m3_3_contract_final_owner_acceptance.md) §8 named as the next act, and
it is the **only** authority under which M3.3 implementation may begin. It authorizes implementing
the accepted M3.3 contract, its tests, and its fixture/disposable-copy rehearsal — **and nothing
that touches real private evidence**.

**It authorizes no real execution.** M3.3-E0 (the real private offline metadata parse), M3.3-E1
(the real candidate snapshot and selection), M3.3-E2 (the real manifest and root), and M3.4 (root
approval) all remain **unauthorized**, and each remains a separate later owner act. Network
authority remains **NONE**, reacquisition authority **NONE**, the request ceiling **0**, migration
**none**, and `m3.2-complete` **immutable**.

**Where this record and an earlier governing record disagree**, this record controls only on the
points it names. Decisions 001–069 remain accepted and **byte-unchanged**; the M3.3 contract, both
independent review artifacts, the fresh rereview artifact, and the historical GR proposal are not
rewritten by this record.

---

## 1. Entry state

Verified live before any edit.

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD / `origin/main` | `882dec057d7446faedd45e3528c77a14051598c8` (tree `1c1faa972347deddc3004c5424ad1485b5ff3beb`) |
| Working tree | clean |
| HEAD subject | `Accept corrected M3.3 contract` |
| Latest accepted decision at entry | **Decision 069** |
| Active stage contract | [`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md) |
| M3.3 contract status at entry | `ACCEPTED — OWNER FINAL CONTRACT ACCEPTANCE — DECISION 069`; `CONTRACT_ACCEPTANCE: YES` |
| Implementation authorization at entry | **NO** |
| `m3.2-complete` | unchanged, immutable (tag object `2865a1479e4576dc18a4098c928b278812f38d00`) |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

The Decision 069 prerequisite is satisfied: the contract is accepted, the fresh independent
rereview passed at BLOCKER 0 / MAJOR 0 / MINOR 0, and this record is the separate owner
implementation packet that acceptance did not supply.

## 2. The authorization

```text
M3_3_I_R_IMPLEMENTATION_AND_REHEARSAL_OWNER_AUTHORIZED
```

Authority extends to exactly five things:

| # | Authorized |
|---|---|
| A | Implementing the **accepted** M3.3 contract — the candidate-snapshot builder, the bounded offline metadata parse driver, and the E1–E8 execution-rehearsal harness |
| B | Tests for that implementation |
| C | **Fixture / disposable-copy rehearsal** of it |
| D | **Narrow R3 hardening** of the paths M3.3 actually uses for a governed read-only action (contract §1.1 **R8**) |
| E | The governance and status records needed to record this implementation stage truthfully |

It extends to **none** of: the accepted private M3.2 evidence root; `EV_ROOT`; M3.3-E0; real
candidate-snapshot construction; real selection; a real manifest or root; SEC; HTTP; network;
reacquisition; new evidence; CompanyFacts; Frames; filing-body retrieval; methodology changes; or
migrations.

**This is one bounded authority, and it is exhausted** once the I/R stage completes and is returned
for independent review.

## 3. The real-private boundary

**No session under this authority may use the real private evidence root.** If `EV_ROOT` exists in
the environment it is not printed, resolved, read, inspected, passed to any command, or used for
any test, and the filesystem is not searched for private evidence.

Implementation, tests, and rehearsal operate **only** on repository fixtures, generated synthetic
fixtures, disposable temporary catalogs, and disposable isolated copies built solely from
non-private test material.

**No implementation token, test result, or rehearsal result grants E0.**

## 4. The one deferred input this record supplies — OQ-6's executable home

Accepted [Decision 067](decision_067_m3_3_snapshot_authority_and_offline_parse.md) §8 fixed
`coverage_policy_version` as the methodology value **`pilot-coverage/1.0`** and §8.1 recorded that
the value had **no authorized executable home**, leaving it "an open path question for the M3.3-I/R
implementation packet, requiring its own owner authorization at that gate". M3.3 contract §20
recorded the same open question and §23 item 28 made reaching it a stop-and-refer condition
**pending exactly this packet**.

**This record is that gate, and the owner supplies the value now.**

| Aspect | Ruling |
|---|---|
| Executable home | `src/disclosure_drift/pilot_policy.py` — **one** canonical constant |
| Name | `PILOT_COVERAGE_POLICY_VERSION` |
| Value | `"pilot-coverage/1.0"` — the Decision 067 §8 methodology value, unchanged |
| Kind | An **engineering/provenance version only** |
| Prohibited | No config setting, no environment variable, no `reference_policy_versions` seed row, **no migration** |
| Consumption | Snapshot construction consumes the canonical constant; the literal is **not** duplicated in implementation code |
| Test obligation | A test must prove **no second competing executable definition** exists |

It **must not** alter coverage dates, cohort dates, selection methodology, quotas, evidence floors,
or candidate membership.

**Consequently, contract §20's "one known open path question" and §23 item 28 are discharged for
`coverage_policy_version` and for nothing else.** Every other §20 prohibition and every other §23
stop condition stands verbatim. The contract's §36 statement that its own acceptance did not
authorize the constant remains true: this record does, and the contract's acceptance did not.

## 5. Scope of the implementation this record authorizes

Stated by workstream, each of which implements the **accepted contract** and never reinterprets it.

| ID | Workstream | Governing contract clause |
|---|---|---|
| **I1** | Bounded **offline metadata parse driver** — plan-bound observation selection, the R18 report-level dispositions, the R17 fifteen-table write footprint, no HTTP and no transport | §6 item 2; §10.2; **R13**, **R17**, **R18** |
| **I2** | The **`PILOT_COVERAGE_POLICY_VERSION`** constant (§4 above) | §20 open path question, discharged here |
| **I3** | **Candidate-snapshot builder** — one atomic construct-and-freeze transaction, the OR-2 135-field mapping | §6 item 1; §8.1; §10; §11; **R5** |
| **I4** | The **OR-1 identity graph** — the eleven snapshot identities, `evidence_sha256`, `contributing_evidence_sha256`, and all eight `*_resolution_sha256` columns | §10.1; **R15**, **R16**, **R16-C1** |
| **I5** | **Structural fingerprint** non-vacuity, reusing the accepted Decision 021 §8.1 definition | §10.2; **R14** |
| **I6** | **Narrow R3 hardening** of the M3.3 read-only paths that still open an OS-level read-write handle | §14; **R3**, **R8** |
| **I7** | Integration with the **accepted** selector, stores, seal, manifest, and replay machinery — reused, never replaced | §5; §12; §13; §14; §17 |
| **I8** | Explicit, testable **gate isolation** between I/R, E0, E1, E2, and M3.4 | §10.2; §23 items 23, 24 |

Real `node_limit` (**OR-7**) and the six Decision 021 §8.4 explicit manifest arguments (**OR-6**)
remain **deferred to their named owner gates**. Rehearsal uses explicitly test-only values, which
are **test values only** and are never recorded as the future real values. **OR-9** and **OR-11**
remain deferred; Decision 023 **O1** remains an owner referral on a real trigger, and the rehearsal
must deliberately trigger it and prove fail-closed referral.

## 6. What completing I/R does, and does not, mean

On successful completion the recorded status becomes:

```text
M3.3-I/R: IMPLEMENTED + REHEARSED — PENDING INDEPENDENT REVIEW
```

and this record's bounded implementation authority is **consumed for the recorded I/R target**.

**That status does not mean E0 is authorized.** The only next action after a successful I/R is
**independent review**. The real M3.3 sequence remains, in order and with no automatic progression
at any step:

1. **M3.3-I/R** — implementation and fixture/disposable rehearsal (this record);
2. **independent implementation/rehearsal review**;
3. **bounded corrections**, if the review requires them;
4. a **fresh A1 independent rehearsal acceptance**;
5. a **separate Sol/GPT M3.3-E0 authorization**;
6. the **real E0** offline private parse;
7. **independent read-only E0 verification**;
8. a **separate Sol/GPT M3.3-E1 authorization**.

**No implementation path may infer owner authorization** from contract acceptance, a Git commit, a
tag, passing tests, a rehearsal token, a prior-stage token, the presence of `EV_ROOT`, or the
presence of a private catalog.

## 7. Governance surfaces this record touches

| Surface | Effect |
|---|---|
| `src/disclosure_drift/m3/**`, `src/disclosure_drift/pilot_policy.py`, `src/disclosure_drift/cli.py`, `tests/**` | The authorized executable envelope for I/R |
| [`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md) | Records this authorization and the §4 discharge of the `coverage_policy_version` open path question. **No other clause changes**, and every negative authorization survives |
| `Milestones/STATUS.md` | Implementation-authorization, stage, blocker, and next-action synchronization |
| `Docs/Decisions/decision_registry.md`, `Docs/decision_index.md`, `Docs/architecture_map.md`, `Docs/change_impact_map.md`, `Docs/m3/operator_runbook.md`, `Docs/m3/limitations_register.md`, `Milestones/milestone_03_master_plan.md`, `Milestones/contracts/README.md` | Current-state synchronization only |
| `Docs/m3/reviews/m3_3_i_r_rehearsal_<sha>.md` | The **implementer** rehearsal/evidence artifact — **not** an independent acceptance review |
| Decisions 067, 068, 069; both review artifacts; the fresh rereview artifact; the GR proposal | **Not modified.** Immutable accepted records and evidence |

**No migration, configuration, or CI file is changed by this authority, and no private evidence is
read or mutated.**

## 8. What this record does not authorize

It does **not**: execute the real offline metadata parse (**M3.3-E0**); progress from E0 to
**M3.3-E1**; construct a real candidate snapshot, freeze one, or run a real selection; construct a
real manifest or root (**M3.3-E2**); approve a root or begin **M3.4**; enable network access;
authorize an SEC request, reacquisition, or re-retrieval; authorize a migration; authorize editing
an accepted S4, S5, or S6 module; authorize reading, mutating, or even resolving the accepted real
private catalog or any M3.2 private evidence; supply **OR-6**, **OR-7**, **OR-9**, or **OR-11**;
pre-resolve Decision 023 **O1**; close any limitation (**D021-L2** and **D067-L1** remain
`ACTIVE`); move, retarget, delete, or recreate `m3.2-complete`; or create any tag.

**Stop and return to Sol/GPT** if accepted methodology is insufficient for a required field;
contributor membership needs a new substantive choice; a parser semantic change looks necessary; a
migration looks necessary; a sixteenth durable E0 table is required; `census_qa_metrics` or a
`census_index_*` write becomes unavoidable; accepted source evidence cannot support a required hard
constraint outside the existing fail-closed rules; Decision 023 O1 needs substantive resolution
rather than rehearsal referral; a real or private evidence path would be needed; network or HTTP
would be needed; a new acquisition would be needed; or a new owner methodology decision is
required. **None of these is solved by invention, and no test or gate is weakened.**

## 9. Next authorized action

**Implement and rehearse under this record, then return the result to Sol/GPT for a separate
read-only bug-discovery pass and a fresh independent A1 rehearsal acceptance.**

```text
M3_3_DECISION_070_I_R_IMPLEMENTATION_AUTHORIZATION_RECORDED
```
