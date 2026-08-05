# Decision 037 — M3.2 Remaining Implementation-Stage Combination

**Date:** 2026-08-04
**Status:** ACCEPTED — OWNER APPROVED 2026-08-04
**Type:** Bounded governance record amending implementation staging and review cadence only.
**Not** a preregistration deviation. It changes no hypothesis, cohort window, maturity gate,
outcome definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage,
migration byte, implementation byte, test byte, script byte, or configuration byte — **no
executable byte changes with this record**. It authorizes no implementation of any stage, no
creation of `src/disclosure_drift/m3/acquisition.py`, no operational-catalog creation, no storage
integration, no scripted or live transport, no receipt emission, no network or CompanyFacts
enablement, no SEC connectivity testing, no live SEC access, no acquisition, no use of the M3.2A
ceiling 801, no T3/T4/T5 or Gate H execution, no migration, no receipt-schema change, no new
reason code, and no tag.
**Supersedes:** the remaining-stage cadence and commit-boundary provisions of the accepted T2
implementation-authorization packet (revision v2) **only** — every other packet requirement
remains controlling. **Amends:** accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §22 (the staged cadence) and
the directly consequent status and authority metadata (header, §1, §4, §8 T2 row, §25). It edits
**no accepted decision**: [Decision 035](decision_035_m3_2_t2_staged_implementation_authorization.md)
and [Decision 036](decision_036_m3_2_t2_1_stage_completion.md) are **not modified**, and the T2
packet and both M3.2 review artifacts are **preserved unchanged** (Decision 030 §10).
**Related:** Decisions 024 §8, 034, 035, 036; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's consolidation of the remaining Milestone 3.2 T2 implementation stages,
the resulting commit subjects and review cadence, and the replacement implementation-freeze
boundary for the independent T3 review.

---

## 1. Why this record is required

Decision 035 §7 item 8 fixed that **"stages may not be combined without a separate explicit owner
decision."** The owner has now issued that decision (§4, verbatim). This record is its durable
home: under CLAUDE.md's authority rules chat transcripts are not repository authority, and
`Milestones/STATUS.md` records workflow state but never overrides a decision. The consolidation is
therefore lawful precisely because it arrives as a numbered accepted record rather than as an
inference from the ledger.

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `7338ef26ccd9afb9b86a21e505127de4a61b4d2e` ("Record M3.2 T2.1 completion") |
| Parent | `7b2ffe643a2e2e600f148592fc9f8ded5695a279` — the accepted, published T2.1 implementation commit |
| `origin/main` | `7338ef26ccd9afb9b86a21e505127de4a61b4d2e`; `HEAD == origin/main`; ahead 0, behind 0 |
| Working tree | clean; nothing staged; no non-ignored untracked path; `.env` ignored and never read |
| Tags | `m3.1-complete` unchanged; **no tag at HEAD**; no tag created by any T2 stage |
| Contract before this amendment | SHA-256 `7a3fe7ff8503268c57081a45ae756989c2c2348c427842b4d2193acd04582b03` (independently recomputed; Decision 036 left the contract unchanged) |
| Contract after this amendment | SHA-256 `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7` |
| T2 packet (unchanged) | SHA-256 `621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599` |
| Migration chain | contiguous through `0013`; unchanged |
| M3.2 state | T2.1 published; **no work beyond T2.1 begun**; no `m3/acquisition.py`; no operational catalog; no receipt or acquisition output; no live SEC activity; ceiling 801 unused |
| Decision numbering | directory and registry both ended at **036** and agree; **037** verified genuinely unused in both |

**Baseline note, recorded rather than treated as a deviation.** The owner's stage-combination task
initially expected baseline `7b2ffe64…` and decision number `036`. Both were superseded during the
same working session by the immediately preceding, separately authorized governance pass, which
created accepted Decision 036 (T2.1 completion) and published it as `7338ef26…`. The owner
confirmed this correction. Numbering is **consistent** — directory and registry agree — and 036 is
simply already taken by a legitimate accepted record, so this record takes **037**. Decision 036 is
not created, replaced, amended, renamed, or overwritten, and no published history is rewritten.

## 3. T2.1 disposition — carried forward, not restated

Accepted **Decision 036** is the controlling record that stage **T2.1** is complete,
owner-accepted, and published at commit `7b2ffe643a2e2e600f148592fc9f8ded5695a279`; that its grant
is **exhausted**; that no implementation beyond T2.1 has begun; that both tracked network switches
remain `false`; and that T2.2 and later work remain unauthorized. This record adds nothing to and
subtracts nothing from that disposition.

T2.1 established: the fail-closed configuration layer; `network.m3_acquire_enabled` tracked as
`false`; all six M3.2 command surfaces; deterministic stage-not-enabled refusal; and **no
transport, catalog, receipt, evidence, or live-request capability**.

## 4. The owner instrument (verbatim, received 2026-08-04)

```text
OWNER_M3_2_REMAINING_STAGE_COMBINATION_DECISION: APPROVED

Date:

2026-08-04

The project owner accepts the completed and published M3.2 T2.1 implementation
stage and approves consolidation of the remaining T2 implementation stages.

Accepted T2.1 implementation commit:

7b2ffe643a2e2e600f148592fc9f8ded5695a279

Controlling staged authorization:

Decision 035

Controlling T2 packet:

Docs/m3/m3_2_t2_implementation_authorization_packet.md

Packet SHA-256:

621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599

T2.1 disposition

T2.1 is complete, reviewed, owner-accepted and published.

It established:

* the fail-closed configuration layer;
* network.m3_acquire_enabled, tracked as false;
* all six M3.2 command surfaces;
* deterministic stage-not-enabled refusal;
* no transport, catalog, receipt, evidence or live request capability.

Revised remaining implementation stages

The Decision 035 six-stage framework is amended for the remaining work.

Combined stage T2.2–T2.3

Canonical name:

M3.2 T2.2–T2.3 — Catalog, Immutable Storage and Acquisition Engine

This combined stage includes:

* operational-catalog initialization at migration chain 0013;
* external evidence-root containment and permission enforcement;
* content-addressed immutable raw-object integration;
* catalog and raw-object transaction ordering;
* duplicate and hash-conflict reconciliation;
* acquisition state machine;
* approved route enforcement;
* scripted transport integration only;
* request, retry, redirect and cooldown accounting;
* physical-attempt ceiling enforcement;
* stop-before-overflow;
* response classifications;
* required-object satisfaction;
* false-success prevention;
* receipt integration required by this stage.

The implementation may use internal subphases for validation, but it produces
one coherent stage candidate and at most one stage commit.

No owner review is required between the internal catalog/storage and
acquisition-engine subphases unless:

* an authorized-path expansion is required;
* a migration appears necessary;
* a new reason code appears necessary;
* the frozen receipt schema appears insufficient;
* the accepted architecture cannot be implemented as written;
* a BLOCKER or relevant MAJOR finding arises.

Expected stage commit subject:

Implement M3.2 T2.2-T2.3 acquisition foundation

Stage T2.4

Canonical name:

M3.2 T2.4 — Recovery, Reconciliation and Drift Control

T2.4 remains separate because it governs:

* recovery repair;
* SAFE, UNSAFE and UNDETERMINED handling;
* conservative interruption accounting;
* resume and predecessor binding;
* request reconciliation;
* required-object absence reporting;
* drift inspection;
* owner resume, new-run or abandonment boundaries.

Expected stage commit subject:

Implement M3.2 T2.4 recovery and reconciliation

Combined stage T2.5–T2.6

Canonical name:

M3.2 T2.5–T2.6 — Operator Surfaces and Integrated Implementation Candidate

This combined stage includes:

* dependent M3.2B plan derivation;
* frozen M3.2A input verification;
* zero-request dependent planning;
* m3 acquire --show-scope;
* final operator-facing command behavior;
* complete offline integration;
* full validation;
* implementation-path proof;
* T3 evidence assembly;
* creation of the implementation-freeze candidate.

It may use internal operator-surface and integration-validation subphases but
produces one coherent stage candidate and at most one stage commit.

Expected stage commit subject:

Complete M3.2 T2.5-T2.6 integrated implementation

The combined T2.5–T2.6 commit replaces the former standalone T2.6 commit as the
implementation-freeze candidate for independent T3 review.

Revised review and publication cadence

For each remaining stage:

1. ChatGPT issues a separate exact implementation packet.
2. Claude implements only that stage.
3. At most one stage commit is created.
4. The commit remains local.
5. ChatGPT reviews and accepts or rejects the stage.
6. An accepted stage commit is normally fast-forward pushed.
7. The next stage may begin only after the prior stage is accepted and
    published.

The three remaining stage candidates may not be combined further without a
new explicit owner decision.

No interim stage tag or T3 tag is authorized.

Preserved boundaries

This decision does not alter:

* the accepted M3.2 contract's substantive acquisition boundaries;
* the fifteen-path maximum T2 envelope;
* route or source restrictions;
* plan, budget or ceiling identities;
* raw-object or catalog semantics;
* receipt-schema restrictions;
* recovery or completion semantics;
* evidence requirements;
* independent T3 review;
* T4 preflight;
* per-window T5 authorization;
* Gate H.

Immediate authority

This decision changes stage and review cadence only.

It does not authorize implementation of T2.2–T2.3.

The next permissible action is preparation and owner review of the exact
combined T2.2–T2.3 implementation packet.

Negative authorization

This decision does not authorize:

* any new executable edit;
* creation of src/disclosure_drift/m3/acquisition.py;
* operational-catalog creation;
* storage integration;
* scripted or live transport;
* receipt emission;
* network or CompanyFacts enablement;
* SEC connectivity testing;
* live SEC access;
* acquisition;
* use of ceiling 801;
* T2.4 or T2.5–T2.6 implementation;
* T3, T4, T5 or Gate H execution;
* a migration;
* a receipt-schema change;
* a new reason code;
* a tag.

The exact next action after durable recording must be:

NEXT_AUTHORIZED_ACTION:
CHATGPT_PREPARATION_OF_COMBINED_M3_2_T2_2_T2_3_IMPLEMENTATION_PACKET

Owner:

Joseph Nihill, project owner acting through the ChatGPT owner decision

This is a transparent recorded owner decision, not a handwritten,
cryptographic or third-party digital signature.
```

Owner: **Joseph Nihill, project owner acting through the ChatGPT owner decision.** This is a
transparent recorded owner decision; it is not a handwritten, cryptographic, or third-party
digital signature.

## 5. The revised remaining-stage structure

The Decision 035 six-stage framework is amended for the remaining work. The cadence now has
**four stages in total** — one complete, three remaining:

| Stage | Canonical name | State | Exact commit subject |
|---|---|---|---|
| **T2.1** | Configuration and fail-closed command-authority layer | **complete, accepted, published** (Decision 036; commit `7b2ffe64…`) | `Implement M3.2 T2.1 authority layer` |
| **T2.2–T2.3** (combined) | **M3.2 T2.2–T2.3 — Catalog, Immutable Storage and Acquisition Engine** | next stage; **not authorized to begin** | `Implement M3.2 T2.2-T2.3 acquisition foundation` |
| **T2.4** | **M3.2 T2.4 — Recovery, Reconciliation and Drift Control** | later owner-gated stage | `Implement M3.2 T2.4 recovery and reconciliation` |
| **T2.5–T2.6** (combined) | **M3.2 T2.5–T2.6 — Operator Surfaces and Integrated Implementation Candidate** | later owner-gated stage; produces the **implementation-freeze candidate** | `Complete M3.2 T2.5-T2.6 integrated implementation` |

**Combined T2.2–T2.3 scope:** operational-catalog initialization at migration chain `0013`;
external evidence-root containment and permission enforcement; content-addressed immutable
raw-object integration; catalog and raw-object transaction ordering; duplicate and hash-conflict
reconciliation; the acquisition state machine; approved-route enforcement; **scripted transport
integration only**; request, retry, redirect, and cooldown accounting; physical-attempt ceiling
enforcement; stop-before-overflow; response classifications; required-object satisfaction;
false-success prevention; and the receipt integration this stage requires.

**T2.4 remains separate** because it governs recovery repair; `SAFE`/`UNSAFE`/`UNDETERMINED`
handling; conservative interruption accounting; resume and predecessor binding; request
reconciliation; required-object absence reporting; drift inspection; and the owner resume,
new-run, or abandonment boundaries.

**Combined T2.5–T2.6 scope:** dependent M3.2B plan derivation; frozen M3.2A input verification;
zero-request dependent planning; `m3 acquire --show-scope`; final operator-facing command
behaviour; complete offline integration; full validation; the implementation-path proof; T3
evidence assembly; and creation of the implementation-freeze candidate.

**Internal subphases.** A combined stage may use internal subphases for validation but produces
**one coherent stage candidate and at most one stage commit**. Within T2.2–T2.3, **no owner review
is required between the catalog/storage and acquisition-engine subphases unless** an
authorized-path expansion is required, a migration appears necessary, a new reason code appears
necessary, the frozen receipt schema appears insufficient, the accepted architecture cannot be
implemented as written, or a BLOCKER or relevant MAJOR finding arises — each of which is an
**immediate stop for owner adjudication**.

## 6. Review and publication cadence

For **each** remaining stage, in order: (1) ChatGPT issues a separate exact implementation packet;
(2) the implementation session implements **only that stage**; (3) **at most one stage commit** is
created, with the §5 subject; (4) the commit **remains local**; (5) ChatGPT reviews and accepts or
rejects the stage; (6) an accepted stage commit is **normally fast-forward pushed**; (7) the next
stage may begin **only after the prior stage is accepted and published**.

**The three remaining stage candidates may not be combined further without a new explicit owner
decision.** **No interim stage tag and no T3 tag is authorized.** The **combined T2.5–T2.6
commit replaces the former standalone T2.6 commit as the implementation-freeze candidate** for the
independent T3 review.

## 7. T2 packet disposition

The T2 implementation-authorization packet (revision v2, SHA-256
`621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599`) is **preserved unchanged** in
its submitted and accepted bytes. **This record supersedes only the packet's remaining-stage
cadence and commit-boundary provisions.** **All other packet requirements remain controlling** —
including the fifteen-path maximum envelope, the per-command dispositions, the R1 design, the F3
conservative interruption accounting, the F4 gate, the test plan, the validation strategy, the
stop-and-return conditions, and the nonchange proof.

## 8. Preserved boundaries

This record alters **none** of: the accepted contract's substantive acquisition boundaries; the
**fifteen-path maximum T2 envelope** (Decision 035 §6, still a ceiling and not a grant, with any
out-of-subset need an immediate stop for new owner adjudication); route or source restrictions;
plan, budget, or ceiling identities (plan `19be7bdc…`, budget `2d453e0b…`, **ceiling 801**);
raw-object or catalog semantics; receipt-schema restrictions (`m3-execution-receipt/2.0` frozen);
recovery or completion semantics; evidence requirements; the independent T3 review and its
independence standard; the T4 preflight; the per-window T5 authorization; or Gate H. The F4
evidence-index vocabulary decision remains unaccepted, open, and due no later than T4 and before
the first affected artifact is publicly indexed.

## 9. Immediate authority and negative authorization

**This decision changes stage and review cadence only. It does not authorize implementation of
T2.2–T2.3.** The next permissible action is **preparation and owner review of the exact combined
T2.2–T2.3 implementation packet**; preparing a packet approves nothing, and no implementation
session may begin before that packet is issued and the owner acts on it.

It authorizes none of: any new executable edit; creation of
`src/disclosure_drift/m3/acquisition.py`; operational-catalog creation; storage integration;
scripted or live transport; receipt emission; network or CompanyFacts enablement; SEC connectivity
testing; live SEC access; acquisition; use of ceiling 801; T2.4 or T2.5–T2.6 implementation; T3,
T4, T5, or Gate H execution; a migration; a receipt-schema change; a new reason code; or a tag.

## 10. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_037_m3_2_remaining_stage_combination.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 037 row and quick-lookup entry;
- `Milestones/contracts/m3_2.md` — the §22 cadence amendment and the directly consequent authority
  and current-state metadata only;
- `Milestones/STATUS.md` — current-state, cadence, and next-action updates;
- `Milestones/contracts/README.md` — the navigation prose the change makes stale;
- **one** governance-only commit with the subject `Combine remaining M3.2 implementation stages`,
  and **one** normal fast-forward push of `main`. **No tag.**

No implementation, test, configuration, migration, template, packet, review-artifact, or
private-evidence byte changes; `Docs/decision_index.md` is not edited; and Decisions 032–036 are
not modified.

## 11. Formal outcome

```text
M3_2_REMAINING_STAGES_COMBINED
```

**Next authorized action:**
`CHATGPT_PREPARATION_OF_COMBINED_M3_2_T2_2_T2_3_IMPLEMENTATION_PACKET` — preparation and owner
review of the exact combined T2.2–T2.3 implementation packet. **Combined T2.2–T2.3 is not
authorized to begin until that packet is issued and the owner acts on it**; T2.4 and combined
T2.5–T2.6 remain later owner-gated stages; and network enablement, live SEC access, acquisition,
operational-catalog creation, and ceiling-801 use all remain unauthorized.
