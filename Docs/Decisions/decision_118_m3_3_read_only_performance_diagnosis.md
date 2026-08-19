# Decision 118 — The Read-Only Performance Diagnosis of the D117 Throughput Failure

```text
STATUS: ACCEPTED — OWNER DIAGNOSIS
DATE: 2026-08-19
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings R21–R26
OUTCOME: M3_3_D118_READ_ONLY_PERFORMANCE_DIAGNOSIS_OWNER_ACCEPTED
SUPERSEDES: Decision 113's performance extrapolation, as a predictive assumption only
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

Why the [Decision 117](decision_117_m3_3_first_source_canary_throughput_failure.md) canary was
slow, established by **read-only** diagnosis over the preserved D117 world and accepted by the
project owner as rulings **R21–R26**.

**Provenance, stated rather than implied.** Every measured value below is quoted from the owner
instrument that accepted the diagnosis. The session that wrote this record did not re-run the
canary, did not open the preserved D117 world, and re-derived none of these numbers.

**This record grants no execution authority.** All three activation constants remain `None`,
migration `0016` remains unapplied, the operational catalog remains at head `0015`, and no
E0-v3 namespace exists. Decision 113's compact derived-evidence ruling — the contract
`e0-compact-evidence/2`, the implicit-resolution rule, the compact corroboration representation,
and their digests — is unchanged in every particular.

## 1. The accepted diagnosis — R22

The primary technical cause, the finding the diagnosis labelled **H2 + H5**:

> D117 throughput was primarily constrained by **SQLite random-write amplification interacting
> with a working set far larger than effective cache residency**.

Two facts make that a mechanism rather than a restatement. The host has `8 GiB` of RAM, and the
D117 working catalog reached about `25.65 GiB` — so the working set could not be resident
whatever the configuration. And **no explicit `cache_size` was ever configured**, so SQLite's own
default applied: about `2 MiB` of page cache for a database three orders of magnitude larger than
that. Every random write therefore met a cold page, and every cold page cost a read before it
cost a write.

## 2. The evidence

| Term | Accepted value |
|---|---|
| host RAM | `8 GiB` |
| D117 working catalog | `25.65 GiB` |
| effective SQLite page cache | about `2 MiB` (default; no `cache_size` configured) |
| observed write-ahead-log lower bound | `>= 169.61 GiB` |
| physical-write amplification lower bound | `>= 13.22x` |
| cold random lookup / page access | about `45-85x` warm access |
| accessions per second | **materially decaying with database size** |
| CPU parsing | **not** the dominant cost |

The last two rows are what rule out the alternative explanations. A parser-bound or CPU-bound run
does not decay as the *database* grows, and a run whose cost were dominated by parsing would not
show a `13.22x` floor on physical writes.

## 3. R21 — the D113 performance basis is superseded, as a predictive assumption

The [Decision 113](decision_113_m3_3_compact_derived_e0_evidence.md) §14 performance samples were
taken **entirely within the RAM-resident regime**. They are not accepted as predictive evidence
for the 50+ GB source-1 working state, because they measured a regime the real run never entered.

The former **8-hour first-source performance gate** is therefore superseded **as a predictive
assumption**. The supersession is exactly that narrow: D113's measured densities, its compaction
ruling, its stop rule, and every other D110–D116 semantic stand unchanged.

**This does not itself authorize a longer full-source run.**

## 4. R23 — post-materialization performance is unmeasured

Materialization is the only phase D117 exercised at real scale. Projection, resolution,
association, and final evidence work remain **unmeasured at real scale**.

Two consequences, both binding:

* **No full-source retry will be authorized merely from improved materialization throughput.**
  A faster prefix says nothing about the phases that follow it.
* A later **bounded finalization measurement** will be required before that question is settled.

## 5. R24 — the capacity model is strained, not invalidated

The Decision 113 capacity density is **`STRAINED BUT NOT INVALIDATED`**. Observed real prefix
density ran approximately **`+28.2%` above the accepted submissions density**.

That finding is recorded here durably, for later recalibration. **No Decision 113 capacity
constant or model change is authorized**, and `src/disclosure_drift/m3/capacity_plan.py` is
unchanged.

## 6. R25 — the sidecar autocommit cadence is a real candidate, and it is deferred

The compact sidecar committed **316,000 synchronous `FULL` autocommit member transactions** over
the D117 prefix. That is accepted as a **real optimization candidate**.

It is **deferred**, and the reason is methodological rather than doubtful: the cache correction
must be measured in isolation first, so its effect is attributable. Compact-sidecar transaction
semantics are therefore unchanged.

## 7. R26 — schema and index changes are deferred

The following remain **potential later optimizations only**, and none is authorized:

* removing the 7-column `UNIQUE` constraint and its index;
* removing `idx_census_parsed_observation`;
* adding or dropping any schema index;
* creating migration `0016` or any other migration.

## 8. The selected next action

**C1 only, plus bounded prefix remeasurement.** One explicit SQLite page-cache budget on the
disposable canary's run-local writable working catalog, and a bounded diagnostic way to
re-measure the accepted materialization path over the first *N* members — nothing else, so the
next measurement attributes its result to one change. That is
[Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md).

## 9. What this record does not do

It authorizes no execution: no first-source retry, no three-source canary, no real replay proof,
no E0-v3, no migration `0016`, no network, no acquisition. It changes no evidence contract, no
digest, no capacity constant, and no schema. It does not reopen semantic compaction, which
Decision 113 §15 closed.
