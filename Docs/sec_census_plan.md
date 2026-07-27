# Milestone 2 census plan

Governing records: Decisions 007, 008, 009, 010, 011, 012.
Policy versions: `quarterly-index-instances/1.0`, `index-retrieval-orchestration/1.0`.

This document describes how a Stage M2.2 census run is planned, executed, resumed, and
judged complete. It does not change any frozen research definition.

---

## 1. Explicit plan inputs

Every planning input is supplied by the operator. **Nothing is inferred from the clock**,
in planning or in parsing, because a plan that depends on the day it ran is not
reproducible and would silently reclassify an unfinished quarter as a missing one.

| Input | CLI argument | Meaning |
|---|---|---|
| `coverage_start` | `--coverage-start` | First date of the requested coverage window |
| `coverage_end` | `--coverage-end` | Last date of the requested coverage window |
| `as_of_date` | `--as-of` | Date the plan is evaluated against |
| open-quarter opt-in | `--include-open-quarter` | Also retrieve the provisional open quarter |
| calendar year | `--calendar-year` | Year the annual EDGAR calendar must cover |

The three date arguments must be supplied together. A partial window is refused rather
than completed from today's date. The intended project coverage begins with support year
2009, but no runtime as-of date is hardcoded anywhere.

## 2. Quarterly instance generation

The quarterly company index is the required reconciliation unit. Every quarter
intersecting the coverage window is generated and classified:

| Kind | Condition | Required | Effect on completion |
|---|---|---|---|
| `required_closed_quarter` | quarter end ≤ `as_of_date` | yes | Missing, failed, malformed, unavailable, or unreconciled **blocks completion** |
| `provisional_open_quarter` | quarter contains `as_of_date` | optional | Retrieved only when explicitly included; reported separately; **never finalized**; failure never fails closed-quarter completion |
| `not_planned` | quarter starts after `as_of_date` | no | Not requested, **not missing**, not a failure |

A quarter that only partially intersects the window is planned in full, because the index
instance is published per quarter and cannot be requested in part. Future quarters get no
persisted row at all, so they can never later read as missing.

An annual index is never a substitute for a missing required quarterly instance. Any
future annual support would be an additional reconciliation layer only.

## 3. Chronological sequential retrieval

One worker, chronological order, through the existing `SecClient`. There is no parallel
downloader and no second rate limiter. Every request keeps the existing identity
validation, aggregate rate limiting, bounded retries, global cooldown, redirect
containment, URL-family containment, block-page handling, snapshot reuse, and recovery
protections.

Required closed quarters are processed oldest first, so a stopped run always resumes at
the earliest gap. The provisional open quarter is processed only after every required
closed quarter, so an open-quarter problem can never consume the budget or the run before
the historical record is complete.

Per instance, in order: confirm the plan row; construct only the approved quarterly index
URL; prove no filing-document or accession URL can be constructed; retrieve or validly
reuse the snapshot; verify raw-object identity and hashes; parse the fixed-width index;
persist raw, parsed, malformed, and normalized rows; reconcile against persisted
submissions observations; feed permitted lower-authority evidence into Decision 012
resolution; rebuild affected canonical accession projections; persist reconciliation and
completion state; update the coverage report.

An instance is **not** marked satisfied until retrieval or reuse, raw verification,
parsing, persistence, reconciliation, and the required QA gates all pass.

## 4. Plan-derived logical budget

```
budget = unsatisfied required closed-quarter instances
       + explicitly included unsatisfied provisional open-quarter instance
```

Each unsatisfied planned instance may initiate **at most one logical retrieval** per
orchestration pass. The existing bounded HTTP retry policy may make several actual
attempts inside that one operation. No arbitrary lower fixed cap is applied: a 2009-2024
plan is a budget of 64.

Logical and actual counts are accounted and reported separately, and are never conflated:

instances planned · already satisfied · logical retrievals initiated · actual HTTP
attempts · retries · successful · failed · remaining.

## 5. Resumability

Each instance's lifecycle state is persisted transactionally as it advances, through
`planned`, `retrieval_started`, `retrieved`, `validly_reused`, `parsed`, `reconciled`,
`satisfied`, `failed`, `blocked`, `unavailable`, and `indeterminate`. Every transition is
also appended to `census_index_instance_events`, so a resumed run can prove what an
earlier process had already done.

On restart or rerun the loop verifies the persisted raw object and its hashes, verifies
parser and reconciliation lineage, treats a fully verified satisfied instance as satisfied
through the existing reuse mechanism, does **not** retrieve it again merely because an
earlier process stopped, and resumes from the earliest unsatisfied required instance. All
earlier attempts and observations are preserved. Failed evidence is never overwritten or
deleted. A new source version or an explicit refresh creates a new observation and a new
reconciliation result under the existing versioning policy; a previous snapshot is never
silently mutated.

Before retrieval begins, startup verifies the exact applied migration chain against the
packaged SQL and reconciles the JSONL observation projection against authoritative
SQLite. Projection validation is identity- and content-based rather than flag-based:
missing, truncated, malformed, prefix-only, duplicate, unknown, modified, reordered, or
garbage-appended files are rebuilt deterministically. The replacement is not accepted
until its temporary file and destination directory have both been `fsync`ed. The
detected condition and rebuild hash remain in projection-recovery history. An unresolved
failure is release-blocking and prevents census completion; a verified rebuild resolves
the block without altering any immutable observation.

Conditional and byte-identical reuse verify the prior object, authoritative storage
representation, hashes, sizes, parser compatibility, source/request identity, and
object-owner lineage before sharing it. Verification uses bounded streaming reads and
rejects absolute, traversing, or symlinked catalog paths. Complete metadata and
archive-member lineage are copied to the new retrieval observation. A reusable stream is explicitly owned:
callers exhaust it or close it (directly or through a context manager), and any iteration
failure closes the local spool.

## 6. Failure continuation and global stop conditions

An ordinary per-instance failure persists its terminal evidence, keeps the census
incomplete, names the exact quarter and reason, and allows later planned quarters to
proceed.

The loop stops immediately, and the run remains resumable, when: SEC identity or
configuration validation fails; a global cooldown or blocking response requires stopping;
network containment fails; the configured global request boundary is reached; catalog
writer ownership is lost; or a release-blocking recovery failure makes further writes
unsafe.

## 7. Completion and coverage semantics

`completed=True` requires every required closed-quarter instance satisfied, every other
required census source satisfied, and all R1 global completion gates passed. It does
**not** require an excluded or failed optional open quarter.

Coverage is reported with finalized and provisional parts kept apart:

- required closed quarters planned, successful, and failed or unavailable;
- provisional open quarter, and whether it was retrieved;
- future quarters not planned;
- `finalized_reconciliation_coverage` — satisfied closed quarters only;
- `provisional_reconciliation_coverage` — the open quarter, when retrieved.

A run never claims finalized coverage through the open quarter or any future period.
`coverage_start`, `coverage_end`, `as_of_date`, and the exact instance list are all
included in the deterministic census-plan hash, so two plans agree only when they
requested exactly the same thing.

## 8. Bulk stream size: an intentional nondecision

**No maximum transport size is imposed on legitimate SEC bulk metadata sources.** This is
a deliberate nondecision, recorded so that its absence is understood as a choice rather
than an oversight.

The reasoning is that a byte ceiling invented without evidence is not a safety control.
The bulk submissions archive is large by nature and grows over time, so a guessed cap
would eventually refuse or truncate exactly the legitimate source the census depends on,
and it would do so as an apparent integrity failure rather than as the configuration
mistake it actually was. A limit that fails honest data while a malicious response is
already contained by other means adds risk instead of removing it.

Containment therefore comes from mechanisms that do not depend on knowing the size in
advance, all of which remain in force:

- **bounded-memory disk spooling** — a streamed response is written to a local spool and
  read in bounded chunks; response size never dictates resident memory;
- **archive protections** — per-member and cumulative expansion limits, an expansion-ratio
  guard, a member-count limit, and refusal of corrupt archives;
- **validation before trust** — content-type, source-family, URL-containment, redirect
  boundary, block-page, and parser checks;
- **deterministic cleanup and explicit stream closure** — the spool closes on exhaustion,
  explicit close, context exit, and iteration failure, idempotently.

Two limits that do exist are unaffected and are not size policy for a source. The
in-memory ceiling for a *buffered* payload still requires large responses to stream rather
than be held in memory, and the same ceiling bounds how much of a rejected payload is
materialized as quarantined evidence, with any truncation recorded.

**Spooling successfully is not acceptance.** A large source that spools must still satisfy
every integrity, storage-representation, archive, parser, reconciliation, and QA gate; one
that fails any of them is failed or quarantined with its evidence preserved. This
nondecision grants no permission for an unbounded in-memory read.

Introducing a source-specific byte ceiling later is a separate, documented decision. It
requires an evidence basis — observed sizes for the specific official source — and a
compatibility review against legitimate SEC source sizes across the covered period, so
that the limit cannot silently exclude valid data.

## 9. Dry run

`sec census --dry-run` prints the coverage window, the as-of date, required closed-quarter
count, satisfied and remaining required instances, the included or excluded open quarter,
the logical retrieval budget, logical retrievals and actual attempts (both zero), finalized
and provisional coverage, every planned instance, and the plan hash. It reports zero
requests and `census completed: no`, and makes no request of any kind.
