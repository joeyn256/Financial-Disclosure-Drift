# Decision 110 — E0 Successor Safety Remediation: Memory Boundedness and Stale-Lease Evidence Preservation

```text
STATUS: ACCEPTED — OWNER REMEDIATION INSTRUMENT
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D110_E0_SUCCESSOR_SAFETY_REMEDIATION
CLOSES: D109 F1 (MAJOR), D109 F2 (MAJOR)
WORKSTREAM_A: WRITER-LEASE EVIDENCE PRESERVATION
WORKSTREAM_B: BOUNDED-MEMORY E0 OFFLINE PARSING
M3_3_E0_EXECUTION_AUTHORITY: None
PRE_E0_CATALOG_TRANSITION_AUTHORITY: None
STALE_WRITER_LEASE_RECOVERY_AUTHORITY: None
E0_V3_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
PERSISTENCE_BRIDGE_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
R52_AUTHORIZATION: NO
ACQUISITION_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
DIAGNOSTIC_CANARY: AUTHORIZED — DISPOSABLE STATE ONLY
CANARY_RSS_CEILING: 2.5 GiB
CANARY_FIRST_SOURCE_TIME_CEILING: 20 minutes
```

This record is the controlling instrument for the remediation the two accepted MAJOR findings of
[Decision 109](decision_109_m3_3_e0_v2_interruption.md) require. It changes **execution mechanics**
and nothing else. It writes no research code, changes no frozen research definition, reads no outcome
value, applies no migration, contacts no network, and redesigns no methodology. Decisions 091-109
remain binding on every point they name, and Decisions 103-108 are **not rewritten**.

**It grants no execution authority.** All three activation constants stay `None`, and a passing
remediation is not permission to run anything.

## 1. Entry state

[Decision 109](decision_109_m3_3_e0_v2_interruption.md) is owner-accepted under token
`M3_3_D109_E0_V2_INTERRUPTION_OWNER_ACCEPTED` at `HEAD`
`c96406984209ebd13b6a9021615c3960850ba4e0`. E0-v2 is `UNDETERMINED / NOT COMPLETE`, its last durable
boundary is `BACKUP_VERIFIED` at sequence 2, the catalog is unchanged from the accepted pre-E0
baseline at migration head `0015`, all 76 planned sources are `not_started`, and `census_parser_runs`
is empty. v1 and v2 are immutable evidence. No v3 namespace exists or is authorized.

## 2. Owner severity ruling

- **D109 F1 — MAJOR, accepted.** The offline parser is not executable safely on this 8 GiB host. A
  v3 retry using materially identical parser mechanics is **PROHIBITED**.
- **D109 F2 — MAJOR, accepted.** Normal `CatalogWriter` acquisition can overwrite a persisted stale
  `held` lease after obtaining a free advisory `flock`, **before** the ordinary E0 predicates refuse.
- **D109 F3-F5** — non-blocking observations and governance debt, as reported.

## 3. Scope

Exactly two remediation workstreams are authorized:

- **A.** Preserve persisted stale or structurally invalid writer-lease evidence.
- **B.** Make E0 offline parsing demonstrably bounded-memory on this host.

Not authorized by this record: E0-v3; any E0 execute against real governed state; migration `0016`;
the persistence bridge; E1; E2; R52; SEC, EDGAR, HTTP, or DNS; acquisition; modification or deletion
of v1 or v2; restoration of either consumed namespace.

## 4. Governance recorded

[Decision 109](decision_109_m3_3_e0_v2_interruption.md) is created as the missing record of the
accepted interruption facts and owner acceptance. This record is the controlling remediation
instrument. Only minimum registry, index, and `Milestones/STATUS.md` navigation is updated. Decisions
103-108 are not rewritten.

## 5. Workstream A — writer-lease evidence preservation

**Required invariant.** *An existing persisted `held` or structurally invalid lease must never be
overwritten by ordinary writer acquisition merely because the advisory `flock` is free.* A stale
`held` lease is historical evidence. Only the governed
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §3 (**R3**) stale-lease reconciliation
surface may convert it to `released`.

Required semantics for ordinary `CatalogWriter` acquisition:

1. Acquire the exclusive advisory `flock` without altering lease bytes.
2. **Before** any truncate, `pwrite`, replacement, or held-document publication, inspect any
   pre-existing lease through the production strict reader.
3. If no persisted lease existed, ordinary acquisition may proceed.
4. If a structurally valid persisted lease records `released`, ordinary acquisition may proceed.
5. If a structurally valid persisted lease records `held`, **refuse** without changing one lease
   byte — regardless of a dead or live PID, regardless of expiry, and regardless of current `flock`
   availability.
6. If the persisted lease exists but is malformed, unreadable, or structurally invalid, **refuse**
   without changing one lease byte.
7. Voluntary release behaviour for a writer that legitimately acquired the lease is unchanged.

[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) stale recovery is not weakened, and
[Decision 105](decision_105_m3_3_unreadable_writer_lease_fail_closed.md) unreadable-lease fail-closed
behaviour is not weakened.

**Fail-fast namespace check.** Ordinary E0 execution additionally checks the create-once run
namespace **before** writer-lease acquisition. This early check is **not authoritative by itself**
and the accepted under-lease create-once recheck **remains**. Its purpose is narrow: a refused repeat
invocation must not churn the lease document at all.

### 5.1 What was implemented

- `CatalogWriter._acquire_lease` now calls `CatalogWriter._refuse_unacquirable_lease` after taking
  the exclusive `flock` and **before** the first byte is written. The four outcomes are exactly
  items 3-6 above. Nothing is written on any refusal path.
- The strict reader is the existing `read_persisted_lease`, so "acquirable" means the same thing at
  the acquisition gate, at the E0 preflight predicate, and in the governed recovery.
- A lease larger than `_LEASE_READ_LIMIT` (64 KiB, the bound `_read_locked_metadata` already used)
  is refused rather than truncated to fit.
- `e0_execute` refuses a consumed run namespace ahead of `CatalogWriter` acquisition.

### 5.2 Two prior tests encoded the defect and were corrected

`test_old_metadata_without_a_held_lock_is_safely_recovered` asserted that a lease missing
`host_fingerprint` and `state` was safely recovered; item 6 now refuses it.
`test_process_termination_releases_the_advisory_lock` asserted that a killed writer's lease was
recovered by the next acquisition; item 5 now refuses that, which is the F2 sequence itself. Both
were rewritten to assert the new invariant, on the bytes.

## 6. Workstream A — required tests

Proved in `tests/unit/test_d110_lease_evidence_preservation.py` (A1-A7, A11, A12, and the mutation
proof), `tests/unit/test_storage_catalog.py` (A8 at the process level), and
`tests/unit/test_m3_e0.py` (A8 at the E0 surface, A9, A10):

**A1** absent lease permits acquisition · **A2** valid `released` lease permits acquisition, including
the reconciled form · **A3** `held` lease with a free `flock` refuses, bytes unchanged · **A4** dead,
expired, this-host `held` lease still refuses, bytes unchanged · **A5** malformed, unknown-field, and
unknown-state leases refuse, bytes unchanged · **A6** torn and oversized leases refuse, bytes
unchanged · **A7** the D103 reconciliation still recovers `held -> released` and its output is then
acquirable · **A8** a post-interruption execute cannot replace a stale `held` lease before refusal ·
**A9** a consumed namespace refuses before the lease is touched, with bytes and mtime unchanged ·
**A10** the under-lease create-once recheck still decides the race · **A11** the ordinary
acquire/release/reacquire lifecycle is unchanged · **A12** every execution authority ships `None`.

One bounded mutation proof restores the pre-D110 overwrite and requires the provenance regression to
die.

## 7. Workstream B — measured root cause

Measured on the real first planned source, read-only, before any parser edit. The source is a
1.56 GB ZIP holding **985,834** JSON members that expand to **5.71 GB** and parse to approximately
**22.5 million** records and **1,976,418** structural observations.

**Cause 1 — whole-source materialization of parsed output.**
`disclosure_drift/m3/offline_parse.py::_parse_bulk_submissions` built `tuple(iter_members(...))`,
holding every member's decompressed payload, then accumulated every member's `ParseOutcome`, then
`merge_outcomes` copied all of it again. Measured retention was **92,639 bytes per member** across a
bounded 20,000-member prefix — about **91 GB** extrapolated. Streaming the identical parse and
retaining nothing held traced memory **flat** at 859.6 MB from 5,000 to 20,000 members, which
isolates the accumulation as the cause rather than the traversal.

**Cause 2 — unbounded run-level reduction state.** Inside the merged `ParseOutcome`, the structural
observations alone measured **1.46 GB** retained and **1.35 GB** rendered into
`census_parser_runs.summary_json`. That exceeds SQLite's `SQLITE_MAX_LENGTH` of 1,000,000,000 bytes,
so **the merged shape cannot produce a valid row for this source at any memory budget** — an
independent hard failure the memory kill had been masking. Every other run-level accumulator is
bounded in practice: 19 distinct unknown field paths, 0 normalization warnings, 0 duplicate
identities, 14,250 required-field failures, 4,750 quarantined records, 4,675 historical references.

**Cause 3 — preloaded whole-catalog structures downstream of the parse**, on the same load-bearing
call. `materialize_census_associations` preloaded a set of every `accession_plain` (~2.9 GB) and a
map of every accession's blocking-field state (~43 million entries); it retained one tuple per
established accession (~2.9 GB); `_measure_association_totality` built a per-accession cardinality
map and `fetchall`ed every established accession; `_membership_observation_counts` `fetchall`ed every
membership observation; and `CensusCatalog.resolve_persisted_accessions` materialized both the target
list and one `AccessionResolution` per accession for a caller that reads only the count.

**Cause 4 — fixed per-archive index, retained but bounded and not the defect.** `iter_members` builds
the ZIP central directory and its collision-detection sets before the first yield: 1.07 GB RSS /
859.6 MB traced for 985,834 members, flat thereafter. It is proportional to member *count*, is
required by the accepted Decision 051 §4.1 archive defences, and sits inside the §10 ceiling. It is
recorded, not removed.

## 8. Workstream B — required memory invariant

*Peak working memory may depend on a bounded chunk, one record or small batch, and explicitly
bounded reduction state. It must not scale linearly with the full source content or with the total
number of parsed records retained in memory.*

Prohibited on the load-bearing path where they are the cause: reading an entire large source into one
Python object; materializing every parsed row in one unbounded list; retaining all relationship
candidates in an unbounded in-memory structure; building an avoidable full intermediate structure;
retaining a prior source's parse payloads after a source boundary.

**Unchanged**: source disposition vocabulary; canonical association semantics; Decision 094, 099, and
100 totality semantics; deterministic ordering; identity preimages; linkage methodology;
source-selection methodology. This is execution-mechanics remediation, not methodology redesign.

### 8.1 What was implemented

- `_stream_bulk_submissions` yields one member's `ParseOutcome` at a time and retains none.
  `_parse_bulk_submissions` keeps its signature and is now the merged form of that same traversal,
  so `_parse_source` stays total and there is one parsing implementation.
- `CensusCatalog.persist_streamed` writes the same one `census_parser_runs` row with the same
  `parser_run_id` preimage and the same rows, in the same order, into every other table, consuming
  and dropping each part. Run-level duplicate identities are applied in one bounded `UPDATE` at the
  end, because a stream cannot know them while its records are being written and the flag is in no
  identity preimage. Historical references are applied at the end, because their CIK resolution
  reads the lowest-`parsed_record_id` registrant record of the whole observation.
- `STREAMED_SOURCE_IDS` names the sources persisted this way. It currently holds exactly
  `sec_bulk_submissions`. Membership is a statement about scale, not about semantics; every other
  source keeps the merged path unchanged.
- The projection's preloaded accession set and blocking-field map became per-accession indexed
  lookups; the established-accession list became a **second streaming pass** that recomputes a pure
  predicate from evidence the first pass does not write, which keeps §6.4 item 5's "completeness is
  written last" ordering law intact; the totality measurement became one lazy joined cursor; and
  accession resolution gained `count_persisted_accession_resolutions` and a keyset-paged target
  scan. `resolve_persisted_accessions` keeps its signature and behaviour for its M2.2 callers.

### 8.2 The one disclosed output change — MAJOR, requires owner ratification

A streamed run's `census_parser_runs.summary_json` carries every key the merged summary carries, with
the same values computed by the same rule, **except** `structural`: it holds the blocking structural
observations only, bounded by `STREAMED_STRUCTURAL_DETAIL_LIMIT` (1,000), and a new
`structural_detail` key states the scope, the observed total, the blocking total, the retained count,
the limit, and the table where the full detail lives.

This is **not** a preference. The merged array for this source is 1,976,418 entries rendering to
about 1.35 GB in a single cell, which exceeds SQLite's 1 GB cell limit outright — the merged shape
cannot be written at all. No detail is lost: every structural observation, blocking or not, is
already persisted individually in `census_structural_observations`, and the summary's copy was always
a duplicate. No existing fixture pins the array. **The owner is asked to ratify this shape**; it is
recorded here rather than absorbed silently because `census_parser_runs` is governed state.

## 9. Synthetic memory validation

Deterministic synthetic regression coverage in `tests/unit/test_d110_bounded_parse_memory.py` drives
**production** parsing code end to end over materially different input volumes. Acceptance
requirement: a tenfold input volume must not produce approximately tenfold peak memory. Measured with
`tracemalloc` and, separately, with process RSS in a subprocess, because ZIP decompression and SQLite
allocate outside Python's allocator. Existing exact-output fixtures remain byte and identity
equivalent, and row-for-row equivalence against the merged path is asserted directly.

## 10. Disposable real-source canary

After Workstream A tests pass, Workstream B implementation passes its targeted tests, and static
checks pass, a bounded diagnostic canary against **real input artifacts** is authorized — but never
against the governed real catalog or run namespace. It uses read-only real source artifacts, a
disposable catalog derived from the accepted pre-E0 backup, and a disposable temporary directory
outside the repository. No `m3_3_e0_offline_parse_v3` namespace. No mutation of the operational
catalog. No mutation of v1 or v2.

The first canary target is the deterministic first planned source — the same source on which v2 spent
approximately 63 minutes without reaching a durable boundary.

**Owner safety ceiling for this 8 GiB host: peak E0 diagnostic-process RSS ≤ 2.5 GiB.** If exceeded,
terminate only the disposable diagnostic process, record the failure, and stop. **If the first source
has not completed within 20 minutes** after the corrected implementation, terminate only the
disposable diagnostic process, record the measured state, and stop. This diagnostic termination
authority does **not** apply to governed E0 execution, and no further optimization follows without an
owner ruling.

## 11. Multi-source canary

Only if the first-source canary passes: one disposable sequential canary over three deterministic
planned sources — the first, one median-size, and the largest by artifact byte length (the next
largest distinct source if the largest is already one of the other two). Same disposable-only
constraints. Requires all three to finish, peak RSS ≤ 2.5 GiB, no monotonic retained-memory growth
across completed source boundaries, prior-source payloads reclaimable, reconciling output and
disposition semantics, no network, and no real-state mutation. Not extended beyond three sources
under this record.

## 12. Validation

Targeted tests during edits. At completion: the Workstream A regression family; the Workstream B
parser and output regression family; the synthetic memory scaling proof; the first-source real
disposable canary; the three-source disposable canary; touched-file Ruff; format check; mypy; the
governance, link, and reference checks; one bounded mutation proof for the lease overwrite; and the
non-vacuity proof for the memory regression. Then exactly **one** final `make check-fast`, with its
first-run output captured. A failure stops the task rather than starting another remediation cycle.

## 13. Real-state nonmutation

Proved unchanged before and after all diagnostics: operational catalog file identity and logical
digest; observation-set digest; migration chain and head `0015`; WAL governed state; the v1 and v2
ledgers and directory contents; both backups; writer-lease identity and state except where an
accepted read-only operation necessarily reads it; and all three execution authorities at `None`. No
diagnostic under this record may create a real E0 run namespace.

## 14. Commit and publication

If every required gate passes, one local remediation and governance commit. **No push. No tag.**
Return to GPT-5.6 Sol for owner acceptance before any successor activation.

## 15. Progress rule

No extra reviewer, no architecture audit, no generalized optimization pass. Only the two accepted
MAJORs are fixed; MINOR and OBSERVATION findings do not expand scope. If either MAJOR cannot be
closed within the bounded task, the measured blocker is returned instead.

## 16. What this record does not do

It authorizes no execution. `M3_3_E0_EXECUTION_AUTHORITY`,
`PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` are all `None` and
are not reopened by this record, by a passing remediation, or by a passing canary. A successor E0
generation still requires **both** a new owner instrument **and** a reviewed source change, exactly
as [Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §3 (**R105**) requires.
