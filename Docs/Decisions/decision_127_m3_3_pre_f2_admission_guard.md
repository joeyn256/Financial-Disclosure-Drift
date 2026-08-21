# Decision 127 — The Pre-F2 Free-Space Admission Guard

```text
STATUS: IMPLEMENTED — READY FOR INDEPENDENT REVIEW; NOT YET OWNER-ACCEPTED
RECORD_TYPE: THE MINIMAL SAFETY IMPLEMENTATION AUTHORIZED BY DECISION 126 §7 (D126-R6),
  PUBLISHED WITH THE IMPLEMENTATION IT RECORDS
DATE: 2026-08-20
OWNER: Joey authorization; Sol/GPT-5.6 owner instrument
AUTHORIZED BY: M3_3_D126_PUBLICATION_AND_D127_PRE_F2_GUARD_IMPLEMENTATION_AUTHORIZED
OUTCOME: M3_3_D127_PRE_F2_GUARD_IMPLEMENTATION_READY_FOR_INDEPENDENT_REVIEW
SCOPE: ONE FROZEN CONSTANT, ONE GUARD BETWEEN F1 AND F2, AND THREE FOCUSED PROOFS —
  NOTHING ELSE
CLOSES: the Decision 126 §7 implementation gap — the sole blocker on the complete-source path
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_V3_EXECUTION_AUTHORIZATION: NO
F1_EXECUTION_AUTHORIZATION: NO
F2_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
DISPOSABLE_WORLD_CREATION_AUTHORIZATION: NO
CATALOG_WRITE_AUTHORIZATION: NONE
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The minimal pre-F2 admission-guard implementation that
[Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md) §7 (D126-R6)
authorized, and nothing beyond it.

## 1. What this record is, and what it is not

**It is an implementation record, published with the implementation it describes.** Unlike
Decisions 120 through 126, it is **not** retrospective: the code, its tests, and this record land
together, and the record's claims are claims about tracked source a reviewer can read.

**It closes the one blocker Decision 126 named.** D126 measured every live-state predicate as
passing and returned `NOT_READY_IMPLEMENTATION_GAP` on exactly one ground: the complete-source path
contained no `>= 30 GiB` disk admission predicate between F1's return and F2's transaction opening,
as accepted [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5) requires.
**This record supplies that predicate.**

**It is not an acceptance, and it is not an authorization.** It is **ready for independent review**
and has not been owner-accepted. **No owner-acceptance token is emitted by it.** Complete source
remains **NOT authorized** and E0 remains **NOT authorized** — §7 states what remains closed and why
closing the gap does not open the run.

**It is deliberately smaller than the problem it belongs to.** D124-R5 states five safety
requirements. D126 §8 (D126-R5) established that four of them are enforceable by the launch wrapper
or are already true by construction, and that **exactly one** needed repository code. This record
implements that one. The `105 GiB` starting gate, the continuous `10 GiB` floor, and the
`SQLITE_TMPDIR` placement are **not** in production code, and their absence here is the accepted
D126-R5 disposition rather than an omission.

## 2. The change

**One file changed**, `src/disclosure_drift/m3/single_source_canary.py`, in three places, plus one
new test module. **`57` added lines, `0` removed, `0` modified.**

### 2.1 The frozen constant

```python
PRE_F2_MINIMUM_FREE_BYTES: Final = 30 * 1024**3
```

**`32,212,254,720` bytes.** It sits with the module's other frozen execution parameters, carries the
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5) and
[Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md) §7 (D126-R6) authority in
its own documentation, and is exported in `__all__` so a reviewer can pin it from outside the module.

**It is an admission predicate, not a budget.** It moves no row, no ordering, no digest, and no
identity, and F2's behaviour at or above the floor is byte-for-byte what it was before.

### 2.2 The guard

```python
def _require_pre_f2_free_space(directory: Path) -> int:
    free = shutil.disk_usage(directory).free
    if free < PRE_F2_MINIMUM_FREE_BYTES:
        ...
        raise SingleSourceCanaryError(message)
    return free
```

**The comparison is strict `<`**, so the floor itself admits: `>= 30 GiB` is the accepted rule, and
`30 GiB` exactly is inside it. **The refusal names three facts** the owner instrument required — the
**actual free bytes**, the **required minimum**, and that **F2 was refused before its single
transaction opened**. It names **no path**, in keeping with the rest of the module.

**It raises `SingleSourceCanaryError`**, the module's existing precondition failure, which is
documented as *never worked around, never retried in place*. Nothing catches it on this path, so the
refusal terminates the run.

### 2.3 The call site

Inside `_materialize`, between the two statements that were previously adjacent:

```text
F1     catalog.count_persisted_accession_resolutions(...)
GUARD  _require_pre_f2_free_space(working.path.parent)
F2     materialize_census_associations(connection, compact_evidence=True)
```

**Free space is measured on the disposable world's own volume** — `working.path.parent` is the
run-local directory holding the working catalog and its write-ahead log, which is the storage F2's
transaction actually consumes.

**The [Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md) §6.4 ordering is
unchanged.** Resolution still runs before projection, for the reason that ordering exists; the guard
is inserted between them and reorders nothing.

### 2.4 Why it must be here

**This is the whole argument, and [Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md)
§7 records it as an owner finding rather than an implementation preference.** An external sampler
cannot satisfy the predicate, for four independent reasons:

1. **No enforceable pause exists at the boundary** — F1 returns and F2 begins in consecutive
   statements.
2. **Ledger state does not distinguish F1 from impending F2** — nothing durable changes there.
3. **An external process can signal but cannot decline admission atomically** — a signal is
   advisory where admission must be dispositive.
4. **A sampling race remains regardless of cadence** — a sample describes a different instant than
   the one that matters. Tightening the interval shrinks the race; it never closes it.

**Only the path that is about to open the transaction can decline to open it.** That is why one
line of production code was required where four other D124-R5 requirements needed none.

## 3. The proofs

`tests/unit/test_d127_pre_f2_admission_guard.py`, six tests, all passing.

| Claim | Proof |
|---|---|
| the constant is exactly `30 GiB` | pinned to the literal `32_212_254_720` **and** to `30 * 1024**3`, and its presence in `__all__` is asserted |
| **A — below the floor refuses** | at `PRE_F2_MINIMUM_FREE_BYTES - 1` the guard raises, and the message carries the actual bytes, the minimum, and the "refused before its single transaction opened" statement |
| **A — F2 is never called** | a real end-to-end run below the floor with F2 **replaced by a tripwire** that records its own invocation: the run refuses, and the tripwire's record is empty |
| **B — the floor admits** | parameterized at exactly `PRE_F2_MINIMUM_FREE_BYTES` **and** at one byte above it |
| **C — ordering** | a real end-to-end run above the floor logs `["F1", "GUARD", "F2"]` from the three **real** participants, each wrapped rather than replaced |
| refusal is not a partial write | the accepted catalog's digest is byte-identical after the refusal, carrying [Decision 116](decision_116_m3_3_disposable_single_source_canary_path.md) §10 through the new gate |

**The tests are proved non-vacuous by mutation**, because a test that passes against a missing guard
proves nothing:

| Mutation | Result |
|---|---|
| the guard call deleted from `_materialize` | **2 failures** — the F2 tripwire fires, and the ordering log loses `GUARD` |
| `<` weakened to `<=` (refusing at the floor) | **1 failure** — the exactly-at-the-floor case is refused, and B catches it |

Both mutations were applied to the working tree, measured, and reverted; the restored tree is the
one published here.

**Free space is pinned in every test**, so no proof depends on how much space the measuring machine
happens to have. That is sound because **line 890's comparison is the only free-space comparison in
the module** — every other `shutil.disk_usage` call there records a number into a result document and
gates nothing.

## 4. What did not change

**Everything the owner instrument prohibited, and this list is the point of the record.**

| Prohibited by the D127 instrument | State |
|---|---|
| the `105 GiB` launch gate in production code | **not added** — wrapper-enforced (D126-R5) |
| the continuous `10 GiB` monitor rule in production code | **not added** — monitor/wrapper-enforced (D126-R5) |
| `create_world` | **untouched** |
| temporary-directory handling | **untouched** — `SQLITE_TMPDIR` stays wrapper-set (D126-R5) |
| the F1 and F2 algorithms | **untouched** — the guard sits between them and changes neither |
| write-ahead log, checkpoint, cache, `synchronous` settings | **untouched** |
| schemas and migrations | **untouched** — head stays `0015`, `0016` stays absent |
| E0 and the authority constants | **untouched** — all three stay `None` |
| network | **not enabled** — both tracked switches stay `false` at request ceiling `0` |
| any canary run | **none executed** |

**No evidence, catalog, or source byte was read for mutation or written.** No disposable world was
created outside the test suite's own temporary directories, no run namespace was consumed, and no
governed SQLite writer was opened against the operational catalog.

## 5. One accepted limitation, stated rather than smoothed

**The guard applies to every run of this path, including the synthetic unit tests.** The Decision 116
and Decision 119 suites build three-member synthetic worlds needing kilobytes, and those runs now
also have to clear a `30 GiB` machine-wide floor. **On a machine with less than `30 GiB` free, those
suites would fail at the admission gate** rather than at anything they are testing.

**This is a consequence of the authorized scope, not a defect in it.** The instrument authorizes
exactly one frozen constant and one guard; making the floor injectable, environment-scoped, or
test-overridable is scope expansion, and a test-overridable safety floor is a weaker artifact than
the one D124-R5 asked for. **It is recorded here so a later reader meets it as a known disposition
rather than as a mystery**, and the new proofs themselves pin free space precisely so that they never
depend on the measuring machine.

The exposure is bounded in practice: the project's own capacity governance already requires
`>= 105 GiB` free before a complete-source run, and Decision 126 §4 measured `127.1971 GiB` free at
preflight exit.

## 6. Validation

| Gate | Result |
|---|---|
| focused D127 tests | **6 passed** |
| mutation proofs | **2 mutations, both caught** |
| nearest affected suites — D116, D119, D127, offline parse, D112 | **210 passed** |
| Ruff lint, touched files | **all checks passed** |
| Ruff format check, touched files | **2 files already formatted** |
| mypy strict, whole `src` | **no issues in 93 source files** |
| full acceptance gate | recorded in the session completion report |

## 7. What this record does not do

**It authorizes no execution.** No complete-source run, no E0, no E0-v3, no F1, no F2, no canary of
any kind, no disposable run world, no migration `0016`, no network, and no acquisition. **Closing the
D126 §7 gap does not open the run** — it removes the reason the run could not be authorized, which is
a different thing from authorizing it.

**It is not owner-accepted.** The outcome token is
`M3_3_D127_PRE_F2_GUARD_IMPLEMENTATION_READY_FOR_INDEPENDENT_REVIEW`. **Independent review comes
first**, then owner acceptance, and only then the two things
[Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md) §10 (D126-R8) requires
before any run: **a regenerated run identity and command**, and **a new final live preflight**. The
D126 run identity `m3_3_d126_complete_first_source_v1` is **not** revived by this record — D126-R8
retired it precisely because this change was coming, and this is the change.

**It relaxes no gate.** The `105 GiB` starting gate, the continuous `10 GiB` floor, the no-`VACUUM`
rule, and the explicit `SQLITE_TMPDIR` placement all stand exactly as
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 and
[Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md) §8 leave them, enforced
where those records place them.

**It supersedes nothing.** Decisions 121 through 126 stand as written.

**All three activation constants remain `None`**, the operational catalog remains at migration head
`0015`, migration `0016` remains absent and unapplied, no E0-v3 namespace exists, and both tracked
network switches remain `false` at request ceiling `0`.

**Complete source is NOT authorized. E0 is NOT authorized.**
