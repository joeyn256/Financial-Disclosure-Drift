# Decision 023 — M2.3 S6 Acceptance, Forced-Consequence Path Ratification, and Residual Limitations

**Date:** 2026-07-31
**Status:** ACCEPTED — OWNER APPROVED 2026-07-31
**Type:** Acceptance and governance-completion decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged. No hypothesis, cohort window, maturity gate, outcome
definition, threshold, or seed is altered. It changes no implementation byte, no migration byte, no
test byte, no hash preimage, no digest, and no crosswalk row.
**Supersedes:** nothing. **Amends:** nothing.
[Decision 021](decision_021_m23_s6_manifest_construction.md) and
[Decision 022](decision_022_m23_s6_reserve_rank_applicability.md) both remain `ACCEPTED`, unchanged,
and controlling for everything they govern.
**Related:** [Decision 013](decision_013_pilot_selection_mechanics.md) §§6–8,
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §§1, 5, 8,
[Decision 018](decision_018_m23_s5_accession_selection_policy.md) §§22, 25,
[Decision 020](decision_020_m23_s5_4_reserve_architecture.md) §§7.1, 8.2, 19.
**Governs:** Milestone 2.3, Stage S6 acceptance and the S6 checkpoint.

---

## 1. Why this record exists

Stage S6 was implemented under separately issued bounded authorizations against the architecture
[Decision 021](decision_021_m23_s6_manifest_construction.md) v0.5 froze, corrected once under the
owner clarification [Decision 022](decision_022_m23_s6_reserve_rank_applicability.md), independently
rereviewed, and then independently reviewed for acceptance. Three things still needed a record:

1. **Acceptance itself.** Decision 021 §22 and Decision 022 §9 both require that S6 remain
   unaccepted, uncommitted, and untagged until a final acceptance review passes. It has passed. That
   outcome belongs in `Docs/Decisions/`, not only in a status file — a completion narrative is not
   repository authority (CLAUDE.md).
2. **A path-authorization gap.** The delivered change set touched **three test modules outside the
   S6 contract's seven authorized paths**. The final acceptance review found this, established that
   every one of the three was a forced consequence of authorized migration `0013`, and referred it
   to the owner rather than resolving it. §4 records the owner's ratification.
3. **Four residual observations** raised by the independent reviews, which the owner accepts as
   nonblocking limitations rather than defects (§7).

## 2. The independent acceptance result

The final independent S6 acceptance review — conducted by a session that did not design, govern,
implement, correct, or rereview S6 — returned:

```
ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING
```

with **no methodological findings, no implementation defects, no test defects, no outstanding owner
clarifications, and no acceptance blockers**. It reproduced the decisive evidence independently
rather than inheriting it: migration `0013`'s statement region byte-for-byte against the SQL
extracted from Decision 021 §15.1, all nine §15.3 digests, the frozen crosswalk counts, and nine
acceptance-critical end-to-end guarantees over real catalogs built through the accepted S5 entry
point. It recorded exactly one governance item requiring owner action — the path gap of §4.

That review followed the fresh independent S6 implementation rereview of the corrected tree, which
returned `ACCEPT_M23_S6_IMPLEMENTATION_FOR_ACCEPTANCE_REVIEW`. Neither review was performed by a
session that wrote the work it reviewed, as Decision 022 §9 requires.

## 3. Frozen ruling — Stage S6 is accepted

**The project owner accepts Milestone 2.3 Stage S6 as complete on 2026-07-31.** The accepted stage
delivers, and nothing beyond:

| # | Accepted S6 capability | Governing section |
|---|---|---|
| 1 | Deterministic manifest construction from persisted terminal state | 021 §§4, 12 |
| 2 | The eight component digests at their frozen preimages | 021 §§7, 8 |
| 3 | `selection_result_sha256` — the terminal selection-result digest | 021 §6 |
| 4 | `root_manifest_sha256` | 021 §9 |
| 5 | `manifest_id` and its six-field identity immutability | 021 §§9.1, 9.2 |
| 6 | Canonical JSON under `DataTree.releases / "pilot"`, content-derived filename | 021 §13.5 |
| 7 | Complete document rendering — all thirteen mandatory blocks | 021 §13.2 |
| 8 | Field-level crosswalk binding — 81 atomic items, item by item | 021 §13.2.1, §13.3 |
| 9 | Historical S5 reconstruction through the accepted entry point | 021 §12 |
| 10 | Append-once sealing in its own prior transaction | 021 §11.3 |
| 11 | Persistence of exactly one `proposed` manifest row plus its document | 021 §11.1 |
| 12 | Public verification that re-derives every digest, the root, the ID, and the document | 021 §12 |
| 13 | Idempotent replay — read, reconstruct, compare, return; never write | 021 §§11.3, 12 |
| 14 | File and database atomicity in one transaction | 021 §11.3 |
| 15 | Migration `0013` lifecycle enforcement — eight triggers, DDL-only | 021 §15 |
| 16 | S4 entity-only-draft isolation, enforced at three independent layers | 021 §14 |
| 17 | S5 preservation — no second selection, no reserve substitution, no re-derivation | 021 §14 |
| 18 | Exclusion of Stage S7 and every later stage | 021 §17 |

**Formal outcome:**

```
M23_STAGE_S6_ACCEPTED_AND_COMPLETE
```

## 4. Frozen ruling — ratification of three forced-consequence test paths

`Milestones/contracts/m23_s6.md` authorized **seven** implementation paths. **That is the historical
fact and it is not rewritten by this record.** The delivered change set additionally modified three
test modules, and no record authorized them at the time:

| Path | What changed | Why migration `0013` forced it |
|---|---|---|
| `tests/unit/test_storage_catalog.py` | one line added to `EXPECTED_MIGRATIONS` | The module asserts the canonical migration chain by exact version **and name**. Migration `0013` extends that chain, so the assertion fails until `(13, "m23_manifest_lifecycle_guards")` is present. There is no discretion in this edit. |
| `tests/unit/test_m23_entity_selection_store.py` | corruption fixture rebuilt | The accepted S4 test constructed its precondition with a plain `UPDATE` on `selection_input_sha256`. Trigger 8 `pilot_selection_run_identity_guard` now refuses exactly that statement, so the test could no longer build the historically corrupted row it must prove is refused. |
| `tests/unit/test_m23_accession_selection_store.py` | corruption fixtures rebuilt and **narrowed** | Same cause at four call sites. Additionally, the pre-existing `_corrupt_sealed_row` helper dropped *every* trigger matching `pilot_%_insert_guard` / `_update_guard` / `_delete_guard` — a blanket pattern that would have silently swallowed migration `0013`'s new `pilot_selection_run_delete_guard`. |

**The owner ratifies all three, retroactively, for inclusion in the accepted S6 checkpoint.**

### 4.1 The basis for ratification

Each of the following was verified by the final independent acceptance review against the actual
diffs, not asserted:

- **No production path changed.** Every accepted S4 and S5 production module is byte-unchanged, as
  are `release/hashing.py`, `release/manifest.py`, `paths.py`, `cli.py`, `cohorts.py`,
  `pilot_policy.py`, and `reasons.py`.
- **No S4 or S5 methodology changed.** No selector, objective, quota, role, cap, floor, evidence,
  family, tie-break, reserve, or reason-code rule was touched.
- **No assertion was removed, weakened, relaxed, skipped, or xfailed.** Every rewritten test still
  raises on the same `GateFailureError` with the same match string.
- **The corruption fixtures became narrower and more fail-closed than the code they replaced.** Only
  a catalog this suite itself created may be corrupted, through an explicit allowlist that holds
  under `--basetemp`, `PYTEST_DEBUG_TEMPROOT`, a relocated `TMPDIR`, and xdist alike; only the single
  exact trigger blocking the one statement is removed, rather than a wildcard family; that trigger is
  restored from its own captured `sqlite_master` definition in a `finally` block before the caller
  regains control, and its reinstallation is asserted; and foreign keys stay enabled except where the
  specific historical corruption being modelled is precisely a broken reference.
- **The edits are forced consequences of authorized migration `0013`**, of the same class Decision
  021 §20 already anticipated for `tests/unit/test_m23_pilot_schema.py`. §20 named that one module
  because it was the one foreseen; the mechanism it describes applies identically to these three.

### 4.2 What this ratification does and does not do

**It closes the contract's original omission by owner act, which is the only way it could be
closed.** Decision 018 §25 and Decision 020 §8.2 establish the standing rule that a gap of this kind
is an owner-level conflict, never a widening a session performs on its own — and the correct handling
was to stop and refer it, which the acceptance review did.

It is **not** a general licence. It ratifies exactly three named paths, for exactly one migration,
on exactly the basis in §4.1. It authorizes no future path widening, and a future session that finds
itself needing a path outside its contract stops and reports under Decision 021 §21 exactly as
before.

**The delivered S6 change set is therefore ten implementation and test paths**: the seven the
contract authorized, plus these three ratified here.

## 5. What Decisions 021 and 022 retain

Both remain `ACCEPTED`, unchanged, and controlling.

- **Decision 021 v0.5 remains the controlling S6 architecture record** — scope, hashing
  infrastructure, every preimage, the root, manifest identity and its immutability, circularity
  exclusions and commitment closure, lifecycle and eligibility, reconstruction and replay, the
  document contract and its crosswalk, the S4/S5 boundary, the migration `0013` ruling and its frozen
  SQL, the no-new-surfaces ruling, the S7–S10 boundary, accepted limitations, test obligations, stop
  conditions, and the checkpoint boundary.
- **Decision 022 remains the controlling record for crosswalk item 46's reserve-rank
  applicability**, and for nothing else.

**This record adds acceptance, ratification, limitations, and checkpoint authorization. It adds no
architecture and reopens no ruling.**

## 6. Invariance confirmations

Each was independently reproduced at the final acceptance review, not accepted on report.

1. **All 81 crosswalk rows are unchanged**, numbered 1–81 with no gap or duplicate.
2. **Classification totals are unchanged:** D 42, T 30, X 8, S9 1, S10 0, **unclassified 0**. Exactly
   one S9 deferral, and it is item 80. No fifth category exists.
3. **Every accepted hash preimage is unchanged** — §6.1, §§7.1–7.4, §§8.1–8.4, §9, §9.1.
4. **All nine migration SQL digests are unchanged**: the eight per-block digests and the region
   digest `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595`, over a statement region
   of **10939 bytes across 186 lines**, byte-for-byte identical to Decision 021 §15.1. The withdrawn
   v0.4, v0.3, and v0.1 regions appear nowhere.
5. **All eight triggers are unchanged**, and migration `0013` remains DDL-only — no table, column, or
   index, and no data statement.
6. **Migrations `0001`–`0012` are byte-unchanged.**
7. **S4 is unchanged.** The entity-only draft stays `running`, non-publishable, and excluded from
   every manifest input; S6 reads it not at all.
8. **S5 is unchanged.** Entity selection, accession selection, roles, evidence, contributions, quota
   rules, reserve rules, dispositions, persistence, reconstruction, replay, and terminal identity all
   stand exactly as accepted.
9. **No Stage-S7, S8, S9, or S10 authority and no Milestone 3 authority is granted.**

## 7. Accepted nonblocking limitations

Recorded for monitoring. None is a defect; none requires an implementation change; none blocks
acceptance. They supplement, and do not replace, Decision 021 §19 and Decision 020 §19.1.

**O1 — an empty sole-carrier crosswalk family fails closed.** Where a §10 item is discharged by more
than one serialized family, emptying one of them is accepted. Where a family is an item's **sole**
carrier, an empty family makes the item unplaceable and raises `GateFailureError`, exactly as
Decision 021 §21 designs. **No accepted current S5 plan reaches that condition.** If a lawful future
run ever does, it is a stop-and-report condition referred for an owner ruling — never resolved by a
session reclassifying an item, adding a category, or changing a count (Decision 021 §13.3). Decision
022 is **not** broadened to pre-resolve it.

**O2 — the release root is assumed owner-controlled.** `Path.write_text` follows a symlink
pre-positioned at the content-derived output path. **Symlink-resistant publication was never an
accepted S6 requirement**, and none is created here. The properties that were required do hold and
were proven: verification fails closed when the bytes behind such a path are wrong, and no database
row survives a failed write. Recorded so the owner-controlled-root assumption is explicit rather than
implicit.

**O3 — a pre-existing artifact at the content-derived path is outside the transaction's ownership.**
S6 atomicity governs artifacts **the current operation created**: a fault removes a newly created
file and rolls back the row, leaving neither. A file that already existed at that exact
content-derived name is not deleted, because deleting another writer's artifact is not this
operation's act. Partial or wrong bytes subsequently fail verification, and an authorized retry
repairs the artifact through the normal construction path.

**O4 — item-46 enforcement is consistent defence in depth.** The Decision 022 applicability check and
the per-record document-completeness check agree on every document; neither is vacuous and neither
weakens the other. **Reserve rank remains substantively enforced for every real package**: a missing
rank, a rank that is not the accepted rank, an invented rank on a disposition-only target, a target
carrying both a package and a disposition, a target carrying neither, a duplicate package, a
duplicate disposition, and a substituted reason code each fail closed.

## 8. Checkpoint authorization

The project owner authorizes, for this acceptance recording and no other purpose:

1. **one permanent commit** of the accepted S6 change set together with this record and the
   acceptance-recording governance updates;
2. **a push to `origin/main`**;
3. **a new annotated tag `m2.3-s6-complete`**, which **supplements** the immutable
   `m2.3-s5-complete` and `m2.3-s5.4-complete` and never moves, replaces, or re-points either
   (Decision 021 §22);
4. **a push of that tag.**

No other commit, tag, branch, or history operation is authorized. CLAUDE.md rule 13 applies
independently to everything beyond this list.

## 9. Forward boundary

**Nothing below is authorized by this record.**

- **No Stage-S7 implementation.** Gate F live-metadata safety and the URL allowlist remain unwritten
  and unauthorized; no S7 contract exists.
- **No live SEC operation**, no metadata acquisition, no real candidate snapshot, no real-data
  manifest instance, no CLI surface, no publication, and no manifest approval.
- **No Milestone 3 implementation** and no Milestone 3 planning.
- **The Milestone 2 / Milestone 3 boundary reorganization** — which will redefine accepted S6 as the
  end of Milestone 2 implementation and move the former S7–S10 obligations into Milestone 3,
  preserving every gate and requirement — is **deferred to a separate governance-only session** that
  authorizes no implementation.
- **The final independent integrated Milestone 2 audit** is deferred until after that reorganization.
- **Milestone 2 is not closed by this decision.** Formal closeout follows the integrated audit, and
  only if it passes.

## 10. Reason

S6 is where a chain of content-derived identities finally closes into a manifest the project owner
can approve by hash, and the discipline that got it there is the same discipline that requires this
record: an acceptance that lives only in a chat transcript binds nothing, and a change set that
quietly exceeded its authorized paths would leave the next session unable to tell what was authorized
from what merely happened. Both are cheap to fix now and expensive to reconstruct later. The three
ratified test paths were not a widening anyone chose — they were the unavoidable tail of a migration
the owner had already authorized, and the correct response to finding them was to refer them, which
is what happened. This record accepts the stage, closes that gap deliberately and narrowly, writes
down what the project has agreed to live with, and authorizes exactly one checkpoint.

No deviation from Decisions 013–022 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.
