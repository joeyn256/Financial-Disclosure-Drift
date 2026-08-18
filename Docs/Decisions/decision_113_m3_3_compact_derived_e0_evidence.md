# Decision 113 — Compact Derived Resolution and Corroboration Evidence, and the Final Local-Capacity Gate

```text
STATUS: ACCEPTED — OWNER EVIDENCE-CONTRACT RULING; IMPLEMENTED; CAPACITY GATE FAILED
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D113_COMPACT_DERIVED_EVIDENCE
CLOSES: D112 §7 items 1 and 2 — the Decision 012 resolution layer and the full-index corroboration layer
RETURNS: ONE BLOCKER — LOCAL_CAPACITY_INSUFFICIENT_AFTER_D113
ENTRY_HEAD: 3a17c5d20465147e77ee29c188bec0391cac9676
COMPACT_EVIDENCE_CONTRACT: e0-compact-evidence/2
COMPACT_EVIDENCE_SCHEMA_VERSION: 2
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
FIRST_SOURCE_CANARY: NOT RUN — the §15 capacity gate failed at the measured projection
THREE_SOURCE_CANARY: NOT RUN — gated on the first-source canary
REAL_REPLAY_PROOF: NOT RUN — gated on the first-source canary
```

This record carries the owner's second evidence-contract ruling, the implementation of it, the
correction of the E0 capacity predicate, and the measured verdict that implementation produced.

It changes **what E0 persists** and **what a future E0 preflight requires**, and nothing else. It
writes no research code, changes no frozen research definition, reads no outcome value, applies no
migration, contacts no network, and redesigns no methodology. Decisions 091–112 remain binding on
every point they name, and Decisions 103–112 are **not rewritten**.

**It grants no execution authority.** All three activation constants stay `None`.

## 1. What the owner ruled

Decision 112 applied one principle to E0's raw observation layer — *persist an entry only where it
carries information the canonical row does not already carry* — and measured what it left behind:
the Decision 012 resolution layer at 4,172.8 bytes per accession, **67.7 %** of everything E0
persists, and the full-index corroboration layer at about 29.6 GB across seventy quarters. Both were
outside D112's own scope, which named `census_accession_observations` and `census_parsed_records` and
no other table.

D113 extends the same principle to both, and to nothing else:

1. **A Decision 012 resolution row is not persisted when its complete governed content is a
   deterministic pure function of already-persisted canonical evidence.** Its content is *defined* by
   replaying the accepted resolver over the reconstructed observation stream, under the frozen
   contract version. The rule is named `DEFAULT_CANONICAL_RESOLUTION`.
2. **A `company.idx` row that corroborates an already-canonical accession is represented by the
   parsed record the traversal already wrote**, rather than by three further observation rows that
   repeat it, and that record's duplicated `raw_line` payload is dropped.
3. **Neither compaction may lose a disagreement.** Conflicts, ambiguity, malformed values, competing
   witnesses, authority-level choices, prior-cohort history, and anything that changes association
   totality stay explicit.

The physical number of resolution and corroboration rows is allowed to differ. The **logical**
governed result is not.

## 2. The contract, in code

`src/disclosure_drift/m3/compact_evidence.py` states both rules once, so the writer and the reader
obey the same rule and a test can hold them to it. The contract version moves to
**`e0-compact-evidence/2`**, schema version 2. `/2` is `/1` **plus** these two rules and changes none
of `/1`'s: the observation omission rule, the parsed-record projection, and the projection digest are
exactly what D112 accepted. `/1` is retained as a named historical constant so the version string is
never reused for different semantics. No durable evidence anywhere carries `/1`, because D112's own
capacity gate stopped before any canary.

Both paths remain **off by default** — `CensusCatalog` takes `compact_evidence=FULL_EVIDENCE` unless
a caller states otherwise, and `_materialize_full_index_registrants` takes `compact=False` — which is
how the scope limit is enforced in code rather than promised in prose.

## 3. Scope

Authorized and implemented: compact Decision 012 field and cohort resolution evidence; compact
full-index corroboration evidence; removal of the duplicate full-index `raw_line` payload while its
exact immutable-source provenance and hash are retained.

Not touched: the Decision 012 resolution methodology, authority ordering, canonical values, canonical
association semantics, the Decision 093 linkage methodology, source selection, and the disposition
vocabulary. Migration `0016` is not applied. No E0-v3 is created or executed. The operational catalog
is not mutated. No network, SEC, or HTTP access occurs.

## 4. The implicit default resolution

A resolution row is omitted only when the resolution the reader will rebuild is
**indistinguishable** from the one the resolver produced. That is decided by comparison, not by a
list of cases: `is_default_resolution` compares whole `AccessionResolution` hashes, which cover every
governed component of both the field resolutions and the cohort consequence and exclude the wall
clock.

Deciding it that way is what makes §5 safe without enumerating §5. A competing value, a conflict,
ambiguity, a malformed alternative, an authority-level choice between different witnesses, a
prior-cohort history, and an approved 2024 transition each make the two differ, and each is therefore
materialized without needing its own clause.

The fast path is the ordinary one: an accession carrying no stored observation, no prior filing date,
and no approval resolves from the reconstruction alone, so the two inputs are the same list and the
second resolve is skipped. On the real first planned source that is **99.35 %** of accessions.

**The reader reconstructs.** `census.reconstructed_accession_resolution` replays the accepted
resolver over the observation stream the canonical accession row and the full-index corroboration
assertions imply. It is asked *after* canonical projection and *after* the association projection,
which is the state a real reader meets; both rewrite `census_accessions`, and the reconstruction is
proved to reach the row that was not written from that later state rather than from the state the
resolution pass saw.

## 5. What stays materialized

Everything that carries information beyond the canonical row: multiple witnesses, competing values,
conflict, ambiguity, malformed alternatives, an authority-level choice between different witnesses,
provenance disagreement, any non-default resolution, and any downstream-governed fact not exactly
reconstructible. A disagreement is never compacted away.

The rule is applied **per accession** rather than per field. An accession that carries any exception
keeps its whole resolution — always-absent fields included — because the components that make it an
exception (`prior_filing_cohorts`, an approved transition) are recorded in the resolution and nowhere
else.

## 6. Always-absent fields

`submitter_cik` and `amendment_relationship` are `absent` for **100 %** of accessions because no
source-native field name maps to either: `CANONICAL_FIELD_BY_SOURCE_FIELD` is the complete map and
neither is in its image, so no observation of either can exist and no resolver branch but `absent` is
reachable. That is a property of the source class, and the contract states it once as
`ALWAYS_ABSENT_RESOLUTION_FIELDS` rather than writing 43.0 million rows to repeat it.

It is deliberately **not** a special case in the omission rule. An accession that unexpectedly
carried one would differ from its reconstruction and would be materialized by the general rule, which
is what the ruling's final paragraph on this point requires. The declared set is held in step with
the field map by a test that derives it.

## 7. Cohort resolution

The same rule, and the same mechanism. A cohort consequence that is an exact deterministic function
of the canonical row and the frozen cohort definitions is not written; an exceptional or non-default
one is. Because `is_default_resolution` compares the whole `AccessionResolution`, the cohort
consequence and the field resolutions are omitted or materialized **together**, so no accession can
end up with one half of its resolution durable and the other half implicit.

The frozen cohort definitions enter through the accepted resolver and its policy version, which the
resolution digest binds.

## 8. The resolution-completeness digest

`ResolutionDigest` folds a canonical line per accession, in ascending accession order, over the
**full logical** Decision 012 result — implicitly reconstructed and explicitly materialized alike.
Physical row omission cannot move it, which is what makes it the evidence that omission changed
nothing: the full-observation path and the compact path fold the same lines and reach the same value.

Every ingredient is the resolver's own output over evidence derived from the frozen artifact: status,
normalized value, authority class, correction reference, reason codes, materiality, blocking state,
the resolver's own detail text, and the winning and competing **counts**. Observation identifiers
themselves are excluded for the reason `ProjectionDigest` excludes parsed-record identifiers — they
are properties of *this* catalog's source registration rather than of the evidence, and a replay in a
separate world must reach the same digest without reproducing them. The counts keep the structural
fact, how many witnesses competed, inside the digest.

## 9. Compact full-index corroboration

Corroboration **presence** is governed evidence; the heavyweight duplicate representation is not.

For a row that merely corroborates an already-canonical accession, the assertion is the
`census_parsed_records` row the traversal already wrote. It carries accession identity
(`accession_plain`, and the native identity built from it), the quarter's source identity
(`source_observation_id`), the form, the filing date, the CIK, the deterministic source-row identity
and provenance (`parsed_record_id`, `line_number`, `record_index`), and a `record_sha256` over the
**complete** raw row. Corroboration presence is the accession's existence in `census_accessions`,
which the materialization checks per row. Nothing is duplicated to say it again.

`census.\_corroboration_rows` and `offline_parse.\_corroborated_membership_rows` restore from that
assertion the observations the accepted R23 materialization would have written — the same
deterministic identifiers, the same renderings, the same provenance — so Decision 012 resolution and
the Decision 094 §6.2 membership projection receive input streams they cannot distinguish from the
stored ones. `CorroborationDigest` folds every assertion and its disposition into one replay binding.

Two honest details, stated rather than buried. The reconstruction's `observed_at_utc` is the parsed
record's own `recorded_at_utc` rather than the materialization pass's run-level clock, because a
reconstruction must read a persisted value and not a wall clock it cannot see; it feeds nothing but
the relation row's two audit timestamps, and no classification, resolution, or membership verdict
reads it. And a row bound to an accession the authoritative layer does not carry is **not**
reconstructed, exactly as **R23** §5.1 writes no observation for one: reconstructing it would hand
the §6.4 projection a group for an accession that does not exist and increment `orphans`, which is a
totality difference the full-observation path never produces.

## 10. Full-index exceptions

A row is an exception, and keeps its observation rows, when its CIK is not already the canonical
registrant, when its form or filing date disagrees with the canonical value, or when the canonical
registrant, form, or filing date is not yet established. Each of those can change a Decision 012
resolution, the association set, or the totality classification.

Requiring the canonical values to be *present* is not caution for its own sake: an accession whose
canonical column is NULL cannot reconstruct the observation the omitted row carried, so omitting it
there would not be reconstructible.

A parsed row the parser recorded `problems` for is unchanged in every respect — it establishes
nothing, is retained as quarantined evidence, and is never repaired.

## 11. The run-local schema

Migration `0016` stays reserved and the operational catalog stays at head `0015`. The run-local
sidecar moves to schema version 2 and gains two tables: `compact_resolution_evidence`, carrying the
implicit rule's name, the always-absent field set, the implicit and explicit counts, the omitted and
materialized row counts, and the completeness digest; and `compact_corroboration_evidence`, carrying
each quarter's row counts, its corroborating/exception split, and its corroboration digest. Both
enter `CompactEvidenceSidecar.identity()`, so both are inside the freeze identity D112 §8 requires.

Historical D112 evidence semantics are not altered. `/1`'s rules are unchanged and its version string
is not reused.

## 12. Information equivalence

Proved in `tests/unit/test_d113_compact_derived_evidence.py`, against the hostile D112 fixture
extended with a corroborating index row, a co-registrant index row, and an index row that binds to
nothing.

* **Logical resolution equality.** Every accession's complete field and cohort resolution is rendered
  from the persisted rows where they exist and from the reconstruction where they do not, and the two
  contracts agree exactly — status, value, authority, both identifier lists, reason codes,
  materiality, blocking state, the resolver's detail text, cohorts, prior cohorts, and the cohort
  row's reason-code union. That is strictly stronger than the physical row comparison it replaces: it
  holds over the same columns **and** requires the omitted rows to be rebuildable from what remains.
* **One digest.** The resolution-completeness digest is identical under both contracts, and replays
  in a third, independently built world.
* **Association and totality.** `census_accessions`, `census_accession_registrants`, and the accepted
  Decision 094 §9.5 totality object are compared directly, counter for counter, and are identical —
  which is what catches an over-produced reconstruction.
* **R52 sufficiency, proved by removing the fallback.** The D093 §6 linkage resolver answers every
  classification against a connection whose authorizer **denies** `census_accession_observations`,
  `census_parsed_records`, `census_accession_field_resolutions`, and
  `census_accession_cohort_resolutions` outright. The denial harness is itself tested against each of
  the four.

One difference is deliberate and is not governed output: the two audit timestamps on a relation row
that a corroborating index row contributes to. §9 states why.

## 13. Non-vacuity

Four mutations, each of which must break something, and each of which does:

* **A.** Applying the default rule where §5 forbids it — removing a conflicting accession's
  resolution rows **and** the exception observations that carry the disagreement — makes the
  reconstruction report `resolved` where the truth is `unresolved`, and the logical resolution set no
  longer matches. A companion test holds the predicate itself: a prior-cohort history and a conflict
  each make `is_default_resolution` refuse. What is *not* claimed is that omitting a conflicting
  accession's resolution rows alone is lossy — it is not, because D112's exception observations carry
  the disagreement — and the predicate refuses such an accession anyway, because `prior_filing_cohorts`
  and an approved transition live nowhere else.
* **B.** Deleting a corroborating index row's parsed record — the assertion itself — removes the
  accession's full-index membership, so the member is uncorroborated and the association set can no
  longer be established.
* **C.** Altering a canonical value an implicit resolution is reconstructed from moves the
  completeness digest.
* **D.** Altering the omitted `raw_line` moves the record's content digest, which the corroboration
  digest folds, so the replay binding moves with it.

## 14. Measured effect, on real data

Real first planned source, real prefixes, disposable working catalogs in scratch, the operational
catalog opened strictly read-only and immutable, batch size 250 with write-ahead-log truncation at
each boundary.

**Component storage, at the same real prefix, under the two contracts.** 1,500 real members of the real first planned source, 346,852 distinct accessions, no index quarter, so the two columns differ only by the compaction.

| Component | full-observation B/accession | compact B/accession | change |
|---|---|---|---|
| `census_parsed_records` + 4 indexes | 1,412.3 | 1,254.9 | **−11.1 %** |
| `census_accessions` + 2 indexes | 416.6 | 416.6 | unchanged |
| `census_accession_registrants` + 2 indexes | 277.6 | 277.6 | unchanged |
| `census_accession_observations` + 2 indexes | 9,725.2 | 47.9 | **−99.5 %** |
| `census_accession_field_resolutions` + 3 indexes | 4,082.4 | 33.3 | **−99.2 %** |
| `census_accession_cohort_resolutions` + 1 index | 274.5 | 2.7 | **−99.0 %** |
| everything else | 24.2 | 24.2 | unchanged |
| **total** | **16,212.7** | **2,057.2** | **−87.3 % (7.88×)** |

The two runs reach the **same resolution-completeness digest** (`8a231fb3440f8e12…`) over 346,852 real accessions, of which 344,587 — 99.35 % — have no resolution row at all in the compact catalog. That is §12's equivalence claim on real data rather than on a fixture. Wall time falls from 817 s to 168 s (4.9×), peak RSS is flat at 1.072 GiB, and the write-ahead log peaks at 99.7 MB and is fully reclaimed.

**Scale, under the compact contract.**

| | 1,500 members | 6,000 members | ratio |
|---|---|---|---|
| distinct accessions | 346,852 | 1,083,569 | 3.124× |
| durable bytes | 713,535,488 | 2,344,411,136 | 3.286× |
| **bytes per accession** | **2,057.2** | **2,163.6** | 1.052× |
| implicit resolutions | 344,587 (99.35 %) | 1,069,574 (98.71 %) | |
| peak RSS | 1.072 GiB | 1.071 GiB | |
| peak WAL / post-checkpoint | 99.7 MB / 0 | 327.8 MB / 0 | |

Durable growth stays linear — 3.286× the bytes for 3.124× the accessions — which is B-tree depth, not a scaling defect. Memory is flat and the write-ahead log is bounded and fully reclaimed.

**The full-index layer**, measured as the difference one real `company.idx` quarter makes to a real catalog: 206,600 parsed rows for 250.8 MB, **1,213.9 B per index row**. Decision 112 measured the same layer at 1,288.5 B per parsed record plus three accession observations at 537.6 B each — 2,901.3 B per row — so D113 removes **58.2 %** of it. The figure is conservative rather than optimistic: at this prefix the submissions layer carries only the first 6,000 members, so just 7,194 of the quarter's 206,600 rows reach the corroborating disposition and the measured bytes still include 16,872 exception observations that a complete run would mostly resolve into corroborations instead.

## 15. The capacity verdict

Projected from the measured densities above, using D111's measured source totals and D112 §6's measured distinct-accession and full-index row counts.

| Component | Basis | Projected |
|---|---|---|
| Source 1, compact, every layer | 21,500,264 × 2,163.6 B | **46.5 GB** |
| 70 `sec_full_index_company` quarters | 18,376,265 × 1,213.9 B | **22.3 GB** |
| base catalog and five small sources | measured | 0.5 GB |
| **complete 76-source working state** | | **69.3 GB** |
| pre-E0 backup | measured | 0.36 GB |
| peak write-ahead log | measured | 0.29 GB |
| run evidence and recovery headroom | measured | 0.40 GB |
| **total working state and overhead** | | **70.4 GB** |
| free disk on this host | measured, scratch cleared | **85.8 GB** |
| **projected reserve** | | **15.4 GB = 14.36 GiB** |
| **required reserve** | D113 §15 | **25 GiB = 26.84 GB** |

**The projected reserve is 14.36 GiB against the 25 GiB the ruling requires — short by 11.4 GB.** The classification is therefore **`LOCAL_CAPACITY_INSUFFICIENT_AFTER_D113`**, and §15's own rule applies: stop, do not compact further, and treat additional local storage as the next owner decision rather than another evidence redesign.

Two things are worth stating precisely rather than leaving to inference. First, the compaction **worked**: the same projection under D112's contract was ~186.5 GB, and it is now 69.3 GB — a 63 % reduction, and it would have cleared D112 §6's own 15 GiB bar. It does not clear the 25 GiB bar §15 raised for actual v3 authorization. Second, the shortfall is not in anything D113 reaches: after this ruling the two largest remaining costs are `census_parsed_records` at 1,254.9 B/accession (~27 GB on source 1) and the full-index parsed records, and both are the record's **identity and provenance rows**, not payload — the layer D112 already projected and this record already stripped `raw_line` from. There is no third compaction of comparable size left that does not start deleting identity.

The accepted requirement's identity is `791618e03a8ed6028d6b0ba70f1fca4473d2434b52e99ec1ddddaec97dba2b31`, and the corrected preflight (§19) refuses on this host today with exactly these numbers.

## 16. The first real-source canary

**NOT RUN.** §15's projection failed, and the ruling's own stop rule is that no further semantic
compaction follows a failed projection. Starting a parse that provably cannot complete would have
filled the host's system volume rather than produced evidence.

## 17. The three-source canary

**NOT RUN.** It is gated on the first-source canary.

## 18. The real replay proof

**NOT RUN.** It is gated on a completed real source. The equivalent proof over the synthetic world is
held in §12: the resolution-completeness digest, the corroboration digest, the member manifest, and
the compact-evidence identity all replay in an independently built world that shares no state with
the first.

## 19. The corrected capacity predicate

The E0 successor preflight asked whether free space covered **three copies of the current catalog
plus a gibibyte**. The current catalog is the pre-E0 one — about 0.36 GB, because E0 has never run —
so that predicate admitted any host with roughly 2.1 GB free. A predicate that passes on a host which
provably cannot finish is worse than none: it converts a refusal into a partial run that fills the
system volume.

`src/disclosure_drift/m3/capacity_plan.py` replaces it with a requirement computed from measured
densities and the *planned* work: each component's measured bytes per unit with the record that
measured it, the planned unit counts, the fixed costs a run needs beside its working state, and the
governed reserve. `WorkingStateRequirement.identity()` digests every term, and the refusal names it,
so the number a preflight refused on can be traced to the densities, counts, and plan it came from.

**Staleness fails closed.** The densities were measured against one source plan, whose fingerprint —
a digest over which sources, how many instances of each, and which are required — is bound into the
requirement. A catalog whose plan does not fingerprint identically is refused rather than answered
from a projection that has stopped describing the work. The historical three-copies form is retained
only as a floor, so the predicate can demand more than it used to and never less.

No v3 activation is authorized here, and the corrected predicate refuses on this host today.

## 20. Real-state nonmutation

The accepted operational catalog was opened strictly read-only and `immutable=1` on every path, and
every real prefix was parsed into a throwaway catalog under the session's scratch directory.
Measured after all work:

| | |
|---|---|
| catalog bytes | `359,378,944` |
| catalog SHA-256 | `57e36a788dc8e03ea4d1a4c722418de4c4244d73590c6643feace93c80af2ded` |
| catalog last modified | `2026-08-16T21:39:42Z` — two days before this session |
| migration head | `0015` |
| write-ahead log | `0` bytes |
| writer lease | present, `277` bytes, unchanged |
| `census_parser_runs` / `census_parsed_records` / `census_accessions` | `0` / `0` / `0` |
| run namespaces | the fourteen that already existed; **no `…_v3`** |

The v1 and v2 namespaces and the backups are unchanged. No migration was applied anywhere but the
throwaway files. All three execution authorities remain `None`.

## 21. Two further executability defects, found by measuring

Both were found by running the real source rather than the fixture, and both are the same shape as
the one D112 §2.6 found: a query that reads like an index probe and is a table scan, or a
derivation that reads a column another pass has already destroyed.

1. **The corroboration reconstruction's first probe could not use the accepted unique index.**
   Asking `NOT EXISTS (SELECT 1 FROM census_accession_observations WHERE parsed_record_id = ...)`
   inside the index-row scan looks like a seek and is not: `parsed_record_id` is the **third**
   column of `(accession_plain, source_observation_id, parsed_record_id, field_name)`, so every
   index row scanned the whole observation table. The real first source with one real quarter had
   not finished in **fifty-two minutes** and was terminated. Asked after the payload is decoded, on
   the full four-column key, it is one seek and the same run completes in **17 minutes**.
2. **The association pass destroyed the column the compact contract reconstructs membership from.**
   Decision 094 §6.4 item 2 clears `census_accessions.registrant_cik_numeric` on a
   multi-registrant accession before the second relation row is inserted, so migration `0014`'s
   trigger can observe the cardinality. That column is exactly what D112 §2.3 reconstructs the
   omitted submissions-side `cik` observation from. The completeness pass **re-derives** its
   verdict rather than remembering it (D110 §8), so it then read a group with no submissions side,
   found it unestablished, and disagreed with the pass that had counted it. The Decision 094 §9.5
   totality invariant refused the run — correctly, and before any durable state existed, because
   the whole projection is one transaction. Measured on the real first source with one real
   quarter: **8 established multi-registrant accessions**. The fix back-fills the observation
   immediately before the clear, for the same reason D112 §2.2 back-fills an incumbent before
   writing a rival, and it is a no-op under the full contract and wherever the row is already
   stored.

**This is a D112 defect, not a D113 one**, and it is stated here because this is the record whose
measurement found it. D112's fixture could not reach it: its only multi-registrant accessions come
from a second *bulk* witness, whose observations are materialized either way, and its full-index
co-registrant was unbindable and so never reached `established`. The D113 fixture now carries a
joint filing whose co-registrant is bindable and whose submissions registrant the index also
lists, which reproduces the state without any real data, and
`test_a_multi_registrant_accession_keeps_its_reconstructed_membership` holds it.

## 22. One live mutation anchor has stopped describing its target

`make check-fast` **failed on exactly one test**, and the failure is a true statement rather than a
defect: `test_every_live_anchor_but_the_superseded_m19_resolves_against_the_live_target` now
reports `['M19', 'M21']` where it expects `['M19']`.

**M21** anchors the exact text

```python
            if plain not in known:
                unbound.add(plain)
                continue
```

in `_materialize_full_index_registrants`, and tests the **R23** §5.1 invariant that an index-only
accession is *reported*, never manufactured. §9 replaced the preloaded `known` set — one string per
accession in the catalog, roughly 21.5 million strings and about 2.9 GB on the first planned source
— with the per-accession primary-key lookup accepted Decision 110 §8 requires, and that lookup also
returns the canonical values the corroboration verdict needs. The predicate is unchanged; the text
it is written in is not.

**The invariant M21 covers is intact and still covered.** The accession is still added to `unbound`
and skipped, `census_accession_observations.accession_plain` is still a foreign key that would
refuse an invented one, `tests/unit/test_m3_offline_parse.py` passes, and D113's own
`test_the_accepted_totality_object_is_identical` holds the unbound set equal between the two
contracts over a fixture that carries an index row binding to nothing.

This record does **not** edit the durable campaign artifact, the live-anchor expectation, or the
test. Decision 097 R87 settled the equivalent question for M19 by owner ruling rather than by an
implementer's edit, and that is the shape this one needs: the owner is asked to rule whether M21 is
**superseded** on the same grounds — its anchor names a memory-bounded derivation that accepted
Decision 110 §8 required to change — or whether the anchor should be re-cut against the live text.
Nothing else in `make check-fast` failed: 4,694 tests passed, one was skipped, and the lint, format,
and type gates that precede the suite all passed.

## 23. What this record does not do

It authorizes no execution, creates no namespace, applies no migration, and grants no network, SEC,
or HTTP access at any request ceiling. It does not rewrite Decisions 103–112. It does not promote the
run-local sidecar into the operational catalog, which still needs its own owner-approved persistence
bridge.
