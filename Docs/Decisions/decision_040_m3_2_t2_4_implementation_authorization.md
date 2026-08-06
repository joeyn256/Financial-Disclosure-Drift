# Decision 040 — M3.2 T2.4 Implementation Authorization

**Date:** 2026-08-06
**Status:** ACCEPTED — OWNER APPROVED 2026-08-06
**Type:** Bounded governance-authorization record for one implementation stage. **Not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte — **no executable byte
changes with this record**. The one approved reason-code registry delta is **implemented only
later, inside the authorized T2.4 implementation stage**, never by this recording. It grants no
implementation before the separate exact T2.4 implementation packet is issued (§4 instrument §18),
no operator CLI wiring, no receipt emission, no private reconciliation-report creation, no
evidence indexing, no real operational catalog, no live SEC access, no connectivity testing, no
network or CompanyFacts enablement, no operational use of the M3.2A ceiling 801, no T2.5–T2.6, no
T3/T4/T5/Gate H/M3.3 work, no migration, no receipt-schema change, no second reason code, no
further path, no tag, and no history rewrite.
**Supersedes:** nothing edited in place.
**Amends:** [Decision 035](decision_035_m3_2_t2_staged_implementation_authorization.md) §6 (the
fifteen-path maximum T2 envelope) and the corresponding fifteen-path maximum recorded in
[`Docs/m3/m3_2_t2_implementation_authorization_packet.md`](../m3/m3_2_t2_implementation_authorization_packet.md)
§5 — **for stage T2.4 only, and only by expressly adding `tests/unit/test_reasons.py`** for the
one-code registry delta, its exact closed-set count adjustment, and its metadata and registration
assertions. This is a narrow, stage-scoped higher-authority amendment in the convention accepted
[Decision 038](decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md) established: no accepted
decision file is edited in place, the T2 authorization packet is **preserved byte-identical**, the
accepted M3.2 contract is **not edited**, and **Decision 038 itself has no authority over T2.4**.
**Related:** Decisions 024 §8, 034, 035, 036, 037, 038, 039; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md); the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's implementation authorization for Milestone 3.2 stage T2.4 — Recovery,
Reconciliation, Resume Boundaries, and Drift Control — its four internal subphases, the
`SOURCE_REQUIRED_OBJECT_UNAVAILABLE` reason-code approval, the migration, receipt,
accounting-vocabulary, attempt-accounting, and F4 dispositions, the exact eight-path maximum
implementation envelope, the commit, review, validation, and stop rules, and the continuing
obligations.

---

## 1. Why this record is required

Decision 037 §6 fixed that each remaining Milestone 3.2 stage requires its own owner act after the
prior stage is reviewed, accepted, and published, and Decision 039 set the next-action marker
`CHATGPT_OWNER_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION_AFTER_T2_2_T2_3_PUBLICATION`. The owner has
now issued that act (§4, verbatim). Under CLAUDE.md's authority rules, chat transcripts are not
repository authority and `Milestones/STATUS.md` records workflow state but never overrides a
decision — only a numbered accepted record in `Docs/Decisions/` binds a future session. This
record is the durable home of the owner's T2.4 implementation authorization, following the
precedent of Decisions 035 (staged T2 authorization), 036 (T2.1 completion), and 039 (T2.2–T2.3
acceptance).

The instrument was preceded by an owner-authorized, read-only T2.4 architecture and
implementation-packet discovery (2026-08-06, this baseline), whose outcome
`M3_2_T2_4_IMPLEMENTATION_PACKET_DISCOVERY_COMPLETE` the instrument's §1 accepts. The discovery
changed no repository byte and committed no artifact; its findings bind only as the instrument
adopts them.

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| `HEAD` == `origin/main` | `01937321263659ad347677865ee5d2cd82c56d27` ("Accept M3.2 T2.2-T2.3 implementation") — the published authority baseline the instrument names |
| `HEAD` tree | `458d2fab630d3d20a7cefe9a12600e6d789c13a5` |
| Ahead / behind | 0 / 0; no divergence |
| Working tree | clean; nothing staged; no non-ignored untracked path; `.env` ignored and never read |
| Tags | `m3.1-complete` unchanged; **no tag at HEAD**; no tag created by any T2 stage |
| Accepted T2.2–T2.3 implementation | `6b189df1651ec3674ec7f96a1f5d66f488c654a9` (tree `8850e1e45e9471bbb8b94612da67715e932a496f`), accepted and published under Decision 039 |
| Decision 038 governance commit | `27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba` |
| Decision 039 governance commit | `01937321263659ad347677865ee5d2cd82c56d27` |
| Accepted contract (unchanged) | SHA-256 `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7` |
| Historical T2 packet (byte-identical) | SHA-256 `621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599` |
| Migration chain | contiguous through `0013`; no migration proposed or authorized here |
| Network switches | `network.enabled: false`; `network.m3_acquire_enabled: false` |
| M3.2 state | T2.1 and combined T2.2–T2.3 accepted and published; **T2.4 and combined T2.5–T2.6 not begun**; no real operational catalog, receipt, evidence artifact, or live SEC activity; ceiling 801 unused |
| Decision numbering | directory and registry both ended at Decision 039 and agree; **040** verified genuinely unused in both |

## 3. The discovery this decision disposes

The read-only T2.4 discovery ran on 2026-08-06 under the owner's explicit discovery authorization
(`OWNER_M3_2_T2_4_IMPLEMENTATION_PACKET_DISCOVERY_AUTHORIZATION: APPROVED`), against exactly this
baseline, in one session with no subagents, and returned
`M3_2_T2_4_IMPLEMENTATION_PACKET_DISCOVERY_COMPLETE` with zero BLOCKER and zero MAJOR findings.
It mapped the existing recovery, reconciliation, conditional-request, 304, attempt-accounting,
and repair primitives; resolved the singleton bootstrap-absence reason question to an exact owner
choice; determined `NO_NEW_MIGRATION_REQUIRED` and `NO_RECEIPT_SCHEMA_CHANGE_REQUIRED`; and
proposed the exact maximum eight-path envelope. **The discovery authorized nothing**; the owner's
instrument below is the sole authorization, and where the two could ever be read to differ, the
instrument controls.

## 4. The owner instrument (verbatim, received 2026-08-06)

```text
OWNER_DECISION_040_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION: APPROVED

The project owner authorizes implementation of Milestone 3.2 stage T2.4:

RECOVERY, RECONCILIATION, RESUME BOUNDARIES, AND DRIFT CONTROL

Published authority baseline:

01937321263659ad347677865ee5d2cd82c56d27

Published baseline tree:

458d2fab630d3d20a7cefe9a12600e6d789c13a5

Accepted T2.2–T2.3 implementation:

6b189df1651ec3674ec7f96a1f5d66f488c654a9

Decision 038:

27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba

Decision 039:

01937321263659ad347677865ee5d2cd82c56d27

Contract SHA-256:

c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7

Historical T2 authorization-packet SHA-256:

621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599

1. Discovery disposition

The owner accepts the read-only T2.4 architecture and implementation-packet
discovery outcome:

M3_2_T2_4_IMPLEMENTATION_PACKET_DISCOVERY_COMPLETE

The discovery established:

* the existing catalog, snapshot, archive, immutable-storage, conditional HTTP,
    request-ceiling, receipt, and recovery primitives are sufficient;
* catalog-authoritative continuation composition is absent and belongs in T2.4;
* deterministic plan-to-catalog reconciliation and drift reporting are absent
    and belong in T2.4;
* continuation binding, conditional-validator supply, conservative interruption
    accounting, and exact remaining-work derivation are absent and belong in
    T2.4;
* an explicit, deterministic repair-applier library boundary is absent and
    belongs in T2.4;
* one new reason code is required;
* no migration is required;
* no receipt-schema change is required;
* an exact maximum eight-path implementation envelope is sufficient.

2. Authorized internal subphases

T2.4 is authorized as one coherent implementation stage with four internal
subphases.

T2.4-A — Catalog-authoritative reconstruction

Implement composition that:

* opens the accepted operational catalog;
* loads durable observations in deterministic order;
* constructs a fresh SnapshotStore;
* adopts catalog observations into that fresh store;
* discards all predecessor-process mutable in-memory snapshot state;
* excludes quarantined, failed, absent, missing, unverifiable, or otherwise
    unusable observations from reuse;
* preserves lawful predecessor, supersession, duplicate, validator, and
    archive-lineage identities;
* re-verifies immutable evidence at the point of reuse.

The catalog remains the durable source of truth.

T2.4-B — Reconciliation and drift inspection

Implement deterministic, read-only reconciliation over:

* approved plan;
* catalog observations and reasons;
* immutable objects;
* archive-member lineage;
* attempt accounting;
* predecessor chains;
* staging and raw partials;
* orphans and missing referents;
* request and route identities;
* completion state;
* registered drift reasons.

The output must enumerate item-level state in deterministic plan order and must
distinguish at least:

* satisfied new;
* byte-identical duplicate;
* conditional not-modified reuse;
* already-satisfied and excluded from continuation;
* changed-content supersession;
* absent;
* quarantined;
* failed;
* stopped;
* not attempted;
* partial;
* orphaned;
* row without object;
* object without row;
* missing or invalid archive lineage;
* drift-blocking;
* drift-observed but nonblocking.

Inspection and reporting must mutate nothing.

T2.4-C — Continuation proposal and conditional reuse

Implement a deterministic, read-only continuation proposal bound to:

* predecessor receipt-chain identity;
* exact plan hash;
* exact acquisition window;
* exact approved ceiling;
* exact catalog and object state;
* cumulative attempt evidence.

The proposal must:

* carry cumulative consumption without reset;
* refuse consumed attempts beyond the approved ceiling;
* conservatively charge an identifiable receiptless in-flight request at the
    full registered A_reachable;
* classify uncertain attempt attribution as UNDETERMINED;
* prohibit continuation from UNDETERMINED;
* derive exact remaining headroom;
* derive exact satisfied and remaining logical requests;
* exclude verified satisfied requests from replay;
* provide ETag and Last-Modified only from a lawful verified predecessor;
* permit a 304 to satisfy only through accepted immutable-evidence and lineage
    verification;
* fail an unreconciled 304 closed with
    SOURCE_SNAPSHOT_REUSE_UNRECONCILED;
* preserve byte-identical 200 responses as duplicate reconciliation;
* preserve changed 200 responses as new immutable superseding observations;
* refuse continuation when the worst-case remaining attempt bound does not fit.

T2.4 creates a continuation proposal only.

Continuation authorization remains an explicit later owner act.

Continuation execution and m3 acquire --resume-from wiring remain deferred.

T2.4-D — Explicit recovery-action library boundary

Implement an inert library-level recovery applier supporting only these
deterministic action classes:

1. adopt one cryptographically proven orphan through the accepted authoritative
    reconciliation path;
2. quarantine one identified partial raw object through the accepted
    move-and-preserve path;
3. remove one identified stale staging .part spool proven never promoted,
    never catalogued, and never referenced;
4. rebuild the derived audit projection through the accepted projection
    rebuild primitive.

The applier must:

* never run automatically;
* require an explicit requested action;
* recompute and verify the currently required action immediately before acting;
* refuse an action that differs from the deterministic recommendation;
* refuse every action from UNDETERMINED state;
* refuse stale, mismatched, already-resolved, or multi-action requests;
* mutate no acquired object through deletion or overwrite;
* record the recovery event through the accepted recovery-event surface;
* require a fresh read-only inspection after mutation;
* treat a mutation followed by failed event recording as UNDETERMINED and
    prohibit further continuation;
* perform no automatic retry, resume, repair cascade, or second action.

If the existing accepted reconciliation primitive cannot scope an orphan
adoption to the exact authorized event without performing unrelated mutations,
implementation must stop for owner adjudication.

No CLI exposes this applier during T2.4.

3. Recovery-state classification

The accepted inspector remains unchanged and read-only.

T2.4 shall preserve:

* SAFE for fully reconciled, known, continuation-compatible state;
* UNSAFE for known fail-closed defects or required repairs;
* UNDETERMINED where durable persistence or attempt attribution cannot be
    established.

T2.4 may classify uncertain cumulative-attempt evidence as UNDETERMINED without
changing the accepted inspector’s existing conditions.

Every UNDETERMINED result:

* prohibits continuation;
* prohibits repair execution;
* requires owner referral;
* may not be reclassified optimistically.

4. Required singleton-object reason code

The owner approves exactly one new registered reason code.

Code:

SOURCE_REQUIRED_OBJECT_UNAVAILABLE

Category:

integrity

Description:

A required source object was not retrieved or not usably obtained at its registered identity, so the window cannot confirm the required object present.

Metadata:

* blocks_release: true
* requires_manual_review: true
* decision reference:
    Docs/Decisions/decision_040_m3_2_t2_4_implementation_authorization.md

Authorized T2.4 mapping:

Attach this code to a required, non-quarterly-index M3.2A logical request when
its committed observation is terminally:

* failed; or
* quarantined.

The code may coexist with a more specific accepted defect code such as:

* SEC_RESPONSE_MALFORMED;
* RAW_ARCHIVE_INVALID;
* RAW_ARCHIVE_MEMBER_REFUSED.

The code means that the required object remains unavailable; it does not replace
the more specific cause.

Exclusions:

* quarterly index instances retain
    INDEX_INSTANCE_UNAVAILABLE and related accepted index codes;
* stopped, interrupted, ceiling-exhausted, and not-attempted requests retain
    their run or request classifications and do not receive this code merely for
    lacking an object;
* recent-target 404 semantics remain unchanged;
* no existing reason is redefined or aliased;
* no second new reason code is authorized;
* no M3.2B acquisition or mapping is authorized by this decision.

A later approved stage may use the code for the same semantics only under its
own path and behavior authority.

5. Durable reconciliation source

For T2.4, required-object and absence reconciliation shall read accepted durable
state from:

* census_source_observations;
* census_observation_reasons;
* census_archive_members;
* accepted recovery-state and recovery-event tables where applicable;
* the governed immutable-object and staging trees.

The earlier packet’s sketch involving the census_index_instances family does
not override the tables actually written by the accepted T2.2–T2.3
implementation.

No schema change is required or authorized.

6. Accounting vocabulary ruling

T2.4 must preserve these distinct quantities:

Already satisfied and not requested in continuation

A logical request with verified satisfying evidence that is excluded from the
continuation plan.

This quantity is the future receipt’s:

cache_hit_count

Conditional request returning lawful 304

A request was physically attempted with accepted validators and the predecessor
evidence was successfully reconciled.

This quantity is the future receipt’s:

not_modified_count

The existing WindowOutcome.cache_hits name currently represents this
not-modified behavior. T2.4 must not use that name to populate the future
receipt’s cache_hit_count.

Byte-identical 200 response

A physically retrieved response whose bytes match preserved immutable evidence.

This quantity is the future receipt’s:

duplicate_object_count

T2.4 shall expose unambiguous internal fields or properties so T2.5–T2.6 can
assemble these frozen receipt fields without inference or schema amendment.

No receipt is emitted during T2.4.

7. Attempt-accounting ruling

The cumulative consumed-attempt calculation is:

1. accepted cumulative attempt count from the resolvable predecessor receipt
    chain;
2. plus deterministically attributable committed observation attempts after the
    final terminating receipt;
3. plus the full registered A_reachable for at most one identifiable
    receiptless in-flight request in the sequential acquisition engine.

An attempt segment must not be counted twice.

If:

* the predecessor chain is missing, cyclic, or inconsistent;
* the post-receipt attempt segment cannot be attributed uniquely;
* more than one in-flight request appears possible;
* the logical request cannot be identified;
* the registered route bound cannot be derived;
* receipt, catalog, and plan evidence disagree materially;

the state is UNDETERMINED and continuation is prohibited.

The ceiling remains exactly the approved ceiling. It may not be increased,
reset, shadowed, reinterpreted, or replaced.

8. Migration ruling

Disposition:

NO_NEW_MIGRATION_REQUIRED

The migration chain remains exactly:

0001–0013

No migration 0014 exists or is implied.

The new reason is runtime-seeded through the accepted reason registry and does
not require schema modification.

9. Receipt ruling

Disposition:

NO_RECEIPT_SCHEMA_CHANGE_REQUIRED

The frozen receipt remains:

m3-execution-receipt/2.0

T2.4:

* emits no receipt;
* changes no receipt field;
* changes no completion-status vocabulary;
* places no item-level reconciliation identities into a receipt;
* preserves unknown-field refusal;
* preserves registered-reason validation.

Detailed reconciliation identities remain in catalog-derived in-memory output
and the later private reconciliation report.

10. F4 ruling

F4 does not block T2.4 implementation.

T2.4 creates no publicly indexed evidence artifact.

F4 remains open and must be resolved:

* no later than T4; and
* before the first affected freeze or reconciliation artifact is publicly
    indexed.

No evidence-index template or vocabulary path is authorized in T2.4.

11. Exact implementation path envelope

The maximum T2.4 implementation envelope is exactly eight tracked paths.

Production

1. src/disclosure_drift/m3/acquisition.py
2. src/disclosure_drift/m3/recovery.py
3. src/disclosure_drift/m3/__init__.py
4. src/disclosure_drift/reasons.py

Tests

5. tests/unit/test_m3_acquisition.py
6. tests/unit/test_m3_recover.py
7. tests/unit/test_m3_recovery.py
8. tests/unit/test_reasons.py

tests/unit/test_m3_recover.py may be created as the one authorized new test
file.

The owner expressly adds tests/unit/test_reasons.py to the Decision 035 path
envelope for T2.4 only and only for:

* the one-code SOURCE_REQUIRED_OBJECT_UNAVAILABLE registry delta;
* exact closed-set count adjustment;
* metadata and registration assertions.

This is a narrow, stage-scoped higher-authority amendment.

The historical T2 authorization packet remains byte-identical.

Decision 038 has no authority over T2.4.

Any need for another path requires an immediate stop before that path is
touched.

12. Explicitly prohibited paths

The following remain prohibited during T2.4:

* src/disclosure_drift/cli.py;
* src/disclosure_drift/m3/request_plan.py;
* src/disclosure_drift/m3/receipt.py;
* src/disclosure_drift/sec/observation_catalog.py;
* src/disclosure_drift/sec/snapshots.py;
* src/disclosure_drift/sec/raw_store.py;
* src/disclosure_drift/sec/http_client.py;
* src/disclosure_drift/sec/response_policy.py;
* src/disclosure_drift/sec/source_registry.py;
* src/disclosure_drift/sec/request_ceiling.py;
* all migrations;
* configuration;
* evidence templates;
* operator documentation;
* Decision 038 paths beyond their accepted T2.2–T2.3 bytes;
* all other source and test paths not expressly listed in §11.

Consumed accepted surfaces must remain byte-identical.

13. Test requirements

Implementation tests must cover:

* fresh catalog-authoritative reconstruction;
* no inherited predecessor-process mutable state;
* quarantine and failed-state exclusion;
* lawful usable-observation selection;
* missing object and hash mismatch;
* valid and missing archive lineage;
* lawful first acquisition, duplicate 200, changed 200, and verified 304;
* ETag-only, Last-Modified-only, and dual-validator behavior;
* unreconciled 304 refusal;
* singleton required-object reason attachment;
* index reason behavior unchanged;
* deterministic plan-to-catalog reconciliation;
* item-level absence enumeration;
* drift-blocking versus nonblocking listing;
* predecessor, plan, window, and ceiling binding;
* cumulative attempt accounting;
* conservative in-flight charge;
* no double counting;
* zero headroom;
* no replay of verified satisfied requests;
* distinction among already-satisfied exclusion, 304, and duplicate 200;
* SAFE, UNSAFE, and UNDETERMINED behavior;
* all four explicit recovery-action classes;
* refusal of mismatched, stale, multi-action, and UNDETERMINED repair requests;
* fresh SAFE inspection required after repair;
* no automatic repair or continuation;
* deterministic ordering and serialization;
* private-path and sensitive-data exclusion;
* no receipt creation;
* no real operational artifact;
* no CLI wiring;
* no network.

The accepted inspector’s no-writer-import and read-only tests must remain
load-bearing.

14. Mutation requirements

At minimum, prove the following guards are effective and load-bearing:

1. catalog-authoritative fresh-store reconstruction;
2. quarantine exclusion;
3. immutable-object verification before satisfaction;
4. archive-lineage verification before reuse;
5. unreconciled-304 refusal;
6. already-satisfied requests excluded from continuation;
7. cumulative attempts not reset;
8. conservative in-flight request charge;
9. stop-before-overflow;
10. UNDETERMINED continuation refusal;
11. automatic repair structurally absent;
12. repair-action mismatch refusal;
13. singleton required-object reason attachment;
14. distinction among already-satisfied, 304, and duplicate 200 accounting.

Before interpreting a surviving mutation as a test weakness, the implementation
session must prove that the mutation actually changes the intended behavior.

15. Commit and review rule

T2.4 uses at most one implementation commit.

Exact subject:

Implement M3.2 T2.4 recovery and reconciliation

The implementation candidate remains local until:

1. implementation completion;
2. ChatGPT owner review;
3. one fresh independent no-subagent stage audit;
4. correction and rereview where required;
5. separate owner acceptance and publication authorization.

No interim commit is authorized without a new owner ruling.

No T2.4 stage tag is authorized.

T2.5–T2.6 may not begin until T2.4 is accepted and published.

16. Validation rule

During implementation, use targeted tests and touched-file static checks.

At stage completion run:

* all authorized-path targeted tests;
* relevant unchanged regression tests identified by the impact map;
* Ruff;
* format check;
* mypy;
* SQLite check;
* secrets;
* hygiene;
* context;
* the full pytest suite with the SEC extra installed.

One full-suite run is required at normal completion.

Additional full-suite runs are required only when:

* nondeterminism is detected;
* a correction affects flaky or timing-sensitive behavior;
* the independent reviewer identifies a specific need.

All protected paths must be proven unchanged.

17. Stop conditions

Implementation must stop immediately before the act if:

* another reason code is needed;
* an existing reason must be redefined;
* a migration appears necessary;
* a receipt-schema change appears necessary;
* route or source authority must change;
* configuration must change;
* CLI wiring is required;
* any path outside §11 is needed;
* catalog-authoritative reconstruction cannot be completed through accepted
    read surfaces;
* a lawful 304 cannot be proved against immutable evidence;
* attempt accounting cannot be bounded deterministically;
* the explicit recovery applier cannot scope exactly one action;
* F4 becomes an immediate implementation prerequisite;
* D023-O1 triggers;
* a socket, real identity, or real SEC response appears necessary;
* a BLOCKER or relevant MAJOR arises;
* the accepted architecture proves unimplementable as written;
* contract, decisions, packet, schema, and implementation materially conflict.

18. Negative authority

This decision does not authorize:

* implementation before the separate execution packet is issued;
* operator CLI wiring;
* receipt emission;
* private reconciliation-report creation;
* evidence indexing;
* a real operational catalog;
* live SEC access;
* connectivity testing;
* network or CompanyFacts enablement;
* operational use of ceiling 801;
* T2.5–T2.6;
* T3, T4, T5, Gate H, or M3.3 work;
* any migration;
* any receipt-schema change;
* another reason code;
* another path;
* a push;
* a tag;
* a force push, amend, rebase, squash, or history rewrite;
* repository-efficiency or review-infrastructure improvements.

Efficiency and repository-infrastructure improvements remain deferred until
T2.4 has been implemented, independently audited, accepted, committed, and
pushed.

19. Continuing obligations

Remain open:

* accepted RawStore resource limitation as a T4 concern;
* sanitization or exclusion of untrusted progress-sink messages before later
    receipt or indexed-artifact use;
* F4 no later than T4;
* D023-O1 as a latent fail-closed referral condition;
* operator wiring and receipt assembly during T2.5–T2.6;
* overall independent T3 implementation acceptance after the combined
    T2.5–T2.6 freeze candidate.

20. Next authorized action

After Decision 040 is durably recorded and published, set exactly:

NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_4_IMPLEMENTATION_PACKET_AFTER_DECISION_040_PUBLICATION

No implementation begins until that separate owner packet is issued.

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

1. **Stage authorization.** M3.2 stage T2.4 — Recovery, Reconciliation, Resume Boundaries, and
   Drift Control — is authorized as one coherent implementation stage with four internal
   subphases (T2.4-A catalog-authoritative reconstruction; T2.4-B deterministic, read-only
   reconciliation and drift inspection; T2.4-C the continuation proposal and conditional reuse;
   T2.4-D the explicit recovery-action library boundary, with no CLI exposure). **No
   implementation session may begin until the separate exact T2.4 implementation packet is
   issued** (instrument §18).
2. **Reason code.** Exactly one new registered code is approved:
   `SOURCE_REQUIRED_OBJECT_UNAVAILABLE` (integrity; `blocks_release` true;
   `requires_manual_review` true; decision reference this record), with the §4.4 mapping and
   exclusions. The registry delta is implemented inside the authorized T2.4 stage, not by this
   recording; no second code is authorized.
3. **Dispositions.** `NO_NEW_MIGRATION_REQUIRED` (chain exactly `0001`–`0013`) and
   `NO_RECEIPT_SCHEMA_CHANGE_REQUIRED` (`m3-execution-receipt/2.0` frozen; no receipt emitted in
   T2.4). The durable reconciliation source is the accepted table set the T2.2–T2.3
   implementation actually writes. The accounting-vocabulary and three-part cumulative
   attempt-accounting rulings apply with their `UNDETERMINED` fail-closed rule. F4 does not block
   T2.4 and remains due no later than T4.
4. **Envelope.** The maximum T2.4 envelope is exactly eight tracked paths (instrument §11), with
   `tests/unit/test_reasons.py` expressly added to the Decision 035 envelope **for T2.4 only**
   and `tests/unit/test_m3_recover.py` the one authorized new test file. Every §12 path remains
   prohibited; any further path is an immediate stop before the path is touched.
5. **Commit, review, validation, stop.** At most one implementation commit with exact subject
   `Implement M3.2 T2.4 recovery and reconciliation`, local until implementation completion,
   ChatGPT owner review, one fresh independent no-subagent stage audit, correction and rereview
   where required, and separate owner acceptance and publication authorization; no T2.4 stage
   tag; T2.5–T2.6 gated on T2.4 acceptance and publication; the §16 validation rule and §17 stop
   conditions bind every implementation session.

## 6. Authority hierarchy and supersession

- **This record is higher authority** than Decision 035 §6's fifteen-path maximum and the T2
  packet §5 table — **for stage T2.4 only, and only for the one added test path and the eight-path
  envelope §4 fixes.** Every other provision of Decisions 035, 036, 037, 038, and 039 remains in
  force verbatim, including the envelope's character as a ceiling and not a grant, the
  immediate-stop rule for any out-of-envelope need, the four-stage cadence, the no-stage-tag and
  no-T3-tag rules, and every declined and prohibited surface.
- **Decision 038 has no authority over T2.4** (its own §9 and the §4 instrument agree): the two
  paths it added for combined T2.2–T2.3 remain prohibited here beyond their accepted bytes.
- **No accepted decision is edited in place.** Decisions 032–039 are byte-unchanged. The T2
  authorization packet is preserved byte-identical (SHA-256 `62120146…`) and must not be silently
  rewritten; the accepted contract is not edited and retains SHA-256 `c526335b…`.
- Where this record and an accepted record could ever be read to disagree, the accepted record
  controls and this record is corrected under a new owner instrument.

## 7. Negative authority

Instrument §18 applies in full and is not restated. In particular: no implementation before the
separate exact T2.4 implementation packet; no operator CLI wiring; no receipt emission or
reconciliation-report creation; no evidence indexing; no real operational catalog; no live SEC
access or connectivity testing; no network or CompanyFacts enablement; no operational use of
ceiling 801; no T2.5–T2.6, T3, T4, T5, Gate H, or M3.3 work; no migration; no receipt-schema
change; no second reason code; no further path; no tag; no force push, amend, rebase, squash, or
history rewrite; and no repository-efficiency or review-infrastructure improvements before T2.4 is
implemented, independently audited, accepted, committed, and pushed.

## 8. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_040_m3_2_t2_4_implementation_authorization.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 040 row and quick-lookup entry;
- `Milestones/STATUS.md` — current-state, blocker, authority-state, and next-action updates, with
  the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_4_IMPLEMENTATION_PACKET_AFTER_DECISION_040_PUBLICATION`;
- **one** governance-only commit with the subject `Authorize M3.2 T2.4 implementation`, and
  **one** normal fast-forward push of `main` under the owner's execution packet. **No tag.**

`Docs/decision_index.md` is deliberately **not** edited — the established navigation ruling stands
and the decision registry remains the discovery route. No implementation, test, script, migration,
template, packet, contract, review-artifact, configuration, or private-evidence byte changes.

## 9. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner instrument is recorded verbatim and neither
broadened nor reinterpreted; (2) `src`, `tests`, `configs`, migrations, the receipt module, the
reason registry, the contract, and the T2 packet are byte-identical, with the contract and packet
SHA-256 values unchanged; (3) Decision 040 is unique — no other decision file or registry row
carries the number, and directory and registry agree; (4) the registry and status ledger match
this record exactly, with the next-action marker line occurring exactly once and carrying no
suffix; (5) `git diff --check`, `git diff --cached --check`, `make context`, `make secrets`, and
`make hygiene` pass over the updated tree; (6) the commit carries exactly the three §8 paths;
(7) no tag is created; (8) no private path, SEC identity, or private-evidence content appears in
any changed file; (9) `Docs/decision_index.md` is unchanged.

## 10. Formal outcome

```text
M3_2_T2_4_IMPLEMENTATION_AUTHORIZED
```

**Next authorized action:**
`CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_4_IMPLEMENTATION_PACKET_AFTER_DECISION_040_PUBLICATION` — the
ChatGPT owner issues the separate exact T2.4 implementation packet. **No implementation session
may begin before it is issued**; network enablement, live SEC access, acquisition, real
operational-catalog creation, and ceiling-801 use all remain unauthorized.
