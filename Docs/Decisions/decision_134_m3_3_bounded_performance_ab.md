# Decision 134 — The Bounded Performance A/B, and the Decision to Adopt Nothing

```text
STATUS: ACCEPTED — OWNER RULING / BOUNDED PERFORMANCE EXPERIMENT
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF A COMPLETED BOUNDED EXPERIMENT WHOSE
  RESULT IS A DECISION TO CHANGE NOTHING
DATE: 2026-08-22
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
CLASSIFICATION: BOUNDED_PERFORMANCE_EXPERIMENT_NO_ADOPTION
ACCEPTANCE_TOKEN: M3_3_D134_BOUNDED_PERFORMANCE_AB_OWNER_ACCEPTED
PUBLICATION_TOKEN: M3_3_D134_GOVERNANCE_PUBLICATION_AUTHORIZED
PRESERVATION_RULING_TOKEN: M3_3_D134_DURABLE_EVIDENCE_PRESERVATION_OWNER_ACCEPTED
PRESERVATION_AUTHORIZATION: M3_3_D134_EVIDENCE_PRESERVATION_CLEANUP_PUBLICATION_RESUME_AUTHORIZED
OUTCOME: D134_NO_LOW_RISK_PERFORMANCE_CHANGE_WORTH_ADOPTING
RUNTIME_CONFIGURATION_DISPOSITION: THE ACCEPTED D131 CONFIGURATION IS UNCHANGED
PRAGMA_SURFACE_DISPOSITION: THE ACCEPTED D119 PRAGMA SURFACE IS UNCHANGED
CANDIDATE_A_MMAP: REJECTED FOR ADOPTION
CANDIDATE_B_CHECKPOINT_CADENCE: REJECTED FOR ADOPTION
EXECUTABLE_CHANGE_SET: NONE — NO SOURCE, TEST, SCRIPT, CONFIGURATION, SCHEMA, OR MIGRATION BYTE
D128_SEMANTIC_DISPOSITION: UNCHANGED. D129-R2'S REJECTION OF EVERY D128 COUNT STANDS ENTIRELY
D131_DISPOSITION: UNAFFECTED AND UNCHANGED
D132_DISPOSITION: UNAFFECTED AND UNCHANGED
D133_DISPOSITION: UNAFFECTED AND UNCHANGED
SOURCE_WIDE_CLAIM: NONE
COMPLETE_SOURCE_AUTHORIZATION: NO
CORRECTED_CANARY_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
CAPACITY_RECONCILIATION_STATUS: D129-R12 UNRESOLVED — AND IT IS THE NEXT SUBSTANTIVE STAGE
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
```

The owner's governance publication of the bounded performance A/B authorized after
[Decision 133](decision_133_m3_3_watchdog_linux_portability_repair.md), together with the owner's
ruling that **neither measured candidate is worth adopting** and the owner's ruling on **how the
experiment's evidence is retained**.

## 1. What this record is, and what it is not

**It is the record of an experiment that changed nothing.** Two low-risk runtime candidates were
measured against a baseline at two bounded operating points. Both were measured honestly, both
produced real numbers, and **both were rejected for adoption**. The accepted
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) runtime configuration and
the accepted [Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md)
pragma surface stand **byte-unchanged**, and this record ships **no executable change set at all** —
no source, test, script, configuration, schema, or migration byte moved for it.

**A negative result is a result.** The experiment was run to answer whether a cheap runtime change
would materially improve the complete-source path. The answer is **no**, and recording that answer
is what prevents the same two candidates from being proposed again as though they were untried.

**It measures operating points, not the population.** Every number below describes the two
bounded fixtures actually run — `3,520` and `6,871` archive members drawn from a source holding
`985,835`. **No complete-source performance claim is authorized by any of it**, and §10 states why
the mmap trend in particular argues *against* extrapolating the benefit upward.

**It certifies no count and moves no semantic boundary.**
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (D129-R2)'s rejection of every
D128 semantic count stands entirely.
[Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md)'s bounded real semantic proof and
[Decision 133](decision_133_m3_3_watchdog_linux_portability_repair.md)'s cross-platform operator-tool
contract are both untouched. The semantic evidence in §7 establishes that the candidates **did not
change the census**, which is a statement about the candidates — not a new census measurement.

**It closes no blocker and authorizes no execution.** §11 carries both open blockers forward
unchanged.

## 2. Entry state

The experiment and this publication both entered at the accepted post-D133 baseline, verified live
rather than assumed:

| Property | Value |
|---|---|
| Branch | `main` |
| HEAD | `e785f7d0395b8d9df0505ff70978a58694ce2e84` |
| HEAD tree | `39767bd662bbb346023557cd558d7a82afdbd1ed` |
| `origin/main` == HEAD | yes; ahead `0`, behind `0` |
| Working tree | clean; nothing staged |
| Latest decision record | `133` |
| Migration head | `0015_m33_verified_document_evidence.sql`; `0016` absent |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` |
| `network.enabled` / `network.m3_acquire_enabled` | `false` / `false`; request ceiling `0` |
| D132 proof manifest SHA-256 | `732e696a…` — re-read and matched at entry |

## 3. The measurement design

**The accepted source.** `sec_bulk_submissions-c85744be921b0dc5.zip` in the private evidence root:
`1,556,847,020` bytes, SHA-256
`c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f`, central directory holding
`985,835` members (`980,497` primary, `5,337` historical shards across `4,144` parent CIKs).

**The deterministic selection rule**, frozen before any arm ran and recorded in the retained
evidence:

> first N primary members by ascending archive ordinal, plus every member named in each selected
> parent's `filings.files[].name` that exists in the archive; fixture written in ascending archive
> ordinal

**Two operating points**, chosen to make the *direction* of any effect visible rather than a single
number:

| Fixture | Primaries | Members | Shards | Accessions | Parsed records | Archive SHA-256 |
|---|---|---|---|---|---|---|
| `ab3000` | `3,000` | `3,520` | `520` | `1,276,084` | `1,294,745` | `4a2903a534c578d5…` |
| `ab6000` | `6,000` | `6,871` | `871` | `2,181,341` | `2,232,465` | `2f5d9d0cba615450…` |

**Both fixtures are byte-identical to the accepted source.** Every member was verified against the
source archive: `ab3000` `3,520` of `3,520` checked with `0` mismatches; `ab6000` `6,871` of `6,871`
checked with `0` mismatches. **No synthetic content entered either arm.**

**The baseline is the accepted D131 configuration**, read back from a real writing connection rather
than recalled: `journal_mode=wal`, `synchronous=2` (`FULL`), `page_size=4096`,
`cache_size=-524288` (512 MiB), `wal_autocheckpoint=1000`, `busy_timeout=10000`,
`mmap_size=0`, on SQLite `3.53.4`.

## 4. Candidate A — `PRAGMA mmap_size` — D134-R2

**The candidate was non-vacuous, and the record states exactly how far it got.** `4,294,967,296`
bytes were requested; SQLite granted **`2,147,418,112`** and silently clamped the rest, because the
accepted interpreter's SQLite is compiled with `MAX_MMAP_SIZE=0x7fff0000`. The baseline connection
read back `mmap_size=0` and the candidate read back `2,147,418,112`, so **the two arms differ on the
connection's own read-back, not merely on the request.**

| Metric | `ab3000` baseline | `ab3000` mmap | `ab6000` baseline | `ab6000` mmap |
|---|---|---|---|---|
| Wall median (s) | `660.401` | `575.605` | `1343.783` | `1212.434` |
| Improvement | — | **`12.84%`** | — | **`9.775%`** |
| Repetitions | `2` | `2` | `1` | `1` |
| Peak RSS (bytes) | `959,201,280` | `2,754,265,088` | `1,041,743,872` | `2,468,855,808` |
| RSS delta | — | **`+1,795,063,808`** | — | **`+1,427,111,936`** |
| CPU/wall ratio | `0.817`–`0.827` | `0.958`–`0.959` | `0.729` | `0.813` |
| Map coverage of catalog | — | `80.64%` | — | `45.33%` |

**The benefit declined as the catalog grew**, and the mechanism is not mysterious: a fixed `2.0` GiB
map covers `80.64%` of the `ab3000` working catalog but only `45.33%` of the `ab6000` one. **The
trend runs the wrong way for the complete-source run**, whose catalog is far larger than either
point measured here.

**Why it is rejected** (D134-R2). It never reached the `>= 15%` preferred adoption threshold at
either point. The owner's own `5–15%` band calls this **modest** and not worth a production change
unless the implementation is trivial **and** risk-free — and while the implementation is trivial
(one pragma), it is **not** risk-free:

- **`+1.33` to `+1.67` GiB peak RSS** on an `8` GiB host, against the `2.271` GiB baseline peak
  [Decision 120](decision_120_m3_3_real_120k_cache_profile_prefix.md) measured for a real prefix run.
  The increase is bounded by `MAX_MMAP_SIZE` and so does not grow with catalog size — but the
  *headroom* it consumes is spent regardless.
- **Under mmap, an I/O error on a mapped page is delivered as `SIGBUS`** rather than an error
  return. That is a robustness change for a multi-hour run, not a tuning knob.
- **Adoption would be governance-visible, not silent**: it would require changing the accepted D119
  pragma-surface test that pins the assigned pragma set to
  `{journal_mode, synchronous, cache_size}`.

## 5. Candidate B — relaxed checkpoint cadence — D134-R3

**The candidate was non-vacuous and the reduction was large.** Of `5,120` eligible batch boundaries
at `ab3000`, the baseline issued `5,120` checkpoints and the candidate issued **`160`**, suppressing
`4,960` — a **`32×`** cadence reduction.

| Metric | `ab3000` baseline | `ab3000` ckpt |
|---|---|---|
| Wall median (s) | `660.401` | `652.578` |
| Improvement | — | **`1.185%` — `IMMATERIAL`** |
| Checkpoints issued | `5,120` | `160` |
| WAL high-water (bytes) | `768,054,552` | **`768,054,552` — identical** |

**Relaxing the cadence bought neither wall-clock time nor peak disk.** The `1.185%` improvement sits
below the owner's `5%` materiality floor, and — more informative than the timing — **the WAL
high-water mark was byte-identical between the arms.**

**The reason is structural, and it is the durable finding of this section**: peak WAL is set entirely
by **F2's single association transaction**, which neither arm checkpoints inside. **The F0/F1
checkpoint cadence never governed the peak at all.** Any future proposal to control peak WAL by
tuning F0/F1 cadence is answered here, in advance: it cannot work.

**The `ab6000` checkpoint arm was cancelled** under the early stop (§6) and, per D134-R3, **does not
need to be run**: the mechanism above does not become cadence-sensitive at a larger operating point.

## 6. The early stop — D134-R4

A prospective early-stop amendment was issued **before** the `ab6000` arms ran, with precommitted
threshold cases. The `ab6000` mmap repetition returned **`9.775%`**, landing in **case 2
(`>= 5%` and `< 10%`)**, whose precommitted action is `STOP_AFTER_MMAP_R1`.

The guard confirmed the stop was clean rather than an artifact: counts matched the baseline exactly
(`2,181,341` accessions, `6,871` members, `2,232,465` parsed records), the arm was non-vacuous
(`effective_mmap_size = 2,147,418,112`), and **no measurement anomaly was flagged**.

**The amendment and its execution are accepted** (D134-R4). **Reduced repetition at `ab6000` is an
accepted consequence of a rule that was fixed in advance — not a defect requiring more execution.**
§10 states the confidence cost plainly rather than hiding it. **No cancelled arm is restarted.**

## 7. Semantic equivalence — D134-R5

**Every arm produced the same census as its baseline.** Across the `8` measured arms, `6`
arm-to-baseline comparisons were computed, and all `6` were semantically equal:

- **`0` stable-column table differences** across `27` tables per arm, each carrying
  `digest_stable_columns`, `digest_all_columns`, and `row_count`;
- **compact-evidence member digest equal** in every comparison;
- **semantic result document equal** in every comparison, with `0` field differences;
- `10` tables differ **only** in columns already classified volatile (run ids, timestamps,
  attempt-scoped identifiers) — recorded rather than smoothed away, because that is the expected and
  correct signature of two separate runs producing the same census.

**What this establishes and what it does not** (D134-R5). It establishes that **neither candidate
perturbed semantics on the measured fixtures**. It establishes **nothing** about population-wide or
source-wide correctness or counts. `6,871` members of `985,835` is a bounded proof, and it is not a
census.

## 8. The adoption decision — D134-R1

**Nothing is adopted.** The formal outcome is
**`D134_NO_LOW_RISK_PERFORMANCE_CHANGE_WORTH_ADOPTING`**.

- `PRAGMA mmap_size` — **not adopted, not implemented**.
- Relaxed checkpoint cadence — **not adopted, not implemented**.
- The accepted **D131 runtime configuration is unchanged**.
- The accepted **D119 pragma surface is unchanged**.
- **No executable byte** ships with this record.

**The bounded measurements establish the measured operating points and nothing further.** They do
**not** authorize extrapolated complete-source performance claims (D134-R1).

## 9. Durable evidence preservation and reclamation — D134-R8

**The first cleanup attempt was correctly refused, and that refusal is part of this record.** The
executing session was authorized to delete the experiment's disposable `worlds/` and `fixtures/`
trees after proving they held no unique audit evidence. **That proof did not hold**, and the session
**stopped without deleting anything** — every fixture hash, per-arm pragma read-back, per-table
digest, compact-evidence digest, and semantic-result digest existed **only** inside the two
directories slated for deletion, with no copy in the retained evidence set or anywhere else. Had the
deletion proceeded, §7's equivalence claim would have become **permanently unverifiable**: a reader
could see the verdict `true` and never re-check it.

**The owner ruled to preserve first, then reclaim.** Under
`M3_3_D134_DURABLE_EVIDENCE_PRESERVATION_OWNER_ACCEPTED`, the unique audit JSON was promoted
**byte-exactly** into the retained evidence set before either tree was removed:

| Preservation fact | Value |
|---|---|
| Artifacts preserved | `32` JSON files — `10` canary results, `9` arm records, `8` arm semantics, `3` fixture manifests, `2` fixture byte-equality records |
| Bytes preserved | `2,919,526` — byte totals equal at source and destination |
| Verification | `32/32` byte-identical by `cmp` **and** by an independent `shasum` pass; `0` missing, `0` hash mismatch, `0` collision |
| Preservation manifest | `evidence/d134_preservation_manifest.json`, `39,960` bytes, SHA-256 `68ed5537af2be388b7ebdf7bff6545f71be3c586649104bb3523731aee6d60b3` |

**The manifest authenticates the chain, not just the copies**: the repository HEAD and tree the
experiment ran at, the accepted source's full SHA-256 and central-directory scan, both deterministic
workload identities with their archive and catalog hashes, the retained harness and `phase1` file
digests, and per artifact its original path, preserved path, size, SHA-256, class, operating point,
run identity, and which claim it proves. It does **not** self-include its own hash — that hash is
recorded here, which is the same convention by which D132's manifest hash was recorded outside
itself.

**An eleven-row audit matrix was proved before anything was deleted**, covering the selection rule,
fixture provenance and hashes, source-byte equality, pragma read-back, arm measurements, the
early-stop decision, the classification, per-table stable-column digests, compact-evidence digests,
semantic-result digests, and the provenance tying those digests to the measured runs. Two
re-derivations were performed **from the preserved copies alone**:

- the published improvements were **recomputed**: `12.84%`, `9.775%`, `1.185%` — matching §§4–5
  exactly;
- the `6` semantic-equivalence verdicts of §7 were **recomputed** using the retained harness's own
  `RESULT_VOLATILE` exclusion set, and all `6` agree with the published verdicts.

**Only then were the two authorized trees deleted**, and nothing else:

| Reclamation fact | Value |
|---|---|
| Deleted | `worlds/` (`25,559,019,520` bytes, `93` files) and `fixtures/` (`101,154,816` bytes, `17` files) |
| Combined measured | `25,660,174,336` bytes = `23.898` GiB |
| Filesystem-observed reclaim | `25,051,648` KiB = **`23.891` GiB**; free `94.279` → `118.170` GiB |
| Retained | `evidence/`, `logs/`, `harness/`, `phase1/` — all present and verified after deletion |

**The retention posture this establishes** (D134-R8): **compact audit evidence is retained; bulky
reproducible worlds and fixtures are reclaimed under owner authority.** The deleted trees are
reproducible from the accepted source plus the recorded deterministic selection rule and the
retained harness; only their JSON carried values that reproduction could not recover, and that JSON
survives.

**One operational note for a future auditor.** The retained `harness/d134_compare.py` resolves arm
documents at `worlds/<run_id>/d134_semantics.json`, a path that no longer exists. The preserved
copies live at `evidence/preserved_world_json/<run_id>/d134_semantics.json`, so re-running that
comparator requires repointing its root. **No data is missing** — the re-derivations above were
performed against the preserved copies — but the path in the harness is stale by construction.

## 10. Limitations and reduced confidence

Stated plainly, because the early stop bought speed at a real cost:

- **`ab6000` carries a single repetition per arm.** Its `9.775%` figure has no within-point spread
  to check it against, unlike `ab3000`, whose baseline arms differed by `1.291%` run to run. A single
  repetition **cannot** distinguish a `9.775%` effect from an effect a point or two either side.
- **The `ab6000` checkpoint arm was never measured.** §5's conclusion at that operating point rests
  on the F2 mechanism, not on measurement.
- **Two operating points do not define a curve.** They establish a direction — declining mmap benefit
  with catalog growth — and a direction is not an extrapolation.
- **Nothing here is a complete-source measurement.** The largest fixture is `6,871` of `985,835`
  members, under `0.7%` of the source.
- **Semantic equivalence is bounded** to the measured fixtures (§7) and certifies no D128 count.

**None of these limitations changes the adoption decision.** Both candidates were rejected for
reasons that a longer run would not reverse: the mmap benefit is below threshold *and trending
down*, and the checkpoint candidate is immaterial *and mechanically incapable* of moving peak WAL.

## 11. Remaining blockers

**Both blockers carry forward exactly as written, and this record closes neither.**

**The capacity reconciliation** (D134-R6).
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12) — the corrected-run
capacity reconciliation — **remains unresolved and is now the next substantive stage**. It requires
its own owner instrument. Free space is **informational only**: an input to a capacity model and
never a substitute for one.

**The pre-network blocker** (D134-R7).
`src/disclosure_drift/sec/census_orchestrator.py::_parse_bulk` still carries the historical-shard
dispatch defect and remains **deliberately unrepaired** under
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §12 (D131-R4). It was not
repaired in this session and **must not be repaired as a side effect of unrelated work**. It is safe
today only because it sits behind `require_network()` with network disabled at both tracked switches
at request ceiling `0` — **unreachable is a property of the current configuration, not of the code**.
**No future network or live-retrieval authorization may reach that path until it is separately
repaired and accepted.**

**A complete-source canary is not authorized**, and remains gated behind *both* a performance
disposition — which this record now supplies — and the D129-R12 reconciliation, which it does not.
**E0 is not authorized.**

## 12. Owner rulings D134-R1 – D134-R8

| Ruling | Content |
|---|---|
| **D134-R1** | **Performance disposition.** The accepted D131 runtime configuration is unchanged. `PRAGMA mmap_size` is not adopted; relaxed checkpoint cadence is not adopted; neither is implemented; the accepted D119 pragma surface is not altered. The bounded measurements establish the measured operating points only and **do not authorize extrapolated complete-source performance claims** |
| **D134-R2** | **mmap rejected for adoption.** Accepted evidence: `ab3000` `12.84%`, `MODEST`; `ab6000` `9.775%`, `MODEST`; benefit **declined** as catalog size increased; SQLite clamped the map to `2,147,418,112` bytes; a material peak-RSS increase was observed; **no semantic differences were observed**. No further D134 mmap repetition is required |
| **D134-R3** | **Checkpoint cadence rejected for adoption.** Accepted evidence: `ab3000` improvement `1.185%`, `IMMATERIAL`; the checkpoint-frequency reduction was **non-vacuous** (`5,120` → `160`); WAL high-water was **unchanged**; **F2 — not F0/F1 checkpoint cadence — determines peak WAL on the measured path**. The cancelled `ab6000` checkpoint arm does not need to be run |
| **D134-R4** | **Early stop accepted.** The prospective early-stop amendment and its execution are accepted. The `ab6000` mmap result of `9.775%` triggered the precommitted `>= 5%`, `< 10%` stop case. **Reduced repetition at `ab6000` is an accepted consequence of that rule, not a defect requiring additional execution.** No cancelled D134 arm is restarted |
| **D134-R5** | **Semantics accepted, bounded.** The semantic-equivalence evidence is accepted **for the bounded experiments**. It does **not** establish population- or source-wide correctness or counts |
| **D134-R6** | **Next sequence.** After D134 publication the next substantive stage is the **D129-R12 corrected-run capacity reconciliation**. It requires a separate owner instrument. Only after that reconciliation may the owner decide whether to authorize another complete-source canary. **E0 remains unauthorized** |
| **D134-R7** | **Pre-network blocker.** `census_orchestrator.py::_parse_bulk` remains a separate **PRE-NETWORK** blocker under D131-R4. It was not repaired in this session, and **no future network or live-retrieval authorization may reach it until it is separately repaired and accepted** |
| **D134-R8** | **Retention posture.** Compact audit evidence is retained; bulky reproducible disposable worlds and fixtures are reclaimed under owner authority. The disposable `worlds/` and `fixtures/` trees were deleted **only after** their unique audit JSON was promoted byte-exactly into the retained evidence set and authenticated by the preservation manifest recorded in §9 |

## 13. What this record does not do

It **adopts no performance change** and **implements neither candidate**. It **alters no accepted
pragma surface**, **no runtime configuration**, **no schema**, and **no migration** — migration head
remains `0015`, `0016` is absent and unauthorized. It **changes no production package code, test,
script, or configuration byte**; its executable change set is **empty**.

It **certifies no D128 count** — D129-R2's rejection stands entirely, and D129-R8's four requirements
for a corrected proof are unchanged. It **reopens no D131, D132, or D133 claim**. It **constructs no
capacity model** and **resolves no part of D129-R12**. It **makes no source-wide claim** of any kind.

It **grants no execution authority**: another performance experiment, a capacity reconciliation, a
corrected canary, any canary, any disposable world, E0, migration `0016`, network, SEC, and HTTP all
remain unauthorized at request ceiling `0`, and **all three activation constants remain `None`**.

**Publishing a decision to change nothing is not authorizing anything.**

## 14. The next sequence — D134-R6

Unchanged from [Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md) §17 except that its
performance step is now **complete and closed with no adoption**:

1. **The D129-R12 corrected-run capacity reconciliation** — the next substantive stage, requiring its
   own owner instrument, and using the repaired parser with the **unchanged** D131 runtime
   configuration this record confirms.
2. **Then and only then**, an owner decision on whether to authorize another complete-source canary —
   which [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §14 (D129-R8) still requires
   to be a **full rerun from scratch in a new world** with a new run identity.

**Separately and independently of that sequence**, `census_orchestrator.py::_parse_bulk` must be
repaired before any network or live-retrieval authorization may reach it (D134-R7).

**E0 remains unauthorized throughout.** No step in this sequence carries E0 authority, and reaching
its last step is not reaching E0.
