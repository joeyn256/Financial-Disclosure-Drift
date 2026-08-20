# Decision 121 — The Local Finalization-Feasibility Preflight

```text
STATUS: ACCEPTED — OWNER FINDING, READ-ONLY PREFLIGHT, CLOSED
RECORD_TYPE: RETROSPECTIVE PUBLICATION OF ALREADY-ACCEPTED OWNER FINDINGS
DATE: 2026-08-20 (record published); the preflight and its owner acceptance preceded it
OWNER: Joey authorization; Sol/GPT-5.6 owner findings
OUTCOME: M3_3_D121_FINALIZATION_FEASIBILITY_PREFLIGHT_OWNER_ACCEPTED
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

[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §4 (R23) recorded that
projection, resolution, association, and final evidence remain **unmeasured at real scale**, and
that a bounded finalization measurement would be required before the full-source question could be
settled. This record is the **read-only** preflight that established whether such a measurement was
feasible locally, and on what shape it would have to be run.

**It is read-only, and that is the whole of it.** No database was written, no world was created, no
world was modified, no source was parsed, and nothing was deleted under this record.

## 1. What this record is, and what it is not

**It is a retrospective publication.** This record did **not** exist when the preflight it describes
was performed. The authority at the time was the **GPT-5.6 Sol owner instrument**, not this file and
not the repository. No timestamp is rewritten and no earlier record is amended; the purpose is to
make durable governance reflect accepted history truthfully.

**Provenance, stated rather than implied.** Every measured and structural finding below is quoted
from the owner instrument that accepted the preflight. The session that wrote this record did not
re-run the preflight and re-derived none of these findings. Where this record notes that a finding
is reproduced by shipped source, it says so and names the symbol.

**No ruling numbers were issued for this record**, and none is invented here.

## 2. Entry state

Migration head `0015`; migration `0016` absent; no E0-v3 namespace; all three activation constants
`None`; both tracked network switches `false` at request ceiling `0`. Entering this preflight the
repository held [Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md)
as the accepted cache correction and prefix surface, and
[Decision 120](decision_120_m3_3_real_120k_cache_profile_prefix.md) as the accepted real
120,000-member measurement over it. The preserved D117 and D120 worlds were not opened for writing.

## 3. The non-governed C3 exploratory experiment

Between the D120 measurement and this preflight, one **non-governed exploratory performance
experiment** was run and accepted as research evidence. It is recorded here as chronology. It is
**not a decision**, it carries **no decision number**, and it governs nothing — repository
convention requires a numbered record for an owner ruling, not for an experiment, and inventing one
would misstate what it was.

**`M3_3_PERF_C3_LOCAL_40K_V1`.** Over 40,000 members, C3 batched the compact sidecar's commits:
**40,000 sidecar commits reduced to 160** — the count a batch size of `250` implies. It is the
optimization candidate [Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §6 (R25)
recorded and deliberately deferred.

| Term | Accepted value |
|---|---|
| members | `40,000` |
| sidecar commits | `40,000` → `160` |
| sidecar evidence | **byte-identical** to the D120 first 40,000 |
| throughput | about **`8.1%` slower** than the D120 control |

**Owner conclusion.** C3 batching is **measured and immaterial for throughput**. It is **not
integrated**, and **no paired C3 rerun is authorized**. The single-run host-drift ambiguity is
acknowledged rather than resolved: one run against one control cannot separate an `8.1%` regression
from host variation, and the owner conclusion is that the question is not worth a second run rather
than that the regression is established.

The byte-identical sidecar evidence is the finding worth keeping: commit **cadence** moved and
recorded evidence did not, which is what makes the cadence a performance question and not an
evidence-semantic one.

Owner token: **`M3_3_PERF_C3_LOCAL_40K_OWNER_ACCEPTED`**.

[Decision 122](decision_122_m3_3_d120_f1_finalization_characterization.md) §§3–4 later authorized
deleting **only** the C3 working catalog, after its SHA-256 identity was captured, while retaining
its compact evidence, result, and progress artifacts. That deletion is recorded there, not here.

## 4. F1 and F2 — finalization is two different shapes, not one

The central structural finding, and the reason this record exists: what is loosely called
"finalization" is **two operations with opposite interruption behaviour**, and they must be measured
and authorized separately.

**F1 — the resolution pass. Batched, checkpointed, interruptible.**
`count_persisted_accession_resolutions` runs at batch size `250` with a write-ahead-log
`checkpoint(TRUNCATE)` at each batch boundary. It is **not** a single giant transaction. An
interruption therefore loses at most the open batch, and the write-ahead log does not grow without
bound. This is reproduced by shipped source: `SecCensusCatalog.count_persisted_accession_resolutions`
in `src/disclosure_drift/sec/census.py` takes `batch_size` and `checkpoint_batches`, and the
Decision 116 canary path in `src/disclosure_drift/m3/single_source_canary.py` passes both.

**F2 — the association projection. One transaction, and no way to checkpoint it.**
`materialize_census_associations` writes **and checks** in **one transaction** spanning both
association traversals and the §9.5 totality check. SQLite **cannot checkpoint an uncommitted
write-ahead log**, so the log cannot be truncated part-way through; and an interruption at any point
before commit **loses the entire F2 transaction**. This too is reproduced by shipped source:
`materialize_census_associations` in `src/disclosure_drift/m3/offline_parse.py` states the
single-transaction contract in its own docstring.

**The single transaction is a correctness property, not a defect.** Decision 094 §§6.2–6.4 requires
the projection to be all-or-nothing precisely so that an interruption cannot leave an `established`
incomplete set, a partial relation, or a persisted partial projection behind. The finding here is
**not** that F2 should be batched. It is that F2's cost and its write-ahead-log high-water mark are
**unmeasured**, and that they cannot be inferred from F1's, because the two have different shapes.

## 5. What D120 is representative of, and what it is not

**D120 is performance-representative of the first-source canary finalization shape**, because
**full-index evidence is absent in both**. That absence is the specific property that makes the
comparison valid, and it is stated as the reason rather than assumed.

**D120 is not representative of full 76-source E0 finalization.** A complete E0 run carries
full-index evidence and 75 further sources; neither is present in a first-source prefix, and no
extrapolation from D120 to complete-source E0 is accepted.

## 6. Storage

| Term | Accepted value |
|---|---|
| D120 world working database | about **`18.554 GiB`** |
| APFS `clonefile` / `cp -c` | **confirmed available** on this host |
| copy-on-write divergence | must still be budgeted as **potentially full divergence** |

The `18.554 GiB` figure is the same measurement
[Decision 120](decision_120_m3_3_real_120k_cache_profile_prefix.md) §4 records as
`19,922,350,080 B`, stated in the other unit.

**Copy-on-write is a scheduling convenience, not a storage saving.** A clone starts near-free and
diverges as either copy is written. Planning that assumes the clone stays cheap is planning that
assumes the diagnostic never writes, which is the opposite of what a diagnostic does. It must be
budgeted at **potentially full divergence**.

## 7. The owner rulings

**D120 is immutable.** The preserved D120 world is evidence. It may not be resumed, modified,
promoted, vacuumed, reindexed, or deleted.

**F1 and F2 are split.** They are separate operations, separately measured and separately
authorized. A measurement of one is not a measurement of the other, and an authorization for one is
not an authorization for the other.

**Finalization characterization is the highest-priority unknown.** Of everything currently open, the
cost and interruption behaviour of the finalization phases is the question whose answer most
constrains what may follow — which is Decision 118 §4 (R23) reaching its intended next step.

**The complete-source local canary conservative free-space planning floor is `>= 85 GiB`.** It is a
**planning floor for a complete-source local canary**, stated conservatively. It is not a capacity
model, it changes no Decision 113 capacity constant, `src/disclosure_drift/m3/capacity_plan.py` is
unchanged by this record, and meeting it authorizes nothing.

**No complete-source authority and no E0 authority is granted.** This record is a feasibility
finding. It moves no constant and opens no execution.

## 8. What this record does not do

It authorizes no execution of any kind: no complete-source canary, no D117 retry, no three-source
canary, no real replay proof, no E0-v3, no migration `0016`, no network, no acquisition. It
supersedes nothing. It changes no evidence contract, no digest, no capacity constant, and no schema,
and it reopens no deferral. All three activation constants remain `None`, the operational catalog
remains at migration head `0015`, and no E0-v3 namespace exists.
