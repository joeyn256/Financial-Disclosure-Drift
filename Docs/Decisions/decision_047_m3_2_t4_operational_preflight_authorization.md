# Decision 047 — M3.2 T4 Operational-Preflight Authorization and Pre-T4 RawStore Streaming Substage

**Date:** 2026-08-07
**Status:** ACCEPTED — OWNER APPROVED 2026-08-07
**Type:** Bounded governance record accepting the read-only M3.2 T4 operational-preflight architecture
discovery, fixing the twelve owner determinations that discovery referred, authorizing the **F4**
evidence-index vocabulary extension, recording limitation **M3-L13**, and authorizing one bounded
**pre-T4 RawStore streaming substage** across exactly two executable paths. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, S4/S5/S6 identity, hash preimage, migration byte, receipt byte, reason
code, or configuration byte.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–046 are byte-unchanged.
The accepted M3.2 contract, the historical T2 authorization packet, the accepted T2.5–T2.6
implementation candidate, and the durable T3 review artifact are all byte-unchanged.
**Related:**
[Decision 046](decision_046_m3_2_t3_acceptance_and_publication.md) (the accepted T3 state this record
builds on); [Decision 045](decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md)
§16 (which prohibits `sec/raw_store.py` and whose prohibition this record narrowly and expressly
releases for this substage only); Decisions 039 §6.4, 040 §§10, 19, 042 §§1, 3 (which carried the
RawStore limitation and F4 to T4); Decision 032 §6.4 and Decision 034 (the F4 gate); Decision 023 §7
**O1**; the accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md)
§§8, 11, 16, 17, 20, 23; [`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the twelve owner determinations of §3; the F4 vocabulary extension (§4); the M3-L13
recording (§5); the pre-T4 RawStore streaming substage and its exact two-path envelope (§6); the
validation, review, and commit boundary for that substage (§§7–9); and the negative authority that
survives all of it (§10).

---

## 1. What this record does, and what it does not

Five determinations, which must not be collapsed:

1. **Discovery acceptance.** The read-only M3.2 T4 operational-preflight architecture discovery
   (`M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY_COMPLETE`) is accepted. It found **zero
   BLOCKER** and four MAJOR conditions, each of which §3 now disposes of.
2. **T4 authorization in principle.** The T4 operational preflight is authorized in its architecture
   and its acceptance criteria. **T4 has NOT been executed by this record**, and its execution
   requires a separate exact owner execution packet.
3. **F4 discharge.** The evidence-index vocabulary extension is authorized exactly, and only, as §4
   states — discharging the obligation six accepted records fixed at "no later than T4".
4. **Pre-T4 RawStore substage.** One bounded implementation substage across **exactly two** paths is
   authorized (§6), correcting the accepted RawStore whole-object buffering limitation before any
   live window.
5. **What this record is not.** It is **not** T4 execution, **not** T4 acceptance, **not** T5, T6, or
   Gate H authority, **not** network authority, and **not** live-operation authority. Nothing here
   permits a live SEC operation, a real operational catalog, a real M3.2 run, a live receipt, or any
   use of the approved request ceiling **801**.

## 2. The owner determination, recorded without alteration

The owner's determination for this stage was issued as the Decision 047 authorization packet itself.
It carries **no separately named `OWNER_DECISION_047_…` instrument token**, and none is invented here
— the same convention accepted Decision 046 §2 records for its own determination. §3 reproduces the
owner's frozen rulings; where this record summarizes for navigation, the owner's own terms control.

## 3. The twelve frozen owner rulings

### 047-A — Operational catalog

```text
T4_DOES_NOT_CREATE_THE_OPERATIONAL_CATALOG
```

The real governed catalog `catalogs/m3_2a_operational.sqlite3` **must not exist at T4**. It is first
created inside the first lawfully authorized M3.2A live invocation under a later T5 instrument.
**No contract §11 amendment is authorized. No new catalog-creation CLI surface is authorized.**

T4 will later be permitted to exercise `prepare_operational_catalog()` **only against a disposable
temporary root** as an offline proof. That disposable proof is not part of the substage this record
authorizes, beyond ordinary tests.

### 047-B — RawStore

```text
AUTHORIZE_PRE_T4_RAWSTORE_STREAMING_SUBSTAGE
```

The current whole-object buffering risk is **NOT accepted** for the live window. The correction must
eliminate unnecessary object-size-proportional whole-object Python buffering in `RawStore.store()`
while preserving every accepted durability, hashing, compression, promotion, deduplication, and
verification semantic. §6 fixes its envelope and postconditions.

### 047-C — Limitation register

Add **M3-L13** documenting the discovered RawStore full-object memory-buffering limitation. **Do not
erase the historical limitation after correction**; after successful correction record its
disposition under the register's **existing** schema. No new schema is invented (§5).

### 047-D — F4

Authorize exactly the three-type evidence-index vocabulary extension of §4, and no fourth type.
**`operational_preflight_attestation` is NOT added.** T4 preflight evidence remains **private** and
is bound through the ledger and the owner decision by SHA-256 rather than publicly indexed.

### 047-E — Backup

Before T5, a **genuine off-device or otherwise independently recoverable copy** of the private
evidence root is **REQUIRED**. Same-device-only backup is **insufficient** for entry into T5.
Requirements: `.env` excluded; SEC identity excluded; a per-file SHA-256 manifest;
source/backup hash verification; a scratch-location restore test; and a restore that **never**
overwrites the operational evidence root. **No new backup script is authorized or required.**

### 047-F — Validation

Because this substage changes accepted executable code: targeted RawStore tests required;
touched-file lint and type validation required; full static gates required; **one** full test-suite
run after the implementation is stable; secrets, hygiene, and context required; and a **fresh
independent review required before owner acceptance**. The full suite is **not** rerun repeatedly
during implementation.

### 047-G — T5 shape

The future T5 authorization will authorize **exactly ONE** initial M3.2A live invocation. **No resume
authority is granted in advance.** Any interrupted invocation requires, in order: read-only recovery
inspection; a `SAFE` determination; an explicit owner resume-or-new-run ruling; exact predecessor
receipt binding; a **new** run identity; and an unchanged ceiling with consumed attempts carried
forward. **`UNDETERMINED` remains a stop.**

### 047-H — Resource floor

The unknown SEC bulk-object size is **not** estimated as fact anywhere. The RawStore correction must
remove reliance on whole-object RAM headroom. At T4 the operator records actual machine resource
measurements. For the local operational volume a conservative hard **T5 entry floor** applies:

```text
FREE DISK >= 50 GiB
```

measured immediately before live authorization and execution. **Below 50 GiB: STOP, do not enable
network, and return to the owner.** This is an operational safety floor, not a claim about the actual
SEC archive size.

### 047-I — Identity

The real SEC identity may be validated locally at T4 but is **never** displayed, logged, committed,
placed in an artifact, placed in a receipt, or typed inline into shell history. The authorized
procedure is `set -a` / `. ./.env` / `set +a`. **The value is never echoed.**

### 047-J — T4 review

A **fresh independent implementation review IS required** for this RawStore substage. A second
independent implementation review will **not** automatically be required for the later
governance/evidence-only T4 execution if no executable byte changes after this substage is accepted.

### 047-K — T3 MINOR-A

Decision 046 §5.1's accepted nonblocking T3 **MINOR-A** remains `ACCEPTED_NONBLOCKING_OBSERVATION —
DEFERRED`. **Do not modify it.** Nothing in this record reopens it, and the `_execute` marker
ordering is expressly outside this substage.

### 047-L — D023-O1 and the progress sink

Progress-sink obligation: **DISCHARGED** (implemented at T2.5–T2.6, confirmed by the accepted T3
review). **D023-O1: LATENT, NOT TRIGGERED, M3.3-scoped.** No implementation action for either.

## 4. F4 — the exact authorized evidence-index vocabulary extension

`Docs/m3/templates/evidence_index.md` is authorized for this one edit, adding **exactly three**
artifact types to the existing eleven:

| # | New artifact type | What it names |
|---|---|---|
| 1 | `frozen_object_identity_set` | The frozen M3.2A bootstrap raw-object identity set produced at the between-windows freeze |
| 2 | `derived_reference_set` | The dependent reference set derived from the frozen M3.2A objects, distinct from the M3.2B plan it feeds |
| 3 | `reconciliation_report` | The private deterministic plan-to-catalog reconciliation report, including its required-absence enumeration |

**Expected-coverage mapping**, added to the index §5 table:

- **M3.2A** — `frozen_object_identity_set`; `reconciliation_report`
- **M3.2B** — `derived_reference_set`

**Existing types are used unchanged** for `request_plan`, `request_budget`, `execution_receipt`,
`recovery_state_report`, and `gate_h_checklist`. **No fourth type is added**, and
`operational_preflight_attestation` is expressly **not** created.

This discharges the F4 gate that Decision 032 §6.4 opened and that Decisions 034, 035 §10, 039 §6.6,
040 §10, 042 §3, 045 §4.5, and 046 §6 each carried forward to "no later than T4".

## 5. M3-L13 — the recorded RawStore limitation

`Docs/m3/limitations_register.md` is authorized for one addition: **M3-L13**, recording the
RawStore full-object memory-buffering limitation under the register's existing field schema, with the
register summary counts updated to match. The limitation is **recorded as discovered and then
dispositioned**; it is never erased. Its closure evidence is the accepted substage of §6 plus its
independent review and owner acceptance.

## 6. The pre-T4 RawStore streaming substage

### 6.1 Exact executable envelope — two paths, no third

| # | Path |
|---|---|
| 1 | `src/disclosure_drift/sec/raw_store.py` |
| 2 | `tests/unit/test_raw_store.py` |

**No third executable or test path is authorized.** Decision 045 §16's prohibition on
`sec/raw_store.py` is released **for this substage only and for nothing else**; every other path it
prohibits stays prohibited. A discovered need for any third path — including
`sec/snapshots.py`, `sec/observation_catalog.py`, `m3/acquisition.py`, `cli.py`, `m3/receipt.py`,
`m3/recovery.py`, `storage/catalog.py`, `sec/request_ceiling.py`, any migration, any configuration,
`Makefile`, or `pyproject.toml` — is an **immediate stop** before the path is touched.

### 6.2 Required postconditions

**Uncompressed storage (`compress=False`).** Chunks consumed incrementally; content SHA-256 and
content size computed incrementally; chunks written incrementally to the staging file; **no
`bytearray`, `list`, or `bytes` object accumulates the entire input body**; the promoted file's
stored SHA-256 and stored size computed incrementally; **no whole-file read** on the stored-object
verification path.

**Compressed storage (`compress=True`).** The complete uncompressed object is **not** accumulated in
Python memory; deterministic gzip semantics, compression level, `mtime`, and canonical byte output
are preserved exactly; `content_sha256` remains the digest of the decoded source bytes;
`stored_sha256` remains the digest of the actual stored compressed bytes; stored size remains exact;
the deterministic round-trip verification remains sound; and the memory problem is **not** traded for
an unbounded temporary in-memory buffer.

**Promotion and durability.** `.part` staging, content-addressed identity, no-overwrite,
atomic create-once promotion, the hard-link primitive, file `fsync`, directory `fsync`, cleanup
behaviour, preservation of recoverable evidence after a failure, and the prohibition on silently
deleting evidence recovery needs are all preserved.

**Deduplication.** The existing-object path must not read an arbitrarily large object wholly into
Python memory; its verification remains exact.

**`verify()`.** It is inside the authorized path and **may** become incremental. Its externally
observable semantics are preserved.

**Failure semantics.** No previously fail-closed condition becomes acceptance. Hash mismatch, size
mismatch, decompression or round-trip failure, collision, promotion failure, `fsync` failure, and
filesystem errors all continue to fail closed.

**API compatibility.** The public `RawStore` API is preserved. **If an API change appears necessary,
STOP.**

## 7. Validation required for the substage

Targeted `tests/unit/test_raw_store.py` while iterating; `ruff check .`; `ruff format --check .`;
`mypy src`; `make secrets`; `make hygiene`; `make context`; and **one** complete test-suite run once
the implementation is stable. The changed-path set must be proved contained within the five
governance paths of §9 and the two executable paths of §6.1, with **no other path differing**.

The substage's tests must be **non-vacuous**. In particular the memory regression must be a
**behavioural or instrumentation-based positive control that would fail against the pre-correction
implementation** — never a source-text scan — and the ordinary suite must not depend on a brittle
OS-specific peak-RSS threshold. The real peak-RSS measurement belongs to the T4 operational preflight.

## 8. Review and commit boundary

The implementation session is **not** the reviewer. After the substage is committed **locally**,
control returns to the owner, who issues a separate packet to a **fresh Claude Opus 5, effort Max**
session that authored neither this Decision, nor the RawStore correction, nor its tests, and that
begins with no carried-over context. **The review artifact is never pre-written.**

**No push. No tag. No amend, rebase, squash, or history rewrite.** The governance recording and the
implementation are separate commits, and every new commit stays local pending independent review and
owner acceptance.

## 9. Authorized governance paths for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 047 row and quick-lookup entry;
- `Milestones/STATUS.md` — narrow current-state, blocker, authority-state, and next-action updates;
- `Docs/m3/templates/evidence_index.md` — the F4 extension of §4;
- `Docs/m3/limitations_register.md` — the M3-L13 entry of §5.

**No sixth governance or documentation path.** The accepted contract, the T2 packet, every earlier
Decision, every review artifact, every other template, the runbook, the receipt specification, the
navigation maps, source, tests, configuration, and migrations are **not modified by this recording**.

## 10. Negative authority

This record does **not** authorize: **T4 operational-preflight execution**; creation of the real
operational catalog; creation of any M3.2 operational state, data root, live receipt, M3.2 run, or
raw SEC object; **T5**; **T6**; Gate H; network enablement (`network.enabled` and
`network.m3_acquire_enabled` both remain `false`); CompanyFacts enablement; live SEC access; a DNS
lookup or connectivity test; any request; any consumption of the approved ceiling **801**; resume
authority; M3.2B work; migration changes; receipt-schema changes; reason-code changes;
configuration-schema changes; any change to M3 acquisition or recovery semantics outside RawStore;
a push; or a tag.

**T4 is not complete. T4 is not accepted. T5 is not authorized. M3.2A is not ready for live
execution.**

## 11. Stop conditions for the substage

Stop **before the act**, and return to the owner, if: a third executable or test path is required; a
migration, receipt-schema, reason-code, or configuration-schema change is required; any change to M3
acquisition or recovery semantics outside RawStore is required; any network activity would be
required; either network switch would need to become `true`; the correction would weaken atomic
promotion, create-once semantics, deterministic compression, content-addressed identity,
`fsync`/durability behaviour, deduplication, verification, quarantine, reconciliation, or failure
preservation; a full-object in-memory buffer remains necessary after reasonable analysis; a
non-vacuous streaming regression test cannot be constructed; the public `RawStore` API would have to
change; anything would create real M3.2 operational state or consume ceiling **801**; a BLOCKER or a
new MAJOR arises whose correction is outside this record; or any ambiguity exists about whether an
action is operational and live versus disposable and offline.

## 12. Formal outcome

```text
M3_2_T4_OPERATIONAL_PREFLIGHT_AUTHORIZED_AND_PRE_T4_RAWSTORE_SUBSTAGE_AUTHORIZED
```

The T4 operational-preflight architecture is authorized and its twelve owner determinations are
fixed; **F4 is discharged**; **M3-L13 is recorded**; and the bounded two-path pre-T4 RawStore
streaming substage is authorized, to be implemented locally, independently reviewed by a fresh
non-author session, and separately accepted by the owner.

**Next authorized action:**
`RETURN_FOR_CHATGPT_OWNER_M3_2_PRE_T4_RAWSTORE_INDEPENDENT_REVIEW_PACKET` — control returns to the
ChatGPT owner once the substage is implemented and committed locally. **T4 execution, T5, T6, network
enablement, live SEC acquisition, real operational-catalog creation, and ceiling-801 use all remain
unauthorized.**

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-07.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
