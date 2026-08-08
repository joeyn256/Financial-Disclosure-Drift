# Decision 054 — M3.2 Interrupted-Run Closure Acceptance

**Date:** 2026-08-08
**Status:** ACCEPTED — OWNER APPROVED 2026-08-08
**Authority classification:** `M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED`
**Type:** Governance-only record accepting the **separately authorized one-time OFFLINE closure
execution** of the historical interrupted initial M3.2A T5 ingestion job, and reconciling the
repository's now-stale pre-execution statement that that job is `running` with the owner-verified
operational truth that it is `stopped`. **Not** a preregistration deviation. It changes no hypothesis,
cohort window, maturity gate, outcome definition, threshold, seed, selection methodology, governed
identity, hash preimage, migration byte, implementation byte, test byte, receipt byte, reason code, or
configuration byte — **no executable byte changes with this record**, and **no operational state
changes with this record**. The operational mutation this record accepts happened earlier, under the
separate execution packet; **this record is the acceptance, not the act**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–053 are byte-unchanged.
The accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md),
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md),
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md), and every durable review artifact
are byte-unchanged by this record. Stage progress is recorded here, in the registry, and in the
ledger — never in the contract.
**Narrowly supersedes:** only the **pre-execution status statements** that the historical job is
`running` and that the closure has not executed, wherever they are carried as *current* state in
[`Milestones/STATUS.md`](../../Milestones/STATUS.md) and in
[Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) §§1, 11 and its
registry row. Those statements were accurate when written and are **historical, not wrong** (§4). No
other clause of Decision 053 is narrowed, and Decision 051's narrow supersession of Decision 032 F3
and Decision 040 §7 is unchanged and is **not** widened here.
**Preserves unchanged:** accepted
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §8's
predecessor-receipt requirement, its no-automatic-resume rule, and ceiling **801**;
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) §8's receiptless-inspection
boundary and §9's permanent old-run no-resume ruling;
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §13's preserved
interrupted-run disposition (except the single `stopped` line §4 reconciles) and §14's negative
authority; Decision 053 §§5–7's procedure architecture and evidence contract as the standard this
execution was measured against; the frozen `m3-execution-receipt/2.0` schema; migrations `0001`–`0013`;
limitations **M3-L14**, **M3-L15**, and **M3-L16**; and every route, host, method, spacing, content,
provenance, leakage, and stop condition not expressly addressed here.
**Related:**
[Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) (the authorizing
record whose §12 next authorized action —
`CLAUDE_M3_2_INTERRUPTED_RUN_CLOSURE_EXECUTION_PACKET` — was issued and executed, and whose one-time
execution authority this record **exhausts**);
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md);
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) (whose §9 required exactly this
separate offline state disposition, now performed);
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md);
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §§12, 16, 17, 24;
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** what this record accepts and what it does not (§1); the owner determination (§2);
authority verification (§3); the resolution of the known apparent conflict (§4); the accepted
execution evidence identities (§5); the accepted preflight and synthetic proof (§6); the accepted real
transaction and its exact effects (§7); the accepted blast radius, lease, and integrity postconditions
(§8); the owner's independent reverification (§9); the recorded reproducibility observation (§10); what
the closure expressly does **not** change (§11); the authority granted and withheld, and the
exhaustion of Decision 053's one-time execution authority (§12); the path and publication boundary
(§13); the recorded status (§14); and the formal outcome and exact next authorized action (§15).

---

## 1. What this record accepts, and what it does not

Seven determinations, which must not be collapsed:

1. **Execution acceptance.** The separately authorized one-time offline closure execution is accepted
   as **PASS** against the complete Decision 053 §§5–7 architecture and evidence contract (§§5–8).
2. **Reverification acceptance.** The owner's own independent reverification of the private evidence
   and of a disposable immutable read-only copy of the catalog is accepted as corroborating that
   result (§9).
3. **State reconciliation.** The repository's intentionally stale `running` / not-executed statements
   are superseded by the owner-verified operational truth **`stopped`** (§4). This is **governance
   recording only** — it mutates nothing.
4. **Truthful disposition, and nothing more.** The closure truthfully disposes of the historical job.
   It does **not** change its recovery classification, reconstruct a receipt, backfill an attempt,
   authorize continuation, or create live readiness (§11).
5. **Authority exhausted.** Decision 053's one-time execution authority is **fully consumed** and
   cannot be re-used (§12). The closure is **complete and irreversible**.
6. **Limitations undisturbed.** **M3-L14**, **M3-L15**, and **M3-L16** remain **`ACTIVE`** and
   byte-unchanged, and **M3-L16 continues to block every clean-run and live authorization** (§11).
7. **What this record is not.** It is **not** new operational-state authority, **not** network or SEC
   authority, **not** resume, retry, replacement, or clean-run authority, **not** T6, M3.2B, or Gate H
   authority, **not** an M3-L16 discharge, and **not** a live-readiness claim.
   **The project is not ready for live operation, and M3.2 is not complete.**

## 2. The owner determination, recorded without alteration

The owner's determination for this record was issued as the Decision 054 recording packet itself. It
carries **no separately named `OWNER_DECISION_054_…` instrument token**, and none is invented here —
the same convention Decisions 046 through 053 record. Its operative terms are:

```text
M3.2 — DECISION 054
INTERRUPTED-RUN CLOSURE ACCEPTANCE

The owner accepts the separately authorized one-time offline closure execution as
PASS. All Decision 053 preflight gates passed; all eleven required synthetic cases
passed; the real transaction committed through the accepted CatalogWriter and one
BEGIN IMMEDIATE transaction; exactly one historical M3.2A ingestion row changed in
exactly three authorized columns from running/NULL/prior-detail to
stopped/new-UTC-instant/fixed-owner-detail; cursor.rowcount was exactly one; all 83
other user tables, every table row count, every governed inventory, raw and lineage
evidence, receipt inventory, attempt ledger, event ledger, and non-target column
remained unchanged; the lease inode remained unchanged and its final state is
released; integrity gates pass; the repository remained byte-identical; and no
network, DNS, SEC, resume, retry, replacement, receipt construction, ledger backfill,
or orphan action occurred.

The owner independently reverified the private evidence manifest, its four entries,
the 11/11 synthetic record, the table-by-table before/after comparison, and a
byte-identical disposable immutable read-only copy of the current catalog. That copy
contains exactly one ingestion job, now stopped, with non-null finish time and the
byte-exact Decision 053 closure detail; zero attempt rows; zero job events; quick and
integrity checks ok; zero foreign-key violations. The original catalog hash was
unchanged by owner verification, and the live lease remains released at the recorded
inode and mode 0600.

The closure is complete and irreversible. It truthfully disposes the historical job
but does not change its recovery classification, reconstruct a receipt, backfill an
attempt, authorize continuation, or create live readiness. M3-L16 remains active and
continues to block every clean-run and live authorization. No new live acquisition,
T6, M3.2B, Gate H, or tag is authorized.
```

Where this record summarizes for navigation, the owner's own terms control.

## 3. Authority verification

The controlling authority was re-read in full before this record was written, at these exact
identities, verified live at the recording baseline `db3b1ca1850dc0d33430c4715e2bff2e195238e0`
(`HEAD == origin/main`, clean, ahead/behind `0/0`):

| Authority | SHA-256 |
|---|---|
| [Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) | `16d2445676db0c80d4e356bc3db01a2c2e667864e9f03de3a9c1cf500e0ea13e` |
| [Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) | `0de413af2f284f46bf1f213bb1cccc3c871701b88678cc64d8c5b161ebb3cff0` |
| [Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) | `252109ed815dec36d2aec588b5d81a9ac37c71bdc9c72897e69eb6cd462a9d86` |
| [Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) | `1380324b52c8597a605e625683d2780bac72d8459de12081e9e874ee7f110f78` |
| [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) | `c557b1090e416f173354de183acccaf85e7ba5a36b7b6184a9353b943ada56a7` |
| [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) | `561b6b6853fd172f3fbe914876d410185e901e7f133aeb9f785f2779e437f675` |

**The chain is self-checking, not merely restated.** Four of those recompute exactly to values a prior
accepted record independently fixed: Decision 053 §3 records the Decision 050, 051, and 052 hashes
`16d2445676…`, `0de413af2f…`, and `252109ed81…`, and the contract hash `c557b1090e…` — which Decision
051 §14 fixed independently. The limitations-register hash `561b6b6853…` likewise recomputes to the
value Decision 053 §3 recorded, confirming that record's **"the register is byte-unchanged"** claim
still holds. All match.

Tracked network configuration was verified **`false` / `false`** in `configs/project.yaml`, and
CompanyFacts remains disabled.

**No operational catalog was opened by this recording — not even read-only.** The owner independently
verified the operational state (§9); this session reverified only the private evidence bundle's
manifest and public-safe facts, and read repository documents and read-only source.

## 4. Ruling 054-A — the known apparent conflict, and its resolution

The repository, as published at Decision 053, states
`HISTORICAL_JOB_STATE_NOW: running` and that the closure has not executed.

**Those statements were accurate at Decision 053 publication and are now intentionally stale.** The
separately owner-authorized execution occurred *after* that publication, and **private operational
state is not self-recording**: nothing in a private SQLite catalog can update a public governance
ledger. The gap between the two is therefore expected residue of the correct sequence — record the
architecture, then execute under a separate packet, then record the acceptance — and **not** a
governance defect, a contradiction between authorities, or evidence that either record is wrong.

```text
PRE_EXECUTION_STATEMENT:   running / closure not executed   (historical — accurate when written)
OWNER_VERIFIED_TRUTH_NOW:  stopped / closure COMPLETE — ACCEPTED
```

This record reconciles the ledger to `stopped`. It **authorizes no further operational action of any
kind**, and no session may read this reconciliation as permission to touch operational state again.
Where an earlier record describes the job as `running`, that description is **preserved as historical**
and is superseded only as a statement of *current* state.

## 5. Ruling 054-B — the accepted execution evidence identities

The private evidence bundle was reverified at this recording. Its manifest verifies, contains exactly
**four** safe relative entries, and all five files are mode **0600**. Public-safe identities only:

| Artifact | SHA-256 | Bytes |
|---|---|---|
| Closure bundle manifest | `9aa1582e9cc6aba646dcbe36f01476d4b731af9d37847e51dd204b82706cbade` | — |
| `closure_evidence.md` | `dd3e25ca00232b4564642b17c242d536e23a977b49bb029afedfb04bafcf6c77` | 5,344 |
| `state_before.json` | `b1404e6d14e76889dd059d00c4a76e63848efd5d903d4829c0851124dca1a498` | 14,635 |
| `state_after.json` | `56df1f0bd117e66d1c324d5a6149300d2b6b59629ad5f1962a37dc16059d2fb2` | 14,108 |
| `synthetic_results.json` | `babddcb8a1b59cbd105a32403f06ae8b52253058f7e569649eda72f19956c214` | 1,988 |

Every hash and every byte count above was **recomputed and matched exactly**, and
`shasum -c` over the manifest returned `OK` for all four covered entries. The private evidence remains
**outside Git**; nothing was copied into the repository, and nothing in the bundle was altered — it was
read and re-hashed only.

## 6. Ruling 054-C — the accepted preflight and synthetic proof

**Preflight (Decision 053 §7.1) — all gates passed.** Migration chain head **`0013`**, contiguous
`0001`–`0013`; `quick_check=ok`, `integrity_check=ok`, `foreign_key_check=0` both before and after;
**exactly one** candidate row satisfying the §6.1 predicates, against **one** total job row
catalog-wide; **zero** `ops_retrieval_attempts` and **zero** `ops_job_events` rows for the target;
no live writer holding the OS lock immediately before the transaction; and the private catalog, lock
directory, and historical job id resolved **without printing or committing** any private absolute path,
identifier, identity value, or raw body.

**Independent target corroboration is accepted.** The target job's start precedes the single accepted
physical SEC attempt by **68.773 s**, and the raw lineage independently records `attempts=1`, HTTP
**200**, **zero** redirect hops, and `stored_new` — the same facts Decision 051 §3 accepted. The target
was therefore identified by converging durable evidence, not by a job id alone.

**Synthetic proof (Decision 053 §7.2) — 11 of 11 required cases PASS**, all against disposable
fixtures, before the real catalog was touched:

| # | Case | Result |
|---|---|---|
| 1 | positive closure — exactly three columns of one row change | **PASS** |
| 2 | unknown job id | **PASS** — refused |
| 3 | wrong `job_kind` | **PASS** — refused |
| 4 | wrong `stage` | **PASS** — refused |
| 5 | already-terminal `job_state` | **PASS** — refused |
| 6 | non-null `finished_at_utc` | **PASS** — refused |
| 7 | non-empty attempt ledger | **PASS** — refused |
| 8 | stale `state="held"` lease metadata | **PASS** — re-acquired normally, **inode unchanged** |
| 9 | live lock contention | **PASS** — refused with the single-writer violation |
| 10 | injected fault inside the transaction | **PASS** — rolled back, no partial effect |
| 11 | table-by-table blast radius | **PASS** — 84 tables, one changed, no row-count change |

**The fixtures carried a decoy row matching predicates 2–5 that was proven untouched.** That is
stronger than the §7.2 minimum: it demonstrates **job-id specificity**, so case 1's success cannot be
explained by a predicate set that would have matched a second row.

**The procedure's shape was proved statically, not merely asserted.** An AST proof recorded **3** SQL
statements total, of which **exactly 1** mutates, and **zero** references to
`prepare_operational_catalog`, `migrate`, `seed_reference_data`, `finish_acquisition_run`, any
live-acquisition entry point, any transport constructor, or any recovery mutation surface — exactly the
Decision 053 §5 prohibition list. A `sys` audit hook additionally **hard-blocked**
`socket.connect`/`getaddrinfo`/`bind`/`sendto` for the duration of the real run, so the offline
guarantee was enforced mechanically rather than by operator discipline.

## 7. Ruling 054-D — the accepted real transaction and its exact effects

The real transaction committed through the accepted `CatalogWriter` and its `batch()`
**one `BEGIN IMMEDIATE`** writer transaction — the normal OS-lock and writer lifecycle Decision 051 §9
requires — importing only `CatalogWriter` and `utc_now`. Exactly **one** conditional `UPDATE` ran, with
the row-state predicates restated in its own `WHERE` clause, and **`cursor.rowcount` was exactly 1**.

On exactly one historical M3.2A ingestion row, and nowhere else:

| Column | Before | After |
|---|---|---|
| `job_state` | `running` | **`stopped`** |
| `finished_at_utc` | `NULL` | one new UTC instant |
| `detail` | prior text, SHA-256 `2065fb487c5b47c4820313e3cd9cb5c2faf5be36889c455394b495008df563ea` | SHA-256 `e787286044080627d2267b96400321428e5539593866234a41fc60bda5724476` |

The new `detail` is **byte-exact to Decision 053 §6.4**, at **222 bytes**. The target job id was
**never recorded in plaintext** anywhere in the evidence — only as a SHA-256 — and is not recorded here.
The row's `job_id`, `job_kind`, `stage`, and `started_at_utc` are **unchanged**.

```text
CHANGED_ROWS:      1
CHANGED_COLUMNS:   3   (job_state, finished_at_utc, detail)
CURSOR_ROWCOUNT:   1
```

**No state, column, index, table, trigger, or migration was added**, and `stopped` is a literal
migration `0001`'s existing `CHECK` constraint already admitted.

## 8. Ruling 054-E — the accepted blast radius, lease, and integrity postconditions

Every Decision 053 §7.3 postcondition is satisfied.

**Blast radius.** User tables compared: **84**. Changed: **exactly 1** — `ops_ingestion_jobs`.
Unchanged: **83**. **Row-count changes across every table: none.** `ops_retrieval_attempts` 0 → 0;
`ops_job_events` 0 → 0; `raw_objects` 0 → 0; `raw_object_observations` 0 → 0.

**Governed inventories byte-identical**, digest-compared: `raw` (**2** files,
**1,556,243,994** bytes — unchanged), `runs` (18 files), `backups` (1 file), and `staging`,
`releases`, `audit`, and `locks` all empty.

**Catalog file identity.** SHA-256
`c4f2215866c953384c3e573211afe8a35c43080552e4cc58cfb96d7261e3e421` →
`31b65e7132e65ae483afb294730f2ed2439ca3c8a2f53ee2e8fb50200034cb5b`, **size unchanged at 1,245,184
bytes**. The changed hash on an unchanged size is exactly what a three-column in-place update produces;
it is evidence of the accepted effect, not of unexpected churn.

**Lease.** Present, **inode unchanged** at the privately recorded value, mode **0600**, `state`
`held` → **`released`** through the ordinary `CatalogWriter` acquire/release cycle. **No deletion,
clearing, `unlink`, replacement, manual edit, or expiry takeover occurred** — the Decision 053 §4.2
and §6.5 boundary held exactly. WAL/SHM was checkpointed away on clean close, which §6.5 permits as
ordinary churn. The inode value is private operational detail and is **deliberately not published
here**; it is recorded in the private evidence.

**Integrity and negative postconditions.** Quick, integrity, and foreign-key gates pass. **No receipt
was created or reconstructed; no attempt row was inserted; no consumed-count mutation, orphan
adoption, quarantine, or reconciliation occurred; no raw or lineage byte changed.** The repository
remained **clean and byte-identical** throughout, tracked network stayed **`false` / `false`**, and
**no SEC, network, or DNS action occurred**.

## 9. Ruling 054-F — the owner's independent reverification is accepted

The owner did not rely solely on the executing session's own report. The owner independently
reverified the private evidence manifest and its four entries, the 11/11 synthetic record, and the
table-by-table before/after comparison, and then inspected a **byte-identical disposable immutable
read-only copy** of the current catalog.

That copy contains **exactly one** ingestion job, now **`stopped`**, with a **non-null** finish time
and the **byte-exact** Decision 053 §6.4 closure detail; **zero** attempt rows; **zero** job events;
`quick_check` and `integrity_check` **ok**; and **zero** foreign-key violations. **The original
catalog's hash was unchanged by the owner's verification** — the inspection was genuinely read-only —
and the live lease remains **`released`** at the recorded inode and mode **0600**.

This is accepted as **independent corroboration** of §§7–8 by a second party working from a separate
copy. It is not a second closure, and it changed nothing.

## 10. Ruling 054-G — the recorded reproducibility observation

The four ephemeral procedure artifacts are identified by SHA-256 in the private evidence, together
with a sanitized protocol description. **Their source was correctly destroyed with the `mktemp -d`
scratch directory** under the execution packet.

**This is an OBSERVATION, not a defect.** Decision 053 §7.1 item 6 required the procedure to be built
in a disposable scratch directory outside the repository and its **hash** recorded; it required the
hashes and a sanitized protocol, **not** source preservation. Decision 053 §5 additionally declined a
permanent surface *by design*, so no durable operator artifact was ever intended to survive.

Recorded plainly so a later reader does not overclaim: **the recorded hashes attest that a specific
byte sequence ran; they do not permit re-deriving that byte sequence.** No session may cite them as
reproducibility evidence, and **no repository record may invent reproducibility that does not exist.**
Consistent with repository convention for a nonblocking observation recorded inside a decision, this
ruling **creates no limitations-register entry**, and the register is byte-unchanged by this record.

**No BLOCKER, MAJOR, or MINOR finding remains** from the closure execution or its acceptance.

## 11. Ruling 054-H — what the closure does NOT change

The closure **truthfully disposes** of the historical job. It does **nothing else**. Every preserved
fact carries forward unchanged from Decision 051 §§3, 5, 9, Decision 052 §§6, 13, and Decision 053 §4.6:

```text
HISTORICAL_JOB_STATE_NOW:              stopped
RECOVERY_CLASSIFICATION:               UNDETERMINED   (unchanged by the closure)
TERMINATING_RECEIPT:                   NONE           (none created; none reconstructed)
HISTORICAL_ATTEMPT_LEDGER_ROWS:        0              (no backfill)
ACCEPTED_PHYSICAL_ATTEMPTS_CONSUMED:   1_OF_801
REMAINING_TOTAL_HEADROOM:              800
BULK_ROUTE_ACCOUNTING_HEADROOM:        5
OLD_RUN_RESUMABLE:                     NEVER
```

**A truthful terminal state is not a resolution.** The job is now honestly recorded as `stopped`, but
that says only *that it ended* — not *what it accomplished*. Recovery therefore remains
**`UNDETERMINED`**, and the old run is **permanently non-resumable**. No session may read `stopped` as
`completed`, as a resolved orphan, as a discharged recovery condition, or as continuation eligibility.

The bulk-route headroom of **5** remains **accounting**, not a claim of runtime enforcement
(Decision 053 §8, finding **F-5**).

**M3-L14**, **M3-L15**, and **M3-L16** remain **`ACTIVE`** and byte-unchanged. **M3-L16 continues to
block every clean-run and live authorization**; nothing here discharges, designs, or implements a
consumed-baseline carry-in mechanism. Decision 053 §9.3's requirement stands: a future T5 instrument
**must explicitly supersede** Decision 050 §9's now-impossible preflight assumptions — consumed count
**0**, the operational catalog **absent**, and **no prior M3.2 live run**, receipt, or raw object.
**Decision 054 does not do so**, and no session may treat this paragraph as having done so.

**M3.2 is not complete, and the project is not ready for live operation.**

## 12. Ruling 054-I — authority granted and withheld

### 12.1 Granted

Decision 054 grants exactly two things:

1. the **acceptance** of the completed closure execution as `PASS`;
2. the **governance reconciliation** of the ledger to `stopped` (§4).

**Both are records. Neither is an operational act.**

### 12.2 Decision 053's execution authority is exhausted

```text
DECISION_053_EXECUTION_AUTHORITY:   EXHAUSTED
CLOSURE_EXECUTION:                  COMPLETE — ACCEPTED
CLOSURE_REVERSIBILITY:              IRREVERSIBLE
REPEAT_CLOSURE:                     NOT_AUTHORIZED
```

The one-time authority Decision 053 §9.1 opened is **fully consumed** by the accepted execution. It
cannot be re-used, re-read as standing authority, or extended to a second row, a second job, or any
other disposition. Any further operational act requires a **new** explicit owner packet.

### 12.3 Withheld

Decision 054 authorizes none of:

- any further operational-state mutation, on this row or any other; any second or repeat closure;
- resume, retry, replacement, `--resume-from`, receipt creation or reconstruction, attempt backfill,
  consumed-count mutation, raw or lineage mutation, orphan adoption or quarantine, reconciliation, or
  lease deletion, clearing, or manual takeover;
- any production, test, configuration, schema, migration, receipt, reason-code, runbook, template,
  review-artifact, or limitations-register change;
- live acquisition, a clean new run, T6, M3.2B, dependent-plan derivation, Gate H, M3.3+, publication
  of research output, or any live-readiness claim;
- tracked or private network enablement; DNS, connectivity tests, `curl`, `wget`, `ping`, an SEC
  request, or any remote contact;
- a commit tag, force push, rebase, amend, cherry-pick, or history rewrite.

Tracked network configuration remains **`false` / `false`**. CompanyFacts and Frames remain disabled
and prohibited. The approved ceiling **801** is never increased, reset, shadowed, or reinterpreted.

## 13. Path and publication boundary

Exactly **three** repository paths are authorized for this recording, with **no fourth**:

1. `Docs/Decisions/decision_054_m3_2_interrupted_run_closure_acceptance.md` (this record)
2. [`Docs/Decisions/decision_registry.md`](decision_registry.md)
3. [`Milestones/STATUS.md`](../../Milestones/STATUS.md)

Expressly **not** edited: any accepted decision 001–053; the accepted contract; the interrupted-run
recovery template; the SEC data dictionary; the limitations register; `Docs/decision_index.md`;
`Docs/m3/templates/evidence_index.md`; every durable review artifact; every production source; every
test; every configuration; every migration; the receipt schema; the operator runbook; the master plan;
the `Makefile`; `pyproject.toml`; every script; and every other `Docs/` and `Milestones/` path. **No
private evidence was altered.**

One governance-only commit containing exactly those three paths, with exact subject:

```text
Accept M3.2 interrupted-run closure
```

followed by **one normal fast-forward push** to `origin/main`. No force, no `--force-with-lease`, no
rebase, no squash, no amend, no cherry-pick, no replacement branch, and **no history rewrite**.
**NO TAG** — **M3.2 is not complete.**

## 14. Recorded status

```text
M3_2_INTERRUPTED_RUN_CLOSURE:             ACCEPTED
CLOSURE_EXECUTION:                        COMPLETE — ACCEPTED
CLOSURE_REVERSIBILITY:                    IRREVERSIBLE
DECISION_053_EXECUTION_AUTHORITY:         EXHAUSTED
HISTORICAL_JOB_STATE_NOW:                 stopped
PRE_EXECUTION_running_STATEMENTS:         HISTORICAL — SUPERSEDED AS CURRENT STATE
OLD_RUN_CLASSIFICATION:                   UNDETERMINED
OLD_RUN_RESUME:                           NEVER
TERMINATING_RECEIPT:                      NONE — NOT CREATED, NOT RECONSTRUCTED
HISTORICAL_ATTEMPT_LEDGER_ROWS:           0 — NO BACKFILL
ACCEPTED_CONSUMED_PHYSICAL_ATTEMPTS:      1_OF_801
REMAINING_TOTAL_HEADROOM:                 800
BULK_ROUTE_ACCOUNTING_HEADROOM:           5
CHANGED_TABLES:                           1 OF 84 — ops_ingestion_jobs
ROW_COUNT_CHANGES:                        NONE
SYNTHETIC_CASES:                          11 OF 11 PASS
LEASE_FINAL_STATE:                        released — INODE UNCHANGED, MODE 0600
REPOSITORY_DURING_EXECUTION:              CLEAN AND BYTE-IDENTICAL
OUTSTANDING_FINDINGS:                     NONE — BLOCKER 0, MAJOR 0, MINOR 0
PERMANENT_PRODUCTION_SURFACE:             DECLINED — NONE CREATED
EPHEMERAL_PROCEDURE_SOURCE:               CORRECTLY DESTROYED — OBSERVATION, NOT A DEFECT
FURTHER_OPERATIONAL_MUTATION:             NOT_AUTHORIZED
M3_L14:                                   ACTIVE — UNCHANGED
M3_L15:                                   ACTIVE — UNCHANGED
M3_L16:                                   ACTIVE — BLOCKS EVERY CLEAN/LIVE AUTHORIZATION
NETWORK_AUTHORITY:                        NONE — TRACKED false / false
COMPANYFACTS:                             DISABLED AND PROHIBITED
NEW_LIVE_INVOCATION_AUTHORITY:            NONE
LIVE_READINESS:                           NOT_CLAIMED — BLOCKED BY M3-L16
T6:                                       NOT_AUTHORIZED
M3_2B:                                    NOT_AUTHORIZED
GATE_H:                                   NOT_AUTHORIZED
TAG:                                      NONE
M3_2:                                     NOT_COMPLETE
```

## 15. Formal outcome

```text
M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED
```

**Next authorized action:**
`CLAUDE_M3_2_M3_L16_CARRY_IN_ARCHITECTURE_DISCOVERY_PACKET`

That next task is **read-only architecture discovery** for the **M3-L16** consumed-baseline carry-in
problem. **It does not self-execute**: no session may begin it, or any part of it, before the owner
issues that exact packet. It grants **no** implementation authority, **no** operational-state
authority, **no** network or SEC authority, and **no** live authority — and **discovery is not
design, design is not implementation, and neither discharges M3-L16.**

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
