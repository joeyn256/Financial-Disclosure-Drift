# Decision 048 — M3.2 Pre-T4 RawStore Acceptance and Publication

**Date:** 2026-08-07
**Status:** ACCEPTED — OWNER APPROVED 2026-08-07
**Type:** Bounded governance record accepting the corrected **pre-T4 RawStore streaming** substage and
its fresh independent PASS rereview, **closing limitation M3-L13**, and publishing the complete local
lineage by one normal fast-forward push. **Not** a preregistration deviation. It changes no
hypothesis, cohort window, maturity gate, outcome definition, threshold, seed, selection methodology,
S4/S5/S6 identity, hash preimage, migration byte, implementation byte, test byte, or configuration
byte — **no executable byte changes with this record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–047 are byte-unchanged.
The accepted M3.2 contract, `Docs/m3/templates/evidence_index.md`, and the durable review artifact are
all byte-unchanged by this record. Stage progress is recorded here, in the registry, and in the
ledger — never in the contract.
**Related:**
[Decision 047](decision_047_m3_2_t4_operational_preflight_authorization.md) (the authorizing record
whose §6 substage authority this record exhausts, and whose ruling **047-J** required the fresh
independent review this record accepts);
[Decision 046](decision_046_m3_2_t3_acceptance_and_publication.md) (T3 acceptance, unchanged);
Decisions 039, 040, 042, 045; the durable review artifact
[`Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md`](../m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md);
the limitations register [`Docs/m3/limitations_register.md`](../m3/limitations_register.md);
the accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of the corrected pre-T4 RawStore streaming correction at the exact
candidate named in §3, the owner's acceptance of the fresh independent PASS rereview and its durable
artifact named in §4, the closure of the first review's acceptance-blocking `verify()` finding (§5),
the dispositions of MINOR-1, MINOR-2, OPTIMIZATION-1, and OPTIMIZATION-2 (§6), the **closure of
M3-L13** (§7), the acceptance for publication of the Decision 047 **F4** vocabulary extension (§8),
the recorded T4/T5/T6 state (§9), and the publication of the complete four-commit lineage by one
normal fast-forward push (§11).

---

## 1. What this record accepts, and what it does not

Seven determinations, which must not be collapsed:

1. **Implementation acceptance.** The corrected **pre-T4 RawStore streaming** substage is accepted at
   the exact candidate and tree named in §3. The acceptance is **SHA-specific and tree-specific** and
   does not transfer automatically to a later changed tree.
2. **Review acceptance.** The fresh independent non-author rereview, its verdict, and its durable
   repository artifact are accepted (§4).
3. **Finding closure.** The first independent review's acceptance-blocking `RawStore.verify()`
   finding is **CLOSED** (§5). No further RawStore correction is required before T4.
4. **Limitation closure.** **M3-L13 is CLOSED** by this record (§7).
5. **F4 acceptance for publication.** The Decision 047 F4 evidence-index vocabulary extension is
   accepted and published as part of the Decision-047 lineage, unchanged (§8).
6. **Publication.** Decision 047, the accepted candidate, the accepted review commit, and this
   acceptance commit are published together above the published Decision 046 baseline by **one normal
   fast-forward push** (§11). **No tag.**
7. **What this record is not.** It is **not** T4 execution, **not** T5 or T6 authority, **not**
   network authority, and **not** live-operation authority. Nothing here may be read as T4 execution
   or Gate H satisfaction, and nothing here permits a live SEC operation, a real operational catalog,
   a live M3.2 run, or any use of the approved request ceiling **801**.

## 2. The owner determination, recorded without alteration

The owner's determination for this acceptance was issued as the Decision 048 recording packet itself.
It carries **no separately named `OWNER_DECISION_048_…` instrument token**, and none is invented here
— the same convention accepted Decisions 046 and 047 record. Its operative terms are:

```text
M3.2 — DECISION 048
PRE-T4 RAWSTORE ACCEPTANCE AND PUBLICATION

The owner accepts the corrected pre-T4 RawStore streaming correction and its
fresh independent PASS rereview, closes M3-L13, and authorizes one normal
fast-forward publication push. T4 execution has not occurred.
```

Where this record summarizes for navigation, the owner's own terms control.

## 3. Ruling 048-A — accepted corrected RawStore candidate

| Fact | Accepted value |
|---|---|
| **Accepted candidate** | `833a192839e888720389c4757250234b5cb219b7` |
| **Accepted tree** | `c2d95badd8d137ebbb00a642d087fb03e1ec7353` |
| **Subject** | `Stream raw-object storage instead of buffering it` |
| **Parent (Decision 047 governance baseline)** | `bc3d170a155aaa6c196536109ef57dd841226675` |
| **Envelope** | exactly two executable paths — `src/disclosure_drift/sec/raw_store.py`, `tests/unit/test_raw_store.py`; **no third path** |
| **Tag** | none |

The accepted candidate:

* **removes full-object buffering** from the governed RawStore storage path;
* **preserves the deterministic stored representation** — the streaming compressor's output is
  byte-identical to `compress_deterministically`;
* **preserves content and stored identities** — `content_sha256`, `stored_sha256`,
  `content_size_bytes`, and `stored_size_bytes` are unchanged in meaning and value;
* **preserves durability and atomic create-once semantics** — `.part` staging, file and directory
  `fsync`, no-overwrite hard-link promotion, evidence preservation after failure;
* **preserves deduplication and collision semantics**;
* **keeps the public `RawStore` API unchanged**;
* **corrects `verify()`** so that the exact immutable gzip representation is structurally validated,
  not merely decoded.

**This acceptance is SHA-specific and tree-specific. It does not transfer automatically to a later
changed tree.**

## 4. Ruling 048-B — accepted independent rereview

| Fact | Accepted value |
|---|---|
| **Artifact** | `Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md` |
| **Artifact SHA-256** | `7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42` |
| **Review commit** | `9406afbe88e83f7a0f0a52db290f9a220d01e6bc` |
| **Verdict** | `M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS` |
| **Findings** | **BLOCKER 0 · MAJOR 0 · MINOR 2 · OPTIMIZATION 2** |

**The substantive acceptance threshold is satisfied: BLOCKER = 0 and MAJOR = 0.**

The accepted rereview independently established, by reviewer-owned fixtures rather than the committed
ones: all three malformed-object classes refused; every malformed record re-pointed so its stored
digest and stored length **truthfully describe the damaged bytes**, proving the structural checks are
load-bearing and **not shadowed** by an identity mismatch; a non-vacuous killer for each of the four
governed identities; `eof` and `unused_data` reachable and load-bearing, with `unconsumed_tail`
redundant and unreachable only; bounded memory for valid objects; **108/108** reduced
deterministic-gzip cases byte-exact; **12/12** independent mutations `KILLED`; a full suite of
**3,246 passed / 1 pre-existing unrelated skip** (the fixed-literal skip in
`tests/unit/test_m23_pilot_manifest.py`); **`tests/unit/test_httpx_transport.py` 30 passed / 0
skipped**; Decision 047 and F4 unchanged; and M3-L13 `ACTIVE` pending this owner acceptance.

## 5. Ruling 048-C — the first-review MAJOR is closed

The earlier acceptance-blocking `RawStore.verify()` finding is **CLOSED**. The corrected candidate
independently proves rejection of:

1. **trailer-truncated gzip** — refused by the inflater's end-of-stream flag, with the complete
   logical payload still decoding and hashing correctly;
2. **valid gzip plus trailing garbage** — refused by `unused_data`, which accumulates across bounded
   read blocks however far into the file the extra bytes begin;
3. **concatenated / second gzip members** — refused by `unused_data`, where `gzip` itself would
   silently join the members into one longer logical payload.

The rereviewer proved these refusals are **not shadowed** by stored or content identity mismatches:
with every digest and length made truthful to the damaged bytes, the structural check is the only
condition left that can refuse, and it does.

**No further RawStore correction is required before T4.**

## 6. Rulings 048-D through 048-G — the four carried findings

None of the four reopens the accepted candidate. **No new limitations-register entry is created for
any of them.**

### 6.1 Ruling 048-D — MINOR-1

**`ACCEPTED_NONBLOCKING_TEST_STRENGTH_OBSERVATION — DEFERRED`**

**Finding.** The committed RawStore unit suite does not contain one isolated mutation killer for the
`content_sha256` comparison.

**Disposition.** Production `content_sha256` enforcement is independently demonstrated correct; the
reviewer-owned S3 falsification kills removal of the production check; **no production correctness
defect exists**; no correction is required before T4; the accepted candidate is **not** reopened
merely to add one redundant test; and any later test-strength cleanup requires separate authority.

### 6.2 Ruling 048-E — MINOR-2

**`ACCEPTED_NONBLOCKING_CORRUPT_PATH_RESOURCE_OBSERVATION — DEFERRED`**

**Finding.** `zlib` may retain a large trailing-garbage tail in `unused_data` while verifying an
already-corrupt gzip object.

**Disposition.** Invalid objects remain **correctly refused**; valid and lawful object verification
remains **bounded-memory**; `RawStore.verify()` has **zero production callers**; the M3.2 live storage
path does not rely on this corrupt-object verification call; **no live-operation safety defect
requiring T4 remediation is established**; and no correction is required before T4.

### 6.3 Ruling 048-F — OPTIMIZATION-1

**`ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED`**

The `unconsumed_tail` final guard is redundant because the bounded decompression loop drains it
before the structural gate. It is **harmless and fail-closed** — it can only refuse, never accept.
**Do not remove it now.**

### 6.4 Ruling 048-G — OPTIMIZATION-2

**`ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED`**

`SnapshotStore.load_payload()` uses a whole-file read, but the rereview established that it is
**outside the M3.2 live acquisition and storage critical path** and appears **nowhere in the `m3`
package** — it is reachable only from the Stage M2.2 census. **M3.2 T4 scope is not broadened to fix
it.**

## 7. Ruling 048-H — M3-L13 is closed

**M3-L13** — `RawStore.store()` buffered the whole object in memory — is **CLOSED** under the
existing limitations-register schema. Its historical description is **preserved and not rewritten**.

Closure evidence, as required:

| # | Item | Value |
|---|---|---|
| 1 | Decision 047 authorization | `bc3d170a155aaa6c196536109ef57dd841226675` |
| 2 | Accepted corrected implementation | `833a192839e888720389c4757250234b5cb219b7` |
| 3 | Accepted candidate tree | `c2d95badd8d137ebbb00a642d087fb03e1ec7353` |
| 4 | Independent PASS artifact | `Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md` |
| 5 | Artifact SHA-256 | `7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42` |
| 6 | Review commit | `9406afbe88e83f7a0f0a52db290f9a220d01e6bc` |
| 7 | Owner acceptance | **Decision 048** |

Status becomes **`CLOSED — DECISION 048`**, and the register's summary counts are updated truthfully
(**35 open, 4 closed**). **No other limitation is closed by this record.** `D023-O1` remains
`LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED` and is unchanged.

## 8. Ruling 048-I — Decision 047 and F4 accepted for publication

Decision 047 remains accepted **exactly as recorded** and is **byte-unchanged** by this record. The
**F4** vocabulary extension remains exactly:

* `frozen_object_identity_set`
* `derived_reference_set`
* `reconciliation_report`

**No fourth type.** **No `operational_preflight_attestation` is added** — the token exists in the
repository only as an explicit negation. The F4 edit to `Docs/m3/templates/evidence_index.md` is
accepted and published as part of the Decision-047 lineage, and that file is **byte-unchanged by this
record**. **No further F4 change is required before T4 execution.**

## 9. Ruling 048-J — the T4 state after this record

After Decision 048 is recorded and published:

* Decision 047 is **accepted and published**;
* the pre-T4 RawStore correction is **accepted and published**;
* its independent PASS rereview is **accepted and published**;
* **M3-L13 is CLOSED**;
* **F4 is COMPLETE**;
* **T4 operational execution has NOT YET OCCURRED.**

Decision 047 provides the governing **T4 authorization**, but actual T4 execution must still use a
**separate exact ChatGPT-owner execution packet**. **T4 is not begun by this record.**

## 10. Ruling 048-K — negative authority

Decision 048 does **not** authorize: creation of the real operational catalog; creation of a real
M3.2 acquisition run; real SEC identity validation; off-device backup execution; T5; T6; network
enablement; CompanyFacts; live SEC access; DNS lookup; connectivity testing; HTTP or socket activity;
any request attempt; any consumption of ceiling **801**; resume; M3.2B derivation; Gate H; any new
executable change; or any additional test change.

**Network remains disabled.**

## 11. Publication

The owner authorizes **one normal fast-forward push** of the complete local lineage, in this order:

```text
e391ff3aa088b14b4be03457f5a13c0292253c86   published Decision 046 baseline
  ↓
bc3d170a155aaa6c196536109ef57dd841226675   Decision 047
  ↓
833a192839e888720389c4757250234b5cb219b7   accepted corrected RawStore candidate
  ↓
9406afbe88e83f7a0f0a52db290f9a220d01e6bc   accepted independent PASS rereview
  ↓
<this Decision 048 commit>                 owner acceptance and publication
```

Push only `main → origin/main`. **Normal fast-forward only**: no force, no `--force-with-lease`, no
rebase, no squash, no amend, no cherry-pick, no replacement branch, and **no history rewrite**. The
accepted candidate and the accepted review commit are published **exactly as they stand**.

**NO TAG.** No `m3.2-complete`, no RawStore tag, no T4 tag, and no other tag. Existing tags are
unchanged. **M3.2 is not complete.**

## 12. Authorized paths and acts for this recording

Exactly **four** paths, with **no fifth**:

1. `Docs/Decisions/decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md` (this record)
2. `Docs/Decisions/decision_registry.md`
3. `Milestones/STATUS.md`
4. `Docs/m3/limitations_register.md`

Expressly **not** edited: Decision 047 or any other accepted decision; the review artifact;
`Docs/m3/templates/evidence_index.md`; RawStore production code; any test; any configuration; the
operator runbook; the contract; the master plan; the receipt schema; any migration; the `Makefile`;
`pyproject.toml`; and every other `Docs/` and `Milestones/` path.

One governance commit containing exactly those four paths, subject
`Accept pre-T4 RawStore correction and independent rereview`, followed by one normal fast-forward
push. No amend, no squash, no rebase, no cherry-pick, no history rewrite.

## 13. Recorded acceptance status

```text
PRE_T4_RAWSTORE_STREAMING_SUBSTAGE:     ACCEPTED_AND_COMPLETE
PRE_T4_RAWSTORE_INDEPENDENT_REREVIEW:   ACCEPTED_AND_COMPLETE
M3_L13:                                 CLOSED_BY_DECISION_048
F4:                                     COMPLETE
T4_GOVERNANCE_AUTHORITY:                RECORDED_BY_DECISION_047
T4_OPERATIONAL_EXECUTION:               NOT_YET_BEGUN
T5:                                     NOT_AUTHORIZED
T6:                                     NOT_AUTHORIZED
NETWORK:                                DISABLED
M3_2A_CEILING_801:                      UNUSED
REAL_OPERATIONAL_CATALOG:               ABSENT
```

## 14. Formal outcome

**`M3_2_PRE_T4_RAWSTORE_ACCEPTED_AND_PUBLISHED`**

**Next authorized action:
`CHATGPT_OWNER_M3_2_T4_OPERATIONAL_PREFLIGHT_EXECUTION_PACKET`** — control returns to the ChatGPT
owner for the separate exact T4 operational-preflight execution packet. It authorizes **no T4
execution, no T5 or T6 work, no network enablement, no SEC contact, and no live operation** until
that packet is issued, and no session may read this record as any of those.
