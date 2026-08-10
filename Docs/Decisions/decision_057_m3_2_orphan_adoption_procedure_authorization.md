# Decision 057 — M3.2 Historical Orphan-Adoption Procedure Architecture

**Date:** 2026-08-09
**Status:** ACCEPTED — OWNER APPROVED 2026-08-09
**Authority classification:** `M3_2_ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE_ACCEPTED`
**Type:** Governance-only owner adjudication of the completed read-only orphan-adoption architecture
discovery authorized by [Decision 056](decision_056_m3_2_carry_in_implementation_acceptance_and_m3_l14_closure.md)
§10. It records the discovery's confirmed **MAJOR** correction and fixes the exact architecture,
row-construction, content, preflight, postcondition, fault-semantics, synthetic-proof, evidence, and
boundary requirements that a later separately authorized execution packet must impose. It changes no
executable or test byte, opens no operational state, and performs no adoption.

**Non-self-executing.** This record **fixes architecture and procedure requirements. It does not
itself grant the operational invocation.** No session may perform, simulate against private state,
or partially begin the adoption on the strength of this record.

**Amends:** nothing in place. Decisions 001–056 remain byte-unchanged.
**Narrowly supersedes:** only the current-state statement in
[Decision 056](decision_056_m3_2_carry_in_implementation_acceptance_and_m3_l14_closure.md) §10,
the decision registry, and `Milestones/STATUS.md` that the next action is the read-only
orphan-adoption architecture discovery. That discovery **has since been issued and completed**; its
statements were accurate when written and are preserved as historical.
**Preserves unchanged:** ceiling **801**; historical seed **1**; the frozen 75-logical-request plan
and SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; consumption
**1 of 801**; the old run's permanent no-resume status; recovery `UNDETERMINED`; the absence of a
terminating receipt; zero historical `ops_retrieval_attempts` rows; **M3-L15**; every network, SEC,
transport, recovery, provenance, and live-operation stop condition; and the rule that **M3-L16 blocks
every clean or live run** until the orphan is adopted and the limitation is separately closed.
**Related:** [Decision 056](decision_056_m3_2_carry_in_implementation_acceptance_and_m3_l14_closure.md),
[Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) §9,
[Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) (the
ephemeral-procedure precedent), [Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md),
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md), and
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).

---

## 1. What this record does, and what it does not

**It does:**

- adjudicate the completed read-only architecture discovery authorized by Decision 056 §10;
- record the owner's confirmation that the discovery's central contract assertion was **MAJOR-wrong**,
  and replace it with the corrected contract (§4);
- fix the exact procedure shape, row construction, content, preflight, terminal delta, fault
  semantics, synthetic proof, evidence contract, and execution boundary a later packet must impose
  (§§5–12).

**It does not:**

- authorize, perform, simulate, or partially begin the adoption;
- open, read, or mutate the real operational catalog, data root, raw object, lineage intent, receipt
  inventory, writer lease, private evidence, or any identity value;
- create any production, test, migration, configuration, reason-code, runbook, contract, or template
  byte;
- mint or consume a carry-in authority;
- close **M3-L16**, claim live readiness, or authorize **T6**, **M3.2B**, or **Gate H**.

The discovery report and its remediation addendum are **advisory evidence, not repository
authority**. Where they conflict with this record, this record controls.

## 2. The owner determination, recorded without alteration

```text
M3.2 — DECISION 057
CORRECTED ORPHAN-ADOPTION PROCEDURE ARCHITECTURE

The completed read-only orphan-adoption architecture discovery is adjudicated.

Its central contract assertion — that a successful adoption adds exactly one new
row and leaves every other table unchanged — is a confirmed MAJOR error. Replace
it with the corrected deterministic two-table, two-row, three-transaction
projection-rebuild contract recorded below.

Retain Architecture C, corrected: one ephemeral, SHA-256-recorded, one-time
procedure outside the repository, using the accepted _observation_from_intent as
its sole verifier and one guarded INSERT inside CatalogWriter.batch, followed by
one mandatory rebuild_audit_projection call in the same authorized process
invocation.

Override the remediation addendum's unbounded "retry to success" recommendation.
One later explicitly authorized process invocation attempts both limbs, once.
No retry loop, no auto-retry, no auto-resume, no automatic relaunch. Any
exception, interruption, uncertainty, or failed postcondition stops and refers
to the owner.

This record is non-self-executing. It authorizes no invocation. The next action
is its fresh independent non-author review. After a passing review and a
separate owner publication ruling, a separate explicit execution packet is still
required.

M3-L16 remains ACTIVE and blocking. No carry-in authority may be minted or
consumed. Consumption remains 1 of 801. The old run remains never resumable.
Recovery remains UNDETERMINED. Live readiness is not claimed.
```

## 3. Authority verification

| Item | Value |
|---|---|
| Baseline `HEAD` | `ea0647459ef38069c75f7b8da2873abf0cbccdb1` |
| `origin/main` | `ea0647459ef38069c75f7b8da2873abf0cbccdb1` — identical |
| Working tree at entry | clean |
| Packaged migration inventory | latest `0013_m23_manifest_lifecycle_guards.sql`, count **13**, contiguous `0001`–`0013` |
| Tracked network switches | `network.enabled: false`; `network.m3_acquire_enabled: false` (`configs/project.yaml`) |
| Tracked CompanyFacts switch | `companyfacts.enabled: false` (`configs/project.yaml:54`) |
| Predecessor authority | Decision 056 §10 authorized the read-only discovery; it completed |
| Authorizing instrument for this record | the owner's response to the prior recommendation: *"Okay fix the major and run a new review."* |

That instruction is authority to **prepare this governance candidate and its fresh review**. It is
**not** authority for operational execution.

**Candidate provenance — four bounded remediations: two before the first publication, two after.**
This record has now been corrected **four times**, each time under a bounded owner instrument and
each time changing **no** executable, test, migration, configuration, contract, runbook, or template
byte and touching **no** operational state.

1. **First remediation (2026-08-09).** Fixed one owner-identified **MAJOR** omission: the record
   fixed the verifier and the guarded `INSERT` but did not mandate the full persisted row
   construction, so a later direct `INSERT` could have satisfied the prose while persisting a
   different tuple or failing to prove exactly one row was written. It added §4.4, §5.1, content
   rulings 8–10, the terminal row-shape postcondition, evidence item 14, the additive fifteenth
   synthetic case, and the §4.2 precision that `record` and `_row` are cited **only** as row-shape
   precedent.
2. **Second remediation (2026-08-09).** The fresh independent review of the first-remediated
   candidate found **two further MAJOR defects, both in the proof layer rather than the
   architecture**: (a) §8 asserted that *"no second generated instant exists anywhere in the run"*,
   which is **false** — a correct rebuild necessarily generates two further library-owned instants
   (§4.2); and (b) §10 demanded that deleting the `cursor.rowcount == 1` guard be caught by a
   behaviourally non-vacuous mutation, which is **impossible** under the accepted plain-`INSERT`
   and schema shape. Four directly related **MINOR** ambiguities were corrected alongside them
   (§5 and §5.1 step 6 — the batch must exit and transaction 1 must commit before the rebuild; §5's
   pinned second-limb call shape; §6 rulings 4–5 — the grounding for the zero-row rulings; §7 gate 10
   and §12 clause 9 — what "exactly one invocation" counts).
3. **Third remediation (2026-08-09) — the first after publication.** The §16 final
   fresh independent non-author review was performed against the published record and returned
   **`DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_FAIL`** — **0 BLOCKER, 1 MAJOR, 3 MINOR,
   2 OPTIMIZATION**. It confirmed the central architecture correct in every material
   code-to-governance particular, with **no** claim contradicted against the frozen code, schema, or
   configuration, and located every finding in the **proof, evidence, and traceability layers**:
   - **MAJOR** — the record required the ephemeral procedure's SHA-256 to be recorded and the §10
     suite to pass, but **never bound the two**: nothing required the hashed bytes to be the bytes
     the suite validated, or to be unchanged and re-verified at the real invocation. Since §10
     case 15 requires **mutated** variants by design, multiple byte-variants necessarily exist, so
     the proof layer was not binding on the artifact that performs the irreversible write. Closed by
     §5, §7 gates 10–12, §10, §11 item 2, and the §15 `PROCEDURE_ARTIFACT_IMMUTABILITY` line.
   - **MINOR** — §14 asserted the record was an uncommitted candidate and that no publication had
     occurred, at the very commit that published it. Closed below and in §14.
   - **MINOR** — §7 mandated no pre-adoption snapshot of the operational catalog, against this
     milestone's accepted backup discipline (contract §20; Decisions 047, 049, 050). Closed by
     §7 gate 13 and §11 item 16.
   - **MINOR** — §7 gate 6, the record's own strongest preflight ruling, had **no** synthetic
     refusal case although gates for duplicate identifier, duplicate path, and two orphans each did.
     Closed by the additive §10 case 16.
   - **OPTIMIZATION** ×2 — the §9 state-5 description and the §4.4/§5 grounds for excluding
     `_recover_orphan`. Both applied.
4. **Fourth remediation (2026-08-09) — this one, and the second after publication.** The
   post-remediation fresh independent rereview was performed against the published corrected record
   `103b3d39…` and returned
   **`DECISION_057_POST_REMEDIATION_FRESH_INDEPENDENT_REVIEW_FAIL`** — **0 BLOCKER, 1 MAJOR,
   2 MINOR, 2 OPTIMIZATION**. It confirmed the complete underlying architecture **correct** against
   the frozen code — every one of the record's cited line numbers resolved to the exact construct
   claimed, with **no** claim contradicted — and confirmed **MAJ-1**, **MIN-3**, **OPT-1**, and
   **OPT-2** correctly resolved. Its findings again fell entirely in the **traceability,
   publication-currency, and evidence layers**:
   - **MAJOR (MAJ-A)** — the corrected record carried the new control set, but the **three companion
     governance files still described the superseded one** — **every figure in this sentence is the
     superseded one, quoted only to identify the defect, and none of it is current**: an eleven-item
     preflight (omitting gates 12 and 13), fifteen synthetic cases (omitting case 16), a
     fourteen-item evidence contract (omitting item 2's two-reading form and items 15 and 16), and a
     single-route `_recover_orphan` exclusion — with two files also self-contradicting between their
     body and their own appended tail. A later packet drafting from the ledger would have rebuilt
     exactly the pre-remediation control set. **All are now corrected to thirteen gates, sixteen
     cases, sixteen evidence items, and the two-route exclusion**, synchronized across all four
     authorized files.
   - **MINOR (MIN-A)** — §14 and §15 asserted in present tense that *this remediation is itself
     uncommitted*, inside the very commit that published it: the same defect class as the third
     remediation's MINOR, one generation later, and the second unrecorded sequence anomaly. Closed
     in §14 and §15.
   - **MINOR (MIN-B)** — the new snapshot gate recorded the snapshot's own digest but never bound it
     to the live pre-write catalog state: no source digest, no equality proof, no snapshot method
     fixed against a WAL-mode source, and no ordering against the lock recheck. Closed by §7.1,
     §7.2, the rewritten §7 gates 9 and 13, and §11 item 16.
   - **OPTIMIZATION ×2** — the residual procedure-artifact path/symlink ambiguity (**OPT-A**, closed
     by §5.2 and §7 gate 12) and the under-inclusive two-route state-5 exception list (**OPT-B**,
     closed by §9). The owner ordered both implemented.

   The rereview's report also disclosed that its `Claude-Session` identifier matched the third
   remediation's. The owner accepted the report as valid defect-discovery evidence while ruling that
   **no eventual `PASS` may rest on that identifier** — see §16.

**Both publications occurred before any qualifying passing review, and both are recorded rather than
asserted away.** Publication 1 was `9475eb3d614aa70b3f2a04b061d63bd7ea51c030` (tree
`e0b9b12095c181ba974336399f04fc1e44eb4a11`, parent `ea0647459ef38069c75f7b8da2873abf0cbccdb1`) under
the exact §14-reserved subject `Authorize M3.2 orphan-adoption procedure architecture`. Publication 2
was `103b3d3910e11fee43f66d8451f101019487588e` (tree `04bd61ca09be271752d432c82f0c2f6a02eb277c`,
parent `9475eb3d…`) under the subject `Correct Decision 057 after failed independent review`. Each
touched exactly the §14 four-path envelope and **no fifth**, with **no tag**. **The owner has ratified
`103b3d39…` as a matter of publication FACT only — not as execution acceptance** (§14). Whether
publication 1 is ratified remains an owner ruling; this record neither ratifies nor voids it. §14
carries the full disposition, including this fourth remediation's own authorized publication.

The **accepted central orphan-adoption architecture is unchanged by all four remediations.** None
granted execution authority. The prohibition on an **automatic correction loop** is **intact and was
honoured at every step**: each review referred every defect to the owner and remediated nothing, and
each correction proceeded **only** under the owner's separate responding instrument — this one under
the bounded second post-remediation correction packet, which expressly accepted **MAJ-A**, **MIN-A**,
**MIN-B**, **OPT-A**, and **OPT-B** for remediation and expressly barred redesign of the already
resolved **MAJ-1**, **MIN-3**, **OPT-1**, and **OPT-2**. An owner-instructed remediation is not an
automatic loop. **No automatic correction loop is permitted at any point**; any further defect
returns to the owner. **Every session that has authored or remediated this record is disqualified
from reviewing it, and §16 now states that requirement in objectively testable form.** §2 is
preserved **verbatim** as the prior owner determination — its "next action" line is historical, and
§16 carries the current pointer.

Every source and schema fact recorded below was verified by direct read-only inspection of the
**committed repository** at that baseline — the packaged migrations, the accepted production source,
and the tracked configuration. **No operational state was opened**, not even read-only. The
**catalog's applied** migration head, orphan count, blocked-row count, and projection validity are
therefore **not** verified here; they are §7 preflight obligations for the later execution packet.

## 4. Ruling 057-A — the confirmed MAJOR correction

### 4.1 What was asserted, and what is true

The discovery asserted a **single-write** contract: one new `census_source_observations` row, one
table touched, every other table unchanged. That is **wrong**, and it is wrong in a way that would
have made the execution packet's postcondition set reject a *correct* run and accept an *incomplete*
one. The owner classifies it **MAJOR** and replaces it.

The corrected contract is **binding**:

| # | Corrected fact |
|---|---|
| 1 | the successful path adds **one** `census_source_observations` row |
| 2 | it **also** adds **one** `census_projection_recovery_events` row, ending `resolved` |
| 3 | the new observation's `projected_to_audit` transitions **0 → 1** |
| 4 | `audit/sec/census_source_observations.jsonl` is **atomically replaced**, not appended |
| 5 | the path spans **three separately committed SQLite transactions** |
| 6 | end-to-end adoption **plus** projection rebuild is **not atomic** |
| 7 | **no source suppresses** the incident row after the orphan `INSERT` |
| 8 | the final `UPDATE` resolves **every** blocked event for the projection path |

**Two tables, two rows, three transactions.** Any later packet that restates the single-write
contract is refused.

### 4.2 The verified three-transaction sequence

Line references are to the committed baseline.

**Transaction 1 — the observation `INSERT`.**
One `BEGIN IMMEDIATE` (`src/disclosure_drift/storage/sqlite.py:100`), entered through
`CatalogWriter.batch()` (`src/disclosure_drift/storage/catalog.py:336`, which wraps `transaction()`
at `:338`), inserts one `census_source_observations` row and commits on exit.

**The later procedure performs that `INSERT` directly, and must not call
`ObservationRecorder.record`.** `record`
(`src/disclosure_drift/sec/observation_catalog.py:299`) opens `transaction(self.writer.connection)`
itself at `:343`, and `transaction()` issues `BEGIN IMMEDIATE` unconditionally
(`sqlite.py:100`) — so calling `record` inside `CatalogWriter.batch` would attempt a **nested**
`BEGIN IMMEDIATE` and raise rather than write. `record` and its serializer
`ObservationRecorder._row` are cited in this record — here and in §4.4 — **only** as the accepted
precedent for the persisted **row shape**, never as a surface the procedure invokes. §5.1 fixes the
direct form that reproduces that row exactly while taking the transaction once.

**Transaction 2 — the blocked incident `INSERT`.**
`rebuild_audit_projection` (`:634`) first calls `validate_audit_projection` at `:648`. Immediately
after transaction 1 the projection file holds `N` lines while SQLite holds `N+1` observations, so
`requires_recovery` is true and `_persist_projection_recovery_detection` runs at `:650`. That
function (`:1101`) opens its **own** transaction at `:1116` and inserts one
`census_projection_recovery_events` row with `resolution_state = 'blocked'`,
`release_blocking_before_resolution = 1`, `projection_sha256 = NULL`, `resolved_at_utc = NULL`.
It commits independently.

**Suppression is scoped, and does not apply here.** `_persist_projection_recovery_detection` returns
early **only** when a `blocked` row already exists **for that same `projection_path`** (`:1108`–`:1115`).
Under the mandatory zero-blocked-rows preflight (§7) no such row exists, so the incident row **is**
written. This is the exact mechanism behind corrected fact 7.

**Between the transactions — the durable file work.** The rebuild loads observations at `:651`
(`load_observations`, `:617`, ordered `retrieved_at_utc, recorded_at_utc, observation_id`), writes a
`uuid4`-named temporary at `:655`–`:665` with `fsync`, calls `temporary.replace(destination)` at
`:668`, `fsync`s the parent directory at `:671`, then **re-reads the destination and compares digest
and size against the temporary** at `:676`–`:682`, raising `CatalogWriteError` on mismatch **before**
any SQLite flag changes. Stale strictly-named temporaries are removed at `:683`.

**Transaction 3 — the flag and resolution `UPDATE`.**
`rebuild_audit_projection` opens its final transaction at `:686` and executes:

- `UPDATE census_source_observations SET projected_to_audit = 1` at `:687` — **unqualified**, so it
  sets the flag on every row, including the newly adopted one (0 → 1) and every pre-existing row
  already at 1 (1 → 1, a no-op in value);
- `UPDATE census_projection_recovery_events SET projection_sha256 = ?, resolution_state = 'resolved',
  resolved_at_utc = ?, detail = detail || ? WHERE projection_path = ? AND resolution_state = 'blocked'`
  at `:689`–`:700`.

The second statement is **path-scoped, not event-scoped**. It resolves **every** blocked event for
that projection path — including one that pre-dated this procedure. That is corrected fact 8, and it
is the reason §7's zero-blocked-rows gate is mandatory rather than advisory: a pre-existing blocked
event would be **both** suppressed at `:1108` **and** silently resolved at `:693`, destroying an
unrelated incident record.

`census_run_id` defaults to `None` (`:639`), so the `census_recovery_states` `UPDATE` at `:701`–`:710`
does **not** execute.

### 4.2.1 The two rebuild-owned instants — expected, and not the procedure's

A correct run generates **three** instants, not one. Exactly one of them belongs to the procedure;
the other two belong to the library and are **required** for the run to be correct:

| # | Instant | Owner | Where generated | Where it lands |
|---|---|---|---|---|
| 1 | `recorded_at_utc` | **the procedure** | §5.1 step 3, once, inside transaction 1 after both guards pass | the new `census_source_observations` row |
| 2 | `detected_at_utc` | **the library** | `utc_now()` evaluated inline in the transaction-2 `INSERT` at `:1130` | the `blocked` `census_projection_recovery_events` row |
| 3 | `resolved_at_utc` | **the library** | `now = utc_now()` at `:673`, after the directory `fsync` and before transaction 3 opens at `:686` | the same event row, on resolution at `:689`–`:700` |

Instants 2 and 3 are **not optional and not suppressible**. `0008:456` makes `detected_at_utc`
`NOT NULL`, so instant 2 must exist for the incident row to be insertable at all; `0008:459`'s
`CHECK ((resolution_state = 'resolved') = (resolved_at_utc IS NOT NULL))` makes instant 3 must-exist
for that row to reach its terminal `resolved` state. The same transaction-2 `INSERT` likewise
generates two library-owned `uuid4` identifiers — `event_id` (`:1124`) and `rebuild_identity`
(`:1129`).

**Consequently:** the "one instant, read once, used once" rule of §5.1 step 3 is scoped **solely to
constructing the new observation row's `recorded_at_utc`**. It is **not** a claim about the run as a
whole. Instants 2 and 3 are **expected**, must be **separately evidenced** (§11 items 6 and 14), and
are **not required to equal one another or to equal `recorded_at_utc`** — they are generated at
different points by different code, and any packet demanding their equality is refused.

### 4.3 Schema facts relied on

- `census_projection_recovery_events` — `0008_r3_durability_and_lineage.sql:445`–`:460`, `STRICT`,
  with `CHECK (resolution_state IN ('blocked','resolved'))` and
  `CHECK ((resolution_state = 'resolved') = (resolved_at_utc IS NOT NULL))`. A `resolved` terminal
  row therefore **must** carry a non-NULL `resolved_at_utc`; the §8 postcondition is enforced by the
  schema, not merely asserted.
- `census_source_observations.projected_to_audit` — `INTEGER NOT NULL DEFAULT 0 CHECK (… IN (0,1))`
  (`0002_source_observations.sql:57`; `0008:56`).
- `CatalogWriter.batch()` (`src/disclosure_drift/storage/catalog.py:336`) wraps `transaction()` and
  therefore takes the ordinary `BEGIN IMMEDIATE` inside the ordinary process-lifetime `fcntl` writer
  lease taken by `CatalogWriter.__enter__` (`catalog.py:107`).
- The `BEFORE INSERT` trigger `census_observation_lineage_insert` (`0008:145`) evaluates
  supersession and reuse lineage. The adopted observation carries neither
  (`supersedes_observation_id` and `reused_observation_id` default `None`,
  `src/disclosure_drift/sec/snapshots.py:139`–`:140`), so the trigger passes without writing.

### 4.4 Row-construction facts relied on

**The verifier does not produce a persistable row.** These are the facts §5.1's row-construction
requirements rest on; each was read directly at the committed baseline.

- `OBSERVATION_COLUMNS` (`observation_catalog.py:126`–`:161`) is the accepted **34-column** insert
  tuple for `census_source_observations`. Its final two columns are `projected_to_audit` and
  `recorded_at_utc`.
- `_observation_from_intent` returns a `SourceObservation`, and that dataclass carries **neither**
  `projected_to_audit` **nor** `recorded_at_utc`. The verifier therefore supplies **32** of the 34
  values and **structurally cannot** supply the last two.
- `ObservationRecorder._row(observation, now)` (`observation_catalog.py:558`–`:595`) is the accepted
  serializer that closes exactly that gap. It is a **`@staticmethod`**, so it is callable without
  constructing an `ObservationRecorder`. It fixes `projected_to_audit` to the literal `0` (`:593`)
  and `recorded_at_utc` to its `now` argument (`:594`), and it fixes the canonical JSON
  serialization of `validators_sent`, `headers`, `redirects`, and `redirect_hops` (`:572`–`:573`,
  `:589`–`:590`) — forms a hand-built tuple could silently get wrong while still inserting
  successfully.
- **`recorded_at_utc` is the only newly generated catalog value in the row.** `record` captures it as
  `now = utc_now()` at `:342`, before opening its transaction at `:343`.
- `_recover_orphan` (`:1372`–`:1387`) is the committed in-repository precedent for performing this
  construction **outside** `record`: it captures `now = utc_now()` at `:1373`, opens `transaction()`
  at `:1374`, re-checks for a duplicate `observation_id` **inside** that transaction at
  `:1375`–`:1379`, then executes a **direct** `INSERT` over `OBSERVATION_COLUMNS` with
  `ObservationRecorder._row(observation, now)` at `:1382`–`:1387`. §5 excludes `_recover_orphan`
  itself — for **both** of its fall-throughs to `RawStore.quarantine` at `:1400`–`:1411`, enumerated
  in §5 — but its **row-construction limb** is the accepted shape §5.1 requires. §5.1 is **stricter**
  in two respects: it also guards `relative_storage_path`, and it requires `cursor.rowcount == 1`.
- `record`'s own duplicate check (`self._exists(…)`, `:335`) runs **outside** the transaction. That is
  a second, independent reason the guards must be reasserted **inside** the procedure's own
  transaction rather than carried over from a pre-transaction read.

## 5. Ruling 057-B — Architecture C retained, corrected

The procedure shape is retained from the Decision 053 precedent and corrected for this operation.

**It must:**

- be **one ephemeral, one-time procedure** built in a disposable `mktemp -d` scratch directory
  **outside the repository**, existing as **exactly one file — the recorded artifact** — whose
  **SHA-256 is recorded privately before the §10 suite runs against it** and **re-verified
  immediately before the real transaction**;
- be **byte-immutable across the whole run**: the recorded artifact is **not edited, regenerated,
  reformatted, patched, or substituted** between the moment the §10 suite passes against it and the
  moment it performs the real `INSERT`. **The bytes that were proved are the bytes that execute.**
  Every mutated variant §10 case 15 requires is produced as a **disposable copy at a distinct path**,
  is **never** the recorded artifact, and is **destroyed with the fixtures**. Any difference between
  the two recorded digests — or an unavailable digest at either point — is a **STOP before any
  write**, referred to the owner (§7 gates 11–12). Without this binding the §10 proof would
  attach to no particular artifact: a compliant run could validate one file, hash a second, and
  irreversibly execute a third, and §12's bar on retry and re-adoption would make the substitution
  undiscoverable afterwards;
- be **identified by one canonical resolved path with a proven filesystem identity**, so that the
  digest binding above attaches to a determinate file rather than to a name. §5.2 fixes this.
- use the accepted **`_observation_from_intent` unchanged as its sole verifier**
  (`observation_catalog.py:1423`);
- use **`CatalogWriter`** and **one guarded `INSERT` inside `CatalogWriter.batch`**, thereby taking
  the ordinary OS-lock and writer lifecycle — which is the accepted single-writer boundary, not a
  workaround of it;
- construct, guard, and prove that `INSERT` **exactly** as §5.1 fixes — in-transaction re-checks on
  both the target `observation_id` and the target `relative_storage_path`, one captured
  `recorded_at_utc`, the accepted `OBSERVATION_COLUMNS` / `ObservationRecorder._row` tuple, and
  `cursor.rowcount == 1`;
- call **`rebuild_audit_projection` exactly once, mandatorily, in the same authorized process
  invocation** as the `INSERT` — but **after the `CatalogWriter.batch` context has exited and
  transaction 1 has committed**, never inside it (§5.1 step 6). The rebuild opens its **own**
  transactions (`:686`, and `:1116` via `_persist_projection_recovery_detection`), and
  `transaction()` issues `BEGIN IMMEDIATE` unconditionally (`sqlite.py:100`), so calling it inside
  the batch would nest and raise. **Same process, outside the batch context**;
- make that call in **exactly** the shape `rebuild_audit_projection(connection, destination)` —
  supplying **neither** `census_run_id` **nor** `fault_hook`. Both are keyword-only and default to
  `None` (`:638`–`:639`), and both defaults are load-bearing: a supplied `census_run_id` would
  enable the `census_recovery_states` `UPDATE` at `:701`–`:710` that §6 ruling 6 forbids, and
  `fault_hook` belongs **only** to the disposable synthetic suite (§10 cases 2 and 13), never to the
  real invocation;
- create **no permanent production surface and no tracked procedure**.

**It must never call:** `ObservationRecorder.record` (§5.1 — it opens its own transaction and would
nest inside `CatalogWriter.batch`); `apply_recovery_action`; `reconcile`; `_recover_orphan`;
`RawStore.quarantine`; `RawStore.reconcile`; `prepare_operational_catalog`; `migrate`;
`seed_reference_data`; any receipt, checkpoint, run-registration, or transport function; or any
live-acquisition entry point.

**Why the governed recovery surface is excluded.** `_recover_orphan` (`:1351`) verifies through the
same `_observation_from_intent`, but reaches `RawStore.quarantine` at `:1400`–`:1411` — which
**moves the governed raw object and its lineage intent** — by **two independent routes**, each
sufficient on its own to require the exclusion:

1. **Verifier failure.** On **any** verifier failure `failure` is set and control falls through to
   the quarantine limb.
2. **Duplicate observation identifier.** The in-transaction duplicate check sets
   `failure = "lineage intent reuses an existing observation identifier"` at `:1379`–`:1380`; the
   guard at `:1388` is then false and control falls to the **same** quarantine limb. So under
   `_recover_orphan` the exact condition §5.1 step 2 treats as a **one-use refusal** would instead
   **move the governed object**. This is the sharper of the two grounds and is the reason the
   exclusion is substantive rather than stylistic.

`reconcile` (`:1136`) additionally quarantines a stray lineage intent whose object is missing
(`:1222`–`:1226`). For a one-shot disposition of a single irreplaceable historical object, a verifier
failure **and** a duplicate identifier must each leave that object exactly where it is. Calling the
verifier directly and raising on failure is the only shape that guarantees it.

### 5.1 The exact form of transaction 1

The `INSERT` limb must take **exactly** this form, in this order. A later packet that satisfies §5's
prose while persisting a different tuple, generating more than one instant **for this row's
`recorded_at_utc`**, or failing to prove that exactly one row was written is **refused**. The
scoping matters: the run as a whole legitimately generates two further library-owned instants
(§4.2.1), and this rule says nothing about them.

1. Enter **one** `CatalogWriter.batch()` — one `BEGIN IMMEDIATE` (`sqlite.py:100`) inside the
   ordinary process-lifetime writer lease.
2. **On that same connection, inside that transaction,** reassert both guards: **no** row holds the
   target `observation_id`, and **no** row holds the target `relative_storage_path`. The §7 preflight
   readings do **not** discharge this — they are pre-transaction reads (§4.4).
3. **Only after both guards pass,** capture **exactly one** `recorded_at_utc = utc_now()`. One
   instant, read once, used once — **for this row's `recorded_at_utc`, and for nothing else**. This
   is a rule about constructing the observation row. It is **not** a claim that the run generates no
   other instant: transactions 2 and 3 generate their own library-owned `detected_at_utc` and
   `resolved_at_utc` (§4.2.1), which are expected and are **not** governed by this step.
4. Execute **one** direct `INSERT INTO census_source_observations` over the accepted
   `OBSERVATION_COLUMNS` (`observation_catalog.py:126`), with values that are **exactly**
   `ObservationRecorder._row(verified_observation, recorded_at_utc)` (`:559`), where
   `verified_observation` is the **unmodified** return of `_observation_from_intent`. The tuple is
   **not** hand-built, reordered, re-serialized, extended, or partially overridden.
5. Require **`cursor.rowcount == 1`**. Anything else — `0`, more than `1`, or unavailable — **raises
   inside the transaction**, so `transaction()` rolls back and nothing is committed. This check is
   **defense-in-depth and stays in the real procedure**: under the accepted plain-`INSERT` and
   schema shape a permitted insert yields exactly `1` and every other accepted outcome raises first,
   so the check is a **directly asserted invariant** rather than a branch expected to fire. The
   actual successful cursor result **must be asserted and evidenced** (§10 case 1, §11 item 14), not
   assumed. §10 case 15 states the corresponding — and deliberately narrower — proof obligation.
6. **Exit the `CatalogWriter.batch` context, committing transaction 1, before anything else
   happens.** `rebuild_audit_projection` is called **only after** that commit, in the same process
   but **outside** the batch (§5). Transaction 1 is the whole of the adoption limb; nothing else may
   ride inside it.

**`ObservationRecorder.record` must not be called.** It opens `transaction(self.writer.connection)`
itself (`:343`) and would nest a second `BEGIN IMMEDIATE` inside `CatalogWriter.batch`, raising
rather than writing. Steps 1–5 reproduce `record`'s persisted **row** exactly while taking the
transaction once — that is the whole reason the row shape is mandated here rather than inherited by
calling `record`.

**The guards are one-use refusals, not reconciliation.** A guard that fires is a **STOP referred to
the owner** under §12 — never an `UPDATE`, `INSERT OR REPLACE`, `INSERT OR IGNORE`, upsert, delete,
retry, or replay. **No path in this procedure revises, replaces, or re-writes an existing row.**

### 5.2 The canonical procedure artifact — path and filesystem identity

§5's digest binding proves *which bytes* were validated. This subsection fixes *which file* those
bytes are, so no residual path or symlink ambiguity can separate the artifact the §10 suite proved
from the artifact that performs the irreversible `INSERT`. It **strengthens proof identity only** and
**changes no part of the orphan-adoption architecture**.

1. **One canonical resolved path, resolved once.** The procedure artifact's private absolute path is
   resolved **exactly once**, before the first digest reading, and that resolved path is **recorded
   privately**. Every later step — the §10 suite, both digest readings, and the real invocation —
   refers to **that same recorded resolved path** and never re-resolves, re-derives, or re-globs it.
2. **Regular file, never a symlink, proven by `lstat` semantics.** At each of the two digest
   readings the artifact is inspected **without following symbolic links** and must be a **regular
   file**: `lstat`-equivalent metadata with `S_ISREG` true and `S_ISLNK` false. A symlink appearing
   at the recorded path — at either reading — is a refusal, not something to follow. The repository
   already uses exactly these primitives, so this imposes no new mechanism: `_open_no_follow`
   (`observation_catalog.py:950`, adding `os.O_NOFOLLOW` at `:953`–`:954`), the `S_ISREG` check at
   `:931`, and the `lstat`-based file-type refusal at `:1018`–`:1021`.
3. **Filesystem identity recorded where available.** At the first reading the artifact's **device and
   inode** are recorded privately alongside its size. Where the platform exposes them, they are
   **re-read and compared** at the second reading. They are corroborating identity, not a substitute
   for the digest: the SHA-256 comparison of §7 gate 12 remains the binding proof.
4. **The digest is taken over that exact artifact**, opened without following symlinks at the
   recorded resolved path — not over a name, a copy, or a re-resolved path.
5. **The §10 suite runs against that exact artifact** (§7 gate 10), and every case-15
   mutation-effectiveness variant is a **disposable copy at a distinct path** (§5, §10 preamble).
6. **The real invocation executes that exact recorded resolved path.** It is not invoked through a
   symlink, a copy, a re-resolved path, a relative path, or a path reconstructed from a name.
7. **Any of the following is a `STOP` before any write**, referred to the owner: the recorded
   resolved path is absent, replaced, or no longer a regular file; a symlink has appeared at it; its
   file type changed; its device or inode changed where those were recorded; either digest is
   unavailable; or the two digests differ.
8. **Private absolute paths, device numbers, and inode numbers stay out of the sanitized report and
   out of Git.** They are resolved and compared privately; the evidence bundle records only that the
   comparisons were performed and matched, over safe relative names (§11 items 2 and 12).

## 6. Ruling 057-C — exact content rulings

| # | Ruling |
|---|---|
| 1 | **Accept `_observation_from_intent`'s hardcoded `detail` unchanged** — `"verified adoption after raw promotion and before catalog commit"` (`:1514`). It is not overridden, appended to, or re-worded |
| 2 | **Accept `outcome = 'stored_new'`** exactly as the verifier fixes it (`:1492`) |
| 3 | **Accept `observation_id`, `retrieved_at_utc`, and every identity, hash, and size value exactly as the governed lineage intent and verifier output produce them.** No value is supplied, defaulted, corrected, or re-derived by the procedure. The **sole** exception is `recorded_at_utc` — ruling 8 |
| 4 | Write **zero** `census_observation_reasons` rows. **The ground is the procedure's own shape, not a library default:** §5.1 executes **exactly one** direct `census_source_observations` `INSERT` and issues **no** reason statement at all. The reason loop at `:350` lives inside the **prohibited** `ObservationRecorder.record` and never runs here, so it must not be cited as the reason. Corroborating but **not** load-bearing: `_observation_from_intent` never sets `reason_codes`, so the verified observation carries the `()` default (`snapshots.py:144`) — there would be nothing to write even if a loop existed |
| 5 | Write **zero** `census_archive_members` rows. **Same ground:** the procedure issues **no** member statement. `members = ()` at `:303` is a parameter default of the **prohibited** `record` and is **not** the reason; `_observation_from_intent` returns a bare `SourceObservation`, which carries no members at all — archive members reach the catalog only as a separate argument to `record`, which is never called |
| 6 | Call **neither** `record_recovery_events` (`:1619`) **nor** `open_recovery_state` (`:1675`); create **no** `census_recovery_states` row |
| 7 | Create **no** receipt, checkpoint, attempt, ingestion-job, or run-registration row |
| 8 | **`recorded_at_utc` is the sole catalog value the *procedure itself* generates, and the sole newly generated value in the observation row.** It is captured **once**, inside transaction 1 and only after both guards pass, as `utc_now()` (§5.1 step 3). Its value is **never** taken from the lineage intent, a caller argument, an environment value, or a second clock read. It is **not** `retrieved_at_utc`, which comes from the governed intent unchanged. **Scope:** this ruling is about the observation row and the procedure's own generation. It does **not** say the run generates nothing else — transactions 2 and 3 generate library-owned `detected_at_utc`, `resolved_at_utc`, `event_id`, `rebuild_identity`, and `projection_sha256` (§4.2.1), all expected, none of them the procedure's to supply or suppress |
| 9 | **Every persisted value is exactly the `ObservationRecorder._row` serialization** of the unmodified verifier result plus that one captured instant, written over the accepted `OBSERVATION_COLUMNS`. No column is added, dropped, reordered, re-serialized, or overridden |
| 10 | **`projected_to_audit` is inserted as `0`** — the literal `_row` fixes at `:593`. It is **not** pre-set to `1`. Transaction 3's rebuild is what moves it **0 → 1** (§8); pre-setting it would make that transition unobservable and would falsely satisfy the §8 flag postcondition |

## 7. Ruling 057-D — mandatory private preflight

All gates are **conjunctive** and **fail closed**. Any mismatch, ambiguity, or unavailable proof is a
**STOP before any write**, referred to the owner.

1. The accepted repository baseline is checked out, the working tree is clean, tracked network is
   **false / false**, and CompanyFacts is disabled.
2. Catalog migration head is **`0013`**; `quick_check`, `integrity_check`, and `foreign_key_check`
   are clean.
3. The historical M3.2A job is `stopped`; historical `ops_retrieval_attempts` count is **zero**; no
   receipt has been manufactured.
4. **Exactly one** orphan exists (`object_without_catalog_row`), **zero** `catalog_row_without_object`
   conditions exist, and **zero** stray lineage intents exist.
5. The audit projection **validates** before adoption — `validate_audit_projection` returns
   `is_valid`.
6. **Zero** rows with `resolution_state = 'blocked'` exist in `census_projection_recovery_events`
   **catalog-wide.** This is a deliberately **stronger** gate than the code's path-scoped checks
   (`:693`, `:1095`, `:1110`): the resolution `UPDATE` is path-scoped and would silently resolve a
   pre-existing blocked event for the same path, and a blocked event on any other path is itself an
   unadjudicated incident that must be referred before an irreversible one-shot proceeds.
7. **No row** already holds the target `observation_id`, and **no row** already holds the target
   `relative_storage_path`.
8. Lineage schema, path, request-identity, registry, storage-representation, hash, and size
   verification all pass **through `_observation_from_intent`** — not through a reimplementation.
9. **Writer-lease exclusivity, then unbroken continuity.** Two obligations, in that order.
   **(a) Exclusivity:** before the lease is taken, **no other live writer holds the OS lock.**
   **(b) Continuity:** the procedure acquires the accepted process-lifetime writer lease — the
   ordinary `CatalogWriter.__enter__` path (`catalog.py:107`), whose `_acquire_lease` takes
   `fcntl.flock(LOCK_EX | LOCK_NB)` on the mode-`0600` lock file — and **holds that same lease
   continuously and unbroken** across gate 13's snapshot, this recheck, gate 12's digest
   re-verification, and entry into transaction 1. The lease is **never released and reacquired**
   across that span, and the `CatalogWriter` context is **not exited and re-entered**.
   **Re-verified immediately before the real transaction:** the lease is still held by this process
   and was never dropped — the lock file's recorded `lease_id` and `writer_pid` are unchanged from
   acquisition. Any lost, released, replaced, or ambiguous lease is a **STOP before any write**.
   **This is what closes the mutation window** §7.1 exists to eliminate, and the frozen code makes
   it enforceable rather than merely asserted: while this process holds the descriptor, any other
   writer's `flock` fails with `SingleWriterViolationError`, and the accepted error text fixes that
   **"Elapsed time never permits takeover"** — so a `expires_at_utc` that lapses during a long
   snapshot **cannot** license another writer to seize the lease. Expiry metadata is recorded state,
   not a takeover licence.
10. The **§10 synthetic suite passes first**, against disposable fixtures, before the real catalog is
    touched, and **against the recorded artifact itself** (§5) — not against a copy, a variant, or a
    regenerated equivalent. **Counting, stated unambiguously:** that suite runs **before**,
    **outside**, and **without any access to** the governed real catalog, data root, raw object, or
    lineage intent. It is **not** the single real adoption invocation and is **never counted as one**.
    Running it is **not authorized by this record** — like every other limb here, it becomes
    performable only under the later owner execution instrument (§12 clause 9).
11. The exact procedure's **SHA-256 is recorded privately before the §10 suite runs against it**,
    taken over the **canonical resolved path** whose regular-file identity §5.2 requires be proven at
    the same moment. This is the **first** of the two required digest readings.
12. That **same SHA-256 is re-read from the recorded artifact and re-verified immediately before the
    real transaction**, after the suite has passed and after gate 9's exclusivity-and-continuity
    check. This is the **second** reading. The two must be **identical**, and §5.2's **path and
    filesystem identity** — same recorded resolved path, still a regular file, still not a symlink,
    same device and inode where recorded — must be **re-proven at the same moment**. **Any digest
    difference, any identity change, or an unavailable digest at either point, is a STOP before any
    write.** The gate is stated separately from gate 11 on purpose: recording a digest proves what
    existed once, while re-verifying it proves that the artifact about to perform the irreversible
    write is the artifact the §10 suite proved. Gate 11 without gate 12 leaves the proof attached to
    no particular bytes; gate 12 without §5.2 leaves it attached to no particular file.
13. A **source-bound, same-device, SQLite-native pre-adoption snapshot of the operational catalog**
    is created and **verified** under the continuously held gate-9 lease, **before any governed
    mutation**, and its identities are recorded privately. §7.2 fixes the mechanism, the
    source-to-snapshot binding, and the evidence; §7.1 fixes where it sits in the order. It is
    **accidental-loss and forensic comparison protection only**, consistent with the accepted
    milestone discipline (`Milestones/contracts/m3_2.md` §20; Decisions 047, 049, and 050). **It
    grants no restoration authority whatsoever**: §12 clauses 5–8 continue to prohibit every rerun,
    rollback, restore, and manual incident-row edit, and any restoration remains a **separate owner
    act** under its own ruling. Its purpose is to give the owner a contemporaneous pre-write image to
    compare against if the §8 "all other `census_*` and `ops_*` … unchanged" postcondition ever
    fails — and, because §7.2 binds it to the source, an image whose correspondence to that
    pre-write state is **proven rather than asserted**.

Private absolute paths, identifiers, identity values, and raw bodies are resolved **without printing
or committing** them.

### 7.1 Execution order

The thirteen gates above are a **conjunctive checklist**; this subsection is the **sequence**. Where
a gate's own prose implies a position, **§7.1 controls**. It adds no gate and removes none.

| Step | Action | Gates discharged |
|---|---|---|
| **A** | All ordinary **read-only** preflight gates pass, against the accepted baseline and — for the suite — against disposable fixtures only | 1–8, 10, 11 (with §5.2's first identity proof taken at gate 11) |
| **B** | **Acquire** the accepted process-lifetime writer lease and begin holding it | 9(a), then 9(b) acquisition |
| **C** | **Create and verify** the source-bound SQLite-native snapshot under that continuously held lease, before any governed mutation | 13, per §7.2 |
| **D** | **Final lease-continuity recheck** — the same lease, never released or reacquired | 9(b) re-verification |
| **E** | **Canonical procedure-artifact digest and filesystem-identity re-verification** | 12, with §5.2 |
| **F** | **Enter transaction 1 immediately thereafter** | §5.1 step 1 |

**The invariant this order exists to enforce:** **no uncontrolled interval may exist between C and F
in which another writer can mutate the source catalog.** The lease acquired at B is held unbroken
through F, so the state the snapshot captured at C is the state transaction 1 writes into at F. A
snapshot taken before the lease, or a lease released and reacquired anywhere across C→F, breaks that
binding and is a **STOP before any write** — the snapshot would then attest to a state that may no
longer exist.

Nothing in this order authorizes any step. Every step remains performable **only** under the later
owner execution instrument (§12 clause 9).

### 7.2 The source-bound snapshot — mechanism, binding, and evidence

#### 7.2.1 Mechanism — SQLite-native, and already accepted in the frozen repository

The snapshot is a **SQLite-native consistent backup**, never an unmanaged filesystem copy. The
hazard is real and code-confirmed, not theoretical: writer connections set
`PRAGMA journal_mode = WAL` (`storage/sqlite.py:86`), so the operational catalog **is** a WAL-mode
database, and a plain `cp` of the main database file can omit committed-but-uncheckpointed content.

**The frozen repository already provides the required mechanism, so no executable-code change is
needed and none is authorized.** `backup_database(source, destination)`
(`storage/sqlite.py:601`) performs `origin.backup(target)` at `:609` — the supported SQLite
online-backup interface — and its accepted docstring already fixes this exact rule: *"A naïve file
copy of a WAL-mode database is prohibited; this uses the supported online-backup interface
instead."* The later procedure uses that accepted function, or the same underlying
`sqlite3.Connection.backup` interface, and **nothing else**.

**Why calling it does not break gate 9's lease.** `backup_database` opens its own source connection
through `connect(source)` **without** `writer=True`. That path takes **no** writer lease and touches
**no** lock file (`catalog.py:107`'s `_acquire_lease` is not on it), and it sets no durability pragma
on the source. Invoking it from **inside** the already-held `CatalogWriter` context therefore leaves
the lease **unbroken**, which is precisely what §7.1 step C requires. It changes no `census_*` or
`ops_*` row and no schema. It is also **not** one of §5's prohibited surfaces: it does not migrate,
seed, prepare, reconcile, quarantine, register, or write to the governed catalog — it reads the
source and writes the disposable snapshot.

The destination is a **same-device** file in the disposable private scratch area **outside the
repository**, mode `0600`.

#### 7.2.2 Source-state evidence, recorded before the snapshot

Immediately before snapshot creation, under the held lease and **before any governed write**, record
privately, for the **live source catalog**:

1. the database file's **SHA-256** and **byte size** — *provenance*;
2. **schema/migration identity** — the applied migration versions (expected head **`0013`**,
   contiguous `0001`–`0013`, via the accepted `applied_versions`, `storage/sqlite.py:184`) and
   `PRAGMA user_version`;
3. **canonical safe row counts** for **every** `census_*` and `ops_*` table already required by the
   §11 before-state evidence contract;
4. a **canonical content digest** for each of those tables.

**Canonical content digest, defined once so source and snapshot are comparable.** For a table: order
its rows deterministically by the declared primary key, or — where there is no single-column primary
key — by every column in declared order; serialize each row as a canonical JSON object mapping column
name to value with sorted keys and no insignificant whitespace; fold the per-row encodings, in that
order, into one SHA-256. **The identical algorithm is applied to source and snapshot.** This needs
only the standard library and reads only; it introduces no repository surface.

#### 7.2.3 Snapshot-state evidence, recorded after creation

Over the created snapshot, record privately the **same four classes**: snapshot file SHA-256 and byte
size (*provenance*), schema/migration identity, canonical safe row counts, and the canonical content
digest per table.

#### 7.2.4 The binding comparison — logical equality, not byte equality

**Raw-file digest equality is expressly NOT required and must never be demanded.** A SQLite-native
backup of a WAL-mode source is a freshly written database; its file bytes will ordinarily **differ**
from the source file's. A packet requiring `source SHA-256 == snapshot SHA-256` would fail every
correct run and is **refused**.

The **binding proof** that the snapshot corresponds to the exact pre-write catalog state is
**logical-state equality**, all of which must hold:

- **identical schema/migration identity** — same applied migration versions and same `user_version`;
- **identical row counts** for every required `census_*` and `ops_*` table;
- **identical canonical content digests** for every required `census_*` and `ops_*` table;
- the snapshot's **`quick_check` clean**, **`integrity_check` clean**, and **`foreign_key_check`
  empty** — via the accepted `integrity_report` (`storage/sqlite.py:593`).

**Any mismatch, ambiguity, or unavailable comparison is a STOP before any write**, referred to the
owner. The raw digest/size pairs of §7.2.2 item 1 and §7.2.3 are retained as **provenance**; they are
**not** the binding proof, and their inequality is **never** a failure.

#### 7.2.5 Placement and restoration authority — unchanged and absolute

The snapshot remains **same-device**, **private**, **mode `0600`**, **outside Git and outside the
repository**, never committed and never publicly indexed, and **forensic and comparative only**. It
confers **no** rollback, **no** automatic restore, **no** manual restore, **no** retry, **no** replay,
and **no** re-adoption authority. §12 clauses 5–8 are untouched. **Any restoration remains a separate
Sol/GPT owner act under its own ruling**, and the existence of a verified snapshot is never evidence
that one was available or permitted.

## 8. Ruling 057-E — the correct successful terminal delta

A successful run **must** satisfy **all** of the following. Nothing less is success.

**Catalog:**

- `census_source_observations` count **N → N+1**;
- the target row's `projected_to_audit` **0 → 1**, and **every** row's flag is **1**;
- the target row's persisted tuple is **exactly**
  `ObservationRecorder._row(verified_observation, recorded_at_utc)` under `OBSERVATION_COLUMNS`, and
  its **`recorded_at_utc` equals the single instant the procedure captured in transaction 1**
  (§5.1 step 3) — **exactly one procedure-generated instant exists, and it is that field's value**.
  **This postcondition is scoped to the observation row and to the procedure's own generation.** It
  is emphatically **not** a requirement that no other instant exists in the run: a correct run also
  carries the two **library-owned** instants of §4.2.1, and a packet that asserts otherwise, or that
  fails a run for producing them, is **refused**;
- the **two rebuild-owned instants are present and separately evidenced** — the incident row's
  `detected_at_utc` (non-NULL by `0008:456`) and its `resolved_at_utc` (non-NULL by `0008:459` once
  `resolved`). They are recorded as distinct values (§11 items 6 and 14). They are **not required to
  equal one another, and not required to equal `recorded_at_utc`**; equality between any of them is
  neither expected nor a success criterion, and inequality is **never** a failure;
- every **pre-existing logical row value** is unchanged;
- `census_projection_recovery_events` count **+1**; that row is terminal `resolved`, with a
  **non-NULL `resolved_at_utc`** and `projection_sha256` **equal to the digest of the new projection
  file**;
- **zero** `blocked` rows remain **catalog-wide**;
- **all other** `census_*` and `ops_*` row counts and content are **unchanged**.

**Projection:**

- the JSONL projection goes **N → N+1** lines and **validates**;
- **no temporary residue** remains — no `.<name>.<32-hex>.tmp` file survives.

**Raw store:**

- the raw object and its lineage intent are unchanged in **SHA-256, size, inode, and location**;
- orphan count **1 → 0**; `catalog_row_without_object` **0**; attempts **0**; **no** receipt and
  **no** checkpoint created.

**Environment:**

- the repository is **unchanged**; network remains **disabled**; no SEC or DNS action occurred.

**Terminal classification.** The receiptless terminal determination for the old run is expected to be
**`UNSAFE`**, **solely because no predecessor receipt exists** — never because the adoption failed.
The old run remains **permanently non-resumable**, and `UNSAFE` **never authorizes resumption**.
**`SAFE` is not expected and could not authorize anything**: receiptless inspection is inspection-only
and structurally cannot return `SAFE`. The **current, pre-execution** recovery state remains
**`UNDETERMINED`**.

## 9. Ruling 057-F — three-transaction fault semantics

**The procedure is not atomic end-to-end.** Transaction 1 and transaction 3 are each locally atomic;
the sequence spanning them, the incident insert, and the file replacement **is not**. Any later
packet claiming end-to-end atomicity is refused.

The six interruption points, each classified **fail-closed**:

| # | Interruption point | State | Classification |
|---|---|---|---|
| 1 | **before** the observation commit | nothing written; orphan intact | **NO-OP** — the adoption did not occur |
| 2 | **after** the observation commit, **before** the incident insert | observation committed; projection stale by one line; every flag on the new row `0`; **no** incident row | **ADOPTED, PROJECTION UNRECONCILED** |
| 3 | **after** the blocked incident insert, **before** the file replace | as above **plus** one `blocked` incident row; projection file still the old `N` lines | **ADOPTED, RECOVERY BLOCKED** |
| 4 | **after** the file replace, **before** the directory fsync | new `N+1`-line projection in place but its directory entry is not durable; flags and incident still stale | **ADOPTED, REPLACEMENT NOT PROVEN DURABLE** |
| 5 | **after** the fsync, **before** the final SQLite update | projection durable and correct; `projected_to_audit` still `0` on the new row; incident still `blocked` | **ADOPTED, FLAGS AND INCIDENT UNRESOLVED** |
| 6 | **after** the final update | all §8 postconditions met | **CANDIDATE SUCCESS** — confirmed only by the full §8 check |

**Rules.**

- **No successful completion may be claimed unless every §8 terminal postcondition passes.** Reaching
  point 6 is necessary, not sufficient.
- States 2–5 are **not** failures of the adoption limb — the observation is committed and must never
  be re-adopted. They are **unfinished projection reconciliation**, and each is referred to the owner
  under §12.
- Fault points 3, 4, and 5 correspond exactly to the committed fault hooks
  `after_rebuild_temporary_durable_before_replace` (`:667`),
  `after_rebuild_replace_before_directory_fsync` (`:670`), and
  `after_rebuild_directory_fsync_before_catalog_update` (`:685`), so each is reachable and provable
  in the synthetic suite rather than reasoned about.
- **State 5's window also carries durable-but-*incorrect*-projection exception paths**, and its
  description above — "projection durable and correct" — is written for the **interruption** case
  only. **At least** the following **three** committed exception routes raise inside the same window,
  after the directory `fsync` at `:671` and before transaction 3 opens at `:686`:
  1. **Digest/size comparison failure** — the re-read comparison raises `CatalogWriteError` at
     `:676`–`:682` because the atomically replaced projection does **not** match the durable
     temporary.
  2. **Ambiguous stale-temporary cleanup failure** — `_remove_stale_projection_temporaries` at
     `:683` refuses an ambiguous artifact, or cannot inspect the parent directory, and raises
     `CatalogWriteError`.
  3. **Destination re-read I/O failure** — `_digest_projection_path` (`:993`) itself raises while
     re-reading the destination at `:676`; it opens the file with `_open_no_follow` and reads it in
     chunks, so an `OSError` from either step lands in this same window without ever reaching the
     comparison of route 1.

  **The list is deliberately open, not exhaustive: "at least" is binding.** **Any other exception
  raised in the same code window receives the same state-5 stop-and-refer classification unless a
  later accepted record separately governs it.** In every one of these routes the replacement is
  durable and the projection is **not** correct — or its correctness is **unestablished**, which is
  handled identically. **Classification and handling are identical throughout** — the catalog state
  is exactly state 5, the run stops, and it is referred to the owner under §12 clause 5 — but the
  report must **not** repeat "durable and correct" where the digest comparison failed, could not be
  performed, or was never reached. §8 forecloses any success claim regardless (the projection must
  **validate**, and §9 rule 1 makes reaching point 6 necessary but not sufficient), and §11 item 7
  records the actual **S0**/**S1** digests, so the owner sees the mismatch directly. **This changes no
  recovery or retry behaviour and creates no mutation authority**: §12 clauses 4–8 apply unchanged.

## 10. Ruling 057-G — synthetic non-vacuity requirements

Against disposable fixtures, **before** the real catalog is touched, and — per §7 gate 10 — **never**
against the governed catalog or object, and **not authorized by this record**.

**What the suite runs against, and what it may never alter.** The suite exercises **the recorded
artifact itself** (§5, §7 gates 10–12) — the one file whose SHA-256 was recorded before the suite
began and is re-verified immediately before the real transaction. Every mutation this section
requires is applied to a **disposable copy at a distinct path**, never to the recorded artifact,
and every such copy is destroyed with the fixtures. **A mutation limb that edits the recorded
artifact in place invalidates the run**: the digest re-verified at §7 gate 12 would no longer match,
which is a STOP before any write. This is what makes the **sixteen** cases below evidence about the
bytes that actually perform the irreversible `INSERT`, rather than about some artifact that merely
resembled them.

**The non-vacuity rule, stated correctly.** Every case that guards a **behaviourally reachable**
requirement must be **non-vacuous**: it must be shown to fail when the behaviour it guards is
removed. That covers **all** row-shape, timestamp, flag, and nested-transaction mutations, and each
of those remains **mandatory and non-vacuous**.

**The one carve-out — the `rowcount` guard.** `cursor.rowcount == 1` is a **statically and directly
asserted invariant**, not a required negative-mutation demonstration. Under the accepted plain
`INSERT INTO … VALUES (…)` and the accepted schema, a **permitted** insert yields exactly `1` and
**every** other accepted outcome raises before the check is reached — so there is no behaviourally
reachable state in which deleting the check changes the outcome. Demanding that its removal be
caught by a non-vacuous mutation demands the impossible, and any packet restating that demand is
**refused**. What **is** required: the check **stays in the real procedure** as defense-in-depth
(§5.1 step 5), and the **actual successful cursor result is asserted and evidenced** (case 1, §11
item 14).

| # | Case | Required behaviour |
|---|---|---|
| 1 | healthy fixture: valid projection, zero blocked rows | positive control — full §8 delta reproduced, **including** that the persisted target tuple equals `ObservationRecorder._row(verified_observation, recorded_at_utc)` under `OBSERVATION_COLUMNS` **field by field**; that the procedure captured **exactly one** instant **of its own** and it is that row's `recorded_at_utc`; that the **two library-owned instants** of §4.2.1 are separately observed as present and non-NULL, with **no equality asserted** between them or against `recorded_at_utc`; and that the **actual successful `cursor.rowcount` was `1`**, asserted directly from the real cursor rather than assumed |
| 2 | **blocked observed mid-flight** via fault hook | the incident row is proven to exist as `blocked`, then proven `resolved` — `blocked → resolved` observed, not inferred |
| 3 | orphan sorting **last** under `load_observations` order | correct projection content and ordering |
| 4 | orphan sorting **middle** and **first** | correct projection content and ordering |
| 5 | pre-existing observation values | proven **unchanged**, field by field |
| 6 | **negative table assertions** | zero rows added to `census_observation_reasons`, `census_archive_members`, `census_projection_recovery_events` beyond the one, `census_recovery_states`, and every `ops_*` table |
| 7 | **verifier failure** | the raw object and lineage intent are **preserved in place**; **zero** writes occur |
| 8 | duplicate `observation_id` | refuses before any write |
| 9 | duplicate `relative_storage_path` | refuses before any write |
| 10 | **two** orphans present | refuses — the preflight requires exactly one |
| 11 | **lock contention** | refuses; no partial effect |
| 12 | **fault inside the transaction** | rolls back; neither row nor partial effect |
| 13 | **fault at each of the three projection fault points** | classified per §9; never reported as success |
| 14 | **non-vacuous contrast** | a `reconcile`/`quarantine` variant is shown to **move a disposable fixture object** — proving the excluded path is materially different, and that the governed real object is never exposed to it |
| 15 | **row-shape non-vacuity, and the `rowcount` assertion** | **Mutation limb (mandatory, non-vacuous).** Mutating or removing §5.1's row construction **must fail the suite**. Each of these is shown to be **caught**: a hand-built, reordered, or re-serialized tuple; a `recorded_at_utc` taken from the lineage intent or a caller argument; a **second procedure clock read used for the observation row's `recorded_at_utc`** — scoped to the procedure's own reads, since the library's §4.2.1 reads are expected and must **not** be counted against it; and a `projected_to_audit` pre-set to `1`. Separately, a nested `ObservationRecorder.record` call inside `CatalogWriter.batch` is shown to **raise rather than write**. Every mutation here is applied to a **disposable copy**, never to the recorded artifact (see above the table). **Assertion limb (mandatory, not a mutation).** The **real** `cursor.rowcount` is asserted to be `1` on the successful path and that value is evidenced. **A removed `cursor.rowcount == 1` check is _not_ required to be caught by a mutation** — it cannot be, for the reason given above the table — and no packet may demand it |
| 16 | **pre-existing `blocked` row on a different `projection_path`** | **Refuses before any write.** A disposable fixture carries one `census_projection_recovery_events` row with `resolution_state = 'blocked'` whose `projection_path` is **not** the adoption target's, and the procedure is proven to **stop at §7 gate 6 before the `INSERT`** — zero rows written to any table, the fixture orphan left in place, the unrelated incident row left `blocked` and unmodified. **Why this case is required and why it is separate.** Gate 6 is the record's strongest preflight ruling (§7, §15 `BLOCKED_ROW_PREFLIGHT`), yet the *same-path* variant it also covers is already refused by gate 5 in code — a same-path `blocked` row makes `_has_unresolved_projection_recovery` true, so `validate_audit_projection` adds `unresolved_recovery_event` and `is_valid` is false. **The catalog-wide extension has no such code backstop**: a `blocked` row on another path leaves the projection valid and the path-scoped `UPDATE` at `:693` untouched, so a procedure that omitted or mis-implemented gate 6 would proceed into a one-shot with an **unadjudicated incident** open, and **no other case would catch it**. Cases 8, 9, and 10 each prove a preflight refusal; this closes the one gate that had none |

Case 14 is mandatory and must run **only** against a disposable fixture. It exists to prove §5's
exclusion is substantive rather than stylistic. **Case 15 is mandatory too, in both limbs**, but for
two different reasons: §5.1's **row construction** is a behaviourally reachable requirement, so a
suite that would still pass with it removed has not proved it; the **`rowcount` guard** is instead a
directly asserted invariant, so what case 15 proves about it is that the real successful cursor
returned `1`, not that its deletion is detectable. **Case 16 is mandatory** and is a
behaviourally reachable refusal, so it is **non-vacuous** under the rule above: a procedure with
gate 6 removed must fail it.

**Cases 1–14 are preserved as accepted and are not renumbered; case 15 is additive and unchanged
apart from the disposable-copy clause; case 16 is additive.** The suite is now **sixteen** cases.
The count grew by the same additive mechanism that took it from fourteen to fifteen — an accepted
case is never renumbered, absorbed, or retired to hold a number constant.

## 11. Ruling 057-H — the private evidence contract

The later execution must produce a **private, mode-`0600` execution bundle and manifest**, outside
Git, over **safe relative names only**, containing at minimum:

1. the **accepted Decision 057 commit identity**, once published;
2. the **procedure SHA-256, recorded as both required readings** — the digest taken before the §10
   suite ran against the recorded artifact (§7 gate 11) and the digest re-read immediately before the
   real transaction (§7 gate 12) — together with the **explicit assertion that the two were
   identical**. Two values and their comparison, never one value restated twice, and never a
   requirement restated in place of an observed reading. Recorded alongside them, per **§5.2**: that
   **one canonical resolved path** was resolved once and used throughout; that at **both** readings
   the artifact was proven a **regular file and not a symbolic link** under `lstat` semantics; that
   its **device and inode matched** between the readings where the platform exposed them; and that
   the **real invocation executed that same recorded resolved path**. Recorded over **safe relative
   names only** — the private absolute path, device number, and inode number are compared privately
   and **never** written into the bundle or Git. Together these bind the sixteen-case proof to the
   exact **file** and the exact **bytes** that performed the irreversible `INSERT`;
3. **safe before/after counts**;
4. the incident **`event_id`**;
5. the incident **`detected_condition`**;
6. the **two rebuild-owned instants** — the incident row's **`detected_at_utc`** and its
   **`resolved_at_utc`** (§4.2.1) — recorded as **two separate values**. They are **library-owned**,
   **expected**, and **not required** to equal one another or the transaction-1 `recorded_at_utc` of
   item 14;
7. projection digests **S0** (before) and **S1** (after);
8. a **safe table-delta summary**;
9. raw-object and lineage **before/after hashes, sizes, and inodes**, **without private absolute
   paths**;
10. **synthetic case results**;
11. **integrity results**;
12. **repository, configuration, and network assertions**;
13. an explicit **termination classification** drawn from §9;
14. the transaction-1 **captured `recorded_at_utc`** — the **one instant the procedure itself
    generated**, recorded as its own value and **distinct from** the two library-owned instants of
    item 6, with **no equality asserted or expected** between them — together with the assertions
    that the persisted target row equalled `ObservationRecorder._row` under `OBSERVATION_COLUMNS`
    and that the **real** `cursor.rowcount` was **`1`** on the successful `INSERT`, recorded as the
    **observed** cursor result rather than a restated requirement. All of these are recorded as
    **safe** values, never beside a private absolute path or an identity value;
15. the **§10 case 16 result** — the proof that a `blocked` row on a different `projection_path`
    refuses before any write — recorded alongside the other synthetic case results of item 10;
16. the **source-bound pre-adoption catalog snapshot record** (§7 gate 13, §7.2), over **safe
    relative names only**, containing every one of:
    - the **live source catalog's SHA-256** and **byte size** (provenance);
    - the **snapshot's SHA-256** and **byte size** (provenance);
    - the **source and snapshot schema/migration identity** — applied migration versions and
      `user_version` — recorded for both and asserted **equal**;
    - the **canonical content digest per table**, for every required `census_*` and `ops_*` table,
      recorded for both and asserted **equal**;
    - the **safe row counts** for those tables, recorded for both and asserted **equal**;
    - the snapshot's **SQLite validation results** — `quick_check`, `integrity_check`, and
      `foreign_key_check`;
    - **continuous writer-lease evidence** — that the gate-9 lease was acquired before the snapshot
      and held **unbroken**, never released and reacquired, through the snapshot, the continuity
      recheck, the artifact digest re-verification, and entry into transaction 1 (§7.1 B→F);
    - the explicit statement that the binding proof is the **logical** comparison, that **raw-file
      digest inequality between source and snapshot is expected and is not a failure** (§7.2.4);
    - the explicit statement that **the snapshot conferred no restoration authority, that no
      restoration was performed, and that none was authorized**.

    Its presence in the bundle is forensic and comparative; it is **never** evidence that a rollback
    was available.

**Never placed in Git:** private absolute paths, user identity values, `.env` contents, raw SEC
response bodies, credentials, or the raw object itself.

**Binding correction.** [Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md)
§6.1 requires the carry-in authority to bind "the later accepted orphan-adoption decision identity
and evidence identity." That binding is to the **eventual accepted orphan-adoption decision** and the
**accepted evidence-manifest SHA-256** — **not** to this architecture record. Decision 057 fixes the
procedure; it is not the acceptance, and a carry-in artifact must never bind it as though it were.

## 12. Ruling 057-I — execution and recovery boundary

This ruling **overrides** the remediation addendum's unbounded "retry to success" recommendation.

1. **Decision 057 performs and authorizes no real invocation.**
2. After a passing **final** fresh independent review (§16) and a separate owner publication ruling, the exact next
   action is a **separate owner execution packet**.
3. That later packet may authorize **exactly one real process invocation** — one that touches the
   **governed** catalog, data root, raw object, or lineage intent — and **no second**. That single
   invocation must attempt **both** limbs: the adoption **and** one mandatory
   `rebuild_audit_projection` call, the second called after the batch commits and outside it
   (§5.1 step 6). Clause 9 states exactly what does and does not count against that one.
4. **No retry loop, no auto-retry, no auto-resume, no automatic relaunch, and no "retry until
   success"** is authorized under any failure point.
5. **Any exception, interruption, uncertainty, or failed postcondition stops and refers to the
   owner.**
6. If the observation `INSERT` is **proven not committed** (state 1), any later adoption attempt
   requires **new owner authority**.
7. If the `INSERT` **is committed, or its commit state is uncertain** (states 2–6), the adoption
   **must never be rerun**. The only authorized next step is **read-only classification**; only a
   **separate explicit rebuild-only recovery ruling** may authorize any further mutation.
8. **No manual `UPDATE` or `DELETE` of an incident row** is authorized under any circumstance.
9. **What "exactly one" counts, stated unambiguously.** The mandatory §10 synthetic preflight suite
   runs **before**, **outside**, and **without any access to** the governed catalog, data root, raw
   object, or lineage intent, entirely against disposable fixtures. It is therefore **not** the
   single real adoption invocation and is **not counted as one** — running it does not consume the
   one permitted invocation, and completing it does not create a second. **Exactly one real process
   invocation may touch the governed object or catalog**, only under a later owner execution
   instrument, and **no second real invocation is authorized** under any outcome. **This record
   authorizes neither.** Nothing here — including the synthetic suite — becomes performable on the
   strength of this record; Decision 057 remains architecture-only.

## 13. Limitations disposition

```text
M3_L14:  CLOSED — DECISION 056; UNTOUCHED BY THIS RECORD
M3_L15:  ACTIVE — UNTOUCHED AND BYTE-UNCHANGED
M3_L16:  ACTIVE — PROCEDURE ARCHITECTURE ACCEPTED; ADOPTION NOT AUTHORIZED, NOT PERFORMED;
         STILL BLOCKS EVERY CLEAN-RUN AND LIVE AUTHORIZATION
```

**M3-L16 remains `ACTIVE`.** Fixing the procedure architecture is **not** performing the adoption and
is **not** closing the entry. Its outstanding closure requirements are unchanged: the separately
authorized one-time verified adoption, its independent verification and owner acceptance with **zero
unresolved orphan mismatch**, and a **separate owner closure act**.

**No carry-in authority may be minted or consumed.** Consumption remains **1 of 801**; the old run
remains **never resumable**; recovery remains **`UNDETERMINED`**. **M3-L15 is preserved
byte-for-byte.**

## 14. Path and publication boundary

Exactly **four** repository paths are authorized for this recording, with **no fifth**:

1. `Docs/Decisions/decision_057_m3_2_orphan_adoption_procedure_authorization.md` (this record)
2. [`Docs/Decisions/decision_registry.md`](decision_registry.md)
3. [`Milestones/STATUS.md`](../../Milestones/STATUS.md)
4. [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) — **M3-L16** current
   authority, status, mitigation, and closure text **only**; **M3-L15 and every unrelated entry are
   preserved byte-for-byte**

[`Docs/decision_index.md`](../decision_index.md) is **not** edited, following the convention for
Decisions 050–056.

Expressly **not** edited: any accepted decision 001–056; the accepted contract; the receipt
specification; the operator runbook; every template and evidence index; the SEC data dictionary;
every durable review artifact; every production source; every test; every configuration; every
migration; every reason code; the master plan; the `Makefile`; `pyproject.toml`; and every script.

**Publication status — corrected, and stated as fact rather than as intent.**

**Preserved as historical — two superseded authoring-stage boundaries, each true only when written,
and each explicitly NOT a statement of current state.**

- *From the original authoring task, before publication 1:* *"Publication is not authorized by the
  authoring task. This record is an uncommitted candidate. Nothing is staged, committed, pushed, or
  tagged."* And of the subject below: *"That subject is reserved, not authorized. It becomes usable
  only under a separate owner publication ruling issued after the §16 review passes. No publication
  has occurred."*
- *From the third remediation, before publication 2:* *"This remediation is itself uncommitted.
  Nothing is staged, committed, pushed, or tagged by the task that produced it. Its publication
  requires a separate owner ruling issued after the fresh non-author review §16 now names."*

Both quotations bounded what their **authoring task** could do at the moment of writing. Both were
**overtaken by events** — publication 1 at `9475eb3d…` and publication 2 at `103b3d39…` respectively
— and both are preserved here in the §3 style rather than silently deleted. **Neither describes the
current state, and no session may read either as current.** A governance record must not deny an act
the repository can prove; the post-remediation rereview correctly found the second quotation stated
as current fact inside the very commit that falsified it, and that defect is corrected here.

**Current fact — publication has occurred twice, and both identities are recorded.**

**Publication 1 — the original candidate.** This record was first committed and pushed as:

```text
commit  9475eb3d614aa70b3f2a04b061d63bd7ea51c030
tree    e0b9b12095c181ba974336399f04fc1e44eb4a11
parent  ea0647459ef38069c75f7b8da2873abf0cbccdb1
subject Authorize M3.2 orphan-adoption procedure architecture
```

There is **no tag**; the change set is exactly the **four authorized paths above and no fifth**; and
the subject used is exactly the one this section reserved.

**Publication 2 — the first corrected remediation, owner-ratified as fact.** The third remediation
(§3) was subsequently committed and pushed as:

```text
commit  103b3d3910e11fee43f66d8451f101019487588e
tree    04bd61ca09be271752d432c82f0c2f6a02eb277c
parent  9475eb3d614aa70b3f2a04b061d63bd7ea51c030
subject Correct Decision 057 after failed independent review
```

Again **no tag**, and again exactly the four authorized paths and no fifth.
**Sol/GPT has ratified `103b3d39…` as the factual historical publication identity of the corrected
remediation candidate.** That ratification is **publication-fact ratification ONLY**. It does **not**
mean the post-remediation rereview passed, that the candidate is accepted for operational execution,
that orphan adoption is authorized, that **M3-L16** may close, or that any later phase is authorized.
**Factual ratification is not execution acceptance, and no session may read it as such.**

**The sequence anomaly, recorded plainly — it happened twice.** Publication 1 preceded the passing
§16 review this section named as its precondition; that review was then performed and returned
**`DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_FAIL`**. Publication 2 then occurred in the same
order: **`103b3d39…` was published before any qualifying fresh independent `PASS` review existed**,
and the post-remediation rereview attempted against it returned
**`DECISION_057_POST_REMEDIATION_FRESH_INDEPENDENT_REVIEW_FAIL`** — 0 BLOCKER, 1 MAJOR, 2 MINOR,
2 OPTIMIZATION (§3, remediation 4). **Neither publication created any operational authority**, and
neither is a substitute for the review gate. **This fourth remediation is the correction of that
failed rereview result.** Whether publication 1 is ratified as-published, ratified retrospectively,
or superseded remains an **owner ruling**; this record neither ratifies nor voids it.

**This fourth remediation's own publication.** Publication of this correction is **authorized** — by
the bounded owner instrument that directed it, which permits exactly **one** commit on `main` over
exactly these four paths, exactly **one** ordinary push, and **no tag**. It is therefore **not** an
uncommitted candidate awaiting a publication ruling; the ruling exists and the act is part of this
instrument. A record cannot contain the hash of the commit that contains it, so **this record's own
commit identity is established by that act and recorded in the owner's post-publication freeze
record**, not inside these bytes — that is a property of self-reference, never a denial that
publication occurred. **That new commit becomes the sole frozen target of the next qualifying
rereview.**

**What follows from this for a later execution packet.** §11 item 1 requires the bundle to carry
"the accepted Decision 057 commit identity, once published." Published identities now exist —
`9475eb3d…`, `103b3d39…`, and this correction's commit — but a **published** identity is **not** an
**owner-ratified accepted** one, and the two must never be conflated. `103b3d39…` is ratified as
publication **fact** only. A later execution packet must bind the identity the owner ratifies **for
execution**, which will be the latest published Decision 057 commit at that time and which no
session may assume in advance.

## 15. Recorded status

```text
ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE:   ACCEPTED — BINDING
RECORD_IS_SELF_EXECUTING:                 NO — FIXES REQUIREMENTS, GRANTS NO INVOCATION
DISCOVERY_MAJOR_CORRECTION:               CONFIRMED — SINGLE-WRITE CONTRACT REPLACED
CORRECTED_CONTRACT:                       TWO TABLES, TWO ROWS, THREE TRANSACTIONS
END_TO_END_ATOMICITY:                     NO — T1 AND T3 LOCALLY ATOMIC ONLY
STATE_5_EXCEPTION_ROUTES:                 AT LEAST THREE, NOT EXACTLY TWO — DIGEST/SIZE COMPARISON FAILURE AT :676-:682; AMBIGUOUS STALE-TEMPORARY CLEANUP FAILURE AT :683; DESTINATION RE-READ I/O FAILURE IN _digest_projection_path AT :993 REACHED FROM :676. ANY OTHER EXCEPTION IN THE SAME WINDOW TAKES THE SAME STATE-5 STOP-AND-REFER CLASSIFICATION UNLESS SEPARATELY GOVERNED. THE TABLE'S "DURABLE AND CORRECT" WORDING DESCRIBES THE INTERRUPTION CASE ONLY. NO CHANGE TO RECOVERY OR RETRY BEHAVIOUR AND NO NEW MUTATION AUTHORITY
INCIDENT_ROW_SUPPRESSION:                 NONE AFTER THE ORPHAN INSERT
BLOCKED_ROW_PREFLIGHT:                    ZERO CATALOG-WIDE — STRONG OWNER RULING
PROCEDURE_SHAPE:                          ARCHITECTURE C — EPHEMERAL, SHA-256-RECORDED, ONE-TIME
PROCEDURE_ARTIFACT_IMMUTABILITY:          ONE RECORDED ARTIFACT, BYTE-IMMUTABLE FROM SUITE-PASS THROUGH THE REAL INVOCATION; SHA-256 RECORDED BEFORE THE SUITE RUNS AND RE-VERIFIED IMMEDIATELY BEFORE THE REAL TRANSACTION; ANY DIFFERENCE OR UNAVAILABLE DIGEST IS A STOP BEFORE ANY WRITE; CASE 15 MUTATIONS RUN ON DISPOSABLE COPIES ONLY
PROCEDURE_ARTIFACT_PATH_IDENTITY:         SECTION 5.2 — ONE CANONICAL RESOLVED PATH RESOLVED ONCE AND RECORDED PRIVATELY; PROVEN A REGULAR FILE AND NOT A SYMLINK UNDER lstat SEMANTICS AT BOTH DIGEST READINGS; DEVICE AND INODE RECORDED AND RECOMPARED WHERE AVAILABLE; THE REAL INVOCATION EXECUTES THAT EXACT RECORDED RESOLVED PATH AND IS NEVER REACHED THROUGH A SYMLINK, COPY, OR RE-RESOLVED PATH; ANY PATH REPLACEMENT, SYMLINK APPEARANCE, FILE-TYPE CHANGE, DEVICE/INODE CHANGE, OR DIGEST MISMATCH IS A STOP BEFORE ANY WRITE; PRIVATE ABSOLUTE PATHS, DEVICE NUMBERS, AND INODES STAY OUT OF THE BUNDLE AND OUT OF GIT
PRE_ADOPTION_CATALOG_SNAPSHOT:            REQUIRED AND SOURCE-BOUND — SECTION 7.2. SQLITE-NATIVE CONSISTENT BACKUP VIA THE ALREADY-ACCEPTED backup_database (storage/sqlite.py:601, origin.backup(target) AT :609), NEVER AN UNMANAGED FILE COPY, BECAUSE WRITER CONNECTIONS SET journal_mode = WAL AT :86; SAME-DEVICE, PRIVATE, MODE 0600, OUTSIDE GIT AND OUTSIDE THE REPOSITORY; CREATED AND VERIFIED UNDER THE CONTINUOUSLY HELD WRITER LEASE BEFORE ANY GOVERNED MUTATION; BINDING PROOF IS LOGICAL-STATE EQUALITY (SAME APPLIED MIGRATIONS AND user_version, SAME SAFE ROW COUNTS, SAME CANONICAL PER-TABLE CONTENT DIGESTS FOR EVERY census_* AND ops_* TABLE, SNAPSHOT quick_check/integrity_check CLEAN AND foreign_key_check EMPTY) — RAW SOURCE-FILE AND SNAPSHOT-FILE SHA-256 EQUALITY IS EXPRESSLY NOT REQUIRED AND THEIR INEQUALITY IS NEVER A FAILURE, BOTH BEING PROVENANCE ONLY; ANY MISMATCH, AMBIGUITY, OR UNAVAILABLE COMPARISON IS A STOP BEFORE ANY WRITE; FORENSIC AND COMPARATIVE ONLY; GRANTS NO ROLLBACK, AUTOMATIC RESTORE, MANUAL RESTORE, RETRY, REPLAY, OR RE-ADOPTION AUTHORITY; RESTORATION REMAINS A SEPARATE OWNER ACT
PREFLIGHT_ORDER:                          SECTION 7.1 — A READ-ONLY GATES 1-8, 10, 11; B ACQUIRE THE WRITER LEASE; C CREATE AND VERIFY THE SOURCE-BOUND SNAPSHOT UNDER IT; D FINAL LEASE-CONTINUITY RECHECK; E ARTIFACT DIGEST AND IDENTITY RE-VERIFICATION; F ENTER TRANSACTION 1. THE LEASE IS HELD UNBROKEN FROM B THROUGH F AND IS NEVER RELEASED AND REACQUIRED, SO NO UNCONTROLLED INTERVAL EXISTS IN WHICH ANOTHER WRITER COULD MUTATE THE SOURCE BETWEEN C AND F; THE FROZEN CODE MAKES THIS ENFORCEABLE — ANOTHER WRITER'S flock FAILS WITH SingleWriterViolationError AND THE ACCEPTED TEXT FIXES THAT ELAPSED TIME NEVER PERMITS TAKEOVER; THIRTEEN GATES REMAIN, NONE ADDED AND NONE REMOVED
SOLE_VERIFIER:                            _observation_from_intent — UNCHANGED
MANDATORY_SECOND_LIMB:                    rebuild_audit_projection(connection, destination) — SAME PROCESS, AFTER THE BATCH EXITS AND T1 COMMITS, OUTSIDE THE BATCH; NEITHER census_run_id NOR fault_hook SUPPLIED
OBSERVATION_ROW_SHAPE:                    OBSERVATION_COLUMNS + ObservationRecorder._row — EXACT
RECORDED_AT_UTC:                          SOLE PROCEDURE-GENERATED CATALOG VALUE AND SOLE NEW VALUE IN THE ROW — ONE utc_now() AFTER GUARDS
REBUILD_OWNED_INSTANTS:                   TWO — detected_at_utc AND resolved_at_utc; LIBRARY-GENERATED, EXPECTED, SEPARATELY EVIDENCED; NO EQUALITY REQUIRED WITH EACH OTHER OR WITH recorded_at_utc
PROJECTED_TO_AUDIT_AT_INSERT:             0 — LITERAL FROM _row; T3 MOVES IT TO 1
INSERT_ROWCOUNT_GUARD:                    cursor.rowcount == 1 — ELSE RAISE AND ROLL BACK; KEPT IN THE REAL PROCEDURE AS DEFENSE-IN-DEPTH; DIRECTLY ASSERTED AND EVIDENCED, NOT A REQUIRED NEGATIVE MUTATION
NESTED_record_CALL:                       PROHIBITED — record OPENS ITS OWN BEGIN IMMEDIATE
DUPLICATE_GUARDS:                         observation_id AND relative_storage_path — IN-TRANSACTION
REPLAY_UPDATE_OR_REPLACEMENT:             PROHIBITED — ONE-USE REFUSAL, NO UPSERT PATH
SYNTHETIC_CASES:                          16 — 1-14 PRESERVED AND NOT RENUMBERED; 15 ADDITIVE (ROW-SHAPE MUTATION LIMB PLUS ROWCOUNT ASSERTION LIMB); 16 ADDITIVE (GATE 6 REFUSAL ON A BLOCKED ROW AT A DIFFERENT projection_path — THE ONE PREFLIGHT GATE THAT PREVIOUSLY HAD NO REFUSAL CASE)
SYNTHETIC_SUITE_COUNTING:                 DISPOSABLE FIXTURES ONLY; RUNS BEFORE, OUTSIDE, AND WITHOUT ACCESS TO THE GOVERNED CATALOG OR OBJECT; NOT THE REAL INVOCATION; NOT COUNTED AGAINST IT; NOT AUTHORIZED BY THIS RECORD
PERMANENT_SURFACE:                        NONE — NO TRACKED PROCEDURE
RETRY_POLICY:                             NONE — NO LOOP, NO AUTO-RETRY, NO AUTO-RESUME
RE_ADOPTION_AFTER_COMMIT:                 PROHIBITED — READ-ONLY CLASSIFICATION ONLY
MANUAL_INCIDENT_ROW_EDIT:                 PROHIBITED
EXECUTION_AUTHORIZED_BY_THIS_RECORD:      NO — SEPARATE OWNER EXECUTION PACKET REQUIRED
INVOCATIONS_A_LATER_PACKET_MAY_AUTHORIZE: EXACTLY ONE REAL INVOCATION TOUCHING THE GOVERNED CATALOG OR OBJECT — NO SECOND
OPERATIONAL_STATE_OPENED:                 NONE — NOT EVEN READ-ONLY
ORPHAN_ADOPTION_PERFORMED:                NO
CARRY_IN_AUTHORITY:                       NOT MINTED, NOT CONSUMED
CARRY_IN_BINDS:                           LATER ACCEPTED ADOPTION DECISION + EVIDENCE MANIFEST SHA-256
CUMULATIVE_CEILING:                       801 — UNCHANGED
CONSUMPTION:                              1 / 801 — UNCHANGED
OLD_RUN_STATE:                            stopped — PERMANENTLY NON-RESUMABLE
RECOVERY_CLASSIFICATION:                  UNDETERMINED — UNCHANGED, PRE-EXECUTION
EXPECTED_TERMINAL_DETERMINATION:          UNSAFE — SOLELY FOR ABSENCE OF A PREDECESSOR RECEIPT
SAFE_DETERMINATION:                       NOT EXPECTED — NEVER AUTHORIZES RESUMPTION
TERMINATING_RECEIPT:                      NONE — NOT CREATED, NOT RECONSTRUCTED
MIGRATION:                                NONE — 0001-0013 UNCHANGED
M3_L14:                                   CLOSED — DECISION 056; UNTOUCHED
M3_L15:                                   ACTIVE — UNTOUCHED, BYTE-UNCHANGED
M3_L16:                                   ACTIVE — BLOCKS EVERY CLEAN-RUN AND LIVE AUTHORIZATION
NETWORK_AUTHORITY:                        NONE — TRACKED false / false
COMPANYFACTS:                             DISABLED AND PROHIBITED
SEC_CONTACT:                              NONE OCCURRED — NONE AUTHORIZED
TRANSPORT_CONSTRUCTION:                   NOT_AUTHORIZED
CLEAN_RUN:                                NOT_AUTHORIZED
LIVE_READINESS:                           NOT_CLAIMED
T6:                                       NOT_AUTHORIZED
M3_2B:                                    NOT_AUTHORIZED
GATE_H:                                   NOT_AUTHORIZED
REMEDIATIONS:                             FOUR — TWO PRE-PUBLICATION, TWO POST-PUBLICATION. FIRST FIXED THE ROW-CONSTRUCTION MAJOR OMISSION; SECOND FIXED TWO PROOF-LAYER MAJORS (THE FALSE "NO SECOND GENERATED INSTANT" CLAIM AND THE IMPOSSIBLE ROWCOUNT NON-VACUITY DEMAND) PLUS FOUR RELATED MINORS; THIRD FIXED THE PROOF-TO-ARTIFACT BINDING MAJOR, THE PUBLICATION-STATE MINOR, THE MISSING PRE-ADOPTION SNAPSHOT MINOR, THE MISSING GATE-6 REFUSAL CASE MINOR, AND TWO OPTIMIZATIONS; FOURTH FIXED THE COMPANION-GOVERNANCE SYNCHRONIZATION MAJOR (MAJ-A), THE SECOND PUBLICATION-CURRENCY MINOR (MIN-A), THE SNAPSHOT SOURCE-BINDING MINOR (MIN-B), AND IMPLEMENTED BOTH ORDERED OPTIMIZATIONS (OPT-A PATH IDENTITY, OPT-B STATE-5 EXCEPTION ROUTES). CENTRAL ARCHITECTURE UNCHANGED BY ALL FOUR
AUTOMATIC_CORRECTION_LOOP:                NONE PERMITTED AT ANY POINT — HONOURED AT EVERY STEP. EACH REVIEW REMEDIATED NOTHING AND REFERRED EVERY DEFECT TO THE OWNER; REMEDIATIONS 3 AND 4 EACH PROCEEDED ONLY UNDER THE OWNER'S SEPARATE RESPONDING INSTRUMENT
SECTION_16_REVIEW_OUTCOME:                TWO REVIEWS, BOTH FAIL, BOTH NOW REMEDIATED. (1) DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_FAIL — 0 BLOCKER, 1 MAJOR, 3 MINOR, 2 OPTIMIZATION. (2) DECISION_057_POST_REMEDIATION_FRESH_INDEPENDENT_REVIEW_FAIL — 0 BLOCKER, 1 MAJOR, 2 MINOR, 2 OPTIMIZATION, AGAINST PUBLISHED 103b3d39; IT CONFIRMED THE COMPLETE ARCHITECTURE CORRECT AGAINST THE FROZEN CODE WITH NO CLAIM CONTRADICTED AND EVERY CITED LINE NUMBER RESOLVING EXACTLY, AND CONFIRMED MAJ-1, MIN-3, OPT-1, AND OPT-2 RESOLVED. ALL FINDINGS OF BOTH REVIEWS LAY IN THE PROOF, EVIDENCE, PUBLICATION-CURRENCY, AND TRACEABILITY LAYERS. AWAITING A QUALIFYING FRESH NON-AUTHOR REREVIEW IN A GENUINELY NEW SESSION
RECORD_PUBLICATION:                       OCCURRED TWICE. PUBLICATION 1 — COMMIT 9475eb3d614aa70b3f2a04b061d63bd7ea51c030, TREE e0b9b12095c181ba974336399f04fc1e44eb4a11, EXACT RESERVED SUBJECT, EXACT FOUR-PATH ENVELOPE, PUSHED, NO TAG; RATIFICATION IS AN OWNER RULING, NEITHER RATIFIED NOR VOIDED BY THIS RECORD. PUBLICATION 2 — COMMIT 103b3d3910e11fee43f66d8451f101019487588e, TREE 04bd61ca09be271752d432c82f0c2f6a02eb277c, PARENT 9475eb3d, SUBJECT "Correct Decision 057 after failed independent review", EXACT FOUR-PATH ENVELOPE, PUSHED, NO TAG; OWNER-RATIFIED AS PUBLICATION FACT ONLY. BOTH PRECEDED ANY QUALIFYING PASSING REVIEW AND NEITHER CREATED ANY OPERATIONAL AUTHORITY. FACTUAL RATIFICATION IS NOT EXECUTION ACCEPTANCE
THIS_REMEDIATION_PUBLICATION:             AUTHORIZED AND PERFORMED UNDER THE BOUNDED SECOND POST-REMEDIATION CORRECTION PACKET — EXACTLY ONE COMMIT ON main OVER THE FOUR AUTHORIZED PATHS, EXACTLY ONE ORDINARY PUSH, NO TAG. IT IS NOT AN UNCOMMITTED CANDIDATE AWAITING A PUBLICATION RULING; THE RULING EXISTS AND THE ACT IS PART OF THAT INSTRUMENT. A RECORD CANNOT CONTAIN THE HASH OF THE COMMIT THAT CONTAINS IT, SO THIS CORRECTION'S OWN COMMIT IDENTITY IS ESTABLISHED BY THAT ACT AND RECORDED IN THE OWNER'S POST-PUBLICATION FREEZE RECORD — SELF-REFERENCE, NEVER A DENIAL THAT PUBLICATION OCCURRED. THAT NEW COMMIT IS THE SOLE FROZEN TARGET OF THE NEXT QUALIFYING REREVIEW
TAG:                                      NONE
M3_2:                                     NOT_COMPLETE
```

## 16. Formal outcome and exact next action

```text
FORMAL_OUTCOME: M3_2_ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE_ACCEPTED
M3_L16: ACTIVE — PROCEDURE ARCHITECTURE ACCEPTED; ADOPTION AND OWNER CLOSURE OUTSTANDING
EXECUTION_AUTHORITY: NONE
LIVE_READINESS: NOT_CLAIMED
NETWORK_OR_SEC_AUTHORITY: NONE
NEXT_AUTHORIZED_ACTION: CLAUDE_M3_2_DECISION_057_FINAL_QUALIFYING_FRESH_INDEPENDENT_REREVIEW_PACKET
```

That next action is a **fresh, independent, non-author rereview of this four-times-remediated
record** (§3), performed against the commit that publishes this correction. **Two earlier pointers
are discharged**, each by a review that was performed and returned `FAIL`:
`CLAUDE_M3_2_DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_PACKET` (findings remediated by
remediation 3) and `CLAUDE_M3_2_DECISION_057_POST_REMEDIATION_FRESH_INDEPENDENT_REVIEW_PACKET`
(findings remediated by remediation 4). Neither may be cited as the current pointer.

**The non-author requirement is binding, and it is now objectively testable rather than a matter of
self-assessment.** The previous rereview disclosed that its `Claude-Session` identifier matched the
identifier of the session that authored the remediation it was reviewing. The owner accepted that
report as valid defect-discovery and remediation evidence, but ruled that **no eventual `PASS` may
rest on that identifier**. Accordingly:

- The qualifying rereview **must run in a genuinely new Claude Code session and process** whose
  `Claude-Session` identifier **differs from `session_01TSthW3MCDzAmbMAVou376C`**.
- **A `/clear` inside a session carrying that identifier is expressly NOT sufficient.** Cleared
  context makes a session substantively fresh; it does not make it a different session, and the
  independence condition is now about session identity, not only about recollection.
- The reviewer must **disclose its own `Claude-Session` identifier if the environment exposes it**
  and **prove it differs from the disqualified identifier before beginning substantive review**. If
  the identifier is unavailable to it, it must supply whatever objective fresh-session evidence the
  environment does expose, and **owner adjudication remains required**.
- The reviewer must have **no prior authored or remediated content for Decision 057** — it may
  neither have written any part of this record nor produced either failing review.
- **Claude Opus 5, maximum effort, exactly one active session, no subagents, no parallel sessions.**
- Disclosing a session identifier is a governance-independence check only; **no credential and no
  private operational information may be exposed by it.**

That review is **read-only and non-self-executing**: it may inspect accepted repository authority and
this record, but it may **not** open or mutate the real operational catalog, raw object, lineage, or
private evidence; perform or simulate the adoption; create a checkpoint or receipt; contact the
network or SEC; publish this record; or authorize its own execution.

**What that rereview must cover.** It must verify **the entire architecture, not only this
correction** — the write contract, the three-transaction model, the fault boundaries, the one-shot
bound, and the raw/lineage preservation rule, independently re-derived. Because the owner ordered
**both** optimizations implemented, it must also confirm **OPT-A** (§5.2 path and filesystem
identity) and **OPT-B** (§9's at-least-three state-5 exception routes) are correctly implemented and
**introduce no new defect**. `PASS` still requires **BLOCKER 0, MAJOR 0, MINOR 0**.

**One question sits with the owner and not with that review:** whether publication 1
(`9475eb3d…`) is ratified. It is not settled by this record, and a passing review does not settle it.
**Two related questions are now closed and must not be reopened as though pending:** publication 2
(`103b3d39…`) **is** owner-ratified as publication **fact**, and this fourth remediation's own
publication **is** authorized and performed (§14). **Neither closure is execution acceptance**, and
no session may treat factual ratification as authority to adopt the orphan.

**Authorization is not implementation, implementation is not acceptance, and none of them discharges
M3-L16.**

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
