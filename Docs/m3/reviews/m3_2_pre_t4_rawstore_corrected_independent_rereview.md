# M3.2 Pre-T4 RawStore — Independent Rereview of the Corrected Streaming Candidate

**Date:** 2026-08-07
**Reviewer role:** `M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEWER`
**Model:** Claude Opus 5 — effort **Max**
**Verdict:** `M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS`

---

## 1. Independence and non-authorship

Performed in a single, genuinely fresh session whose first substantive project instruction was the
owner's rereview packet. This session did **not** record Decision 047, did **not** implement the
original RawStore streaming candidate, was **not** the first independent RawStore reviewer, and did
**not** implement the findings-scoped correction.

No subagent, delegated agent, background agent, parallel session, Git worktree, or dynamic workflow
was used. Every command ran directly in the one active session.

Both implementation completion reports were treated as **claims to falsify**, never as authority.
Every material assertion below was reproduced independently from the source, from Git, and from
reviewer-owned fixtures. The committed fixtures were **not** relied on to establish any acceptance
conclusion; they were run only as a separate corroborating signal (§10).

## 2. Baseline and authority

Read directly before judging: `CLAUDE.md`; `Milestones/STATUS.md`; Decision 047; the Decision 047
and Decision 046 entries in `Docs/Decisions/decision_registry.md`; `Docs/m3/limitations_register.md`
(M3-L13); `Docs/m3/templates/evidence_index.md`; the current and baseline `raw_store.py`; the
current and pre-correction `tests/unit/test_raw_store.py`; and the directly relevant callers
(`m3/acquisition.py`, `m3/rehearsal.py`, `sec/snapshots.py`, `sec/observation_catalog.py`,
`sec/census_orchestrator.py`, `sec/index_retrieval.py`).

Live baseline, verified from Git rather than assumed from any document:

| Fact | Verified value |
|---|---|
| Corrected candidate | `833a192839e888720389c4757250234b5cb219b7` |
| Verified tree | `c2d95badd8d137ebbb00a642d087fb03e1ec7353` |
| Subject | `Stream raw-object storage instead of buffering it` |
| Parent (Decision 047 commit) | `bc3d170a155aaa6c196536109ef57dd841226675` |
| Published `origin/main` | `e391ff3aa088b14b4be03457f5a13c0292253c86` |
| Branch / position | `main`; ahead 2 / behind 0 |
| Working tree | clean; nothing staged; zero non-ignored untracked paths |
| Tag at candidate | none; candidate not pushed |
| Pre-correction candidate (reflog) | `f723656706b65fb2db225589b6b12b55e4571c9c`, tree `3b2c0ae6…`, same parent `bc3d170a…` |

The reflog confirms `833a192…` is an **amend** of `f723656…` (`HEAD@{…}: commit (amend)`), so the
correction was folded into the single authorized candidate commit rather than added as a third one.

Protected state, verified live: `network.enabled = false`; `network.m3_acquire_enabled = false`;
`companyfacts.enabled = false` (tracked `configs/project.yaml`, and `False` defaults in
`config.py`); migrations exactly `0001`–`0013`; receipt schema `m3-execution-receipt/2.0`; no
`catalogs/` directory and no `m3_2a_operational.sqlite3`; no M3.2 run, live receipt, raw acquisition
object, or SEC evidence artifact; ceiling **801** operationally unused.

No material baseline mismatch was found, so the rereview proceeded.

## 3. Path-envelope proof

Complete local delta `origin/main` → candidate, derived independently — exactly **seven** paths,
matching the Decision 047 five-governance + two-executable envelope, **with no eighth path**:

| # | Path | Class |
|---|---|---|
| 1 | `Docs/Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md` | governance (added) |
| 2 | `Docs/Decisions/decision_registry.md` | governance |
| 3 | `Milestones/STATUS.md` | governance |
| 4 | `Docs/m3/templates/evidence_index.md` | governance |
| 5 | `Docs/m3/limitations_register.md` | governance |
| 6 | `src/disclosure_drift/sec/raw_store.py` | executable |
| 7 | `tests/unit/test_raw_store.py` | executable |

The **correction commit itself** (`bc3d170…` → `833a192…`) touches exactly the two executable paths
and **no governance byte**. This rereview session's own claim of "zero governance changes" was
therefore verified from Git, not accepted from the report.

## 4. Disposable review environment

All destructive probes and mutations ran in a disposable `git clone --no-hardlinks` outside the
repository, checked out at `833a192…` (clone tree `c2d95bad…`, clone source hashes identical to the
candidate). **No Git worktree was used.**

Import isolation was **proved, not assumed**: the project venv carries an editable `.pth` pointing at
the primary checkout, so every probe ran under `PYTHONPATH=<clone>/src` and asserted at runtime that
`disclosure_drift.sec.raw_store.__file__` resolved **inside the clone** and that its SHA-256 matched
the file under test. `PYTHONDONTWRITEBYTECODE=1` was set throughout, `pytest` ran with
`-p no:cacheprovider`, and `__pycache__` was purged before every mutation run.

After the campaign: exact candidate bytes restored, source hashes re-verified, environment deleted,
deletion verified. The primary checkout was never mutated and remained clean throughout
(`raw_store.py` = `b1b578a2482817472fa315a2c78199722a22a38429485cc03029202ed945900d`,
`test_raw_store.py` = `a54947dacc70f4dea8c7a530778821451a27056a054ce837c8ff04ee5fc3f072`).

## 5. Exact correction diff

Delta `f723656…` → `833a192…` touches only `src/disclosure_drift/sec/raw_store.py` (+115/−26 region)
and `tests/unit/test_raw_store.py` (+207). A function-level AST hash comparison across the two trees
gives the precise blast radius:

| Function | Status |
|---|---|
| `_require_one_complete_gzip_member` | **added** |
| `_measure_stored_file` | **changed** |
| `RawStore.verify` | **changed** |
| `RawStore.store` | unchanged |
| `RawStore.quarantine`, `RawStore.reconcile`, `RawStore._write_lineage_intent` | unchanged |
| `RawStore._fsync_directory`, `lineage_path`, `_iter_stored_files`, `_directory_for` | unchanged |
| `RawStore._object_id`, `_superseded_observation`, `__init__` | unchanged |
| `compress_deterministically`, `decompress`, `sha256_of` | unchanged |

**Exactly three functions changed.** Compression generation was **not** altered; the
durability/promotion path was **not** modified.

What changed behaviourally:

* `_measure_stored_file` now also counts `decompressed_size_bytes` during the same bounded drain, and
  calls `_require_one_complete_gzip_member` after `flush()`, which refuses on `not eof`,
  `unconsumed_tail`, or `unused_data`.
* `verify()` now catches `RawObjectIntegrityError` and returns `False`, and compares **four**
  identities instead of one — `stored_sha256`, `stored_size_bytes`, decoded digest vs
  `content_sha256`, decoded length vs `content_size_bytes`. The accepted baseline (`e391ff3…`)
  compared only the decoded digest, after a whole-file `path.read_bytes()`.

## 6. First-review MAJOR — disposition

The first independent review's MAJOR was that `verify()` accepted three malformed gzip stored
representations. Reviewer-owned cases were constructed independently (the committed fixtures were
**not** used for this determination). Each case starts from one canonical RawStore gzip object proven
to verify `True`, is damaged, and is then paired with a record whose stored digest and stored size
**truthfully describe the damaged bytes** — removing stored-hash mismatch as a shadowing explanation.

### R1 — trailer truncation (dropped 1, 2, 4, 8 bytes)

All four cases decode the **complete** logical payload (52 200 B, digest equal to the recorded
`content_sha256`), so they genuinely reach structural validation rather than re-covering the
short-read case. `eof = False`, `unused_data` empty. With the truthfully re-pointed record — stored
SHA, stored size, content SHA and content size all agreeing with the bytes on disk —
`verify()` is **`False`** in every case. Refuser: `stored object … ends before its gzip stream is
complete`. **CLOSED.**

### R2 — trailing garbage (37 B, 1 B, and 3 MiB spanning multiple 1 MiB read blocks)

Decoded first member correct, `eof = True`, `unused_data` non-empty. Truthfully re-pointed record →
`verify()` **`False`**. Refuser: `carries N byte(s) after the end of its gzip stream`. The 3 MiB case
confirms `unused_data` **accumulates across read blocks** (3 145 728 B surfaced), so trailing bytes
remain visible however far into the file they begin. **CLOSED.**

### R3 — concatenated second member (adjacent, 2 MiB apart, and self-concatenation)

First demonstrated positively that a normal decoder tolerates the concatenation:
`gzip.decompress(A‖B) == PAYLOAD + SECOND` (53 500 B vs 52 200 B) — gzip silently joins the members.
The candidate does not: `zlib.decompressobj(wbits=31)` stops at the first member and surfaces the
second through `unused_data`. Truthfully re-pointed record → `verify()` **`False`** in all three
variants. **CLOSED.**

**No R1/R2/R3 case verifies `True` under a truthfully re-pointed record.**

## 7. Shadowing / non-vacuity — explicit answer

For every malformed class above the rereview proved, per case: the actual bytes; expected stored
SHA-256 **==** actual stored SHA-256; expected stored size **==** actual stored size; expected content
digest **==** actual decoded digest; expected content size **==** actual decoded size; that the
candidate still rejects; and the exact remaining structural signal responsible.

**The structural gzip checks are genuinely load-bearing and are not shadowed by another identity
mismatch.** With every digest and length made truthful, the only thing left that can refuse is
`eof` (R1) or `unused_data` (R2, R3) — and it does refuse, in all ten reviewer-owned cases.

## 8. Stored and content identity — independently load-bearing

| Case | Construction | Result |
|---|---|---|
| **S1** stored SHA | gzip header **OS byte** (offset 9) XOR `0xFF`: same length, valid structure, identical decoded payload | `verify()` **False**; re-pointing the expected stored SHA to the altered representation makes the refusal **disappear** (`True`) — so the stored-SHA check is *specifically* what refused |
| **S2** stored size | bytes untouched; recorded size ±1 and +4096 | **False** each; correct size restored → **True** |
| **S3** content digest | canonical bytes untouched; recorded `content_sha256` changed | **False** (gzip and uncompressed) |
| **S4** content size | canonical bytes untouched; recorded `content_size_bytes` ±1 | **False** (gzip and uncompressed) |

**Every governed identity has its own non-vacuous killer.**

## 9. gzip structural signals — `eof` / `unused_data` / `unconsumed_tail`

The production loop was instrumented directly (spy wrapper over `zlib.decompressobj` in the module
namespace) across valid, truncated, trailing-garbage, second-member, corrupt-mid-stream and
empty-file inputs:

1. **`eof`** — reachable and load-bearing. Trailer truncation reliably leaves `eof == False` for 1,
   2, 4 and 8 dropped bytes; an empty file likewise.
2. **`unused_data`** — reachable and load-bearing. Accumulates correctly across many 1 MiB blocks.
3. **`unconsumed_tail`** — **empty at the structural gate on every path that reaches it.** The drain
   loop (`pending = inflater.unconsumed_tail`) guarantees it. The guard is therefore **redundant and
   unreachable**.

Answering the packet's five questions directly: (1) the guard is logically **harmless** — it can only
refuse, never accept, so it fails closed; (2) the draining algorithm **does** ensure bounded output —
measured max returned piece ≤ 1 MiB and max `unconsumed_tail` ≤ 1 MiB in every scenario, with
`flush()` returning **0 bytes** throughout; (3) **no** malformed input bypasses `eof`/`unused_data`
validation because the tail is drained — after `eof`, further input is disowned into `unused_data`
rather than consumed, and the gate is always reached; (4) a second member **cannot** be accidentally
consumed — `wbits = 31` stops at one member, proven by three R3 variants; (5) trailer truncation
**reliably** leaves `eof == False`.

Per the packet, the redundant-but-harmless guard is classified **OPTIMIZATION** and its removal is
**not** required. (The one case where `unconsumed_tail` is non-empty afterwards — a corrupt
mid-stream byte — never reaches the gate at all: `zlib.error` has already been converted to
`RawObjectIntegrityError` inside the loop, so the residue is never inspected.)

## 10. Independent mutation campaign

Twelve reviewer-owned mutations. For each: source change proved by hash; mutation proved **loaded**
by asserting the imported module's on-disk SHA-256 inside the probe process; smallest load-bearing
reviewer assertion run; committed suite run separately; exact bytes restored; restoration hash
verified.

| # | Mutation | Verdict | Killed by |
|---|---|---|---|
| M1 | bypass stored SHA comparison | **KILLED** | reviewer S1 + committed suite (1 failed) |
| M2 | bypass stored-size comparison | **KILLED** | reviewer S2 + committed suite (1 failed) |
| M3 | treat `inflater.eof` as always true | **KILLED** | reviewer R1 + committed suite (4 failed) |
| M4 | ignore `unused_data` | **KILLED** | reviewer R2 + committed suite (2 failed) |
| M5 | accept a concatenated second member (tolerate trailing gzip magic) | **KILLED** | reviewer R3 + committed suite (1 failed) |
| M6 | accept trailer truncation (delete the `eof` guard) | **KILLED** | reviewer R1 + committed suite (4 failed) |
| M7 | bypass decoded/content digest comparison | **KILLED** | reviewer S3 **only** — committed suite passed 39/39 |
| M8 | bypass decoded/content-size comparison | **KILLED** | reviewer S4 + committed suite (1 failed) |
| M9 | unbounded `decompress(block)` | **KILLED** | reviewer bound probe (piece grew to 67 108 864 B, peak 141 MiB) + committed suite (1 failed) |
| M10 | reintroduce whole-file `read_bytes()` verification | **KILLED** | committed suite **only** (1 failed) — the reviewer probe's stored file was too small to expose it |
| M11 | make a corrupted-but-structurally-complete representation verify | **KILLED** | reviewer S1 + committed suite (3 failed) |
| M12 | `verify()` always answers yes | **KILLED** | reviewer R1/R2/R3/S1–S4 + committed suite (13 failed) |

**12/12 KILLED. Zero `SURVIVED_EFFECTIVE`. Zero `SURVIVED_NO_OP`.** Final `raw_store.py` SHA-256
restored exactly. M7 and M10 are recorded honestly as asymmetric: the implementation kills both, but
each was caught by only one of the two independent signals — M7 is carried as **MINOR-1** (§15).

## 11. Streaming and bounded memory — non-regression

Compression generation was untouched, so this was a targeted rather than exhaustive campaign.

**Constant-memory scaling proof** — `tracemalloc` peak while the object grows **8×** (16 → 128 MiB):

| Representation | store peak growth | verify peak growth |
|---|---|---|
| gzip / highly compressible | **1.09×** | **1.11×** |
| gzip / incompressible | **1.35×** | **1.40×** |
| uncompressed | **1.00×** | **1.00×** |

Peak is a *constant* (≈ 2–5 MiB), not a proportion. The uncompressed path is flat to two decimals
(2.51 MiB store / 2.01 MiB verify) at every size.

**Decompression-bomb probe (reviewer-owned, highly compressible):** a 256 MiB logical payload stored
in 260 934 B (1029:1). Verification peaked at **3.79 MiB**, made **256** bounded `decompress` calls,
and the **largest single returned chunk was 1 048 576 B** — exactly `_STREAM_BLOCK_BYTES`. The full
logical payload never materialised in one returned decompression chunk. Decompressed size
(268 435 456) and digest were both correct.

Confirmed for uncompressed: no whole-object accumulation, incremental write, incremental stored
measurement. Confirmed for compressed: streaming compression path unchanged, no whole-object buffer,
bounded decompressor output, `max_length` retained, `unconsumed_tail` draining retained. Committed
memory regression tests ran green (`test_store_does_not_retain_the_whole_object_in_memory`,
`test_deduplication_verifies_a_large_existing_object_exactly`, and neighbours).

**M3-L13's measured defect (2.12× object size for `compress=False`, 3.80× for `compress=True`) is
closed on the lawful path.**

## 12. Deterministic gzip — non-regression

**108 cases** (12 payloads × 9 chunkings), each asserting **exact byte equality** against
`compress_deterministically(payload)`. No decompression-only comparison was used anywhere.

Payloads: empty; one byte; tiny; highly compressible 4 MiB; repetitive 3 MiB; incompressible 2 MiB;
32 KiB; 64 KiB; 1 MiB − 1; 1 MiB exactly; 1 MiB + 1; mixed 5 MiB.
Chunkings: one chunk; 1 B; 7 B; 32 KiB; 64 KiB; 1 MiB; uneven geometric; deterministic random
(seeded); empty chunks interleaved.

**108/108 byte-exact. Zero mismatches.** Each case also asserted that the emitted record's
`stored_sha256`, `stored_size_bytes`, `content_sha256` and `content_size_bytes` describe those exact
bytes, and that the canonical object verifies `True`.

## 13. `verify()` exception semantics

**Documented contract:** boolean integrity verification — "Return whether the file on disk is still
exactly the object `record` describes."

**Production callers: zero.** An exhaustive search of `src/` for `.verify(` returns no production
call site. `m3/rehearsal.py` uses `SnapshotStore.verify_payload()` and the static
`RawStore.lineage_path()`; `m3/acquisition.py` uses `verify_payload()` at four sites. The only
callers of `RawStore.verify()` are `tests/unit/test_raw_store.py` and
`tests/unit/test_m3_acquisition.py::test_verify_detects_a_hash_mismatch`, both of which assert
boolean results. No caller depends on gzip exception classes.

Measured behaviour — all object-integrity damage becomes `False` with **no exception escaping**:
malformed gzip, not-gzip-at-all, mid-deflate truncation, trailer truncation, trailing garbage,
concatenated member, empty file, single flipped payload byte. Genuine OS failures **propagate**: a
`chmod 000` file raises `PermissionError` rather than silently answering "no"; a path replaced by a
directory returns a clean `False` via the `is_file()` guard.

The change is **fail-closed** and the normalization is acceptable. Remaining exception-type delta:
**MINOR-class, benign** — the accepted baseline surfaced `EOFError`/`zlib.error` from a whole-file
`gzip.decompress`, which no caller distinguished; the candidate states the same refusal in the
method's own vocabulary.

## 14. Durability, dedup, collision, and API

The function-level hash comparison (§5) proves `store`, `quarantine`, `reconcile`,
`_write_lineage_intent`, `_fsync_directory`, `lineage_path`, `_iter_stored_files`, `_directory_for`,
`_object_id` and `_superseded_observation` are **byte-identical** to the first-reviewed candidate, so
a targeted regression set is sufficient. All targeted probes passed: `.part` staging retained; file
and directory `fsync` retained; atomic hard-link promotion; **no overwrite**; identical-destination
reuse with the original inode preserved; conflicting-destination refusal with `refusing to overwrite`
and the original bytes untouched; the refused promotion's `.part` evidence **preserved, never
deleted**; `fail_after="promotion"` raising after the atomic rename with the object surviving for
reconciliation; and no unrelated deletion. Committed durability tests ran green (39/39).

**API compatibility:** `__all__`, public method signatures, return types, `GZIP_COMPRESSION_LEVEL`,
`LINEAGE_SUFFIX`, `Compression`, file naming, and the compressed representation are all unchanged.
`_StoredFileMeasurement` gained a field but is private. **No direct caller needs any change.**

**`SnapshotStore.load_payload()` disposition.** `snapshots.py:422` uses a whole-file `read_bytes()`.
It is reached only from `sec/index_retrieval.py:363` and `sec/census_orchestrator.py:505,647`;
`census_orchestrator` is imported only by `cli.py:1083` for the **Stage M2.2 census**. The string
`load_payload` appears **nowhere in the `m3` package**, and the M3.2 live path uses the already
streaming `verify_payload()`. It is therefore **not** reachable from the M3.2 T5/T6 live acquisition
critical path:

> **`DEFERRED_OPTIMIZATION — OUTSIDE CURRENT M3.2 LIVE STORAGE PATH`**

Scope was not broadened and `snapshots.py` was **not** edited.

## 15. Findings

**BLOCKER: none. MAJOR: none.**

**MINOR-1 — the committed suite does not isolate the content-digest comparison.** Mutation M7
(`decoded_sha256 == record.content_sha256` → `True`) leaves the committed suite fully green (39/39).
No committed test anywhere mismatches `content_sha256` against an otherwise-lawful object;
`test_m3_acquisition.py::test_verify_detects_a_hash_mismatch` overwrites an uncompressed object with
`b"tampered"`, which trips the stored digest and both sizes as well. Every *other* governed identity
has a dedicated committed killer (`test_verify_binds_the_stored_hash_when_the_payload_still_decodes`,
`test_verify_binds_the_recorded_sizes[stored_size_bytes]`, `[content_size_bytes]`). **The production
check itself is correct and load-bearing** — reviewer case S3 proves `verify()` returns `False` for a
mismatched content digest on a lawful gzip object. This is a test-diagnostic weakness that does not
invalidate acceptance. Safely deferrable; the natural closure is one parametrised case extending the
existing `test_verify_binds_the_recorded_sizes` shape to `content_sha256`.

**MINOR-2 — on the malformed path only, verification memory scales with trailing-garbage length.**
`zlib` retains every post-member byte in `unused_data`, so verifying a *corrupt* object whose garbage
tail is large costs memory proportional to that tail. Measured: 1 MiB tail → 3.01 MiB peak; 8 → 16.04;
32 → 64.04; 128 → 256.04; 256 MiB tail → **512.04 MiB** peak (≈ 2× the tail). Contrast: a **valid**
256 MiB-logical object peaks at **3.79 MiB**. Characterization: the outcome is a **correct
fail-closed refusal** in every case, so there is no integrity or false-acceptance consequence; the
file is still read in 1 MiB blocks, so no whole-file *read* is reintroduced; the lawful path is
provably constant-memory (§11); the uncompressed and dedup paths construct no inflater at all and are
immune; and **no production path can reach it today** — `RawStore.verify()` has zero production
callers, and `store()` only ever measures the `.part` file it just wrote, which by construction is
exactly one member with no trailing bytes. Reaching it would require a future production caller of
`verify()` plus filesystem corruption or tampering. Precisely characterized and safely deferrable;
the natural closure is an early `unused_data` check inside the read loop.

**OPTIMIZATION-1 — redundant unreachable `unconsumed_tail` guard** (§9). Harmless and fail-closed;
removal **not** required.

**OPTIMIZATION-2 — `SnapshotStore.load_payload()` whole-file read** (§14). Off the M3.2 live storage
path; deferred, out of envelope.

## 16. Decision 047 / F4 / M3-L13 verification

Verified unchanged by the correction commit and correct on their own terms:

* Decision 047 **authorizes** the two-path pre-T4 RawStore substage (047-B), narrowly releasing
  Decision 045 §16's prohibition for this substage only.
* F4 adds **exactly three** evidence-index artifact types — `frozen_object_identity_set`,
  `derived_reference_set`, `reconciliation_report` — and **no fourth**.
* **`operational_preflight_attestation` is not added.** The token appears in the repository only as an
  explicit negation (Decision 047 lines 93 and 175, `evidence_index.md` line 107, and the registry).
* T4 execution is **not** complete; T5/T6 remain **unauthorized**; network remains disabled; the real
  operational catalog remains **uncreated**.
* **M3-L13 remains `ACTIVE`**, pending an independent PASS and the owner's separate acceptance. It was
  **not** modified by this rereview.

## 17. Validation

Focused: `tests/unit/test_raw_store.py` — **39 passed** (0.54 s). Direct consumers
(`test_m3_acquisition.py`, `test_sec_snapshots.py`, `test_observation_catalog.py`,
`test_m3_recover.py`, `test_m3_recovery.py`) — **449 passed** (17.30 s).

Static: `ruff check .` → *All checks passed!* (0.06 s). `ruff format --check .` → *145 files already
formatted* (0.01 s). `mypy src` → *Success: no issues found in 76 source files* (0.27 s).

Repository: `make secrets` → 290 files scanned, **0 findings** (0.55 s). `make hygiene` → 292 paths,
**0 findings** (0.14 s). `make context` → migration count 13; latest decision 047; both network
switches `false`; stage and blocker as recorded (0.34 s).

Full suite: the canonical `make check` gate ran to completion through its final gate (2 m 13 s). Its
pytest summary was not captured from that invocation, so the suite was executed once more with
capture — this was an output-capture omission on the reviewer's part, **not** a nondeterminism
concern, and both runs were green:

> **3246 passed, 1 skipped in 123.04 s — exit 0**

**Skip inventory — exactly one skip, enumerated in full:**

| Test | Reason |
|---|---|
| `tests/unit/test_m23_pilot_manifest.py:429` | `snapshot_state is a fixed literal asserted before hashing` |

This is the known pre-existing intentional skip recorded at Decision 042. **No other test was
skipped.** `tests/unit/test_httpx_transport.py` **ran and was not skipped** — 30 tests collected,
**30 passed**, confirmed both in the full run and by an explicit isolated execution.

## 18. Verdict

Reviewer-owned evidence, not the committed fixtures, establishes that the corrected candidate closes
the first review's `RawStore.verify()` MAJOR by proving the exact immutable stored representation,
while preserving streaming storage, bounded memory, deterministic gzip bytes, content and stored
identities, durability, atomicity, deduplication, and the public API.

**BLOCKER = 0. MAJOR = 0.** Two MINOR and two OPTIMIZATION findings remain, each precisely
characterized and safely deferrable.

> ### `M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS`

## 19. Network and operational state at completion

No network access was attempted or made at any point. `network.enabled = false`;
`network.m3_acquire_enabled = false`; CompanyFacts disabled; migrations `0001`–`0013`; receipt schema
`m3-execution-receipt/2.0`; no operational catalog; no M3.2 run; no live receipt; no raw or live SEC
object; ceiling **801** unused. T4 was not executed, T5/T6 were not begun, and no tag or push was
created by this rereview.
