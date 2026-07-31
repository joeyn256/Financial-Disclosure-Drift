# Decision 024 — Milestone 2 Completion Boundary and Milestone 3 Obligation Transfer

**Date:** 2026-07-31
**Status:** ACCEPTED — OWNER APPROVED 2026-07-31
**Type:** Milestone-boundary governance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged. It changes no hypothesis, cohort window, maturity gate,
outcome definition, threshold, seed, methodology, identity, preimage, migration byte, or line of
code. It is a **boundary and naming** record: it fixes where Milestone 2 implementation ends, moves
the remaining obligations to Milestone 3 intact, and hands off to the final integrated audit.
**Supersedes:** nothing. **Amends:** nothing.
[Decision 021](decision_021_m23_s6_manifest_construction.md),
[Decision 022](decision_022_m23_s6_reserve_rank_applicability.md), and
[Decision 023](decision_023_m23_s6_acceptance_and_path_ratification.md) all remain `ACCEPTED`,
unchanged, and controlling for what they govern.
**Related:** [Decision 013](decision_013_pilot_selection_mechanics.md),
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md),
[Decision 018](decision_018_m23_s5_accession_selection_policy.md),
[Decision 019](decision_019_m23_s5_storage_to_pure_input_mapping.md),
[Decision 020](decision_020_m23_s5_4_reserve_architecture.md);
[`milestone_2_3_pilot_selection_plan.md`](../../Milestones/milestone_2_3_pilot_selection_plan.md)
§§11, 16; Decision 021 §17 (the S7–S10 table this record transfers).
**Governs:** the Milestone 2 / Milestone 3 boundary, the obligation transfer, the Milestone 3 phase
map, and the integrated-audit handoff.

---

## 1. Why this record exists

Stage M2.3 S6 was accepted and checkpointed on 2026-07-31. At that point the project's remaining
pilot obligations — the work described throughout Milestones 2.3 as "S7–S10" — were still nominally
Milestone 2 stages, even though Milestone 2 implementation was finished and the accepted S6 contract
authorized nothing further.

That left three things unstated, and a subsequent attempt to run the final integrated Milestones 1–2
audit **correctly stopped** because the governance record fixing them did not exist:

1. **Where Milestone 2 implementation ends.** Decision 023 §9 deferred the boundary to "a separate
   governance-only session" without defining it.
2. **Where the S7–S10 obligations live.** They could not remain Milestone 2 stages once Milestone 2
   implementation was complete, and they must not be lost, weakened, or renumbered in the move.
3. **What happens next, and in what order.** The audit, the closeout, and any Milestone 3 work must
   be sequenced explicitly rather than inferred.

This record settles all three. **It is governance only**: no code, test, migration, configuration,
or methodology changes with it.

## 2. Frozen ruling — accepted S6 is the end of Milestone 2 implementation

**Accepted Milestone 2.3 Stage S6 is the final implementation stage of Milestone 2.**

The accepted S6 checkpoint, for the record:

| | |
|---|---|
| Commit | `5c53412d820fe20a7bd727eac333ae2fb8724cd6` |
| Annotated tag | `m2.3-s6-complete` (supplements the immutable `m2.3-s5-complete` and `m2.3-s5.4-complete`) |
| Formal outcome | `M23_STAGE_S6_ACCEPTED_AND_COMPLETE` (Decision 023 §3) |
| Independent recommendation | `ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING` |
| Accepted suite | 2324 passed, 2 skipped |
| Contract | `Milestones/contracts/m23_s6.md` — `ACCEPTED_AND_COMPLETE`, `IMPLEMENTATION_AUTHORIZATION: NO` |

**No further implementation is authorized under Milestone 2, in any stage, by any contract.**

## 3. Frozen ruling — the final scope of Milestone 2

Milestone 2 consists of exactly three parts, all now implementation-complete:

- **Milestone 2.1 — offline SEC policy, storage, provenance, and governance foundation.** Approved
  source policy and registry, identifiers, temporal and availability policy, response policy, rate
  limiting, inventory and amendment policy, reason-code registry, raw-store governance,
  schema-drift policy, CompanyFacts-disabled policy, SQLite storage and the single-writer catalog,
  release boundaries, forecast storage, and cohort-divergence audit.
- **Milestone 2.2 — controlled live-metadata readiness.** Approved-source retrieval policy,
  immutable source observations, defensive bulk-archive handling, source-native parsers, the
  transactional registrant census, restart recovery, deterministic QA, and R3 durability and
  provenance hardening. Checkpointed at `m2.2-r3-complete`.
- **Milestone 2.3 through accepted Stage S6 — deterministic pilot selection and manifest
  architecture.** The candidate/selection/manifest schema (S3), deterministic entity selection (S4),
  joint entity–accession selection, persistence, reconstruction, and replay (S5.1–S5.3), reserve
  packages, quota-contribution membership, and dispositions (S5.4), and manifest construction,
  terminal result identity, lifecycle enforcement, verification, atomicity, and acceptance (S6).

## 4. Frozen ruling — Milestone 2 is not closed

**Milestone 2 is implementation-complete but NOT formally closed.** It remains open for exactly
four things, in order:

1. one **final independent integrated audit of Milestones 1 and 2**;
2. **bounded correction** of any findings that audit returns;
3. a **fresh independent rereview** where the corrections require one;
4. **formal Milestone 1 and Milestone 2 closeout**.

Nothing else keeps Milestone 2 open, and no implementation is authorized under any of the four.

## 5. Frozen ruling — the obligation transfer

**The obligations previously described as M2.3 Stages S7–S10 move into Milestone 3 intact.**

**No gate, prohibition, owner ruling, validation requirement, identity, methodology, or accepted
limitation is removed, weakened, renumbered, deferred further, or silently rewritten by this move.**
The transfer changes the *milestone label and phase name* of each obligation and nothing else. Where
Decision 021 §17 says "Stage S7", read "Milestone 3 phase M3.1", and so on; that record's substance
stands exactly as approved.

### 5.1 The Milestone 3 phase map

| New phase | Former | Scope |
|---|---|---|
| **M3.1 — Controlled live-operation readiness** | S7 | Final operational readiness; **Gate F**; controlled-network authorization prerequisites; **no live access until every required gate is satisfied** |
| **M3.2 — Controlled SEC metadata acquisition** | S8 | Authorized **metadata-only** SEC access; required SEC user agent; rate limiting; response-policy enforcement; raw-store provenance; schema-drift controls; **Gate H**. **No filing-body, CompanyFacts, Frames API, outcome, or publication authority** |
| **M3.3 — Frozen real pilot snapshot and deterministic execution** | S9 | Freeze the real candidate snapshot; execute the accepted joint entity/accession selection; execute reserve and disposition handling; persist and reconstruct the real pilot; construct the exact real-data manifest and the CLI output Decision 021 §16 deferred from S6; produce the exact root hash. **No owner approval and no publication** |
| **M3.4 — Exact root-hash owner approval** | S10 | Present the exact `root_manifest_sha256` and the governed evidence package; obtain an **explicit** owner decision. **No implied approval; no premature publication** |
| **M3.5 — Integrated real-pilot acceptance and Milestone 3 checkpoint** | *new* (the post-S10 integrated review and checkpoint) | Integrated review of acquisition, snapshot, selection, manifest, provenance, approval, and release eligibility; correction and rereview loops where required; **formal Milestone 3 closeout only after acceptance passes** |

**M3.5 is created by this record.** It is not a new obligation: the post-S10 integrated review and
checkpoint were always implied by the project's acceptance discipline, and naming the phase makes the
final review and closeout explicit rather than assumed.

### 5.2 Traceability — every transferred obligation, with what it carries

| Former stage | New phase | Inherited gates | Inherited prohibitions | Required owner decision | Required validation | Implementation authorization |
|---|---|---|---|---|---|---|
| S7 | **M3.1** | Gate F (live-metadata safety and allowlist); network off by default; explicit live flag; printed request budget; zero-request dry run; two dry runs producing an identical plan hash | No live access before every gate passes; no filing body; no CompanyFacts; no Frames API; no outcome access; no publication | Owner authorization to proceed to M3.2 | Full offline suite; the Gate F dry-run evidence; secrets, hygiene, lint, types | **NO** |
| S8 | **M3.2** | Gate H pre-run recovery state; authorized SEC user agent; deterministic bounded rate limiting; governed response classification and retry; raw-store content-addressed provenance; fail-closed schema-drift detection | Metadata only — no filing body, no CompanyFacts, no Frames API; no outcome acquisition; no publication; no approval | Owner authorization to freeze a real snapshot | Provenance completeness; migration integrity; no-network assertions outside the authorized window | **NO** |
| S9 | **M3.3** | Frozen-snapshot validation obligations (Decision 019 §9); accepted S5 joint-selection identity and reconstruction; accepted S5.4 reserve and disposition rules; accepted S6 manifest eligibility (Decision 021 §11.2), document contract, and the 81-item §13.2.1 crosswalk | No owner approval; no publication; no second selector; no reserve substitution; no relaxation of any accepted S5 output; no manifest state past `proposed` | Owner decision is **not** taken here | Full reconstruction and replay proofs over real data; byte-identical re-serialization; every digest recomputed from persisted rows | **NO** |
| S10 | **M3.4** | Decision 013 §8 — completion is owner approval of *the exact final manifest hash*; migration `0009`'s `approved_root_sha256 = root_manifest_sha256` check; Decision 021 §9's copy-not-hash rule | No implied, partial, or inferred approval; no publication before approval; no root recomputation to obtain a convenient value | **Explicit owner approval of the exact root** | The presented root reproduces from persisted state at the moment of approval | **NO** |
| — | **M3.5** | Every gate above, reviewed together; the independence discipline of Decisions 022 §9 and 023 §2 — no reviewer may review work it wrote | No closeout before acceptance passes; no publication authority created by acceptance itself | Owner acceptance of the integrated result | Integrated review of acquisition, snapshot, selection, manifest, provenance, approval, and release eligibility | **NO** |

**Implementation authorization is `NO` for every phase, without exception.**

### 5.3 Confirmation that every former obligation is preserved

Checked item by item against Decision 021 §17 and milestone plan §§11, 16: **every S7–S10 obligation
appears in exactly one Milestone 3 phase above, none was dropped, none was merged away, none was
weakened, and none was moved to a later phase than the one it previously occupied.** The CLI output
Decision 021 §16 deferred from S6 to S9 travels with M3.3, and milestone plan §10's "command
invocation" item — crosswalk item 80, the single `S9` deferral in Decision 021 §13.2.1 — travels with
it, still deferred and still not dropped.

## 6. Frozen ruling — inherited authority

**Milestone 3 inherits every applicable accepted control from Milestones 1 and 2**, unchanged:

- **Frozen research definitions** — cohort windows, maturity gates, outcome cutoffs, and **bootstrap
  seed `20260725`**; `src/disclosure_drift/cohorts.py` remains canonical (CLAUDE.md rule 3).
- **Temporal authority** — official filing date is authoritative for cohort assignment
  (Decision 010); the acceptance date remains **audit-only** where governed.
- **Identifier rules** — plain accession is database and foreign-key identity; **canonical dashed
  accession** is used for deterministic hashing and presentation (Decision 018 §5); loaders verify
  plain-to-dashed consistency and fail closed on disagreement.
- **SEC access controls** — required SEC user agent; deterministic bounded rate limiting; governed
  response policy and retry classification; raw-store and provenance rules; fail-closed schema-drift
  detection.
- **Data-source prohibitions** — **CompanyFacts disabled**; **Frames API prohibited**; external
  corpora **validation-only**.
- **Leakage controls** — the whole of `Docs/leakage_register.md`, **including L01, L04, L10, and
  L18**, plus L15 and L19 and the Decision 015 pilot-use prohibition.
- **Accepted S4 isolation** — the entity-only draft stays `running`, non-publishable, and is never
  mutated, deleted, promoted, or used as a manifest input (Decision 018 §§6, 27; Decision 020 §11).
- **Accepted S5** — identity, selection, roles, evidence, contributions, quota rules, reserves,
  dispositions, persistence, reconstruction, and replay.
- **Accepted S6** — every manifest identity and preimage, the lifecycle and its eight migration-`0013`
  guards, verification, and file/database atomicity.
- **The decision record** — Decisions 013, 016, 018, 019, 020, 021, 022, 023, and **this Decision
  024**.
- **All accepted nonblocking limitations and future owner-ruling conditions** — Decision 020 §19.1
  (five), Decision 021 §19 (items 1–10; §19.11 closed), Decision 022's applicability boundary, and
  Decision 023 §7 (**O1**–**O4**). O1's empty sole-carrier crosswalk family remains a **future
  owner-ruling condition** that Milestone 3 inherits unresolved and must refer if a real run reaches
  it.

## 7. Authority separation

Stated so that no later session has to infer which record answers which question.

| Record | Controls |
|---|---|
| **Decision 021 v0.5** | The **S6 architecture** — every digest preimage, the root, `manifest_id` and its immutability, eligibility, the proposed-only boundary, reconstruction and replay, the document contract and the 81-item crosswalk, the S4/S5 boundary, migration `0013`, and the original S7–S10 scope definitions this record renames |
| **Decision 022** | **Crosswalk item-46 reserve-rank applicability**, and nothing else |
| **Decision 023** | **S6 acceptance**, the three-path ratification, the accepted residual limitations O1–O4, and the S6 checkpoint authorization |
| **Decision 024** (this record) | **Only** the milestone boundary, the obligation transfer, the audit handoff, and the future phase naming |

**This record adds no architecture, reopens no ruling, and resolves no open question belonging to
another record.**

## 8. Frozen ruling — no implementation authority

**This decision grants no implementation authority of any kind.**

**Assigning an obligation to Milestone 3 is not authorization to begin Milestone 3.** The transfer
is a governance relabelling; it starts nothing. This is the same distinction the project has drawn
throughout — an approved decision was never authorization to write code (Decision 021 §23), and a
cleared blocker was never authorization to implement
([`contracts/README.md`](../../Milestones/contracts/README.md)).

**No Milestone 3 phase may begin implementation without all of:**

1. a **separate accepted governance record** where the phase requires one;
2. a **bounded implementation contract** for that phase;
3. **explicit owner authorization**;
4. **exact path authorization** — the authorized-path discipline of every prior stage contract;
5. **satisfaction of that phase's inherited prerequisite gates** (§5.2).

**And, before any of that: Milestone 3 implementation may not begin until the required Milestone 1
and Milestone 2 closeout is complete** (§9).

## 9. Frozen ruling — what happens next, in order

1. **`FINAL_INDEPENDENT_INTEGRATED_MILESTONES_1_AND_2_AUDIT`** — the next authorized action. Read-only
   and adversarial; it records no closeout and authorizes no implementation. It must also verify this
   record, the exact obligation transfer, Milestone 3 governance readiness, the existence and
   consistency of its expected audit-input documents, and the absence of premature Milestone 3
   implementation.
2. **Bounded correction and fresh rereview**, if the audit returns findings.
3. **Formal Milestone 1 and Milestone 2 closeout**, in a separate governance-only session, only after
   the audit passes. That session controls the final closeout tags; **this record authorizes no tag.**
4. **Only then**, Milestone 3 planning and governance — and, later still and separately, any
   Milestone 3 implementation authorization under §8.

## 10. Negative confirmations

True at the moment this record is accepted, and verified against the repository rather than assumed:

- **No S7 implementation began.** No S7 contract exists and none ever did.
- **No Milestone 3 implementation began.** No Milestone 3 contract, production module, test,
  migration, CLI surface, or network allowlist exists.
- **No live SEC operation occurred.** Network access remains disabled at the accepted boundary.
- **No real candidate snapshot exists**, and no candidate-snapshot builder exists.
- **No real pilot manifest exists.** Every accepted S6 artifact is a fixture-only `proposed` manifest.
- **No root hash was approved**, and `approved_root_sha256` has never been written.
- **No publication authority exists** anywhere in the repository.
- **No production catalog database exists.**

## 11. What this record does not change

Recorded so that no later session reads a boundary decision as a licence:

**cohort boundaries; outcome cutoffs; the bootstrap seed; SEC policy; identifiers; temporal policy;
leakage controls; selection methodology; reserves; dispositions; hash preimages; manifest identities;
migration SQL; S4 behaviour; S5 behaviour; S6 behaviour; and every accepted limitation.**

Also unchanged: all 81 crosswalk rows and their totals (D 42 / T 30 / X 8 / S9 1 / S10 0 /
unclassified 0); the nine migration-`0013` digests over a 10939-byte, 186-line statement region; the
eight triggers; migrations `0001`–`0013`; and every accepted contract, which stays closed.

## 12. Formal outcome

```
M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED
```

## 13. Checkpoint authorization

The project owner authorizes, for this boundary recording and no other purpose:

1. **one governance-only commit** containing this record and the navigation, status, and contract-index
   updates it requires;
2. **a push to `origin/main`**.

**No tag is authorized in this session.** The final Milestone 1 and Milestone 2 closeout session
controls the closeout tags. `m2.3-s6-complete`, `m2.3-s5.4-complete`, and `m2.3-s5-complete` are
immutable and are never moved, replaced, or re-pointed. CLAUDE.md rule 13 applies independently to
everything beyond this list.

## 14. Reason

A milestone boundary is worth a decision record for the same reason a hash preimage is: left
implicit, it is re-derived differently by each session that needs it. Milestone 2 finished its
implementation at accepted S6, but the obligations still labelled "S7–S10" would have sat in an
ambiguous place — nominally Milestone 2 stages, under a milestone whose every contract was closed and
whose implementation was complete. The integrated audit stopped rather than proceed against that
ambiguity, which was the correct action and is why this record exists.

The move itself is deliberately boring: same obligations, same gates, same prohibitions, same owner
decisions, new phase names. What it adds is sequence — audit, then closeout, then planning, then, only
with its own contract and authorization, implementation. Naming M3.5 is the one addition, and it makes
explicit what the project has done at every prior boundary: review the whole thing together before
calling it finished.

No deviation from Decisions 013–023 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.
