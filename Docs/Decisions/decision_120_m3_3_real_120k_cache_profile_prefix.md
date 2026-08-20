# Decision 120 — The Real 120,000-Member Cache-Bound Prefix Measurement

```text
STATUS: ACCEPTED — OWNER FINDING, CLOSED
RECORD_TYPE: RETROSPECTIVE PUBLICATION OF ALREADY-ACCEPTED OWNER FINDINGS
DATE: 2026-08-20 (record published); the execution and its owner acceptance preceded it
OWNER: Joey authorization; Sol/GPT-5.6 owner findings
OUTCOME: M3_3_D120_REAL_120K_CACHE_PROFILE_OWNER_ACCEPTED
SUPERSEDES: nothing
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The first **real** use of the bounded diagnostic prefix surface
[Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md) §§6–8 built:
120,000 governed members of the accepted `sec_bulk_submissions` first planned source, under the
Decision 119 §4 **C1** 512 MiB page-cache budget. It measured the cache correction against real
data, and it is recorded here as an accepted owner finding.

## 1. What this record is, and what it is not

**It is a retrospective publication.** This record did **not** exist when the run it describes
executed, and nothing here should be read as though it did. The authority under which the D120
execution ran was the **GPT-5.6 Sol owner instrument** issued for that run — not this file, not any
other committed record, and not the repository itself. Decision 119 §11 expressly prohibited real
data under Decision 119, and that prohibition was not what authorized this; a separate owner
instrument was.

What this record does is make durable repository governance reflect accepted history truthfully.
No timestamp is rewritten, no earlier record is amended, and no claim is made that the repository
authorized the execution in advance.

**Provenance, stated rather than implied.** Every measured value below is quoted from the owner
instrument that accepted the D120 execution. The session that wrote this record did not re-run the
prefix, did not open the preserved D120 world, and re-derived none of these numbers. Where a value
below is arithmetic over two accepted values, it says so.

**No ruling numbers were issued for this record.** Decisions 118 and 119 carry numbered rulings
(`R21`–`R28`) because the owner issued them as numbered rulings. The D120 findings were issued as
accepted findings and a token, without ruling numbers, and none is invented here.

## 2. Entry state at execution

The published code baseline the run executed against was commit
`ac4636cb2d770ae9822e4e0216a480b05a423729` — the commit that carries the Decision 119 cache
correction and the prefix surface. Migration head `0015`; migration `0016` absent; no E0-v3
namespace; `M3_3_E0_EXECUTION_AUTHORITY`, `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` all `None`; both tracked network switches `false` at
request ceiling `0`. The preserved D117 world was not opened.

## 3. What ran

Run identity **`m3_3_d120_cache_120k_prefix_v1`**, on a local Apple M1 host with `8 GiB` of RAM.

The exact diagnostic: the accepted `sec_bulk_submissions` first planned source, its **first 120,000
governed deterministic members**, through `--mode profile-prefix`, at a `512 MiB` `WorkingCatalog`
cache, `WorkingCatalog` batch size `250`, `journal_mode = WAL`, `synchronous = FULL`, and a
write-ahead-log checkpoint at every batch boundary.

Everything else is the accepted path unchanged: the same deterministic member ordering, the same
parser, the same working-catalog persistence, the same compact member recording, and the same
compact sidecar.

## 4. What was measured

| Term | Accepted value |
|---|---|
| host | local Apple M1, `8 GiB` RAM |
| elapsed | `16,006.98 s` = **`4.446 h`** |
| peak resident set | about **`2.271 GiB`** |
| working database | `19,922,350,080 B` (about `18.554 GiB`) |
| compact sidecar | `33,366,016 B` (about `31.82 MiB`) |
| final write-ahead log | `0` |
| parsed accessions | `9,157,697` |
| durable canonical accessions | `8,258,521` |

The last two rows are the **processed** and **durable** counts Decision 119 §8 requires to be
reported separately, and they are reported separately here for that reason. They are not two
measurements of the same quantity and neither is a correction of the other.

Peak resident set of about `2.271 GiB` against a `512 MiB` configured cache on an `8 GiB` host is
recorded as a measured fact, not as a budget the run was held to.

## 5. The classification

**`INCOMPLETE_DIAGNOSTIC_PREFIX`** — the Decision 119 §6 classification, deliberately outside the
accepted `SourceDisposition` vocabulary.

Everything that classification forecloses held: no source reached a terminal disposition, no
`census_plan_sources.parser_state` transition occurred, no full-index materialization ran, no
catalog-wide resolution pass ran, no Decision 094 §6.4 association projection ran, and none of the
five complete-source identities — member-manifest digest, projection digest, `ResolutionDigest`,
`CorroborationDigest`, compact-evidence identity — was emitted. Nothing was promoted, no migration
was applied, and no authority constant was touched.

**A prefix is not a source.** 120,000 members is a bounded diagnostic over the first planned source
and says nothing about the remaining members of that source, and nothing at all about the other 75.

## 6. The owner conclusions

**C1 is retained.** The Decision 119 §4 512 MiB working-catalog cache budget stays exactly as
Decision 119 accepted it. Measured against real data it provides a **modest real improvement**.

**It does not fix the failure it was aimed at.** The database-size-dependent throughput collapse
Decision 118 §1 diagnosed is **not removed** by the cache correction. C1 moves the constant; it does
not change the shape of the curve.

**No complete-source retry follows.** No complete-source retry, and no retry of any kind, is
authorized by this record or by the measurement in it. That is the same position Decision 118 §4
(R23) already states from the other direction — improved materialization throughput alone does not
settle the question — and this record neither weakens nor re-argues it.

## 7. The preserved D120 world

The D120 world is **preserved evidence**. Its working catalog is the `19,922,350,080 B` database
§4 records, and its identity is captured in
[Decision 122](decision_122_m3_3_d120_f1_finalization_characterization.md) §3.

It may not be resumed, promoted, vacuumed, reindexed, or deleted. Decision 122 §4 authorized taking
an **APFS copy-on-write clone** of it into a separate diagnostic world and operating on the clone;
that authorization reached the clone and never the original, and the original is unmodified.

## 8. What this record does not do

It authorizes nothing. It grants no execution authority, no complete-source authority, no E0-v3
authority, no migration `0016`, no network, no acquisition, no D117 retry, and no three-source
canary. All three activation constants remain `None`, the operational catalog remains at migration
head `0015`, and no E0-v3 namespace exists. It supersedes nothing, changes no evidence contract, no
digest, no capacity constant, and no schema, and it reopens no deferral.
