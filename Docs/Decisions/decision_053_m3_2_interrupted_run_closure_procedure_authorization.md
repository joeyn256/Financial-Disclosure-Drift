# Decision 053 — M3.2 Interrupted-Run Closure Procedure Authorization

**Date:** 2026-08-08
**Status:** ACCEPTED — OWNER AUTHORIZATION RECORDED
**Authority classification:** `M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED`
**Type:** Governance-only record fixing the **one-time architecture and boundaries** of the later
offline closure of the historical interrupted initial M3.2A T5 invocation to job state `stopped`, and
authorizing **only** a separate exact owner execution packet for it. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, governed identity, hash preimage, migration byte, implementation byte,
test byte, receipt byte, reason code, or configuration byte — **no executable byte changes with this
record**, and **no operational state changes with this record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–052 are byte-unchanged.
The accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md),
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md),
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md), and every durable review artifact
are byte-unchanged by this record. Stage progress is recorded here, in the registry, and in the
ledger — never in the contract.
**Narrowly supersedes:** nothing. Decision 051's narrow supersession of Decision 032 F3 and
Decision 040 §7 is unchanged and is **not** widened here.
**Preserves unchanged:** accepted
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §8's
predecessor-receipt requirement, its no-automatic-resume rule, and ceiling **801**;
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) §8's receiptless-inspection
boundary and §9's permanent old-run no-resume ruling;
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §13's preserved
interrupted-run disposition and §14's negative authority; the frozen `m3-execution-receipt/2.0`
schema; migrations `0001`–`0013`; limitations **M3-L14**, **M3-L15**, and **M3-L16**; and every route,
host, method, spacing, content, provenance, leakage, and stop condition not expressly addressed here.
**Related:**
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) (whose §18 next
authorized action — `CHATGPT_OWNER_M3_2_INTERRUPTED_RUN_CLOSURE_PACKET` — this record answers);
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) (whose §9 requires exactly this
separate offline state-disposition authorization);
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md);
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §§12, 16, 17, 24;
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md);
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md) §5A;
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the current-state boundary of this record (§1); the owner determination (§2); authority
verification (§3); the accepted repository observations (§4); the owner architecture ruling and its
rationale (§5); the exact future transaction predicates and intended effects (§6); the synthetic,
preflight, and postcondition evidence contract the later execution packet must impose (§7); the
disposition of closure-discovery findings **F-1**–**F-7** (§8); the authority granted and withheld
(§9); the path and publication boundary (§10); the recorded status (§11); and the formal outcome and
exact next authorized action (§12).

---

## 1. What this record does, and what it does not

Six determinations, which must not be collapsed:

1. **Architecture fixed.** The owner fixes the exact one-time architecture and boundaries for the
   later closure of the historical interrupted M3.2A T5 ingestion job to `stopped` (§§5–6).
2. **Evidence contract fixed.** The owner fixes the preflight, synthetic-rehearsal, and postcondition
   proof obligations the later execution packet must impose (§7).
3. **Execution deferred.** **This record performs no closure.** It opens no catalog — not even
   read-only — reads no private evidence, and mutates no operational state. The later execution
   remains gated on a separate exact owner packet.
4. **No permanent surface.** No production or test implementation is authorized, and none is
   required: the closure runs as one ephemeral, hash-recorded operator procedure outside the
   repository, so no durable operator surface is created and no implementation commit or independent
   code-review cycle for such a surface is required.
5. **State unchanged now.** The historical job remains `running`; recovery remains `UNDETERMINED`;
   accepted consumption remains **1 of 801**; the real catalog, raw object, lineage, receipt
   inventory, and writer lease remain untouched.
6. **What this record is not.** It is **not** network or SEC authority, **not** resume, retry,
   replacement, or clean-run authority, **not** T6, M3.2B, or Gate H authority, **not** an M3-L16
   discharge, and **not** a live-readiness claim. **The project is not ready for live operation.**

## 2. The owner determination, recorded without alteration

The owner's determination for this record was issued as the Decision 053 recording packet itself. It
carries **no separately named `OWNER_DECISION_053_…` instrument token**, and none is invented here —
the same convention Decisions 046 through 052 record. Its operative terms are:

```text
M3.2 — DECISION 053
INTERRUPTED-RUN CLOSURE PROCEDURE

The owner records the accepted repository observations about the writer lease,
the ordinary lock lifecycle, prepare_operational_catalog's blast radius, the
under-constrained finish_acquisition_run, and the absence of any closure-only
public surface; rules that a permanent production CLI/API change is NOT required
for exactly one historical disposition; fixes the later closure as one ephemeral,
hash-recorded, one-time operator procedure outside the repository that uses the
accepted CatalogWriter and its batch() transaction; fixes the exact predicates,
the exact three intended column effects, and the exact fixed closure detail text;
fixes the preflight, synthetic-rehearsal, and postcondition evidence contract; and
authorizes only a later exact execution packet. No private evidence read, no real
catalog open, no real closure, no operational-state mutation, no network or SEC
authority, and no live readiness are granted or claimed by this record.
```

Where this record summarizes for navigation, the owner's own terms control.

## 3. Authority verification

The controlling authority was re-read in full before this record was written, at these exact
identities, verified live at the recording baseline `628087b82bc3cfa356166e6f9cba076f7154ac17`:

| Authority | SHA-256 |
|---|---|
| [Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) | `16d2445676db0c80d4e356bc3db01a2c2e667864e9f03de3a9c1cf500e0ea13e` |
| [Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) | `0de413af2f284f46bf1f213bb1cccc3c871701b88678cc64d8c5b161ebb3cff0` |
| [Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) | `252109ed815dec36d2aec588b5d81a9ac37c71bdc9c72897e69eb6cd462a9d86` |
| [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) | `c557b1090e416f173354de183acccaf85e7ba5a36b7b6184a9353b943ada56a7` |
| [`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md) | `28bcbd1342e492e4ac74ec104be0e746de04c0c7b5a049810817a2f806061151` |
| [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) | `561b6b6853fd172f3fbe914876d410185e901e7f133aeb9f785f2779e437f675` |
| [`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md) | `451a996f67affde9f098426e6dd418c59d50a23eea9de640dc1578eb74c4efe7` |

Two of those recompute exactly to values a prior accepted record independently fixed, so the chain is
self-checking rather than merely restated: Decision 051 §2 records the Decision 050 hash
`16d2445676…`, and Decision 051 §14 records the post-amendment contract hash `c557b1090e…`. Both match.

The read-only source consulted for §4's evidence statements, at the same baseline:

| Module | SHA-256 |
|---|---|
| `src/disclosure_drift/storage/catalog.py` | `a7e05602bc1a2b5d741b40c6004907b9884c9abc1bc347789260e75d79c8b32c` |
| `src/disclosure_drift/storage/sqlite.py` | `4a0d94af41781b82cfee6285d7f0e37b6a27c46f11c9508a95fa548c2f3a61f0` |
| `src/disclosure_drift/m3/acquisition.py` | `a108c18c9e8702a07806c0b933bf5f11adbe2037f4198ca8e1e6c31a9e0e2190` |
| `src/disclosure_drift/cli.py` | `ba29bfa183344f90d6d6c1ba1fe1aee9a2713026319a6a35b57ae87926506294` |
| `src/disclosure_drift/m3/receipt.py` | `cf202ee6cf344178af554f8da82640217339cd033a051ff160fe36da07f4f07e` |

`m3/acquisition.py` recomputes exactly to the file identity Decision 052 §3 accepted
(`a108c18c…`), confirming the reviewed implementation is byte-unchanged at this recording.

**Every module above was read only.** No module was imported, executed, or modified, and no database
was opened.

## 4. Ruling 053-A — the accepted repository observations

These are recorded as **owner-verified repository observations**, each traceable to source at the
identities in §3. They are facts about the accepted implementation, not new architecture.

### 4.1 The writer lease is an OS lock; its persisted JSON is metadata

`CatalogWriter` acquires a **process-lifetime `fcntl.flock`** on the lease file
(`storage/catalog.py:172`–`177`: `os.open(..., O_CREAT | O_RDWR, 0o600)` then
`flock(LOCK_EX | LOCK_NB)`). Process death releases the kernel lock automatically. The persisted JSON
`state="held"` (`storage/catalog.py:169`) is therefore **stale metadata after an abrupt end, not an
active time-based ownership claim**. This matches
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md) §5, which already records
`lease_expires_at_utc` as diagnostic metadata that never authorizes takeover, and
`storage/catalog.py:185`'s own refusal text: *"Elapsed time never permits takeover."*

### 4.2 Ordinary acquisition and release need no manual lease act

Ordinary acquisition **opens the existing lease path**, takes `LOCK_EX | LOCK_NB`, and then
**overwrites the stale payload in place** (`ftruncate(0)` → `lseek(0)` → `write` → `fsync`;
`storage/catalog.py:195`–`198`). Ordinary release rewrites the same payload with `state="released"`
and a `released_at_utc` stamp, then unlocks and closes (`storage/catalog.py:231`–`243`).

**No deletion, clearing, `unlink`, expiry takeover, or manual lease act is needed — or permitted.**
Because the path is opened rather than replaced, the lease file's **inode is unchanged** by an
ordinary acquire/release cycle.

### 4.3 `prepare_operational_catalog` is prohibited for this closure

`prepare_operational_catalog` calls `writer.migrate()` and `writer.seed_reference_data()`
(`m3/acquisition.py:570`–`571`). `seed_reference_data()` performs `INSERT OR REPLACE` over
`reference_form_types`, `reference_reason_codes`, `reference_cohort_definitions`, and
`reference_policy_versions`, writing a **fresh `recorded_at_utc`** on every policy row
(`storage/catalog.py:274`, `325`–`330`).

That is an unnecessary and irreversible rewrite of governed reference rows for an operation whose
entire lawful effect is three columns of one row. **`prepare_operational_catalog` is therefore
prohibited for this closure.**

### 4.4 `finish_acquisition_run` is under-constrained for this disposition

`finish_acquisition_run` validates only that `job_state` is one of the accepted terminal states, then
executes `UPDATE ops_ingestion_jobs SET job_state = ?, finished_at_utc = ?, detail = ? WHERE
job_id = ?` (`m3/acquisition.py:4568`–`4572`).

It **does not** enforce `cursor.rowcount`, the job kind, the prior state, or a null prior finish time.
That is defensible for the in-process live lifecycle it was written for, where the row was registered
moments earlier by the same invocation. It is **not** sufficient for a **one-time irreversible offline
disposition** of a historical row.

### 4.5 No public surface performs only the closure

No current supported public CLI or API performs the closure and nothing else. Exactly two call sites
invoke `finish_acquisition_run`, both inside `execute_live_acquisition`
(`m3/acquisition.py:5364` and `:5378`) and both **after the transport is constructed**
(`m3/acquisition.py:5304`). The `m3` command group exposes `rehearse`, `rehearse-report`,
`plan-requests`, `show-budget`, `show-receipt`, `recovery-state`, `acquire`,
`derive-dependent-plan`, `reconcile-requests`, `show-drift`, and `recover`; none closes a run row.
`m3 recover` applies exactly one recovery action and emits no receipt (`cli.py:3024`–`3079`). Outside
`finish_acquisition_run`, the only other writer of `ops_ingestion_jobs.job_state` in `src/` is the
M2.2 census orchestrator (`sec/census_orchestrator.py:1445`), which is hardcoded to the M2.2 job kind
and stage.

**The existing live call sites must not be used for this closure.**

### 4.6 The historical accepted facts are unchanged

```text
ACCEPTED_PHYSICAL_ATTEMPTS_CONSUMED:  1_OF_801
HISTORICAL_ATTEMPT_LEDGER_ROWS:       0
TERMINATING_RECEIPT:                  NONE
RECOVERY_CLASSIFICATION:              UNDETERMINED
OLD_RUN_RESUMABLE:                    NEVER
EVENTUAL_TRUTHFUL_JOB_STATE:          stopped
```

Exactly **1** of **801** physical attempts is consumed; the real `ops_retrieval_attempts` table holds
**zero** rows for this job; no terminating receipt exists and none is reconstructed; recovery remains
`UNDETERMINED`; the old run is **permanently non-resumable**; and its eventual truthful job state is
`stopped`. These carry forward unchanged from Decision 051 §§3, 5, 9 and Decision 052 §§6, 13.

## 5. Ruling 053-B — the owner architecture ruling

**A permanent production CLI/API or source-code change is NOT required for exactly one historical
disposition, and would add unnecessary durable operator surface.** A committed "close a run row"
command would outlive its single use and would have to be defended, tested, and guarded forever
against exactly the misuse §4.4 describes. The owner declines to create it.

The later execution will instead use **one ephemeral, hash-recorded, one-time operator procedure
outside the repository**, bound by all of the following:

**It must:**

- import and use the accepted `CatalogWriter` and its `batch()` transaction, thereby using the
  **normal OS-lock and writer lifecycle** — which is precisely what Decision 051 §9 requires of this
  operation;
- select and update **inside one `BEGIN IMMEDIATE` writer transaction** (`storage/sqlite.py:100`, the
  transaction `batch()` opens);
- **fail closed** unless exactly one private target row satisfies every §6.1 predicate.

**It must not** call `prepare_operational_catalog`, `migrate()`, `seed_reference_data()`,
`finish_acquisition_run`, any live-acquisition entry point, or any transport constructor.

**Why this is the correct shape.** Opening the catalog through `CatalogWriter` is not a workaround of
the accepted single-writer boundary — it *is* that boundary. Its `__enter__` takes the same
process-lifetime advisory lock every governed writer takes, and `connect()` verifies the applied
migration chain against the packaged inventory before handing over the connection
(`storage/sqlite.py:84`; `verify_applied_migrations` is read-only and raises on any drift, gap,
duplicate, or checksum mismatch). What the procedure declines to reuse is not the writer boundary but
two things that are wrong for this job: a preparation helper that rewrites reference rows (§4.3), and
a closure helper whose predicates are too weak for an irreversible one-shot (§4.4). The missing
constraints are supplied in the same transaction as the update, rather than by widening a permanent
function that no longer has a caller who needs them.

## 6. Ruling 053-C — exact transaction predicates and intended effects

### 6.1 Selection predicates — all required, conjunctively

The procedure fails closed unless **exactly one** private target row satisfies **all** of:

| # | Predicate |
|---|---|
| 1 | the **exact owner-resolved historical job id** |
| 2 | `job_kind = 'm3_2_acquisition'` |
| 3 | `stage = 'M3.2A'` |
| 4 | `job_state = 'running'` |
| 5 | `finished_at_utc IS NULL` |
| 6 | exactly **zero** `ops_retrieval_attempts` rows for that job |

Predicates 2 and 3 are the accepted constants, not invented literals: `ACQUISITION_JOB_KIND` is
`'m3_2_acquisition'` (`m3/acquisition.py:218`) and `M3.2A` is a member of `ACQUISITION_WINDOWS`
(`m3/acquisition.py:204`).

**Zero candidate rows, more than one candidate row, or any predicate unsatisfied is a STOP before the
write.**

### 6.2 The single conditional UPDATE

The **one** `UPDATE` must additionally carry the row-state predicates in its own `WHERE` clause — job
id, `job_kind`, `stage`, `job_state = 'running'`, and `finished_at_utc IS NULL` — and must require:

```text
cursor.rowcount == 1
```

Anything other than exactly one affected row aborts the transaction. Restating the predicates in the
`WHERE` clause is deliberate: it makes the update itself conditional, so a row that changed between
the select and the update cannot be overwritten on the strength of a stale read.

### 6.3 The only intended database effects

On that one row, and nowhere else:

| Column | Before | After |
|---|---|---|
| `job_state` | `running` | `stopped` |
| `finished_at_utc` | `NULL` | one new UTC instant |
| `detail` | prior text | the fixed owner closure detail below |

`stopped` is a literal migration `0001`'s existing `CHECK` constraint already admits; **no state,
column, index, table, trigger, or migration is added.**

### 6.4 The fixed closure detail text

This public, non-secret text is fixed exactly, and the later execution packet must use it verbatim:

```text
Owner-authorized offline closure of the interrupted initial M3.2A T5 invocation; no receipt emitted; recovery remains UNDETERMINED; old run permanently non-resumable; accepted physical-attempt consumption remains 1 of 801.
```

### 6.5 Lease and storage-churn boundary

The ordinary lease file payload may change **only** through normal acquire/release (§4.2). Its
**inode must remain unchanged**, and its final state must be `released`. Ordinary SQLite WAL/SHM churn
is allowed. **No other logical row or governed artifact may change.**

## 7. Ruling 053-D — the evidence contract for the later execution

The later exact execution packet **must** impose all of the following. This record fixes the
obligations; it discharges none of them.

### 7.1 Required preflight, before any real write

1. Resolve the private catalog, lock directory, and historical job id **without printing or
   committing** private absolute paths, identifiers, identity values, or raw bodies.
2. Verify repository HEAD, and that tracked network remains **false / false**.
3. Verify catalog migration head **`0013`** and the SQLite quick, integrity, and foreign-key gates.
4. Prove **exactly one** target row satisfies every §6.1 predicate.
5. Capture private **before-state** hashes and counts sufficient to prove blast radius: all table row
   hashes and counts; raw-object and lineage counts and hashes; the receipt inventory; the lease
   inode; and attempt and event counts.
6. Build the exact ephemeral procedure in a disposable `mktemp -d` scratch directory **outside the
   repository**, record its **SHA-256** privately, and run it **first against a synthetic catalog
   fixture**.
7. Complete the §7.2 synthetic proof.
8. Re-verify that **no live writer holds the OS lock** immediately before the real transaction.

**Any mismatch, ambiguity, extra candidate row, live lock, integrity failure, unexpected mutation, or
unavailable proof is a STOP before the real write.**

### 7.2 Required synthetic proof

Against the synthetic fixture, before the real catalog is touched:

| # | Case | Required behaviour |
|---|---|---|
| 1 | positive closure | succeeds, exactly three columns of one row change |
| 2 | unknown job id | refuses |
| 3 | wrong `job_kind` | refuses |
| 4 | wrong `stage` | refuses |
| 5 | already-terminal `job_state` | refuses |
| 6 | non-null `finished_at_utc` | refuses |
| 7 | non-empty attempt ledger | refuses |
| 8 | stale `state="held"` lease metadata | re-acquires normally, **inode unchanged** |
| 9 | live lock contention | refuses |
| 10 | injected fault inside the transaction | rolls back, no partial effect |
| 11 | blast radius | table-by-table before/after comparison |

### 7.3 Required postconditions, after the real transaction

- exactly the **three** intended columns of **exactly one** row changed;
- the target is `stopped`, with a non-null finish time and the §6.4 fixed detail;
- attempt rows remain **zero**; the event count is unchanged;
- all non-target tables and non-target columns are byte- or logically unchanged by the recorded
  hashes;
- raw object, lineage, receipt inventory, and governed originals unchanged;
- **no receipt created or reconstructed; no attempt row inserted; no orphan adoption, quarantine, or
  reconciliation**;
- the lease file is present, at the **same inode**, final state `released`;
- integrity gates pass;
- the repository stays clean and byte-identical;
- tracked network stays **false / false**;
- **no SEC or network action occurred.**

## 8. Ruling 053-E — finding dispositions

The closure-architecture discovery's findings are disposed of as follows. Consistent with repository
convention for nonblocking observations recorded inside a decision, **this ruling creates no new
limitations-register entry**, and the register is byte-unchanged by this record.

| Finding | Severity | Disposition |
|---|---|---|
| **F-1** — `prepare_operational_catalog` blast radius (§4.3) | **MAJOR** | **Accepted, and resolved architecturally by prohibition.** The helper is not called. |
| **F-2** — under-constrained `finish_acquisition_run` (§4.4) | **MAJOR** | **Accepted, and resolved architecturally** by not using it, plus the §6.1–§6.2 same-transaction predicates and the `rowcount == 1` requirement. |
| **F-4** — no public closure surface (§4.5) | **MAJOR observation** | **Accepted.** A permanent surface is **declined as unnecessary** for a one-time governed procedure (§5). |
| **F-3** — receipt / carry-in trap | **MAJOR planning finding for M3-L16** | **Accepted only as a later design constraint.** **Not acted on here.** |
| **F-5** — no per-route runtime counter | **MINOR planning observation** | Recorded. The bulk-route headroom of **5** is **accounting**, not a claim of runtime enforcement. |
| **F-6** — Decision 050 §9 preflight obsolete after the incident | **MINOR planning observation** | Recorded for the future T5 instrument (see §9.3). |
| **F-7** — lease expiry metadata unused | **OPTIMIZATION** | **Deferred. Do not alter locking.** |

**The M3-L16 discovery is useful planning evidence only.** No M3-L16 architecture and no M3-L16
implementation is accepted or authorized by this record.

## 9. Ruling 053-F — authority granted and withheld

### 9.1 Granted

Decision 053 authorizes exactly two things:

1. the **procedure architecture** fixed in §§5–7;
2. a **later exact owner execution packet** for it.

### 9.2 Withheld

Decision 053 itself authorizes **no** private evidence read, **no** real catalog open — not even
read-only — **no** real closure, and **no** operational-state mutation. It further authorizes none of:

- any production, test, configuration, schema, migration, receipt, reason-code, runbook, template, or
  limitations-register change — **no permanent surface will be created**, so no implementation commit
  and no independent code-review cycle for one is required;
- resume, retry, replacement, `--resume-from`, receipt creation, attempt backfill, raw mutation,
  orphan adoption or quarantine, reconciliation, or lease deletion, clearing, or manual takeover;
- live acquisition, a clean new run, T6, M3.2B, dependent-plan derivation, Gate H, M3.3+, publication
  of research output, or any live-readiness claim;
- tracked or private network enablement; DNS, connectivity tests, `curl`, `wget`, `ping`, an SEC
  request, or any remote contact;
- a commit tag, force push, rebase, amend, cherry-pick, or history rewrite.

Tracked network configuration remains **false / false**. CompanyFacts and Frames remain disabled and
prohibited. The approved ceiling **801** is never increased, reset, shadowed, or reinterpreted.

**The later one-time execution remains separately owner-packet-gated and is irreversible.**

### 9.3 Limitations and the future T5 instrument

**M3-L14** and **M3-L15** remain **`ACTIVE`** and unchanged. **M3-L16** remains **`ACTIVE`** and
**continues to block every clean-run and live authorization**; nothing here discharges it, and no
session may read this record as live readiness.

A future T5 instrument **must explicitly supersede** Decision 050 §9's now-impossible preflight
assumptions — consumed count **0**, the operational catalog **absent**, and **no prior M3.2 live run**,
receipt, or raw object. **Decision 053 does not do so**, and no session may treat this paragraph as
having done so.

## 10. Path and publication boundary

Exactly **three** repository paths are authorized for this recording, with **no fourth**:

1. `Docs/Decisions/decision_053_m3_2_interrupted_run_closure_procedure_authorization.md` (this record)
2. [`Docs/Decisions/decision_registry.md`](decision_registry.md)
3. [`Milestones/STATUS.md`](../../Milestones/STATUS.md)

Expressly **not** edited: any accepted decision 001–052; the accepted contract; the interrupted-run
recovery template; the SEC data dictionary; the limitations register; `Docs/decision_index.md`;
`Docs/m3/templates/evidence_index.md`; every durable review artifact; every production source; every
test; every configuration; every migration; the receipt schema; the operator runbook; the master plan;
the `Makefile`; `pyproject.toml`; every script; and every other `Docs/` and `Milestones/` path.

One governance-only commit containing exactly those three paths, with exact subject:

```text
Authorize M3.2 interrupted-run closure procedure
```

followed by **one normal fast-forward push** to `origin/main`. No force, no `--force-with-lease`, no
rebase, no squash, no amend, no cherry-pick, no replacement branch, and **no history rewrite**.
**NO TAG** — **M3.2 is not complete.**

## 11. Recorded status

```text
M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE:   AUTHORIZED — ARCHITECTURE AND BOUNDARIES FIXED
CLOSURE_EXECUTION:                        NOT PERFORMED BY THIS RECORD
CLOSURE_EXECUTION_AUTHORITY:              REQUIRES_SEPARATE_OWNER_PACKET
PERMANENT_PRODUCTION_SURFACE:             DECLINED — NOT REQUIRED, NOT AUTHORIZED
HISTORICAL_JOB_STATE_NOW:                 running
OLD_RUN_CLASSIFICATION:                   UNDETERMINED
OLD_RUN_RESUME:                           NEVER
ACCEPTED_CONSUMED_PHYSICAL_ATTEMPTS:      1_OF_801
REAL_CLOSURE:                             NOT EXECUTED / NOT AUTHORIZED BY THIS RECORD
PRIVATE_EVIDENCE_ACCESS:                  NONE
OPERATIONAL_STATE_MUTATION:               NOT_AUTHORIZED
RECEIPT_CREATION:                         PROHIBITED
HISTORICAL_LEDGER_BACKFILL:               PROHIBITED
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

## 12. Formal outcome

```text
M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED
```

**Next authorized action:**
`CLAUDE_M3_2_INTERRUPTED_RUN_CLOSURE_EXECUTION_PACKET`

The owner may later issue that exact packet. **It does not self-execute**, no session may begin the
closure or any part of it before it is issued, and it grants no network or live authority in advance.

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
