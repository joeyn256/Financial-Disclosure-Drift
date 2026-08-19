# Decision 117 — The First Real Single-Source Canary, and Its Throughput Failure

```text
STATUS: ACCEPTED — OWNER FINDING, CLOSED
DATE: 2026-08-19
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OUTCOME: M3_3_D117_THROUGHPUT_FAILURE_OWNER_ACCEPTED
SUPERSEDES: nothing
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The first **real** single-source canary ran, over the accepted `sec_bulk_submissions` first
planned source, on the path
[Decision 116](decision_116_m3_3_disposable_single_source_canary_path.md) §§5–11 built. It did
not finish, and it was not meant to be allowed to: it was stopped at a throughput gate. This
record carries the owner's accepted findings from that execution so the committed repository
holds them.

**Provenance, stated rather than implied.** Every measured value below is quoted from the owner
instrument that accepted the D117 execution. The session that wrote this record did not re-run
the canary, did not open the preserved D117 world, and re-derived none of these numbers. They
are recorded here as accepted owner findings, which is what they are.

**This record grants no execution authority.** All three activation constants remain `None`,
migration `0016` remains unapplied, the operational catalog remains at head `0015`, and no
E0-v3 namespace exists.

## 1. What ran

One governed planned source — the accepted first source, `sec_bulk_submissions` — through
`m3 canary-source --mode run`, into a create-once disposable world beneath an operator-supplied
work root outside both the repository checkout and the private evidence root, under evidence
contract `e0-compact-evidence/2`, at batch size `250` with write-ahead-log truncation at each
boundary.

## 2. The disposition

**`M3_3_D117_THROUGHPUT_FAILURE_OWNER_ACCEPTED`.** The run was stopped at a throughput gate
before the source finished materializing. It is a **failure**, recorded as one:

* no source reached a terminal disposition;
* no complete-source member manifest, projection digest, `ResolutionDigest`,
  `CorroborationDigest`, or compact-evidence identity was emitted;
* **no success token was issued**, and none may be inferred from the fact that the path ran;
* nothing was promoted, no migration was applied, and no E0 authority constant was touched.

## 3. What held

The safety architecture behaved as designed, and that is the one positive finding:

* the **accepted operational catalog was untouched** — opened strictly read-only on every path,
  with no writer lease taken on it, and byte-identical afterwards;
* every write landed in the run-local Decision 111 working catalog inside the disposable world;
* **memory stayed bounded** — the streamed traversal accepted
  [Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) §8 required did not
  reproduce the D109 resident-set failure;
* the partial state was **truthful while incomplete**: committed batches were durable under a
  parser run that claimed nothing, which is exactly the interruption behaviour
  [Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md) §3 exists to
  produce.

## 4. What failed

**Throughput.** Materialization rate decayed materially as the working catalog grew, to the
point where the accepted first-source performance expectation could not be met. The diagnosis of
*why* is not this record's — it is
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md).

## 5. The preserved world

The D117 disposable world is **preserved as diagnostic evidence**. Its working catalog is about
`25.65 GiB` (about 27.5 GB).

It is preserved under a hard boundary, restated here because it binds every later session: the
D117 world **must not be resumed, modified, promoted, vacuumed, reindexed, or deleted**, and it
must never be opened for writing. Reading it is permitted only where a quoted identity has to be
verified, and preferably not at all.

## 6. What this record does not do

It does not authorize a retry of the first-source canary, a three-source canary, a real replay
proof, E0-v3, migration `0016`, network, or acquisition. It supersedes nothing. It closes the
D117 execution as an accepted failure and hands the question of cause to Decision 118.
