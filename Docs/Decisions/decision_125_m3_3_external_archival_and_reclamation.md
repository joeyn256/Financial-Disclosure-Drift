# Decision 125 — External Evidence Archival, and Verified Internal Storage Reclamation

```text
STATUS: ACCEPTED — OWNER RULING, CLOSED
RECORD_TYPE: OWNER ACCEPTANCE OF A COMPLETED ARCHIVAL AND VERIFIED RECLAMATION —
  A RETROSPECTIVE DURABLE RECORD, PUBLISHED AFTER THE OPERATION
DATE: 2026-08-20
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OUTCOME: M3_3_D125_EXTERNAL_ARCHIVAL_AND_RECLAMATION_OWNER_ACCEPTED
SCOPE: EXTERNAL ARCHIVAL, EXTERNAL VERIFICATION, AND THE AUTHORIZED INTERNAL RETIREMENT
  THAT FOLLOWED IT — NOT A CAPACITY MODEL AND NOT AN EXECUTION AUTHORIZATION
DISCHARGES: the Decision 124 section 11 archival obligation (D124-R7, D124-R8, D124-R9)
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_V3_EXECUTION_AUTHORIZATION: NO
F1_EXECUTION_AUTHORIZATION: NO
F2_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
FURTHER_DELETION_AUTHORIZATION: NONE
EXTERNAL_VOLUME_ACTIVE_SQLITE_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The archival plus verified internal reclamation that
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §11 required and named as the D125
obligation, and that its §14 (D124-R10) made a precondition of any later complete-source
authorization.

## 1. What this record is, and what it is not

**It is a retrospective durable record of a completed operation.** The archival, the external
verification, and the authorized internal retirement had all already run when this file was
written. **This file did not exist before the operation and did not authorize it.** The authorizing
instrument was the GPT-5.6 Sol owner instrument issued at execution time; this record is the
durable governance publication of what that instrument authorized and what the operation produced.
Nothing here may be read as a pre-authorization, and no part of this publication executed,
archived, copied, moved, or deleted anything.

**It discharges the Decision 124 §11 obligation.** D124-R7 made the preserved worlds eligible under
a later instrument, D124-R8 required a fresh SHA-256 of the D122 post-F1 working catalog with a
stop-on-mismatch comparison recorded **before** any deletion, and D124-R9 required an explicit
cryptographic and metadata manifest because exFAT does not preserve all relevant POSIX metadata.
All three were satisfied before anything was removed. §3 records the identity, §4 and §5 the
archive and its verification, §6 the retention records, and §7 the retirement that followed.

**It is not an execution authorization of any kind.** No complete source, no E0, no F1, no F2, no
canary, no migration `0016`, no network, no acquisition. **It is also not a further deletion
authority** — §7's retirement is spent, and D125-R3 forbids deleting any additional Disclosure
Drift storage to satisfy a capacity gate.

**It is not a capacity model.** The Decision 124 §8 model is unchanged. §9 below reports one
*measured* outcome — internal free space after reclamation — against that model's D124-R5 gate.

## 2. Entry state

Branch `main` at published `11ca0f9695b64bdd7b383fd8b58009d901b04768`, tree
`3791de11020e39dc28763b1a6e2f8ed0474077f8`, `origin/main` identical at `0`/`0` and the worktree
clean, with governance published through Decision 124. Migration head `0015`; migration `0016`
absent; no E0-v3 namespace; all three activation constants — `M3_3_E0_EXECUTION_AUTHORITY`,
`PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — `None` in
`src/disclosure_drift/m3/e0.py`; both tracked network switches `false` in `configs/project.yaml` at
request ceiling `0`.

Every one of those predicates was verified at publication and still holds. **This record changes
none of them.**

## 3. The accepted D122 identity

**D125-R2 establishes the D122 post-F1 working catalog identity as durable and accepted:**

```text
fa4a635d36a487774e02670bb0fab1ded1c696b5e25faf54fb6f55b69799f413
```

[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §11 (D124-R8) was explicit that this
value was **a candidate and not yet accepted durable identity** — it came from the D123 completion
report, and a completion report is not repository authority. The obligation was to hash the actual
preserved catalog, compare, **stop on mismatch**, and record the result before deletion.

**Four independent reads converged on that value:**

1. a **fresh internal D125 hash** of the actual preserved catalog matched;
2. the **historical D123 candidate** matched;
3. the **external archive member was streamed back off the external device and rehashed** to the
   same value;
4. **multiple independent reads converged** across those paths.

**The value is therefore no longer a candidate.** It is the accepted durable identity of the D122
post-F1 working catalog, and the internal copy could be retired against it. The stop-on-mismatch
condition never fired, because there was no mismatch.

## 4. The external archive

**Volume.** `SSK SSD`, mounted at `/Volumes/SSK SSD`, filesystem **exFAT**, nominal `500 GB` — the
volume [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §10 (D124-R6) approved **in
principle as archival / cold-preservation storage only**.

**Destination.** `/Volumes/SSK SSD/FDD_M3_D125_ARCHIVE/`

**Format.** Uncompressed **PAX/TAR**. The container is metadata-preserving by construction, which is
half of the D124-R9 answer to exFAT's metadata limitations; §6 carries the other half.

**The seven archive identities:**

| Archive member | Bytes | SHA-256 |
|---|---:|---|
| `d117_world.tar` | `27,629,187,072` | `ba5097226cf7ac89ccf54fc93c4136e7f2b35aec9b714cfb9e4ae065d05a8974` |
| `d120_world.tar` | `19,955,783,680` | `cf7b09cffcc71248f4e2ae010c5772a3a3f81bd0d2bb82a54c22d403faaa5df9` |
| `d122_f1_world.tar` | `23,530,204,160` | `60e58265996eb8c97454077b6076aac4ba6a8490b84bf2c2fb1686ae9b924ffe` |
| `d123_characterization.tar` | `4,034,596,352` | `007247db2726feb06ee95322770b84f6c279da8838004b85dcdd32612bda411c` |
| `m3_perf_experiments.tar` | `84,995,072` | `1b70e21a580f13eb165b1c767a26a943081d0aa713a07fa2c16383942dc56709` |
| `c3_retained_evidence.tar` | `11,043,328` | `12711dc9c86f19f7dd515b59addc89c4285438fa60afc736bfefe26f8d7dda9a` |
| `d117_diagnostics.tar` | `277,504` | `6de81d43d8454a6d61404cb43a54702233e974ecbac0aab1e5f432d4ac5943ad` |

**Total external TAR bytes: `75,246,087,168`** — about **`70.0784 GiB`**. The seven member sizes sum
to exactly that total.

## 5. Verification

**Verification was performed by streaming the actual TAR contents back from the external device.**
It is a read-back of what the external volume holds, not a re-statement of what the writer believed
it had written — which is the distinction that makes the §7 retirement safe.

| Check | Result |
|---|---|
| Archive members matched | **`2,777` / `2,777`** |
| Regular-file SHA-256 values matched | **`2,470` / `2,470`** |
| Missing | **`0`** |
| Unexpected | **`0`** |
| Duplicate | **`0`** |
| Metadata comparisons | **all passed** |

The two counts differ because an archive member is not always a regular file: directories, symbolic
links, and other member types are verified for presence and metadata but carry no content hash.

## 6. Retention records

**Permanent internal retention root:** `~/m3-retention/d125/`

**Primary final manifest:** `d125_manifest_final.json`, SHA-256

```text
1366a5dd484e8d0e57c3b7ae6e401f3420c21be8685494c7d28199da3e5c3a9c
```

**The external RETENTION copy was verified byte-identical to the internal record**, so the manifest
survives the loss of either side.

**How the D124-R9 exFAT metadata limitation is addressed.** exFAT does not preserve all relevant
POSIX metadata, so the archive does not rely on the filesystem to carry it. Four mechanisms carry it
instead:

- **PAX archive metadata**, in the container itself;
- **explicit manifests**, independent of the container;
- **per-file hashes**;
- **recorded `mode`, `uid`/`gid`, `owner`/`group`, `path`, `type`, `size`, `mtime`, and symlink
  metadata**.

That set covers the D124 §11 minimum field list. The manifest is the authority for metadata that
exFAT itself cannot hold.

## 7. Authorized internal retirement

**After all verification gates in §5 passed — and only after — exactly these five internal roots
were removed:**

```text
~/m3-disposable-canaries/m3_3_d117_first_source_disposable_v1
~/m3-disposable-canaries/m3_3_d120_cache_120k_prefix_v1
~/m3-disposable-canaries/m3_3_d122_d120_f1_finalization_v1
~/m3-disposable-canaries/m3_3_d123_f2_characterization_v1
~/m3-perf-experiments
```

**The ordering is the governance point, not an implementation detail.** D124-R7 permitted removal
**only after external verification**, and that is the order in which it happened: hash, archive,
stream back, verify `2,777`/`2,777` members and `2,470`/`2,470` content hashes, record the identity
and the manifests, and only then retire. **The corresponding verified external archives now stand as
the preserved evidence** for all five roots.

**Nothing else was removed.** The five roots above are the complete deletion set, and no further
Disclosure Drift deletion is authorized (D125-R3).

## 8. Internal preservation

**Still internal and protected:**

```text
~/m3-private-evidence
~/m3-disposable-canaries/m3_3_perf_c3_local_40k_v1
~/m3-d117-diagnostics
~/m3-retention/d125
```

— together with **the repository**, **the current raw SEC source**, and **the operational catalog**.

This satisfies the [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §11 requirement that
C3's retained evidence and the tiny diagnostics stay internal. The raw SEC source is append-only
under the standing repository rule and was never in scope for archival or deletion.

## 9. The measured capacity result

**Measured internal reclamation:**

| Quantity | Value |
|---|---:|
| Reclaimed | `66,289,078,272` bytes — **`61.7365 GiB`** |
| Decision 124 §12 prediction | about **`61.77 GiB`** |
| Model error | about **`0.03 GiB`** |

**The Decision 124 clone-aware reclaim model is confirmed to approximately `0.03 GiB`.** That is the
one genuinely predictive result in this record: a clone-aware estimate over APFS copy-on-write
extents, made before the deletion, landed within about `0.03 GiB` of the measured free-block change.

**Settled internal free after D125: `104,500,830,208` bytes — `97.3240 GiB`.**

| Quantity | Bytes | GiB |
|---|---:|---:|
| Settled internal free after D125 | `104,500,830,208` | `97.3240` |
| Controlling D124-R5 starting gate | `112,742,891,520` | `105` |
| **Remaining hard gap** | **`8,242,061,312`** | **`7.6760`** |

**The gate is not met.** D124-R5's `>= 105 GiB` starting gate stands unchanged and unrelaxed, and
`97.3240 GiB` is below it by about `7.68 GiB` (D125-R5).

**A measurement condition is stated rather than smoothed.** Free space on a live APFS volume drifts
continuously. The settled figure above is the controlling one. The D125 retention artifact recorded
`104,503,115,776` bytes (`97.3261 GiB`) at its own moment, and a re-read at publication time
returned `104,485,810,176` bytes (`97.3100 GiB`) — a spread of about `17 MB`, about `0.016%`, across
three readings of an active filesystem. **All three fall short of the `105 GiB` gate by about the
same `7.68 GiB`, so the conclusion is identical under any of them**, and the gap figure is quoted
against the settled value.

**The `110 GiB` figure is a preference, not a predicate.** D125-R6 states an owner *staging
preference* of approximately `110 GiB` free **if ordinary non-project cleanup makes that easy**,
which would need about `12.7 GiB` more than the settled baseline. **`110 GiB` is not the formal
gate and must never be described as one. The formal admission predicate remains `>= 105 GiB`**, and
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 already said the same thing of the
same figure.

## 10. Residue, and what the safety preflight must check

**Two historical consumed E0 namespaces remain under the private evidence root:**

```text
m3_3_e0_offline_parse_v1
m3_3_e0_offline_parse_v2
```

**A stale `catalog_writer.lease` file is also present.**

**D125 did not modify any of these.** They were not archived, not deleted, and not touched.

**Their mere existence is not a new E0 namespace and must never be characterized as one**
(D125-R8). They are historical residue of consumed generations — v1 interrupted, v2 consumed — and
**no E0-v3 authority exists**. A consumed namespace is spent, not available.

**They must be explicitly checked during the final pre-complete-source safety preflight.** That is
the operational consequence of leaving them in place: the preflight has to account for them rather
than discover them.

**Two idle historical `tmux` servers were also observed and held no project handles.** No action is
required, and none was taken in this publication.

## 11. Owner rulings D125-R1 – D125-R8

| Ruling | Content |
|---|---|
| **D125-R1** | **The D125 external archival and verified internal reclamation is ACCEPTED**, as recorded in §§4–7. |
| **D125-R2** | **The D122 post-F1 working catalog SHA-256 `fa4a635d36a487774e02670bb0fab1ded1c696b5e25faf54fb6f55b69799f413` is ACCEPTED as durable identity**, on the four converging reads in §3. It is no longer a candidate, and the [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §11 (D124-R8) obligation is discharged. |
| **D125-R3** | **No additional Disclosure Drift storage may be deleted merely to satisfy the capacity gate.** The §7 retirement is spent. |
| **D125-R4** | **The external `SSK SSD` remains cold / archive storage only. No active governed SQLite use. No reformat.** This carries [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §10 (D124-R6) forward unchanged. |
| **D125-R5** | **The current settled internal free of `97.324 GiB` does NOT meet the `105 GiB` gate.** |
| **D125-R6** | **Prefer staging approximately `110 GiB` if ordinary non-project cleanup makes that easy.** The **formal admission predicate remains `>= 105 GiB`**; `110 GiB` is a preference and **not** a second gate. |
| **D125-R7** | **Crossing the disk threshold does NOT itself authorize complete-source execution.** A final live preflight is still required, and every other predicate must pass. |
| **D125-R8** | **The historical E0-v1 and E0-v2 namespaces remain historical residue. No E0-v3 authority exists**, and their existence is not a new namespace. |

## 12. Carried forward, not discharged

**One [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §4 obligation is explicitly not
discharged here.** D124 §4 recorded that the identifier `c85744be921b0dc5` appears in no tracked
record before Decision 124, while
[Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md)
§3 names the older object, and it named reconciling that **stored-object naming** as a D125
obligation.

**The D125 owner instrument is scoped to archival and reclamation and does not address it.** It is
therefore **recorded as outstanding rather than silently treated as closed**: the naming
reconciliation carries forward to a later instrument. Nothing in this record resolves it, and no
reader may cite D125 as having closed it.

The [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §7 term-label condition — D122 §5
labels `638,071` **cohort-resolution rows** while D124 reads it as explicit-resolution accessions —
likewise stands as recorded there, untouched by this record.

## 13. What this record does not do

**It authorizes no execution.** No complete-source run, no E0-v3, no F1, no F2, no full-population
F2 rerun, no D117 retry, no three-source canary, no real replay proof, no canary of any kind, no
migration `0016`, no network, and no acquisition. **Crossing the disk threshold is not an
authorization** (D125-R7) — a final live preflight is required, and the §10 residue must be checked
in it.

**It authorizes no further archival, copy, or deletion.** The §7 retirement was authorized by the
owner instrument at execution time, it is **spent**, and **D125-R3 forbids deleting any further
Disclosure Drift storage to close a capacity gap**. The §8 preserved material stays preserved.

**It changes no code and no schema.** No source, test, migration, configuration, or capacity
constant changed; `src/disclosure_drift/m3/capacity_plan.py` is untouched; no database was opened;
and no governed SQLite writer was opened. The [Decision 124](decision_124_m3_3_capacity_reconciliation.md)
§8 capacity model is unchanged — §9 measures one outcome against it rather than revising it.

**It supersedes nothing.** Decisions 121, 122, 123, and 124 stand as written. D125 *discharges* the
Decision 124 §11 archival obligation and *accepts* the §3 identity; neither is a supersession, and
the D124-R5 gates are carried forward intact.

**All three activation constants remain `None`**, the operational catalog remains at migration head
`0015`, migration `0016` remains absent, no E0-v3 namespace exists, and both tracked network
switches remain `false` at request ceiling `0`.

**The next action is ordinary non-project storage top-up chosen by the user**, followed by a **final
live M3.3 complete-source preflight**. Neither is executed here, and neither is authorized by
anything written here. **Complete source is NOT authorized. E0 is NOT authorized.**
