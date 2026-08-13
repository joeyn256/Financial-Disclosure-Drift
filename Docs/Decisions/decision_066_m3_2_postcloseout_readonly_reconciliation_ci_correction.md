# Decision 066 — M3.2 Post-Closeout Read-Only Reconciliation CI Correction

**Date:** 2026-08-13
**Status:** ACCEPTED — OWNER POST-CLOSEOUT CI CORRECTION AUTHORIZATION 2026-08-13
**Authority classification:** `M3_2_POSTCLOSEOUT_READONLY_RECONCILIATION_CI_CORRECTION`
**Type:** Owner **post-closeout maintenance** record. It authorizes exactly one bounded corrective
change restoring an **already-accepted** invariant — that `m3 reconcile-requests` is durably
read-only except for its own report artifact — after GitHub Actions CI exposed an implementation
defect on the Decision 065 closeout commit. It reopens no methodology, no acquisition stage, and no
milestone.

**Grants no live authority.** No SEC request is authorized or made, no network switch changes, no
CompanyFacts access is opened, no acquisition is invoked, and no real or private M3.2 evidence is
read or mutated. Investigation and proof use test fixtures only.

**Amends:** nothing in place. Decisions 001–065 remain **byte-unchanged**.

**Preserves unchanged:** every accepted M3.2 operational fact (§3 below); the annotated
`m3.2-complete` tag and its target; the accepted implementation baseline `5c4c875e…`; the Decision
065 closeout commit `2185f583…`; migrations `0001`–`0013`; the frozen receipt authority; tracked
`network.enabled` and `network.m3_acquire_enabled` at `false` / `false`; and every leakage,
filing-body, pilot-use, CompanyFacts, and Frames prohibition.

---

## 1. What happened

The Decision 065 governance closeout itself succeeded. The GitHub Actions CI run for the closeout
commit `2185f5835a711963659cf7c4067ff5a8b88349b9` then failed one **required** job — *SEC-enabled
environment (`[dev,sec]`) — required* — at the **Full pytest suite** step, `1 failed, 3622 passed,
1 skipped`.

| Fact | Value |
|---|---|
| Failing test | `tests/integration/test_m3_cli.py::test_a_transition_aware_reconciliation_writes_only_its_report` |
| Failing assertion | `assert {name: after[name] for name in before} == before, "nothing existing was modified"` |
| Command exit code | `0` (`EXIT_OK`) — the reconciliation itself was correct |
| Report artifact | created exactly as authorized (`reports/readonly.json`) |
| Durable artifact modified | `catalogs/m3_2a_operational.sqlite3` |

The reported byte difference is confined to the SQLite database header: the **file change counter**
`3 → 4`, the **database size in pages** `342 → 343`, the **first freelist trunk page** `0 → 343`, the
**freelist page count** `0 → 1`, and the **version-valid-for** counter `3 → 4`. The schema cookie and
schema format were unchanged.

## 2. The exact invariant that failed

A successful `m3 reconcile-requests` invocation may create **exactly** its authorized report
artifact, and must leave every pre-existing durable evidence artifact — including the main
operational SQLite catalog file — byte-identical.

The command satisfied the first half and violated the second. The test's assertion is correct, and
the failure is evidence of an implementation defect, not of a test defect.

## 3. Accepted state this record does not reopen

| Condition | Accepted value |
|---|---|
| C1 M3.2 successor satisfaction | 75 / 75 |
| C2 cumulative physical attempts | 77 / 801 |
| C3 predecessor identities replayed | 0 |
| C4 authoritative SQLite observations | 77 |
| C5 audit projection | 77 / 77 |
| C6 stored raw objects | 76 / 76 hash-valid |
| C7 quarterly index objects | 70 / 70 present and hash-valid |
| Gate H | PASSED / OWNER ACCEPTED |
| M3.2B | CLOSED / NOT EXECUTED / NOT REQUIRED |
| Recovery | SAFE / fully resolved |
| Continuation | permitted **no**, remaining **0** |
| Network authority | **NONE** |

No further M3.2 acquisition authority exists. These operational facts are not reopened.

## 4. Owner rulings

### R1 · Reconcile-requests is durably read-only except its report

**Defect.** The required CI test proves transition-aware reconciliation changes the existing SQLite
catalog bytes despite the accepted claim that the command is read-only except for its explicitly
requested report artifact.

**Rule.** A successful `m3 reconcile-requests` invocation may create exactly its authorized report
artifact. It **must not** modify any pre-existing durable evidence artifact, including the main
SQLite catalog file. Transient SQLite process-lifetime artefacts (`-wal`, `-shm`) and the existing
governed lease treatment remain governed by their accepted rules; they do **not** justify changing
the main database bytes.

**Generality.** General for `reconcile-requests`, including transition-aware reconciliation.

**Expected.** Before/after bytes of every pre-existing durable artifact are identical; exactly the
requested reconciliation report is newly created.

**On conflict.** Use or introduce the narrowest legitimate read-only catalog access path. Do not
weaken writer-path initialization, migrations, integrity guards, or schema enforcement merely to
satisfy this command. A broader architectural requirement is a stop condition.

### R2 · The existing CI test is normative

**Defect.** None in the assertion.

**Rule.** CI is **not** made green by excluding the SQLite database from the before/after comparison,
by comparing logical rows instead of durable bytes, by normalizing or ignoring changed timestamps, by
deleting, skipping, or xfailing the test, by weakening "nothing existing was modified", or by
changing CI to omit the `[dev,sec]` suite. Tests may be strengthened or refactored only without
weakening that claim.

**Expected.** The failing test passes because the command stops mutating the catalog, not because the
test stops observing it.

### R3 · M3.2 closeout and tag remain historical; the correction becomes the M3.3 entry software baseline

**Rule.** Decision 065, M3.2 Gate-H acceptance, and `m3.2-complete` are not rewritten, and
`m3.2-complete` is not moved. This correction is a post-closeout maintenance commit restoring an
already-accepted invariant.

If the correction is accepted and all required CI becomes green, its final commit becomes the
**current software baseline** presented for M3.3 entry governance. It does **not** replace the
recorded accepted implementation baseline `5c4c875e89ea588acd7c04414a05e566c647b39c` as historical
fact, the Decision 065 closeout commit `2185f5835a711963659cf7c4067ff5a8b88349b9`, or the
`m3.2-complete` tag target.

**Expected.** History remains linear and truthful. Only the minimum truthful current-state annotation
is authorized, distinguishing the accepted M3.2 baseline, the closeout tag, and this later
post-closeout correction.

### R4 · M3.3 implementation remains blocked until green

**Rule.** This record authorizes **no** M3.3 executable work. M3.3 governance planning may follow;
real M3.3 implementation requires a separate owner packet and its own accepted stage contract.

The corrected HEAD may be proposed as the M3.3 entry software baseline only after the targeted
correction tests pass, one complete local validation pass succeeds, and required GitHub CI for the
correction commit is green.

## 5. Root cause found

The clue in the CI byte diff — timestamp-like values changing during a supposedly read-only
invocation — is **not** the cause. The header fields that changed are SQLite's own bookkeeping
counters, and the actual write path is a **WAL checkpoint performed on connection close**:

1. `m3 reconcile-requests` opens the operational catalog exactly once, through
   `reconstruct_catalog_state` → `read_only_catalog` → `read_only_connection` →
   `connect(path, writer=False)`.
2. `connect` opened that handle with `sqlite3.connect(path)` — a **read-write** operating-system
   handle. `PRAGMA query_only = TRUE` makes SQLite reject any *statement* that would mutate the
   database, but it does not stop SQLite's automatic checkpoint when the last connection to a
   WAL-mode database closes.
3. When a committed-but-un-checkpointed WAL is present and no other connection holds the database
   open, closing that handle copies the pending log into the main database file. That is the
   observed byte change: the file grows by one page, the freed page is recorded on the freelist, and
   the change counter and version-valid-for counter both advance.

The condition was intermittent for a second, related reason. `prepare_operational_catalog`'s
read-only pre-flight, `_refuse_inconsistent_recorded_chain`, opened its connection with
`with sqlite3.connect(...) as connection:`. On a `sqlite3.Connection` that context manager governs
the *transaction*, not the connection — the connection is never closed. Because that leaked handle is
itself read-only it can never checkpoint, so it pins the `-wal` and `-shm` sidecars in place and,
while it is alive, prevents any other process from checkpointing either. Whether it was still alive
when the reconciliation subprocess ran therefore decided whether the defect surfaced — green on a
short local run, red in the full CI suite.

Both are corrected. Neither correction weakens writer-path initialization, migrations, integrity
guards, or schema enforcement.

## 6. Authorized scope

**Authorized.** `src/disclosure_drift/**`, `tests/**`, this record,
`Docs/Decisions/decision_registry.md`, `Docs/decision_index.md`, and `Milestones/STATUS.md` only as
required for truthful current-state synchronization.

**Not authorized.** Migrations, `configs/project.yaml`, `.github/workflows/**`, `pyproject.toml`,
historical Decisions 001–065, M3.2 private evidence, and M3.3 implementation files.

**Not authorized under any reading of this record:** an SEC request, live acquisition, transport
construction, network use, a snapshot, a selection, a manifest, M3.2B execution, moving, deleting,
recreating, or replacing the `m3.2-complete` tag, or tagging this correction.

## 7. Disposition

This is a post-closeout maintenance record. It changes no accepted M3.2 fact, no methodology, no
frozen research definition, no schema, and no authority. Its whole effect is to restore an invariant
the project had already accepted and to return the required GitHub CI job to green.

Until required CI for the correction commit is confirmed green, the correction commit is a
**proposed** M3.3 entry software baseline and nothing more.
