# Decision 112 — The Compact E0 Evidence Contract, and the Measured Capacity Verdict

```text
STATUS: ACCEPTED — OWNER EVIDENCE-CONTRACT RULING; IMPLEMENTED; CAPACITY GATE FAILED
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D112_COMPACT_E0_EVIDENCE_CONTRACT
CLOSES: D111 §5 (MAJOR) — for census_accession_observations and census_parsed_records
RETURNS: ONE BLOCKER — the projected complete 76-source working state does not fit this host
ENTRY_HEAD: ab4398afc60f3d85f4e0e3ba4b161221e9bb6578
COMPACT_EVIDENCE_CONTRACT: e0-compact-evidence/1
COMPACT_EVIDENCE_SCHEMA_VERSION: 1
OPERATIONAL_MIGRATION_HEAD: 0015
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
FIRST_SOURCE_CANARY: NOT RUN — the disk gate failed at the measured projection (§6)
THREE_SOURCE_CANARY: NOT RUN — gated on the first-source canary
```

This record carries the owner's evidence-contract ruling on
[Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md) §5, the
implementation of it, and the measured capacity verdict that implementation produced.

It changes **what E0 persists**, and nothing else. It writes no research code, changes no frozen
research definition, reads no outcome value, applies no migration, contacts no network, and
redesigns no methodology. Decisions 091–111 remain binding on every point they name, and Decisions
103–110 are **not rewritten**.

**It grants no execution authority.** All three activation constants stay `None`.

## 1. The owner's evidence-contract ruling

For E0 the **frozen immutable source artifact is the authoritative complete raw evidence**. E0's
durable relational evidence exists to prove complete deterministic traversal, parser disposition,
canonical accession identity, canonical registrant identity, canonical accession-to-registrant
association, malformed and quarantined and conflicting evidence, structural failure evidence,
lineage and provenance, replayability, and exact source and result identities.

E0 is **not** required to reproduce the entire raw JSON archive field by field in SQLite when those
ordinary field values are already preserved in the immutable source artifact and are
deterministically reconstructible. Therefore:

> **One SQLite row per ordinary raw field observation is no longer required for E0 run-local
> evidence.**

The ruling is deliberately limited to **E0 successor execution**. It does not rewrite historical M2
acquisition evidence, and it does not reach any table other than `census_accession_observations` and
`census_parsed_records`.

## 2. What the contract is, in code

`src/disclosure_drift/m3/compact_evidence.py` states the contract once, so the writer and the reader
obey the same rule and a test can hold them to it. It is **off by default** — `CensusCatalog` takes
`compact_evidence=FULL_EVIDENCE` unless a caller states otherwise — which is how §1's scope limit is
enforced in code rather than promised in prose.

**2.1 An accession field observation is omitted only when it is inert or exactly reconstructible.**

* *Ungoverned fields are inert.* `CANONICAL_FIELD_BY_SOURCE_FIELD` is the complete set of
  source-native field names any accepted consumer reads: Decision 012 resolution drops every other
  name before looking at it, and the Decision 094 §6.2 membership projection selects only `cik` and
  `cik_padded`. On the real first source that is about **eleven of every seventeen** rows written,
  read back, and discarded.
* *A governed field's canonical column is the observation.* `census_accessions` already stores each
  governed value together with the provenance triple the observation carried —
  `source_observation_id`, `parsed_record_id`, `first_observed_at_utc` — and the observation
  identifier is a pure function of those. Where the raw value round-trips through that column
  exactly, the row duplicates the canonical row.

**2.2 Everything that does not round-trip is materialized, deliberately.** A malformed date, a value
normalisation would rewrite or drop, a blank membership rendering, and every governed field of a
second or competing witness all fail the round-trip and are written individually. That is the ruling's required
exception evidence, not an exception to it. **When a rival witness appears the incumbent's rows are
back-filled first**, because the accepted conflict pass marks a row only when it can see a sibling
that differs — writing the newcomer alone would leave a disagreement with one side missing.

**2.3 The reader reconstructs.** `reconstructed_observations` emits, for each governed field whose
canonical column is non-NULL, the value with the same deterministic identifier, the same
`raw_value_json` rendering, and the same provenance the omitted row carried. Decision 012 resolution
and the Decision 094 membership projection therefore receive an input stream they cannot distinguish
from the stored one, re-sorted on the same key the single cursor ordered by.

**2.4 The redundant accession payload is projected.** The full payload of an accession-class
`census_parsed_records` row is read by **nothing**: the two readers of that column both restrict
themselves by native identity (`registrant:` for historical references, `index_row:` for full-index
materialization), and accession normalization reads the in-memory parsed record. The row stays —
it is the identity, the provenance, and the foreign-key target the canonical accession row names —
and its `record_sha256` still digests the **complete** raw record, so identity does not move. Its
payload is reduced to the governed projection and carries `__evidence_contract__` so the omission is
self-describing rather than silent.

**2.5 The member manifest and completeness digest.** `CompactSourceEvidence` records,
during the one traversal, each member's ordinal, name, payload length and SHA-256, parsed-record
counts by class, quarantine and structural-failure counts, omitted and materialized observation
counts, its projection digest, and its disposition — and folds every record's normalized governed
projection, canonical relation contribution, and exception contribution into one running
`ProjectionDigest`. **No parsed-record identifier, observation identifier, or timestamp enters the
digest**, because those are properties of *this* write rather than of the evidence, and a replay
must reach the same digest without reproducing them. Both live in a **versioned run-local sidecar**
beside the working catalog: migration `0016` stays reserved, the operational catalog stays at head
`0015`, and the working catalog stays a byte-for-byte schema twin of it.

**2.6 One further executability defect, found by measuring and fixed here.**
`CensusCatalog._insert_record` derived a record's run-level duplicate flag by scanning
`outcome.duplicate_identities` **per record**. That is the same
per-record-over-run-level-state shape [Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md)
§3 removed from two other derivations, in a path it did not reach: it is invisible on the streamed
bulk path, where the outcome is one member, and quadratic on the merged path, where the outcome is
the whole source. Measured on one real median `company.idx` quarter — 252,622 records against 62,266
duplicate identities — that is **15.7 billion string comparisons for one of seventy quarters**. The
source did not finish in **twelve minutes** and was terminated. Deriving the set once and asking for
membership answers the identical question: after the fix the same quarter completes in **15.8
seconds**, and the seventy quarters go from more than fourteen hours to about eighteen minutes. No
row's value moves, which the equivalence proofs in §3 hold.

## 3. Proofs

Held in `tests/unit/test_d112_compact_evidence.py`, against a fixture built to break the rule rather
than to agree with it — a joint filing whose witnesses agree, a joint filing whose witnesses
disagree on `form`, a malformed `filingDate`, a blank `reportDate`, a whitespace-padded `form`,
absent optional fields, ungoverned fields, and a `company.idx` quarter binding a second registrant.

* **Equivalence.** Twelve governed tables compared row for row over every non-timestamp column,
  including `census_accession_field_resolutions`' winning and competing observation identifier lists
  — which name observations the compact catalog never stored. `census_parsed_records` is identical
  on every column but the payload. Observation rows are asserted a **strict subset**, so a compact
  path that wrote a *different* row fails even if it wrote the same number.
* **Sufficiency.** The D093 §6 resolver runs against a connection whose authorizer **denies**
  `census_accession_observations` and `census_parsed_records` outright, so a resolver that reached
  for one raises rather than quietly succeeding. The denial harness is itself tested. Five
  registrant/form/date cases resolve identically to the full-observation catalog, and a non-vacuity
  test requires more than one classification to occur.
* **Replay.** Two separately built worlds, two archives on disk, two traversals sharing no
  object, reach the same completeness digest; changing an *omitted* ordinary value moves it; member
  order is bound.
* **Non-vacuity.** Two mutation proofs: omitting the exception rows must break a governed result,
  and a lossy reconstruction must break the field resolutions. Both do.

## 4. Measured effect, on real data

Real first planned source, real prefixes, disposable working catalogs, operational catalog opened
strictly read-only.

| | 1,500 members | 6,000 members | ratio |
|---|---|---|---|
| distinct accessions | 346,852 | 1,083,569 | 3.124× |
| parsed records | 351,201 | 1,113,662 | |
| **accession observation rows** | **30,722** | **222,847** | |
| relation rows | 349,955 | 1,108,404 | |
| parse+resolution layer bytes | 2,096,242,688 | 6,675,771,392 | **3.185×** |
| **bytes per accession** | **6,043.6** | **6,160.9** | 1.019× |
| peak RSS | 1.073 GiB | 1.094 GiB | |
| peak WAL / post-checkpoint | — / 0 | 288.6 MB / 0 | |

**Durable growth is linear, not superlinear** — 3.185× the bytes for 3.124× the
accessions across a 3.1× scale-up, which is B-tree depth, not a scaling defect. Memory is flat and
the write-ahead log is bounded and fully reclaimed.

`census_accession_observations` falls from a projected **204.2 GB** to **110.5 bytes per accession**
— about **2.4 GB** for the whole first source, a **98.8 %** reduction, with every conflicting,
malformed, ambiguous, and second-witness row retained.

## 5. Where the bytes now are

Per accession, measured at 6,000 members:

| Component | B/accession | Share |
|---|---|---|
| `census_accession_field_resolutions` + its index | 3,897.3 | 63.3 % |
| `census_parsed_records` + its two indexes | 1,156.4 | 18.8 % |
| `census_accessions` + its two indexes | 414.3 | 6.7 % |
| `census_accession_registrants` + its index | 283.1 | 4.6 % |
| `census_accession_cohort_resolutions` + its index | 275.5 | 4.5 % |
| **`census_accession_observations` + its two indexes** | **110.5** | **1.8 %** |
| everything else | 23.8 | 0.4 % |
| **total** | **6,160.9** | |

**The resolution layer is now 67.7 % of everything E0 persists**, and it is outside this ruling:
names `census_accession_observations` and `census_parsed_records` and no other table.

Two of the eight `census_accession_field_resolutions` rows written per accession —
`amendment_relationship` and `submitter_cik` — are `absent` for **100.0 %** of accessions in the
measured prefix, each carrying the constant text "no observation of this field was recorded" for a
field this source never carries. That is **43.0 million rows** and about **22.4 GB** on the first
source alone.

## 6. The capacity verdict

Projected from the measured slope, using D111's measured source totals (985,479 members;
22,973,187 parsed records; 21,993,042 accession records), the measured distinct-accession ratio
0.97759 giving **21,500,264 distinct accessions**, and the measured full-index row density giving
**~18,376,265 index rows** across the seventy quarters.

| Component | Basis | Projected |
|---|---|---|
| Source 1, compact, incl. resolution layer | 21,500,264 × 6,160.9 B | **132.5 GB** |
| 70 `sec_full_index_company` parsed records | 18,376,265 × 1,288.5 B | **23.7 GB** |
| 70 `sec_full_index_company` accession observations | 18,376,265 × 3 × 537.6 B | **29.6 GB** |
| run-local evidence sidecar | 985,479 member rows | ~0.3 GB |
| base catalog and five small sources | measured | ~0.5 GB |
| **complete 76-source working state** | | **~186.5 GB** |
| E0 backup (taken from the *pre*-E0 catalog) | measured | 0.36 GB |
| peak transient write-ahead log | measured, batch 250 | 0.29 GB |
| run evidence and recovery headroom | | ~0.4 GB |
| **total required** | | **~187.6 GB** |
| free disk on this host | measured, scratch cleared | **86.3 GB** |
| **reserve** | | **≈ −101 GB** |

**The owner ruling requires at least 15 GiB of reserve and says STOP below it. The reserve is negative by about
101 GB, so the full first-source canary was not run and the three-source canary, which is
gated on it, was not reached.** Starting a parse that provably cannot complete would have filled the
host's system volume rather than produced evidence.

**The gate fails on source 1 alone**, at 132.5 GB against 86.3 GB free, so no refinement of the
full-index figure changes the verdict.

## 7. What the owner has to decide

The authorized compaction is implemented and does exactly what it was asked to do. It is not
sufficient, and the two remaining costs are outside it. Measured, so the ruling can be made on
numbers:

1. **The Decision 012 resolution layer — 4,172.8 B/accession, ~89.7 GB on source 1.** Every
   accession receives eight field-resolution rows plus one cohort-resolution row whether or not any
   of them records a disagreement. For a single-witness accession the resolution is a pure function
   of the canonical row. Two of the eight — `amendment_relationship` and `submitter_cik` — are
   `absent` for **100.0 %** of accessions in the measured prefix, each carrying the constant text
   "no observation of this field was recorded" for a field this source never carries: **43.0 million
   rows and about 22.4 GB** on source 1 alone. Applying §1's own principle — persist an entry only
   where it carries information the canonical row does not already carry — would remove most of the
   layer, but it is Decision 012 governed evidence and this record does not touch it.
2. **The full-index corroboration layer — ~29.6 GB of accession observations across 70 quarters.**
   A `company.idx` row that agrees with the canonical row cannot change a Decision 012 resolution
   (full index is authority level 3, below entity submissions at level 2) and adds no co-registrant
   when its CIK is already the registrant. It is not information-free: its *presence* is what
   distinguishes a corroborated association from an uncorroborated one, and the accepted totality
   counts that. Compacting it therefore needs somewhere to record corroboration, which is a schema
   question and so a migration question.

**With both, the projected working state falls to about 67.2 GB and the required reserve becomes positive
at about 18.0 GB** — above the 16.1 GB the rule requires, but by under 2 GB. That is a real margin
and a thin one: it assumes every full-index row binds, and it leaves nothing for growth. A third
lever (the full-index parsed record retains the complete `raw_line`, roughly a third of its payload)
or more disk would make it comfortable rather than marginal. Neither ruling is authorized here.

## 8. What this record does not do

No canary was run against the real first source. No real catalog was mutated: the operational
catalog was opened strictly read-only on every path, and its bytes, logical digest, observation-set
digest, migration chain at head `0015`, write-ahead-log state, and writer lease are unchanged. No
namespace was created, no migration was applied, no v3 exists, and all three execution authorities
remain `None`.

## 9. Governance actions this record directs

The owner ruling that produced this record also directed the governance work around it, so those
actions are recorded here rather than left to a commit message:

1. **Publish the accepted D111 candidate** `ab4398afc60f3d85f4e0e3ba4b161221e9bb6578` by ordinary
   push. No force, no rebase, no amend, no tag. Done: `ca12b86..ab4398a` on `origin/main`.
2. **Create the missing Decision 111 record.** Done —
   [Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md).
3. **Create this record**, carrying the owner's evidence-contract ruling.
4. **Update the minimum registry, index, and STATUS navigation** — and nothing beyond it.
5. **Do not rewrite Decisions 103–110.** None is modified.

The D112 implementation commit is local and is not pushed, and no tag is created.
