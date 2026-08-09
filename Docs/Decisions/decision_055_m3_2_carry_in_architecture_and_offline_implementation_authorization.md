# Decision 055 — M3.2 Carry-In Architecture and Offline Implementation Authorization

**Date:** 2026-08-08
**Status:** ACCEPTED — OWNER APPROVED 2026-08-08
**Authority classification:**
`M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED`
**Type:** Governance-only record fixing the **binding owner architecture** for the **M3-L16**
consumed-baseline carry-in problem and the **M3-L14** fail-closed correction, and authorizing **one
bounded OFFLINE implementation candidate** on an exact sixteen-path envelope. It is **not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, governed identity, hash preimage, migration byte,
implementation byte, test byte, receipt byte, reason code, or configuration byte — **no executable
byte changes with this record**, and **no operational state changes with this record**. It is the
authorization, not the implementation: the sixteen-path candidate is written later, under a separate
owner packet, and **this record accepts no candidate and closes no limitation**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–054 are byte-unchanged.
Every durable review artifact, [`Docs/decision_index.md`](../decision_index.md),
[`Docs/m3/templates/evidence_index.md`](../m3/templates/evidence_index.md), every migration, every
configuration, every reason code, every production source, and every test are byte-unchanged by this
record. The accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md),
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md),
[`Docs/m3/templates/gate_h_checklist.md`](../m3/templates/gate_h_checklist.md),
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md), and
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md) are **byte-unchanged by this record** and
are edited only later, inside the §10 envelope. Stage progress is recorded here, in the registry, and
in the ledger — never in the contract.
**Narrowly supersedes:** exactly four things, and nothing else (§12) — contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §12 **only** where it recognizes
solely predecessor-receipt carry-forward, adding the one-use non-resume carry-in root; the prior
clauses freezing `src/disclosure_drift/m3/receipt.py` and receipt schema `m3-execution-receipt/2.0`
(contract §16; [Decision 045](decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md)),
**solely** for a backward-compatible schema `3.0` and version dispatch; the prior withholding of
implementation authority, **solely** for the sixteen-path offline candidate at §10; and **M3-L14**'s
unresolved owner choice, selecting the fail-closed one-to-one cardinality rule.
**Preserves unchanged:** the cumulative M3.2A ceiling **801** and its binding to plan hash
`19be7bdc…`; accepted [Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md)
§8's predecessor-receipt requirement for every resume and its no-automatic-resume rule;
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) §8's receiptless
inspection-only boundary and §9's permanent old-run no-resume ruling;
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §§13–14;
[Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) §§5–7 and its
**exhausted** one-time execution authority;
[Decision 054](decision_054_m3_2_interrupted_run_closure_acceptance.md) in full, including
`HISTORICAL_JOB_STATE_NOW: stopped`, recovery `UNDETERMINED`, zero historical
`ops_retrieval_attempts` rows with no backfill, and the absence of a terminating receipt; migrations
`0001`–`0013`; **M3-L15** byte-for-byte; and every route, host, method, spacing, content, provenance,
leakage, fail-closed, evidence-preservation, determinism, and owner-gated-live-operation rule not
expressly addressed here.
**Related:** [Decision 054](decision_054_m3_2_interrupted_run_closure_acceptance.md) (whose §15 next
authorized action — `CLAUDE_M3_2_M3_L16_CARRY_IN_ARCHITECTURE_DISCOVERY_PACKET` — was issued and
completed as read-only validation, and whose findings this record adjudicates);
[Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md);
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §§7, 9 (the
origin of **M3-L14** and **M3-L16**);
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md);
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md);
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §§5, 8, 9, 12, 16, 17, 19;
[`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md) §§4.8, 11, 12;
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md) **M3-L14**, **M3-L15**, **M3-L16**;
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** what this record does and does not do (§1); the owner determination and the verbatim
approval (§2); authority verification (§3); the accepted validation facts (§4); ruling **055-A**,
ceiling and plan (§5); ruling **055-B**, the one-use carry-in authority (§6); ruling **055-C**,
receipt schema `3.0` and recovery arithmetic (§7); ruling **055-D**, the M3-L14 fail-closed
correction (§8); ruling **055-E**, the historical orphan Path B (§9); ruling **055-F**, the bounded
offline implementation authorization (§10); ruling **055-G**, validation and review gates (§11);
ruling **055-H**, narrow supersession and continuing authority (§12); the limitations disposition
(§13); the path and publication boundary for **this recording** (§14); the recorded status (§15); and
the formal outcome and exact next authorized action (§16).

---

## 1. What this record does, and what it does not

Seven determinations, which must not be collapsed:

1. **Architecture acceptance.** The owner's carry-in architecture is **fixed and binding** as recorded
   at §§5–9. It is recorded here **without reinterpretation**; where a summary elsewhere is shorter,
   these sections control.
2. **Bounded implementation authorization.** Exactly one **OFFLINE** implementation candidate is
   authorized, on the exact sixteen paths at §10 and no seventeenth, producing exactly one local
   candidate commit with a fixed subject, **unpushed and untagged** (§10).
3. **M3-L14's open owner choice is resolved.** The register's two-way choice is decided in favour of
   the **fail-closed one-to-one reservation-consumption rule** (§8). Resolving the choice is **not**
   closing the entry.
4. **The historical orphan takes Path B.** A separately authorized, offline, one-time, verified
   adoption must precede any clean carry-in run. **Decision 055 neither designs it in executable
   detail nor performs it** (§9).
5. **No limitation is closed.** **M3-L14** and **M3-L16** remain **`ACTIVE`**, now carrying a selected
   architecture and an implementation authority. **M3-L15** is untouched and byte-unchanged.
   **M3-L16 continues to block every clean-run and live authorization** (§13).
6. **No candidate is accepted.** This record accepts no code, no test, no review, and no evidence
   produced later. Candidate acceptance, M3-L14 closure, M3-L16 closure, orphan adoption, network,
   live invocation, T6, M3.2B, and Gate H each require a **later separate owner act** (§10, §12).
7. **What this record is not.** It is **not** implementation, **not** operational-state authority,
   **not** network or SEC authority, **not** resume, retry, replacement, or clean-run authority, and
   **not** a live-readiness claim. **The project is not ready for live operation, and M3.2 is not
   complete.**

## 2. The owner determination, recorded without alteration

The owner's approval was given on **2026-08-08** and is recorded verbatim:

```text
approve Decision 055.
```

The substance approved was issued as the Decision 055 recording packet itself. It carries **no
separately named `OWNER_DECISION_055_…` instrument token**, and none is invented here — the same
convention Decisions 046 through 054 record. Its operative terms are the eight rulings **055-A**
through **055-H**, reproduced at §§5–12 without reinterpretation, together with the accepted
validation facts at §4.

Where this record summarizes for navigation, the owner's own terms control.

## 3. Authority verification

The controlling authority was re-read in full before this record was written, at these exact
identities, verified live at the recording baseline `542f8cf3a6d7075c6aef823891950b948eee9a3d`
(`HEAD == origin/main`, clean index and worktree, ahead/behind `0/0`, no tag at `HEAD`):

| Authority | SHA-256 |
|---|---|
| [Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) | `16d2445676db0c80d4e356bc3db01a2c2e667864e9f03de3a9c1cf500e0ea13e` |
| [Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) | `0de413af2f284f46bf1f213bb1cccc3c871701b88678cc64d8c5b161ebb3cff0` |
| [Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) | `252109ed815dec36d2aec588b5d81a9ac37c71bdc9c72897e69eb6cd462a9d86` |
| [Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) | `1380324b52c8597a605e625683d2780bac72d8459de12081e9e874ee7f110f78` |
| [Decision 054](decision_054_m3_2_interrupted_run_closure_acceptance.md) | `fed6a4abae09b0b1a968d783a9ea48a07fadc977d2c649726df372418141d9f2` |
| [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) | `c557b1090e416f173354de183acccaf85e7ba5a36b7b6184a9353b943ada56a7` |
| [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) | `561b6b6853fd172f3fbe914876d410185e901e7f133aeb9f785f2779e437f675` |
| [`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md) | `ad360538cd7fdab0628cc28088afdd3275eddcd528c228811d11f96fc165f70e` |

**The chain is self-checking, not merely restated.** Six of those recompute exactly to values a prior
accepted record independently fixed: Decision 054 §3 records the Decision 050, 051, 052, and 053
hashes `16d2445676…`, `0de413af2f…`, `252109ed81…`, and `1380324b52…`, the contract hash
`c557b1090e…` (independently fixed earlier by Decision 051 §14), and the limitations-register hash
`561b6b6853…`. All match, confirming that the register and the contract are still byte-unchanged and
that no accepted record drifted between Decision 054's publication and this one.

Tracked network configuration was verified in [`configs/project.yaml`](../../configs/project.yaml):
`network.enabled: false`, `network.m3_acquire_enabled: false`, and CompanyFacts `enabled: false`.

The repository source cited at §§5–7 was read **read-only** to verify that each citation names a real
surface: `src/disclosure_drift/cli.py`, `src/disclosure_drift/m3/acquisition.py`,
`src/disclosure_drift/m3/recovery.py`, `src/disclosure_drift/m3/receipt.py`,
`src/disclosure_drift/sec/request_ceiling.py`, and the `ops_checkpoints` table created by migration
`0001_initial.sql`. **No operational catalog, private evidence artifact, raw object, lineage record,
lease, receipt store, or operational checkpoint was opened by this recording — not even read-only.**

## 4. The accepted validation facts

The completed read-only validation issued under Decision 054 §15's next authorized action
independently established all four facts exactly, and they are accepted here:

1. Accepted historical **physical-attempt consumption is 1 of cumulative ceiling 801**.
2. That attempt is attributable to route **`sec_bulk_submissions`**.
3. Historical **`ops_retrieval_attempts` rows equal 0**.
4. Recovery remains **`UNDETERMINED`**, **never `SAFE`** — because of the **raw-store/catalog orphan
   mismatch**, rather than because the attempt evidence is ambiguous.

Consequent accepted accounting:

```text
HISTORICAL_SEED_H:                     1
CUMULATIVE_CEILING:                    801
REMAINING_TOTAL_HEADROOM:              800
REMAINING_BULK_ROUTE_HEADROOM:         5 — ACCOUNTING AND REPORTING ONLY, NOT A RUNTIME REFUSAL
OLD_RUN:                               STOPPED — PERMANENTLY NON-RESUMABLE
TERMINATING_RECEIPT:                   NONE EXISTS
```

The validation **changed nothing**, performed **no network or SEC action**, and left the repository at
the required baseline.

The fourth fact is load-bearing for §9: the blocking condition is an **orphan mismatch**, not an
attempt-count ambiguity, so no amount of carry-in accounting resolves it. That is why the orphan must
be adopted under a separate instrument **before** any clean carry-in run.

## 5. Ruling 055-A — ceiling and plan

- The **cumulative M3.2A ceiling remains exactly 801**.
- **Historical seed `H` equals 1**; future cumulative consumption is `H` plus new durable
  reservations.
- **No `802` ceiling, additive ceiling, shadow ceiling, reset, or reinterpretation is permitted.**
- The **frozen request plan and its hash remain unchanged** (SHA-256
  `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; contract §5).
- **The full 75-logical-request plan remains.** It is not trimmed, re-derived, re-planned, or
  substituted to fit the reduced headroom.
- The global `PhysicalAttemptCeiling` (`src/disclosure_drift/sec/request_ceiling.py`) is constructed
  with **`approved_ceiling` 801 and `consumed` 1** for the authorized clean carry-in root.
- The global ceiling **may lawfully stop the run at cumulative 801 with planned work remaining**.
  There is **no pre-run fit gate** and **no false promise that all worst-case retries still fit**. A
  stop at the ceiling remains `stopped_at_ceiling` under contract §9 and a Gate H failure; it is not
  redefined here.
- **Route attribution to `sec_bulk_submissions` is evidence and reporting only.** There is **no
  per-route runtime refusal** and **no change to `src/disclosure_drift/sec/http_client.py`**. The
  remaining bulk-route headroom of **5** is an accounting figure, never a second enforcement gate.

## 6. Ruling 055-B — one-use carry-in authority

**Add exactly one explicit clean-root carry-in interface. It is never resume**, and it **must refuse
coexistence with `--resume-from`.**

### 6.1 The authority artifact

- The authority artifact has **canonical JSON bytes** under schema **`m3-carry-in-authority/1.0`**.
- **Required semantic bindings**, all of them:
  - window **`M3.2A`**;
  - the **frozen request-plan SHA-256**;
  - the **cumulative ceiling 801**;
  - the **historical seed 1**;
  - the **route allocation of that one attempt to `sec_bulk_submissions`**;
  - the **Decision 055 identity**;
  - the **authorized new run id**;
  - the **later accepted orphan-adoption decision identity and evidence identity** (§9).
- It contains **no secret, no identity header, no response body, and no private absolute path**.
- The **SHA-256 of the exact canonical artifact bytes is its external identity**. **Do not create a
  circular self-hash field** inside the artifact.

### 6.2 How it is supplied and validated

- The CLI takes the artifact **from the governed evidence root by a safe relative path** — the same
  escape-refusing discipline the existing artifact resolution already applies.
- The **authorized new run id comes from the artifact** and **replaces random generation** for that
  invocation.
- **Parse, canonicalize, hash, and validate the artifact before transport construction.**

### 6.3 How it is consumed, exactly once

- Consume it **exactly once** by inserting a **deterministic `ops_checkpoints` primary key keyed by
  its SHA-256**, in the **same existing `BEGIN IMMEDIATE` transaction as new-run registration**
  (`register_acquisition_run` in `src/disclosure_drift/m3/acquisition.py`). **No migration** — the
  `ops_checkpoints` table created by migration `0001_initial.sql` already provides
  `checkpoint_key TEXT PRIMARY KEY`, `checkpoint_value TEXT NOT NULL`, and `updated_at_utc TEXT NOT
  NULL`, so the primary key itself enforces single use.
- The **checkpoint value must preserve enough canonical safe data for later receipt and catalog
  cross-checks** (§7.5). It carries no secret, no identity value, no response body, and no private
  absolute path.

### 6.4 Refusals — all before transport

Each of the following **refuses before transport construction**:

- **replay** — the deterministic checkpoint key already exists;
- **run-id mismatch**;
- **plan, window, ceiling, seed, or route mismatch**;
- **malformed or noncanonical bytes**;
- a **conflicting resume** — the carry-in interface and `--resume-from` may never coexist;
- any **missing required binding**.

### 6.5 Atomicity, and the burn-before-wire rule

- The registration transaction is **all-or-nothing**: the checkpoint insertion and the run
  registration commit together or not at all.
- **If a later pre-wire failure occurs after that commit, the authority remains burned even with zero
  attempts.** **No automatic reissue and no automatic retry is authorized.** A replacement authority
  is a new owner act, never an automatic recovery.

## 7. Ruling 055-C — receipt schema 3.0 and recovery arithmetic

### 7.1 A bounded unfreeze

The receipt schema is **unfrozen only for this bounded change**. The new **writer** schema is
**`m3-execution-receipt/3.0`**.

Existing **`m3-execution-receipt/2.0`** receipts remain **byte-unchanged, valid, readable, and usable
in mixed-version chains**. Implement **version dispatch**; **never rewrite an old receipt**.

### 7.2 `consumed_request_count_carried_forward`, restated for 3.0

In `3.0`, `consumed_request_count_carried_forward` means **cumulative physical attempts before the
current invocation**. It is:

- **required** for a **resume**;
- **required** for a **clean carry-in root**;
- **omitted** for an **ordinary zero-baseline fresh root**.

### 7.3 `carry_in_authority_sha256`

Add `carry_in_authority_sha256`. It is:

- **required only** on a **clean carry-in root** — one with **no predecessor** and a **nonzero
  carried-forward count**;
- **absent** on ordinary roots and on resume receipts;
- **retained by the root for the chain**.

### 7.4 The clean carry-in root receipt

A clean carry-in root:

- **omits** `recovery_predecessor_receipt_id`;
- **carries 1** in `consumed_request_count_carried_forward`;
- **names the authority hash** in `carry_in_authority_sha256`;
- records `actual_physical_attempt_count` as **current-invocation wire attempts `N` only**.

Receipt accounting validates that **carried-forward plus actual is no greater than the approved
ceiling**.

### 7.5 The chain walker, and the consumers that must agree with it

The receipt-chain walker **adds the root carry-in exactly once**:

```text
cumulative = sum(actual_physical_attempt_count over every receipt in the chain)
           + carried_forward of the single no-predecessor root only
```

**Never `N` alone, and never double-counted.** `m3 acquire --show-scope` and every
recovery/continuation consumer **must agree with that walker**.

The **catalog checkpoint and the root receipt mutually cross-check**. A **missing or mismatched
authority or carry-in becomes `UNDETERMINED`** and **cannot authorize continuation**.

## 8. Ruling 055-D — M3-L14 fail-closed correction

**M3-L14 is pre-resolved architecturally** by a **global one-to-one reservation-consumption rule
across all owned receiptless lineage segments**.

- A **durable reservation may satisfy at most one segment**.
- **`UNDETERMINED`** is returned on any of: unmatched cardinality; multiply matchable cardinality;
  duplicate reservation reuse; source, URL, or run mismatch; a leftover contradiction; or **any
  inability to establish an exact bijection**.
- The existing counterexample — **one reservation plus two owned same-URL segments** — **must produce
  `UNDETERMINED`**, **never consumed count 1 with `UNSAFE`**.
- **Receiptless inspection remains inspection-only.** It can **never return `SAFE`** and can **never
  authorize continuation** (Decision 051 §8, preserved).

This ruling selects between the two corrections M3-L14's "Required owner action" left open; it
**does not close the entry**. **M3-L14 remains `ACTIVE`** until implementation, non-vacuous tests,
full validation, a fresh independent review, and **separate owner closure**.

## 9. Ruling 055-E — historical orphan Path B

**Path B is chosen:** a **separately authorized, offline, one-time, verified orphan adoption** must
occur **before any clean carry-in run**.

- **Decision 055 does not authorize, design in executable detail, or perform that adoption.**
- **No adoption, quarantine, reconciliation, catalog/raw/lineage mutation, or operational checkpoint
  is authorized now.**
- A **later owner instrument** must define the exact procedure, execute it **once, offline**,
  **independently verify** it, **record acceptance**, and leave **zero unresolved historical orphan
  mismatch** before a carry-in artifact may be **minted or consumed**.
- The **carry-in authority must bind that later adoption decision identity and evidence identity**
  (§6.1).
- **Until then, a clean run, transport construction, network, SEC contact, and live readiness remain
  prohibited.**

## 10. Ruling 055-F — implementation authorization

**One bounded OFFLINE implementation candidate** is authorized, on **at most these sixteen paths**,
with **no seventeenth path**:

**Production (4):**

1. `src/disclosure_drift/cli.py`
2. `src/disclosure_drift/m3/acquisition.py`
3. `src/disclosure_drift/m3/recovery.py`
4. `src/disclosure_drift/m3/receipt.py`

**Normative and operator documentation (6):**

5. [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md)
6. [`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md)
7. [`Docs/m3/templates/gate_h_checklist.md`](../m3/templates/gate_h_checklist.md)
8. [`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md)
9. [`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md)
10. [`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md)

**Tests (6):**

11. `tests/unit/test_m3_acquisition.py`
12. `tests/unit/test_m3_recovery.py`
13. `tests/unit/test_m3_recover.py`
14. `tests/unit/test_m3_receipt.py`
15. `tests/unit/test_request_ceiling.py`
16. `tests/integration/test_m3_cli.py`

The later implementation session may create **exactly one local candidate commit** with the exact
subject:

```text
Implement M3.2 carry-in authority and receipt v3
```

It **may not push and may not tag**.

**Each of the following requires a later separate owner act:** candidate acceptance, **M3-L14**
closure, **M3-L16** closure, orphan adoption, network enablement, live invocation, **T6**, **M3.2B**,
and **Gate H**.

## 11. Ruling 055-G — validation and review gates

### 11.1 Targeted tests and non-vacuous positive controls

The implementation must include targeted tests and **non-vacuous positive controls** for:

1. **baseline 1 plus `N` reservations equals cumulative `1 + N`**;
2. **current-run attempt 800 reaches cumulative 801**; the **next physical attempt is refused without
   increment**;
3. a **sixth future bulk attempt is not refused by a new per-route guard** — the **global ceiling
   remains the sole runtime enforcement**;
4. **artifact replay and all mismatches refuse before transport-factory invocation**;
5. **atomic rollback** between checkpoint insertion and run registration leaves **neither row**;
6. **burn-before-wire remains consumed and is never auto-reissued**;
7. **`2.0` receipts remain valid and readable**; **`3.0` field conditions are exact**;
8. **the root carry-in is counted once through mixed-version chains**, and **`--show-scope` agrees**;
9. a **checkpoint/receipt mismatch becomes `UNDETERMINED`**;
10. the **M3-L14 one-reservation/two-segment counterexample becomes `UNDETERMINED`** — and **that
    test must fail against current behaviour**;
11. **prohibited-path nonchange**;
12. **network containment**.

### 11.2 Validation sequence

Run **targeted validation while editing**, and the **full authorized gate once at stage end**, in
order: `ruff check .`; `ruff format --check .`; `mypy src`; the **full `pytest` suite including the
SEC transport test** (`tests/unit/test_httpx_transport.py` running, not skipped); `make sqlite-check`;
`make secrets`; `make hygiene`; `make context`.

### 11.3 Independent review

After the **frozen candidate**, a **fresh Claude Opus 5 Max non-author session** must **independently
review it without modifying the candidate**.

**Decision 055 itself accepts no candidate and closes no limitation.**

## 12. Ruling 055-H — narrow supersession and continuing authority

Decision 055 **narrowly supersedes only** these four things:

1. **Contract §12**, where it recognizes **only** predecessor-receipt carry-forward — adding the
   **one-use non-resume carry-in root**.
2. **Prior clauses freezing `m3/receipt.py` and receipt schema `2.0`** — **solely** for the
   backward-compatible schema **`3.0`** and version dispatch (§7).
3. **The prior withholding of implementation** — **solely** for the sixteen-path offline candidate at
   §10.
4. **M3-L14's unresolved owner choice** — selecting the **fail-closed one-to-one cardinality rule**
   (§8).

**All other accepted authority remains binding**, including: **ceiling 801**; the **old run's
permanent no-resume** status; **no automatic continuation**; **fail-closed recovery**; **evidence
preservation**; **deterministic behaviour**; and **owner-gated live operations**.

Nothing in this record widens Decision 051's narrow supersession of Decision 032 F3 and Decision 040
§7. Decision 050 §8's predecessor-receipt requirement remains fully binding **for every resume** — the
carry-in root at §6 is **not** a resume and does not touch that requirement.

## 13. Limitations disposition

```text
M3_L14:  ACTIVE — ARCHITECTURE SELECTED (FAIL-CLOSED ONE-TO-ONE), IMPLEMENTATION AUTHORIZED, NOT CLOSED
M3_L15:  ACTIVE — UNTOUCHED AND BYTE-UNCHANGED
M3_L16:  ACTIVE — ARCHITECTURE SELECTED, IMPLEMENTATION AUTHORIZED, NOT CLOSED;
         STILL BLOCKS EVERY CLEAN-RUN AND LIVE AUTHORIZATION
```

**M3-L14** and **M3-L16** remain **`ACTIVE`**, now carrying the selected architecture and the
implementation authority recorded above. **They are not closed.** Closing either requires the
implementation, its tests, full validation, a fresh independent review, and a **separate owner
closure act** — and, for **M3-L16**, additionally the completed and accepted orphan adoption of §9.

**M3-L15** is not addressed by this record and is preserved **byte-for-byte**.

## 14. Path and publication boundary

Exactly **four** repository paths are authorized for **this recording**, with **no fifth**:

1. `Docs/Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md`
   (this record)
2. [`Docs/Decisions/decision_registry.md`](decision_registry.md)
3. [`Milestones/STATUS.md`](../../Milestones/STATUS.md)
4. [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) — **only** the **M3-L14** and
   **M3-L16** status/authority text; **M3-L15 is preserved byte-for-byte**

[`Docs/decision_index.md`](../decision_index.md) is **not** edited: the current project convention for
Decisions 050–054 records position through the registry and the status ledger.

Expressly **not** edited by this recording: any accepted decision 001–054; the accepted contract; the
receipt specification; the operator runbook; every template, including the Gate H checklist, the
interrupted-run recovery template, and the evidence index; the SEC data dictionary; every durable
review artifact; every production source; every test; every configuration; every migration; every
reason code; the master plan; the `Makefile`; `pyproject.toml`; and every script. **The ten §10
documentation and production paths are authorized for the LATER implementation session only, and are
byte-unchanged by this record.** **No private evidence was read or altered, and no operational state
was opened.**

One governance-only commit containing exactly those four paths, with exact subject:

```text
Authorize M3.2 carry-in implementation
```

followed by **one normal fast-forward push** to `origin/main`. No force, no `--force-with-lease`, no
fetch, no pull, no `ls-remote`, no rebase, no squash, no amend, no cherry-pick, no branch, no
worktree, no stash, and **no history rewrite**. **NO TAG** — **M3.2 is not complete.**

## 15. Recorded status

```text
M3_2_CARRY_IN_ARCHITECTURE:               ACCEPTED — BINDING
OFFLINE_IMPLEMENTATION:                   AUTHORIZED — SIXTEEN PATHS, NO SEVENTEENTH
IMPLEMENTATION_PERFORMED_BY_THIS_RECORD:  NO — GOVERNANCE RECORDING ONLY
CANDIDATE_COMMIT_SUBJECT:                 Implement M3.2 carry-in authority and receipt v3
CANDIDATE_PUSH:                           NOT_AUTHORIZED
CANDIDATE_TAG:                            NOT_AUTHORIZED
CANDIDATE_ACCEPTANCE:                     REQUIRES A LATER SEPARATE OWNER ACT
CUMULATIVE_CEILING:                       801 — UNCHANGED, NEVER 802, NEVER RESET OR SHADOWED
HISTORICAL_SEED_H:                        1
REMAINING_TOTAL_HEADROOM:                 800
BULK_ROUTE_HEADROOM:                      5 — ACCOUNTING AND REPORTING ONLY
PER_ROUTE_RUNTIME_REFUSAL:                NONE — GLOBAL CEILING IS SOLE RUNTIME ENFORCEMENT
HTTP_CLIENT_CHANGE:                       NONE AUTHORIZED
REQUEST_PLAN:                             FROZEN — 19be7bdc…, 75 LOGICAL REQUESTS, UNCHANGED
PRE_RUN_FIT_GATE:                         NONE — CEILING MAY LAWFULLY STOP AT 801
CARRY_IN_AUTHORITY_SCHEMA:                m3-carry-in-authority/1.0
CARRY_IN_IS_RESUME:                       NEVER — REFUSES COEXISTENCE WITH --resume-from
CARRY_IN_CONSUMPTION:                     EXACTLY ONCE VIA DETERMINISTIC ops_checkpoints PRIMARY KEY
MIGRATION:                                NONE — 0001-0013 UNCHANGED
BURN_BEFORE_WIRE:                         AUTHORITY STAYS CONSUMED — NO AUTOMATIC REISSUE OR RETRY
RECEIPT_WRITER_SCHEMA:                    m3-execution-receipt/3.0
RECEIPT_v2_RECEIPTS:                      BYTE-UNCHANGED, VALID, READABLE, MIXED-CHAIN USABLE
ROOT_CARRY_IN_COUNTING:                   EXACTLY ONCE — NEVER N ALONE, NEVER DOUBLE-COUNTED
CHECKPOINT_RECEIPT_MISMATCH:              UNDETERMINED — CANNOT AUTHORIZE CONTINUATION
M3_L14_RULE:                              FAIL-CLOSED GLOBAL ONE-TO-ONE RESERVATION CONSUMPTION
M3_L14_COUNTEREXAMPLE:                    1 RESERVATION + 2 OWNED SEGMENTS => UNDETERMINED
RECEIPTLESS_INSPECTION:                   INSPECTION ONLY — NEVER SAFE, NEVER CONTINUATION
HISTORICAL_ORPHAN:                        PATH B — SEPARATE OFFLINE ONE-TIME VERIFIED ADOPTION
ORPHAN_ADOPTION_AUTHORIZED_NOW:           NO — NOT AUTHORIZED, NOT DESIGNED, NOT PERFORMED
OPERATIONAL_STATE_MUTATION:               NONE — NOT AUTHORIZED
OLD_RUN_STATE:                            stopped — PERMANENTLY NON-RESUMABLE
OLD_RUN_CLASSIFICATION:                   UNDETERMINED — ORPHAN MISMATCH, NOT ATTEMPT AMBIGUITY
TERMINATING_RECEIPT:                      NONE — NOT CREATED, NOT RECONSTRUCTED
HISTORICAL_ATTEMPT_LEDGER_ROWS:           0 — NO BACKFILL
INDEPENDENT_REVIEW:                       REQUIRED AFTER FREEZE — FRESH OPUS 5 MAX NON-AUTHOR SESSION
M3_L14:                                   ACTIVE — NOT CLOSED
M3_L15:                                   ACTIVE — UNTOUCHED, BYTE-UNCHANGED
M3_L16:                                   ACTIVE — BLOCKS EVERY CLEAN-RUN AND LIVE AUTHORIZATION
NETWORK_AUTHORITY:                        NONE — TRACKED false / false
COMPANYFACTS:                             DISABLED AND PROHIBITED
SEC_CONTACT:                              NONE OCCURRED — NONE AUTHORIZED
TRANSPORT_CONSTRUCTION:                   NOT_AUTHORIZED
CLEAN_RUN:                                NOT_AUTHORIZED
LIVE_READINESS:                           NOT_CLAIMED — BLOCKED BY M3-L16 AND BY THE ORPHAN
T6:                                       NOT_AUTHORIZED
M3_2B:                                    NOT_AUTHORIZED
GATE_H:                                   NOT_AUTHORIZED
TAG:                                      NONE
M3_2:                                     NOT_COMPLETE
```

## 16. Formal outcome

```text
M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED
```

**Next authorized action:**
`CLAUDE_M3_2_DECISION_055_OFFLINE_IMPLEMENTATION_PACKET`

That next task is the **bounded OFFLINE implementation** of §§5–8 across the exact sixteen paths at
§10. **It does not self-execute**: no session may begin it, or any part of it, before the owner issues
that exact packet. It grants **no** operational-state authority, **no** orphan-adoption authority,
**no** network or SEC authority, and **no** live authority — and **authorization is not
implementation, implementation is not acceptance, and none of them discharges M3-L14 or M3-L16.**

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
