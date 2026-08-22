# Decision 130 — The D128 External Archival and Verified Internal Reclamation

```text
STATUS: ACCEPTED — OWNER RULING, CLOSED
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF A COMPLETED ARCHIVAL AND RECLAMATION
  EXECUTION — A RETROSPECTIVE DURABLE RECORD, PUBLISHED AFTER THE WORK
DATE: 2026-08-22
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
EXECUTION_TOKEN: M3_3_D130_D128_ARCHIVE_RECLAIM_AUTHORIZED
STOP_ACCEPTANCE_TOKEN: M3_3_D130_STOP_NO_EXTERNAL_VOLUME_OWNER_ACCEPTED
OWNER_TOKEN: M3_3_D130_D128_ARCHIVE_RECLAIM_OWNER_ACCEPTED
OUTCOME: D128_EXTERNAL_ARCHIVAL_COMPLETE_AND_VERIFIED;
  D128_INTERNAL_RECLAMATION_COMPLETE
D128_SEMANTIC_DISPOSITION: D128_SEMANTIC_REPAIR_REQUIRED — UNCHANGED BY THIS RECORD
D128_WORLD_DISPOSITION: ARCHIVED EXTERNALLY, VERIFIED, AND DELETED INTERNALLY —
  COLD EVIDENCE ONLY, NOT RESUMABLE AND NOT REUSABLE AS A CORRECTED RUN WORLD
SCOPE: THE ARCHIVAL, THE VERIFICATION, THE DELETION, AND THE RECLAIMED CAPACITY —
  NOT A REPAIR, NOT A RERUN, NOT A CAPACITY MODEL, AND NOT AN EXECUTION AUTHORIZATION
PARSER_REPAIR_STATUS: NOT STARTED
PARSER_REPAIR_AUTHORIZATION: NO
CORRECTED_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
FURTHER_DELETION_AUTHORIZATION: NONE
```

The owner's governance publication of the completed D130 archival and reclamation of the
complete-first-source canary world `m3_3_d128_complete_first_source_v1`.

## 1. What this record is, and what it is not

**It is a retrospective durable record of work that had already finished.** The archival, the
read-back verification, the deletion, and the capacity measurement all completed before this file
existed. **This file did not authorize any of it**; the authorizing instrument was the owner's
`M3_3_D130_D128_ARCHIVE_RECLAIM_AUTHORIZED` instrument, issued outside this repository. What D130
publishes is **the result**.

**It is the durable internal index to an external archive** (§6, D130-R2). The archive lives on one
removable volume. Unlike [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md),
**no separate internal retention artifact was written for D130** — the manifests exist only on the
SSD. That makes this record, and not a file under `~/m3-retention/`, the thing that survives if the
volume does not. Every identity a future reader would need to recognise, locate, or challenge the
archive is reproduced in §6 for that reason.

**It changes nothing about D128's semantics.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
adjudicated D128 and its verdict `D128_SEMANTIC_REPAIR_REQUIRED` **stands entirely unmodified**.
D130 moved bytes and reclaimed disk. **It did not repair a defect, revisit a count, or certify
anything D129 rejected.**

**It is not a rerun and not a capacity model.** §9 publishes the reclaimed capacity and §10 rules
explicitly that **the resulting free space is not run readiness**. [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
§12 (D129-R12) continues to control, and it requires a *new* corrected-run reconciliation that this
record does not construct.

**It is not a repair.** No production source, test, schema, migration, configuration, or authority
constant changed in this publication or in the execution it records.

## 2. Entry state

The execution and this publication both entered at the same verified baseline:

| Item | Value |
|---|---|
| Branch | `main` |
| `HEAD` | `9b4c58226d1d77569cf8d4d0f0981ad6301f2963` |
| Tree | `b550962a42b50743e5df05343fcb94169aba946c` |
| `origin/main` | identical to `HEAD`, ahead/behind `0/0` |
| Worktree | clean |
| Latest decision | Decision 129 |
| Migration head | `0015`; `0016` absent and unapplied |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` |
| `network.enabled` | `false` |
| `network.m3_acquire_enabled` | `false` |

**The repository was not modified by the execution.** `HEAD` and tree are unchanged from entry
through the end of §8, and the reflog head remained the Decision 129 commit throughout.

## 3. The first attempt, and why it stopped — D130-R1

**The first D130 attempt stopped correctly, and stopping was the right outcome.** The instrument
required an external SSK volume; **no external device was attached to the machine at all**.
`diskutil list external physical` was empty, both Thunderbolt/USB4 ports reported `No device
connected`, `ioreg` enumerated no removable media, and `/Volumes/` held only the `Macintosh HD`
symlink.

**The stop is recorded as a correct execution of the instrument, not as a failure.** Nothing was
archived, nothing was staged internally, and **nothing was deleted**. The retained D128 set was
re-verified intact at 26 regular files after the stop. The owner accepted that outcome under
`M3_3_D130_STOP_NO_EXTERNAL_VOLUME_OWNER_ACCEPTED`.

**Internal staging was never an available substitute** and was not attempted: internal free space at
that moment was about `26.2 GiB` against a `96.826 GiB` source set, and the instrument authorized no
internal staging in any case.

**The successful run was a same-session resumption under the same execution token**, with every
§2 predicate re-derived live rather than inherited from the stopped attempt.

## 4. The D128 source artifact set

The exact pre-deletion facts, measured live and reconciled against the instrument's expected values:

| Item | Value |
|---|---|
| Run identity | `m3_3_d128_complete_first_source_v1` |
| World path | `~/m3-disposable-canaries/m3_3_d128_complete_first_source_v1` |
| Run log path | `~/m3-run-logs/m3_3_d128_complete_first_source_v1` |
| Sibling SQLite temp | `~/m3-disposable-canaries/m3_3_d128_complete_first_source_v1__sqlite_tmp` — present, **empty** |
| Regular files | `26` |
| Directories | `4` |
| Logical bytes | `103,966,642,558` = `96.826 GiB` |
| `canary_result.json` SHA-256 | `1eaa0b67b14bdf3d2431f460a8837e63c086666377161052c0d3bc8429948267` |
| `working_catalog.sqlite3` | `103,694,548,992` bytes |
| `working_catalog.sqlite3` SHA-256 | `69b457caf840b41e8f6c0f7d40ad3f88028ee9b1a8824657c484ed8fdbdd52f5` |
| `compact_evidence.sqlite3` | `271,335,424` bytes |
| `compact_evidence.sqlite3` SHA-256 | `4dcaae97ac874e0cfbbd3c483a387fa8d43dbff5757e14672897390f5dc85dcd` |
| `working_catalog.sqlite3-wal` | `0` bytes |
| Special file types | none — `0` symlinks, sockets, FIFOs, block or character devices |
| Extended attributes / ACLs | none |

**The working-catalog byte count matches the accepted [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
§11 figure exactly.** No canary process, watchdog, or SQLite writer existed, and no process held an
open handle inside any of the three paths, at preflight or at the post-archive recheck.

**D128's semantic disposition is unchanged: `D128_SEMANTIC_REPAIR_REQUIRED`.** The archived world is
**cold evidence only**. It is **not resumable** and **cannot serve as the corrected run world** —
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §14 (D129-R8) requires new code, a
new run identity, a new create-once world, and a full source rerun from the beginning, and archiving
D128 does not soften any of those four.

## 5. The external SSK volume

| Item | Value |
|---|---|
| Device node | `/dev/disk4s2`, on external physical `/dev/disk4` |
| Volume name | `SSK SSD` |
| Mount point | `/Volumes/SSK SSD` |
| Filesystem | ExFAT, USB, mounted read/write |
| Volume UUID | `397A4D4A-9508-391E-814E-3B533C7BD049` |
| Disk / partition UUID | `411E4166-1A78-4B2B-BB75-9AFB9239C42B` |
| Capacity | `499,955,924,992` bytes |
| Archive directory | `/Volumes/SSK SSD/FDD_M3_3_D130_D128_ARCHIVE` |

**Exactly one external volume was present, so the identity was unambiguous.** The destination
directory was confirmed **absent** before creation. The volume was not erased, repartitioned,
reformatted, repaired, or renamed.

**The prior [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) archive at
`/Volumes/SSK SSD/FDD_M3_D125_ARCHIVE` remained untouched** — its seven tars and its `RETENTION/`
directory were verified present and unmodified after D130 completed. [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md)
§7's ordering — verified external preservation first, authorized internal retirement only after it —
was the ordering D130 followed.

## 6. The durable internal archive index — D130-R2

**This section is the durable internal index to the external D128 archive.** No separate internal
retention artifact was created, so **loss or unavailability of the SSK volume must not erase what
was archived**. These identities are recorded here for that purpose.

| Artifact | Bytes | SHA-256 |
|---|---|---|
| `d128_complete_first_source_v1.pax.tar` | `103,966,696,960` | `b4f13e9277b4d6bc79462a2c44c599a48a8844173f18cefc829d255e42583013` |
| `d128_source_manifest.tsv` | `3,645` | `af5088e4ac1c387675d50ba933e187c20f95e0e4cb471bf157665f00e366fac4` |
| `d128_tar_member_manifest.tsv` | `3,645` | `af5088e4ac1c387675d50ba933e187c20f95e0e4cb471bf157665f00e366fac4` |
| `d128_archive_receipt.txt` | `6,343` | `63d8fc4b72e6d3f7e3996fa1b76133dcc15b44828fe3890dc6f8052ea6f46b94` |
| `d130_post_deletion_proof.txt` | `4,251` | `8387e9eb9994c3aae4e5e7b023bba0d587df46e3bbb80d06e220030c395d507d` |

A third manifest, `d128_source_manifest_recheck.tsv`, is the §7 post-archive re-hash; it is
byte-identical to the other two and carries the same `af5088e4…fac4` digest.

**The two manifest digests being equal is the point, not a coincidence.** `d128_source_manifest.tsv`
was built from the internal source before archival; `d128_tar_member_manifest.tsv` was built by
streaming members back out of the finished tar. **They are byte-identical files**, which is a
stronger result than the normalized tuple-set equality the instrument permitted as a fallback.

**Archive format is uncompressed PAX/TAR**, written relative to the home directory and containing
exactly the three D128 paths. Compression was deliberately not used, so that a future reader can
verify any single member byte-for-byte without a decompression stage. The `54,402`-byte difference
between the archive and the source logical total is PAX header, padding, and end-of-archive blocks;
the archive length is `512`-aligned.

## 7. The verification record — D130-R3

**Successful tar creation was not treated as verification.** The archive was independently read
**back from the external device**, with `F_NOCACHE` set on the descriptor so the unified buffer
cache could not mask a bad read — the same discipline [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md)
established.

| Predicate | Result |
|---|---|
| Archive structurally readable, streamed to EOF | yes |
| Member namespace | exactly the three intended D128 paths |
| Absolute or path-traversal member names | `0` |
| Verified regular members | `26` of `26` expected |
| Directory members | `4` |
| Byte-length mismatches | `0` |
| SHA-256 mismatches | `0` |
| Missing members | `0` |
| Unexpected members | `0` |
| Source and tar-member manifests | **byte-identical** |
| Post-archive source recheck against the original manifest | **byte-identical** |

**The post-archive source recheck is what proves the source did not change during the multi-hour
archival**, and it re-established the process, handle, WAL, and `canary_result.json` predicates as
well as the per-file digests.

**The archive was read in full four separate times**, three of them with `F_NOCACHE`: once for the
post-creation digest, once during member-by-member verification, once after deletion, and once again
during this publication. **Every read returned `b4f13e9277b4d6bc79462a2c44c599a48a8844173f18cefc829d255e42583013`.**

**The final full re-read of all `103,966,696,960` bytes occurred *after* the internal source had
been deleted**, and returned that identical digest. That ordering matters: it is the evidence that
the only surviving copy is intact, taken at the moment the only surviving copy is all there is.

## 8. The internal deletion — D130-R4

**Deletion occurred only after every archive, read-back, and source-recheck predicate in §7 had
passed.** Exactly three paths were removed:

- `~/m3-disposable-canaries/m3_3_d128_complete_first_source_v1`
- `~/m3-run-logs/m3_3_d128_complete_first_source_v1`
- `~/m3-disposable-canaries/m3_3_d128_complete_first_source_v1__sqlite_tmp`

**All three are absent after deletion**, confirmed both immediately and after the filesystem settled.

**Explicit path guards and a full dry run preceded the deletion.** Each path was proved, before any
`rm` ran, to be: non-empty; none of the forbidden set — `/`, `/Users`, the home directory itself,
either of the two parent directories, `/Volumes`, `/Volumes/SSK SSD`, `.`, and `..`; absolute, at
depth at least four; free of glob metacharacters and of `..`; carrying the D128 run identity in its
basename; a real directory and not a symbolic link; resolving through `realpath` to itself, so no
symbolic aliasing anywhere in the path could redirect the removal; and free of open handles. Glob
expansion was disabled for the whole deletion script. **The dry run reported every guard passing
before execute mode was entered.**

**No generic cleanup occurred**, and none was authorized. Nothing outside those three literal paths
was removed.

## 9. Capacity result — D130-R5

| Measurement | Bytes | GiB |
|---|---|---|
| Internal free before the successful D130 | `26,964,860,928` | `25.113` |
| Internal free after | `130,960,166,912` | `121.966` |
| **Reclaimed** | **`103,995,305,984`** | **`96.853`** |
| External free before | `414,468,145,152` | `386.004` |
| External free after | `310,498,689,024` | `289.174` |

**Reclaimed allocated space need not equal logical archived bytes, and here it exceeds them** by
`28,663,426` bytes. This is expected and is not evidence that something extra was deleted: APFS
allocated-block usage differs from logical file size, and the working catalog alone was allocated
`103,707,029,504` bytes against a logical `103,694,548,992`. No APFS snapshot existed on the data
volume to withhold reclaimed space. **The instrument did not require these two figures to match, and
they should not be expected to.**

## 10. The capacity ruling — `121.966 GiB` is not run readiness — D130-R6

**The `121.966 GiB` of internal free space does NOT authorize another complete canary.** It exceeds
[Decision 124](decision_124_m3_3_capacity_reconciliation.md)'s historical `>= 105 GiB` start
threshold, and that fact is **not** an authorization.

**[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12) controls: a new
corrected-run capacity reconciliation is required before another complete-source execution
authorization.** Four reasons, each sufficient on its own:

1. **Corrected shard dispatch will add millions of previously omitted accessions** — `3,037,614`
   accessions are genuinely absent from D128, and a corrected run must store what D128 never stored.
2. **D128's actual working catalog was already `96.57 GiB`**, which is a **floor** for the corrected
   run rather than an estimate of it.
3. **The real D128 pre-F2 admission margin was only about `2 GiB`**, not the comfortable figure the
   earlier summary implied.
4. **[Decision 124](decision_124_m3_3_capacity_reconciliation.md) materially underpredicted F1/F2
   runtime and storage behaviour** — the measured F1+F2 underprediction is about `1.8x`–`1.9x`.

**Do not reinterpret `121.966 GiB` as run readiness.** A free-space number is an input to a capacity
model, never a substitute for one, and D130 constructs no model.

**No [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5) gate is retired or
relaxed by this record** — the `>= 105 GiB` start gate, the continuous `10 GiB` floor, the
`>= 30 GiB` pre-F2 admission gate, no `VACUUM`, and explicit `SQLITE_TMPDIR` placement all stand
exactly as written.

## 11. Retained and unchanged

**Retained and confirmed present after deletion:**

- `~/m3-disposable-canaries/m3_3_perf_c3_local_40k_v1` — C3 retained evidence
- `~/m3-d117-diagnostics`
- `~/m3-retention` — the [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md)
  retention record
- `~/m3-private-evidence` — raw SEC source and the operational catalog
- `/Volumes/SSK SSD/FDD_M3_D125_ARCHIVE` — the prior external archives

**The now-empty `~/m3-run-logs` directory is harmless and remains.** Only the D128 subdirectory was
removed; the parent was not, and removing it was not authorized.

**The idle `tmux` session named `d128` is not part of D128 evidence and was not touched during
D130.** It holds no handle inside any D128 path, and it was verified as holding none before
archival. It may be disposed of later under ordinary operator housekeeping before another run.
**No action follows from this publication.**

**Nothing else changed.** No parser change, no watchdog change, no test change, no canary, no E0, no
migration `0016`, no network, no operational-catalog write, and no frozen-source write.

## 12. The next sequence — D131 — D130-R7

**The next stage is D131, a semantic and operational repair.** It requires its own owner instrument;
nothing here authorizes it. D131 must address, **separately and explicitly**:

| | Item |
|---|---|
| **A** | Correct bulk historical-shard dispatch |
| **B** | Per-reference explicit parent registrant binding |
| **C** | Recognized optional fields — `lei`, `filings.recent.core_type`, `filings.recent.isXBRLNumeric` |
| **D** | Repair and **prove** actual `SIGINT` delivery for watchdog stop actions |
| **E** | Correct post-traversal stall monitoring |

The controlling sequence after D131, each step requiring its own owner instrument:

1. **D131 semantic/operational repair** (A–E above).
2. **Bounded real semantic validation.**
3. **Bounded performance A/B optimization.**
4. **Corrected-run capacity reconciliation** (D129-R12).
5. **Only then**, an owner decision on a corrected complete-source canary.

**E0 remains unauthorized throughout.** No step in this sequence carries E0 authority, and reaching
step 5 is not reaching E0.

## 13. Owner rulings D130-R1 – D130-R7

| Ruling | Content |
|---|---|
| **D130-R1** | **The first D130 attempt stopped correctly because the external SSD was absent.** Nothing was archived, nothing was staged, nothing was deleted, and the D128 set was re-verified intact. Owner-accepted under `M3_3_D130_STOP_NO_EXTERNAL_VOLUME_OWNER_ACCEPTED`; the successful execution was a same-session resumption with every predicate re-derived live (§3). |
| **D130-R2** | **Decision 130 is the durable internal index to the external D128 archive.** No separate internal retention artifact exists for D130, so §6 carries every identity needed to recognise, locate, or challenge the archive if the volume is unavailable. **Do not create another standalone internal retention artifact** unless repository convention requires one (§6). |
| **D130-R3** | **The archival is COMPLETE and VERIFIED.** Read back from the external device with `F_NOCACHE`: `26` of `26` regular members verified, `0` byte mismatches, `0` SHA mismatches, `0` missing, `0` unexpected; source and tar-member manifests **byte-identical**; post-archive source recheck **byte-identical**; and a final full `103,966,696,960`-byte re-read **after deletion** returning the identical archive digest (§7). |
| **D130-R4** | **Internal reclamation is COMPLETE, and deletion followed verification rather than preceding it.** Exactly three literal paths were removed, under explicit guards and a passing dry run, with glob expansion disabled. All three are absent. **No generic cleanup occurred and none is authorized** (§8). |
| **D130-R5** | **`103,995,305,984` bytes = `96.853 GiB` were reclaimed**, taking internal free from `25.113 GiB` to `121.966 GiB`. Reclaimed allocated space **need not equal** logical archived bytes; APFS allocation accounts for the difference (§9). |
| **D130-R6** | **`121.966 GiB` of free space does NOT authorize another complete canary.** It clears D124's historical `>= 105 GiB` threshold and that is not an authorization. **D129-R12 controls** and requires a new corrected-run capacity reconciliation first. **No D124-R5 gate is relaxed** (§10). |
| **D130-R7** | **The next stage is D131** — correct bulk shard dispatch, per-reference parent registrant binding, the three recognized optional fields, proven `SIGINT` delivery, and corrected post-traversal stall monitoring — **then** bounded semantic validation, **then** bounded performance A/B, **then** corrected-run capacity reconciliation, **then** an owner decision on a corrected canary. **E0 remains unauthorized throughout** (§12). |

## 14. What this record does not do

- **It does not repair a parser defect.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
  §5 and §6 remain open, and D131 is where they are addressed.
- **It does not certify any D128 count.** D129-R2's rejection stands entirely.
- **It does not authorize a rerun, a canary, a disposable world, E0, migration `0016`, network
  access, or any catalog write.**
- **It does not construct a capacity model**, and §9's figures may not be used as one.
- **It does not supersede any record.** Decisions 121 through 129 stand as written, and every
  D124-R5 gate carries forward intact.
- **It does not authorize any further deletion.** [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md)
  §7's rule that no further Disclosure Drift evidence may be deleted for capacity (D125-R3) stands,
  as does D125-R4 — **the SSK SSD remains cold archival storage only, and is never an active SQLite
  location.**
