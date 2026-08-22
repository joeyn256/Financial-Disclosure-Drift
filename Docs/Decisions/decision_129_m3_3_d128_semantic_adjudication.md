# Decision 129 — The D128 Semantic Adjudication

```text
STATUS: ACCEPTED — OWNER RULING, CLOSED
RECORD_TYPE: OWNER SEMANTIC ADJUDICATION OF A COMPLETED COMPLETE-SOURCE CANARY —
  A RETROSPECTIVE DURABLE RECORD, PUBLISHED AFTER THE RUN
DATE: 2026-08-22
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OWNER_TOKEN: M3_3_D129_D128_SEMANTIC_ADJUDICATION_OWNER_ACCEPTED
OUTCOME: D128_SEMANTIC_REPAIR_REQUIRED
DISPOSITION: D128 IS PARTIALLY ACCEPTED — EXECUTION MECHANICS ACCEPTED,
  SEMANTIC COUNTS REJECTED AND NOT OWNER-CERTIFIED
SCOPE: THE ADJUDICATION OF THE COMPLETED D128 RUN AND THE DEFECTS IT EXPOSED — NOT A
  REPAIR, NOT A RERUN, NOT A CAPACITY MODEL, AND NOT AN EXECUTION AUTHORIZATION
CLASSIFICATION: PARSER_IMPLEMENTATION_DEFECT (two, sections 5 and 6)
D128_WORLD_DISPOSITION: RETAIN UNCHANGED — NOT RESUMABLE, NOT REPAIRABLE IN PLACE,
  AND NOT ARCHIVED, DELETED, MOVED, OR MUTATED BY THIS RECORD
CORRECTED_RERUN_AUTHORIZATION: NO
REPAIR_IMPLEMENTATION_AUTHORIZATION: NO
ARCHIVAL_OR_DELETION_AUTHORIZATION: NONE
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_V3_EXECUTION_AUTHORIZATION: NO
F1_EXECUTION_AUTHORIZATION: NO
F2_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
DISPOSABLE_WORLD_CREATION_AUTHORIZATION: NO
CATALOG_WRITE_AUTHORIZATION: NONE
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The owner's semantic adjudication of the completed D128 complete-first-source canary,
run identity `m3_3_d128_complete_first_source_v1`.

## 1. What this record is, and what it is not

**It is a retrospective durable record of a run that had already finished.** D128 executed to
completion before this file existed. **This file did not exist before the run and did not authorize
it**; the authorizing instrument was the GPT-5.6 Sol owner instrument issued at the time, which is
not held in this repository and which this record does not reconstruct. What D129 adjudicates is
**the result**, not the launch.

**It is a partial acceptance, and the partition is the whole point.** D128 is accepted as an
execution and rejected as a measurement. §3 lists exactly what is accepted; §4 lists exactly what is
not. **Neither list may be read without the other**, and neither may be summarized as "D128 passed"
or as "D128 failed" — it did one and not the other.

**The verdict is `D128_SEMANTIC_REPAIR_REQUIRED`.** Two implementation defects (§§5–6) mean the
run's accession census is **structurally incomplete**, not noisy. **No E0 authorization follows from
D128**, and no downstream research count may rest on it.

**It is not a repair.** No production source, test, schema, migration, configuration, or authority
constant changed in this publication. §§7–10 state the invariants a corrected implementation must
satisfy; **writing that implementation is a later stage and is not authorized here.**

**It is not a rerun and not a capacity model.** §11 publishes the corrected D128 resource record and
two corrections to the earlier summary; §12 rules that this record's numbers are **not** a
sufficient basis to authorize the corrected run.

**It disposes of nothing physical.** §14 rules the D128 world **retained unchanged**. Archival and
internal reclamation are D130 and are **not** authorized here.

## 2. Entry state

Branch `main` at published `298ad7f9c50a1a23dfe88f7e00ea9197b22f9f40`, tree
`0b77ed01f1b0b7c9758ba609e201687e8f4c2e44`, `origin/main` identical at `0`/`0` and the worktree
clean, with governance published through [Decision 127](decision_127_m3_3_pre_f2_admission_guard.md).
Migration head `0015`; migration `0016` **absent and unapplied**. All three activation constants in
`src/disclosure_drift/m3/e0.py` — `PRE_E0_CATALOG_TRANSITION_AUTHORITY`,
`M3_3_E0_EXECUTION_AUTHORITY`, and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — remain `None`. Both
tracked switches in `configs/project.yaml` remain `false`: `network.enabled` and
`network.m3_acquire_enabled`, at request ceiling `0`.

**One numbering condition is stated rather than smoothed.** There is **no `decision_128_*.md`
file**, and there never was one. `D128` names a **run identity**, not a decision record: the
disposable canary world `m3_3_d128_complete_first_source_v1`. The registry index therefore steps
from `127` to `129`, and that gap is expected rather than missing — the same shape as the
Decision 102 owner finding the registry already carries as an open item, whose findings
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §1 restates. **This record is the first and only governance record of D128.**

## 3. What D128 is accepted for — D129-R1

**The complete-source execution mechanics are ACCEPTED, independently of what the run counted.**
D128 is the first traversal of the entire governed source this project has performed, and it
finished. Each item below is accepted on its own and none of them depends on the accession counts
that §4 rejects:

| Accepted | What it establishes |
|---|---|
| **Full `985,834`-member complete-source traversal mechanics** | The whole governed member set was traversed. Not a prefix, not a sample, not a bounded diagnostic. |
| **Exactly-one-source execution mechanics** | The single-source canary shape executed end to end against the real source. |
| **Runtime and resource evidence** | §11's measurements are accepted as real observations of this code on this machine. |
| **Bounded-memory feasibility** | Peak RSS `3,178,020,864` bytes = `2.9598 GiB` over a `33`-hour run — no unbounded growth. |
| **F1 feasibility** | Accession-resolution finalization ran to completion at complete-source scale. |
| **F2 feasibility** | Association materialization ran to completion in its single transaction at complete-source scale. |
| **[Decision 127](decision_127_m3_3_pre_f2_admission_guard.md) pre-F2 admission-gate operation** | The guard measured, compared, and **admitted** — its first exercise in a real complete-source run. |
| **Complete working-catalog finalization** | The working catalog was finalized rather than left mid-write. |
| **Write-ahead-log checkpoint to zero** | The catalog's WAL stands at `0` bytes after close. |
| **Operational-catalog nonmutation** | The governed operational catalog was not written by the canary. |
| **Monitor and runtime evidence** | The monitoring record is accepted as evidence, subject to the §10 blind spot. |
| **D128 as a valid negative semantic experiment** | Its most valuable output is the defect it exposed. A run that surfaces a structural defect **before** any research artifact depends on it has done its job. |

**Feasibility is not correctness.** Everything in this table is a statement about *whether the path
can run*. **None of it is a statement about what the path recorded**, and §4 is where that question
is answered.

## 4. What D128 is NOT accepted for — D129-R2

**The following are REJECTED and are NOT owner-certified:**

- **D128's accession counts as semantically complete.** They are not; §5 measures the shortfall.
- **`counts_are_trustworthy`.** Refused.
- **`parser_state` as successful.** Refused. The run's parser state may not be read as a success.
- **D128 as an E0-readiness proof.** It is not one, and **no E0 authorization follows from it.**
- **Any downstream research count based on the omitted shard population.** None may be published,
  derived, cited, or carried into an analysis artifact.

**A completed run is not a certified run.** D128 finished, and finishing is exactly what makes the
distinction necessary to state: the run produced a full set of numbers, and those numbers are
wrong in a structured way that a completion signal cannot reveal.

## 5. Defect A — bulk shard dispatch

**Classification: `PARSER_IMPLEMENTATION_DEFECT`.**

**What happened.** `5,337` legitimate governed members whose names match the tracked shape
`HISTORICAL_FILE_NAME_PATTERN` = `^CIK[0-9]{10}-submissions-[0-9]{3}\.json$` in
`src/disclosure_drift/sec/parsers/submissions.py` were routed through
`parse_submissions_document(...)` **instead of the existing historical-submission contract**. That
parser's own contract is stated in its first line: *"One submissions document describes one CIK: its
current name, former names, tickers, exchanges, SIC, fiscal year end, and its accession-level filing
metadata."* A historical overflow shard is not that document. It carries accessions belonging to a
parent registrant and none of the registrant identity the parser requires, so the parser did what a
fail-closed parser should do with a document of the wrong shape — **it rejected it**. **The defect
is the dispatch, not the rejection.**

**The measured consequences.**

| Quantity | Value |
|---|---|
| Rejected shard members | **`5,337`** |
| Accessions carried by those shards | **`5,102,087`** |
| Of those, recovered elsewhere in the traversal | **`2,064,473`** |
| **Genuinely absent from the census** | **`3,037,614`** |
| Real accession universe | **`19,034,205`** |
| **Omitted share of the real universe** | **`15.96%`** |

The subtraction is exact: `5,102,087 - 2,064,473 = 3,037,614`, and
`3,037,614 / 19,034,205 = 0.159585` = **`15.96%`**. **About one accession in six of the real
universe is missing from what D128 recorded.** The complementary census figure —
`19,034,205 - 3,037,614 = 15,996,591` — is published here as an **arithmetic complement of two
owner-measured figures under the stated reading, as scale rather than as a certified count**, and
it is precisely the kind of count **D129-R2 rejects**.

**The Form 10-K family, which is the study's own population.**

| Quantity | Value |
|---|---|
| Form 10-K family accessions absent | **`42,363`** |
| Omitted share, all years | **`13.57%`** |
| Omitted share, development cohort `2010`–`2021` | **`9.11%`** |
| Omitted share, evaluation cohort `2022`–`2026` | **`0.25%`** |

**This differential missingness is a structural confound on the preregistered temporal comparison,
and it is recorded as one rather than as a rounding concern.** The development-cohort omission rate
is roughly **`36`** times the evaluation-cohort rate — `9.11 / 0.25`. A loss that lands on one arm
of a temporal comparison at thirty-six times the rate it lands on the other is **not** a negligible
random loss and cannot be treated as one: it would bias exactly the quantity the study is designed
to measure, in a direction set by an implementation defect rather than by anything about
disclosures. The frozen cohort windows are unchanged by this record —
[Decision 003 v0.2](decision_003_temporal_split.md) and
[Decision 005](decision_005_2025_2026_recency_extension.md) continue to control them.

**No preregistration deviation is recorded by this defect**, and the reason is worth stating: the
counts are rejected before any preregistered analysis consumed them, so nothing frozen has been
changed or worked around. The register that matters here is this record. **If any future artifact
were built on the D128 population, that would be the point at which
[`Docs/preregistration.md`](../preregistration.md) §25 became engaged** — and D129-R2 forecloses
building one.

## 6. Defect B — observation-wide reference binding

**Classification: `PARSER_IMPLEMENTATION_DEFECT`.**

**What happened.** All `5,337` of `5,337` `census_historical_references` rows received **one
incorrect observation-wide registrant CIK**.

| Quantity | Value |
|---|---|
| Rows bound | **`5,337` of `5,337`** |
| True distinct registrants represented | **`4,144`** |
| Persisted distinct registrant identity | **`1`, and it is incorrect** |

**`4,144` distinct registrants collapsed to a single wrong one.** This is not an imprecision in a
few rows; the persisted registrant dimension of that evidence carries no information at all.

**The compounding hazard, recorded because it survives the immediate defect.**
`_historical_registrant_cik(...)` in `src/disclosure_drift/m3/offline_parse.py` resolves a
registrant by reading accepted `census_historical_references` evidence and refuses unless the match
is unique — its guard is `len(rows) != 1`, raising *"resolves to N accepted registrant references;
exactly one is required and no registrant is inferred"*. **That guard detects ambiguity and cannot
detect uniform error.** Zero candidates fail closed; two or more candidates fail closed; **one
consistently wrong candidate passes silently and is then returned as authority.** A fail-closed
check that only tests uniqueness will certify a single wrong answer as confidently as a single right
one, which is how a binding defect upstream becomes an identity assertion downstream.

## 7. Registrant identity and dispatch — D129-R5 and D129-R6

**D129-R5 — the parent declaration is authoritative.** The authoritative shard-to-registrant
relationship is the **explicit parent `filings.files[].name` declaration**. The CIK embedded in a
shard filename **may be used only as corroborating consistency evidence** and **must never become
the sole registrant-identity inference rule**. A name is a label; the parent's declaration is the
assertion. Where the two disagree, no identity has been established.

**Fail-closed behaviour is required for all four of:** no parent; multiple parents; conflicting
parent identities; and a parent/member-name CIK contradiction wherever that comparison is performed.
**Fail-closed means refuse and report**, never guess, never pick a winner, and never fall back to
the filename.

**D129-R6 — archive member order may not affect correctness.** A shard may appear in the archive
**before** its parent, and a corrected implementation must handle that through a **bounded,
deterministic** mechanism — for example deferring shard member names and resolving them against an
explicit parent mapping once the parents are known. **The invariants are frozen here; the algorithm
is not.** D129 deliberately freezes no implementation beyond order-independence, boundedness, and
determinism, so that the repair stage can choose the mechanism that best satisfies them.

## 8. Schema drift — D129-R7

**Three fields observed in the source are accepted as legitimate optional SEC fields:**

- `lei`
- `filings.recent.core_type`
- `filings.recent.isXBRLNumeric`

They **may later be registered as known non-semantic fields**. Doing so is a later matter; **no code
change is made in this publication**, and the parser's existing behaviour of preserving unknown
fields as evidence rather than narrowing them stands unchanged.

**This changes nothing that matters to the study**: not accession identity, not registrant identity,
not the cohort definition, and not the study methodology. It is recorded so that a future reader
does not mistake ordinary upstream field growth for a defect, and does not mistake this
acknowledgement for a schema change.

## 9. The watchdog and launch defect — D129-R10

**The D129 forensic result is `WATCHDOG_FALSE_ALERT_SIGNAL_NOT_DELIVERED_TO_CANARY`.** The watchdog
believed it had stopped the run. It had not, and the run was never interrupted.

**The causal chain, each link measured:**

1. Watchdog v1 targeted Python PID `6456`.
2. Its socket condition was **false**, because the `lsof` selectors were **ORed without `-a`** —
   a selector-composition error, so the predicate never meant what it read as.
3. The launch pattern started the chain as a **background job from non-interactive `zsh`**.
4. Python therefore **inherited `SIGINT = SIG_IGN`**.
5. `kill -INT` consequently **had no effect**.
6. **No rollback and no replay occurred.**
7. **Compact evidence proves one row per member** — the traversal was not disturbed.
8. `/usr/bin/time` **recorded zero received signals**.

**The run was correct despite the watchdog, not because of it.** The alerts were false and the stop
was inert; had the condition been real, the watchdog would have been equally unable to act.

**D129-R10.** Before any corrected long run, **the launch and watchdog design must positively prove
that `SIGINT` is actually deliverable to the canary.** A future watchdog **may not treat a successful
`kill(2)` return as proof that the process stopped** — `kill(2)` reports that a signal was *sent*,
which is a different fact from the process having *acted on it*, and this run is the demonstration
that the two can diverge for the entire length of a `33`-hour execution. **No watchdog implementation
is written in this publication.**

## 10. The monitor blind spot — D129-R11

**The `13` post-traversal stall alerts were false alerts.** Their cause was structural rather than
incidental: member-count progress was **complete** while F1 and F2 **legitimately continued**, so a
detector watching `compact_source_members` saw a counter that had correctly stopped moving and read
it as a stall.

**D129-R11.** Future stall detection based on `compact_source_members` applies **only while**

```text
member_count < governed_member_count
```

**or must otherwise use a phase-appropriate progress signal.** A progress signal that has reached
its terminal value is not evidence of a stall, and a monitor that cannot tell those apart will
manufacture alarms during exactly the phases that take longest. **No code change is made now.**

## 11. The corrected D128 resource record

**These are the durable corrected facts.** They are accepted observations of this code on this
machine (D129-R1) and are **not** projections.

### 11.1 Runtime

| Phase | Elapsed |
|---|---|
| **Wall** | **`119,923.08` s** = `33 h 18 m 43 s` |
| Parse | ≈ `26 h 59 m 30 s` |
| F1 | ≈ `1 h 44 m 47 s` |
| F2 | ≈ `4 h 20 m 54 s` |
| Final close and evidence | ≈ `7 m 27 s` |
| **Post-parse total** | ≈ **`6 h 19 m 12 s`** |

**One arithmetic condition is published rather than smoothed.** The three named post-parse
components sum to `6 h 13 m 08 s`, while the post-parse total is `6 h 19 m 12 s` — a residual of
**`364` s ≈ `6 m 04 s` that is not attributed to any named component**. Parse plus post-parse
(`97,170 + 22,752 = 119,922` s) reconciles with the wall figure to about `1` second, so the residual
sits **inside** the post-parse span rather than being unaccounted for overall. §11.3 records that a
parse-finalization/resolution segment occupies that boundary; **this record does not assert that the
residual is exactly that segment**, and names it as a residual instead.

### 11.2 Memory and storage

| Quantity | Value |
|---|---|
| Peak RSS | `3,178,020,864` B = **`2.9598 GiB`** |
| Final working catalog | `103,694,548,992` B = **`96.5729 GiB`** |
| Minimum free during the run | `18,851,307,520` B = **`17.5568 GiB`** |
| Final free | `28,195,401,728` B = **`26.2589 GiB`** |

**The continuous `10 GiB` hard-stop floor from
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5) was never breached**: the
run's minimum free stood `7.5568 GiB` above it.

### 11.3 Two corrections to the earlier summary

**Correction 1 — the pre-F2 free space at admission.** The [Decision 127](decision_127_m3_3_pre_f2_admission_guard.md)
gate **admitted** (D129-R1). The free space at that moment was approximately
**`31.98`–`32.01 GiB`**, **not** the approximately `37 GiB` the earlier summary stated. Against the
frozen floor `PRE_F2_MINIMUM_FREE_BYTES` = `30 * 1024**3` = `32,212,254,720` bytes, **the actual
margin above the gate was approximately `2 GiB`** — not the approximately `7 GiB` the superseded
figure implied. **The gate did its job with far less room than anyone believed at the time**, and
that is the fact a corrected-run capacity model has to start from.

**Correction 2 — write-ahead-log attribution.** The approximately **`15.17 GiB` peak WAL occurred
BEFORE the pre-F2 gate**, during parse-finalization/resolution. **F2's own WAL peak was
approximately `8.67 GiB`.** Attributing the `15.17 GiB` peak to F2 would misplace the largest
transient storage demand of the run into the wrong phase — and, worse, into the phase the pre-F2
gate protects, which would make the gate look better calibrated than the measurements show it to be.

### 11.4 The D124 planning comparison

| Basis | F1 + F2 |
|---|---|
| [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §8 planning | ≈ `3.37 h` |
| **Actual** | **`6 h 05 m 41 s`** = `21,941` s |
| **Underprediction** | **≈ `1.8x`–`1.9x`** |

`21,941 / 12,132 = 1.81`. The D124 §8 model was published as planning estimates rather than
observations, and this is the first complete-source measurement against it. **It underpredicted the
finalization phases by nearly a factor of two.**

## 12. Capacity ruling — D129-R12

**The old [Decision 124](decision_124_m3_3_capacity_reconciliation.md) launch-capacity model is NOT
sufficient by itself to authorize a corrected rerun.** Three independent reasons, each of which
would be enough on its own:

1. **D128's actual storage and runtime exceeded important D124 projections** — §11.4 measures the
   F1+F2 underprediction at about `1.8x`–`1.9x`.
2. **The real pre-F2 margin was only about `2 GiB`** (§11.3), not the comfortable figure the earlier
   summary implied.
3. **A corrected parse adds millions of presently absent accessions and records** — `3,037,614`
   accessions are missing from D128 (§5), and a corrected run must store what D128 never stored, so
   D128's own `96.57 GiB` final catalog is a **floor** for the corrected run rather than an estimate
   of it.

**A new corrected-run capacity reconciliation is required before another complete-source execution
authorization.** **This record does not construct that model**, and nothing in §11 may be used as
one: §11 reports what a *defective* run consumed, which is systematically less than what a corrected
run will consume.

**Nothing in D124 is retired or relaxed by this.** The D124 §9 (D124-R5) gates — the `>= 105 GiB`
start gate, the continuous `10 GiB` floor, the `>= 30 GiB` pre-F2 admission gate, no `VACUUM`, and
explicit `SQLITE_TMPDIR` placement — **all stand exactly as written**. D129-R12 rules the *model*
insufficient as an authorization basis; it does not weaken a single gate.

## 13. Prior canaries — D129-R9

**D117, D120, D122, and D123 retain their prior acceptance for their stated purposes.** They were
performance, feasibility, and prefix experiments, and **structurally could not have reached terminal
parser semantic adjudication**: none of them traversed the complete source, so none of them could
have encountered the shard population at the scale that made Defect A visible. Finding a defect that
only a complete traversal can expose is not a retroactive indictment of experiments that were never
in a position to expose it.

**No prior owner acceptance is retroactively invalidated.** Decisions 121 through 127 stand as
written, and [Decision 123](decision_123_m3_3_f2_bounded_characterization.md) §8's scope limits
remain the correct account of what that record does and does not establish.

## 14. The D128 world disposition — D129-R8

**D128 is NOT resumable and NOT repairable in place.** A corrected complete-source proof requires
**all four** of:

- **new code**;
- **a new run identity**;
- **a new create-once world**;
- **a full source rerun from the beginning**.

**Repair in place is not available and is not a shortcut being declined for caution** — the world's
create-once semantics and the structural nature of the omission mean there is nothing to resume
into.

**D128 is nevertheless valuable pre-correction evidence**, and it is the only complete-source
observation that exists. **For now: RETAIN D128 UNCHANGED.**

**A next separate owner stage — D130 — will archive it cryptographically to the external `SSK SSD`
and only then authorize exact internal deletion and reclamation.** **This publication archives
nothing, deletes nothing, moves nothing, and mutates nothing**, and the ordering is the same one
[Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) §7 established: verified
external preservation first, authorized internal retirement only after it.

## 15. Owner rulings D129-R1 – D129-R12

| Ruling | Content |
|---|---|
| **D129-R1** | **D128's complete-source execution mechanics are ACCEPTED** — the full `985,834`-member traversal, exactly-one-source execution, runtime and resource evidence, bounded-memory feasibility, F1 and F2 feasibility, the D127 pre-F2 gate's operation, working-catalog finalization, the WAL checkpoint to zero, operational-catalog nonmutation, the monitor and runtime evidence, and D128 as a valid negative semantic experiment (§3). |
| **D129-R2** | **D128's semantic counts are REJECTED and NOT owner-certified** — the accession counts as semantically complete, `counts_are_trustworthy`, `parser_state` as successful, D128 as an E0-readiness proof, and any downstream research count based on the omitted shard population (§4). **No E0 authorization follows.** |
| **D129-R3** | **Bulk historical-shard misdispatch is a BLOCKING `PARSER_IMPLEMENTATION_DEFECT`** — `5,337` shard members rejected, `3,037,614` accessions genuinely absent, `15.96%` of the real universe omitted, and a `9.11%` vs `0.25%` cohort differential that is a **structural confound on the preregistered temporal comparison** (§5). |
| **D129-R4** | **Observation-wide historical-reference CIK binding is a BLOCKING `PARSER_IMPLEMENTATION_DEFECT`** — `5,337` of `5,337` rows carry one incorrect registrant identity where `4,144` distinct registrants are represented (§6). |
| **D129-R5** | **The parent `filings.files[].name` declaration is the authoritative child binding.** A filename CIK is **corroborative only** and may never be the sole inference rule. **Ambiguity or conflict fails closed** — no parent, multiple parents, conflicting parent identities, and parent/member-name contradiction (§7). |
| **D129-R6** | **Archive member order cannot determine correctness.** The corrected path must tolerate a shard appearing before its parent, **deterministically and boundedly**. No implementation algorithm is frozen beyond those invariants (§7). |
| **D129-R7** | **`lei`, `filings.recent.core_type`, and `filings.recent.isXBRLNumeric` are ACCEPTED optional non-semantic SEC fields**, registrable later as known non-semantic fields. **No code change now**, and nothing about accession identity, registrant identity, cohort definition, or methodology changes (§8). |
| **D129-R8** | **A corrected complete-source canary must rerun from scratch in a new world** — new code, new run identity, new create-once world, full source rerun. **D128 is not resumable and not repairable in place.** **RETAIN D128 UNCHANGED**; D130 archives it, and only then is internal reclamation authorized (§14). |
| **D129-R9** | **Prior bounded and performance canaries remain accepted for their original purposes** — D117, D120, D122, D123. They structurally could not have reached terminal parser semantic adjudication, and **no prior owner acceptance is retroactively invalidated** (§13). |
| **D129-R10** | **`SIGINT` delivery must be positively proven and watchdog stop effectiveness repaired before another long run.** A future watchdog **may not treat a successful `kill(2)` return as proof that the process stopped**. Forensic result: `WATCHDOG_FALSE_ALERT_SIGNAL_NOT_DELIVERED_TO_CANARY` (§9). |
| **D129-R11** | **Member-count stall detection ends with member traversal**, or must use a phase-specific progress signal thereafter. The `13` post-traversal stall alerts were **false alerts** caused by complete member progress while F1/F2 legitimately continued (§10). |
| **D129-R12** | **A new corrected-run capacity reconciliation is required before rerun authorization.** The D124 launch-capacity model is **not sufficient by itself**: actual storage and runtime exceeded important projections, the real pre-F2 margin was about `2 GiB`, and a corrected parse adds millions of presently absent accessions and records. **No new model is constructed here**, and **no D124 gate is relaxed** (§12). |

## 16. What this record does not do

**It authorizes no execution.** No corrected rerun, no complete-source run, no E0, no E0-v3, no F1,
no F2, no canary of any kind, no disposable run world, no migration `0016`, no network, and no
acquisition. **Accepting a run's mechanics is not authorizing another run**, and identifying the
repair a rerun needs is not authorizing the rerun either.

**It implements no repair.** The §7 identity and dispatch invariants, the §8 field registration, the
§9 watchdog repair, and the §10 monitor correction are **specified and not written**. No production
source, test, schema, migration, configuration, or authority constant changed in this publication,
and no capacity constant moved.

**It archives, deletes, moves, and mutates nothing.** D128 is retained exactly as the run left it
(D129-R8). The operational catalog, the frozen source, the evidence root, the retention records, and
the external archive are all untouched, and **no `SSK SSD` operation of any kind occurs here** — the
volume remains cold/archive only with no reformat, per
[Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) §11 (D125-R4).

**It amends no frozen research definition.** The cohort windows, maturity gates, primary outcome,
hypotheses, thresholds, and bootstrap seed are unchanged. §5 records a structural confound **as a
finding**; it does not amend [`Docs/preregistration.md`](../preregistration.md),
[`Docs/leakage_register.md`](../leakage_register.md), or
[`Docs/research_risk_register.md`](../research_risk_register.md), and it records **no §25 deviation**
— the rejected counts never reached a preregistered analysis.

**It supersedes nothing.** Decisions 121 through 127 stand as written, and the D124-R5 gates carry
forward intact, **including the `>= 30 GiB` pre-F2 gate — which §11.3 shows was met by about `2 GiB`
rather than comfortably, a calibration fact and not a relaxation.**

**All three activation constants remain `None`**, the operational catalog remains at migration head
`0015`, migration `0016` remains absent and unapplied, no E0-v3 namespace exists, and both tracked
network switches remain `false` at request ceiling `0`.

**The next stage is D130 — D128 external archival and internal reclamation — and nothing else.**
After D130: a bounded parser, reference, and watchdog correction stage; then semantic validation;
then the corrected capacity reconciliation; then the corrected complete-source canary. **Each of
those requires its own owner instrument.**

**Complete source is NOT authorized. E0 is NOT authorized.**
