# Decision 044 — M3.2 G1 Navigation and Workflow Repair Acceptance and Publication

**Date:** 2026-08-06
**Status:** ACCEPTED — OWNER APPROVED 2026-08-06
**Type:** Bounded governance record accepting one **non-production** repository stage and publishing
it, together with its durable independent-review artifact, by one normal fast-forward push. **Not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration byte,
implementation byte, test byte, or configuration byte — **no executable byte changes with this
record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–043 are byte-unchanged.
The accepted M3.2 contract, the T2 authorization packet, the accepted G1 implementation candidate,
and the durable G1 review artifact are all byte-unchanged. Stage progress is recorded here and in the
ledger, never in the contract.
**Related:** [Decision 043](decision_043_m3_2_g1_navigation_workflow_repair_authorization.md) (the
authorizing record), Decisions 024 §8, 033, 034, 035, 037, 040, 041, 042; the durable review artifact
[`Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md`](../m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md);
the accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of the bounded non-production stage **M3.2 G1 — Navigation and
Workflow Repair** at the exact candidate named in §3, the owner's acceptance of the fresh independent
G1 review and its durable artifact, the exhaustion of G1's implementation authority, and the
publication of the three-commit chain by one normal fast-forward push.

---

## 1. What this record accepts, and what it does not

Four determinations, which must not be collapsed:

1. **Stage acceptance.** The bounded non-production stage **M3.2 G1 — Navigation and Workflow
   Repair** is accepted at the exact candidate named in §3. Formal classification:
   **`M3_2_G1_ACCEPTED_AND_COMPLETE`**.
2. **Review acceptance.** The fresh independent G1 review, its verdict, and its durable repository
   artifact are accepted (§4). This is the first exercise of the Decision 043 §11 durable-review
   lifecycle, and that lifecycle is confirmed in effect prospectively.
3. **Publication.** The G1 implementation candidate, the G1 review commit, and this acceptance commit
   are published together by **one normal fast-forward push** (§7). **No tag.**
4. **What this record is not.** G1 sits **outside the contract T-series**. Accepting it alters no T2
   cadence, T2 completion, T2 methodology, or accepted contract meaning, and grants **no** stage
   **T2.5** or **T2.6** authority. Overall M3.2 **T3** implementation acceptance has not occurred.
   Nothing here may be read as T3, T4, T5, or Gate H satisfaction.

## 2. The owner instrument, recorded without alteration

```text
OWNER_DECISION_044_M3_2_G1_ACCEPTANCE_AND_PUBLICATION: APPROVED
```

The owner accepts the fresh independent G1 review and authorizes the acceptance and publication
recorded here. Where this record summarizes for navigation, the instrument's own terms control.

## 3. Accepted G1 implementation candidate

Every value below was resolved live from Git before this record was written; the tree SHA was
resolved directly rather than carried from any report.

| Fact | Value |
|---|---|
| Accepted candidate | `7ac33d0abd9e05bf895b38270bde476317c974be` |
| Candidate subject | `Repair M3.2 navigation and review workflow` |
| Candidate tree | `a848320f1edd159f07b112f45790a229ec48827e` |
| Candidate parent — published Decision 043 | `c1fbece9242356b840787dd00ad46f15bb880133` |
| Tags at candidate | none |

**The candidate changed exactly the seven paths Decision 043 §6 authorized, and no eighth path:**
`Docs/decision_index.md`, `Docs/change_impact_map.md`, `Docs/architecture_map.md`,
`Milestones/STATUS.md`, `scripts/context_snapshot.sh`, `Makefile`, and the new
`Docs/m3/review_execution_conventions.md`.

**No production source, test, configuration, migration, schema, receipt, reason-code, route,
source-authority, contract, packet, or accepted-decision byte changed.** The migration chain remains
`0001`–`0013`, the receipt remains `m3-execution-receipt/2.0`, and both tracked network switches in
`configs/project.yaml` remain `false`. No operational catalog, raw object, receipt, or evidence
artifact exists.

## 4. Accepted independent review

| Fact | Value |
|---|---|
| Verdict | `M3_2_G1_INDEPENDENT_REVIEW_PASS` |
| Artifact | `Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md` |
| Artifact SHA-256 | `ec12e038759d61b238c3a6fb7b46627ec070651fba9084d728fb09dfd1ad958f` |
| Review commit | `983fceb27122e4c4275f9554ad001c2d0a9d8524` |
| Review commit subject | `Record independent review of M3.2 G1 navigation repair` |
| Review commit tree | `2ac6a0a04973494cd561c0440652959a2c499592` |
| Review commit parent | `7ac33d0abd9e05bf895b38270bde476317c974be` |
| Findings | BLOCKER 0 · MAJOR 0 · MINOR 1 · OPTIMIZATION 2 |
| Review commit contents | exactly one added path — the artifact |
| Tags at review commit | none |

**The Decision 043 §11 lifecycle was followed as written.** The reviewer was a genuinely fresh
session and was not the implementation session; it remained read-only over the repository until the
substantive verdict was determined, and **the artifact was created only after that verdict was
reached**. The review commit carries only the artifact and the exact required subject.

**The prospective-only rule held.** No historical T2.2–T2.3 or T2.4 review artifact was
reconstructed, fabricated, back-dated, or replaced by a pseudo-artifact. Decision 042's disclosure
that no T2.4 rereview artifact exists stands exactly as written.

## 5. The owner ruling

The owner accepts:

1. **The G1 implementation candidate** `7ac33d0abd9e05bf895b38270bde476317c974be`, at tree
   `a848320f1edd159f07b112f45790a229ec48827e`, on parent
   `c1fbece9242356b840787dd00ad46f15bb880133`, as the accepted G1 implementation.
2. **The fresh independent G1 review**, verdict `M3_2_G1_INDEPENDENT_REVIEW_PASS`.
3. **The durable review artifact and its review commit**, at the path, SHA-256, tree, parent, and
   subject bound in §4.
4. **The Decision 043 R1–R5 implementation** — R1 navigation repair across the decision index, the
   change-impact map, and the architecture map; R2 marker and context repair; R3 `make stage-gate`;
   R4 `Docs/m3/review_execution_conventions.md`; R5 the piloted durable-review lifecycle — as
   satisfying what Decision 043 authorized, within the seven-path ceiling and the §4 hard semantic
   boundary.
5. **G1 as COMPLETE and ACCEPTED.**

### 5.1 Context-optimization evidence

The accepted evidence is the independent review's reproducible measurement, taken in disposable
clones outside the repository with the sole path-dependent field normalized:

| Measurement | Value |
|---|---|
| Pre-G1 published baseline (`c1fbece…`, clean) | **14,579 bytes** |
| Accepted G1 candidate (`7ac33d0…`, committed and clean) | **2,654 bytes** |
| Reduction | **11,925 bytes — 81.8%** |

**The earlier observations of `14,724` and `2,795` bytes are superseded for G1 acceptance evidence by
these reproducible measurements.** `2,795` reproduces only over the pre-commit working tree, and
`14,724` reproduces on no clean commit in this lineage; both are measurement-state artifacts of when
they were taken. **Neither is classified as an implementation defect**, no repository byte asserts any
size, and the accepted candidate's actual result is better than the figure earlier reported. The
review's **MINOR-1** finding is discharged by binding `14,579 → 2,654` here rather than by any
repository change; none was needed and none was made.

The review's two **OPTIMIZATION** observations — the absolute phrasing of one default in
`review_execution_conventions.md` §4, and the residual staleness a reader sees in the accepted
contract's own `STATUS:` marker now that the parser reports it in full — are recorded as observations
only. Neither is a defect in the accepted candidate, the contract was correctly left untouched as a
prohibited path, and **neither is authorized for action by this record** (§6).

### 5.2 Historical skip observation, preserved

Decision 043 §12's ruling is preserved unchanged and is not re-adjudicated:

- The single skip in the accepted T2.4 full-suite run was the pre-existing **fixed-literal skip in
  `tests/unit/test_m23_pilot_manifest.py`**; the **HTTPX transport tests executed and did not skip**.
- **Decision 042's historical wording is not edited** and stands as written.
- The older Milestone-2-era `[sec]`-extra skip sentence in the ledger remains **historical**, is
  factually correct for its era, and was **correctly left outside G1's adjudication scope**.

## 6. G1 disposition and the exhaustion of its authority

```text
M3_2_G1_ACCEPTED_AND_COMPLETE
```

**G1's seven-path implementation authority is exhausted.** Neither Decision 043 nor this record
authorizes any further G1 implementation, any further edit to the seven paths under G1 authority, or
a second G1 commit. Any later change to those paths requires its own explicit owner authorization.

**The prospective durable-review-artifact convention established by Decision 043 §11 remains in
effect** for later acceptance-relevant independent reviews, unless superseded by later owner
authority.

**Not reopened by this record**, and outside G1 acceptance entirely: a structural rewrite of
`Milestones/STATUS.md`; splitting `src/disclosure_drift/m3/acquisition.py`; a repo-owned audit
harness; a second context command; a mutation framework; and a frozen-input manifest. Decision 043
§13's dispositions stand, including the deferral of the acquisition-module split until post-M3.

## 7. Publication

One **normal fast-forward push** of `main` publishes, in order, the three commits above
`origin/main`:

1. `7ac33d0abd9e05bf895b38270bde476317c974be` — the accepted G1 implementation candidate;
2. `983fceb27122e4c4275f9554ad001c2d0a9d8524` — the durable independent-review artifact;
3. this acceptance commit, exact subject `Accept and publish M3.2 G1`, on parent `983fceb…`.

Permitted only after: durable recording of this record; registry and ledger agreement; unchanged
candidate and review-artifact bytes; a staged path set of exactly the three §8 governance paths;
passing governance validation; one fetch confirming `origin/main` remains
`c1fbece9242356b840787dd00ad46f15bb880133`; and a verified fast-forward.

**No commit in the chain may be inserted, rewritten, squashed, amended, rebased, reset, or removed.
No tag. No release. No force push, no `--force-with-lease`, no history rewrite.** If the remote has
changed unexpectedly, the operation **stops** and returns for owner adjudication; it is never resolved
by a merge or a rebase.

## 8. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_044_m3_2_g1_acceptance_and_publication.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 044 row and quick-lookup entry;
- `Milestones/STATUS.md` — narrow current-state, blocker, authority-state, and next-action updates,
  with the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_M3_2_T2_5_STAGE_AUTHORIZATION_DECISION`;
- **one** governance-only commit with the exact subject `Accept and publish M3.2 G1`, and the one
  normal fast-forward push of §7. **No tag.**

**No fourth path.** The accepted candidate, the review artifact, Decision 043, every earlier
Decision, the navigation maps, the context script, the `Makefile`, the conventions document, source,
tests, configuration, migrations, contracts, and the T2 packet are **not modified**.
`Milestones/STATUS.md` is updated narrowly and is **not structurally rewritten**.

## 9. Negative authority

This record does **not** authorize: **T2.5** implementation; **T2.6** implementation; T3, T4, or T5
execution; network enablement; CompanyFacts enablement; SEC contact or connectivity testing; live
acquisition; real operational-catalog creation; receipt emission; use of the **801** request ceiling;
migration changes; receipt-schema changes; reason-code changes; production behavior changes; tag
creation; Gate H work; or M3.3 and later work.

G1 acceptance and T2.5 stage authorization remain **separate owner judgments**, and neither follows
from the other. After publication, control returns to the ChatGPT owner for the separate T2.5
stage-authorization decision.

## 10. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner's acceptance is recorded without change of substance
and is neither broadened nor reinterpreted; (2) the accepted candidate's SHA and tree, and the review
commit's SHA, tree, parent, and subject, are unchanged from the reviewed chain; (3) the review
artifact's SHA-256 is exactly `ec12e038759d61b238c3a6fb7b46627ec070651fba9084d728fb09dfd1ad958f`;
(4) Decisions 001–043 are byte-unchanged and the seven G1 implementation paths are byte-unchanged
from the reviewed candidate; (5) `src`, `tests`, `configs`, migrations, contracts, the T2 packet, and
every template and review artifact are byte-unchanged; (6) Decision 044 is unique — no other decision
file or registry row carries the number, and directory and registry agree; (7) the registry and
status ledger match this record exactly, with the next-action marker line occurring exactly once and
carrying no suffix; (8) `git diff --check` and `git diff --cached --check` pass; (9) the commit
carries exactly the three §8 paths; (10) no tag is created; (11) no private path, SEC identity, or
private-evidence content appears in any changed file; (12) both tracked network switches remain
`false`, the migration chain remains `0001`–`0013`, the receipt remains `m3-execution-receipt/2.0`,
and no operational artifact exists.

## 11. Formal outcome

```text
M3_2_G1_ACCEPTED_AND_PUBLISHED
```

Stage **M3.2 G1 — Navigation and Workflow Repair** is accepted, complete, and — on the §7 push —
published together with its durable independent-review artifact. G1's implementation authority is
exhausted. Overall Milestone 3.2 implementation acceptance remains the separate later **T3** act.

**Next authorized action:** `CHATGPT_OWNER_M3_2_T2_5_STAGE_AUTHORIZATION_DECISION` — control returns
to the ChatGPT owner for the separate T2.5 stage decision. **T2.5 and T2.6 have not begun and are not
authorized by this record**; network enablement, live SEC access, acquisition, real
operational-catalog creation, receipt emission, and ceiling-801 use all remain unauthorized.

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-06.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
