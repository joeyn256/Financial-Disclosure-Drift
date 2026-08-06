# Decision 041 — M3.2 T2.4 Recovery-State Primitive and Path-Envelope Amendment

**Date:** 2026-08-06
**Status:** ACCEPTED — OWNER APPROVED 2026-08-06
**Type:** Bounded governance-authorization record for one implementation-stage correction. **Not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte — **no executable byte
changes with this record**. The authorized primitive pair is implemented only later, inside the
separately issued T2.4 correction packet. It grants no correction before that packet is issued
(§4 instrument §14), no operator CLI wiring, no receipt emission, no private reconciliation-report
creation, no evidence indexing, no real operational catalog, no live SEC access, no connectivity
testing, no network or CompanyFacts enablement, no operational use of the M3.2A ceiling 801, no
T2.5–T2.6, no T3/T4/T5/Gate H/M3.3 work, no migration, no receipt-schema change, no second reason
code, no eleventh path, no push of the T2.4 implementation, no tag, and no rewrite of published
history.
**Supersedes:** nothing edited in place.
**Amends:** [Decision 040](decision_040_m3_2_t2_4_implementation_authorization.md) §11 (the
eight-path maximum T2.4 envelope) and §12 (the prohibited-path set) — **for the T2.4 correction
only**, by adding exactly two paths: `src/disclosure_drift/sec/observation_catalog.py` (released
from §12 solely for the narrow additive primitives §4 instrument §5 authorizes) and
`tests/unit/test_observation_catalog.py`. This is a narrow, stage-scoped higher-authority amendment
in the convention [Decision 038](decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md) and
Decision 040 §11 established: no accepted decision file is edited in place, the T2 authorization
packet is **preserved byte-identical**, the accepted M3.2 contract is **not edited**, and
**Decision 038 itself has no authority over T2.4**. No other previously prohibited path is
released.
**Related:** Decisions 024 §8, 034, 035, 036, 037, 038, 039, 040; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md); the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's disposition of the read-only durable-lifecycle feasibility determination,
the T2.4 path-envelope amendment to ten paths, the exact additive recovery-state primitive pair
(`open_recovery_state` and `resolve_recovery_state`), the generic `t2_4_recovery_action` state
vocabulary, the run-identity ruling, the corrected thirteen-step write-ahead sequence, the failure
semantics, the primitive test requirements, the candidate-correction and unpublished-history
ruling, and the continuing correction obligations.

---

## 1. Why this record is required

Decision 040 authorized stage T2.4 within an exact eight-path maximum envelope and expressly
prohibited `src/disclosure_drift/sec/observation_catalog.py` (§12). The independent T2.4 audit then
established that the candidate's post-mutation event-recording failure prohibition is **in-memory
only**, and a subsequent owner-authorized read-only feasibility determination established that the
durable blocked-to-resolved recovery lifecycle **cannot** be implemented inside that envelope,
because no accepted callable resolves an exact generic `census_recovery_states` row.

Under CLAUDE.md's authority rules, chat transcripts are not repository authority and
`Milestones/STATUS.md` records workflow state but never overrides a decision — only a numbered
accepted record in `Docs/Decisions/` binds a future session. This record is the durable home of the
owner's recovery-state primitive authority and path-envelope amendment, following the precedent of
Decisions 035, 036, 038, 039, and 040.

## 2. Verified baseline

Verified live immediately before this record was written, from a **disposable governance clone**
leaving the primary checkout untouched:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Published governance baseline (`origin/main`) | `df9de4b0ed1c51695728a804e9e55d4b499b77d5` ("Authorize M3.2 T2.4 implementation") — the baseline the instrument names |
| Governance-clone `HEAD` | `df9de4b0ed1c51695728a804e9e55d4b499b77d5`; clean; nothing staged; no non-ignored untracked path |
| Local unaccepted T2.4 candidate | `5cba2863f47df09c83564258be897a4fd71cf6be` (tree `e3c47528e6059c7b8e10369846934c56e3b8eabe`), subject `Implement M3.2 T2.4 recovery and reconciliation` |
| Candidate state | **local, unaccepted, unpushed, untagged**; primary checkout ahead 1, behind 0, clean |
| Tags | `m3.1-complete` unchanged; **no tag at the candidate**; no tag created by any T2 stage |
| Decision 040 governance commit | `df9de4b0ed1c51695728a804e9e55d4b499b77d5` |
| Accepted contract (unchanged) | SHA-256 `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7` |
| Historical T2 packet (byte-identical) | SHA-256 `621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599` |
| Migration chain | contiguous through `0013`; no migration proposed or authorized here |
| Network switches | `network.enabled: false`; `network.m3_acquire_enabled: false` |
| M3.2 state | T2.1 and combined T2.2–T2.3 accepted and published; **T2.4 implemented as an unaccepted local candidate requiring correction**; combined T2.5–T2.6 not begun; no real operational catalog, receipt, evidence artifact, or live SEC activity; ceiling 801 unused |
| Decision numbering | directory and registry both ended at Decision 040 and agree; **041** verified genuinely unused in both |

## 3. The feasibility determination this decision disposes

The read-only durable-lifecycle feasibility determination ran on 2026-08-06 under the owner's
explicit authorization, against exactly this baseline, in one fresh session with no subagents and no
workflow invocation, and returned:

```text
M3_2_T2_4_DURABLE_RECOVERY_LIFECYCLE_NOT_FEASIBLE_WITHIN_CURRENT_AUTHORITY
```

It established, through schema inspection, exhaustive source search, and executed disposable probes,
that:

- `census_recovery_states.scenario` is **unconstrained** and `(census_run_id, recovery_state_id)` is
  already a **primary key**, so the schema supports the lifecycle today;
- generic **block creation** is reachable through the accepted `record_recovery_events`, but only by
  also writing a `census_recovery_events` row asserting an event that has not occurred, and only
  under one of that table's eight CHECK-constrained scenarios;
- **no accepted callable resolves an exact generic `census_recovery_states` row** — the sole
  `resolution_state = 'resolved'` statement in the package is embedded in `rebuild_audit_projection`,
  hard-filtered to `audit_projection_interrupted`, bulk rather than primary-key exact, performing a
  projection rebuild and other unrelated mutations, and resolving **during** the mutation and
  therefore **before** recovery-event recording;
- three of the four authorized T2.4 recovery actions have **no resolver at all**;
- the enforced foreign key from `census_recovery_states.census_run_id` to
  `ops_ingestion_jobs(job_id)` means a lawful run identity can only be **required**, never minted,
  derived, or substituted;
- the generic **readback** path is already correct: `_unresolved_recovery_states` is
  scenario-agnostic and drives the accepted inspector's condition 8.9 to `UNSAFE` in a fresh
  process.

**The determination authorized nothing**; the owner's instrument below is the sole authorization, and
where the two could ever be read to differ, the instrument controls.

## 4. The owner instrument (verbatim, received 2026-08-06)

```text
OWNER_DECISION_041_M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY: APPROVED

Decision title:

M3.2 T2.4 Recovery-State Primitive and Path-Envelope Amendment

Date:

2026-08-06

1. Authority baseline

This decision is controlled by:

* accepted Decision 040;
* the M3.2 contract;
* the historical T2 implementation-authorization packet;
* the independent T2.4 audit verdict requiring corrections;
* the accepted read-only durable-lifecycle feasibility determination.

Published governance baseline:

df9de4b0ed1c51695728a804e9e55d4b499b77d5

Local unaccepted T2.4 candidate:

5cba2863f47df09c83564258be897a4fd71cf6be

Candidate tree:

e3c47528e6059c7b8e10369846934c56e3b8eabe

The candidate remains local, unaccepted, unpushed, and untagged.

2. Feasibility disposition

The owner accepts:

M3_2_T2_4_DURABLE_RECOVERY_LIFECYCLE_NOT_FEASIBLE_WITHIN_CURRENT_AUTHORITY

The current authority is insufficient because:

* no accepted callable resolves an exact generic
    census_recovery_states row;
* the sole existing resolver is embedded in
    rebuild_audit_projection;
* that resolver is hard-filtered to
    audit_projection_interrupted;
* it resolves every blocked projection state for a run rather than one exact
    primary-key identity;
* it performs a projection rebuild and other unrelated mutations;
* it resolves during the mutation, before recovery-event recording;
* three of the four T2.4 recovery actions have no resolver at all.

The schema is sufficient. The missing capability is an accepted exact primitive.

3. Model and source-availability disposition

The feasibility session's use of Claude Opus 5 rather than Claude Fable 5 is
accepted as non-material.

The independent-audit report's absence from that session is also nonblocking.
The session independently reproduced the central durability defect and
established the callable-surface gap through schema inspection, complete source
search, and executed probes.

4. Path-envelope amendment

Decision 040 §11 is amended for the T2.4 correction only.

The maximum corrected T2.4 envelope becomes exactly ten tracked paths.

Existing production paths

1. src/disclosure_drift/m3/acquisition.py
2. src/disclosure_drift/m3/recovery.py
3. src/disclosure_drift/m3/__init__.py
4. src/disclosure_drift/reasons.py

Newly added production authority

5. src/disclosure_drift/sec/observation_catalog.py

Existing test paths

6. tests/unit/test_m3_acquisition.py
7. tests/unit/test_m3_recover.py
8. tests/unit/test_m3_recovery.py
9. tests/unit/test_reasons.py

Newly added test authority

10. tests/unit/test_observation_catalog.py

Decision 040 §12 is amended only to remove
src/disclosure_drift/sec/observation_catalog.py from the prohibited set for
the narrow additions authorized below.

No other previously prohibited path is released.

The ten paths are a maximum, not a requirement to edit every path.

5. Exact accepted-primitive extension

The owner authorizes additive, public recovery-state primitives in:

src/disclosure_drift/sec/observation_catalog.py

Existing public and private functions must retain their accepted semantics.

No existing resolver, reconciliation function, recorder, schema, or projection
behavior may be rewritten to simulate the new authority.

5.1 Open primitive

Add a public function equivalent to:

def open_recovery_state(
    writer: CatalogWriter,
    *,
    census_run_id: str,
    recovery_state_id: str,
    scenario: str,
    action_taken: str,
    detail: str,
    observation_id: str | None = None,
    relative_path: str | None = None,
) -> None:
    ...

Required behavior:

* require nonempty census_run_id;
* require nonempty recovery_state_id;
* require nonempty scenario, action_taken, and detail;
* verify that census_run_id identifies an existing
    ops_ingestion_jobs.job_id;
* insert exactly one row into census_recovery_states;
* set resolution_state = 'blocked';
* address the row by the full primary key:
    (census_run_id, recovery_state_id);
* commit through the accepted transaction and writer-lease conventions;
* raise on a missing run, duplicate state identity, constraint failure, or
    failed write;
* write nothing to census_recovery_events;
* write nothing to census_projection_recovery_events;
* mutate no observation, object, projection, receipt, or other recovery state.

There is no silent skip when a run ID is absent.

5.2 Exact resolution primitive

Add a public function equivalent to:

def resolve_recovery_state(
    writer: CatalogWriter,
    *,
    census_run_id: str,
    recovery_state_id: str,
    action_taken: str,
    detail: str,
) -> bool:
    ...

Required behavior:

* require nonempty inputs;
* update only the exact row addressed by:
    (census_run_id, recovery_state_id);
* require its current state to be blocked;
* set resolution_state = 'resolved';
* record the supplied completed action and sanitized completion detail;
* perform no scenario filtering;
* perform no projection rebuild;
* perform no repair;
* update no sibling state;
* write no recovery-event row;
* return success only when exactly one blocked row was resolved;
* treat zero affected rows as failure;
* rely on the primary key to make more than one affected row structurally
    impossible;
* commit through accepted transaction and writer-lease conventions.

The function must not bulk-resolve by run or scenario.

6. Recovery-state vocabulary

The T2.4 applier shall use the exact generic state scenario:

t2_4_recovery_action

This scenario is stored only in census_recovery_states, whose schema does not
constrain scenario vocabulary.

It must not be inserted into census_recovery_events, whose scenario vocabulary
is separately constrained.

The blocked row's action_taken records the explicitly requested recovery
action.

The resolved row's action_taken records the completed action result.

All details must use the project's accepted sanitization and private-path
exclusion rules.

7. Run-identity ruling

Every mutating T2.4 recovery action requires a caller-supplied, already
registered:

ops_ingestion_jobs.job_id

This value becomes census_run_id.

The applier must refuse before mutation when:

* no run ID is supplied;
* the run ID is empty;
* the run ID does not resolve;
* the referenced ingestion job is not a lawful existing governed run;
* a blocked T2.4 recovery state already exists for that run.

T2.4 may not:

* create an ingestion-job row;
* invoke the private census-orchestrator job creator;
* fabricate a job identity;
* substitute a receipt ID;
* create a new recovery-run identity model;
* create a real operational run during tests or implementation.

Tests may create lawful temporary catalog fixtures containing an
ops_ingestion_jobs row.

The recovery-state identity is an opaque unique ID created before the open
primitive is called and returned in the action result. UUID generation is
permitted for this internal durable row identity. It is not a plan, evidence,
receipt, request, or authorization identity.

8. Corrected write-ahead sequence

For every authorized mutating recovery action:

1. Recompute and validate the exact required action and target.
2. Validate the existing caller-supplied census_run_id.
3. Refuse if any unresolved T2.4 recovery state already exists for that run.
4. Create one unique recovery_state_id.
5. Call open_recovery_state.
6. Commit the block before mutation.
7. Verify through a fresh read-only catalog connection that the exact row is
    blocked.
8. Perform exactly one authorized mutation.
9. Record the actual completed recovery event through
    record_recovery_events.
10. For this actual event-recording call, use census_run_id=None so the
    accepted function writes only the actual census_recovery_events row and
    does not create a second recovery-state row.
11. Only after event recording succeeds, call resolve_recovery_state.
12. Verify through a fresh connection that the exact state is resolved.
13. Require a fresh read-only recovery inspection before continuation.

Opening the block is not itself a recovery event.

9. Failure semantics

Required outcomes:

* run validation failure: refuse before mutation;
* open failure: refuse before mutation;
* fresh blocked-state verification failure: refuse before mutation;
* mutation failure: leave the exact state blocked;
* recovery-event recording failure: leave the exact state blocked;
* resolution failure: leave the exact state blocked;
* unresolved block after restart: fresh inspection reports blocking state and
    continuation is prohibited;
* a second action while a block remains unresolved: refuse before mutation.

If exact resolution commits but the current invocation cannot complete its
fresh readback, that invocation remains UNDETERMINED and must not authorize
continuation. A later process must recompute from durable catalog state.

No in-memory flag may be the only continuation prohibition.

10. Primitive tests

tests/unit/test_observation_catalog.py may be edited only to prove the new
primitive pair.

Required tests include:

* valid blocked-state insertion;
* no event-row insertion by the open primitive;
* missing run ID refusal;
* nonexistent run ID refusal;
* duplicate state-ID refusal;
* exact full-primary-key addressing;
* exact single-row resolution;
* sibling blocked state preserved;
* scenario-agnostic resolution;
* zero-row resolution failure;
* no projection mutation;
* no observation mutation;
* no unrelated table mutation;
* transaction rollback on failure;
* fresh-connection visibility.

Existing observation-catalog tests and accepted behavior must remain
load-bearing.

11. Migration, receipt, and reason dispositions

Unchanged:

NO_NEW_MIGRATION_REQUIRED

The chain remains:

0001–0013

Unchanged:

NO_RECEIPT_SCHEMA_CHANGE_REQUIRED

The receipt remains:

m3-execution-receipt/2.0

Unchanged:

* exactly one T2.4 reason-code addition;
* no second reason code;
* no alias;
* no route or source-authority change;
* no configuration change.

12. Candidate correction and history ruling

The current candidate is unpublished and may not be pushed.

Decision 041 must first be recorded and published from a disposable governance
clone without changing the primary checkout.

After Decision 041 publication, a separate correction packet may authorize the
primary checkout to:

1. fetch the new published governance baseline;
2. verify the primary candidate is still exactly 5cba2863…;
3. preserve the candidate's code delta in the index and working tree;
4. move local main to the new published Decision 041 baseline through one
    controlled soft reset;
5. apply the authorized corrections;
6. create exactly one corrected T2.4 implementation commit with subject:
    Implement M3.2 T2.4 recovery and reconciliation

The old unaccepted SHA must not be preserved by a branch or tag.

The corrected implementation remains local until a fresh independent rereview
passes and the owner separately accepts publication.

This narrow reconstruction of unpublished history does not authorize changing
published history.

13. Continuing correction obligations

The correction must still resolve all sustained independent-audit findings,
including:

* durable post-mutation fail-closed behavior;
* exact durable in-flight identity or UNDETERMINED classification;
* preservation of the multiple-possible-in-flight basis;
* exhaustive continuation-state partitioning;
* blocking of hash mismatch and invalid archive lineage;
* stray-lineage adoption coverage;
* symlink-sweep alignment;
* refusal-reason coverage;
* snapshot-counter documentation.

Mutation 02 remains accepted as a proven no-op.

14. Negative authority

This decision does not authorize:

* correction before Decision 041 is durably published;
* a migration;
* receipt changes;
* another reason code;
* an eleventh path;
* direct recovery-state SQL from m3/acquisition.py;
* use of private catalog helpers;
* reuse of the projection-specific bulk resolver;
* operational-run creation;
* CLI wiring;
* an operational catalog;
* network or CompanyFacts enablement;
* SEC contact;
* a push of the T2.4 implementation;
* a tag;
* T2.5–T2.6;
* T3, T4, T5, Gate H, or M3.3 work;
* repository-efficiency or review-infrastructure work.

15. Governance recording

Decision 041 shall be recorded at:

Docs/Decisions/decision_041_m3_2_t2_4_recovery_state_primitive_authority.md

Update only:

* Docs/Decisions/decision_registry.md
* Milestones/STATUS.md

Exact governance commit subject:

Authorize M3.2 T2.4 recovery-state primitives

No executable byte changes in the governance commit.

No tag.

16. Next authorized action

After Decision 041 is durably recorded and published, set exactly:

NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_REISSUANCE_OF_M3_2_T2_4_CORRECTION_PACKET_AFTER_DECISION_041_PUBLICATION

No correction begins until that separate packet is issued.

Owner:
Joseph Nihill, acting through the ChatGPT project-owner role

Date:
2026-08-06

This is a transparent recorded owner decision, not a handwritten,
cryptographic, or third-party digital signature.
```

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.

## 5. What this decision fixes

The §4 instrument controls; this summary neither broadens nor narrows it.

1. **Feasibility disposition.** The owner accepts
   `M3_2_T2_4_DURABLE_RECOVERY_LIFECYCLE_NOT_FEASIBLE_WITHIN_CURRENT_AUTHORITY` on the seven grounds
   the instrument §2 enumerates. **The schema is sufficient; the missing capability is an accepted
   exact primitive.** The feasibility session's use of Claude Opus 5 rather than Claude Fable 5, and
   the independent-audit report's absence from that session, are both accepted as non-material and
   nonblocking (instrument §3).
2. **Path envelope.** The maximum corrected T2.4 envelope becomes **exactly ten tracked paths**
   (instrument §4). Decision 040 §11's eight paths stand, and exactly two are added:
   `src/disclosure_drift/sec/observation_catalog.py` and
   `tests/unit/test_observation_catalog.py`. Decision 040 §12 is amended **only** to release
   `observation_catalog.py` for the narrow additions instrument §5 authorizes; **no other previously
   prohibited path is released**, and the ten paths are a **maximum**, not a requirement to edit
   every path. An eleventh path is an immediate stop.
3. **Primitive pair.** Two **additive, public** recovery-state primitives are authorized in
   `observation_catalog.py` — `open_recovery_state` (instrument §5.1) and `resolve_recovery_state`
   (instrument §5.2) — with their exact required behaviors. **Existing public and private functions
   must retain their accepted semantics**, and no existing resolver, reconciliation function,
   recorder, schema, or projection behavior may be rewritten to simulate the new authority. The
   resolution primitive is primary-key exact, scenario-agnostic, performs no repair or projection
   rebuild, updates no sibling state, writes no event row, and **must not bulk-resolve by run or
   scenario**.
4. **Vocabulary and identity.** The applier uses the generic state scenario `t2_4_recovery_action`,
   stored **only** in `census_recovery_states` and never inserted into the CHECK-constrained
   `census_recovery_events` (instrument §6). Every mutating recovery action requires a
   **caller-supplied, already registered `ops_ingestion_jobs.job_id`**, with five enumerated
   pre-mutation refusal conditions and six express prohibitions on minting, fabricating, or
   substituting a run identity (instrument §7). The recovery-state identity is an opaque unique ID;
   UUID generation is permitted for it and it is **not** a plan, evidence, receipt, request, or
   authorization identity.
5. **Corrected sequence and failure semantics.** The thirteen-step write-ahead sequence (instrument
   §8) fixes that the block is committed and fresh-connection verified **before** mutation, that the
   actual event is recorded with `census_run_id=None` so no second recovery-state row is created,
   and that exact resolution happens **only after** event recording succeeds. **Opening the block is
   not itself a recovery event.** Eight failure outcomes are fixed (instrument §9); a committed
   resolution whose readback cannot complete leaves that invocation `UNDETERMINED`; and **no
   in-memory flag may be the only continuation prohibition**.
6. **Tests and dispositions.** Fifteen required primitive tests are fixed and
   `tests/unit/test_observation_catalog.py` may be edited **only** to prove the new pair, with
   existing tests and accepted behavior remaining load-bearing (instrument §10).
   `NO_NEW_MIGRATION_REQUIRED` (chain exactly `0001`–`0013`), `NO_RECEIPT_SCHEMA_CHANGE_REQUIRED`
   (`m3-execution-receipt/2.0` frozen), exactly one T2.4 reason-code addition, no alias, no route or
   source-authority change, and no configuration change all stand unchanged (instrument §11).
7. **Candidate and history.** The candidate is unpublished and **may not be pushed**. This record is
   recorded and published from a **disposable governance clone without changing the primary
   checkout**. A separate later correction packet may authorize the primary checkout to fetch the
   new baseline, verify the candidate is still exactly `5cba2863…`, preserve its code delta, move
   local `main` to the published Decision 041 baseline through **one controlled soft reset**, apply
   the corrections, and create **exactly one** corrected implementation commit with the subject
   `Implement M3.2 T2.4 recovery and reconciliation`. **The old unaccepted SHA must not be preserved
   by a branch or tag**, the corrected implementation remains local until a fresh independent
   rereview passes and the owner separately accepts publication, and **this narrow reconstruction of
   unpublished history does not authorize changing published history** (instrument §12).
8. **Continuing correction obligations.** Nine sustained independent-audit findings must still be
   resolved by the correction (instrument §13). **Mutation 02 remains accepted as a proven no-op.**

## 6. Authority hierarchy and supersession

- **This record is higher authority** than Decision 040 §11's eight-path maximum and §12's
  prohibited-path set — **for the T2.4 correction only, and only as to the two added paths and the
  narrow additive primitives §4 fixes.** Every other provision of Decisions 035, 036, 037, 038, 039,
  and 040 remains in force verbatim, including the envelope's character as a **ceiling and not a
  grant**, the immediate-stop rule for any out-of-envelope need, the four-stage cadence, the
  no-stage-tag and no-T3-tag rules, the one-commit rule and its exact subject, the §16 validation
  rule, the §17 stop conditions, the §19 continuing obligations, and every declined and prohibited
  surface.
- **Decision 038 has no authority over T2.4** (its own §9, Decision 040, and this record agree). That
  Decision 038 previously authorized `observation_catalog.py` for the combined T2.2–T2.3 stage is
  **not** the source of this record's authority; the path is released here afresh, on this record's
  own terms, and bounded to the additive primitives alone.
- **No accepted decision is edited in place.** Decisions 032–040 are byte-unchanged. The T2
  authorization packet is preserved byte-identical (SHA-256 `62120146…`) and must not be silently
  rewritten; the accepted contract is not edited and retains SHA-256 `c526335b…`.
- Where this record and an accepted record could ever be read to disagree, the accepted record
  controls and this record is corrected under a new owner instrument.

## 7. Negative authority

Instrument §14 applies in full and is not restated. In particular: no correction before this record
is durably published; no migration; no receipt change; no second reason code; no eleventh path; no
direct recovery-state SQL from `m3/acquisition.py`; no use of private catalog helpers; no reuse of
the projection-specific bulk resolver; no operational-run creation; no CLI wiring; no operational
catalog; no network or CompanyFacts enablement; no SEC contact; no push of the T2.4 implementation;
no tag; no T2.5–T2.6, T3, T4, T5, Gate H, or M3.3 work; and no repository-efficiency or
review-infrastructure work.

## 8. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_041_m3_2_t2_4_recovery_state_primitive_authority.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 041 row and quick-lookup entry;
- `Milestones/STATUS.md` — current-state, blocker, authority-state, and next-action updates, with
  the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_REISSUANCE_OF_M3_2_T2_4_CORRECTION_PACKET_AFTER_DECISION_041_PUBLICATION`;
- **one** governance-only commit with the subject `Authorize M3.2 T2.4 recovery-state primitives`,
  and **one** normal fast-forward push of `main`, both performed from a **disposable governance
  clone** that leaves the primary checkout byte-unchanged. **No tag.**

`Docs/decision_index.md` is deliberately **not** edited — the established navigation ruling stands
and the decision registry remains the discovery route. No implementation, test, script, migration,
template, packet, contract, review-artifact, configuration, or private-evidence byte changes.

## 9. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner instrument is recorded verbatim and neither broadened
nor reinterpreted; (2) `src`, `tests`, `configs`, migrations, the receipt module, the reason
registry, the contract, and the T2 packet are byte-identical, with the contract and packet SHA-256
values unchanged; (3) Decision 041 is unique — no other decision file or registry row carries the
number, and directory and registry agree; (4) the registry and status ledger match this record
exactly, with the next-action marker line occurring exactly once and carrying no suffix;
(5) `git diff --check` and `git diff --cached --check` pass over the updated tree; (6) the commit
carries exactly the three §8 paths; (7) no tag is created; (8) no private path, SEC identity, or
private-evidence content appears in any changed file; (9) `Docs/decision_index.md` is unchanged;
(10) the primary checkout is proven byte-unchanged, still at candidate `5cba2863…` (tree
`e3c47528…`), clean, ahead one, behind zero, with no tag.

## 10. Formal outcome

```text
M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY_RECORDED
```

**Next authorized action:**
`CHATGPT_OWNER_REISSUANCE_OF_M3_2_T2_4_CORRECTION_PACKET_AFTER_DECISION_041_PUBLICATION` — the
ChatGPT owner reissues the exact T2.4 correction packet. **No correction session may begin before it
is issued**; the candidate remains local, unaccepted, unpushed, and untagged, and network
enablement, live SEC access, acquisition, real operational-catalog creation, and ceiling-801 use all
remain unauthorized.
