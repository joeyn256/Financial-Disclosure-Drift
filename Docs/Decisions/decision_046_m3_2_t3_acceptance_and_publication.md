# Decision 046 — M3.2 T3 Acceptance and Publication

**Date:** 2026-08-07
**Status:** ACCEPTED — OWNER APPROVED 2026-08-07
**Type:** Bounded governance record accepting the corrected combined M3.2 **T2.5–T2.6** implementation
freeze candidate and its fresh independent **T3** rereview, and publishing both by one normal
fast-forward push. **Not** a preregistration deviation. It changes no hypothesis, cohort window,
maturity gate, outcome definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash
preimage, migration byte, implementation byte, test byte, or configuration byte — **no executable
byte changes with this record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–045 are byte-unchanged.
The accepted M3.2 contract, the historical T2 authorization packet, the accepted implementation
candidate, and the durable T3 review artifact are all byte-unchanged. Stage progress is recorded here
and in the ledger, never in the contract.
**Related:**
[Decision 045](decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md) (the
authorizing record whose implementation authority this record exhausts); Decisions 024 §8, 034, 035,
037, 040, 041, 042, 043, 044; the durable review artifact
[`Docs/m3/reviews/m3_2_t3_corrected_freeze_candidate_independent_rereview.md`](../m3/reviews/m3_2_t3_corrected_freeze_candidate_independent_rereview.md);
the accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of the corrected combined T2.5–T2.6 implementation at the exact
candidate named in §3, the owner's acceptance of the fresh independent T3 corrected-candidate
rereview and its durable artifact named in §4, the disposition of the two nonblocking observations
(§5.1), the overall determination `M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE` (§6), and the
publication of the four-commit lineage by one normal fast-forward push (§7).

---

## 1. What this record accepts, and what it does not

Five determinations, which must not be collapsed:

1. **Implementation acceptance.** The corrected combined stage **T2.5–T2.6 — Operator Surfaces and
   Integrated Implementation Candidate** is accepted at the exact candidate named in §3. This is the
   **accepted implementation freeze** for the combined stage.
2. **Review acceptance.** The fresh independent **T3 corrected-candidate rereview**, its verdict, and
   its durable repository artifact are accepted (§4), under the prospective durable-review lifecycle
   established by Decision 043 §11 and confirmed by Decision 044 §1.
3. **Authority exhaustion.** Decision 045's implementation authority is **exhausted** by this
   accepted implementation (§6).
4. **Publication.** The accepted implementation candidate, the review commit, and this acceptance
   commit are published together, above the published Decision 045 baseline, by **one normal
   fast-forward push** (§7). **No tag.**
5. **What this record is not.** It is **not** T4 acceptance, **not** T5 authority, **not** network
   authority, and **not** live-operation authority. Nothing here may be read as T4, T5, T6, or Gate H
   satisfaction, and nothing here permits a live SEC operation, a real operational catalog, a live
   M3.2 run, or any use of the approved request ceiling **801**.

## 2. The owner determination, recorded without alteration

The owner's determination for this stage was issued as the Decision 046 recording packet itself. It
carries **no separately named `OWNER_DECISION_046_…` instrument token**, and none is invented here.
Its operative terms are:

```text
Decision 046 — M3.2 T3 Acceptance and Publication

The owner accepts the corrected combined M3.2 T2.5-T2.6 implementation and its
fresh independent T3 corrected-candidate rereview.
```

Where this record summarizes for navigation, the owner's own terms control.

## 3. Accepted T2.5–T2.6 implementation candidate

Every value below was resolved live from Git before this record was written; the tree SHA was
resolved directly rather than carried from any report.

| Fact | Value |
|---|---|
| Accepted candidate | `810d567ba7610b22e2ce7cd56b67b7f0e76d26fb` |
| Candidate subject | `Complete M3.2 T2.5-T2.6 integrated implementation` |
| Verified tree | `aa7a7d4a6117160a2a4b2d1165d9b82c318cf968` |
| Candidate parent — published Decision 045 baseline | `f2bbbbf2a1b13e0780c3ea50d01797f78405e97b` |
| Tags at candidate | none |

**The candidate changed exactly eight paths, inside the Decision 045 §11 fifteen-path ceiling, with
no sixteenth path:** `src/disclosure_drift/cli.py`, `src/disclosure_drift/m3/__init__.py`,
`src/disclosure_drift/m3/acquisition.py`, `src/disclosure_drift/m3/request_plan.py`,
`tests/integration/test_m3_cli.py`, `tests/unit/test_m3_acquisition.py`,
`tests/unit/test_m3_dependent_plan.py` (added), and `tests/unit/test_m3_request_plan.py` — 7,707
insertions and 347 deletions.

**No prohibited path was touched.** The independent reviewer compared twenty-five paths by Git blob
hash against the published baseline and found each byte-identical, including `m3/receipt.py`,
`m3/recovery.py`, `reasons.py`, `config.py`, `configs/project.yaml`, `sec/observation_catalog.py`,
`sec/http_client.py`, `sec/request_ceiling.py`, and `storage/catalog.py`. `git diff` over `Docs`,
`Literature`, `Milestones`, `configs`, `scripts`, `src/disclosure_drift/storage`, `pyproject.toml`,
and `Makefile` was empty. The migration chain remains `0001`–`0013`, the receipt schema remains
`m3-execution-receipt/2.0`, both tracked network switches remain `false`, and CompanyFacts remains
disabled. No operational catalog, real M3.2 run, live receipt, raw acquisition object, or live SEC
artifact exists.

**This is the accepted implementation freeze for the combined T2.5–T2.6 stage.**

## 4. Accepted independent T3 review

| Fact | Value |
|---|---|
| Verdict | `M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS` |
| Artifact | `Docs/m3/reviews/m3_2_t3_corrected_freeze_candidate_independent_rereview.md` |
| Artifact SHA-256 | `31cf05dfe6a1a157df6b05bb6788f6ec9c391742028c24bf06dd3e3fcec2e773` |
| Review commit | `3794178584bd935d5718e6ec5c4279dd235c7b3d` |
| Review commit subject | `Record independent rereview of corrected M3.2 T3 freeze candidate` |
| Review commit tree | `3df60f1430c79eb9cd28f12f265b8bb9c9514234` |
| Review commit parent | `810d567ba7610b22e2ce7cd56b67b7f0e76d26fb` |
| Reviewed candidate | `810d567ba7610b22e2ce7cd56b67b7f0e76d26fb` |
| Reviewed tree | `aa7a7d4a6117160a2a4b2d1165d9b82c318cf968` |
| Findings | BLOCKER 0 · MAJOR 0 · MINOR 1 · OPTIMIZATION 1 |
| Review commit contents | exactly one added path — the artifact |
| Tags at review commit | none |

**What the review established:**

- **BLOCKER: 0. MAJOR: 0. MINOR: 1. OPTIMIZATION: 1.**
- **14 of 14 independent mutations `KILLED`** — zero `SURVIVED_EFFECTIVE`, zero `SURVIVED_NO_OP` —
  with the mutated bytes proved changed and the exact bytes proved restored afterward.
- **Full suite: 3,222 passed, 1 skipped**, that one skip being the **pre-existing, unrelated**
  fixed-literal skip in `tests/unit/test_m23_pilot_manifest.py`.
- **`tests/unit/test_httpx_transport.py`: 30 passed, 0 skipped** — it executed rather than skipped.
- **Interruption → recovery → SAFE → resume was exercised through the real CLI path** with a
  substituted non-network transport, including across separate OS processes.
- **No live SEC operation occurred.** No real SEC identity, DNS lookup, connectivity test, or request;
  no real operational catalog, real M3.2 run, live receipt, raw operational object, or SEC evidence
  artifact; ceiling **801** operationally unused.

**The Decision 043 §11 lifecycle was followed as written.** The reviewer was a genuinely fresh,
non-author session using no subagent, delegated agent, background agent, parallel session, worktree,
or dynamic workflow; it treated the candidate as read-only until the substantive verdict was
complete, ran every destructive probe and every mutation inside a disposable copy outside the
repository that was deleted and verified deleted, and created the artifact only after the verdict.
The review commit carries only the artifact.

**Therefore the T3 acceptance threshold is satisfied.**

## 5. The owner ruling

The owner accepts:

1. **The corrected implementation candidate** `810d567ba7610b22e2ce7cd56b67b7f0e76d26fb`, at verified
   tree `aa7a7d4a6117160a2a4b2d1165d9b82c318cf968`, on parent
   `f2bbbbf2a1b13e0780c3ea50d01797f78405e97b`, subject
   `Complete M3.2 T2.5-T2.6 integrated implementation`, as the **accepted implementation freeze** for
   the combined T2.5–T2.6 stage.
2. **The fresh independent T3 corrected-candidate rereview**, verdict
   `M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS`.
3. **The durable review artifact and its review commit**, at the path, SHA-256, tree, parent, and
   subject bound in §4.
4. **T2.5–T2.6 as COMPLETE and ACCEPTED**, and the implementation phase governed through **T3** as
   complete (§6).

### 5.1 Nonblocking observations, carried forward without reopening T2.5–T2.6

Both observations are recorded as carried forward. **Neither reopens the accepted stage, and neither
was acted on during this recording** — the accepted implementation was not modified.

**MINOR-A — post-commit marker ordering in `AcquisitionEngine._execute`.**
The `_execute` ordering permits an extremely narrow interruption timing window after durable commit
but before `_committed_any = True`, potentially reporting `before_raw_store_write` despite the
durable retrieval already being committed. The independent reviewer demonstrated that this does
**not** alter durable remainder determination, attempt accounting, SAFE recovery, or resume behavior,
because those are **evidence-derived rather than phase-label-derived**: the resume remainder is
derived from `reconcile_requests` over durable catalog state and the attempt accounting from
committed instants, and neither branches on the state string.

```text
ACCEPTED_NONBLOCKING_OBSERVATION — DEFERRED
```

**OPTIMIZATION-A — `_window_reason_code` fallback breadth.**
`_window_reason_code` may use `SEC_ACQUISITION_INTERRUPTED` as the fallback reason code for certain
non-interrupted failed, stopped, or incomplete outcomes. The independent reviewer found **no safety
consequence and no acceptance defect**: resumability is decided by `completion_status` and
`interruption_state`, both of which correctly exclude those cases.

```text
ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED
```

**Any future cleanup of either observation requires separate owner authorization.** Neither is
authorized for action by this record.

## 6. Overall T3 determination and the exhaustion of Decision 045's authority

```text
M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE
```

The implementation phase governed through **T3** is complete.

**Decision 045's implementation authority is exhausted by this accepted implementation.** Neither
Decision 045 nor this record authorizes any further T2.5–T2.6 implementation, any further edit to the
accepted candidate's paths under Decision 045 authority, or a second combined-stage commit. Any later
change to those paths requires its own explicit owner authorization.

**This determination does NOT constitute T4 acceptance, T5 authority, network authority, or
live-operation authority.** F4 — public evidence-index vocabulary for the private reconciliation
report — remains a **T4** obligation, exactly as Decision 045 fixed it.

## 7. Publication

One **normal fast-forward push** of `main` publishes, in order, the commits above `origin/main`. The
published lineage retains, in order:

1. `f2bbbbf2a1b13e0780c3ea50d01797f78405e97b` — the published Decision 045 baseline (already on
   `origin/main`);
2. `810d567ba7610b22e2ce7cd56b67b7f0e76d26fb` — the accepted corrected implementation candidate;
3. `3794178584bd935d5718e6ec5c4279dd235c7b3d` — the accepted independent PASS review;
4. this Decision 046 governance commit, exact subject `Accept M3.2 T3 implementation and independent
   review`, on parent `3794178…`.

Permitted only after: durable recording of this record; registry and ledger agreement; unchanged
candidate and review-artifact bytes; a staged path set of exactly the three §8 governance paths;
passing governance validation; and a verified fast-forward with `origin/main` still at
`f2bbbbf2a1b13e0780c3ea50d01797f78405e97b`.

**No commit in the lineage may be amended, squashed, rebased, cherry-picked, inserted, reset, or
removed. No force push, no `--force-with-lease`, no history rewrite. No tag — none is authorized.**
If the remote has changed unexpectedly, the operation **stops** and returns for owner adjudication; it
is never resolved by a merge or a rebase.

## 8. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_046_m3_2_t3_acceptance_and_publication.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 046 row and quick-lookup entry;
- `Milestones/STATUS.md` — narrow current-state, blocker, authority-state, and next-action updates,
  with the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY`;
- **one** governance-only commit with the exact subject `Accept M3.2 T3 implementation and
  independent review`, and the one normal fast-forward push of §7. **No tag.**

**No fourth path.** The accepted candidate, the review artifact, Decision 045, every earlier Decision,
the contract, the T2 packet, the navigation maps, `Docs/decision_index.md`, source, tests,
configuration, migrations, runbooks, templates, and evidence files are **not modified**.
`Milestones/STATUS.md` is updated narrowly and is **not structurally rewritten**. Any executable
change is a **STOP** condition.

## 9. Negative authority

This record does **not** authorize: **T4** implementation or acceptance; **T5**, **T6**, or Gate H
work; network enablement (`network.enabled` and `network.m3_acquire_enabled` both remain `false`);
CompanyFacts enablement; SEC contact, DNS lookup, or connectivity testing; any live SEC request or
live acquisition; real operational-catalog creation; a real M3.2 run row, raw object, live receipt, or
evidence artifact; use of the approved **801** request ceiling; migration changes; receipt-schema
changes; reason-code changes; production behavior changes; tag creation; or M3.3 and later work.

After publication, control returns to the ChatGPT owner. The next authorized action is
**`CHATGPT_OWNER_M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY`**, which authorizes **no** T4
implementation and **no** live operation — it identifies only the next owner-directed
planning/discovery action.

## 10. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner's determination is recorded without change of substance
and is neither broadened nor reinterpreted; (2) the accepted candidate's SHA and tree, and the review
commit's SHA, tree, parent, and subject, are unchanged from the reviewed chain, with the review commit
the direct child of the candidate and the candidate the direct child of the published Decision 045
baseline; (3) the review artifact's SHA-256 is exactly
`31cf05dfe6a1a157df6b05bb6788f6ec9c391742028c24bf06dd3e3fcec2e773`; (4) Decisions 001–045 are
byte-unchanged and the accepted candidate's eight implementation paths are byte-unchanged from the
reviewed candidate; (5) `src`, `tests`, `configs`, migrations, contracts, the T2 packet, and every
template, runbook, and review artifact are byte-unchanged; (6) Decision 046 is unique — no other
decision file or registry row carries the number, and directory and registry agree; (7) the registry
and status ledger match this record exactly, with the next-action marker line occurring exactly once
and carrying no suffix; (8) `git diff --check` and `git diff --cached --check` pass; (9) the commit
carries exactly the three §8 paths; (10) no tag is created; (11) no private path, SEC identity, or
private-evidence content appears in any changed file; (12) both tracked network switches remain
`false`, CompanyFacts remains disabled, the migration chain remains `0001`–`0013`, the receipt remains
`m3-execution-receipt/2.0`, ceiling **801** remains unused, and no operational or live artifact
exists.

## 11. Formal outcome

```text
M3_2_T3_ACCEPTED_AND_PUBLISHED
```

The corrected combined stage **T2.5–T2.6** is accepted and complete; the fresh independent **T3**
rereview and its durable artifact are accepted; Decision 045's implementation authority is exhausted;
the implementation phase governed through T3 is complete
(`M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE`); and — on the §7 push — the accepted candidate, the
review, and this record are published. **No tag.**

**Next authorized action:**
`CHATGPT_OWNER_M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY` — control returns to the ChatGPT
owner. **T4 and T5 have not begun and are not authorized by this record**; network enablement, live
SEC acquisition, real operational-catalog creation, receipt emission, and ceiling-801 use all remain
unauthorized.

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-07.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
