# Decision 036 — M3.2 Stage T2.1 Acceptance and Completion

**Date:** 2026-08-04
**Status:** ACCEPTED — OWNER APPROVED 2026-08-04
**Type:** Bounded governance-acceptance record for one implementation stage. **Not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte — **no executable byte
changes with this record**. It grants no T2.2-or-later stage authority, no T3 implementation
acceptance, no T4 preflight, no T5 live-operation authorization, no network or CompanyFacts
enablement, no SEC connectivity testing, no live SEC access, no acquisition, no operational-catalog
creation, no use of the M3.2A ceiling 801, no Gate H, no migration, no receipt-schema change, no
new reason code, no tag, and no M3.3-or-later work.
**Supersedes:** nothing. **Amends:** nothing — accepted
[Decision 035](decision_035_m3_2_t2_staged_implementation_authorization.md) is **not modified in
place** (Decision 030 §10), and the accepted M3.2 contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) is **preserved unchanged**:
implementation progress belongs in this record and the status ledger, not in the contract.
**Related:** Decisions 024 §8, 034, 035; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of Milestone 3.2 implementation stage **T2.1**, the durable
record of its published commit and validation evidence, and the confirmation that stages T2.2
through T2.6 remain separately owner-gated.

---

## 1. Why this record is required

Two owner instruments govern this stage boundary — the T2.1 stage acceptance (§4) and the
authorization to record its completion (§5). Both were issued conversationally. Under CLAUDE.md's
authority rules, **chat transcripts are not repository authority**: only what is committed to
`Docs/Decisions/`, a migration, or source under `src/` binds a future session, and
`Milestones/STATUS.md` "records workflow state but never overrides a decision." A status-ledger
entry alone would therefore leave the owner's acceptance without a durable home. This record is
that home, following the precedent of Decisions 031 (M3.1 acceptance), 034 (T1 contract
acceptance), and 035 (staged T2 authorization).

Decision 035 §7 already fixed the stage cadence — each stage commit stays local until reviewed and
accepted, then publishes by one normal fast-forward push, and the next stage may not begin before
the prior stage is reviewed, accepted, and published. **This record fixes no new rule**; it records
that the T2.1 pass through that cadence completed.

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| `HEAD` == `origin/main` | `7b2ffe643a2e2e600f148592fc9f8ded5695a279` — the published T2.1 implementation commit |
| Working tree | clean; nothing staged; no non-ignored untracked path; `.env` ignored and never read |
| Tags | `m3.1-complete` unchanged (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`); **no tag at HEAD**; no tag created by T2.1 |
| Migration chain | contiguous through `0013`; unchanged by T2.1 |
| M3.2 state | T2.1 published; **T2.2–T2.6 not begun**; no `m3/acquisition.py`; no operational catalog; no live SEC activity; ceiling 801 unused |
| Decision numbering | directory and registry both ended at Decision 035; **036** verified genuinely unused in both |

## 3. The accepted stage

| Field | Value |
|---|---|
| Stage | **T2.1 — configuration and fail-closed command-authority layer** (T2 packet v2 §6) |
| Implementation commit | `7b2ffe643a2e2e600f148592fc9f8ded5695a279` |
| Parent | `9730f8b564f49b8fdba76da31cf6d2fa0b6aacc6` |
| Tree | `0ae3cb0ba8bd9484c02f8920e2ed44c30a96a87e` |
| Commit subject | `Implement M3.2 T2.1 authority layer` (the exact subject T2 packet v2 §6 prescribes) |
| Published | one normal fast-forward push, `9730f8b..7b2ffe6 main -> main`; no tag pushed |
| Formal outcome | `M3_2_T2_1_IMPLEMENTATION_PUBLISHED` |

**Changed paths — exactly the six Decision 035 §8 authorized, and no seventh:**
`configs/project.yaml` · `src/disclosure_drift/config.py` · `src/disclosure_drift/cli.py` ·
`src/disclosure_drift/m3/__init__.py` · `tests/integration/test_m3_cli.py` ·
`tests/unit/test_config.py`.

**Proven byte-identical across the stage commit:** `tests/integration/test_no_network.py`;
`tests/conftest.py` (the suite-wide socket guard); `src/disclosure_drift/m3/receipt.py` (the frozen
receipt schema); `src/disclosure_drift/reasons.py` (the reason registry); every migration; and all
of `Docs/` and `Milestones/`.

**Validation evidence:** targeted suite **126 passed, with no skipped and no xfailed test**
(`tests/unit/test_config.py` and `tests/integration/test_m3_cli.py`); `ruff check` and
`ruff format --check` clean over the five touched Python files; `mypy` clean over the three touched
source files; `make secrets` 0 findings; `make hygiene` 0 findings; `git diff --check` clean; the
changed-path set proven a subset of the authorization.

## 4. The owner stage-acceptance instrument (verbatim, received 2026-08-04)

```text
OWNER_M3_2_T2_1_STAGE_ACCEPTANCE: APPROVED

Date:

2026-08-04

The project owner accepts the Milestone 3.2 T2.1 implementation candidate.

Accepted stage:

T2.1 — configuration and fail-closed command-authority layer

Accepted implementation commit:

7b2ffe643a2e2e600f148592fc9f8ded5695a279

Accepted parent:

9730f8b564f49b8fdba76da31cf6d2fa0b6aacc6

Accepted commit subject:

Implement M3.2 T2.1 authority layer

Accepted changed paths:

* configs/project.yaml
* src/disclosure_drift/config.py
* src/disclosure_drift/cli.py
* src/disclosure_drift/m3/init.py
* tests/integration/test_m3_cli.py
* tests/unit/test_config.py

The owner accepts that:

1. network.m3_acquire_enabled was added with a tracked default of false.
2. network.enabled remains false and retains its existing semantics.
3. The two network switches are independent.
4. All six planned M3.2 command surfaces are recognized.
5. Every M3.2 command remains fail-closed and unavailable at T2.1.
6. No switch combination can reach or construct transport.
7. No fake T3, T4, T5, readiness, or owner-authorization state was introduced.
8. Existing M2.2 commands remain controlled only by network.enabled.
9. No operational catalog, receipt, evidence artifact, raw object, token,
    logical request, physical attempt, hostname lookup, socket operation, or SEC
    contact occurred.
10. Tests and validation are sufficient for the bounded T2.1 stage.
11. Reported findings M1 and M2 are nonblocking.
12. Reported optimization O1 was corrected before acceptance.

This acceptance authorizes one normal fast-forward publication of the accepted
T2.1 commit after the required ancestry and integrity checks pass.

This acceptance does not authorize:

* any edit to the accepted T2.1 commit;
* T2.2 or any later implementation stage;
* creation of m3/acquisition.py;
* operational-catalog creation;
* storage integration;
* transport construction;
* receipt emission;
* request execution or attempt accounting;
* network or CompanyFacts enablement;
* SEC connectivity testing;
* live SEC access;
* use of ceiling 801;
* M3.2A, M3.2B, Gate H, or M3.3 work;
* a tag.

Do not amend, rebase, reset, recreate, squash, or otherwise rewrite the
accepted T2.1 commit.

After successful publication, the next action is preparation and owner review
of the exact T2.2 implementation packet. T2.2 remains unauthorized until that
packet is separately issued.

Owner:

Joseph Nihill, project owner acting through the ChatGPT owner decision

Recorded acceptance reference:

ChatGPT owner T2.1 stage acceptance dated 2026-08-04, bound to implementation
commit 7b2ffe643a2e2e600f148592fc9f8ded5695a279 and parent
9730f8b564f49b8fdba76da31cf6d2fa0b6aacc6.

This is a transparent recorded owner acceptance, not a handwritten,
cryptographic, or third-party digital signature.
```

**One transcription note, recorded rather than silently corrected.** The instrument's fourth
accepted path reads `src/disclosure_drift/m3/init.py`; the actual committed path is
`src/disclosure_drift/m3/__init__.py`. This is a markdown underscore-rendering artifact naming the
same file. The committed six-path delta matches the authorization exactly, verified by
`git diff --name-only`, so nothing turns on the difference.

## 5. The owner completion-recording authorization (verbatim, received 2026-08-04)

```text
OWNER_M3_2_T2_1_COMPLETION_RECORDING_AUTHORIZATION: APPROVED

The project owner accepts the published Milestone 3.2 T2.1 implementation
stage and authorizes a governance-only update recording its completion.

Date:

2026-08-04

Accepted T2.1 implementation commit:

7b2ffe643a2e2e600f148592fc9f8ded5695a279

Accepted T2.1 parent:

9730f8b564f49b8fdba76da31cf6d2fa0b6aacc6

Accepted stage outcome:

M3_2_T2_1_IMPLEMENTATION_PUBLISHED

The owner finds that:

1. T2.1 was implemented within its exact six-path authorization.
2. T2.1 was reviewed, accepted and published.
3. Both tracked network switches remain false.
4. All M3.2 command surfaces remain fail-closed.
5. No transport, catalog, receipt, evidence artifact or live request was
    produced.
6. T2.2 through T2.6 remain separately owner-gated.
7. The next permissible task is preparation and owner review of the exact T2.2
    implementation packet.

This authorization permits only:

* durable recording of T2.1 completion;
* correction of stale current-state and next-action ledger text;
* any strictly required navigation update;
* one governance-only commit and normal fast-forward push.

This authorization does not permit:

* T2.2 implementation;
* creation of src/disclosure_drift/m3/acquisition.py;
* operational-catalog creation;
* storage integration;
* network or CompanyFacts enablement;
* SEC connectivity testing;
* transport construction;
* receipt generation;
* live SEC access;
* acquisition;
* use of ceiling 801;
* a tag.

The exact next-action marker after this update must be:

NEXT_AUTHORIZED_ACTION: CHATGPT_PREPARATION_OF_M3_2_T2_2_IMPLEMENTATION_PACKET
```

Owner: **Joseph Nihill, project owner acting through the ChatGPT owner decision.** This is a
transparent recorded owner acceptance and authorization; it is not a handwritten, cryptographic,
or third-party digital signature.

## 6. What the accepted stage delivered

Confirmed by the owner and independently verified from the committed code before publication:

1. `network.m3_acquire_enabled` added to the tracked default configuration with the value
   **`false`**, and to `NetworkSection` as `m3_acquire_enabled: bool = False`.
2. `network.enabled` **remains `false`** with its existing Stage M2.2 semantics unchanged.
3. **The two switches are independent in both directions** — neither infers, mutates, or reaches
   the other — and strict unknown-field rejection (`extra="forbid"`, `frozen=True`) is intact with
   no environment fallback or coercion for either.
4. **All six** planned M3.2 command surfaces are recognized by the parser: `m3 acquire` (with
   `--live` and `--show-scope`), `m3 derive-dependent-plan`, `m3 reconcile-requests`,
   `m3 show-drift`, `m3 recover`.
5. **Every one of them is fail-closed and unavailable**, refusing deterministically with
   `EXIT_STAGE_NOT_ENABLED` (3), no traceback, no private path, no identity, and no implied
   authorization. `--show-scope` prints a static, non-operational authority summary and is still a
   refusal — it never returns success while unimplemented.
6. **No switch combination reaches or constructs transport**, proven across the complete
   six-row conjunction including both switches true with `--live`; `httpx` is never loaded.
7. **No fake T3, T4, T5, readiness, or owner-authorization state was introduced** — the refusal is
   unconditional, so nothing simulates a governance gate.
8. **Existing M2.2 commands remain controlled only by `network.enabled`**, proven behaviourally
   (identical outcomes with the acquire switch true and false, across both settings of the global
   switch) and structurally (`_sec_command` reads `config.network.enabled` and never
   `m3_acquire_enabled`).
9. **Nothing operational was produced**: no transport, operational catalog, receipt, evidence
   artifact, raw object, token, logical request, physical attempt, hostname lookup, socket
   operation, or SEC contact.

The owner accepts the reported findings **M1** (a pre-existing test whose "unknown subcommand"
example became a recognized command, retargeted inside an authorized test path with no assertion
weakened) and **M2** (the configuration loader *refuses* an unrecognized `DISCLOSURE_DRIFT_*`
variable rather than ignoring it — stronger than assumed, with the test corrected to the actual
behaviour) as **nonblocking**, and records that optimization **O1** (a test-fixture aliasing defect
that would have made the independence comparisons vacuous) was **corrected before acceptance** and
locked with a dedicated positive control.

## 7. Stage boundary — what remains gated

**Stages T2.2 through T2.6 remain separately owner-gated and are not authorized to begin.** Under
Decision 035 §7 each requires its own owner act after the prior stage is reviewed, accepted, and
published; T2.1's completion advances the cadence by exactly one stage and confers nothing further.
The Decision 035 §6 fifteen-path maximum envelope is unchanged and remains a ceiling, not a grant:
**a discovered need to edit any path outside the relevant stage subset is an immediate stop for a
new owner adjudication before the path is touched.**

`src/disclosure_drift/m3/acquisition.py` does not exist and is not authorized. T3 implementation
acceptance, T4 live-operation preflight, and each per-window T5 live-operation authorization remain
separate later owner acts. **`NETWORK_AUTHORIZATION: NONE`**, the ceiling **801 remains unused**,
and the **F4** evidence-index vocabulary decision remains unaccepted, open, and due no later than
T4 and before the first affected artifact is publicly indexed.

## 8. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_036_m3_2_t2_1_stage_completion.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 036 row and quick-lookup entry;
- `Milestones/STATUS.md` — the current-state and next-action corrections;
- `Milestones/contracts/README.md` — the one materially stale navigation sentence;
- **one** governance-only commit with the subject `Record M3.2 T2.1 completion`, and **one** normal
  fast-forward push of `main`. **No tag.**

**The accepted M3.2 contract is deliberately preserved unchanged.** Its header authority line
(`IMPLEMENTATION_AUTHORIZATION: STAGE T2.1 ONLY`) remains a true ceiling — no stage beyond T2.1 is
authorized — and stage progress belongs in this record and the ledger rather than in the contract.
No executable, test, configuration, migration, template, packet, review-artifact, or
private-evidence byte changes, and `Docs/decision_index.md` is not edited.

## 9. Formal outcome

```text
M3_2_T2_1_ACCEPTED_AND_PUBLISHED
```

**Next authorized action:** `CHATGPT_PREPARATION_OF_M3_2_T2_2_IMPLEMENTATION_PACKET` — preparation
and owner review of the exact T2.2 implementation packet. **T2.2 remains unauthorized until that
packet is separately issued and the owner acts on it**, and network enablement, live SEC access,
acquisition, operational-catalog creation, and ceiling-801 use all remain unauthorized.
