# Decision 136 — The External SSD Active-Working-Volume Qualification, and the Narrow One-Canary Exception

```text
STATUS: ACCEPTED — OWNER RULING / QUALIFICATION EVIDENCE AND ARCHITECTURE EXCEPTION
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF A COMPLETED BOUNDED EXTERNAL-VOLUME QUALIFICATION,
  TOGETHER WITH THE OWNER'S NARROW EXCEPTION TO THE STANDING D125-R4 COLD/ARCHIVE-ONLY RULE
DATE: 2026-08-23 (record). The qualification itself ran 2026-08-23 local time; its evidence is
  stamped 2026-08-23T04:22Z UTC onward, the same evening
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
CLASSIFICATION: BOUNDED_VOLUME_QUALIFICATION_ONLY
ACCEPTANCE_TOKEN: M3_3_D136_QUALIFICATION_EVIDENCE_OWNER_ACCEPTED
NUMERIC_ACCEPTANCE_TOKEN: M3_3_D136_D135_NUMERIC_AUTHENTICATION_OWNER_ACCEPTED
ARCHITECTURE_RULING_TOKEN: M3_3_D136_SINGLE_CANARY_EXTERNAL_SSD_EXCEPTION_SELECTED
QUALIFICATION_AUTHORIZATION: M3_3_D136_EXTERNAL_SSD_ACTIVE_VOLUME_QUALIFICATION_AUTHORIZED — issued
  outside this repository and now spent; this record authorized none of the work it publishes
VERDICT: D136_EXTERNAL_SSD_PASS_WITH_ARCHIVE_ISOLATION_REQUIRED
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049
QUALIFIED_VOLUME_FILESYSTEM: ExFAT VIA APPLE FSKit — NON-JOURNALED, LOCAL PHYSICAL USB SSD
POST_CLEANUP_EXTERNAL_FREE: 310,498,557,952 BYTES / 289.1743 GiB
ACCEPTED_START_FREE_FLOOR: 185 GiB — 198,642,237,440 BYTES — UNCHANGED AND STILL CONTROLLING
ACCEPTED_PRE_F2_FREE_FLOOR: 50 GiB — 53,687,091,200 BYTES — UNCHANGED AND STILL CONTROLLING
CAPACITY_SURPLUS_OVER_START_FLOOR: 111,856,320,512 BYTES / 104.1743 GiB
D135_NUMERIC_RULING: THE AUTHORITATIVE ROW-UPLIFT NUMERATOR IS 21,098,678. THE 21,099,278 VALUE WAS
  AN OWNER PACKET TYPO AND APPEARS IN NO REPOSITORY OR EVIDENCE FILE
REPOSITORY_CORRECTION: NONE REQUIRED AND NONE AUTHORIZED — THE REPOSITORY WAS ALREADY CORRECT
POWER_LOSS_CLAIM: NONE — PROCESS-CRASH RECOVERY ONLY (D136-R6)
D125_R4_DISPOSITION: REMAINS THE GENERAL RULE. ONE NARROW EXCEPTION IS CREATED (D136-R8)
SHARED_FAILURE_DOMAIN: EXPLICITLY ACCEPTED FOR ONE FUTURE CORRECTED CANARY ONLY (D136-R9)
EXECUTABLE_CHANGE_SET: NONE — NO SOURCE, TEST, SCRIPT, CONFIGURATION, SCHEMA, OR MIGRATION BYTE
CODE_CONSTANT_DISPOSITION: PRE_F2_MINIMUM_FREE_BYTES REMAINS 30 * 1024**3 IN CODE — NOT EDITED HERE
  AND NOT AUTHORIZED TO BE EDITED HERE
D131_CONFIGURATION_DISPOSITION: UNCHANGED. NO D134 CANDIDATE ADOPTED
D134_DISPOSITION: mmap AND RELAXED-CHECKPOINT CANDIDATES REMAIN REJECTED
D128_SEMANTIC_DISPOSITION: UNCHANGED. D129-R2'S REJECTION OF EVERY D128 COUNT STANDS ENTIRELY
D129_R8_DISPOSITION: UNCHANGED — ANY LATER CANARY RUNS FROM SCRATCH, NEW WORLD, NEW RUN ID
EXTERNAL_VOLUME_ADOPTION_AUTHORIZATION: NO — QUALIFICATION IS NOT ADOPTION
CORRECTED_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
NEXT_STAGE: DECISION 137 — EXTERNAL WORKING-ROOT AND SAFETY IMPLEMENTATION (D136-R11)
```

The owner's governance publication of the bounded external-volume qualification that
[Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) §10 (**D135-R5**)
required, together with the owner's ruling that the evidence is accepted, that the exact candidate
SSD is mechanically suitable for the corrected workload, and that a **narrow, single-canary
exception** to the standing cold/archive-only rule is created for that one volume.

## 1. What this record is, and what it is not

**It is a qualification verdict about one physical device.** D135-R5 selected the external-volume
path and named six independent requirements a candidate must prove — filesystem suitability, SQLite
WAL and locking correctness, durability and recovery, capacity against the D135 floors,
sustained-write practicality, and safe separation from retained D130 evidence. It also ruled that
**the currently attached SSD must not be assumed suitable until a future D136 proves it**. This
record publishes that proof, and its formal outcome is
`D136_EXTERNAL_SSD_PASS_WITH_ARCHIVE_ISOLATION_REQUIRED`.

**It is not an adoption, and it is not a canary authorization.** D135 §10 stated the sequence
plainly: *selecting a path is not qualifying a volume, and qualifying a volume is not adopting it* —
three distinct steps, each needing its own instrument. D136 completes the second. The third belongs
to **Decision 137** (§11), and even a completed D137 does not start a run.

**Its executable change set is empty.** No source, test, script, configuration, schema, or migration
byte moves with it. In particular `PRE_F2_MINIMUM_FREE_BYTES` in
`src/disclosure_drift/m3/single_source_canary.py` **remains `30 * 1024**3`**, exactly as
[Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) §8 (D135-R3) left it. The
correction of that constant is D137 work (D136-R11 item 6), not this record's.

**It certifies no count and moves no semantic position.** Nothing here revisits
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (D129-R2), which still rejects
every D128 semantic count, and D129-R8 still requires any later canary to run **from scratch, in a
new world, under a new run identity**.

**It makes no power-loss claim.** That limitation is stated as a ruling of its own, D136-R6, rather
than buried in a limitations section, because the qualification's most quotable numbers are the ones
most likely to be over-read.

## 2. Entry state

Accepted [Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) closed the
capacity half of the pre-complete-source gate with the verdict that the **internal** volume cannot
host the corrected run, and selected external-volume qualification as the next step. At the point the
qualification ran:

- **HEAD** was the D135 publication `7f97d679d5943c8afbb950ce4e784fd2693db511`, tree
  `838a5b5b7cf754b1477356857f6f56303d6ad096`; `origin/main == HEAD`, ahead/behind `0/0`; the working
  tree was clean and nothing was staged.
- **Migration head `0015`**; `0016` absent, unapplied and unauthorized.
- **All three activation constants `None`.** Network disabled at both tracked switches, request
  ceiling `0`.
- The accepted **D131 runtime configuration** was byte-unchanged, so the volume was qualified
  against **the configuration that would actually run**.
- `CensusOrchestrator._parse_bulk` **open as a PRE-NETWORK blocker**
  ([Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §12, D131-R4).

The repository exited the qualification **byte-identical** to that entry state.

## 3. The D135 numeric authentication — and an owner packet typo, recorded transparently

The D136 instrument required the qualification to authenticate D135's capacity arithmetic **before
touching the SSD**, and stated that the locked model's conservative row-uplift numerator was
`21,099,278`, describing the D135 completion summary's `21,098,678` as a typo. It directed a hard
stop returning `D136_BLOCKED_D135_PUBLICATION_NUMERIC_MISMATCH` if the repository disagreed with the
locked model.

**The premise was inverted, and the owner now rules on it.** The authoritative numerator is:

> **`21,098,678`**, from **`15,996,591 + 5,102,087`**, giving
> **`U_rows` = `21,098,678 / 15,996,591` ≈ `1.3189484`**.

The value `21,099,278` appears in **no** repository file and **no** evidence file. It existed only in
the owner's D136 instruction and is recorded here as an **OWNER PACKET TYPO**.

All four required sources were checked and all four agree:

| Source | Numerator present | Notes |
|---|---|---|
| [Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) §4, line 149 | `21,098,678` | the published governance record |
| `capacity_model_locked.json` | `21098678/15996591` | SHA-256 `cba5ba2b…b69a982`, **matching the hash D135 itself published** |
| `model_a_d128_uplift.json` | `21098678/15996591` | `U_rows.value` `1.3189483934420778` |
| the accepted arithmetic cross-check | `21,098,678` (derived) | `21` quantities, two independent paths, exact agreement |

Three independent proofs settle it, and each is reproducible:

1. **The instrument's own stated ratio matches the repository, not its own numerator.** The packet
   gave `U_rows ≈ 1.3189484`. `21,098,678 / 15,996,591 = 1.3189483934…`, which rounds to exactly
   that. `21,099,278 / 15,996,591 = 1.3189859014…`, which does not.
2. **The numerator is derived, not transcribed.** In the accepted cross-check the numerator is
   `u = n + h`, where `n = 15,996,591` (D128 planning accessions) and `h = 5,102,087` (shard-carried
   accessions) are **separately measured inputs**. Reaching `21,099,278` would require
   `h = 5,102,687` — a different measurement, not a different transcription.
3. **Only `21,098,678` reproduces the accepted totals.** Re-running the accepted BSD `bc`
   cross-check reproduced every published figure exactly — projected peak live `158,648,106,397` B,
   projected final durable `137,164,199,880` B, START floor `198,642,237,440` B, PRE-F2 floor
   `53,687,091,200` B. The counterfactual numerator reproduces **none** of them: it yields catalog
   `136,771,648,176` B against the accepted `136,767,758,802` B, pre-F2 consumption
   `129,065,994,296` B against the accepted `129,062,324,047` B, and so on down the model.

**The blocking token was correctly not returned.** `D136_BLOCKED_D135_PUBLICATION_NUMERIC_MISMATCH`
names a mismatch **between the published record and its locked model**. No such mismatch exists: the
publication and the locked evidence are identical, and the locked file hash-authenticates against the
digest D135 published. Returning the blocker would have reported a defect that is not there and spent
an authorized qualification window on a phantom.

**No repository correction is required or authorized**, because the repository was never wrong. The
figure `21,098,678` in D135 §4, in the registry, in `Docs/decision_index.md`, and in
`Milestones/STATUS.md` stands exactly as written and is **not edited by this record**.

## 4. The qualified volume — D136-R1

The qualification identified **exactly one** external volume from live disk metadata cross-referenced
against [Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md) §5. The match was
unambiguous: `/Volumes` held only `Macintosh HD` (a symlink to `/`) and the candidate.

| Item | Value |
|---|---|
| Mount point | `/Volumes/SSK SSD` |
| Volume name | `SSK SSD` |
| **Volume UUID** | **`397A4D4A-9508-391E-814E-3B533C7BD049`** |
| Disk / partition UUID | `411E4166-1A78-4B2B-BB75-9AFB9239C42B` |
| Device node | `/dev/disk4s2`, on external physical `/dev/disk4` |
| Filesystem | **ExFAT**, served by **Apple FSKit** (user-space framework, not a kernel VFS driver) |
| Mount flags | `exfat, local, nodev, nosuid, noowners, noatime, fskit` |
| Protocol / location | USB / External / Solid State |
| Allocation block size | `131,072` bytes (`128` KiB) |
| Volume total | `499,955,924,992` bytes |
| SMART status | **Not Supported** |
| Read-only | No |

**The volume UUID, not the BSD device identifier, is the stable identity.** `disk4s2` is assigned at
attach time and will differ across reboots and re-plugs; the UUID will not. D136-R11 item 2 makes
that distinction a fail-closed requirement of the D137 guard.

**No rejection criterion was triggered.** It is local physical storage — not network-mounted, not
SMB/NFS/WebDAV, not cloud-backed, not remote user-space storage, not read-only. FSKit is a user-space
*implementation* serving a *local* device; that is a correctness surface to test, which the
qualification did, not a disqualification.

## 5. Capacity — D136-R2

**External free capacity passes the D135 START floor with a wide margin, and the floor is unchanged.**

| Quantity | Bytes | GiB |
|---|---|---|
| Post-cleanup external free (minimum of three observations) | `310,498,557,952` | `289.1743` |
| **D135 START floor (D135-R2)** | **`198,642,237,440`** | **`185`** |
| **Surplus** | **`111,856,320,512`** | **`104.1743`** |
| D135 projected peak live footprint | `158,648,106,397` | `147.7526` |
| Headroom at projected peak | `151,850,451,555` | `141.4218` |
| D135 projected final durable footprint | `137,164,199,880` | `127.7441` |
| Headroom at projected final | `173,334,358,072` | `161.4302` |

Three pre-write observations and three post-cleanup observations were taken; **each set had a spread
of `0` bytes**. No archived byte is counted as free — the `189,457,235,968` bytes already in use by
the D130 archive, the D125 archives, and unrelated user data are excluded by measurement.

**The contrast with the internal volume is the point.** D135-R4 measured internal minimum free at
`126,846,775,296` B against the same floor, a shortfall of `71,795,462,144` B. The external volume
clears it by `111,856,320,512` B — a swing of `183,651,782,656` B. **The `185` GiB START floor and
the `50` GiB PRE-F2 floor remain controlling and are not adjusted by this record.**

## 6. SQLite mechanics — D136-R3

Every test used the **project's own environment** — the `.venv` interpreter, Python `3.12.13`,
SQLite `3.53.4` — not the macOS system Python (`3.9.5` / SQLite `3.35.5`). No project code was
altered to obtain any setting.

**The accepted D131 pragma values read back correctly on ExFAT.**

| Pragma | Requested | Effective |
|---|---|---|
| `journal_mode` | `WAL` | `wal` |
| `synchronous` | `FULL` | `2` |
| `cache_size` | `-524288` | `-524288` |
| `wal_autocheckpoint` | `1000` | `1000` |
| `foreign_keys` | `ON` | `1` |
| `busy_timeout` | `10000` | `10000` |
| `mmap_size` | **not set** | `0` |

`page_size` is `4096`. **WAL is effective on this volume** — the requirement whose failure D135-R5
named as disqualifying.

**Locking exclusion is correct, proved with separate operating-system processes rather than two
cursors in one process.** Writer A held `BEGIN IMMEDIATE`; writer B waited its full bounded busy
timeout — `2.1759` s against a `2000` ms setting — and was refused with `OperationalError: database
is locked`, **leaving no row behind**. A reader was never blocked (`0.0005` s) and saw the correct
WAL snapshot: zero rows, because A had not committed. After A committed, B acquired and committed in
`0.003` s. Final state was exactly two rows; `integrity_check` returned `ok`. **No double writer at
any point.**

**Crash recovery is correct in both directions.** Signalling was confined to disposable D136 children
whose PID *and* command line were authenticated immediately before the signal, through ten checks —
positive PID, matches the spawned child, not self, not parent, not init, `ps`-confirmed live, PID
agreement, parent-PID is this process, command line carries the unique marker, command line is the
expected script. No escalation ladder was used and no project or canary process was signalled.

- **Uncommitted transaction.** A child wrote `500` rows inside an open transaction, confirmed
  invisible from a separate process, then received `SIGKILL` (exit `-9`). On reopen the `500`
  uncommitted rows were **absent**, the seed row survived, and `integrity_check` returned `ok`.
- **Committed but not checkpointed.** A child committed `500` rows leaving a `24,752`-byte WAL
  present, then received `SIGKILL`. The WAL was still `24,752` bytes after the kill. A **fresh
  process** recovered **all `500` committed rows**, `integrity_check` returned `ok`, a `TRUNCATE`
  checkpoint returned `[0, 0, 0]`, and the WAL truncated to `0`.

## 7. I/O practicality — D136-R4

**Sequential.** A `2` GiB non-sparse file with deterministic content was written with an explicit
`fsync` before timing completion, hashed on write, and independently re-hashed on read-back. **The
hashes matched.** Allocated bytes equalled logical bytes exactly.

| Measurement | Value |
|---|---|
| Write (excluding sync) | `7.6611` s |
| `fsync` | `0.5166` s |
| `F_FULLFSYNC` | `0.0009` s |
| Read | `6.3516` s |
| **Sustained fsync-complete write** | **`250.438` MiB/s** |
| Sustained `F_FULLFSYNC`-complete write | `250.409` MiB/s |
| Sustained read | `322.438` MiB/s |
| I/O errors | `0` |

Against the qualification floor of **`50` MiB/s** this is a **`5×`** margin. **The floor is a
qualification predicate, not a performance target**, and clearing it by `5×` licenses no runtime
claim.

**Bounded SQLite workload.** A synthetic workload only: D134 was **not** reconstructed, **no** SEC
JSON was parsed, and **no** canary was run. `180,000` rows across `90` commits at a `4` KiB payload
produced a **`793.96` MiB** database in **`4.176` s** — inside the `512` MiB–`1` GiB target band and
far inside the `15`-minute bound.

| Measurement | Value |
|---|---|
| Commit latency — median / p95 / max | `0.0388` s / `0.0544` s / `0.0741` s |
| Explicit checkpoints | `9`, all `busy = 0` |
| WAL high-water | `8.927` MiB |
| Stalls over `5` s | `0` |
| I/O errors | `0` |
| `integrity_check` before and after final checkpoint | `ok` / `ok` |
| Final `TRUNCATE` checkpoint | `[0, 0, 0]`, WAL → `0` |

**One reading trap is recorded so a later session does not fall into it.** The sampled WAL size never
*fell*, because SQLite **reuses** the WAL file in place after a checkpoint rather than shrinking it.
That is not evidence that checkpointing did not happen. The positive evidence that it ran
continuously is that the WAL high-water stayed at `8.927` MiB **while `793.96` MiB of database was
written** — with no checkpointing the WAL would have grown to roughly the full database size.

**No complete-source runtime may be extrapolated from any of these measurements** (D136-R4). The
workload is synthetic, the shape is not the canary's, and D135 §15's limitations — one defective
source run, no F0/F1 interior breakpoint, unmeasured peak temp/spill, an unmeasured D131
deferred-shard reopen phase — are untouched by it.

## 8. Allocation — D136-R5

D135's floor was derived on **internal APFS** allocation behaviour, so the external volume's
behaviour had to be measured rather than assumed.

| Object | Logical | Allocated | Ratio |
|---|---|---|---|
| `2` GiB sequential file | `2,147,483,648` | `2,147,483,648` | `1.000000` |
| `793.96` MiB SQLite database | `832,532,480` | `832,569,344` | `1.0000443` |
| WAL | `1,437,912` | `1,441,792` | `1.0027` |
| SHM | `32,768` | `131,072` | `4.0` |
| Qualification tree total | `833,974,572` | `834,928,640` | `1.001144` |
| **Internal APFS D128 world (D135's basis)** | `103,966,642,558` | `103,995,305,984` | **`1.0002757`** |

**External allocation overhead for large objects is smaller than the internal overhead the `185` GiB
floor was already derived on.** Rescaling D135's projected final durable footprint by the measured
external database ratio adds `6,073,630` B (`~5.79` MiB); rescaling the projected peak adds
`7,024,938` B (`~6.70` MiB). Both are absorbed thousands of times over by the `104.1743` GiB surplus.
**No floor is raised, and D136 proposes no adjustment.**

**The counter-risk is recorded rather than dismissed.** ExFAT's `128` KiB minimum allocation makes
**many small files** disproportionately expensive: an `8,192`-byte SQLite database allocated
`131,072` bytes, a `16×` overhead, and the `-shm` file allocated `4×` its logical size. This is
bounded here because the corrected run world is a few very large objects, where the cost is at most
one partial block per file — **`853,404` separate files would be needed to consume the surplus**.
Where it could still bite is **`SQLITE_TMPDIR` temp and spill files**, whose placement
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5) already requires to be
explicit, and whose peak D135 §15 carries as `0` **because `0` is what the evidence supports, not
because `0` is known to be right**. That interaction is **unmeasured** and is carried forward to
D137, not resolved here.

## 9. What D136 does not establish — D136-R6

**D136 establishes process-crash recovery only.** It does **not** establish:

- power-loss safety;
- surprise-removal safety;
- USB-bridge cache-flush correctness;
- journaled-filesystem semantics.

The filesystem is **ExFAT and has no metadata journal**. A power loss or surprise disconnect during a
metadata update can damage directory structure, not merely an in-flight file. `SIGKILL` testing
exercises **SQLite's** WAL recovery; it exercises **nothing** about filesystem metadata recovery.

**The `F_FULLFSYNC` measurement is explicitly not evidence of a physical flush.** It returned success
in `0.0009` s immediately after a `0.5166` s `fsync`. That is consistent with the flush already being
satisfied by the completed `fsync` — and **equally consistent with the USB bridge silently ignoring
the cache-flush command**. D136 cannot distinguish the two without power-cut testing, which was out
of scope and not authorized. **The claim made is that `F_FULLFSYNC` is available and returns success.
The claim not made is that this device honours a physical cache flush.**

**SMART is Not Supported through this bridge.** There is no drive-health telemetry and no early
warning of media degradation. The volume is also a **shared general-purpose disk** carrying unrelated
user data, not a dedicated project device.

## 10. The D130 archive, the shared failure domain, and the narrow exception — D136-R7, D136-R8, D136-R9

**The archive was authenticated before and after, and did not move — D136-R7.** The `~104` GB pax
archive was **not opened, not hashed, and not re-hashed**; only the governed compact proofs
[Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md) §6 (D130-R2) records were
verified, in `0.040` s. Every one matched:

| Artifact | Bytes | SHA-256 | Result |
|---|---|---|---|
| `d128_complete_first_source_v1.pax.tar` | `103,966,696,960` | `b4f13e92…583013` (D130-recorded) | size unchanged; **body never opened** |
| `d128_source_manifest.tsv` | `3,645` | `af5088e4…66fac4` | unchanged |
| `d128_tar_member_manifest.tsv` | `3,645` | `af5088e4…66fac4` | unchanged |
| `d128_source_manifest_recheck.tsv` | `3,645` | `af5088e4…66fac4` | unchanged |
| `d128_archive_receipt.txt` | `6,343` | `63d8fc4b…f46b94` | unchanged |
| `d130_post_deletion_proof.txt` | `4,251` | `8387e9eb…5d507d` | unchanged |

The postcheck ran **before** any cleanup and found **zero differences** across all `24` entries: entry
set, sizes, mtimes, and compact-proof hashes all identical, and **the archive directory was never
written by D136**. The D136 scratch tree was created as a **sibling at the volume root**, never
underneath the archive. The prior D125 archive was likewise untouched.

**The archive is uniquely retained on this volume.** `d130_post_deletion_proof.txt` records all three
internal D128 paths as `ABSENT` after D130's authorized reclamation. There is **no internal copy**.
Therefore a future active database on this SSD and the retained D130 archive would share:

- the same **filesystem**;
- the same **physical device**;
- the same **cable and USB bridge**;
- the same **surprise-removal failure domain**.

**This is why the verdict is conditional rather than unconditional.** Every other PASS predicate was
met; the single failing one is *no unresolved filesystem-level durability blocker*. The outcome
`D136_EXTERNAL_SSD_PASS_WITH_ARCHIVE_ISOLATION_REQUIRED` is precisely the result the qualification
instrument reserved for this condition. **It was not softened from a FAIL** — no concrete
qualification predicate failed — and it is **not INCONCLUSIVE**, because the testing was defensible
and complete.

### The narrow D125-R4 exception — D136-R8

[Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) §11 (**D125-R4**) rules: *"The
external `SSK SSD` remains cold / archive storage only. No active governed SQLite use. No reformat."*
It carries [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §10 (D124-R6) forward, and
D135's registry entry confirms it stands.

**D136's own testing did not violate it** — bounded synthetic disposable scratch tests are
qualification instruments, not active governed SQLite use, and the D136 authorization expressly
permitted them while expressly declining to adopt the volume.

**D125-R4 remains the GENERAL rule.** The owner now creates one narrow exception:

> **After successful Decision 137 implementation and owner acceptance (§11), this exact volume may host ONE corrected M3.3 complete-source canary working
> world.**

The exception is bounded on every axis:

- It applies **only** to volume UUID **`397A4D4A-9508-391E-814E-3B533C7BD049`**. No other device, and
  not to a re-created filesystem on the same hardware.
- It authorizes **one** corrected canary working world, not arbitrary active governed SQLite use on
  this SSD.
- It permits **no** write inside `/Volumes/SSK SSD/FDD_M3_3_D130_D128_ARCHIVE`. **The D130 archive
  remains immutable.**
- The future working world **must be a separate sibling tree**, outside the archive.
- It grants **no authority now**. D137 must be implemented, independently reviewed, and owner
  accepted first, and even then the canary needs its own authorization.

### The accepted residual risk — D136-R9

The owner **explicitly accepts, for this one future corrected canary only**, the residual risk that a
device-level or filesystem-level failure could affect both the disposable corrected canary world and
the uniquely retained D130 archive.

The reasons are stated so the acceptance can be audited rather than merely asserted:

- internal capacity **cannot** satisfy the accepted D135 floor (D135-R4: a `66.8647` GiB shortfall
  against a container where the floor is `81.04%` of total capacity);
- **every** bounded mechanical SQLite predicate passed;
- the MacBook battery substantially reduces ordinary mains-loss exposure;
- the run remains **disposable** until accepted;
- **no reformat or repartition operation** will endanger the archive beforehand.

**This ruling does not convert ExFAT into a journaled filesystem and does not claim zero risk.** It
records a bounded, reasoned acceptance of a named risk for a single disposable run.

### Physical and run conditions for any later authorization — D136-R10

Any later canary authorization relying on this exception **must** require:

1. Mac connected to external power.
2. SSD physically connected throughout.
3. Mac and SSD kept stationary.
4. No manual eject or unplug.
5. No unrelated write-heavy activity on the SSD.
6. No reformat or repartition.
7. **D130 archive precheck immediately before launch.**
8. **Stable volume-UUID verification.**
9. At least **`185` GiB / `198,642,237,440` bytes** free immediately before launch.
10. Working root **outside** the D130 archive tree.
11. **D130 archive postcheck after the run.**
12. System sleep prevented for the duration, via the governed launcher and runbook.

**These are future run conditions only. No run starts under this record.**

## 11. The next implementation stage — D136-R11

The next stage is **Decision 137**. It must implement and validate, at minimum:

1. **External working-root selection**, using an existing supported surface if one already exists;
   otherwise the **smallest new surface necessary**.
2. A **fail-closed candidate-volume identity guard** keyed on the **stable Volume UUID**
   `397A4D4A-9508-391E-814E-3B533C7BD049`, **not** the volatile `disk4s2` identifier.
3. **Refusal if the selected working root is inside the D130 archive tree.**
4. A pre-launch free-space requirement of **`>= 185` GiB / `198,642,237,440` bytes**.
5. A PRE-F2 requirement of **`>= 50` GiB / `53,687,091,200` bytes**.
6. **Replacement of the known-inadequate `30` GiB `PRE_F2_MINIMUM_FREE_BYTES` behaviour.**
7. Phase-boundary and F2 capacity monitoring consistent with
   [Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) §11 (D135-R7) — with
   the `DURING_F2` hard floor **unchanged at `10` GiB** (D124-R5), and the operator told explicitly
   that **because F2 is a single transaction, a stop is a rollback**.
8. Operator and runbook requirements for external power, stable mount, and `caffeinate`/no-sleep
   execution.
9. **Targeted tests and independent validation.**

**D137 does not start the canary.**

## 12. What did not change — D136-R12

- [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (**D129-R2**) remains
  controlling: **every D128 semantic count remains rejected.**
- **D129-R8 remains controlling:** any future corrected proof runs **from scratch, in a new world,
  under a new run identity.**
- The accepted **D131 runtime configuration is unchanged**.
- **D134's mmap and relaxed-checkpoint candidates remain rejected.**
- **E0 remains unauthorized**; all three activation constants remain `None`.
- **Network remains disabled** at both tracked switches, request ceiling `0`.
- **`census_orchestrator.py::_parse_bulk` remains a separate open PRE-NETWORK blocker**, deliberately
  unrepaired — its repair **must not** be performed as a side effect of unrelated work.
- Every **D124-R5** gate carries forward: the continuous `10` GiB floor, no `VACUUM`, and explicit
  `SQLITE_TMPDIR` placement.
- **D125-R3** (no further evidence deleted for capacity) stands. **D125-R4 stands as the general
  rule**, narrowed only by D136-R8.

## 13. Where the evidence lives

The durable D136 evidence is retained **internally**, outside this repository, at
`~/m3-d136-ssd-qualification` — `15` files, `64,242` bytes, authenticated by
`d136_evidence_manifest.json`, SHA-256:

```text
4a9e45993974bb8b6bc1ffbc1cd5424a7e6629b3fef3317f8ffa21262524c001
```

All fourteen files the qualification instrument required are present: `entry_gate.json`,
`d135_numeric_authentication.json`, `volume_identity.json`, `capacity_observations.json`,
`filesystem_classification.json`, `d130_archive_before.json`, `sequential_io_result.json`,
`sqlite_pragma_result.json`, `sqlite_locking_result.json`, `sqlite_crash_recovery_result.json`,
`sqlite_write_practicality_result.json`, `allocation_reconciliation.json`,
`d130_archive_after.json`, and `qualification_result.json`, together with
`scratch_cleanup_result.json` and the manifest itself.

**The external scratch tree was deleted.** `/Volumes/SSK SSD/FDD_M3_3_D136_QUALIFICATION_SCRATCH` was
removed after sixteen deletion guards passed — absolute, non-empty, not a forbidden path, no glob
metacharacter, no `..`, depth `>= 3`, basename carries the D136 marker, real directory, not a
symlink, `realpath` resolves to itself, neither the D130 nor the D125 archive and not inside
either, the archive not inside it, and the parent is the volume root. **No sibling path was deleted.** Peak simultaneous scratch
residency stayed under the `4` GiB ceiling. Afterwards the scratch root was **absent**, the D130
archive **present with its `24` entries**, and the D125 archive **present**.

**One `131,072`-byte residue is recorded honestly rather than rounded away.** Net external free space
is `131,072` bytes lower than at session entry — one ExFAT allocation block that the root directory
grew to hold the scratch directory entry and does not release when the entry is removed. This is
normal ExFAT behaviour, not leaked data; **no D136 file remains on the volume.**

No large artifact was retained: neither the `2` GiB qualification file nor any scratch database, since
a successful qualification does not need them.

## 14. Limitations, stated rather than smoothed

1. **No power-loss evidence exists.** Process-crash recovery is proved; power-loss and
   surprise-removal safety are not, and ExFAT is not journaled (D136-R6).
2. **The `F_FULLFSYNC` result is ambiguous by construction.** A `0.9` ms return cannot distinguish a
   satisfied flush from an ignored one without power-cut testing.
3. **No drive-health telemetry.** SMART is Not Supported through this USB bridge.
4. **The volume is shared.** Unrelated user data lives beside the archives on the same filesystem.
5. **`SQLITE_TMPDIR` behaviour on ExFAT is unmeasured**, and the `128` KiB minimum allocation makes
   many-small-file workloads expensive.
6. **The bounded workload is synthetic** and licenses no runtime extrapolation.
7. **The mechanical qualification says nothing about semantics.** It qualifies a disk, not a dataset.

## 15. Owner rulings D136-R1 – D136-R12

| Ruling | Statement |
|---|---|
| **D136-R1** | **The D136 bounded mechanical qualification is ACCEPTED**, as recorded in §§4–8. The candidate is the exact volume `/Volumes/SSK SSD`, volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049`, ExFAT via Apple FSKit, a local physical USB SSD. |
| **D136-R2** | **External free capacity passes D135.** Post-cleanup free `310,498,557,952` B / `289.1743` GiB against the START floor `198,642,237,440` B / `185` GiB — surplus `111,856,320,512` B / `104.1743` GiB. **The D135 `185` GiB START floor remains controlling.** |
| **D136-R3** | **SQLite mechanics are ACCEPTED**: WAL effective; `synchronous = FULL` effective; the accepted D131 pragma values read back correctly; no double writer; expected lock exclusion; correct snapshot-reader behaviour; uncommitted transaction lost after an authenticated `SIGKILL`; committed WAL transaction survived an authenticated `SIGKILL`; `integrity_check == ok`; WAL `TRUNCATE` succeeds. |
| **D136-R4** | **I/O practicality is ACCEPTED**: fsync-complete sequential write `~250.4` MiB/s against the `50` MiB/s qualification floor, and a bounded SQLite result of `~794` MiB with no I/O errors, no stalls over `5` s, a bounded WAL, and clean integrity checks. **Do NOT extrapolate complete-source runtime from these measurements.** |
| **D136-R5** | **External allocation overhead does NOT require raising the D135 `185` GiB floor.** The ExFAT `128` KiB minimum allocation remains a known **minor** risk for many-small-file workloads and for unmeasured `SQLITE_TMPDIR` behaviour. |
| **D136-R6** | **D136 establishes PROCESS-CRASH recovery only.** It does **not** establish power-loss safety, surprise-removal safety, USB-bridge cache-flush correctness, or journaled-filesystem semantics. The `~0.9` ms `F_FULLFSYNC` return is **not** evidence that the bridge physically flushed volatile device cache. |
| **D136-R7** | **The D130 archive remained byte- and proof-stable throughout D136**, and is **uniquely retained** on this SSD. A future active database and that archive would therefore share filesystem, physical device, cable/bridge, and surprise-removal failure domain. |
| **D136-R8** | **D125-R4 remains the GENERAL rule.** A **narrow exception** is created: after successful D137 implementation and acceptance, **this exact volume** — UUID `397A4D4A-9508-391E-814E-3B533C7BD049` — may host **ONE** corrected M3.3 complete-source canary working world. It does **not** authorize arbitrary active governed SQLite use on this SSD, and permits **no** write inside `/Volumes/SSK SSD/FDD_M3_3_D130_D128_ARCHIVE`. The future working world must be a **separate sibling tree**, and **the D130 archive remains immutable**. |
| **D136-R9** | **The shared failure-domain risk is EXPLICITLY ACCEPTED for this one future corrected canary only**, on the five reasons in §10. **This does NOT convert ExFAT into a journaled filesystem and does NOT claim zero risk.** |
| **D136-R10** | **Any later canary authorization using this exception must require the twelve physical and run conditions in §10** — external power, stable connection, stationary hardware, no manual eject, no unrelated write-heavy SSD activity, no reformat/repartition, D130 precheck and postcheck, stable volume-UUID verification, `>= 185` GiB free at launch, a working root outside the archive, and sleep prevented via the governed launcher/runbook. **These are future run conditions only.** |
| **D136-R11** | **The next stage is Decision 137**, which must implement and validate the nine items in §11 — external working-root selection, a fail-closed **Volume-UUID** identity guard, refusal inside the archive tree, the `185` GiB launch floor, the `50` GiB PRE-F2 floor, replacement of the inadequate `30` GiB constant behaviour, D135-consistent capacity monitoring, operator/runbook power and no-sleep requirements, and targeted tests with independent validation. **D137 does NOT start the canary.** |
| **D136-R12** | **Other safety state is unchanged.** D129-R2 controlling; D129-R8 controlling (from scratch, new world, new run id); D131 runtime configuration unchanged; D134 mmap and relaxed-checkpoint candidates rejected; E0 unauthorized; network disabled; `census_orchestrator.py::_parse_bulk` a separate open PRE-NETWORK blocker. |

## 16. What this record does not do

- It does **not** adopt the external volume as the working root. **Qualification is not adoption.**
- It does **not** authorize a canary — corrected or otherwise — or any disposable world.
- It does **not** change path configuration or add external-root support. That is D137 work.
- It does **not** edit `PRE_F2_MINIMUM_FREE_BYTES`, and does not authorize editing it here.
- It does **not** change the `185` GiB or `50` GiB floors.
- It does **not** create or authorize migration `0016`.
- It does **not** authorize E0, network, SEC acquisition, or HTTP. Request ceiling remains `0`.
- It does **not** repair `census_orchestrator.py::_parse_bulk`.
- It does **not** certify any semantic count, and discharges neither D129-R2, D129-R8, nor D129-R12.
- It does **not** correct any repository figure, because none was wrong (§3).
- It does **not** claim power-loss safety, and it does **not** extrapolate any canary runtime.

## 17. The next authorized action

**An owner-prepared Decision 137 implementation packet — and nothing else.** No implementation
authority arises from this publication. The corrected complete-source canary remains unauthorized
until the D137 external working-root, identity-guard, and `50` GiB PRE-F2 implementation is
completed, independently reviewed, and owner accepted.

**Qualifying a volume is not adopting it, and adopting it is not authorizing the run.**
