# Decision 035 — M3.2 T2 Staged Implementation Authorization (Stage T2.1 Only)

**Date:** 2026-08-04
**Status:** ACCEPTED — OWNER APPROVED 2026-08-04
**Type:** Bounded governance-authorization record, **and the durable recording the owner's
instrument makes a precondition of acting on it**. **Not** a preregistration deviation. It changes
no hypothesis, cohort window, maturity gate, outcome definition, threshold, seed, selection
methodology, S4/S5/S6 identity, hash preimage, migration byte, implementation byte, test byte,
script byte, or executable-configuration byte — **no executable byte changes with this record**.
It grants no T3 implementation acceptance, no T4 live-operation preflight authorization, no T5
per-window live-operation authorization, no network or CompanyFacts enablement, no SEC
connectivity testing, no HTTP request, no live SEC access, no operational-catalog creation or
population, no operational use of the M3.2A ceiling 801, no M3.2A or M3.2B execution, no Gate H,
no migration, no receipt-schema change, no new reason code, no tag, and no M3.3-or-later work.
**Supersedes:** nothing. **Amends:** the accepted M3.2 contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) **§22 only** — the
one-implementation-commit default is replaced by the six-stage T2.1–T2.6 commit and review
cadence (§7 below) — together with the directly consequent status and authority metadata (header,
§1, §8 T2 row, §16 preamble, §25). It edits **no** accepted decision: Decisions 032, 033, and 034
are untouched, and the T2 packet and both M3.2 review artifacts are **preserved unchanged**, in
the convention Decision 030 §10 fixes and Decision 032 §6 applied to the prior review artifact.
**Related:** Decisions 023 §7, 024 §8, 026 §21, 027 v0.2, 028–034;
[the T2 packet](../m3/m3_2_t2_implementation_authorization_packet.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's staged T2 implementation authorization for Milestone 3.2 — the approval
of the T2 packet revision v2 as the controlling implementation plan, the Decision 024 §8
disposition, the fifteen-path maximum envelope, the contract §22 six-stage amendment, the
stage-review and publication cadence, the **immediate stage limit to T2.1 only**, and the binding
dispositions of R1, F3, and F4.

---

## 1. Why this record is required

The owner's instrument (§4, verbatim) contains an express **durability condition**: it "may not be
acted upon until it is durably recorded in the repository as the next accepted numbered decision,
the contract and ledger are updated consistently, the governance commit is pushed normally, and
`HEAD == origin/main`." This record, with the contract and ledger updates it authorizes and the
push it directs, **is** that durable recording. It is a precondition to acting on the
authorization, not itself the act: even after recording, **a separate exact T2.1 execution packet
from the ChatGPT owner is still required before an implementation session begins** (§11).

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `8dd4a1675019a9a885b04703d18e0274173f52c3` ("Prepare M3.2 T2 implementation authorization packet") — the exact baseline the owner instrument binds to |
| `origin/main` | `8dd4a1675019a9a885b04703d18e0274173f52c3`; `HEAD == origin/main`; ahead 0, behind 0, no divergence |
| Working tree | clean; nothing staged; no non-ignored untracked path; `.env` ignored and never read |
| Tags | `m3.1-complete` unchanged (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`); no tag at HEAD |
| Protected bytes | `src` and `tests` byte-identical to the frozen accepted M3.1 SHA `970e050deb06910adcde8588101564beb7d19c74` (empty diff) |
| Migration chain | contiguous through `0013`; no migration proposed or authorized here |
| M3.2 state | **no M3.2 implementation exists; no operational catalog exists; no live SEC activity has occurred; ceiling 801 unused** |
| Decision numbering | directory and registry both ended at Decision 034; **035** verified genuinely unused in both |

## 3. The approved objects and their identities

| Object | Identity |
|---|---|
| T2 implementation-authorization packet | `Docs/m3/m3_2_t2_implementation_authorization_packet.md`, **revision v2**, SHA-256 `621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599` — **approved as the controlling implementation plan** and **preserved unchanged by this record** |
| Accepted M3.2 contract text (T1) | SHA-256 `75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3` |
| Contract file before this amendment | SHA-256 `a5ac0e8d042d90a7cff43a476258523ab71977b4b3d50ffe6777424720ae4ab2` |
| Contract file after this amendment | SHA-256 `7a3fe7ff8503268c57081a45ae756989c2c2348c427842b4d2193acd04582b03` — §22 plus the consequent authority metadata only; **no substantive route, source, plan, ceiling, storage, receipt, recovery, completion, evidence, or live-operation rule changed** |
| T1 acceptance | [Decision 034](decision_034_m3_2_contract_acceptance.md), outcome `M3_2_CONTRACT_ACCEPTED_AT_T1` |
| Independent rereview | artifact SHA-256 `91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf`, commit `3069b03ede9d805e9d0196a3e4c45c8cc68f42b7`, verdict `M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS` |

## 4. The owner authorization instrument (verbatim, received 2026-08-04)

```text
OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION: APPROVED_WITH_STAGE_LIMIT

Date:

2026-08-04

The project owner approves the Milestone 3.2 T2 implementation-authorization
packet, revision v2, as the controlling implementation plan.

Repository baseline:

8dd4a1675019a9a885b04703d18e0274173f52c3

Packet:

Docs/m3/m3_2_t2_implementation_authorization_packet.md

Packet revision:

v2

Packet SHA-256:

621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599

Accepted M3.2 contract text SHA-256:

75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3

Current post-acceptance contract-file SHA-256:

a5ac0e8d042d90a7cff43a476258523ab71977b4b3d50ffe6777424720ae4ab2

T1 acceptance decision:

Decision 034

Decision 024 §8 disposition

The owner determines:

1. The required accepted governance record exists.
2. The bounded M3.2 contract is accepted at T1.
3. This instrument supplies the explicit owner T2 authorization.
4. This instrument approves the packet §5 fifteen-path maximum implementation
    envelope, subject to the narrower per-stage path subsets.
5. All inherited prerequisite gates are satisfied.

The Decision 024 §8 entry conditions are therefore satisfied for the bounded
staged implementation authorized here.

Contract §22 amendment

The owner approves the packet's six-stage implementation and commit cadence.

This decision amends the accepted M3.2 contract §22 one-implementation-commit
default as follows:

* implementation is divided into stages T2.1 through T2.6;
* each stage produces at most one implementation commit;
* each stage uses the exact commit subject prescribed by packet §6;
* no interim commit inside a stage is permitted without a separate owner
    interruption ruling;
* each stage commit remains local until ChatGPT reviews and accepts that stage;
* after stage acceptance, one normal fast-forward push may publish the stage
    commit;
* the next stage may not begin before the prior stage is reviewed, accepted,
    and published;
* stages may not be combined without a separate explicit owner decision;
* no stage tag or T3 tag is authorized;
* the T2.6 commit becomes the implementation-freeze candidate for the
    independent T3 review.

This amendment changes only implementation staging and commit governance. It
does not alter routes, sources, plans, ceilings, storage semantics, recovery
semantics, evidence requirements, or live-operation authority.

Maximum T2 path envelope

The maximum T2 implementation envelope is exactly packet §5, P1–P8 and T1–T7.

The packet's declined and prohibited surfaces remain prohibited.

A discovered need to edit any path outside the relevant stage subset requires
an immediate stop and a new owner adjudication before the path is touched.

Immediate stage limit

This decision approves the staged T2 framework but grants immediate executable
implementation authority only for stage T2.1.

T2.1 authorized paths:

* configs/project.yaml
* src/disclosure_drift/config.py
* src/disclosure_drift/cli.py
* src/disclosure_drift/m3/__init__.py
* tests/integration/test_m3_cli.py
* tests/unit/test_config.py

No other production or test path may change during T2.1.

Stages T2.2 through T2.6 remain owner-gated and are not authorized to begin.

T2.1 permitted work

T2.1 may implement only:

* network.m3_acquire_enabled: false in the tracked default configuration;
* m3_acquire_enabled: bool = False in NetworkSection;
* strict parsing and fail-closed configuration behavior;
* parser and command-dispatch skeletons for all six M3.2 command surfaces;
* refusal behavior for unavailable or unauthorized command paths;
* the m3 acquire --live refusal skeleton;
* proof that no transport can be constructed by the T2.1 implementation;
* proof that existing M2.2 commands remain governed only by
    network.enabled;
* the T2.1 tests and positive controls named by the packet.

T2.1 must not implement acquisition, storage integration, reconciliation,
drift processing, recovery repair, dependent-plan derivation, receipt
emission, or transport construction.

Network and governance enforcement

network.enabled remains false and unchanged.

network.m3_acquire_enabled is added with a tracked default of false and may
not be committed true.

Only the future canonical m3 acquire --live path may consume the scoped key.

T3 acceptance and T5 live-operation authorization remain governance and
preflight requirements. T2.1 must not invent a fake machine-readable
"T3 accepted" or "T5 authorized" boolean, token, bypass, or hard-coded
authorization.

No implementation-stage test may contact the SEC or use the real SEC identity.

R1, F3, and F4

The packet's R1 design is accepted and binding for the stages where it becomes
applicable.

The conservative interruption-accounting requirements are accepted and
binding for T2.4.

The proposed evidence-index vocabulary additions are not accepted by this
decision. They remain a separate governance decision required no later than
T4 and before the first affected artifact is publicly indexed.

Negative authorization

This decision does not authorize:

* any T2 stage beyond T2.1;
* network or CompanyFacts enablement;
* SEC connectivity testing;
* any HTTP request;
* live SEC access;
* creation or population of the operational catalog;
* operational use of ceiling 801;
* M3.2A or M3.2B execution;
* Gate H;
* any migration;
* any receipt-schema change;
* any new reason code;
* any tag;
* any M3.3 or later work.

Durability condition

This authorization may not be acted upon until it is durably recorded in the
repository as the next accepted numbered decision, the contract and ledger are
updated consistently, the governance commit is pushed normally, and
HEAD == origin/main.

After durable recording, a separate exact T2.1 execution packet from ChatGPT
is still required before an implementation session begins.

Owner:

Joseph Nihill, project owner acting through the ChatGPT owner decision

Recorded authorization reference:

ChatGPT owner M3.2 T2 staged-implementation authorization dated 2026-08-04,
bound to repository baseline
8dd4a1675019a9a885b04703d18e0274173f52c3 and packet SHA-256
621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599.

This is a transparent recorded owner authorization, not a handwritten,
cryptographic, or third-party digital signature.
```

Owner: **Joseph Nihill, project owner acting through the ChatGPT owner decision.** This is a
transparent recorded owner authorization; it is not a handwritten, cryptographic, or third-party
digital signature.

## 5. Decision 024 §8 condition satisfaction

The owner determines all five entry conditions satisfied **for the bounded staged implementation
authorized here** — and for nothing wider:

| # | Condition (Decision 024 §8) | Owner determination | Where proven |
|---|---|---|---|
| 1 | A separate accepted governance record where the phase requires one | **Exists** | Decisions 027 v0.2, 028, 029, 030 fix the M3.2 methodology; Decision 034 accepts the contract |
| 2 | A bounded implementation contract for that phase | **Accepted at T1** | `Milestones/contracts/m3_2.md` (accepted text `75e7e5a1…`), Decision 034 |
| 3 | Explicit owner authorization | **Supplied by this instrument** | §4 above |
| 4 | Exact path authorization | **The packet §5 fifteen-path maximum envelope, subject to the narrower per-stage subsets** | §6 below; T2 packet v2 §5 |
| 5 | Satisfaction of the phase's inherited prerequisite gates | **Satisfied** | Gate F readiness token; M3.1 owner-accepted (Decision 031) and checkpointed at `m3.1-complete`; plan `19be7bdc…`, budget `2d453e0b…`, ceiling 801 accepted; M3-L11/M3-L12 `CLOSED`; D023-O1 latent |

Milestones 0–2 closeout, the precondition Decision 024 §9 imposes before any Milestone 3
implementation, is complete (Decision 026).

## 6. Maximum T2 path envelope

The maximum T2 implementation envelope is **exactly T2 packet v2 §5, P1–P8 and T1–T7** —
`configs/project.yaml`; `src/disclosure_drift/config.py`;
`src/disclosure_drift/m3/acquisition.py` (new); `src/disclosure_drift/cli.py`;
`src/disclosure_drift/m3/request_plan.py`; `src/disclosure_drift/m3/recovery.py`;
`src/disclosure_drift/reasons.py` (reserved — an unregistered condition is a stop, never a code
invented under T2); `src/disclosure_drift/m3/__init__.py`;
`tests/unit/test_m3_acquisition.py`; `tests/unit/test_m3_dependent_plan.py`;
`tests/unit/test_m3_recover.py`; `tests/integration/test_m3_cli.py`;
`tests/unit/test_m3_request_plan.py`; `tests/unit/test_m3_recovery.py`;
`tests/unit/test_config.py`.

**The envelope is a ceiling, not a grant** — each stage may touch only its own narrower subset.
**The packet's declined and prohibited surfaces remain prohibited**, including
`sec/census_orchestrator.py`, `sec/index_retrieval.py`, `src/disclosure_drift/m3/receipt.py`
(frozen schema), every migration, `tests/integration/test_no_network.py` and `tests/conftest.py`
(both byte-identical), the accepted M3.1 evidence and identities, and the `m3.1-complete` tag.
**A discovered need to edit any path outside the relevant stage subset requires an immediate stop
and a new owner adjudication before the path is touched.**

## 7. Contract §22 amendment — the six-stage cadence

Accepted contract §22's one-implementation-commit default is **replaced** by:

1. implementation is divided into stages **T2.1 through T2.6**;
2. **each stage produces at most one implementation commit**;
3. each stage uses the **exact commit subject prescribed by T2 packet v2 §6**;
4. **no interim commit inside a stage** without a separate owner interruption ruling;
5. each stage commit **remains local until ChatGPT reviews and accepts that stage**;
6. after stage acceptance, **one normal fast-forward push** may publish the stage commit;
7. **the next stage may not begin** before the prior stage is reviewed, accepted, and published;
8. **stages may not be combined** without a separate explicit owner decision;
9. **no stage tag and no T3 tag** is authorized;
10. the **T2.6 commit becomes the implementation-freeze candidate** for the independent T3 review.

This amendment changes **only implementation staging and commit governance**. It alters no route,
source, plan, ceiling, storage semantic, recovery semantic, evidence requirement, or
live-operation authority. The governance-only M3.2 acceptance-commit rule (master plan M3.2 §33)
and the final annotated-tag rule (`m3.2-complete`, only after independent M3.2 acceptance; master
plan §34) are **preserved unchanged**.

## 8. Immediate stage limit — T2.1 only

This decision approves the staged framework but grants **immediate executable implementation
authority for stage T2.1 alone**. **Stages T2.2 through T2.6 remain owner-gated and are not
authorized to begin.**

**T2.1 authorized paths — exactly six, and no other production or test path may change during
T2.1:**

1. `configs/project.yaml`
2. `src/disclosure_drift/config.py`
3. `src/disclosure_drift/cli.py`
4. `src/disclosure_drift/m3/__init__.py`
5. `tests/integration/test_m3_cli.py`
6. `tests/unit/test_config.py`

**T2.1 may implement only:** `network.m3_acquire_enabled: false` in the tracked default
configuration; `m3_acquire_enabled: bool = False` in `NetworkSection`; strict parsing and
fail-closed configuration behaviour; parser and command-dispatch skeletons for all six M3.2
command surfaces; refusal behaviour for unavailable or unauthorized command paths; the
`m3 acquire --live` refusal skeleton; proof that **no transport can be constructed** by the T2.1
implementation; proof that existing M2.2 commands remain governed **only** by `network.enabled`;
and the T2.1 tests and positive controls the packet names.

**T2.1 must not implement** acquisition, storage integration, reconciliation, drift processing,
recovery repair, dependent-plan derivation, receipt emission, or transport construction.

## 9. Network and governance enforcement

`network.enabled` **remains `false` and unchanged**. `network.m3_acquire_enabled` is added with a
**tracked default of `false` and may not be committed `true`**. Only the future canonical
`m3 acquire --live` path may consume the scoped key. **T3 acceptance and T5 live-operation
authorization remain governance and preflight requirements: T2.1 must not invent a fake
machine-readable "T3 accepted" or "T5 authorized" boolean, token, bypass, or hard-coded
authorization.** **No implementation-stage test may contact the SEC or use the real SEC
identity.**

## 10. R1, F3, and F4

- **R1 (rereview MINOR; Decision 034 §6).** The packet's R1 design is **accepted and binding for
  the stages where it becomes applicable** — item-level absent-object identities resident in the
  operational catalog and the private reconciliation report, never in the frozen receipt;
  `completed_with_absences` as a window governance classification, never a receipt
  `completion_status` value; the plan-hash linkage across receipt, catalog,
  `m3 reconcile-requests`, and Gate H; and the non-vacuous frozen-receipt-schema tests.
- **F3 (conservative interruption accounting).** Accepted and **binding for T2.4** — the full
  per-route `A_reachable` charge for an unrecorded in-flight request, the `UNDETERMINED` stop,
  the carried-forward accounting that can never raise or reset the ceiling, and the eight
  kill-point tests.
- **F4 (evidence-index vocabulary).** The packet's proposed additions are **NOT accepted by this
  decision**. They **remain a separate governance decision, required no later than T4 and before
  the first affected artifact is publicly indexed**. No template is edited here, and no artifact
  may be publicly indexed under an unaccepted type.

## 11. Durability condition and what must still happen

The owner's instrument may not be acted upon until it is **durably recorded as the next accepted
numbered decision, the contract and ledger updated consistently, the governance commit pushed
normally, and `HEAD == origin/main`** — which this record and its commit discharge.

**After durable recording, a separate exact T2.1 execution packet from the ChatGPT owner is still
required before an implementation session begins.** Neither this record, nor the contract
amendment, nor the approval of the staged framework starts any executable work.

## 12. Negative authorization

This decision does not authorize: **any T2 stage beyond T2.1**; network or CompanyFacts
enablement; SEC connectivity testing; **any HTTP request**; live SEC access; creation or
population of the operational catalog; operational use of ceiling 801; M3.2A or M3.2B execution;
Gate H; any migration; any receipt-schema change; any new reason code; any tag; or any M3.3 or
later work. It does not grant T3, T4, T5, or T6; does not edit accepted Decisions 032, 033, or
034, the T2 packet, either M3.2 review artifact, `Docs/decision_index.md`, any migration, any
template, or any private evidence; and closes, opens, or edits no limitations-register entry.

## 13. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_035_m3_2_t2_staged_implementation_authorization.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 035 row and quick-lookup entry;
- `Milestones/contracts/m3_2.md` — the §22 amendment and the directly consequent authority
  metadata only;
- `Milestones/contracts/README.md` — the m3_2 authority-state wording;
- `Milestones/STATUS.md` — current stage, blocker, authority state, next-action marker, and the
  directly dependent machine markers;
- **one** bounded governance commit with the subject `Record staged M3.2 T2 authorization`, and
  **one** normal fast-forward push of `main`. **No tag.**

No implementation, test, script, migration, template, executable-configuration, packet,
review-artifact, or private-evidence byte changes.

## 14. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner instrument is recorded verbatim and neither
broadened nor reinterpreted; (2) the contract carries the §22 amendment and the T2.1-only
authority state, with every substantive rule unchanged and the post-amendment SHA-256 recorded
here; (3) Decision 035 is unique — no other decision file or registry row carries the number, and
directory and registry agree; (4) `src`, `tests`, `configs`, migrations, and templates remain
byte-identical; (5) `git diff --check`, `make context`, `make secrets`, and `make hygiene` pass;
(6) the commit carries exactly the §13 paths; (7) the next-action marker occurs exactly once;
(8) no tag is created; (9) no private path, SEC identity, or private-evidence content appears in
any changed file.

## 15. Formal outcome

```text
M3_2_T2_STAGED_IMPLEMENTATION_AUTHORIZED
```

**Next authorized action:** `CHATGPT_ISSUANCE_OF_M3_2_T2_1_IMPLEMENTATION_PACKET` — the ChatGPT
owner issues the exact T2.1 implementation packet. **No implementation session may begin before
it**, stages T2.2 through T2.6 remain owner-gated, and network enablement, live SEC access,
acquisition, operational-catalog creation, and ceiling-801 use all remain unauthorized.
