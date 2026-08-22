# Decision 132 — The Bounded Real Semantic Proof of the D131 Repair

```text
STATUS: ACCEPTED — OWNER RULING / BOUNDED REAL SEMANTIC PROOF
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF A COMPLETED BOUNDED PROOF —
  RETROSPECTIVE; THE PROOF RAN BEFORE THIS RECORD EXISTED AND THIS RECORD AUTHORIZED NONE OF IT
DATE: 2026-08-22
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
CLASSIFICATION: BOUNDED_REAL_SEMANTIC_FIXTURE_ONLY
ACCEPTANCE_TOKEN: M3_3_D132_BOUNDED_REAL_SEMANTIC_PROOF_OWNER_ACCEPTED
PUBLICATION_TOKEN: M3_3_D132_GOVERNANCE_PUBLICATION_AUTHORIZED
EXECUTION_TOKEN: M3_3_D132_BOUNDED_REAL_SEMANTIC_PROOF_AUTHORIZED — issued outside this
  repository and recorded in the private proof manifest; it is spent
OUTCOME: D131_REPAIR_PROVEN_OVER_AUTHENTICATED_REAL_SEVEN_MEMBER_FIXTURE
D128_SEMANTIC_DISPOSITION: UNCHANGED. D129-R2'S REJECTION OF EVERY D128 COUNT STANDS ENTIRELY
SCOPE: BOUNDED REAL SEMANTIC BEHAVIOUR OF THE ACCEPTED D131 REPAIR OVER SEVEN AUTHENTICATED
  REAL SEC MEMBERS — NOT A SOURCE-WIDE RESULT, NOT A PERFORMANCE RESULT, NOT A CAPACITY MODEL,
  AND NOT AN EXECUTION AUTHORIZATION
SOURCE_WIDE_CLAIM: NONE
CORRECTED_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO — AND NO MIGRATION IS REQUIRED BY THIS PROOF
PERFORMANCE_AUTHORIZATION: NO
CAPACITY_RECONCILIATION_STATUS: D129-R12 UNRESOLVED
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
```

The owner's governance publication of the bounded real semantic proof that
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §17 named as the next
stage and that [Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §11
(D131-R7) ruled an ordinary `--member-limit` prefix could not supply.

## 1. What this record is, and what it is not

**It is a retrospective record of a completed proof.** The proof had already run when this record
was written, under an owner instrument issued outside this repository
(`M3_3_D132_BOUNDED_REAL_SEMANTIC_PROOF_AUTHORIZED`). **This record authorized none of it**, and the
grant is spent. In that respect it is shaped like
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) and
[Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md), not like
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md), which entered with its
code.

**It proves the repair against real SEC bytes, over exactly seven members.** Every payload the proof
parsed came byte-identically out of the accepted bulk archive. Nothing was normalized,
reserialized, edited, or synthesized. What is bounded is the *population*, not the authenticity —
and §14 states the boundary in the terms the owner fixed.

**It changes no production code, and no code changed to permit it.** §3 records that the proof
exercised the accepted D131 call path end to end and that no new repository mode, flag, or parser
was introduced. The scratch harness supplied disposable fixture provenance and world initialization
only.

**It certifies no count of the real source.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
§4 (D129-R2) rejected every D128 count, and **that rejection stands entirely and is not revisited
here.** The `4,135` historical accessions of §9 are a property of four selected shards, not of the
archive.

**It is not a performance result and not a capacity model.** No tuning was performed and none is
authorized. [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12) continues
to require a corrected-run capacity reconciliation this record does not construct.

**It closes no pre-network blocker.** `CensusOrchestrator._parse_bulk` still carries the Defect A
dispatch, exactly as [Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §12
(D131-R4) left it.

## 2. Entry state

The proof and this publication both entered at the same verified baseline:

| Item | Value |
|---|---|
| Branch | `main` |
| `HEAD` | `c455e4022c00b3b0c7b55d493d8415365060f2fd` |
| Tree | `3aeb1b1e6b2a8530c51b45d4d94df99569781876` |
| `origin/main` | identical to `HEAD`, ahead/behind `0/0` |
| Worktree | clean; nothing staged |
| Latest decision | Decision 131 |
| Migration head | `0015`; `0016` absent and unapplied |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` |
| `network.enabled` | `false` |
| `network.m3_acquire_enabled` | `false` |

`git diff -- Docs Literature Milestones` was empty at execution, and the proof left the repository
byte-unchanged (§13).

## 3. The accepted path, unchanged — D132-R1

**No new repository mode was required, and none was created.** The proof drove the accepted D131
implementation through its own entry points, in order:

```text
select_planned_source
  -> materialize_one_planned_source
    -> _stream_bulk_submissions
      -> historical-shard classification / deferral
        -> explicit parent resolution
          -> sec.archive.iter_named_members
            -> parse_historical_submissions
              -> CensusCatalog.persist_streamed
                -> historical-reference reverse lookup
```

Every link in that chain is the surface
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §§4, 5 and 8 accepted.
**No repository semantics were reimplemented by the scratch harness**: it supplied disposable
fixture provenance and world initialization, and nothing else. The proof is therefore a measurement
of the shipped implementation rather than of a parallel one written to succeed.

The parser versions observed on the run are the D131 versions, derived as D131 §7 requires:
`submissions-json/1.2` for the primary documents and `submissions-historical/1.1` for the shards.

## 4. The authenticated real source — D132-R2

The proof read the accepted bulk source, resolved governed through
`census_plan_sources -> census_source_observations -> SnapshotStore.payload_path`:

| Item | Value |
|---|---|
| Filename | `sec_bulk_submissions-c85744be921b0dc5.zip` |
| Bytes | `1,556,847,020` — measured equal to expected |
| SHA-256 | `c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f` — measured equal to expected |
| Governed JSON members | `985,834` |
| Source instance | `sec_bulk_submissions` |

**Central-directory corroboration**, taken independently of the governed member count:

| Item | Count |
|---|---|
| Total members | `985,835` |
| JSON members | `985,834` |
| Placeholder member | `1` |
| Historical shard members | `5,337` |
| Distinct shard parent CIKs | `4,144` |
| Parents declaring more than one shard | `442` |

The `5,337` and `4,144` reproduce exactly the figures
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §§5–6 recorded for the two defects,
which is what makes this the same population D128 mishandled. **The source was opened read-only and
is unchanged** — SHA-256 and mtime were both rechecked afterwards (§13).

## 5. The deterministic bounded selection — D132-R3

Selection was a stated rule applied to the real central directory, not a hand-picked set: the lowest
shard-parent CIK declaring at least two shards (taking its first two), then the two lowest CIKs
declaring exactly one, ascending.

| Parent CIK | Registrant | Shard | Historical accessions |
|---|---|---|---|
| `0000001750` | AAR CORP | `CIK0000001750-submissions-001.json` | `1,354` |
| `0000001800` | ABBOTT LABORATORIES | `CIK0000001800-submissions-001.json` | `2,001` |
| `0000001800` | ABBOTT LABORATORIES | `CIK0000001800-submissions-002.json` | `608` |
| `0000002034` | ACETO CORP | `CIK0000002034-submissions-001.json` | `172` |

**All four shards**: physically exist in the accepted archive; are explicitly named by their real
parent's `filings.files[].name`; match the governed historical-shard shape; carry real historical
accessions; and have a filename CIK consistent with the explicit parent — so the corroborative check
D129-R5 permits had something to agree with, and §11 shows what happens when the *declaration* is
the thing that is missing.

**The selection cost `7` payload reads against a `24`-member budget.** A bounded selection that had
to read widely to find its subjects would have been a survey, not a selection.

**The real archive supplied the child-before-parent case rather than the fixtures inventing it**:
`CIK0000001800-submissions-002.json` occurs *before* its parent document in the accepted archive.
The ordering hazard D129-R6 names is a property of the real source.

## 6. Byte-exact fixtures — D132-R4

Two disposable fixture ZIPs were built over **the same seven byte-exact real SEC member payloads** —
three primary documents and four historical shards.

- **No JSON normalization. No reserialization. No field edits. No CIK edits. No synthesized
  accessions.**
- **Only member order differed.**

| Fixture | SHA-256 | Bytes |
|---|---|---|
| `PARENT_FIRST` | `d99c264a55c2cc281083533fb1052ce5d76d9c85613476cecbbae0d29ce95ea8` | `169,186` |
| `CHILD_FIRST` | `efcf4e20d78b0b3c279bca979a3507793c1c7d2018ea02cfad2f7c1ba2f4477d` | `169,186` |

Across the two fixtures, **member names, payload lengths, and payload SHA-256s were proven equal**,
and the archive bytes differ only because the members are laid out in a different order. **Every
fixture payload SHA-256 matched its source member**, so what the parser saw is what the SEC
published. The two archives being the same size while hashing differently is the point: the only
variable is order.

## 7. Real dispatch — D132-R5

The observed dispatch, **in both fixture orders**:

| Member class | Count | Parser | Version |
|---|---|---|---|
| Primary submissions documents | `3` | `parse_submissions_document` | `submissions-json/1.2` |
| Historical shards | `4` | `parse_historical_submissions` | `submissions-historical/1.1` |

| Question | Observed |
|---|---|
| Historical shards reaching the primary parser | **`0`** |
| Historical shards reaching the historical parser | **`4` of `4`** |
| Total parser calls | `7` |

This is the direct contradiction of D128, where all `5,337` shards reached the primary parser and
were rejected ([Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §5).

**The instrumentation was transparent call-through only** — it observed which parser received which
member and changed nothing about the call. And the observation does not rest on the instrumented
runs alone: **two non-instrumented disposable worlds independently corroborated the same result
through durable provenance**, with every shard's persisted records carrying `record_path`
`historical` and no primary document's records ever carrying it.

## 8. Explicit parent binding — D132-R6

For every real shard, four independently derived facts agreed:

1. the real primary's `filings.files[].name` declaration;
2. the persisted `census_historical_references.registrant_cik_padded`;
3. the reverse-lookup result;
4. the `registrant_cik` argument passed to the historical parser.

| Shard | Declared by | Persisted | Reverse lookup | Parser argument |
|---|---|---|---|---|
| `CIK0000001750-submissions-001.json` | `0000001750` | `0000001750` | `0000001750` | `0000001750` |
| `CIK0000001800-submissions-001.json` | `0000001800` | `0000001800` | `0000001800` | `0000001800` |
| `CIK0000001800-submissions-002.json` | `0000001800` | `0000001800` | `0000001800` | `0000001800` |
| `CIK0000002034-submissions-001.json` | `0000002034` | `0000002034` | `0000002034` | `0000002034` |

**Three distinct parent registrants survived correctly**, and the distinct-CIK sets over persisted
reference rows, registrant rows, accession registrants, and reverse lookups were each exactly
`{0000001750, 0000001800, 0000002034}`. **No observation-wide parent CIK leaked across registrants**
— the collapse [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §6 found, in which
`4,144` distinct registrants became one wrong CIK, did not occur.

**[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §7 (D129-R5) remains controlling.**
The explicit parent declaration is authoritative; the filename CIK is **corroborative only**. Here
the two happened to agree for all four shards, which is why §11's negative case matters: agreement
is not the same as authority, and the record must not let one be read as the other.

## 9. Restored historical semantic material — D132-R7

Historical accessions contributed by the selected shards:

| Shard | Accessions |
|---|---|
| `CIK0000001750-submissions-001.json` | `1,354` |
| `CIK0000001800-submissions-001.json` | `2,001` |
| `CIK0000001800-submissions-002.json` | `608` |
| `CIK0000002034-submissions-001.json` | `172` |
| **Total** | **`4,135`** |

For this bounded fixture, the shard accessions **absent from the corresponding selected primary**
number **`4,135`** — every one of them. The repaired path therefore demonstrably restores real
historical semantic material that was absent from those primary documents, which is the material
D128 lost.

**THIS IS NOT A SOURCE-WIDE COUNT. It must not be extrapolated to the full archive.** It is a
measurement over four shards belonging to three registrants, selected by rule from `5,337` shards
belonging to `4,144`.

## 10. Archive order independence — D132-R8

`PARENT_FIRST` and `CHILD_FIRST` each produced:

| Item | Value |
|---|---|
| Members | `7` |
| Records | `7,139` |
| Parsed | `7,139` |
| Quarantined | `0` |
| Malformed references | `0` |
| `parser_state` | `not_started` → `completed` |

**The accepted order-independent semantic comparison returned `PASS`**, with **no semantic
differences** across: accession identity; canonical record content; the applicable record SHA;
registrant binding; historical-reference rows; parser provenance; reverse lookup; quarantine;
malformed references; order-independent member representation; and the applicable F1/F2 semantic
material the bounded path produced.

This is D129-R6 measured against real bytes rather than argued: a shard may precede its parent in
the archive and the semantic result does not move.

**One incidental equality is recorded as incidental.** For these two specific orderings the
completeness digest (`ebf473937d1da4eab795893bc03764f125a75f885c5e6d5690deab90149b7bdf`), the parser
run id, and the resulting member-manifest ordinals also agreed — because D131 defers every shard to
the end of the traversal, so both orderings converge on the same three-primaries-then-four-shards
sequence. **That equality must NOT be generalized to arbitrary archive permutations.** It is a
consequence of the deferral behaviour over this member set, not an invariant this proof established.

## 11. Filename is not identity authority — D132-R9

The bounded negative proof. A third disposable fixture
(`5d62cf7a5b3626d0cd91e6355d29633acb1b7871268567a5ade9f90a5c6fb677`) retained the **four byte-exact
real historical shard members** and **omitted their real declaring primaries**. The shard filenames
still encoded their correct CIKs — `0000001750`, `0000001800`, `0000001800`, `0000002034` — so a
filename-trusting implementation would have had everything it needed to proceed, and would have been
right by accident.

**The accepted implementation refused the fixture** under the D129-R5 missing-parent rule:

> historical shard `CIK0000001750-submissions-001.json` is present in the bulk archive but no primary
> submissions document declares it under `filings.files`; the shard's own filename is corroboration
> and never a binding, so the traversal refuses rather than adopting the registrant its name encodes

Persisted result after the refusal:

| Item | Value |
|---|---|
| Parsed records | `0` |
| Accessions | `0` |
| References | `0` |
| Parser runs | `0` |
| Plan `parser_state` | `not_started` |

The refusal cost no partial state: nothing was written and the plan never left its starting state,
which is what "fails closed" has to mean to be worth anything.

**Therefore a filename CIK cannot rescue absent explicit parent evidence.** Two limits are stated
rather than implied: **contradicted-parent behaviour was NOT reproduced here**, because reproducing
it would have required modifying real JSON bytes and this proof modified none; and the accepted
**D131 negative unit proof remains controlling for the contradiction case**.

## 12. The disposable evidence — D132-R10

| Item | Value |
|---|---|
| Private proof manifest | `~/m3-d132-semantic-proof/d132_proof_manifest.json` |
| SHA-256 | `732e696ab8327c6d2ac64f5d472e2d35cb17eeac82ebcac4c4cf4e628c95b3a7` |
| Evidence root size | `95,891,640` B written across the disposable worlds |

**The `~96 MB` evidence root is NOT copied into the repository**, and no part of it is tracked.
**This Decision record is the durable governance pointer** — the same architecture
[Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md) §6 (D130-R2) adopted, where the
record itself carries the identities rather than a separate internal artifact.

The scratch harness is authenticated compactly, so a later reader can tell whether a recovered
script is the one that produced this evidence:

| Harness file | SHA-256 |
|---|---|
| `d132_semantic_proof.py` | `75e4650942fbcb0cdcc27018c277ade8c37850de7cdc25ad7fc8e49ef5975ef7` |
| `d132_compare.py` | `b47f6d5844ff148dcdc97bf0dd21f5412504d2b00a93c973e0e5c8ed8f342e91` |
| `d132_failclosed.py` | `7eb7312581177ec2d3a755cfe718281e7ae1f529802ea5b1883698e22d9e1418` |
| `d132_manifest.py` | `9b2cc7d12f782efa305477f64b514a1148e168a718e93ecc602915d4fa407dcf` |

The four disposable run identities were `m3_3_d132_real_semantic_parent_first_v1`,
`m3_3_d132_real_semantic_child_first_v1`, `m3_3_d132_dispatch_witness_parent_first_v1`, and
`m3_3_d132_dispatch_witness_child_first_v1`, with the negative case at
`m3_3_d132_fail_closed_orphan_shards_v1`. **None of them is an E0 namespace**, and none is resumable
or promotable.

## 13. Non-mutation and safety — D132-R11

| Item | Result |
|---|---|
| Repository | **unchanged** during execution — `0` files touched, `0` bytes changed |
| Operational catalog | **database bytes unchanged**; opened strictly read-only |
| Operational catalog SHA-256 | `57e36a788dc8e03ea4d1a4c722418de4c4244d73590c6643feace93c80af2ded` — measured equal to the prior recorded value |
| Operational catalog WAL | `0` B |
| Accepted source | SHA-256 **and** mtime unchanged |
| Network | prohibited by configuration **and** additionally guarded by raising `socket` stubs installed before any access |

The catalog digest matches the value already carried by two prior independent evidence artifacts —
the [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) retention manifest and the
C3 prefix canary result — so the equality is a cross-record agreement rather than a self-comparison.
A read-only open does remap the SQLite `-shm` file; that is recorded as observed and is not a
database mutation.

**Not done, and measured as not done:** no E0; no E0 namespace; no complete-source canary; no
`census_orchestrator` import; no migration `0016`; no authority change; no network reached.

## 14. The claim boundary — D132-R12

**D132 certifies ONLY** the bounded real semantic behaviour of the accepted D131 repair over the
authenticated seven-member fixture.

**D132 does NOT certify:**

- source-wide completeness;
- a source-wide accession count;
- a source-wide record count;
- corrected D128 counts;
- any replacement of D128;
- E0 readiness;
- complete-source canary readiness;
- performance readiness;
- capacity readiness.

**[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (D129-R2) remains fully
controlling: every D128 semantic count remains rejected.** Proving that the repaired parser behaves
correctly on seven members says nothing about what the earlier run recorded over `985,834`, and the
two must never be netted against each other.

**[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12) remains
unresolved**: the corrected-run capacity must be reconciled later, and this record constructs no
part of that model.

`7` members of `985,834` were parsed. The classification `BOUNDED_REAL_SEMANTIC_FIXTURE_ONLY` is
carried in the evidence manifest itself, alongside the explicit list of claims withheld, so the
boundary travels with the evidence and not only with this record.

## 15. Owner rulings D132-R1 – D132-R13

| Ruling | Content |
|---|---|
| **D132-R1** | **No new repository mode was required.** The proof exercised the accepted D131 call path from `select_planned_source` through `materialize_one_planned_source`, `_stream_bulk_submissions`, historical-shard classification and deferral, explicit parent resolution, `sec.archive.iter_named_members`, `parse_historical_submissions`, `CensusCatalog.persist_streamed`, to the historical-reference reverse lookup. **No repository semantics were reimplemented by the scratch harness**, which supplied disposable fixture provenance and world initialization only (§3). |
| **D132-R2** | **The real source is authenticated.** `sec_bulk_submissions-c85744be921b0dc5.zip`, `1,556,847,020` B, SHA-256 `c85744be…82b82f`, `985,834` governed JSON members; central-directory corroboration `985,835` total members, `985,834` JSON, `1` placeholder, `5,337` historical shards, `4,144` distinct shard parent CIKs, `442` parents declaring more than one shard. **Read-only and unchanged** (§4). |
| **D132-R3** | **The bounded proof set was selected deterministically from the real archive.** Parent `0000001750` with `CIK0000001750-submissions-001.json` (`1,354`); parent `0000001800` with `CIK0000001800-submissions-001.json` (`2,001`) and `CIK0000001800-submissions-002.json` (`608`); parent `0000002034` with `CIK0000002034-submissions-001.json` (`172`). All four physically exist, are explicitly declared by their real parent's `filings.files[].name`, match the governed shard shape, carry real historical accessions, and have a filename CIK consistent with the explicit parent. Selection used `7` payload reads against a `24`-member budget, and the archive itself supplied a genuine child-before-parent case (§5). |
| **D132-R4** | **The fixtures are byte-exact.** Two disposable ZIPs over the same seven byte-exact real SEC payloads — no normalization, no reserialization, no field edits, no CIK edits, no synthesized accessions — differing **only** in member order. `PARENT_FIRST` `d99c264a…95ea8`, `CHILD_FIRST` `efcf4e20…4477d`, each `169,186` B; member name, length, and payload SHA-256 equality proven across fixtures, and every fixture payload SHA-256 matched its source member (§6). |
| **D132-R5** | **Real dispatch is proven in both orders.** `3` primary documents to `parse_submissions_document` at `submissions-json/1.2`; `4` historical shards to `parse_historical_submissions` at `submissions-historical/1.1`; **`0`** shards reaching the primary parser and **`4` of `4`** reaching the historical parser. Instrumentation was transparent call-through only, and **non-instrumented disposable worlds independently corroborated historical `record_path` provenance** (§7). |
| **D132-R6** | **Explicit parent binding holds across three registrants.** For every shard the primary's `filings.files[].name` declaration, the persisted `census_historical_references.registrant_cik_padded`, the reverse lookup, and the `registrant_cik` passed to the historical parser all agreed: `1750 -> 1750`, `1800 -> 1800`, `1800 -> 1800`, `2034 -> 2034`. **No observation-wide parent CIK leaked across registrants.** D129-R5 remains controlling — the explicit parent declaration is authoritative and the filename CIK is corroborative only (§8). |
| **D132-R7** | **The repair restores real historical semantic material.** The selected shards contributed `1,354 + 2,001 + 608 + 172 = 4,135` historical accessions, and for this bounded fixture **all `4,135` are absent from the corresponding selected primary documents**. **THIS IS NOT A SOURCE-WIDE COUNT and must not be extrapolated to the full archive** (§9). |
| **D132-R8** | **Archive order does not change the semantic result.** `PARENT_FIRST` and `CHILD_FIRST` each produced `7` members, `7,139` records, `7,139` parsed, `0` quarantined, `0` malformed references, `parser_state` `completed`, and the accepted order-independent semantic comparison returned **`PASS`** with no differences across accession identity, canonical record content, applicable record SHA, registrant binding, historical-reference rows, parser provenance, reverse lookup, quarantine, malformed references, order-independent member representation, or applicable F1/F2 semantic material. **The incidental equality of completeness digest and manifest ordinals for these two orderings follows from D131 deferral behaviour and must NOT be generalized to arbitrary archive permutations** (§10). |
| **D132-R9** | **A filename is not identity authority.** A disposable fixture holding the four byte-exact real shards with their declaring primaries omitted — filenames still encoding the correct CIKs — was **refused** under the D129-R5 missing-parent rule, leaving `0` parsed records, `0` accessions, `0` references, `0` parser runs, and plan `parser_state` `not_started`. **Contradicted-parent behaviour was NOT reproduced**, because that would have required modifying real JSON bytes; the accepted **D131 negative unit proof remains controlling for contradiction** (§11). |
| **D132-R10** | **The evidence is private, disposable, and pointed to rather than copied.** The proof manifest `~/m3-d132-semantic-proof/d132_proof_manifest.json`, SHA-256 `732e696ab8327c6d2ac64f5d472e2d35cb17eeac82ebcac4c4cf4e628c95b3a7`, authenticates the run. **The `~96 MB` evidence root is not copied into the repository**, and **this Decision record is the durable governance pointer**; the four scratch-harness SHA-256s in §12 authenticate the instrument compactly (§12). |
| **D132-R11** | **Nothing was mutated.** Repository unchanged; operational catalog bytes unchanged at SHA-256 `57e36a78…af2ded`, matching two prior independent evidence artifacts; accepted source SHA and mtime unchanged; network prohibited and additionally guarded by raising `socket` stubs. **No E0, no E0 namespace, no complete-source canary, no `census_orchestrator` import, no migration `0016`, and no authority change** (§13). |
| **D132-R12** | **The claim boundary is bounded real semantics and nothing else.** D132 certifies only the bounded real semantic behaviour of the D131 repair over the authenticated seven-member fixture, and certifies **no** source-wide completeness, accession count, or record count, **no** corrected D128 counts, **no** replacement of D128, and **no** E0, canary, performance, or capacity readiness. **D129-R2 remains fully controlling — every D128 semantic count remains rejected** — and **D129-R12 remains unresolved** (§14). |
| **D132-R13** | **The next sequence is bounded performance A/B, then capacity reconciliation, then an owner decision.** (1) Bounded performance A/B; (2) corrected-run capacity reconciliation under D129-R12 using the repaired parser and the adopted performance configuration; (3) **only then** an owner decision on another complete-source canary. **No complete-source canary is authorized by D132. E0 remains unauthorized.** The standing PRE-NETWORK blocker remains: `census_orchestrator.py::_parse_bulk` must be repaired before any future network or live-retrieval authorization may reach it (§17). |

**The controlling earlier rulings are preserved, not replaced.** D129-R5 remains the authoritative
child-binding rule and §8 measures it; D129-R6 remains the order-independence invariant and §10
measures it; **D129-R2's rejection of every D128 count stands entirely**; **D129-R8's four
requirements for a corrected proof are unchanged**; **D129-R12 continues to require a corrected-run
capacity reconciliation this record does not construct**; and **D131-R4's pre-network blocker stays
open**. D131-R7 is not contradicted — it ruled that an ordinary `--member-limit` prefix cannot be
this proof, and this proof was not a prefix.

## 16. What this record does not do

- **It does not certify any D128 count.** D129-R2's rejection stands entirely.
- **It does not make any source-wide claim.** `7` members of `985,834` were parsed, and the `4,135`
  restored accessions belong to four shards, not to the archive.
- **It does not repair `CensusOrchestrator._parse_bulk`** (D131-R4), and repairing it now remains out
  of scope.
- **It does not tune performance** and **does not construct a capacity model** (D129-R12 unresolved).
- **It does not change production code, tests, scripts, configuration, or migrations.** No code
  changed to permit the proof, and none changed to publish it.
- **It does not authorize** another semantic execution, a bounded performance A/B, a capacity
  reconciliation, a corrected complete-source canary, any canary, any disposable world, E0, an E0
  namespace, migration `0016`, network, SEC or HTTP access, or any catalog write. **Request ceiling
  remains `0`.**
- **It does not alter any authority constant.** All three remain `None`.
- **It does not supersede any record.** Decisions 121 through 131 stand as written, and **every
  D124-R5 gate carries forward intact**.
- **It does not publish the private evidence root**, and no part of it is tracked.

## 17. The next sequence — D132-R13

1. **Bounded performance A/B.**
2. **Corrected-run capacity reconciliation** under
   [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12), using the repaired
   parser and the adopted performance configuration.
3. **Only then**, an owner decision on another complete-source canary — which
   [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §14 (D129-R8) still requires to be
   a full rerun from scratch in a new world.

Each step requires its own owner instrument. **E0 remains unauthorized throughout**, and reaching
step 3 is not reaching E0. Separately and independently of that sequence,
`census_orchestrator.py::_parse_bulk` must be repaired before any future network or live-retrieval
authorization may reach it; that repair is not part of this sequence and must not be performed as a
side effect of unrelated work.
