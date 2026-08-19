# Decision 119 — The Cache-Bound Persistence Correction and the Bounded Prefix Diagnostic Surface

```text
STATUS: ACCEPTED — OWNER IMPLEMENTATION INSTRUMENT, RULINGS R21–R28
DATE: 2026-08-19
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OUTCOME: M3_3_D119_CACHE_BOUND_PERSISTENCE_AND_PREFIX_DIAGNOSTIC
SUPERSEDES: nothing
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The bounded implementation the owner selected in
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §8: **one** performance
correction, and a diagnostic way to re-measure it. It grants **no execution authority of any
kind** — all three activation constants remain `None`, migration `0016` remains unapplied, no
E0-v3 namespace exists, and **no real SEC source may be parsed under this record**. The next real
execution needs its own owner instrument, which this is not.

Rulings **R21–R26** are recorded by Decision 118, which is the diagnosis they belong to. **R27**
(§5) and **R28** (§9) are recorded here, with the implementation §§4 and 6–8 authorize.

## 1. What this record answers

Decision 117 failed on throughput and Decision 118 named the cause. Two things then had to exist
before the question could be reopened at all: the cause had to be **corrected**, and the
correction had to be **measurable without committing to a whole source**. This record is those
two, and deliberately nothing else — the value of the next measurement comes entirely from there
being exactly one change to attribute it to.

## 2. Entry state

Migration head `0015`; migration `0016` absent; no E0-v3 namespace;
`M3_3_E0_EXECUTION_AUTHORITY`, `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` all `None`; both tracked network switches `false` at
request ceiling `0`. The preserved D117 world is diagnostic evidence and is not opened, resumed,
modified, promoted, vacuumed, reindexed, or deleted by anything under this record.

## 3. What stays deferred

Decision 118 §§5–7 defer the compact-sidecar autocommit cadence and every schema and index
change, and this record changes neither. Restated here because it is what makes §4 attributable:
**C1 is the only performance behaviour that moves.** Unchanged, deliberately, are the sidecar
transaction semantics, `synchronous = FULL`, `journal_mode = WAL`, batch size `250`, per-batch
checkpointing, `cache_spill`, `mmap_size`, the table and index schema, the parser algorithms, the
lookup logic, the source ordering, the persistence semantics, and the digest semantics.

## 4. C1 — the explicit working-catalog cache budget

**The defect.** The Decision 111 run-local working catalog never configured a page cache, so
SQLite's own default applied — about `2 MiB` against a working set Decision 118 §1 measured at
`25.65 GiB` on an `8 GiB` host.

**The correction.** An explicit budget of **512 MiB**, which in SQLite's negative `cache_size`
form is a kibibyte budget of **`-524288`**. The negative form is used rather than a page count
because a page count means a different amount of memory at a different `page_size`, and the thing
being budgeted is memory.

**Where it reaches, and where it must not.** It is a parameter of the D111 working-catalog
mechanism, `cache_bytes`, defaulting to `None`:

* it is applied to the **run-local writable** working-catalog connection, after that connection
  exists, and to nothing else;
* the **governed operational catalog**, every read-only authoritative connection, SQLite's global
  defaults, E0 execution semantics, and every unrelated SQLite user are untouched. The shared
  `storage/sqlite.py` connection helper configures no cache at all, which is asserted by test
  rather than by convention;
* an existing caller that requests nothing behaves exactly as it did, which is why the default is
  `None` and not a value;
* the D116 disposable canary path requests the accepted 512 MiB **explicitly**.

**It is an execution parameter, not an evidence semantic.** It changes how much memory a write
may use and moves no row, no ordering, no digest, and no identity. It is therefore reported by
the canary **preflight** and by the diagnostic prefix result, and deliberately **not** by the
accepted `CanaryResult` — that surface records no equivalent execution parameter, batch size
included, and a cache budget is not the thing to make it start. Two canaries over one accepted
catalog differing only in the budget are required to produce identical evidence, and are.

## 5. R27 — the `CompactSourceEvidence` residency correction

`CompactSourceEvidence` documented itself as retaining "nothing proportional to the source". That
was true of the members and their records — each manifest entry is written and dropped, and the
projection digest is one running hash — and **false** of `_seen`, which retains the native
identity of every distinct accession the traversal has met.

The docstring is corrected to say so: `_seen` is one identity string per distinct accession, and
it is therefore proportional to the source's accession count. It exists because
`materialized_fields` must know whether a record is a first witness or a rival, which is a
question about the whole source.

**The data structure is unchanged.** Dropping or bounding it would change which observation rows
the compact contract materializes, and that is an accepted evidence semantic rather than a
performance decision.

## 6. The bounded prefix diagnostic surface

A diagnostic-only way to run the **exact** accepted single-source materialization path over the
first *N* deterministic governed members.

**Operator surface.** `m3 canary-source --mode profile-prefix --member-limit N`.

**The bound belongs to exactly one mode.** `--mode run` stays **complete-source-only** and
**refuses** a member limit rather than ignoring one; `--mode preflight` refuses it too;
`profile-prefix` **requires** it and requires it positive. Zero, negative, and absent bounds are
refused — there is no unbounded prefix, because an unbounded prefix is a whole source.

**What a prefix is.** It selects exactly one accepted planned source, traverses the same
deterministic member ordering, uses the same parser, the same working-catalog persistence path,
the same compact member-recording path, batch size `250`, and the 512 MiB budget from §4. It
stops cleanly immediately after exactly *N* governed members.

**What a prefix can never do.** It never advances to a second source, never claims a source
terminal, never emits a complete-source identity, never reports a canary success, never promotes,
and remains create-once. Concretely, none of the following is reachable from it: a
`census_plan_sources.parser_state` transition, the **R23** full-index materialization, the
catalog-wide resolution pass, the Decision 094 §6.4 association projection, a source-level compact
evidence row, a member-manifest digest, a projection digest, a `ResolutionDigest`, a
`CorroborationDigest`, or a compact-evidence identity.

**Its terminal classification is `INCOMPLETE_DIAGNOSTIC_PREFIX`** — not parsed, not completed,
not a successful source. The token is deliberately **not** a member of the accepted closed
`SourceDisposition` vocabulary, so it cannot be read as a disposition even by accident, and the
result is written to its own filename so a world holding a prefix result holds no canary result.

**Implementation shape.** No parallel parser exists. The cap is an **internal** parameter of the
accepted member stream, `max_members`, whose default is `None`:

* `max_members=None` is the exact existing complete-source behaviour, and
  `materialize_one_planned_source` does not expose the parameter at all — the production `run`
  path cannot supply a bound because it has nothing to supply it through;
* `max_members=N` runs the same path over the first *N* governed members and then terminates
  deliberately, **before** source-level finalization, through
  `materialize_planned_source_prefix`.

**How it stops, and why that is the accepted behaviour and not a new one.** The bounded stream
signals its bound by raising an internal control signal once the consumer has finished writing
member *N*. That signal passes through the accepted `BoundedTransaction`, which rolls the open
batch back and leaves the parser run at the seeded `failed` state — the accepted meaning of "no
consumer may read this run's counts as a real observation". A prefix therefore leaves committed
batches durable and **no run claiming to have completed**, which is Decision 111's interruption
behaviour unchanged and deliberately triggered. It also means a prefix that ends between two
commit boundaries loses its open batch, exactly as any interruption does; §8 reports processed
and durable counts separately for that reason.

**A prefix is defined only over a source with a member ordering.** A single-payload source is one
indivisible logical member ([Decision 116](decision_116_m3_3_disposable_single_source_canary_path.md)
§22), so no prefix boundary exists inside it, and a prefix over one would mean finalizing a
complete parser run under a mode whose whole purpose is to never finalize. It is refused.

## 7. Create-once, disposability, and failure

A diagnostic prefix world is disposable and **create-once**, on the same primitives the D116
canary uses and with the same boundaries: the work root is refused unless it lies outside both
the repository checkout and the private evidence root, refused by the run itself rather than only
by the operator wrapper; a duplicate run identity or world fails closed; an existing directory is
never adopted; a partial prefix is never resumed; the result document is write-once at the
operating system. On an exception the world is preserved, failure is returned, and nothing is
retried automatically. **No promotion mechanism is permitted.**

## 8. The prefix measurement surface

Without pretending to be complete, a prefix makes available: the run identity; the source
identity and plan position; the requested member limit; the members actually processed and their
manifest ordinals; the payload bytes those members represent; the parsed-accession count; the
durable canonical-accession, parsed-record, observation, and parser-run counts; the
working-catalog and write-ahead-log bytes; the compact-sidecar bytes; the requested and
**effective** cache setting; the plan row's `parser_state` before and after; the run-local
progress state; and the terminal diagnostic classification.

Processed and durable counts are reported **separately and deliberately** (§6). No absolute path
enters the document. Per-record instrumentation of the hot loop is deliberately absent —
resource sampling stays an outer-operator responsibility, because a prefix that paid to measure
itself would no longer be measuring the accepted path.

## 9. R28 — the status correction

`Milestones/STATUS.md` is corrected to record truthfully that D116 is owner-accepted and
published; that D117 completed as an accepted throughput failure; that D118's diagnosis is
owner-accepted; that the current work is this bounded persistence correction; that E0-v3 remains
unauthorized; that the migration head remains `0015`; and that no three-source canary is
authorized.

## 10. What the tests prove

**Cache.** An existing `WorkingCatalog` caller without a budget still reports SQLite's default;
the canary requests exactly 512 MiB; the writable canary working connection reports
`PRAGMA cache_size == -524288`, read back from SQLite rather than echoed; the operational and
read-only catalog connections receive no cache mutation and the shared connection helper
configures none; an unrepresentable budget is refused before anything is created; and two
canaries over one accepted catalog differing only in the budget produce identical identities,
identical durable counts, and an identical result record but for what a clock or a filesystem
decides.

**Prefix.** A positive bound is required and zero, negative, and absent bounds refuse; `run` and
`preflight` reject a bound; a prefix processes exactly *N* members with ordinals exactly
`0 .. N-1`; source 2 is untouched; no terminal disposition, no resolution pass, no association
projection, and none of the five complete-source identities appears; the classification is
`INCOMPLETE_DIAGNOSTIC_PREFIX`; a duplicate world refuses; a work root inside the private
evidence root refuses; the operational catalog is byte-identical; the result document carries no
absolute path and is written once; and a bound equal to the whole synthetic archive still
produces a diagnostic prefix rather than a complete-source canary.

## 11. Real-data prohibition

This record authorizes implementation and tests only, over deterministic synthetic fixtures.
Under it, nothing may parse `sec_bulk_submissions`, run any real SEC source, open the preserved
D117 world for continued parsing, create a real prefix world, execute E0, create an E0-v3
namespace, enable network, or apply migration `0016`.

## 12. The bounded change set

| Path | What changed |
|---|---|
| `src/disclosure_drift/m3/working_catalog.py` | the optional `cache_bytes` budget on the D111 working catalog, the `cache_size_pragma` primitive, and read-back accessors |
| `src/disclosure_drift/m3/offline_parse.py` | the internal `max_members` cap on the accepted member stream, `materialize_planned_source_prefix`, `DiagnosticPrefixOutcome`, `DIAGNOSTIC_PREFIX_CLASSIFICATION`, and the §5 residency correction |
| `src/disclosure_drift/m3/single_source_canary.py` | the accepted 512 MiB binding, the preflight cache report, and `run_single_source_prefix_profile` with its create-once result document |
| `src/disclosure_drift/cli.py` | the `profile-prefix` mode and `--member-limit`, routing and rendering only |
| `tests/unit/test_d119_cache_and_prefix.py` | **new** — the §10 proofs |

`materialize_one_planned_source` is unchanged.

## 13. What this record does not do

It is not owner acceptance of the implementation; the completion token states readiness for owner
review only. It authorizes no D117 retry, no three-source canary, no real replay proof, no E0-v3,
no migration `0016`, no push, and no tag. It changes no frozen research definition, no evidence
contract, no digest, no capacity constant, and no schema, and it reopens neither semantic
compaction nor any deferral Decision 118 §§5–7 recorded.
