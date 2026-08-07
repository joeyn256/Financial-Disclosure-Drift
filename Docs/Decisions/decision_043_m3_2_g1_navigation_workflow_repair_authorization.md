# Decision 043 — M3.2 G1 Navigation and Workflow Repair Authorization

**Date:** 2026-08-06
**Status:** ACCEPTED — OWNER APPROVED 2026-08-06
**Type:** Bounded governance record authorizing one **non-production** repository stage that sits
outside the accepted contract T-series. **Not** a preregistration deviation. It changes no
hypothesis, cohort window, maturity gate, outcome definition, threshold, seed, selection
methodology, S4/S5/S6 identity, hash preimage, migration byte, implementation byte, test byte, or
configuration byte — **no executable byte changes with this record**, and none is authorized to
change in the stage it authorizes.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–042 are byte-unchanged.
The accepted M3.2 contract is not edited. **One prior standing instruction is superseded, and only
to a stated extent:** the navigation-preservation instruction of
[Decision 033](decision_033_m3_2_correction_pass_adjudication.md) §5, as carried forward by
[Decision 034](decision_034_m3_2_contract_acceptance.md) §8 and restated in Decisions 036, 037,
040, 041, and 042 — see §5 below. That supersession is partial and is recorded here rather than by
editing any earlier record.
**Related:** the read-only post-T2.4 workflow-efficiency discovery of 2026-08-06 whose
recommendation `RECOMMEND_MINIMAL_OPTIMIZATION_BEFORE_T2_5` this record accepts; Decisions 024 §8,
033, 034, 035, 037, 040, 041, 042; the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the authorization, envelope, content requirements, validation, review lifecycle, and
negative authority of the bounded non-production stage **M3.2 G1 — Navigation and Workflow
Repair**.

---

## 1. What this record authorizes, and what it does not

Three determinations, which must not be collapsed:

1. **Stage authorization.** One bounded non-production stage, **M3.2 G1 — Navigation and Workflow
   Repair**, is authorized. G1 exists **outside the contract T-series**. It does not alter T2
   cadence, T2 completion, T2 methodology, or any accepted contract meaning.
2. **Authorization is not permission to begin.** G1 implementation **may not begin** on this
   record. It begins only after this Decision is durably recorded and published **and** the owner
   issues the separate G1 implementation packet (§18 of the instrument; §16 below).
3. **What remains outstanding.** Stage **T2.5–T2.6** remains owner-gated, unauthorized, and not
   begun; its commit remains the implementation-freeze candidate for the independent T3 review
   (Decision 037). Overall M3.2 **T3** implementation acceptance has not occurred. Nothing here may
   be read as T3, T4, T5, or Gate H satisfaction.

## 2. Verified baseline

Verified live, read-only, before this record was written:

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD, and `origin/main` | `59374d71a9cd89a5f03414a74071962eb8778757` (identical) |
| Subject | `Accept and publish M3.2 T2.4` |
| Working tree | clean — no staged, unstaged, or untracked path |
| Tags at HEAD | none |
| Latest migration | `0013_m23_manifest_lifecycle_guards.sql` (chain `0001`–`0013`) |
| Latest decision before this record | `decision_042_m3_2_t2_4_acceptance_and_publication.md` |
| `network.enabled` | `false` |
| `network.m3_acquire_enabled` | `false` |

Stage T2.4 is accepted, complete, and published. T2.5 and T2.6 are not begun and are not
authorized. No live SEC operation has occurred and none is authorized.

## 3. The owner instrument, recorded without alteration

```text
OWNER_DECISION_043_M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZATION: APPROVED
```

The owner accepts the read-only workflow-efficiency discovery recommendation
`RECOMMEND_MINIMAL_OPTIMIZATION_BEFORE_T2_5` and authorizes one bounded non-production stage before
T2.5, named **M3.2 G1 — Navigation and Workflow Repair**, whose purpose is to reduce
review/navigation friction before the T2.5–T2.6 freeze-candidate work **while preserving or
improving auditability**.

The operative content of that instrument is reproduced in §§4–14 of this record, in the owner's
terms and without broadening. Where this record summarizes for navigation, the instrument's own
words control.

## 4. Hard semantic boundary

G1 may not alter: SEC acquisition semantics; request planning; route or source authority; recovery
or reconciliation semantics; request-attempt accounting; ceiling semantics; receipt schema or
vocabulary; reason-code semantics; database schema or migrations; network configuration; M3.2
methodology; contract meaning; or any accepted Decision 001–042.

**No production source or test behavior is authorized to change.**

## 5. Navigation ruling, and the exact extent of the supersession

The repository's navigation aids are authorized to be **brought current through Decision 042 and
accepted T2.4**.

**What is superseded, and only so far as necessary to perform this G1 navigation repair:** the
standing instruction that `Docs/decision_index.md` be left unedited. That instruction originates in
Decision 033 §5 — which restored the file to its `3fbaa12d…` bytes after an out-of-scope edit,
recorded the stale Decision-029 next-action sentence as "an open, nonblocking navigation-staleness
item," and required that "correcting it later requires its own explicit path authorization." It was
carried forward by Decision 034 §8 and restated as a not-edited path in Decisions 036, 037, 040,
041, and 042.

**This record is that explicit path authorization**, and no more than that. Specifically:

- **Historical decisions remain immutable.** Nothing in Decisions 001–042 is edited, reinterpreted,
  withdrawn, or re-approved. Decision 033 §5's adjudication of the original path-scope deviation
  stands unchanged as the historical record of that event.
- **The supersession is partial and prospective.** It removes only the bar on editing
  `Docs/decision_index.md`, and only for the G1 navigation repair within the §6 envelope.
- **Navigation documents remain aids only.** They do not become authority. On any conflict they
  defer to accepted Decisions, the accepted contract, and the status ledger. The registry remains
  authoritative for which decisions exist and their approval status; `Docs/decision_index.md` is
  never consulted to establish that a decision exists or is approved.

## 6. The G1 implementation envelope — seven paths, a ceiling not a requirement

After this Decision is separately recorded and published, G1 implementation may modify **only**:

1. `Docs/decision_index.md`
2. `Docs/change_impact_map.md`
3. `Docs/architecture_map.md`
4. `Milestones/STATUS.md`
5. `scripts/context_snapshot.sh`
6. `Makefile`
7. `Docs/m3/review_execution_conventions.md`

**No eighth implementation path is authorized.** The seven paths are a **ceiling, not a requirement
to edit every path**. A need for an eighth path is an immediate stop (§14).

## 7. R1 — Navigation repair

**`Docs/decision_index.md`.** Add Decisions 030–042 using the existing navigation convention. **Do
not copy entire decisions.** Provide concise, correct pointers sufficient to reach the governing
record.

**`Docs/change_impact_map.md`.** Add a bounded M3.2 T2 section covering the accepted and currently
governed T2 surfaces, their nearest tests, and their relevant gates. **Do not create a second
source of substantive authority.**

**`Docs/architecture_map.md`.** Extend the map through the relevant M3.2 `m3/` surfaces and their
accepted supporting modules at **navigation-level granularity**. **Do not redesign or refactor
architecture.**

## 8. R2 — Marker and context repair

**`Milestones/STATUS.md` is not to be structurally rewritten**, and its historical narrative is
preserved. Only the machine-readable values whose prose has expanded beyond their navigation
purpose are shortened — especially `CURRENT_STAGE`, `ACTIVE_BLOCKER`, and
`IMPLEMENTATION_AUTHORIZATION` — targeting **no more than approximately 200 characters per marker**
unless a slightly longer value is required to preserve correctness. **No historical evidence may be
deleted merely to reach a byte target.**

Current explanatory prose that incorrectly describes the following is corrected:

- the single full-suite skip, described as an `[sec]`-extra transport skip;
- the active contract, described as the obsolete M2.3 S6 contract.

**Decision 042 is not edited.** Its wording is recorded as historical (§10 below).

**`scripts/context_snapshot.sh`** is improved rather than replaced — no second context command is
created. Required additions: HEAD tree; HEAD parent; ahead/behind; `network.enabled`;
`network.m3_acquire_enabled`. Marker parsing is fixed so that an authoritative marker whose value
legitimately uses indented continuation lines is returned **completely rather than truncated**, and
the implementation **must not broaden marker parsing into unrelated prose**. **No frozen contract
hash, packet hash, receipt version, or other authority manifest may be added to this script.**

A substantially smaller context result is targeted; **approximately 4 KiB is a goal, not
authority, and correctness outranks the byte target.**

## 9. R3 — Stage gate

Add `make stage-gate`, executing the contract-required boundary validation in **deterministic,
sequential order**: (1) the existing `make check`; (2) `make sqlite-check`; (3) `make context`.
Parallelizable Make prerequisites may **not** merely be declared if that could change the required
order.

`stage-gate` is a **convenience implementation of accepted requirements. It is not itself
authority**; if it ever diverges from an accepted contract or Decision, the accepted record
controls.

## 10. R4 — Review-execution conventions

Create `Docs/m3/review_execution_conventions.md`. It **grants no implementation, network, schema,
or stage authority**, and records default execution conventions **subordinate to accepted Decisions
and task-specific packets**. It must cover, compactly:

- **Session preflight.** Each packet states role; expected model; effort; fresh-session
  requirement; authorship/independence restrictions; and whether subagents or workflows are
  permitted. For **mutating implementation or governance work and for independent reviews**, a
  material role/freshness/model mismatch **defaults to STOP** unless the packet expressly provides
  a different disposition. **Pure read-only discovery** may use disclose-and-continue **only when
  the packet expressly permits it**.
- **Authority / execution / evidence separation.** Accepted Decision = durable authority; execution
  packet = the mechanics needed to exercise it; completion or review report = evidence of what
  happened. A packet should **cite** accepted authority rather than reproduce large sections of it.
  The exact path envelope, negative authority, stop conditions, commit and publication rules, and
  task-specific acceptance conditions **remain explicit in the packet**.
- **Packet and report compression.** Default to compact, evidence-driven packets and reports; a
  normal report should generally fit within roughly 15–20 meaningful headings. This is a **default,
  not a reason to omit required evidence.** The same hashes, Git status, prohibitions, and
  authority prose are not duplicated across multiple headings.
- **Independent-review environment.** A short **reviewer-owned** procedure for: an ordinary
  isolated clone at an explicit SHA; dependency and environment setup **without importing project
  source from the primary checkout**; bytecode and cache isolation; scratch/temp data only;
  **mandatory teardown**; and **explicit verification that teardown succeeded**. **No repo-owned
  candidate-specific audit oracle or scenario harness may be created.**
- **Mutation hygiene.** Establish a positive control; verify the mutation changes source bytes;
  ensure Python executes the mutated bytes; use `PYTHONDONTWRITEBYTECODE=1`; purge the relevant
  `__pycache__`; disable the pytest cache where appropriate; **prove behavior changed before
  judging survival**; classify as `KILLED`, `SURVIVED_EFFECTIVE`, or `SURVIVED_NO_OP`; restore
  exact bytes; and verify restoration by hash and clean diff. **No general mutation framework is
  authorized by G1.**
- **Validation tiers.** Targeted validation is preferred during bounded implementation for fast
  feedback. At every consequential stage boundary the **complete accepted stage gate is the
  default**. Additional complete runs require a concrete reason — an invalid prior run,
  nondeterminism, timing sensitivity, or a correction requiring confirmation. Changes to
  high-blast-radius test infrastructure, migrations, or the reason vocabulary must receive a
  full-suite validation after the change before handoff; the normal boundary run may satisfy this
  when no later relevant edit occurs.

## 11. R5 — Durable independent-review evidence

**Beginning with G1**, a successful acceptance-relevant independent review must **normally become a
durable repository artifact before final owner acceptance**.

**The rule is prospective.** The missing historical T2.2–T2.3 and T2.4 review artifacts must **not**
be reconstructed, fabricated, back-dated, or replaced by pseudo-artifacts. Decision 042's disclosure
that no T2.4 rereview artifact exists stands exactly as written.

For G1, the lifecycle is piloted as follows:

1. The G1 implementation candidate remains **unaccepted**.
2. A **genuinely fresh** independent reviewer performs the review, and is **not** the implementation
   session.
3. The reviewer remains **read-only until the substantive verdict is determined**.
4. On a **PASS** verdict, the reviewer may create exactly
   `Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md`.
5. The reviewer commits **only that artifact**, with the exact subject
   `Record independent review of M3.2 G1 navigation repair`.
6. The later owner acceptance Decision binds: the reviewed implementation commit; the
   review-artifact path; the review-artifact SHA-256; and the review commit identity.

**A failed review gains no implementation authority** and returns for owner adjudication. Future
task-specific Decisions may refine this lifecycle.

## 12. Historical observations, recorded without modifying Decision 042

Recorded here because accepted records are amended by new records and never edited in place:

1. **The single skipped test in the accepted T2.4 full-suite run was the pre-existing fixed-literal
   skip in `tests/unit/test_m23_pilot_manifest.py`** (`snapshot_state is a fixed literal asserted
   before hashing`), **while the HTTPX transport tests executed and did not skip.**
2. **Decision 042's wording therefore understated the actual validation.** Describing the skip as
   the historical `[sec]`-extra skip was inaccurate in a direction that **understates** compliance:
   contract §18's requirement that the `[sec]` extra be installed with
   `tests/unit/test_httpx_transport.py` running and not skipped was in fact **satisfied**, and CI
   independently enforces it with a dedicated "Transport suite must execute, not skip" step.
3. **This does not change the validity of T2.4 acceptance.** No accepted outcome, identity, count,
   or authorization is affected. Decision 042 is not edited, and its historical wording stands as
   written.
4. **The stale active-contract explanatory prose** in `Milestones/STATUS.md` — which describes
   `ACTIVE_STAGE_CONTRACT` as naming the obsolete M2.3 S6 contract while the marker in fact names
   `Milestones/contracts/m3_2.md` — is a **navigation and status maintenance issue, not a
   historical-decision defect.** It is corrected under §8, in the G1 implementation commit.

## 13. Explicitly rejected and deferred optimizations

G1 does **not** authorize: a repo-owned audit harness; a second context command; a mutation
framework; a frozen-input manifest; a structural rewrite of `Milestones/STATUS.md`; splitting
`src/disclosure_drift/m3/acquisition.py`; or any production refactor.

**The acquisition-module split is deferred until post-M3** unless a later genuine correctness issue
requires separate owner adjudication.

## 14. G1 validation, commit structure, and stop conditions

**Validation during G1 implementation.** Use focused command checks while editing. Run the existing
`make context` **before and after** and record approximate output size. Verify each navigation
entry against its authoritative source. Run the completed new `make stage-gate` **once** at the
normal stage boundary. Prove an **empty diff** against all prohibited production, contract, and
configuration paths. Because `stage-gate` includes `make check`, the same full suite is **not**
separately repeated unless a concrete reason requires it. **No mutation campaign is required for
G1.** Command-level **positive and negative** checks of `context_snapshot.sh` and `stage-gate` are
required.

**Commit and review structure.** After this Decision is published, G1 implementation may create **at
most one implementation commit**, with the exact subject `Repair M3.2 navigation and review
workflow`. **No tag.** **No T2.5 work in that commit.** After the candidate is complete, control
returns for a **separate fresh independent-review authorization**. G1 acceptance and T2.5
implementation authorization remain **separate owner judgments**.

**Stop before the act** on: a need for an eighth G1 implementation path; a disagreement between a
navigation aid and its authoritative record that cannot be resolved by a faithful pointer; a need to
change accepted authority meaning; a need to edit an accepted Decision or contract; any production,
configuration, schema, or test semantic change; `stage-gate` behavior that cannot reproduce the
accepted gate sequence; context compression that would require deleting an audit-relevant fact; or
any unexpected network or live-operation requirement.

## 15. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 043 row and quick-lookup entry;
- `Milestones/STATUS.md` — current-state, blocker, authority-state, and next-action updates, with
  the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_ISSUANCE_OF_M3_2_G1_IMPLEMENTATION_PACKET_AFTER_DECISION_043_PUBLICATION`;
- **one** governance-only commit with the exact subject `Authorize M3.2 navigation and workflow
  repair`. **No tag.**

**No implementation change belongs in that commit.** The seven §6 paths other than
`Milestones/STATUS.md` are **not** touched by this recording, and `Milestones/STATUS.md` is touched
here **only** for the decision-recording and next-action updates listed above — the §8 marker
compression and prose corrections are **G1 implementation work**, not part of this commit. No
implementation, test, script, migration, receipt, template, packet, contract, review-artifact,
configuration, or private-evidence byte changes.

## 16. Negative authority

This record does **not** authorize: T2.5; T2.6; network enablement; CompanyFacts enablement; live
SEC contact; real operational-catalog creation; use of the 801-request ceiling; migration changes;
receipt changes; reason-code changes; production behavior changes; tag creation; T3, T4, T5, or
Gate H work; or M3.3 and later work.

It does not begin G1: **G1 implementation must not begin before the separate owner-issued G1
implementation packet.** It confers no authority to push beyond what is separately authorized, and
authorizes no force push, history rewrite, rebase, squash, or amend.

## 17. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner's authorization is recorded without change of
substance and is neither broadened nor reinterpreted; (2) `src`, `tests`, `configs`, migrations, the
contract, the T2 packet, and every template and review artifact are byte-unchanged; (3) Decisions
001–042 are byte-unchanged, and the Decision 033 §5 supersession is recorded here rather than by
editing any earlier record; (4) Decision 043 is unique — no other decision file or registry row
carries the number, and directory and registry agree; (5) the registry and status ledger match this
record exactly, with the next-action marker line occurring exactly once and carrying no suffix;
(6) `git diff --check` and `git diff --cached --check` pass over the updated tree; (7) the commit
carries exactly the three §15 paths; (8) no tag is created; (9) no private path, SEC identity, or
private-evidence content appears in any changed file; (10) the six G1 implementation paths other
than `Milestones/STATUS.md` are unchanged; (11) both tracked network switches remain `false`, the
migration chain remains `0001`–`0013`, and the receipt remains `m3-execution-receipt/2.0`.

## 18. Formal outcome

```text
M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZED
```

G1 is authorized and **has not begun**. Stage T2.5–T2.6 remains owner-gated, unauthorized, and not
begun, and overall M3.2 **T3** implementation acceptance remains the separate later act.

**Next authorized action:**
`CHATGPT_OWNER_ISSUANCE_OF_M3_2_G1_IMPLEMENTATION_PACKET_AFTER_DECISION_043_PUBLICATION` — control
returns to the ChatGPT owner. **G1 implementation must not begin before that separate packet**, and
network enablement, live SEC access, acquisition, real operational-catalog creation, receipt
emission, and ceiling-801 use all remain unauthorized.

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-06.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
