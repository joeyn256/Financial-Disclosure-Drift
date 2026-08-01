# Decision 027 — Milestone 3 Master Plan and Operational Readiness Design

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
| **M3.1** | S7 | Gate F and controlled-live readiness | **M3.1A NONE; M3.1B ZERO LIVE REQUESTS** | `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` |
| **M3.2** | S8 | Controlled metadata-only SEC acquisition and Gate H | **CONTROLLED AND EXPLICITLY AUTHORIZED** | `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` |
| **M3.3** | S9 | Frozen real snapshot, deterministic selection, persistence, reconstruction, replay, and exact real manifest construction | **OFF** | `M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL` |
| **M3.4** | S10 | Exact root-hash owner approval | **NONE** | `M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE` |
| **M3.5** | — | Integrated real-pilot acceptance and the Milestone 3 checkpoint | **NONE** unless a separate bounded correction contract authorizes otherwise | `M3_5_REAL_PILOT_ACCEPTED_MILESTONE_3_COMPLETE` |

**Sequential execution only.** No phase overlaps another, no concurrent sessions are recommended or
permitted, and no parallel worktree is used.

## 6. The M3.1A / M3.1B planning subdivision

**M3.1 is planned in two sequential internal parts. This creates no new milestone and no new phase.**

- **M3.1A — offline operator-workflow rehearsal.** Network permission **NONE**. Completion token
  `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED`. **No annotated tag** — M3.1A is an internal part of
  M3.1, not an independently accepted phase, and the tag policy (§13) forbids tagging an unreviewed
  or non-phase state.
- **M3.1B — Gate F and zero-request readiness.** Network permission **ZERO LIVE REQUESTS**.
  Completion token `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`, which is M3.1's token.

M3.1B may not begin until M3.1A has passed. The subdivision exists because the two parts have
different network permissions and different failure meanings: a failed rehearsal is a design finding,
and a failed Gate F is a readiness finding.

## 7. The operator-runbook requirement

**A documentation-first operator runbook must exist and be reviewed before any live access.**
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) is that runbook. It is Mac-specific,
sequential, and paste-ready, and it is **documentation only**: every command it names is labelled
either `AVAILABLE NOW` or `PLANNED — NOT YET IMPLEMENTED`, with the planned commands carrying their
exact intended interface contract so a later bounded contract implements the interface the runbook
describes rather than inventing one.

**No command that does not yet exist may be presented as available.** A runbook that overstates the
repository is worse than no runbook, because it is followed.

## 8. The mandatory offline rehearsal before the first SEC request

**The complete offline rehearsal specified in
[`Docs/m3/offline_rehearsal_spec.md`](../m3/offline_rehearsal_spec.md) must be implemented and must
pass before the first SEC request is sent.** It opens no socket, uses scripted responses and
synthetic fixtures only, and injects deterministic clock inputs wherever an operational timestamp is
required.

It exercises the whole workflow end to end — planned request generation, deterministic request
ordering, request-budget construction, deterministic rate limiting, retry scheduling, response
classification, content-addressed raw storage, raw-object provenance, duplicate response handling,
schema-drift refusal, snapshot freezing, entity and accession selection, reserves, dispositions, S5
persistence, S5 reconstruction, S5 replay, selection-result sealing, S6 manifest construction,
canonical serialization, manifest verification, identical replay, injected interruption, transaction
rollback, file and database atomicity, interrupted-run recovery, execution-receipt production, and
the proof that operational receipt content enters no governed identity.

**The rehearsal was not executed in this session and this record does not authorize its execution.**
It is specified so that a later bounded M3.1 contract can implement and run it.

## 9. The execution-receipt requirement

**Every future live command must produce exactly one machine-readable execution receipt**, designed
by [`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md). A live command that
produces no receipt is an incomplete command, and its phase does not pass.

Receipts are **operational evidence**. They exist so that "what did the live run actually do" has an
answer that does not depend on a terminal scrollback or a chat transcript.

## 10. The frozen operational-template set

Seven templates are frozen in planning form under [`Docs/m3/templates/`](../m3/templates/request_budget.md):

| Template | Purpose |
|---|---|
| `request_budget.md` | Route-by-route planned counts, maximum physical attempts, retry allowance, hard ceiling, contingency, expected raw objects, expected elapsed window, and the exact owner approval |
| `gate_f_checklist.md` | The Gate F pass/fail record: rehearsal, identity, network default, allowlist, denylist, two dry runs, identical plan hashes, budget, ceiling, operator readiness, owner approval |
| `gate_h_checklist.md` | The post-acquisition Gate H record: actual versus planned, route compliance, response totals, raw-store and provenance completeness, drift, retry compliance, no overflow, no leakage, network disabled afterward |
| `schema_drift_incident.md` | The fail-closed drift incident record and its owner ruling |
| `interrupted_run_recovery.md` | The interrupted-run state reconstruction, safe-resume determination, and duplicate-prevention proof |
| `real_snapshot_evidence_packet.md` | The complete M3.3 evidence packet, ending in an explicit no-approval statement |
| `root_hash_approval_packet.md` | The M3.4 exact-root approval or rejection, with the exact-hash-only clause |

"Frozen in planning form" means the field set is fixed by this record; a template is filled in by the
phase that uses it, never rewritten by it. Changing a template's field set requires a new accepted
decision.

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

## 15. Request-volume values may not be invented

**No integer request count may be invented anywhere in Milestone 3.** A count is either derived from
accepted offline inputs and reproducible, or it is explicitly deferred.

Where the current repository state permits a deterministic estimate, the master plan calculates it
from accepted offline inputs and states the inputs. At the Decision 013 §1 as-of — 2026-06-30,
coverage 2009-01-01 to 2026-06-30, `include_open_quarter = false` — the accepted planner yields
**69 required closed quarterly index instances** (2009QTR1 through 2026QTR1), with 2026QTR2
provisional and excluded, at plan hash
`25257d753295ecb1befc23ff2a54cf37052c873ba425efd0717118b6c8a4a0b6`. The four one-shot bulk sources
and the annual calendar instance contribute one logical request each, and the calendar-announcement
manifest currently holds zero entries, so that route plans zero.

## 16. Where an exact request count cannot yet be derived

Where a real candidate set or current SEC state is required, the master plan writes

```
EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN
```

and, for each such count, it must:

1. **provide the exact formula** that produces the count;
2. **identify every count dependency** by name;
3. **define the future zero-request planning command** that resolves it, with its exact intended
   interface;
4. **define a hard request ceiling** that binds regardless of what the formula resolves to;
5. **require explicit owner approval of the exact budget and ceiling before network enablement.**

Two M3.2 routes currently sit in this category: `sec_submissions_historical`, whose count depends on
the historical-file references named inside the retrieved bulk archive, and `sec_submissions_entity`,
whose count depends on the controlled reconciliation set the acquisition actually needs.

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

The project owner authorizes, for this planning recording and no other purpose:

1. **one planning/governance commit** containing this record, the master plan, the `Docs/m3/`
   documentation pack, and the navigation and status updates they require;
2. **one push to `origin/main`**.

**No tag is authorized in this session.** No existing tag is moved, replaced, re-pointed, or
recreated. CLAUDE.md rule 13 applies independently to everything beyond this list.

## 23. The next authorized action

```
INDEPENDENT_M3_MASTER_PLAN_REVIEW
```

A focused, fresh Opus review — performed by a session that authored none of this planning pack — must
verify that:

- all Decision 024 obligations are represented **exactly once**;
- each M3 phase has complete inputs, outputs, permissions, stop conditions, validation, recovery,
  tokens, and checkpoint policy;
- the operator runbook is executable as documentation **without pretending planned commands already
  exist**;
- the offline-rehearsal specification covers the complete workflow;
- request budgeting is exact or explicitly deferred to the zero-request plan;
- execution receipts cannot contaminate accepted identities;
- templates and limitations are complete;
- **no implementation authority was granted**;
- **no live access occurred.**

## 24. Only after that review may the M3.1 contract be created

**Only after `INDEPENDENT_M3_MASTER_PLAN_REVIEW` passes may the owner authorize a separate session to
create the bounded M3.1 implementation contract.** That contract is itself not implementation
authority — it is one of Decision 024 §8's five conditions, and the others must also hold.

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
- **No offline rehearsal has been run**, no Gate F has passed, and no Gate H has passed.
- **No migration beyond `0013` exists.**

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
