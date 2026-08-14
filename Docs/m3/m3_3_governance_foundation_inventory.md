# Milestone 3.3 — Governance Foundation Inventory

**Date:** 2026-08-13
**Type:** Read-only governance inventory produced under the owner's M3.3-G entry packet.
**Status:** `INVENTORY — INPUT TO OWNER REVIEW`. It authorizes nothing, accepts nothing, and
freezes nothing.

**Updated 2026-08-13 under the owner's M3.3-GR packet.** Ten of the twelve owner-ruling requests in
§G have been disposed of — six ruled (R3, R4, R5, R8, R10, R12) and four deferred to named owner
gates (OR-6, OR-7, OR-9, OR-11). **OR-1 and OR-2 remain open and entry-blocking.** The dispositions
are stated in [`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md) §1.1 and §1.2,
which control; §G below records them for navigation only. An exact **proposal** for OR-1 and OR-2 —
which decides nothing — is in
[`m3_3_snapshot_authority_adjudication_proposal.md`](m3_3_snapshot_authority_adjudication_proposal.md).
This document remains a navigation index and gains no authority from either change.

**Updated again 2026-08-13 under accepted
[Decision 067](../Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md) — the
paragraph above is historical as at the M3.3-GR packet.** **No owner-ruling request is open.**
**OR-1** and **OR-2** are **RESOLVED — OWNER RULED** (Decision 067 §§9, 10), and four further rulings
were issued: **R13** offline parse prerequisite and source binding, **R14** structural fingerprint
non-vacuity, **R15** evidence provenance identity retained (ALT-3), and **R16** candidate evidence
and resolution identity. The owner also recorded four previously frozen dispositions for the first
time — **OQ-3** fail closed on a same-catalog `snapshot_id` collision, **OQ-4** `snapshot_id`
excluded from the seven family digests, **OQ-6** `coverage_policy_version` = `pilot-coverage/1.0`,
and **OQ-8** evidence roles `winning` / `competing` / `supporting` — and corrected the proposal at
**GR-C1** and **GR-C2**. The census parse layer is verified **EMPTY**, and **R13** makes a bounded
offline metadata parse the prerequisite, with real execution separately gated at **M3.3-E0**.
**The contract is CORRECTED and still NOT ACCEPTED**, implementation remains unauthorized, network
authority remains `NONE`, and **no limitation is closed** — one is added, **D067-L1**. §F and §G
below are updated for navigation only; the decision and the contract control.

**Updated a third time 2026-08-13 under accepted
[Decision 068](../Decisions/decision_068_m3_3_e0_contract_correction.md).** The fresh independent
review of the Decision-067-corrected contract (frozen target `c8acfef…`) returned
`M3_3_CORRECTED_CONTRACT_FRESH_INDEPENDENT_REVIEW_FAILED` — BLOCKER 0 / **MAJOR 1** / **MINOR 1** /
OBSERVATION 5 ([review artifact](reviews/m3_3_corrected_contract_independent_review_c8acfef.md),
immutable). The owner adopted its findings and Decision 068 corrected the contract: **R17** fixes
the E0 permitted persistence footprint at exactly **fifteen tables** (the mechanically verified
write set of the reusable accepted parser-and-`CensusCatalog` path, `census_qa_metrics` and every
index-side table excluded), **R18** fixes the report-level per-planned-source E0 dispositions
(A/B/C, the 70 full-index sources category C, no `parser_state` mutation for category C), and
**R16-C1** clarifies resolution contributor membership. The contract became
`CORRECTED — DECISIONS 067–068 OWNER RULINGS RECORDED — PENDING FRESH INDEPENDENT REREVIEW AND
OWNER ACCEPTANCE`; implementation, E0, and E1 remained unauthorized, and the next act was a **fresh
independent rereview by a new non-author epoch**.

**Updated a fourth time 2026-08-13 under accepted
[Decision 069](../Decisions/decision_069_m3_3_contract_final_owner_acceptance.md) — the paragraph
above is historical as at Decision 068.** The fresh independent rereview by a new non-author epoch
ran against frozen target `7bb36b8…` and **PASSED** — BLOCKER 0 / MAJOR 0 / MINOR 0 / OBSERVATION 1
([rereview artifact](reviews/m3_3_decisions_067_068_corrected_contract_fresh_rereview_7bb36b8.md),
immutable, committed `033d0d9…`) — and the owner accepted the rereview and the contract. The M3.3
contract is now **`ACCEPTED — OWNER FINAL CONTRACT ACCEPTANCE — DECISION 069`** and is the active
stage contract; the single observation (OBS-R1, Decision 068 §3.1's "twenty-four durable-write
statements" numeral) is disposed as a **nonblocking historical narrative erratum** (read as 19
execute sites, or 23 write clauses counting embedded upserts; the fifteen-table footprint is
unchanged), without editing Decision 068. **Acceptance is not implementation authorization**:
implementation, E0, E1, and E2 remain unauthorized, network authority remains `NONE`, no limitation
changed state, and the next act is a **separate owner M3.3-I/R implementation + rehearsal
authorization packet**. This document remains a navigation index and gains no authority.

**What this document is.** A compact map from each M3.3 requirement to the accepted record that
governs it, the code that already implements it, and what remains. It exists so that the owner can
rule on the open methodology questions without re-deriving the corpus, and so that the M3.3 stage
contract — [`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md), currently a
**draft** — can cite rather than invent.

**What it is not.** Not an authority. It defines, approves, and amends nothing; where it and a
decision record, a migration, or a module disagree, the decision, migration, or module controls
(CLAUDE.md authority rules). It cites exact sections and paths and deliberately does not duplicate
governing text.

**Entry state this inventory was built against**, verified live before it was written:

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD / `origin/main` | `e3e58f93efb868263ce8cc501f506528fcbc6fae` |
| Tree | `0e2df64a2f4c570495668368ecbc23912a96d1d2` |
| Working tree | clean |
| Latest accepted decision | **Decision 066** |
| `m3.2-complete` | tag object `2865a1479e4576dc18a4098c928b278812f38d00`, peeled `2185f5835a711963659cf7c4067ff5a8b88349b9` — **unmoved** |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

Three commits are distinct and are never collapsed: the **accepted M3.2 implementation baseline**
`5c4c875e89ea588acd7c04414a05e566c647b39c`; the **Decision 065 closeout commit**
`2185f5835a711963659cf7c4067ff5a8b88349b9`, which carries the tag; and the **Decision 066
post-closeout correction** `e3e58f93…`, which the owner has accepted as the **M3.3 entry software
baseline** and which replaces neither of the first two as historical fact (Decision 066 R3).

---

## A. Authority map

`ACTION` is one of `REUSE`, `EXTEND`, `NEW`, `NOT APPLICABLE`, `OWNER RULING REQUIRED`.

| # | Requirement | Governing record | Exact section | Current implementation | Action |
|---|---|---|---|---|---|
| A1 | M3.3 phase objective, scope, non-scope, stop conditions, tokens | `Milestones/milestone_03_master_plan.md` | Phase M3.3 §§1–36 | — (plan only) | REUSE |
| A2 | M3.3A/M3.3B internal split; M3.3B gated on the M3.3A review | master plan; Decision 027 | M3.3 preamble, §26; D027 §6.3 | — | REUSE |
| A3 | Mandatory contents of a Milestone 3 phase contract | master plan | §16 (twenty items) | — | REUSE |
| A4 | Required sections of any stage contract | `Milestones/contracts/README.md` | "Required sections" (thirteen) | — | REUSE |
| A5 | No Milestone 3 phase begins without five conditions | Decision 024 | §8 | — | REUSE |
| A6 | Candidate-snapshot **representation** obligations | Decision 019 | §§5–8 | none — no builder exists | REUSE (as obligations) |
| A7 | Candidate-snapshot **freeze validation** obligations | Decision 019 | §9 | partially, at read time, in `sec/accession_selection_store.py` | EXTEND |
| A8 | Candidate-builder boundary — the builder does not exist and is unauthorized | Decision 019 | §9.1 | confirmed true at `e3e58f9` | NEW (needs authorization) |
| A9 | Exact candidate-snapshot **identity preimages** — still unresolved; an exact proposal is at proposal §§A–C (`snapshot_id`, `coverage_window_sha256`, `input_observation_set_sha256`, the seven `candidate_*_sha256`, `candidate_snapshot_sha256`) | Decision 016 §1 names inputs **in prose only**; Decision 021 §8.2 binds declared digests without recomputing them; limitation **D021-L2** records the absence | D016 §1; D021 §8.2; D021-L2 | none | **OWNER RULING REQUIRED** (OR-1) |
| A10 | Derivation of candidate rows from accepted M3.2 evidence | no accepted record fixes it | — | none | **OWNER RULING REQUIRED** (OR-2) |
| A11 | S5 run identity (`selection_run_id`, `selection_input_sha256`) | Decision 019 §10; Decision 018 §26 | D019 §10; D018 §26 | `build_joint_selection_run_identity`, `accession_selection_store.py:1540` | REUSE |
| A12 | Joint objective and its term order | Decision 013 §5; Decision 018 §3 | D018 §§3.1–3.4 | `solve_joint_selection`, `accession_selector.py:2554` | REUSE |
| A13 | Deterministic selected-accession order and `selected_order` | Decision 018 | §4 | `accession_selector.py`; persisted by `accession_selection_store.py` | REUSE |
| A14 | Canonical dashed accession; plain DB/FK identity; tie-break formula; fail-closed loader | Decision 018 | §§5.1–5.3 | `sec/identifiers.py`, `accession_selector.accession_selection_rank`, `accession_selection_store._dashed_from_plain` / `_validate_accession_identity` | REUSE |
| A15 | Accession roles, mutual exclusivity, counting consequences | Decision 018 | §7 | `assign_accession_role`, `accession_selector.py:1130` | REUSE |
| A16 | Accession caps and entity accession floors | Decision 018 | §§8, 9 | `accession_cap_outcomes`, `accession_caps_satisfied` | REUSE |
| A17 | Amendment families, unresolved parentage, linked-amendment coverage | Decision 018 §10; Decision 019 §5 | D018 §§10.1–10.5 | `derive_amendment_families`, `sec/amendments.py`, `_walk_to_root_original` | REUSE |
| A18 | Fiscal-year-end-change evidence | Decision 018 | §12 | `circular_month_day_distance`, `accession_selector.py:388` | REUSE |
| A19 | Name-change (name-only at M2.3) and ticker treatment | Decision 018 §13; Decision 019 §8 | D018 §13; D019 §§8.1–8.6 | `_name_change_evidence`, `accession_selection_store.py:1018` | REUSE |
| A20 | Difficult-or-nonstandard package quota — deferred, `unproven`/`unavailable` | Decision 018 | §14 | quota persistence in `accession_selection_store.py` | REUSE |
| A21 | 2009 support / 2010 target pairs; pre-study provenance | Decision 018 §15; Decision 019 §7 | D018 §15; D019 §§7.1–7.6 | `_cohort_mapping`, `accession_selection_store.py:860` | REUSE |
| A22 | Hard / deferred / measurable quota dispositions | Decision 018 | §16 | quota diagnostics in `accession_selector.py` | REUSE |
| A23 | Node limit as an explicit run input; failure semantics | Decision 018 §17; unsuccessful-outcome handling fixed by **Owner Ruling R10** | D018 §17; contract §1.1, §12 | `execute_and_persist_joint_selection(node_limit=…)` | REUSE — the **real value** is a deferred owner input (OR-7, §1.2); R10 forbids relabelling node-limit exhaustion as proven infeasibility |
| A24 | No automatic retry; no retry entry point | Decision 018 | §18 | enforced in `accession_selection_store.py` | REUSE |
| A25 | Pure core versus persistence adapter; no second methodological implementation | Decision 018 | §19 | `accession_selector.py` (pure) / `accession_selection_store.py` (adapter) | REUSE |
| A26 | Reserve methodology, single rank 1, eligible pool, tie-break, signature | Decision 020 | §7 | `sec/reserve_selector.py:551` `build_reserve_packages` | REUSE |
| A27 | No-compatible-reserve disposition — target-specific, nonblocking | Decision 020 | §7.1 | `_persist_reserve_dispositions`, `accession_selection_store.py:1837` | REUSE |
| A28 | Quota-contribution membership, three row families | Decision 020 | §6 | `_persist_quota_contribution_membership` | REUSE |
| A29 | `selection_result_sha256` canonical preimage | Decision 021 | §6.1, §6.2, §6.3 | `release/pilot_manifest.selection_result_sha256` | REUSE |
| A30 | The eight component digests | Decision 021 | §§7.1–7.4, 8.1–8.4 | `release/pilot_manifest.py` | REUSE |
| A31 | `root_manifest_sha256` | Decision 021 | §9 | `release/pilot_manifest.root_manifest_sha256` | REUSE |
| A32 | `manifest_id` derivation and six-field immutability | Decision 021 | §§9.1, 9.2 | `manifest_identifier`; migration `0013` trigger 4 | REUSE |
| A33 | Circularity exclusions and commitment closure | Decision 021 | §§10, 10.1 | `release/pilot_manifest.py` | REUSE |
| A34 | Proposed-only boundary; eligibility's seven conditions; transactions | Decision 021 | §§11.1, 11.2, 11.3 | `_require_eligible_run`, `build_and_persist_pilot_manifest` | REUSE |
| A35 | Reconstruction and replay; nothing stored is trusted that was not re-derived | Decision 021 | §12 | `verify_pilot_manifest`, `reconstruct_persisted_joint_selection` | REUSE |
| A36 | The thirteen-block document and the 81-item §10 crosswalk | Decision 021 | §§13.2, 13.2.1, 13.3 | `CROSSWALK`, `crosswalk_totals` in `release/pilot_manifest.py` | REUSE |
| A37 | Operational envelope excluded from digests **and** from the document | Decision 021 | §13.4 | `OPERATIONAL_ENVELOPE_FIELDS` | REUSE |
| A38 | Canonical encoding, `DataTree.releases / "pilot"`, content-derived filename | Decision 021 | §13.5 | `manifest_filename`, `PILOT_MANIFEST_SUBDIRECTORY` | REUSE |
| A39 | S4 draft exclusion; S5 as sole joint-selection authority | Decision 021 §14; Decision 018 §6 | D021 §14 | eligibility condition 6; migration `0013` | REUSE |
| A40 | Item-46 reserve-rank applicability | Decision 022 | whole record | `NOT_APPLICABLE_WITHOUT_RESERVE_PACKAGE` | REUSE |
| A41 | **O1** — empty sole-carrier crosswalk family fails closed and is **referred, never resolved** | Decision 023 | §7 (O1) | `GateFailureError` on an unplaceable item | REUSE — referral remains an owner act |
| A42 | O2 owner-controlled release root; O3 atomicity ownership; O4 item-46 defence in depth | Decision 023 | §7 | as accepted | REUSE |
| A43 | The CLI output deferred from S6 to this phase | Decision 021 | §16 | none — no S6/S9 CLI exists | NEW |
| A44 | Execution receipts, `invocation_mode = "offline_execution"` | `Docs/m3/execution_receipt_spec.md` | §§ mode table, fields | `m3/receipt.py` writer `m3-execution-receipt/3.0` | EXTEND |
| A45 | E1–E8 execution-rehearsal scenarios and pass criteria | `Docs/m3/offline_rehearsal_spec.md` | Part II §§7–9 | none — unimplemented | NEW |
| A46 | Private-evidence two-layer model; ledger-not-index practice | master plan §12; Decision 065 §8 | — | `m3/evidence_paths.py`, `scripts/check_repo_hygiene.py` | REUSE |
| A47 | Read-only invariant for a durable-artifact-preserving command | Decision 066 R1/R2, extended to M3.3 by **Owner Ruling R3** | D066 R1, R2; contract §1.1, §14 | `strictly_read_only_connection`, `storage/catalog.py:100` | REUSE — R3 fixes the M3.3 standard as durable-byte equality on a true OS-level strictly-read-only handle, with no writer lease |
| A48 | Leakage controls L01–L05, L10, L13, L15, L19; Decision 015 | `Docs/leakage_register.md`; Decision 015 | — | pilot-use prohibition throughout | REUSE |
| A49 | Frozen research definitions, seed `20260725`, cohort rules | `cohorts.py`; Decision 010 | — | `src/disclosure_drift/cohorts.py` | REUSE — never altered |
| A50 | Gate H as an M3.3 precondition | Decision 065 §3 + the current `Milestones/STATUS.md` record, per **Owner Ruling R4** | contract §1.1, §22 | token never emitted and never emitted retroactively; Gate H owner-accepted by Decision 065 §3; the two operative surfaces now cite the durable proof | **RULED — R4** (was OR-4, CF1) |

---

## B. Implementation reuse / gap map

Classification: `REUSE AS-IS`, `EXTEND`, `NEW`, `NOT SUITABLE`, `OWNER QUESTION`.

| Item | Exact path | State at `e3e58f9` | Class |
|---|---|---|---|
| **A. Candidate generation / loading** | — | **No candidate-snapshot builder exists.** `grep -rn "INSERT INTO pilot_candidate" src/` returns nothing; every `pilot_candidate_*` reference in `src/` is a read, a count, or a validation. Decision 019 §9.1's statement remains literally true | **NEW** + OWNER QUESTION (OR-1, OR-2) |
| Candidate **loading** (frozen rows → pure inputs) | `sec/accession_selection_store.py:1194` `load_frozen_joint_candidates`; `sec/entity_selection_store.py:163`,`:200` | accepted, implemented, tested | REUSE AS-IS |
| **B. Accepted joint selector** | `sec/accession_selector.py:2554` `solve_joint_selection` | accepted S5.1; **the sole methodological selector** (`Milestones/contracts/README.md`, S5.1 entry; Decision 021 §14; Decision 018 §19) | REUSE AS-IS |
| Entity-only solver (S4) | `sec/entity_selector.py:926` `solve_entity_selection` | accepted; produces the permanently-`running` S4 **draft**, excluded from manifest authority (Decision 021 §14) | REUSE AS-IS — never a second joint selector |
| **C. Entity deterministic ordering** | `sec/entity_selector.py:81` `selection_rank`; `pilot_policy.PILOT_SELECTION_SEED` | accepted | REUSE AS-IS |
| **D. Accession ordering / tie-break** | `sec/accession_selector.py:364` `accession_selection_rank`; Decision 018 §§4, 5.2 | accepted | REUSE AS-IS |
| **E. Plain ↔ dashed validation** | `sec/identifiers.py:65` `parse_accession`; `accession_selection_store.py:436` `_dashed_from_plain`, `:1356` `_validate_accession_identity` | accepted; fails closed | REUSE AS-IS |
| **F. Amendment family / parentage** | `sec/accession_selector.py:1187` `derive_amendment_families`; `sec/amendments.py:79` `link_amendment`; `accession_selection_store.py:631` `_walk_to_root_original`, `:688` `_require_strict_acceptance_order` | accepted; unresolved parentage fails closed for affirmative contribution (Decision 018 §10.2) | REUSE AS-IS |
| **G. Role classification** | `sec/accession_selector.py:1130` `assign_accession_role` | accepted; four mutually exclusive roles | REUSE AS-IS |
| **H. Quota evaluation** | `sec/accession_selector.py` quota diagnostics; `accession_selection_store.py:1922` `_insert_quota_result` | accepted | REUSE AS-IS |
| **I. Reserves** | `sec/reserve_selector.py:551` `build_reserve_packages` | accepted S5.4 | REUSE AS-IS |
| **J. Dispositions** | `accession_selection_store.py:1837` `_persist_reserve_dispositions`; `reasons.REVIEW_PILOT_NO_COMPATIBLE_RESERVE` | accepted | REUSE AS-IS |
| **K. Persistence schema / migrations** | `storage/migrations/0009`–`0013` | complete for candidate, selection, reserve, quota, and manifest families; snapshot lifecycle guards present (§C below) | REUSE AS-IS — **no new migration is expected**; if one becomes necessary that is a stop condition |
| **L. Reconstruction** | `accession_selection_store.py:2121` `reconstruct_persisted_joint_selection` | accepted; re-derives from the frozen snapshot and compares field by field | REUSE AS-IS |
| **M. Replay** | `accession_selection_store.py:1964` `execute_and_persist_joint_selection` (same-ID replay); `pilot_manifest_store.py:1019` `build_and_persist_pilot_manifest` (manifest replay) | accepted; both read-reconstruct-compare-return | REUSE AS-IS — proof standard is OR-3 |
| **N. Canonical serialization / hashing** | `release/hashing.py` (`normalize_value`, `hash_table`, `NULL_SENTINEL`) | accepted; **no second hashing implementation may be created** (Decision 021 §5) | REUSE AS-IS |
| **O. Manifest construction** | `release/pilot_manifest.py` (2280 lines — eight component digests, root, `manifest_id`, 81-item crosswalk, thirteen-block document, canonical JSON) and `sec/pilot_manifest_store.py:1019` | **exists, accepted, and complete** (Decision 023 §3) | REUSE AS-IS |
| **P. Manifest verification** | `sec/pilot_manifest_store.py:1125` `verify_pilot_manifest` | exists; re-derives every digest, the root, `manifest_id`, and the document from persisted rows | REUSE AS-IS |
| **Q. Atomic file/database writes** | `storage/sqlite.py:119` `transaction`; `pilot_manifest_store._require_serialized_document` and the single-transaction write in `build_and_persist_pilot_manifest` | accepted; row and file commit together (Decision 021 §11.3) | REUSE AS-IS |
| **R. Recovery / interruption** | `Docs/m3/templates/interrupted_run_recovery.md`; migration `0013` guards; `m3/recovery.py` (M3.2-shaped) | template REUSE; the selection/manifest safe-state enumeration REUSE (master plan §M3.3 §28); the **snapshot-freeze** boundary is now fixed by **Owner Ruling R5** — one atomic construct-and-freeze transaction, a surviving `building` row nonauthoritative and blocking, and no automatic recovery across any authoritative boundary | EXTEND — **RULED (R5)** |
| **S. Evidence packet utilities** | `Docs/m3/templates/real_snapshot_evidence_packet.md`; `m3/evidence_paths.py`; `m3/receipt.py` | templates and the containment boundary exist | REUSE AS-IS / EXTEND for `offline_execution` fields |
| **T. Limitations handling** | `Docs/m3/limitations_register.md` | 36 open, 6 closed; register is read at phase start and never closes an inherited entry on its own | REUSE AS-IS |
| **CLI output deferred from S6** | none | Decision 021 §16 defers it to this phase; `cli.py` has no pilot-manifest subcommand | **NEW** |
| **E1–E8 rehearsal harness** | none | `Docs/m3/offline_rehearsal_spec.md` Part II specifies it; nothing implements it | **NEW** |
| **Offline metadata parse driver** | the **pure parsers**, `SnapshotStore` local loading and verification, archive iteration, and `CensusCatalog` persistence — **all already offline-capable** (M3.3-GV2) | **The seam is missing, not the machinery.** Retrieval and parsing are coupled **only at the orchestration entry points** (`sec/census_orchestrator.py`, whose sole entry is the network-gated `sec census`); no offline entry point exists. The census parse layer is **EMPTY**, `parser_state` `not_started` for all 76 plan sources. Owner Ruling **R13** makes a bounded offline parse the prerequisite; real execution is separately gated at **M3.3-E0** | **NEW — SMALL_EXTENSION; RULED (R13, R14)** |

### Proof that exactly one accepted selector exists

1. **`sec/accession_selector.py` is named the sole methodological selector** by
   `Milestones/contracts/README.md` (the `m23_s5_1.md` index entry: "It remains the sole
   methodological selector") and by `Docs/change_impact_map.md` row for that module.
2. **Decision 018 §19** puts every methodological rule in the pure core and forbids the adapter from
   becoming a second implementation.
3. **Decision 021 §14** states that Stage S5 remains the sole accepted joint-selection authority,
   that S6 runs no second selection, and that the five selector/store modules are unchanged by S6.
4. **The master plan's M3.3 §10** lists those same five modules as **reused, never edited**, and its
   §17 stop condition 16 makes "a second selector appearing" a stop condition.
5. Mechanically, `src/` contains exactly two solvers — `solve_joint_selection` (S5, joint) and
   `solve_entity_selection` (S4, entity-only draft, excluded from manifest authority) — and no other
   module derives a selection.

**M3.3 therefore constructs inputs for the existing selector. It does not implement a selector.**

---

## C. Schema and persistence map

| Family | Tables | Migration | Guards already in place | M3.3 use |
|---|---|---|---|---|
| Candidate snapshot | `pilot_candidate_snapshots` | `0009` | `pilot_snapshot_insert_must_be_building`; `pilot_snapshot_transition_guard` (`building→frozen|invalidated`, `frozen→invalidated` only); `pilot_snapshot_frozen_fields_immutable` (22 fields, NULL-safe, holds across `frozen→invalidated`); `pilot_snapshot_no_delete`; `pilot_snapshot_freeze_requires_valid_state` (declared counts, one anchor per accession) | **written** by the new builder |
| Candidate content | `pilot_candidate_entities`, `pilot_candidate_accessions`, `pilot_candidate_accession_registrants`, `pilot_candidate_entity_evidence`, `pilot_candidate_accession_evidence`, `pilot_candidate_entity_reasons`, `pilot_candidate_accession_reasons` | `0009` | per-table insert/update/delete guards refusing any write unless the parent snapshot is `building` | **written** by the new builder |
| Selection run | `pilot_selection_runs`, `pilot_selection_run_events` | `0009`, `0011`, `0013` | `0013` triggers 1, 2, 6, 7, 8 — insert-only-unsealed, append-once seal, no replacement, no delete, immutable `selection_run_id`/`snapshot_id`/`selection_input_sha256` | written by the **accepted** S5 store |
| Selection results | `pilot_selected_entities`, `pilot_selected_accessions`, the two contribution tables, `pilot_quota_results`, `pilot_quota_result_members`, `pilot_selection_entity_reasons` | `0009`, `0012` | `running`-window guards | written by the **accepted** S5 store |
| Reserves | `pilot_reserves`, `pilot_reserve_accessions`, `pilot_reserve_quota_contributions` | `0009` | signature `CHECK`, `target <> replacement` | written by the **accepted** S5 store |
| Manifest | `pilot_manifest_versions` | `0009`, `0013` | `0013` triggers 3, 4, 5 — proposed-only insert over a `feasible` run, six-field identity immutability, no replacement | written by the **accepted** S6 store |
| Projection recovery | `pilot_projection_recovery_events` | `0009` | — | **stays unwritten** (Decision 021 §16) |

**Schema conclusion.** Every table M3.3 needs already exists, and the snapshot lifecycle is already
guarded at the schema layer. **No migration is anticipated.** Migration `0009`'s `frozen`-state
`CHECK` additionally requires nine content digests to be non-`NULL` at freeze —
`candidate_snapshot_sha256`, `input_observation_set_sha256`, and the seven `candidate_*_sha256`
columns — **none of whose preimages any accepted record freezes** (see OR-1).

---

## D. Hashing and canonicalization map

| Identity | Preimage frozen? | Where | Implemented? |
|---|---|---|---|
| `snapshot_id` | **NO** — Decision 016 §1 names its *inputs* in prose (coverage window, three policy versions, an input-observation-content hash) but fixes no `hash_table` name, field tuple, ordering, or serialization | D016 §1 | no |
| `coverage_window_sha256` | **NO** | — | no |
| `input_observation_set_sha256` | **NO** — Decision 016 §1 describes it as a hash of the cited `census_source_observations` content. Whether it is the *same* digest as Decision 021 §8.1's `source_observation_set_sha256` is **not established by any accepted record**, and the two are computed at different times: §8.1's cited set is derived from `pilot_candidate_*_evidence` rows that exist only after the snapshot row, while migration `0009` requires this column from `INSERT` onward because `snapshot_id` depends on it. Settling that relationship is part of OR-1 | D016 §1; `0009` column comment | no |
| `candidate_entity_table_sha256`, `candidate_accession_table_sha256`, `candidate_registrant_table_sha256`, `candidate_entity_evidence_sha256`, `candidate_accession_evidence_sha256`, `candidate_entity_reasons_sha256`, `candidate_accession_reasons_sha256` | **NO** — Decision 021 §8.2 deliberately **binds the declared digests rather than recomputing them**, and limitation **D021-L2** records that no accepted derivation exists to recompute against | D021 §8.2; D021-L2 | no |
| `candidate_snapshot_sha256` | **NO** | — | no |
| Entity tie-break / `selection_rank` | yes | D013 §6; D016 §7 | `entity_selector.selection_rank` |
| `accession_tie_break_sha256` | yes — exact formula | D018 §5.2 | `accession_selector.accession_selection_rank` |
| `entity_content_sha256`, `accession_content_sha256`, `selection_input_sha256`, `selection_run_id` | yes | D019 §10; D018 §26 | `accession_selection_store.py:1470`, `:1522`, `:1540` |
| Per-accession registrant-content digest | yes | D019 §6.6.1 | `_registrant_content_sha256` |
| `reserve_signature_sha256` / `replaces_signature_sha256` / `reserve_package_id` | yes | D016 §7; D020 §7 | `reserve_selector.py` |
| `selection_result_sha256` — fourteen fields, sorted by key, `pilot_selection_result` | yes | D021 §6.1 | `release/pilot_manifest.selection_result_sha256` |
| Eight manifest component digests | yes | D021 §§7.1–7.4, 8.1–8.4 | `release/pilot_manifest.py` |
| `root_manifest_sha256` — twelve fields, `pilot_root_manifest` | yes | D021 §9 | `release/pilot_manifest.root_manifest_sha256` |
| `manifest_id` — `pilot_manifest_identity` over `{root_manifest_sha256, ordinal_version, supersedes_manifest_id}` | yes | D021 §9.1 | `release/pilot_manifest.manifest_identifier` |
| Canonical JSON encoding and content-derived filename | yes | D013 §7; D021 §13.5 | `release/hashing.py`, `manifest_filename` |

**Substantive versus operational (Q2), already resolved.** Decision 021 §5 applies Decision 016 §8's
exclusions to every digest without exception — absolute paths, SEC identity, secrets, outcome values,
filing text, every free-text `detail`, every operational event ID, and **every timestamp column**;
§6.3, §9, and §13.4 name the excluded manifest approval and publication fields explicitly, and §13.4
excludes them from the document body as well. Decision 019 §10 adds the one deliberate inclusion:
`acceptance_audit_date` is a **calendar date and a frozen candidate classification input**, not a
timestamp, and is therefore inside identity. **No further ruling is needed for Q2.**

**No governed identity depends on physical SQLite bytes (CF5).** Every identity above is a logical
`hash_table` digest over normalized row content, sorted before digesting; `release/hashing.py`
touches no file. Neither the SQLite library version nor the physical page layout can reach any
governed identity, so the CI/local version difference Decision 066 observed (3.45.1 versus 3.53.4)
is **not** an identity-portability risk. It is a live risk only for a *durable-byte* equality
proof (OR-3), which is a proof standard rather than an identity.

---

## E. M3.2 evidence inputs allowed into M3.3

| Accepted M3.2 artifact | Status | Admissible as an M3.3 candidate input? |
|---|---|---|
| 76 stored raw objects, hash-valid, fully provenanced | accepted (Decision 065 §3) | yes, as the provenance root — **read-only** |
| 70 quarterly full-index objects, present and hash-valid | accepted | yes — read-only |
| `census_source_observations` — 77 authoritative rows | accepted | yes; also the source of Decision 021 §8.1's cited-observation set |
| Structural observations / schema fingerprints | accepted | yes, for Decision 021 §8.1's fingerprint partition rule |
| Audit projection 77/77 | accepted | yes, as evidence — never an identity input |
| `census_index_instances` | **empty by design** (`Milestones/STATUS.md`) and never a reason to re-request an index | **AVAILABLE-AS-NONE.** Its emptiness is not a blocker and it may not be populated artificially. The proposal's §D and §E trace it as a census planning/coverage table carrying no candidate-column content and therefore **NOT USED** by the builder — a proposal, not a ruling; OR-2 still governs |
| T6 failed run row, receipt, observations | immutable | **read-only, never mutated** |
| T7 completed receipt and run | immutable | read-only |
| Historical `stopped`, receiptless run | permanently non-resumable | read-only |
| The S4 entity-only draft | permanently `running` | **prohibited as an input** (Decision 021 §14; Decision 018 §6) |
| Outcome values, filing text, CompanyFacts, Frames | never acquired | **prohibited absolutely** (CLAUDE.md rules 4–5; Decision 015; L15/L19) |
| Pilot membership or stratification as a feature input | — | **prohibited absolutely** (Decision 015) |

**The exact table-and-column read set that produces each candidate column is not fixed by any
accepted record.** That is OR-2, and it is the substance of the master plan's M3.3 §5 required owner
decision 3.

---

## F. Limitations classification for M3.3

Classification: `BLOCKING M3.3 ENTRY`, `BLOCKING REAL SNAPSHOT`, `BLOCKING REAL SELECTION`,
`BLOCKING MANIFEST/ROOT`, `NONBLOCKING CARRY-FORWARD`, `HISTORICAL / ALREADY DISCHARGED`.
**No limitation is closed by this document, and Gate H passing closes none of them.**

| ID | Status in register | M3.3 classification | Why |
|---|---|---|---|
| D020-L1 … D020-L5 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Methodological consequences of the accepted reserve architecture; each changes which rows exist, and M3.3 hashes rows as persisted (Decision 021 §19.1) |
| D021-L1 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Carries the six S5-era limitations forward unchanged |
| **D021-L2** | `ACTIVE` | **BLOCKING REAL SNAPSHOT** | It records precisely the gap OR-1 names: `candidate_tables_sha256` binds declared digests because no accepted derivation exists. A real freeze cannot declare digests whose preimages are unfrozen. **Updated 2026-08-13:** accepted Decision 067 §9 **rules OR-1** and supplies the derivation, answering the entry's "Required owner action". The entry stays **`ACTIVE`** — closure additionally requires the implemented recomputation-and-comparison step, reviewed, which is unauthorized M3.3A work |
| **D067-L1** | `ACTIVE` | **NONBLOCKING CARRY-FORWARD** | New at Decision 067 §6.2 (**R15**). Candidate evidence and family digests are deterministic for the accepted **frozen** observation set, but Decision-016 candidate evidence identity is **not cross-reacquisition invariant**. Unreachable inside M3.3, which forbids reacquisition; **not repaired here**, and it grants **no** acquisition authority |
| D021-L3, D021-L4, D021-L5 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Deliberate defensive/diamond properties of accepted preimages |
| D021-L6 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | A sealed run without a manifest is not a publication — reinforces the M3.3/M3.4 separation |
| **D021-L7** | `ACTIVE` | **BLOCKING MANIFEST/ROOT** *(as an owner input, not a defect)* | The six Decision 021 §8.4 arguments are asserted, never verified. The real root cannot be constructed until the owner supplies them (OR-6) |
| D021-L8, D021-L9, D021-L10 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Fingerprint exclusions, attestation semantics, fixture weight |
| D021-L11 | `CLOSED` | HISTORICAL / ALREADY DISCHARGED | Closed by migration `0013` triggers 6–8 |
| D022-L1 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Item-46 applicability is per persisted package; E5 exercises it |
| **D023-O1** | `ACTIVE — OWNER RULING PENDING` | NONBLOCKING CARRY-FORWARD **until triggered**, then BLOCKING MANIFEST/ROOT | `LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED` (register closing note; Decision 030 Ruling E). Reaching it in E8 or in M3.3B is a **stop-and-refer**, never a resolution |
| D023-O2 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | The release root is assumed owner-controlled; symlink-resistant publication was never a requirement |
| D023-O3 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Atomicity governs artifacts the operation created; E7 tests exactly this |
| D023-O4 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Item-46 defence in depth |
| D024-L1, D024-L2 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Assignment is not authorization; every inherited control transfers unchanged |
| D026-L1 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Literature refresh is a publication obligation, not an M3.3 gate |
| **D026-L2** | `ACTIVE` | NONBLOCKING CARRY-FORWARD *(must be reported, never satisfied)* | The difficult-or-nonstandard-package quota stays `unproven`/`unavailable` at M3.3 and remains an M2.5 obligation (Decision 018 §14) |
| M3-L01 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Platform and filesystem assumptions |
| **M3-L02** | `ACTIVE` | NONBLOCKING CARRY-FORWARD, and **directly in scope at M3.3A** | Synthetic-fixture limitations: M3.3A runs on fixtures by design, so the gap between fixture and real shape is the phase's central residual risk |
| **M3-L03** | `ACTIVE` | NONBLOCKING CARRY-FORWARD, and **directly in scope at M3.3B** | First-real-instance uncertainty is exactly what M3.3B encounters |
| M3-L04, M3-L05 | `ACTIVE` | HISTORICAL for this phase | Live SEC availability and rate-limit behaviour; M3.3 issues zero requests |
| M3-L06 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Drift in *acquired* data is closed at Gate H; a stored payload failing its structural expectation in M3.3 is **blocking** by the master plan's §19, independently of this entry |
| M3-L07 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Interrupted-run uncertainty; the M3.3 interruption boundaries are OR-5 |
| M3-L08 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Operator-error risk |
| M3-L09 | `ACTIVE` | NONBLOCKING CARRY-FORWARD | Receipt-schema evolution; M3.3 adds `offline_execution` usage of the accepted `3.0` writer |
| M3-L10 | `ACTIVE` | HISTORICAL for this phase | Request-budget derivation; M3.3's ceiling is `0` |
| M3-L11, M3-L12, M3-L13, M3-L14, M3-L16 | `CLOSED` | HISTORICAL / ALREADY DISCHARGED | Closed by Decisions 029 §12 step 17, 048, 056, 059 |
| **M3-L15** | `ACTIVE` | **NONBLOCKING CARRY-FORWARD** | The second-SIGTERM latch belongs to the **live-acquisition** lifecycle. M3.3 runs no live acquisition, so the entry's stop condition — an edit to the scoped SIGTERM handling — is unreachable from an M3.3 path that touches no acquisition module. It is **not** discharged, and Gate H passing did not discharge it |

---

## G. Owner-ruling requests

Each is stated as a question. **None was answered by this inventory.** All twelve have since been
disposed of — **eight ruled** and **four deliberately deferred to named owner gates** (OR-6, OR-7,
OR-9, OR-11) — and accepted
[Decision 067](../Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md) added **four
further rulings**, R13–R16. **No owner ruling is open.** The dispositions are recorded in
[`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md) §1.1 and §1.2, which are the
current statement; the questions below are retained as the record of what was asked.

**Disposition, as at 2026-08-13 (after Decision 067):**

| ID | Disposition | Where the current statement lives |
|---|---|---|
| **OR-1** | **RESOLVED — OWNER RULED**, Decision 067 §9. The proposal's eleven-digest matrix adopted as the normative basis, with OQ-3/OQ-4/OQ-5/OQ-6/OQ-7/OQ-8 applied and expanded by R16 | Decision 067 §9; contract §10.1, §21 |
| **OR-2** | **RESOLVED — OWNER RULED**, Decision 067 §10. The proposal's 135-column mapping adopted as the normative basis, with eight mandatory GV2 corrections | Decision 067 §10; contract §8.1, §21 |
| **OR-3** | **RULED — R3** (durable-byte equality; true OS-level strictly-read-only connections; no writer lease; fail closed) | contract §1.1, §14 |
| **OR-4** | **RULED — R4** (Decision 065 §3 + the current STATUS record substitute; no token is emitted) | contract §1.1, §22 |
| **OR-5** | **RULED — R5** (one atomic construct-and-freeze transaction; a surviving `building` row blocks; no automatic recovery across an authoritative boundary) | contract §1.1, §11, §17, §32 |
| **OR-6** | **DEFERRED** to M3.3-E2 authorization; values stay caller-supplied | contract §1.2, §16 |
| **OR-7** | **DEFERRED** to after I/R evidence and A1 acceptance, before M3.3-E1 | contract §1.2, §12 |
| **OR-8** | **RULED — R8** (narrow hardening of actually-used paths only; no repository-wide cleanup) | contract §1.1, §14, §20 |
| **OR-9** | **DEFERRED** to Sol/GPT after a fresh A1 rehearsal acceptance | contract §1.2, §2 |
| **OR-10** | **RULED — R10** (fail closed; `infeasible_or_unproven` is never relabelled proven infeasibility) | contract §1.1, §12 |
| **OR-11** | **DEFERRED, Decision 023 retained exactly**; rehearsal must trigger it, real execution stops and returns | contract §1.2, §25 |
| **OR-12** | **RULED — R12; correction applied 2026-08-13** | contract §1.1; `Docs/architecture_map.md` §0, §10.1 |
| **R13** | **RULED**, Decision 067 §4 — bounded offline metadata parse prerequisite; `census_plan_sources.observation_id` binding; complete non-acquisition prohibition list. **Real execution separately gated at M3.3-E0** | Decision 067 §§4, 11; contract §1.1, §10.2 |
| **R14** | **RULED**, Decision 067 §5 — structural fingerprint non-vacuity; the parse must precede snapshot construction; a failed source is never a fabricated empty parse | Decision 067 §5; contract §1.1, §10.2 |
| **R15** | **RULED**, Decision 067 §6 — **ALT-3**, Decision 016 §4 retained exactly; bounded cross-reacquisition limitation **D067-L1** recorded, not repaired | Decision 067 §6; contract §1.1, §25; register **D067-L1** |
| **R16** | **RULED**, Decision 067 §7 — `evidence_sha256` call shape and the eight candidate `*_resolution_sha256` derivations; tie-break hashes unchanged; contributor membership clarified by **R16-C1** | Decision 067 §7; Decision 068 §8; contract §1.1, §10.1 |
| **R16-C1** | **CLARIFIED**, Decision 068 §8 — contributor membership is substantive, mechanical, independently recomputable, and exposed by I/R through one explicit deterministic membership selection; an undeterminable set stops and refers | Decision 068 §8; contract §1.1, §26 item 3 |
| **R17** | **RULED**, Decision 068 §3 (adopting review finding MAJ-1) — the E0 permitted persistence footprint is exactly fifteen tables, mechanically verified against the reusable persistence path; `census_qa_metrics` and every index-side table excluded; no second writer | Decision 068 §3; contract §1.1, §10.2 item 2, §19 |
| **R18** | **RULED**, Decision 068 §4 — report-level per-planned-source E0 dispositions A/B/C; **superseded on one point by accepted Decision 072 R22 — `sec_full_index_company` is candidate-substantive A/B, never C**; the 70 full-index sources are category C; no fabricated parse and no `parser_state` mutation for category C; no schema enum, no migration | Decision 068 §4; contract §1.1, §10.2 items 6 and 14 |
| **OQ-3 / OQ-4 / OQ-6 / OQ-8** | **PREVIOUSLY FROZEN BY THE OWNER; first recorded in the repository by Decision 067 §8** — fail closed on a same-catalog `snapshot_id` collision; `snapshot_id` excluded from the seven family digests; `coverage_policy_version` = `pilot-coverage/1.0`; evidence roles `winning` / `competing` / `supporting` | Decision 067 §8; contract §10.1 |

**The OR-1 and OR-2 proposal** is
[`m3_3_snapshot_authority_adjudication_proposal.md`](m3_3_snapshot_authority_adjudication_proposal.md),
now `PROPOSAL — OWNER-DISPOSED BY ACCEPTED DECISION 067 — HISTORICAL PROPOSAL EVIDENCE, NO
AUTHORITY`. Its matrices were **adopted as the normative bases**, subject to the owner's corrections;
**it is still not itself an authority**, and a session cites Decision 067 or the contract, never the
proposal.

| ID | Question | Why existing authority does not settle it | Blocks |
|---|---|---|---|
| **OR-1** | What are the exact canonical preimages — `hash_table` name, frozen field tuple in order, serialization, and inclusion/exclusion list — for `snapshot_id`, `coverage_window_sha256`, `input_observation_set_sha256`, the seven `candidate_*_sha256` digests, and `candidate_snapshot_sha256`? | Decision 016 §1 fixes the *inputs* in prose only. Decision 021 §8.2 explicitly binds the declared digests rather than recomputing them, "because recomputing them would be a second implementation of a snapshot-freeze derivation that does not yet exist". Limitation D021-L2 records the same absence. Migration `0009` nevertheless requires all nine at freeze | **M3.3A implementation** and every later step |
| **OR-2** | Which accepted M3.2 tables and columns may the builder read, and what is the exact deterministic mapping from that read set to each `pilot_candidate_*` column — including `base_eligible`, `support_eligible`, `size_stratum`, `industry_family`, `history_class`, `primary_universe_eligible`, cohort assignment, and `acceptance_audit_date`? What is the disposition of `census_index_instances`, which is recorded empty by design? | Decisions 013, 014, 016, and 019 fix the *representation* the builder must produce; no accepted record fixes the *derivation* that produces it. This is the master plan's M3.3 §5 required owner decision 3, in its exact terms | **M3.3A implementation** |
| **OR-3** | What is the proof standard for "write-free"? Durable-byte equality of every pre-existing artifact including the main SQLite file (the Decision 066 R1 standard), or logical-row equality? Which connection mode must each M3.3 read path use, and does the writer lease apply to a read-only M3.3 path? | Decision 066 R1's generality is stated as "**general for `reconcile-requests`**"; it does not extend itself to M3.3. Decision 021 §§11.3, 12 say replay "never writes" in the sense of issuing no statement. Rehearsal E8 demands persisted state "**byte-identical** before and after each replay". Those two readings differ exactly where a read-write handle checkpoints on close | **M3.3A rehearsal design**; M3.3B replay proof |
| **OR-4** | What is the smallest ruling that removes the Gate-H precondition contradiction without inventing a retroactive historical token? | Gate H is passed and owner-accepted (Decision 065 §3), and `Milestones/STATUS.md` already records that "**No Gate H phase token emission is claimed by any record**". The master plan's M3.3 §6 and the runbook's §29 still name the token as a precondition. Which durable proof substitutes for it is an owner act | **M3.3 contract acceptance** |
| **OR-5** | What is the authoritative state after an interruption at (a) snapshot freeze, (b) selection persistence, (c) sealing, (d) manifest construction — and who may invalidate or supersede a snapshot? | (b)–(d) are enumerable from migration `0013` and the master plan's §28. For (a), migration `0009`'s guards make a surviving `building` row possible and undeletable-once-frozen, but no accepted record says whether a surviving `building` row may be completed, must be invalidated, or is a stop condition; and the master plan's §27 says a wrong snapshot is superseded "under explicit authorization" without naming the instrument | **M3.3A rehearsal (E1/E7)**; M3.3B |
| **OR-6** | What exact values are supplied for the six Decision 021 §8.4 explicit arguments at the real M3.3B run, and which decision records enter `decision_authority_sha256`? | §8.4 forbids inferring any of them from Git, the environment, the interpreter, the config, or the working tree; limitation D021-L7 records that they are asserted, not verified. Enumerating the in-force decision set is an owner act | **M3.3B manifest/root** |
| **OR-7** | What is the exact `node_limit` for the real M3.3B run? | Decision 018 §17 declines to freeze a production default, makes it an explicit run input, and puts it inside run identity — so choosing it visibly changes `selection_run_id` | **M3.3B selection** |
| **OR-8** | Must the CF4 strict read-only hardening land **before** M3.3-I/R? | `read_only_connection` (`storage/catalog.py:84`) is read-only by convention on a read-write OS handle. Whether any M3.3 path may use it, or whether every M3.3 read path must use `strictly_read_only_connection`, is a scope decision that interacts with OR-3 | **M3.3-I/R entry** |
| **OR-9** | Authorization to proceed from M3.3A to M3.3B, separate from contract acceptance | Master plan M3.3 §5 required owner decision 2 — pre-declared as a separate owner act, "not implied by the builder working" | **M3.3B** |
| **OR-10** | A ruling if the real candidate universe cannot satisfy the frozen design | Master plan M3.3 §5 required owner decision 5. M3.3B **fails closed** and reports binding constraints; it never relaxes a quota | **M3.3B**, on the infeasible branch |
| **OR-11** | A ruling if D023-O1 is reached | Master plan M3.3 §5 required owner decision 4; Decision 023 §7 O1 makes it stop-and-refer | **M3.3A E8 / M3.3B**, if triggered |
| **OR-12** | Should the stale current-state claims in `Docs/architecture_map.md` be corrected in a bounded pass before M3.3-I/R? | Found by the semantic-consistency review this packet's §11 requires; outside this session's authorized edit set. See §K | **nothing** — but it is a live contradiction on a navigation surface |

---

## H. Known rule interactions

| # | Interaction | Resolution as it stands |
|---|---|---|
| H1 | **Snapshot declared digests versus recomputed candidate content.** `candidate_tables_sha256` binds *declared* digests (Decision 021 §8.2); `selection_input_sha256` binds *actual* row content and is re-derived at reconstruction | Row content is proven by the second path, not trusted by the first. **OR-1 has since fixed the first** (accepted Decision 067 §9; contract §10.1), which is what migration `0009` needs to permit a freeze at all. **D021-L2 stays `ACTIVE`** until the recomputation-and-comparison step is implemented and reviewed |
| H15 | **The candidate mapping depends on a parse layer that is empty.** Decision 067 §2.1 records `census_structural_observations` and the whole census parse family as **empty**, with `parser_state` `not_started` for all 76 plan sources | Owner Ruling **R13** — a bounded **offline metadata parse** over the already-accepted stored objects is the **prerequisite**, binding every source through `census_plan_sources.observation_id`, with no network, no transport, no reacquisition, and no fabrication. **R14** forbids skipping it and using a uniformly empty structural fingerprint instead. **This is not an acquisition authority**, and the *real* parse is separately gated at **M3.3-E0** with an owner gate on each side |
| H16 | **Evidence identity binds uuid4 provenance, yet M3.3 must be deterministic** | **GR-C2 / R15.** A **reparse** of the same accepted observation is deterministic; only **re-retrieval** mints a new `source_observation_id`, and M3.3 forbids reacquisition — so the accepted M3.2 values are frozen provenance constants here. The residual cross-reacquisition asymmetry is recorded as **D067-L1** and **not repaired** |
| H2 | **`acceptance_audit_date` is inside identity while every timestamp is outside it** | Decision 019 §10 states which side of Decision 016 §8 the column falls on; it is a calendar date and a classification input, not a timestamp. No conflict |
| H3 | **Plain accession is FK identity; dashed accession is canonical for hashing and presentation** | Decision 018 §5.1; both must agree and disagreement fails closed (§5.3). E2 exercises it |
| H4 | **Amendment family identity is diagnostic, not identifying** | Decision 018 §10.3 keeps it out of the tie-break and out of `selected_order`, so a later M2.5 parentage correction cannot move a frozen manifest hash. Parentage still enters candidate content hashing |
| H5 | **Zero compatible reserves must not make a feasible run manifest-ineligible** | Decision 020 §7.1 plus Decision 022; `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` is `blocks_release=False`. Item 46 is structurally not applicable for a disposition-only target; item 70 remains total coverage. E5 exercises all three variants |
| H6 | **Sealing is append-once and precedes the manifest write, in its own transaction** | Decision 021 §11.3; migration `0013` trigger 2. An identical re-seal is idempotent; a differing seal is refused |
| H7 | **`manifest_id` commits `ordinal_version` and `supersedes_manifest_id`; the root does not** | Decision 021 §10.1 — deliberately, so two ordinal versions of identical content share a root. At M3.3 `supersedes_manifest_id` is always `NULL` (§11.1) |
| H8 | **Approval and publication state must not touch substantive identity** | Decision 021 §§6.3, 9, 13.4 exclude every approval and publication field from every digest **and** from the document body. Constructed and verified ≠ approved (Q8, settled) |
| H9 | **The receipt records identities but is never an input to a digest** | Master plan M3.3 §22 — the direction is one-way. Architecture map §0 rule one says the same |
| H10 | **Node limit is in run identity, so choosing it is a methodology-visible act** | Decision 018 §17 + OR-7 |
| H11 | **Decision 066's read-only rule versus M3.3's write-free replay** | Decision 066 R1 is scoped to `reconcile-requests`. The M3.3 standard is OR-3. The mechanism is available either way: `strictly_read_only_connection` exists and every accepted S5/S6 entry point takes a caller-supplied connection, so M3.3 chooses the handle per path |
| H12 | **Gate H accepted, Gate-H token never emitted** | CF1 / OR-4. `Milestones/STATUS.md` already records that no record claims a Gate H phase-token emission, which is the durable proof that exists today |
| H13 | **A completed contract authorizes nothing further** | `Milestones/contracts/README.md`. `m3_2.md` cannot start any part of M3.3, and neither can the `m3.2-complete` tag |
| H14 | **The S4 draft is excluded twice** | Decision 021 §§11.2(6), 14, and — at the schema layer — because migration `0013` refuses a manifest over a run that is not `feasible`, and the draft is permanently `running` |

---

## I. Rehearsal coverage map (E1–E8)

Source: [`Docs/m3/offline_rehearsal_spec.md`](offline_rehearsal_spec.md) Part II §§7–9. **None has
been implemented or executed.**

| Scenario | Covers | Exercises which accepted code | New harness work |
|---|---|---|---|
| **E1** | Deterministic snapshot construction and freeze; identical `snapshot_id` from identical inputs; declared digests agree with actual rows | migration `0009` guards | the **new builder** |
| **E2** | Every Decision 019 §9 obligation violated in isolation, non-vacuously; plain/dashed disagreement | `load_frozen_joint_candidates` validators | fixtures per obligation |
| **E3** | Feasible joint selection; roles; `selected_order`; objective order | `solve_joint_selection`, `execute_and_persist_joint_selection` | fixtures |
| **E4** | Infeasible and node-limit fail-closed; no quota relaxed; run preserved in its failed state | selector failure semantics (Decision 018 §17) | fixtures |
| **E5** | Reserve and disposition totality across three variants; item 46; item 70 | `build_reserve_packages`, `_persist_reserve_dispositions` | fixtures |
| **E6** | Reconstruction mismatch refusal across every `JointSelectionRunIdentity` field; both entry points equally strict | `reconstruct_persisted_joint_selection`, `execute_and_persist_joint_selection` | corruption fixtures |
| **E7** | Seal and manifest atomicity under six fault variants; D023-O3 pre-existing-file behaviour | `seal_selection_result`, `build_and_persist_pilot_manifest`, `verify_pilot_manifest` | fault injection |
| **E8** | Write-free replay; two clean rebuilds → identical root; identical re-seal idempotent, differing seal refused; **D023-O1 fails closed and is referred** | manifest replay path; crosswalk completeness | replay harness + the O1 fixture |

**Pass criteria (spec §9), all nine:** every scenario implemented and executed with none skipped,
`xfail`ed, or disabled; observed equals expected field by field; every reason code registered; no
socket opened; **no accepted S4, S5, or S6 module modified to make a scenario pass**; E8 reproduces
the identical root from unchanged state; E8's O1 fixture fails closed and is referred; a whole
re-run reproduces the same results; and the M3.3A independent review passes.

---

## J. Current test coverage map

| Area | Existing module | M3.3 disposition |
|---|---|---|
| Joint selector (S5.1) | `tests/unit/test_m23_accession_selector.py` | run as **regression, unedited** |
| Selection persistence (S5.2) | `tests/unit/test_m23_accession_selection_store.py` | regression, unedited |
| Reserves (S5.4) | `tests/unit/test_m23_reserve_selector.py` | regression, unedited |
| Entity selection (S4) | `tests/unit/test_m23_entity_selector.py`, `test_m23_entity_selection_store.py` | regression, unedited |
| Manifest pure layer (S6) | `tests/unit/test_m23_pilot_manifest.py` | regression, unedited |
| Manifest persistence (S6) | `tests/unit/test_m23_pilot_manifest_store.py` | regression, unedited |
| Schema and the eight `0013` triggers | `tests/unit/test_m23_pilot_schema.py` | regression, unedited |
| Migration chain provenance | `tests/unit/test_migration_provenance.py` | regression; must stay green with **no** new migration |
| M3 CLI surfaces | `tests/integration/test_m3_cli.py` | extended only for a new M3.3 subcommand; **`test_a_transition_aware_reconciliation_writes_only_its_report` is normative and may never be weakened** (Decision 066 R2) |
| No-network guarantee | `tests/integration/test_no_network.py` | regression; M3.3 must not open a socket |
| **Candidate-snapshot builder** | **none** | **NEW** module and test module |
| **E1–E8 rehearsal harness** | **none** | **NEW** |

Per `Docs/change_impact_map.md`, a change touching the manifest layer runs
`test_m23_pilot_manifest.py`, `test_m23_pilot_manifest_store.py`, `test_m23_pilot_schema.py`, and
`test_migration_provenance.py` plus `make sqlite-check`; a change touching the selection stores adds
the S5.1 and S4 regression suites.

---

## K. Decision 066 carry-forward findings

| ID | Finding | Determination for M3.3 | Action now |
|---|---|---|---|
| **CF1** | The Gate-H completion token `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` is named as an M3.3 precondition but was never emitted | **Surfaces that treat it as an operative M3.3 precondition:** `Docs/m3/operator_runbook.md:946` (the §29 snapshot-freeze precondition list) and `Milestones/milestone_03_master_plan.md:1464` (M3.3 §6). **Surfaces that name it historically, not as an M3.3 precondition:** master plan `:156`, `:1087`, `:1347`, `:1367` (M3.2's own outputs/token/next action), `Milestones/contracts/m3_2.md:557`, `Docs/m3/templates/gate_h_checklist.md:21` and `:326`, and `Docs/Decisions/decision_027…:154` (byte-unchanged history). **No emitter exists in `src/`**; `tests/integration/test_m3_cli.py:2471` is a *negative* control asserting a refused command must not print it. **An equivalent durable acceptance proof already exists**: Decision 065 §3's `M3_2_FINAL_OWNER_ACCEPTANCE` with Gate H owner-accepted, and `Milestones/STATUS.md`'s `M3_2_GATE_H_STATUS`, which states in terms that "No Gate H phase token emission is claimed by any record". The **smallest** ruling is therefore a one-line owner substitution — naming Decision 065 §3 as the precondition in place of the token, on the two operative surfaces only — with no historical text rewritten and **no token emitted** | **RULED — R4, 2026-08-13.** The Decision-065/STATUS proof is the operative precondition; **no token is emitted, then or ever**. Under R12's companion correction the two operative surfaces (`Docs/m3/operator_runbook.md` §29 and `Milestones/milestone_03_master_plan.md` M3.3 §6) now cite that proof; **every historical reference listed at left is preserved byte-unchanged**, including the `tests/integration/test_m3_cli.py` negative control |
| **CF2** | Limitations mention Gate-H closure evidence; **M3-L15** remained `ACTIVE` at closeout | Classified in §F. **M3-L15 is `NONBLOCKING CARRY-FORWARD`** — it guards the live-acquisition SIGTERM latch, and M3.3 runs no live acquisition. **No limitation is closed by this document, and none is closed merely because Gate H passed** | none |
| **CF3** | `_refuse_inconsistent_recorded_chain` (`src/disclosure_drift/m3/acquisition.py:685`) builds `f"file:{database_path}?mode=ro"` without URI-quoting the path; a path containing `?` or `#` may be misparsed | **Relevant to M3.3?** Only indirectly. The function is an M3.2 catalog-preparation pre-flight, not an M3.3 path; M3.3 opens the catalog through `read_only_catalog` / `strictly_read_only_connection`, which use `Path.absolute().as_uri()` and are not affected. **Correctness/auditability blocker before I/R?** **No** — the accepted evidence root is an owner-chosen absolute path containing neither character, and the failure mode is a refusal, not a silent wrong answer. **Safely deferrable** to a later bounded hardening packet | **DEFER.** Not fixed here, as instructed |
| **CF4** | Some "non-writer" paths still open read-write OS handles and retain checkpoint-on-close capability | **Complete inventory at `e3e58f9`.** *Strictly read-only (`SQLITE_OPEN_READONLY`, cannot checkpoint):* `storage/catalog.py:100` `strictly_read_only_connection` → `storage/sqlite.py:96` `connect(read_only=True)`; `m3/recovery.py:141` `read_only_catalog`, used by `m3/acquisition.py:2415` (`reconstruct_catalog_state`), `:3888`, `:4413`, `:4605`, `m3/recovery.py:1675`, `:2569`, and `m3/rehearsal.py:1749`. *Read-write OS handle despite being a non-writer:* `storage/catalog.py:84` `read_only_connection` → `connect(writer=False)`, used at `cli.py:1310`, `cli.py:2185`, `cli.py:2274`; and `storage/sqlite.py:626` `backup_database`, which at `:633` opens the source through `connect(source)` — read-write — and the destination through `with sqlite3.connect(destination) as target:`, the exact pattern Decision 066 §5 identified as governing the *transaction* rather than the connection, so that handle closes only at garbage collection. **Will any be used by M3.3?** Every accepted S5/S6 entry point — `load_frozen_joint_candidates`, `execute_and_persist_joint_selection`, `reconstruct_persisted_joint_selection`, `seal_selection_result`, `build_and_persist_pilot_manifest`, `verify_pilot_manifest` — takes a **caller-supplied** `sqlite3.Connection`, so **M3.3 chooses the handle for every path**. The three `read_only_connection` call sites are CLI status helpers (latest-migration name, retrieved index instances) that an M3.3 command could reach incidentally. **Determination:** **R3 does set a durable-byte proof standard**, so strict read-only hardening of the actually-used paths is required before M3.3-I/R: every M3.3 read path must be bound to `strictly_read_only_connection`, and any status helper an M3.3 command touches must be too | **RULED — R3 and R8, 2026-08-13.** R3 sets the standard: durable-byte equality, a **true OS-level strictly-read-only** connection on every governed M3.3 read path, and **no writer lease** — so `read_only_connection` is not admissible for a governed M3.3 read, and the three CLI status-helper call sites are in scope wherever an M3.3 command can reach them. R8 authorizes M3.3-I/R to harden **narrowly, only the paths M3.3 actually uses**, and forbids a repository-wide cleanup of unrelated M2/M3.2 call sites. **No fix is implemented by this inventory** |
| **CF5** | CI SQLite 3.45.1 versus local 3.53.4 | **No proposed substantive M3.3 identity depends on physical SQLite file bytes or on version-specific serialization.** Every governed identity is a logical `hash_table` digest over `normalize_value`-rendered rows, sorted before digesting (Decision 021 §5; `release/hashing.py`). The existing canonical logical serialization rules are already governed and are reused unchanged; **no new serialization is invented**. The version difference bears only on a *durable-byte* replay proof, which is OR-3 — a proof standard, not an identity | **No owner ruling required on identity portability.** Folded into OR-3 and therefore settled by **R3**, whose durable-byte proof standard is where the version difference actually bears |

### Additional finding from the §11 semantic-consistency review

The packet's §11 requires a semantic consistency review beyond any supplied phrase list. Running one
across the current-state governance surfaces produced one finding outside CF1–CF5:

**`Docs/architecture_map.md` carries stale current-state claims that the Decision 065 closeout
synchronization did not reach.** In §0's Milestone 3 row (line 26) and in §10.1's `Status` bullet
(line 418), the map states as **current** that "combined T2.5–T2.6 is owner-gated, unauthorized, and
not begun", that "T3 implementation acceptance has not occurred", that "no … real operational
catalog, receipt, real snapshot …exists", that "no live SEC access has occurred", and that "Gate F
execution has not begun". Each is contradicted by accepted Decisions 046, 049, 063, 064, and 065.
Neither passage carries the historical marker that `Milestones/STATUS.md` and
`Milestones/contracts/README.md` use where they preserve pre-acquisition text — both read as live
state. §10's own heading was updated at closeout ("M3.2 complete and owner-accepted"), which makes
the two unsynchronized passages an omission rather than a deliberate preservation.

This is **not** an authority defect — the architecture map is explicitly a navigation aid and never
an authority (CLAUDE.md; the map's own header) — but it is exactly the class of stale current-state
contradiction Decision 065's broader closeout scan found after a bounded phrase-list audit had
passed, which is why the M3.3 contract requires **both** a bounded residue scan and an independent
semantic review. `Docs/architecture_map.md` was outside *this inventory's* authorized edit set, so the
finding was **reported, not corrected**.

**Now closed by Owner Ruling R12.** The owner's M3.3-GR packet of 2026-08-13 ruled that the stale
**current**-state claims be corrected before M3.3-I/R, scoped to `Docs/architecture_map.md` §0's
Milestone 3 row and §10.1's current `Status` bullet, preserving historical stage-era text as
historical and rewriting no architecture. **The correction was applied on 2026-08-13** under that
ruling. The paragraph above is retained as the record of the finding.

---

## What this document does not do

It accepts nothing, approves nothing, and freezes nothing. It creates no snapshot, runs no selector,
persists no selection, seals no digest, constructs no manifest, and computes no root. It authorizes
no implementation, no network access, and no M3.4 work. It closes no limitation. It resolves none of
OR-1 through OR-12, and a future session may not read an entry in the tables above as a ruling: the
governing record each row cites is the authority, and this map is only the index to it.
