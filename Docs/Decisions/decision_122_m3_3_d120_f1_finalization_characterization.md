# Decision 122 — Retention Reclamation, and the Real F1-Only Finalization Characterization

```text
STATUS: ACCEPTED — OWNER FINDING, CLOSED
RECORD_TYPE: RETROSPECTIVE PUBLICATION OF ALREADY-ACCEPTED OWNER FINDINGS
DATE: 2026-08-20 (record published); the execution and its owner acceptance preceded it
OWNER: Joey authorization; Sol/GPT-5.6 owner findings
OUTCOME: M3_3_D122_D120_F1_FINALIZATION_OWNER_ACCEPTED
SUPERSEDES: nothing
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
F2_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The bounded finalization measurement
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §4 (R23) required and
[Decision 121](decision_121_m3_3_finalization_feasibility_preflight.md) §7 made the highest-priority
unknown — run for **F1 only**, over an APFS clone of the preserved D120 world, plus the storage
reclamation that made room for it.

## 1. What this record is, and what it is not

**It is a retrospective publication.** This record did **not** exist when the work it describes was
authorized and executed. The authority at the time was the **GPT-5.6 Sol owner instrument**, not
this file and not the repository. No timestamp is rewritten, no earlier record is amended, and this
record does not claim the repository authorized the execution in advance.

**Provenance, stated rather than implied.** Every measured value and every hash below is quoted from
the owner instrument that accepted the D122 work. The session that wrote this record did not re-run
the pass, did not open any world, and did not recompute any digest. Where a value is arithmetic over
two accepted values, it says so.

**No ruling numbers were issued for this record**, and none is invented here.

## 2. Entry state

Migration head `0015`; migration `0016` absent; no E0-v3 namespace; all three activation constants
`None`; both tracked network switches `false` at request ceiling `0`.
[Decision 120](decision_120_m3_3_real_120k_cache_profile_prefix.md) was the accepted real
120,000-member prefix measurement, its world preserved and immutable; Decision 121 was the accepted
read-only feasibility preflight, carrying the **F1/F2 split** (§4) and the copy-on-write budgeting
rule (§6); and the non-governed C3 experiment (Decision 121 §3) had been accepted and closed as
immaterial.

## 3. The retention identities, and the one authorized deletion

Before anything was deleted, **SHA-256 identities were captured** for all three working catalogs, so
that a reclaimed artifact is still identifiable and a retained one is still verifiable.

| Working catalog | SHA-256 | Disposition |
|---|---|---|
| D117 | `1d124577a96d3bf58fa736cb5a45460ce9e00eb0301df187158900efbe5302f2` | **retained**, immutable |
| D120 | `8356a2cc1dded403d816201641a2457a91059b7127d9e8010944b7459d9bb888` | **retained**, immutable |
| C3 | `de0fc98b782584c075397535e7bc3e0cf36867df57e99ea3a0acf38dbaaf8ea6` | **deleted** after capture |

**Exactly one deletion was authorized, and exactly one occurred: the C3 working catalog.** Its
compact evidence, result, and progress artifacts were **retained** — the deletion reclaimed the bulk
database and nothing else. That is what makes it a reclamation rather than a loss: the C3 findings
Decision 121 §3 records, including the byte-identical sidecar evidence, survive their database.

**No D117 or D120 deletion was authorized, and none occurred.** Both worlds remain preserved and
immutable, and their identities above are the record of what "unchanged" means for each.

## 4. The F1 diagnostic world

The D120 world was **APFS copy-on-write cloned** into a separate diagnostic world,
**`m3_3_d122_d120_f1_finalization_v1`**, and every write landed in the clone. The original D120
world was the clone's source and nothing else: it was not opened for writing, resumed, promoted,
vacuumed, reindexed, or deleted.

Cloning is what made the measurement possible at all — it is the mechanism Decision 121 §6 confirmed
available on this host, used for the purpose that record anticipated.

## 5. What the F1 pass measured

**Exactly one F1 resolution pass** was executed over the clone.

| Term | Accepted value |
|---|---|
| accessions | `8,258,521` |
| elapsed | `1,842.195 s` = **`0.5117 h`** |
| peak resident set | **`0.666 GiB`** |
| field-resolution rows | `5,104,568` |
| cohort-resolution rows | `638,071` |
| database growth | `3.360 GiB` |
| write-ahead-log peak | **`1.12 MiB`** |
| final write-ahead log | `0` |
| disk consumed | about **`13.60 GiB`**, including APFS copy-on-write divergence |

The accession count is exactly the durable canonical accession count
[Decision 120](decision_120_m3_3_real_120k_cache_profile_prefix.md) §4 records, which is the
expected relationship: F1 resolves what the prefix made durable. Dividing the two accepted values
gives about `4,483` accessions per second; that figure is arithmetic over the table above and not an
independently measured rate.

**What did not run.** **No F2.** No association projection, no §9.5 totality check, and **no
completion artifact** — nothing in the clone claims a completed source, and nothing may be read as
though it does.

**Copy-on-write divergence is confirmed as a real cost, not a theoretical one.** `3.360 GiB` of
database growth consumed about `13.60 GiB` of disk. That is the Decision 121 §6 ruling — budget a
clone at potentially full divergence — measured rather than predicted, and it is the reason that
ruling stands rather than being relaxed.

## 6. The accepted interpretation

**F1 is characterized for the first-source-canary path**, and for that path only. Decision 121 §5's
limit carries: this says nothing about full 76-source E0 finalization.

**Memory and the write-ahead log are bounded.** A `0.666 GiB` peak resident set and a `1.12 MiB`
write-ahead-log peak, finishing at `0`, over `8,258,521` accessions. Against the
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §2 `>= 169.61 GiB` write-ahead-log
lower bound from D117, the F1 log is not in the same regime — which is the batched, checkpointed
shape Decision 121 §4 identified, behaving as that shape predicts.

**No resume cursor exists.** F1 completed here; it is not restartable from part-way. An interrupted
F1 loses at most its open batch, per Decision 121 §4, but there is no mechanism that resumes one.

**The good F1 behaviour is not attributed to C1.** No cache A/B was run. The `512 MiB` budget was
present, and nothing in this measurement isolates its contribution — attributing bounded F1 memory
or a small write-ahead log to the cache correction would be a claim the evidence does not support.
Decision 120 §6 already records what C1 is accepted to have done, and it is not this.

**F2 remains unmeasured, and it is next.** It is the single-transaction shape Decision 121 §4
describes, whose cost and write-ahead-log high-water mark no measurement has yet touched.

## 7. What is preserved, and what F2 would run against

The **D122 F1 working catalog is preserved**, and it is the input a later F2 characterization would
take: F2 must run against a catalog that has already been through F1, which is what this world now
is.

Preserving it is a statement about the input, **not** an authorization to consume it. Executing F2
requires its own owner instrument, and this record is not one.

## 8. What this record does not do

It authorizes no F2 execution, no complete-source canary, no D117 retry, no three-source canary, no
real replay proof, no E0-v3, no migration `0016`, no network, and no acquisition. It authorizes no
further deletion of any kind — the single C3 working-catalog deletion §3 records is spent, and the
D117, D120, and D122 F1 worlds are all preserved. It supersedes nothing, changes no evidence
contract, no digest, no capacity constant, and no schema, and it reopens no deferral. All three
activation constants remain `None`, the operational catalog remains at migration head `0015`, and no
E0-v3 namespace exists.
