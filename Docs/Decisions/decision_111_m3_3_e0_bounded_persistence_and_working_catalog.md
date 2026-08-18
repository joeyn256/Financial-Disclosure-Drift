# Decision 111 — E0 Bounded Persistence, the Run-Local Working Catalog, and the Persistence-Contract MAJOR

```text
STATUS: ACCEPTED — OWNER ACCEPTANCE OF THE D111 REMEDIATION
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D111_THROUGHPUT_REMEDIATION_OWNER_ACCEPTED
OUTCOME: M3_3_D111_WORKING_CATALOG_ARCHITECTURE_OWNER_ACCEPTED
CLOSES: D110 §10 throughput defect, journal-residency defect, blast-radius defect
RETURNS: ONE MAJOR — the E0 persistence CONTRACT over-materializes real source evidence
ACCEPTED_CANDIDATE_HEAD: ab4398afc60f3d85f4e0e3ba4b161221e9bb6578
ACCEPTED_CANDIDATE_TREE: 6ac3d4f4c1aae555c3204d151a7d1e80a8e711da
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
```

This record carries the owner's acceptance of the D111 remediation and the one MAJOR it returned
unclosed. It was written after the fact, at the owner's instruction recorded in
[Decision 112](decision_112_m3_3_compact_e0_evidence_contract.md) §9, because the implementation was
committed at `ab4398a` before its record existed. The gap is closed here rather than left to the
commit message.

It changes **execution mechanics** and nothing else. It writes no research code, changes no frozen
research definition, reads no outcome value, applies no migration, contacts no network, and
redesigns no methodology. Decisions 091–110 remain binding on every point they name, and Decisions
103–110 are **not rewritten**.

**It grants no execution authority.** All three activation constants stay `None`.

## 1. Entry state

[Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) is accepted and its two
workstreams are closed in shipped source. Its §10 canary established that memory is no longer the
barrier — peak RSS 0.864 GiB against a 2.5 GiB ceiling — and that the first planned source
nonetheless **did not complete**: it had not reached member 50,000 at the owner's 20-minute
diagnostic ceiling, and its single transaction had grown a 3.85 GB write-ahead log. D110 §10
required that state to be recorded and the work stopped there.

## 2. What was defective, measured rather than inferred

Three separate defects, all measured on the real first planned source, read-only, against
disposable catalogs.

**2.1 Throughput.** Two derivations were recomputed after **every** record even though each is a
function of the run's whole observation. Candidate lineage edges ran a full grouped scan of every
registrant observation of the source, twice per registrant record. Accession conflict indicators ran
a grouped read plus an update per accession record. Both are monotone in the run's evidence, so the
per-record recomputation was pure quadratic waste. Measured on the real archive, the marginal cost
of a 40-member block had already grown **5×** across the first 400 members.

**2.2 Journal residency.** A single transaction per source cannot keep its journal bounded once the
source is large enough: every page the write dirties has to stay in the journal until the one
commit, so the journal grows with the whole source rather than with any bounded unit of work.

**2.3 Blast radius.** Any bounded-commit scheme applied directly to the accepted operational catalog
would make partial, un-dispositioned progress durable in the artifact the project treats as accepted
state.

## 3. What was corrected

**3.1 The two derivations are hoisted** out of the per-record path and computed once after the last
record. They write exactly the same rows: both are monotone, so a single evaluation over the
complete evidence reaches the same answer the repeated evaluation converged to. Measured on a real
mid-archive slice the parse now sustains **103.2 members/sec with flat block times**, against about
5 members/sec and falling.

**3.2 `BoundedTransaction`** splits one logical write into a bounded series of real transactions and
optionally truncates the write-ahead log at each boundary. **Batch size is not observable in the
result**: the rows, their identities, and their order are decided by the writer before any boundary
is reached, and a commit boundary is only a point at which already-decided rows become durable. Two
materially different batch sizes are asserted equal row for row across every table the parse
touches. Batching stays opt-in and the operational catalog keeps the accepted whole-source
transaction.

**3.3 `WorkingCatalog`** gives a run a writable twin of the accepted catalog at the same migration
head, derived through the supported online-backup interface from a **strictly read-only** handle, so
the accepted artifact stays byte-identical for the whole of a long parse. Partial progress becomes
durable only in the twin.

**3.4 Run-local progress lives outside the accepted schema.** `census_parser_runs.outcome` and
`census_plan_sources.parser_state` have closed accepted vocabularies with no in-progress term, and
no migration may add one under this record. The `not_started / in_progress / parsed / disposed`
distinction the instrument needs is recorded in a ledger beside the working catalog, because it is a
fact about *this attempt* rather than about the census. A batched run's `census_parser_runs` row is
seeded `failed` and corrected to its real terminal only after the last part, so **an interruption
leaves committed rows under a run that claims nothing**. A disposition cannot be recorded over a
source that never finished parsing.

**3.5 The conflict pass is a correlated `EXISTS`, not the `GROUP BY` it reads like.** The grouped
form builds a temporary B-tree over every accession observation in the catalog before it can answer
— an intermediate proportional to the whole source, which is exactly what the accepted D110 §8
memory invariant forbids.

## 4. Owner-accepted correction of a prior finding

The earlier reading that the observed write-ahead-log growth was pathological transient
amplification is **corrected**: it largely reflected useful data. That correction is accepted, and it
is what makes §5 a contract problem rather than a journal problem.

## 5. The MAJOR this record returns unclosed

**The E0 persistence contract over-materializes real source evidence.** Measured on the first
planned source by a complete read-only parse census of all 985,479 members, with per-row byte costs
attributed using `dbstat` on a representative mid-archive slice:

| Quantity | Measured |
|---|---|
| Members | 985,479 |
| Parsed records | 22,973,187 |
| Accession records | 21,993,042 |
| Accession field observations | 373,881,714 |
| Peak RSS during the census | 1.10 GiB |

| Projected table | Bytes |
|---|---|
| `census_accession_observations` | ~204.2 GB |
| `census_parsed_records` | ~29.9 GB |
| `census_accessions` | ~9.0 GB |
| other | ~3.1 GB |
| **first source total** | **~246.2 GB** |

That is **before the resolution layer and before the remaining 75 sources**, against 76 GiB free on
this host. It is final useful data, not transient journal amplification, so it was returned as a
MAJOR rather than solved by deleting governed observations. **No amount of batching closes it** — a
bounded transaction changes when rows become durable, never how many there are.

## 6. Owner acceptance

Accepted under `M3_3_D111_THROUGHPUT_REMEDIATION_OWNER_ACCEPTED` and
`M3_3_D111_WORKING_CATALOG_ARCHITECTURE_OWNER_ACCEPTED` at `HEAD` `ab4398a`, tree `6ac3d4f`. The
accepted scope is the run-local working-catalog architecture, operational-catalog isolation, bounded
transaction and checkpoint mechanics, set-based persistence remediation, deterministic output
equivalence across batch sizes, interruption truthfulness, disposable atomic-promotion mechanics,
and the §4 correction. The transparent second `make check-fast` following correction of a
documentation citation is accepted, and no further D111 validation is required.

**Measured remediation:** ~5 members/sec and degrading before, **~103.2 members/sec with flat block
times** after; peak RSS ~1.11 GiB; peak WAL ~196 MB; post-checkpoint WAL 0.

**These defects are CLOSED.**

## 7. What this record does not do

No canary was run against the real first source under D111, no real catalog was mutated, no
namespace was created, no migration was applied, and all three execution authorities remain `None`.
The §5 MAJOR is answered by [Decision 112](decision_112_m3_3_compact_e0_evidence_contract.md), not
here.
