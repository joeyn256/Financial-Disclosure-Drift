# Decision 027 — Milestone 3 Master Plan and Operational Readiness Design

**Version:** v0.2 (2026-07-31)
**Date:** 2026-07-31
**Status:** ACCEPTED — OWNER APPROVED 2026-07-31
**Type:** Planning and operational-readiness governance decision. **Not** a preregistration
deviation; `Docs/preregistration.md` is unchanged and was not edited. It changes no hypothesis,
cohort window, maturity gate, outcome definition, threshold, seed, methodology, identity, hash
preimage, migration byte, schema object, configuration value, CI workflow, test, or line of
production code. It records a **plan**, not an authorization to execute one.
**Supersedes:** nothing. **Amends:** nothing. Decisions 001–026 all retain the authority they
already hold.
**Related:** [Decision 013](decision_013_pilot_selection_mechanics.md) §§1, 5–8,
[Decision 015](decision_015_pilot_use_prohibition.md),
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md),
[Decision 018](decision_018_m23_s5_accession_selection_policy.md),
[Decision 019](decision_019_m23_s5_storage_to_pure_input_mapping.md) §9,
[Decision 020](decision_020_m23_s5_4_reserve_architecture.md) §19.1,
[Decision 021](decision_021_m23_s6_manifest_construction.md) v0.5 §§6–17, 19,
[Decision 022](decision_022_m23_s6_reserve_rank_applicability.md),
[Decision 023](decision_023_m23_s6_acceptance_and_path_ratification.md) §7,
[Decision 024](decision_024_m2_m3_boundary_governance.md) §§5–8,
[Decision 026](decision_026_milestones_0_1_2_final_closeout.md) §§12, 17–21;
[`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md);
[`Docs/m3/`](../m3/operator_runbook.md); [`Docs/leakage_register.md`](../leakage_register.md);
[`Docs/preregistration.md`](../preregistration.md) §25.
**Governs:** the Milestone 3 master plan, the operational-readiness design, the operator runbook
requirement, the mandatory offline rehearsal, the execution-receipt requirement, the frozen
operational-template set, the Milestone 3 limitations register, and the sequencing, validation,
model, commit, tag, and review policies for Milestone 3.

---

## 0. Revision history

**This record has been `ACCEPTED — OWNER APPROVED 2026-07-31` since v0.1. v0.2 does not change that,
and nothing here should be read as a claim that Decision 027 was previously unaccepted.** v0.2 is a
bounded correction pass issued by the project owner after the required independent review of the v0.1
planning package, in exactly the shape Decision 021 used for its own v0.1 → v0.5 corrections: the
record is revised in place, the corrections are recorded, and no second numbered decision is created.

**v0.2 supersedes the affected v0.1 operational-planning language and nothing else.** The formal
outcome, the acceptance, the Decision 024 phase map, the implementation-authorization status, and
every prohibition in v0.1 are unchanged.

| # | v0.1 language | v0.2 correction |
|---|---|---|
| 1 | M3.1's rehearsal covered snapshot freeze, S5 selection, reserves, sealing, S6 manifest construction, and root computation | **Corrected.** M3.1 rehearses **acquisition and operator operations only**. The execution scenarios move to **M3.3A**, which is where the production paths they exercise are first built. **No scenario may be placed in a phase that lacks the production path it exercises** (§6.1) |
| 2 | M3.2 was one acquisition window with a 10% contingency covering references that might appear between the dry run and the live run | **Corrected.** M3.2 becomes **two sequential windows** (§6.2). M3.2A retrieves only sources whose complete logical-request set is known before access; transport is then disabled, the bootstrap objects are frozen, the dependent references are **derived** from them, a second zero-request plan is produced, and a **second exact owner approval** is obtained before M3.2B. **The contingency is removed** — each window's count is derived, not estimated |
| 3 | M3.3 was one phase freezing the real snapshot | **Corrected.** **M3.3A** implements the candidate-snapshot builder under a bounded contract and rehearses it offline; **M3.3B** performs the real freeze and deterministic real execution only after M3.3A passes (§6.3) |
| 4 | M3.4 was "documentary" if no recording path was authorized | **Corrected.** M3.4 **always requires a bounded contract** (§6.4). **M3.4A** implements and independently validates a minimal approval-recording entry point against synthetic catalogs; **M3.4B** invokes it once, after explicit exact-hash approval. **Manual SQL against the real catalog is prohibited** |
| 5 | 69 required closed quarters, subtotal 74, plan hash `25257d75…`, and 888 maximum attempts were recorded as derived values | **Withdrawn.** Those values were faithful to the accepted planner but **not** to Decision 013 §1, which requires coverage through the **closed 2026 Q2** quarter. The discrepancy is recorded in §15.1 and must be diagnosed by the bounded M3.1 contract. **No count is frozen in this record or in the master plan** |
| 6 | `A_max = 1 + MAX_REDIRECT_DEPTH + max_transient_retries + 1 = 12`, with `maximum physical attempts = planned × 12` | **Withdrawn.** That bound was inferred by reading three guards and was never tested, and it assumes retries, redirects, and cooldowns compose additively rather than multiplicatively. The maximum reachable physical attempts is a **property of the implemented response-policy state machine** and must be derived and independently tested per route, not asserted in a plan (§16) |
| 7 | The receipt carried both `receipt_id` and an optional `receipt_content_sha256` | **Corrected.** **One** receipt integrity identity: `receipt_id = SHA256(canonical receipt bytes with `receipt_id` omitted)`. `receipt_content_sha256` is removed |
| 8 | Receipt fields were "optional unless marked required", then validated as mandatory | **Corrected.** Every field is classified as **required in all modes**, **conditionally required for named modes**, or **prohibited for named modes** |
| 9 | Rehearsal scenarios recorded simulated traffic in the receipt's actual-network fields | **Corrected.** In `rehearsal` and `dry_run` modes the actual logical and physical **network** counts are **`0`**; simulated totals belong to the rehearsal evidence report |
| 10 | Completed evidence packets were to "live in the repository as documentation" | **Corrected.** Two-layer model (§10.1): the repository tracks **blank templates**, planning and governance records, the limitations register, and a **public evidence index** carrying artifact type, phase, status, SHA-256, and a non-sensitive reference identifier. **Completed operational evidence lives in an owner-controlled private evidence root outside the repository** |
| 11 | "Any regeneration produces a new `root_manifest_sha256`" | **Withdrawn as false.** It contradicts the determinism the manifest exists to provide. **Unchanged governed state plus byte-identical canonical serialization produces the same root**, and an independently re-derived identical root **remains the same approved value** (§10.2) |

**What v0.2 does not change.** The formal outcome
`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`; the acceptance itself; the Decision 024
§5.1 phase map M3.1–M3.5; implementation authorization `NO`; network authorization `NO`; the
requirement for an operator runbook, a mandatory offline rehearsal before the first SEC request, and
one execution receipt per live command; the frozen template set; the seeded limitations register and
its rule that nothing is closed; the sequential model and validation policy; the commit and tag
policy and the frozen future tag names; the focused independent-review policy; the prohibition on
inventing request-volume values; the non-contamination rule; and every negative confirmation in §25.

**Next authorized action after v0.2:** `INDEPENDENT_M3_MASTER_PLAN_REREVIEW`.

## 1. Why this record exists

Milestones 0, 1, and 2 are formally closed (Decision 026, `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`),
and Decision 026 §18 makes `MILESTONE_3_MASTER_PLANNING` the next authorized action. Decision 024
§5.1 already fixes *what* the five Milestone 3 phases are. What did not exist was the plan that says,
for each of them, exactly what the inputs are, what the outputs are, what the network permission is,
what stops the phase, what evidence it must produce, how it is validated, how it recovers, what
token completes it, and what may be committed and tagged.

Milestone 3 is the first part of this project that touches a live external service and produces a
real research artifact. Every prior milestone could be re-run from nothing. **Milestone 3 cannot:**
a request sent is sent, a rate limit tripped is tripped, and an approved root is approved. That
asymmetry is why the plan is written, reviewed, and accepted **before** the first request rather
than discovered during it.

**This record is governance only.** It grants no implementation authority of any kind.

## 2. The exact Milestones 0–2 closeout baseline

Verified live at the start of this planning session with `scripts/context_snapshot.sh` and direct
Git inspection, never assumed from a document:

| | |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| **Closeout commit (HEAD at session start)** | `034bbc1fa62c353602291f7f863092eb595f3c51` |
| Subject | `Close Milestones 0 1 and 2` |
| Parent (the Decision 026 §2 closeout baseline) | `65a57f40ddc92853ba756bb8eea23c2b64fdfff2` — `Complete pilot data dictionary coverage` |
| `origin/main` | `034bbc1fa62c353602291f7f863092eb595f3c51` |
| `HEAD == origin/main` | yes |
| Working tree | clean — nothing staged, nothing unstaged, nothing untracked |
| **Decision 026 status** | `ACCEPTED — OWNER APPROVED 2026-07-31` |
| **Decision 026 formal outcome** | `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED` |
| `m0-complete` | annotated → `034bbc1fa62c353602291f7f863092eb595f3c51` |
| `m1-complete` | annotated → `034bbc1fa62c353602291f7f863092eb595f3c51` |
| `m2-complete` | annotated → `034bbc1fa62c353602291f7f863092eb595f3c51` |
| Migration chain | contiguous `0001`–`0013`; nothing beyond `0013` |
| Migration `0013` normative region | 10939 bytes, 186 lines, `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595` |
| Implementation authorization | `NO` — every stage contract closed; no Milestone 3 contract exists |

Earlier accepted tags, unchanged and immutable:

| Tag | Target |
|---|---|
| `m2.2-r3-complete` | `d9e09a556e9a1758bd995d990e93de595c9417a4` |
| `m2.3-s3.2-complete` | `5fb8e27806f918daf9a60b734486de2937669087` |
| `m2.3-s4-complete` | `e7157aa55f1af268cafb4f6dcb6070b025255e07` |
| `m2.3-s5-complete` | `51837c0bd7e32ff09538020a425d2abd61722ded` |
| `m2.3-s5.4-complete` | `903f4ccfb9b393de8e9a696af491b42706a510f2` |
| `m2.3-s6-complete` | `5c53412d820fe20a7bd727eac333ae2fb8724cd6` |

**No tag was created, moved, re-pointed, or deleted by this session.**

## 3. Decision 024 remains controlling for the M2 → M3 obligation transfer

**Decision 024 is the controlling record for where Milestone 2 implementation ends and where the
obligations formerly called S7–S10 now live.** Its §5.1 phase map, its §5.2 seven-column
traceability table, its §5.3 preservation confirmation, its §6 inherited authority, its §7 authority
separation, and its §8 five entry conditions all stand exactly as approved.

**This record adds no phase, removes none, renames none, and reorders none.** It plans the five
phases Decision 024 already fixed. Where this record and Decision 024 could be read to disagree
about *what a phase is*, Decision 024 controls.

## 4. Decision 026 remains controlling for the Milestones 0–2 closeout

**Decision 026 is the controlling record for whether Milestone 0, Milestone 1, and Milestone 2 are
closed, what closure covers, which tags exist, and what is authorized next.** Its §12 keeps the
inherited limitations register active; its §§19–20 bound what this planning session may and may not
do; its §21 confirms that closure granted no Milestone 3 implementation authority.

**This record operates strictly inside Decision 026 §19** and does none of the nine things §20
prohibits.

## 5. The exact M3.1–M3.5 phase map

As fixed by Decision 024 §5.1 and planned in
[`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md):

| Phase | Former | Scope | Network permission | Completion token |
|---|---|---|---|---|
| **M3.1** | S7 | **Acquisition-path rehearsal** and Gate F | **M3.1A NONE; M3.1B ZERO LIVE REQUESTS** | `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` |
| **M3.2** | S8 | Controlled metadata-only SEC acquisition in **two sequential windows**, and Gate H | **CONTROLLED AND EXPLICITLY AUTHORIZED, per window** | `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` |
| **M3.3** | S9 | **Candidate-snapshot builder and execution rehearsal**, then the frozen real snapshot, deterministic selection, persistence, reconstruction, replay, and exact real manifest construction | **OFF** | `M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL` |
| **M3.4** | S10 | **Accepted approval entry point**, then exact root-hash owner approval | **NONE** | `M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE` |
| **M3.5** | — | Integrated real-pilot acceptance and the Milestone 3 checkpoint | **NONE** unless a separate bounded correction contract authorizes otherwise | `M3_5_REAL_PILOT_ACCEPTED_MILESTONE_3_COMPLETE` |

**Sequential execution only.** No phase overlaps another, no concurrent sessions are recommended or
permitted, and no parallel worktree is used.

## 6. The frozen internal subdivisions

**M3.1, M3.2, M3.3, and M3.4 each run in two sequential internal parts. This creates no new
milestone and no new phase — the Decision 024 §5.1 phase map is unchanged.** Each subdivision exists
for the same structural reason: the second part depends on something the first part must first build,
freeze, or prove, and merging them would let an unproven path reach a real artifact.

### 6.1 M3.1 — acquisition-path rehearsal, then Gate F

**M3.1A — offline acquisition and operator rehearsal.** Network permission **NONE**. Completion token
`M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED`. **No annotated tag** — M3.1A is an internal part of M3.1,
not an independently accepted phase, and §13 forbids tagging a non-phase state.

It rehearses **only acquisition and operator operations**:

request planning and ordering; request-budget enforcement; rate limiting; retries, redirects,
`Retry-After`, cooldowns, block pages, and terminal responses; route allowlist and denylist
enforcement; raw storage and provenance; duplicate and changed-body handling; parser and
schema-drift behaviour; catalog transactionality; interruption and recovery; execution receipts and
prohibited-field scanning.

**M3.1 must not rehearse or implement candidate-snapshot construction, snapshot freeze, S5 selection,
reserves, dispositions, selection-result sealing, S6 manifest construction, or root computation.**
Those paths do not exist at M3.1 — no candidate-snapshot builder exists anywhere in the repository —
so a rehearsal claiming to exercise them would be exercising nothing.

**The general rule, frozen here: no scenario may be placed in a phase that lacks the production path
it exercises.** This is the v0.1 defect that produced the correction: v0.1 placed snapshot, selection,
reserve, sealing, and manifest scenarios in M3.1A while M3.1's own non-scope prohibited touching the
builder.

**M3.1B — Gate F and zero-request readiness.** Network permission **ZERO LIVE REQUESTS**. Completion
token `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`, which is M3.1's token. M3.1B may not
begin until M3.1A has passed.

### 6.2 M3.2 — two sequential acquisition windows

**M3.2 remains one phase, with two sequential windows.** Gate H integrates both.

- **M3.2A** retrieves **only bootstrap sources whose complete logical-request set is derivable before
  any network access.**
- **After M3.2A, in order:** disable transport; freeze and identify the exact bootstrap raw objects;
  **derive** the historical-submission references from the frozen bulk-submissions object; **derive**
  the explicit entity reconciliation set; produce a **second zero-request request plan**; obtain a
  **second exact owner-approved budget and hard ceiling**.
- **M3.2B** retrieves **only** the dependent historical-submission and entity-submission requests
  enumerated by that second plan.

**Each window carries its own plan identity, budget, hard ceiling, owner approval, execution
receipts, and stop-before-overflow enforcement.** A window's approval never covers the other window.

**No general contingency allowance is frozen, and the v0.1 10% contingency is withdrawn.** Each
window's count is **derived from explicit inputs and frozen source objects**, not estimated with
slack. The contingency existed only because v0.1 tried to acquire, in one window, requests whose
count depended on an object it had not yet retrieved; the two-window split removes the cause instead
of padding for it.

### 6.3 M3.3 — builder rehearsal, then real deterministic execution

- **M3.3A** implements the **candidate-snapshot builder** under its own bounded contract and performs
  a synthetic or real-shaped **offline execution rehearsal**, independently reviewed, covering:
  snapshot construction and freeze; every Decision 019 snapshot-validation obligation; plain/dashed
  accession disagreement; feasible and fail-closed selection; reserves and dispositions; persistence
  and reconstruction; write-free replay; selection-result sealing; S6 manifest construction;
  file/database atomicity; identical-root replay; and Decision 023 **O1** behaviour.
- **M3.3B** performs the **real snapshot freeze and deterministic real execution** — and only after
  M3.3A passes its review.

### 6.4 M3.4 — accepted approval entry point, then the exact-root decision

**M3.4 always requires a bounded contract. It is never purely documentary.**

- **M3.4A** implements and independently validates a **minimal approval-recording application entry
  point** against **synthetic catalogs**.
- **M3.4B** presents the exact real root to the owner and invokes that accepted entry point **once**,
  only after an explicit exact-hash approval.

**Manual SQL against the real catalog is prohibited.** v0.1 allowed M3.4 to be "documentary" if no
recording path was authorized, which would have left hand-written SQL as the only way to write
`approved_root_sha256` — editing by hand the exact artifact whose integrity the milestone exists to
protect, and navigating the accepted migration-`0013` guards manually. That is closed.

## 7. The operator-runbook requirement

**A documentation-first operator runbook must exist and be reviewed before any live access.**
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) is that runbook. It is Mac-specific,
sequential, and paste-ready, and it is **documentation only**: every command it names is labelled
either `AVAILABLE NOW` or `PLANNED — NOT YET IMPLEMENTED`, with the planned commands carrying their
exact intended interface contract so a later bounded contract implements the interface the runbook
describes rather than inventing one.

**No command that does not yet exist may be presented as available.** A runbook that overstates the
repository is worse than no runbook, because it is followed.

## 8. The mandatory offline rehearsals

**Two offline rehearsals are required, each immediately before the live or real work it de-risks, and
each in the phase that owns the production paths it exercises.** Both are specified in
[`Docs/m3/offline_rehearsal_spec.md`](../m3/offline_rehearsal_spec.md). Neither opens a socket, both
use scripted responses and synthetic fixtures only, and both inject deterministic clock inputs
wherever an operational timestamp is required.

**The M3.1A acquisition rehearsal must pass before the first SEC request is sent.** It covers, at
minimum: all-success acquisition; retry then success; `Retry-After`; cooldown and block-page
termination; stop-before-budget-overflow; allowlist and denylist enforcement; unknown-field
retention; blocking schema drift; byte-identical duplicate reconciliation; changed-body
new-observation behaviour; raw-store and catalog interruption recovery; and receipt non-contamination
with a non-vacuous prohibited-field scan.

**The M3.3A execution rehearsal must pass before the real snapshot is frozen.** It covers, at
minimum: deterministic snapshot freeze; snapshot-validation refusal; feasible selection; infeasible
and node-limit fail-closed behaviour; reserve and disposition totality; reconstruction-mismatch
refusal; seal and manifest atomicity; and identical replay with Decision 023 **O1** handling.

**Neither rehearsal has been implemented and neither has been run**, and this record authorizes
neither. They are specified so that the bounded M3.1 and M3.3 contracts can implement and run them.

## 9. The execution-receipt requirement

**Every future live command must produce exactly one machine-readable execution receipt**, designed
by [`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md). A live command that
produces no receipt is an incomplete command, and its phase does not pass.

Receipts are **operational evidence**. They exist so that "what did the live run actually do" has an
answer that does not depend on a terminal scrollback or a chat transcript.

## 10. The frozen operational-template set

Eight templates are frozen in planning form under [`Docs/m3/templates/`](../m3/templates/request_budget.md):

| Template | Purpose |
|---|---|
| `request_budget.md` | Per-window, route-by-route planned counts, the derived maximum physical attempts, retry allowance, hard ceiling, expected raw objects, expected elapsed window, and the exact owner approval |
| `gate_f_checklist.md` | The Gate F pass/fail record: rehearsal, identity, network default, allowlist, denylist, two dry runs, identical plan hashes, budget, ceiling, operator readiness, owner approval |
| `gate_h_checklist.md` | The post-acquisition Gate H record: actual versus planned, route compliance, response totals, raw-store and provenance completeness, drift, retry compliance, no overflow, no leakage, network disabled afterward |
| `schema_drift_incident.md` | The fail-closed drift incident record and its owner ruling |
| `interrupted_run_recovery.md` | The interrupted-run state reconstruction, safe-resume determination, and duplicate-prevention proof |
| `real_snapshot_evidence_packet.md` | The complete M3.3 evidence packet, ending in an explicit no-approval statement |
| `root_hash_approval_packet.md` | The M3.4 exact-root approval or rejection, with the exact-hash-only clause |
| `evidence_index.md` | **New at v0.2.** The public index of private evidence artifacts: type, phase, status, artifact SHA-256, and a non-sensitive reference identifier |

"Frozen in planning form" means the field set is fixed by this record; a template is filled in by the
phase that uses it, never rewritten by it. Changing a template's field set requires a new accepted
decision.

### 10.1 Evidence storage — the two-layer model

**The repository is public. Completed operational evidence is not committed to it.**

**Tracked publicly:** blank templates; planning and governance records; the limitations register;
non-sensitive status and navigation; and the **evidence index**, carrying artifact type, phase,
status, the completed artifact's own SHA-256, and a non-sensitive reference identifier.

**Held privately, in an owner-controlled evidence root outside the repository:** execution receipts;
request budgets; Gate F and Gate H packets; interrupted-run records; schema-drift records;
real-snapshot evidence packets; root-approval packets; raw objects; catalogs; candidate, selection,
reserve, and manifest artifacts; and every unpublished governed identity.

The operator computes a private artifact's digest with `shasum -a 256 <private-evidence-file>` and
enters **only the digest and non-sensitive metadata** in the public index. **No absolute private path
is ever recorded publicly.** Completed private evidence requires a **separate owner-controlled
backup** — a private root with no backup is a single point of loss for the only record of a run that
cannot be re-run.

**A public acceptance decision may reference the SHA-256 of a private evidence artifact. It may not
expose an unpublished root or any substantive row.**

v0.1 said completed packets would "live in the repository as documentation." That would have written
an unpublished `root_manifest_sha256` into permanent public history while publication authority is
`NOT_AUTHORIZED` — a contradiction with v0.1's own publication boundary, and irreversible once
pushed. **This session does not edit `.gitignore`;** creating the private root's ignore entry is a
configuration change requiring its own authorization, and is recorded as a follow-up.

### 10.2 Deterministic root re-derivation

**Frozen, replacing the v0.1 claim that any regeneration necessarily creates a new root:**

1. **Unchanged governed state plus byte-identical canonical serialization produces the same
   `root_manifest_sha256`.** This is the determinism the manifest exists to provide, and it is
   already required by the two-clean-rebuilds obligation.
2. **An independently re-derived identical root remains the same approved value.** Re-deriving does
   not invalidate an approval, and does not require a new packet.
3. **A differing root, changed governed state, or a superseding manifest requires a new packet and a
   new explicit owner decision.**

The v0.1 wording conflated "regenerated" with "different." Only the second invalidates an approval.

## 11. The Milestone 3 limitations register

[`Docs/m3/limitations_register.md`](../m3/limitations_register.md) is the Milestone 3 limitations
register. It is **seeded with every inherited limitation** — Decision 020 §19.1's five, Decision 021
§19's items 1–10 (with item 11 recorded as closed at v0.5), Decision 022's applicability boundary,
Decision 023 §7's **O1**–**O4**, Decision 001's required final literature refresh, Decision 018 §14's
deferred difficult-or-nonstandard-package quota, and Milestone 0's standing limitations — plus new
Milestone 3 entries for platform and filesystem assumptions, synthetic-fixture limitations,
first-real-instance uncertainty, live SEC availability, rate-limit behaviour, schema-drift
uncertainty, interrupted-run uncertainty, operator error, receipt-schema evolution, and
request-budget estimation uncertainty.

**No inherited limitation is marked closed by this record, and none may be closed merely because a
phase passed.** Decision 026 §12 is unchanged: closing a milestone does not close its limitations.

## 12. The sequential model and validation policy

**Model assignment.**

- **Claude Opus, Max effort** — architecture, phase contracts, owner decisions, consequential
  methodology, focused independent reviews, exact-root approval preparation, and final integrated
  acceptance.
- **Claude Sonnet, High or Max effort** — bounded implementation, tests, CLI work, separately
  authorized migrations, operator tooling, and narrow corrections.
- **Haiku is placed nowhere on the Milestone 3 critical path.**

**Validation cadence.**

- **During implementation:** targeted tests and touched-file checks only.
- **At the end of each phase:** one full suite and every required repository gate.
- **Independent Opus review:** only at consequential phase boundaries.
- **At M3.5:** the final integrated Milestone 3 acceptance review.

**Sequential execution only.** No concurrent Claude sessions, no parallel worktrees, and no
overlapping implementation phases are recommended or permitted.

## 13. Commit and tag policy

**Commit.** One implementation commit per accepted phase by default. An intermediate implementation
checkpoint is allowed **only** where the phase plan explicitly justifies it **and** the owner
separately authorizes it. Governance-only records may take a separate bounded governance commit. No
noisy sequence of mechanical checkpoint commits.

**Tag.** Annotated tags only; only after independent phase acceptance; never for an unreviewed
implementation state; **none in this session**. The future tag names are frozen by the master plan
after confirming against every existing tag that none conflicts: `m3.1-complete`, `m3.2-complete`,
`m3.3-complete`, `m3.4-complete`, and `m3-complete`. **M3.1A takes no tag.**

## 14. The focused independent-review policy

A Milestone 3 review answers **the specific phase-acceptance question** it was convened for. It does
not repeat the complete Milestones 0–2 audit unless a new finding gives a concrete reason to.

The independence discipline of Decisions 022 §9 and 023 §2 carries forward without change: **no
reviewer may review work it wrote.**

## 15. Request-volume values may not be invented, and none is frozen here

**No integer request count may be invented anywhere in Milestone 3, and no count is frozen in this
record or in the master plan.** Every count is produced by the accepted planner from explicit inputs,
at the time the plan is produced, and approved by the owner as an exact integer for that window.

v0.1 recorded a set of derived counts and a plan hash. **They are withdrawn** — not because they were
invented, but because they were faithful to the accepted planner rather than to accepted authority
(§15.1), and because freezing a planner-dependent value into a governance record makes that record
false the moment the planner is lawfully corrected.

### 15.1 `CURRENT_PLANNER_DISCREPANCY`

**The accepted planner and accepted authority currently disagree about the 2026 Q2 quarter, and the
disagreement is unresolved.**

[Decision 013](decision_013_pilot_selection_mechanics.md) §1 fixes the as-of date at **2026-06-30**
and states that **coverage extends through the closed 2026 Q2 quarter**, with
`include_open_quarter = false` and no open-2026-Q3 retrieval. The milestone plan's Gate G rule reads
"quarters ending on or before the as-of date are required."

The accepted planner, at exactly those inputs, classifies **2026 Q2 as the provisional open quarter**
— because 2026-06-30 falls *inside* 2026 Q2 — and, with `include_open_quarter = false`, **excludes
it**. Its last required closed instance is therefore 2026 QTR1, not 2026 QTR2.

2026 Q2 satisfies both conditions simultaneously: it **ends on** the as-of date and it **contains**
the as-of date. The planner resolves that tie one way; Decision 013 §1 states the other.

**This record does not resolve it, and it does not change Decision 013**, which remains byte-unchanged
and controlling.

**The bounded M3.1 contract must diagnose this discrepancy.** Until the planner's behaviour agrees
with accepted authority, or a new owner-approved decision changes that authority, **Gate F cannot
pass** — because a request plan that disagrees with the accepted coverage cutoff is not a plan the
owner can approve a budget against.

### 15.2 Where an exact count cannot yet be derived

Where a real candidate set, a frozen source object, or current SEC state is required, the master plan
writes

```
EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN
```

and, for each such count, it must:

1. **provide the exact formula** that produces the count;
2. **identify every count dependency** by name;
3. **define the future zero-request planning command** that resolves it, with its exact intended
   interface;
4. **define a hard request ceiling** that binds regardless of what the formula resolves to;
5. **require explicit owner approval of the exact budget and ceiling before network enablement**, per
   window.

The two dependent M3.2 routes — `sec_submissions_historical`, whose count depends on the
historical-file references named inside the bulk archive, and `sec_submissions_entity`, whose count
depends on the reconciliation set — are resolved by the **second** zero-request plan produced after
M3.2A freezes the bootstrap objects (§6.2), not by an estimate.

## 16. Maximum physical attempts is derived from the implemented state machine

**Withdrawn from v0.1:** `A_max = 1 + MAX_REDIRECT_DEPTH + max_transient_retries + 1 = 12`; every
formula treating retries, redirects, and cooldowns as simply additive; `maximum physical attempts =
planned × 12`; the 10% contingency; and every hardcoded derived physical-attempt total.

That bound was inferred by reading three guards in the accepted response-policy loop. It was never
tested, and it assumes the three mechanisms compose additively when the loop structure permits them
to interact. **A worst-case attempt bound is a property of the implemented state machine, not a
constant a plan may assert.**

**The future implementation must instead:**

1. **derive the maximum reachable physical attempts per route** from the implemented response-policy
   state machine as written;
2. **count every redirect hop, every retry, and every controlled post-cooldown request** as a
   physical attempt;
3. **test the worst reachable path independently**, rather than deriving the bound only by reading;
4. **produce an exact per-window integer**;
5. **obtain explicit owner approval** of that integer;
6. **refuse the request that would exceed the approved ceiling** — stop before, never after;
7. **never increase a ceiling during a running window.**

## 17. Operational receipts are outside the accepted S5 and S6 substantive identity graphs

**Confirmed.** The accepted substantive identity graph is fixed by Decision 021 §§6–10: the
fourteen-field `selection_result_sha256` preimage, the eight component digests and their preimages,
`root_manifest_sha256`, the `manifest_id` derivation, the eight circularity exclusions, and the §10.1
commitment closure. **No execution receipt, and no receipt digest, appears anywhere in any of them.**

An execution receipt is an operational artifact of the *command that ran*, not of the *content that
was produced*. The two are deliberately disjoint.

## 18. Nothing operational may contaminate a governed identity

**Confirmed, and stated as a prohibition.** No execution receipt, receipt digest, receipt identifier,
operational timestamp, request count, response total, attempt total, elapsed duration, filesystem
path, log location, SEC identity, operator name, machine identity, or other operational state may
enter, alter, or be committed by:

- **candidate identity** — the frozen candidate snapshot and its declared component digests;
- **selection identity** — `selection_run_id`, `selection_input_sha256`, and the S5 run identity;
- **`selection_result_sha256`**;
- **the eight S6 component digests**;
- **`root_manifest_sha256`**;
- **`manifest_id`**.

This restates rather than extends the accepted design: Decision 021 §8.4 already requires the six
identity arguments to be supplied explicitly and forbids inferring them from Git, the environment,
the interpreter, or the working tree, and Decision 013 §7 already excludes `generated_at` from the
content hash. **A receipt is read by people, never by a digest.**

## 19. No full identity, secret, or restricted payload may appear in a receipt

**Confirmed, and stated as a prohibition.** No execution receipt may contain the full SEC user-agent
identity, an email address, a secret, an API token, a cookie, an authorization header, a raw response
body, an absolute personal path, a candidate row, a selected row, a reserve row, filing text, an
outcome value, or any other unpublished substantive payload not already represented by a governed
identity.

The corresponding positive rule is that a receipt carries **counts, classifications, versions,
identifiers, and statuses** — the facts an auditor needs and an attacker cannot use.

## 20. No Milestone 3 implementation authority is granted

**This record grants none.** It is a plan. Every one of Decision 024 §8's five entry conditions still
applies in full to every Milestone 3 phase:

1. a separate accepted governance record where the phase requires one;
2. a bounded implementation contract for that phase;
3. explicit owner authorization;
4. exact path authorization;
5. satisfaction of that phase's inherited prerequisite gates.

**Implementation authorization is `NO` for every Milestone 3 phase.** No Milestone 3 contract exists,
none is created here, and **planning a phase is not authorization to begin it** — the same
distinction Decision 024 §8 and Decision 026 §21 already draw.

Specifically, and for the avoidance of any doubt: this record does **not** enable SEC network access,
acquire live metadata, create a real candidate snapshot, run a real pilot, construct a real manifest,
approve a root, or publish anything. None of those has occurred.

## 21. Formal outcome

```
M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED
```

## 22. Checkpoint authorization

**v0.1.** The project owner authorized, for the original planning recording and no other purpose:
one planning/governance commit containing this record, the master plan, the `Docs/m3/` documentation
pack, and the navigation and status updates they require; and one push to `origin/main`. That
checkpoint is commit `f00b3adae542b17451cca70b7504dca1937cf64e`, "Define Milestone 3 master plan".

**v0.2.** The project owner authorizes, for this bounded correction and no other purpose:

1. **one governance-only correction commit** containing this revision, the corrected planning
   package, the new evidence-index template, and the navigation and status updates they require;
2. **one push to `origin/main`**.

**No tag is authorized in either session.** No existing tag is moved, replaced, re-pointed, or
recreated. CLAUDE.md rule 13 applies independently to everything beyond this list.

## 23. The next authorized action

```
INDEPENDENT_M3_MASTER_PLAN_REREVIEW
```

**The v0.1 `INDEPENDENT_M3_MASTER_PLAN_REVIEW` has run**; its corrections are recorded in §0 and
applied throughout this record and the planning package. Because those corrections changed phase
subdivisions, request-volume policy, receipt semantics, and evidence storage, **a fresh independent
rereview is required before the bounded M3.1 contract may be drafted** — the same discipline
Decision 021 applied across v0.1–v0.5.

A focused, fresh Opus review — performed by a session that authored neither v0.1 nor the v0.2
corrections — must verify that:

- all Decision 024 obligations are represented **exactly once**;
- each M3 phase has complete inputs, outputs, permissions, stop conditions, validation, recovery,
  tokens, and checkpoint policy;
- **every corrected subdivision is internally consistent** — M3.1A rehearses only acquisition,
  M3.2's two windows each carry their own plan and approval, M3.3A precedes M3.3B, and M3.4 is never
  documentary;
- **no scenario is placed in a phase that lacks the production path it exercises**;
- the operator runbook is executable as documentation **without pretending planned commands already
  exist**;
- **no withdrawn count, plan hash, `A_max`, or contingency survives anywhere as an accepted value**;
- the `CURRENT_PLANNER_DISCREPANCY` is recorded and unresolved, and Decision 013 is unchanged;
- request budgeting is derived per window or explicitly deferred to a zero-request plan;
- execution receipts cannot contaminate accepted identities, and carry exactly one integrity
  identity;
- the two-layer evidence model is applied consistently across the master plan and every template;
- templates and limitations are complete;
- **no implementation authority was granted**;
- **no live access occurred.**

## 24. Only after that rereview may the M3.1 contract be created

**Only after `INDEPENDENT_M3_MASTER_PLAN_REREVIEW` passes may the owner authorize a separate session
to draft the bounded M3.1 implementation contract.** That contract is itself not implementation
authority — it is one of Decision 024 §8's five conditions, and the others must also hold.

**Drafting the M3.1 contract is not authorized by this record**, and this session does not begin it.

## 25. Negative confirmations

True at the moment this record is accepted, and verified against the repository rather than assumed:

- **No SEC network access occurred**, and none is authorized.
- **No live metadata was acquired.**
- **No real candidate snapshot exists**, and no candidate-snapshot builder exists.
- **No real pilot-selection run exists.**
- **No real manifest exists** — every accepted S6 artifact is a fixture-only `proposed` manifest.
- **No root hash was approved**; `approved_root_sha256` has never been written.
- **Nothing was published**, and no publication authority exists anywhere in the repository.
- **No production catalog database exists.**
- **No Milestone 3 implementation path exists** — no contract, module, test, migration, CLI surface,
  network allowlist, request-plan command, or execution receipt.
- **Neither offline rehearsal has been run**, no Gate F has passed, and no Gate H has passed.
- **No migration beyond `0013` exists.**
- **No M3.1 contract has been drafted or begun**, and no phase contract of any kind exists.
- Verified again at v0.2, on the same repository, with every frozen path byte-unchanged.

## 26. What this record does not change

Recorded so that no later session reads a planning decision as a licence:

**production code; tests; migrations; configuration; CI workflows; `Docs/preregistration.md`;
`Docs/sec_data_dictionary.md`; Decisions 001–026; every completed contract; hypotheses; cohort
windows; maturity gates; outcome definitions; thresholds; the bootstrap seed `20260725`; SEC source
policy; identifiers; temporal policy; leakage controls; selection methodology; reserves;
dispositions; hash preimages; manifest identities; digests; crosswalk rows and their totals; and S4,
S5, or S6 behaviour.**

Decision 021 remains controlling for the S6 architecture, Decision 022 for crosswalk item-46
applicability, Decision 023 for S6 acceptance and limitations O1–O4, **Decision 024 for the
Milestone 2 → Milestone 3 obligation transfer**, Decision 025 for the integrated-audit documentation
corrections, and **Decision 026 for the Milestones 0–2 closeout**.

## 27. Reason

Every earlier milestone in this project could be undone by deleting a file and running the suite
again. Milestone 3 cannot. The first live request is the first act this repository takes that the
repository cannot take back, and the exact-root approval is the first act the *owner* takes that the
owner cannot take back. Planning both before either happens is not ceremony; it is the only point at
which the design is still cheap to change.

The three things this plan insists on are deliberately unglamorous. **Rehearse the whole workflow
offline first**, because the failure modes that matter — an interruption between a raw-store write
and a catalog commit, a schema change mid-run, a duplicate object, a partial file — are exactly the
ones a first live run is worst at producing on demand. **Write a receipt for every live command**,
because "what did it actually do" must have an answer that outlives a terminal window. **Keep the
receipt out of every governed identity**, because the moment a timestamp or a request count reaches a
digest, the artifact stops being reproducible and starts being a recording.

What is deliberately *not* claimed here matters as much. Nothing has been retrieved, rehearsed,
acquired, snapshotted, selected, manifested, approved, or published. This record is a plan for doing
those things carefully, and the authorization to do any of them is not in it.

No deviation from Decisions 001–026 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.
