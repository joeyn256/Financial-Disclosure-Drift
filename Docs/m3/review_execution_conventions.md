# Review and Execution Conventions — Milestone 3

**This document records default execution conventions only. It grants no stage, implementation,
schema, network, or live-operation authority. Accepted Decisions, contracts, and task-specific
packets control on conflict.**

Created under accepted
[Decision 043](../Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md) §10.
It exists so that a routine packet does not have to restate the same mechanics every time. A
convention here is a **default a packet may override**, never a permission a packet may omit.

## 1. Session preflight

Every packet states, and every session attests to, six things before touching the repository:

| Field | What it fixes |
|---|---|
| Role | The one role the session is executing (implementer, reviewer, discovery, governance recorder) |
| Model | The expected model |
| Effort | The expected reasoning effort |
| Fresh session | Whether the session must begin with no carried-over context |
| Authorship / independence | Which prior sessions this session must **not** be — a reviewer is never the implementer |
| Workflow mechanisms | Whether subagents, delegated or background agents, parallel sessions, worktrees, or dynamic workflows are permitted; the default is **none** |

**Default disposition on a material mismatch: STOP.** For mutating implementation work, governance
recording, and independent review, a material role, model, freshness, or independence mismatch is a
stop condition — disclose it and return for owner adjudication rather than proceeding. A packet may
provide a different disposition; silence does not.

**Pure read-only discovery** may disclose-and-continue **only when its packet expressly permits
it.** Read-only is not by itself a licence to continue past a mismatch.

## 2. Authority, execution, and evidence are three different things

- **Accepted Decision — durable authority.** What is permitted, what is forbidden, what is accepted.
- **Execution packet — mechanics.** How to exercise authority that already exists. A packet should
  **cite** the governing record rather than reproduce large sections of it.
- **Completion or review report — evidence.** What actually happened, with the outputs that prove it.

Citing rather than reproducing does not thin the packet. Each packet still states explicitly, in its
own words: the **exact path envelope**; the **negative authority** (what it does not grant); the
**stop conditions**; the **commit and publication rules**; and the **acceptance or verdict
conditions**. Those five are never left to be inferred from a cited record.

## 3. Packet and report compression

Default to compact, evidence-driven packets and reports. A normal completion or review report should
generally fit within roughly **15–20 meaningful headings**.

This is a default, **not permission to omit required evidence**. What compression removes is
repetition and ceremony: the same commit identities and hashes repeated under several headings, Git
state restated in three places, authority prose copied out of the decision it cites, and empty
sections carried only to match a template. A required output that appears exactly once is complete.

## 4. Independent-review environment

The reviewer owns this procedure. **It is a procedure, not a repository-owned script**, and no
repo-owned candidate-specific audit oracle or scenario harness may be created for it.

1. An ordinary isolated clone at an **explicit SHA** — never a review conducted in the primary
   checkout.
2. An isolated environment with the project's declared dependencies installed into it.
3. **No import of project source from the primary checkout.** Verify this rather than assume it.
4. Bytecode and cache isolation, so a stale artifact cannot answer for current source.
5. Scratch and temporary data only, written outside the repository.
6. **Mandatory teardown**, and
7. **explicit verification that teardown succeeded** — the clone, environment, and scratch data are
   gone, and the primary checkout is unchanged.

**The independence boundary.** Environment setup may be shared as a procedure, because it encodes no
expectation about the candidate. Candidate-specific oracles, expected-result generators,
candidate-specific assertion helpers, and scenario builders that encode the assumptions under review
**stay reviewer-owned** — shipping them into the repository would let the implementation supply the
standard it is judged against.

## 5. Mutation hygiene

These steps make a mutation result mean something. **No general mutation framework is authorized**;
this is a discipline, not a tool.

- Establish a **positive control** first — a mutation known to be caught — before trusting any
  survival result.
- Prove the mutation **changed source bytes**.
- Prove Python **executed the mutated bytes**: `PYTHONDONTWRITEBYTECODE=1`, purge the relevant
  `__pycache__`, and use `-p no:cacheprovider` where appropriate.
- **Prove a behavioural effect before interpreting survival.** A mutation with no observable effect
  proves nothing about the tests.
- Classify with exactly this vocabulary:
  - **`KILLED`** — a test failed, as it should have;
  - **`SURVIVED_EFFECTIVE`** — behaviour changed and no test caught it (a real gap);
  - **`SURVIVED_NO_OP`** — the mutation provably changed no behaviour, so survival is expected.
- **Restore exact bytes**, and prove restoration by hash **and** a clean diff.

## 6. Validation tiers

- **During bounded implementation:** targeted checks, chosen from
  [`Docs/change_impact_map.md`](../change_impact_map.md). Fast feedback is the point.
- **At a consequential stage boundary:** the **complete accepted stage gate** is the default. In
  this repository that is `make stage-gate` — `make check`, then `make sqlite-check`, then
  `make context`, in that order. The target is a convenience implementation of accepted
  requirements and is **not itself authority**.
- **One normal complete boundary run, not ceremonial repetition.** Re-run only for a concrete
  reason: the prior run was invalid, a result is nondeterministic or timing-sensitive, or a relevant
  file changed after the run.
- **High-blast-radius changes** — shared test fixtures, migrations, the reason vocabulary — receive
  a full-suite validation after the change and before handoff. The normal final boundary run
  satisfies this when nothing relevant changed afterwards.

## 7. Durable review-artifact lifecycle

The convention Decision 043 §11 makes **prospective from stage G1**:

1. The implementation candidate remains **unaccepted** while it is reviewed.
2. A **genuinely fresh** reviewer, who is not the implementation session, performs the review.
3. The reviewer stays **read-only until the substantive verdict is determined**. The verdict is not
   a product of writing the artifact.
4. On a passing verdict the reviewer commits **only the review artifact**, before owner acceptance.
5. The later owner acceptance Decision binds the reviewed implementation commit, the artifact path,
   the artifact SHA-256, and the review commit identity.
6. **A failed review gains no implementation authority** and returns for owner adjudication.

**Historical gaps stay gaps.** Where an accepted stage has no durable review artifact, none is
reconstructed, fabricated, or back-dated. The record of its absence stands as written.

**The G1 pilot instance.** Artifact path
`Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md`; review-artifact commit
subject `Record independent review of M3.2 G1 navigation repair`. That artifact is created by the
reviewer, on a passing verdict, and never by the implementation session.
