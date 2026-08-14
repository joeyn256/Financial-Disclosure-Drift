# M3.3-I/R Implementer Rehearsal Evidence — frozen target `6f87abc`

```text
ARTIFACT: IMPLEMENTER REHEARSAL AND EVIDENCE RECORD — NOT AN INDEPENDENT ACCEPTANCE REVIEW
DATE: 2026-08-14
AUTHOR: the implementing session (Claude Opus 5, maximum effort, single fresh epoch)
AUTHORITY: accepted Decision 070, governed by accepted Decisions 071, 072, 073, and 074

IMPLEMENTATION_REHEARSAL_READY: YES
REAL_BUILDER_FEASIBILITY_PROVED: NO
REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE: OPEN
REAL_LINKED_AMENDMENT_FEASIBILITY_GATE: OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY: PENDING FUTURE AUTHORIZED E0 VERIFICATION
REAL_PRIVATE_PARSE_AUTHORIZATION: NO

M3.3-E0: NOT AUTHORIZED
M3.3-E1: NOT AUTHORIZED
M3.3-E2: NOT AUTHORIZED
M3.4:    NOT AUTHORIZED

NETWORK: NONE   SEC: NONE   REACQUISITION: NONE   MIGRATION: none   REQUEST_CEILING: 0
```

**This is the implementer's own evidence record.** It is **not** an independent review and it
accepts nothing. The next act is an independent read-only review of the frozen target below, then a
fresh independent I/R acceptance, then a **separate** Sol/GPT resolution of **both** open real-path
feasibility gates — and only then any consideration of real E0 authority.

---

## 1. Frozen executable target

| Fact | Value |
|---|---|
| Implementation commit | `6f87abc6a8601bb5dc9029d2b113351e34f9e948` |
| Tree | `f1dc77269eeac12f4fd2432d5aa4e45acbcd28f1` |
| Parent | `882dec057d7446faedd45e3528c77a14051598c8` |
| Branch | `main`, `HEAD == origin/main`, working tree clean |
| `m3.2-complete` | unmoved (tag object `2865a1479e4576dc18a4098c928b278812f38d00`) |
| Migration chain | `0001`–`0013`, unchanged — **no migration was created** |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

## 2. Governing records

Accepted **Decision 070** is the bounded I/R implementation-and-rehearsal authority and supplies
`PILOT_COVERAGE_POLICY_VERSION`'s executable home. Accepted **Decision 071** rules **R19**–**R21**
and disposes IN-2–IN-5. Accepted **Decision 072** rules **R22**–**R26**. Accepted **Decision 073**
rules **R27**–**R30**. Accepted **Decision 074** rules **R31**–**R34**, accepts IMP-1/2/3, and
extends the mutation campaign to M1–M38.

## 3. Track A — builder-derived integrity

Track A runs the **real production path** end to end: synthetic accepted-shaped stored objects →
`run_offline_metadata_parse` → `build_and_freeze_candidate_snapshot`. No stub stands in for the
builder, the parser, the persistence path, or the loader.

| Proved | Evidence |
|---|---|
| Offline parse, no request, no transport | parse report `requests_made 0`, `transports_constructed 0` |
| **R18** dispositions | 28 planned sources: 26 category A, 1 category B preserved unavailable, 1 category C **deliberately untouched** with `parser_state` unmutated |
| **R17** containment | SQLite authorizer refuses at statement-prepare time; M23 kills any write outside the fifteen-table footprint |
| **R22**–**R25** | `sec_full_index_company` category A/B; 213 registrant observations materialized from stored `company.idx` |
| **R23** multi-registrant | 2 associated registrants and 2 `multi_registrant` accessions, established only from index rows |
| **R19** / **R20** / **R26** | 24 entities classified; controls one per frozen kind; RIC/ETF SIC exactly `{6722, 6726}` |
| **R21** XBRL composite | both persisted flags bound through the existing canonical-JSON serializer |
| **OR-1** / **OR-2** | eleven-digest graph recomputed from persisted rows inside the freeze transaction |
| **R5** atomicity | four injected faults, each leaving **no** partial authoritative snapshot |
| Determinism | two builds over identical synthetic inputs share one `snapshot_id` and one `candidate_snapshot_sha256` |

**Required negative result, proved mechanically:**

```text
BUILDER_DERIVED_SELECTION_DISPOSITION = INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE
```

The persisted run reaches `infeasible`, and the binding-constraint set is exactly
`("amendment_purpose_categories",)` — **no other quota is short**. The builder was **not** modified
to make Track A feasible: no purpose classifier was added, no quota disabled, no unproven row made
quota-contributing, no fixture purpose injected into the production builder, and the selector is
untouched.

## 4. Track B — explicitly governed feasible rehearsal

Track B derives through the **production** `derive_candidate_snapshot`, applies an amendment-purpose
overlay **only**, and persists through the **single** authoritative persistence routine. It uses the
same accepted selector, the same quota definitions, the same objective, the same role rules, the
same caps, the same persistence, the same reconstruction, the same seal, and the same manifest
machinery. There is no test selector, no selector-mode bypass, no removed quota, and no patched
requirements map.

Result: `feasible`, 24 selected entities, 38 selected accessions.

**Unreachability from production**, proved by test: importing
`disclosure_drift.m3.candidate_snapshot` loads **none** of the rehearsal modules; the builder's
source contains neither the overlay module name nor the `SYNTHETIC_REHEARSAL_ONLY` label; and the
production builder has no hook, flag, or fallback that reaches an overlay.

```text
FEASIBILITY SOURCE: EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT
```

## 5. R28 bridge

Paired siblings from **one** synthetic base case, compared **mechanically before** any selector
execution, across five candidate row families at their identity column tuples, both reason families
as sets, and 21 snapshot fields.

**48 differences observed, 0 violations.** All 48 sit inside the explicit allowlist: nine amendments
× four amendment-purpose columns, nine `REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN` reason rows absent
on the Track-B side, and three transitively affected digests. Entity rows, registrants, evidence,
reason rows, full-index facts, cohorts, roles, eligibility, XBRL, linkage, `multi_registrant`,
support/base facts, and the 2009/2010 pair facts are **identical**.

Adversarially tested: three independent unrelated divergences introduced in the **census input** and
rebuilt (a size stratum, an inline-XBRL flag, a registrant CIK) each **fail** the bridge, and the
mutation campaign kills both a permit-everything bridge (M26) and a widened allowlist (M27).

## 6. E1–E8 matrix, at the accepted Decision 073 track assignment

| Scenario | Track | Feasibility source | What it proves | Result |
|---|---|---|---|---|
| **E1** | A | `BUILDER_DERIVED` | offline parse, R18 A/B/C, deterministic freeze, immutability, four-fault rollback | **PASS** |
| **E2** | A | `BUILDER_DERIVED` | five isolated freeze refusals, each for its own reason, plus the OQ-3 rebuild | **PASS** |
| **E3** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | feasible selection; six distinct pair entities | **PASS** |
| **E4** | A | `BUILDER_DERIVED` | `INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE`; node-limit exhaustion reported as `infeasible_or_unproven`, never as proven infeasibility; no seal, no manifest | **PASS** |
| **E5** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | **R31**: (a) the positive compatible path at the pure reserve layer; (b) zero-compatible totality; (c) mixed totality | **PASS** |
| **E6** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | all six governed `JointSelectionRunIdentity` components refused | **PASS** |
| **E7** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | seal/manifest atomicity; deleted, truncated, and byte-modified documents refused with the row unchanged; a write fault leaves no row and the seal intact | **PASS** |
| **E8** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | write-free replay, identical root, two clean rebuilds, Decision 023 **O1** fail-closed and referred | **PASS** |

Committed-target run: all eight pass, evidence reference
`m3-3a-execution-rehearsal-report-516cd77e8a7b1581d1511dcd9024536446e7e0a013c5039cb4d98c22fb950514`,
receipt `ca83170f8e1a71349daba4a419f2cf4209ac9f73a92acb17eabc1511224973f8`, token
`M3_3A_EXECUTION_REHEARSAL_PASSED_NO_REAL_EXECUTION_AUTHORIZED`.

```text
ACCEPTED_SELECTOR_FEASIBLE_ON_CONFORMING_EXPLICIT_REHEARSAL_SNAPSHOT = YES
BUILDER_DERIVED_SELECTION_DISPOSITION = INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE
```

**These coexist by design. Track-B success does not imply real feasibility.**

## 7. E5 under corrected R31

* **(a)** the positive compatible-reserve path, proved at the **pure** reserve layer without
  invoking the pilot-scale joint selector: exactly one `reserve_rank = 1` package; deterministic
  ranking under a reversed pool; target/replacement disjointness; recomputed signature equality on
  both sides; a **superset** bundle rejected; and, with no compatible replacement, exactly one
  deterministic disposition;
* **(b)** an end-to-end feasible run in which **zero** targets have a compatible reserve: 24 targets,
  0 packages, 24 dispositions, `running -> feasible`, one outcome per target, no overlap;
* **(c)** an end-to-end **mixed** run: 24 targets, 6 packages, 18 dispositions, total coverage, no
  overlap, no invented rank.

No production reserve rule was altered; no accession was dropped from a replacement's whole bundle;
the selector objective and the selected bundle are unchanged.

## 8. I7 — the accepted downstream machinery, reused

Frozen-candidate load through the accepted Decision 019 S5.2 mapping; the accepted joint-selector
input and the **single** accepted selector; the pair rule verified on the **joint result**;
persistence through the accepted store in its own `running` window; independent reconstruction;
write-free replay; the seal in its own prior transaction; manifest construction, verification, and
identical-root replay; crosswalk **item 80** delivered as the sanitized command-invocation renderer.
`release/pilot_manifest.py`, `sec/pilot_manifest_store.py`, `sec/accession_selector.py`,
`sec/accession_selection_store.py`, `sec/reserve_selector.py`, `sec/entity_selector.py`, and
`sec/entity_selection_store.py` are **byte-identical** to the parent commit.

## 9. 2009/2010 pair wiring

Six **distinct** entities, each contributing a selected SUPPORT-role 2009 original `10-K` that is
explicitly pre-study and a selected BASE-role 2010 original `10-K` in the `development` cohort under
one anchor CIK, both in the **same** joint result, counted once per entity. Track A carries the same
pair facts and selects nothing, because it is infeasible. The pure rule and its full
single-condition negation matrix are unchanged.

## 10. Persistence, reconstruction, replay, seal, manifest

Reconstruction reproduces the persisted run; every governed `JointSelectionRunIdentity` component is
refused when corrupted — three by migration `0013`'s immutable-identity trigger, three by the single
centralized identity comparison. Replay is **write-free to the R3 standard**: the main database's
SHA-256 is identical before and after, every read uses `SQLITE_OPEN_READONLY`, and the handle's
refusal is **observed by probing a write**, not asserted. The seal is append-once in its own prior
transaction and survives a manifest fault. The manifest verifies and replays to an **identical root**
with byte-identical canonical JSON.

## 11. Decision 023 O1

Deliberately triggered: a required milestone-plan §10 item's **sole** serialized carrier family is
emptied and the accepted crosswalk coverage check is asked to place it. It **fails closed**, no
manifest row is added or deleted, and the condition is **referred, never resolved** — no item is
reclassified, no category added, no count changed, and no alternate carrier chosen.

## 12. Mutation campaign M1–M38

**All 38 killed. Zero survivors. Zero residual mutation. Positive control passing** on every test
selection before any mutation ran. Source isolation was enforced by in-memory byte restore in a
`finally` block; every touched file was re-verified against its entry SHA-256; and bytecode writing
was disabled so a restored file could not be shadowed by a stale `.pyc`.

Seven mutations initially survived. **Each was closed by a narrow added test, never by weakening the
mutation**: the RIC/ETF enumeration (M9), the foreign-private-issuer original-form rule (M11), the
accepted-unavailable source disposition (M25), the bridge allowlist decision (M26), the observed
strictly-read-only handle (M32), whole-bundle reserve compatibility (M35), and the self-referential
amendment parentage claim (M38). M32 additionally produced a **production** improvement: the replay
proof now probes the handle before applying `query_only`, so a convention-only reader is
distinguishable from an OS-level read-only one.

## 13. Committed-target validation

| Gate | Result | Elapsed |
|---|---|---|
| `ruff check .` | **All checks passed** | 0.07 s |
| `ruff format --check .` | **163 files already formatted** | 0.02 s |
| `mypy src` | **Success — 87 source files** | 0.27 s |
| `pytest` | **3948 passed, 1 skipped** (pre-existing skip) | 227 s |
| `make sqlite-check` | Python 3.12.13, SQLite 3.53.4 | 0.05 s |
| `make secrets` | **passed** — 342 files, 0 findings | 0.71 s |
| `make hygiene` | **passed** — 344 paths, 0 findings | 0.18 s |
| `make context` | clean tree, `HEAD == origin/main` | — |
| `git diff --check` | clean | — |

## 14. Determinism, network, and private-data proof

Two builds over identical synthetic inputs produce one `snapshot_id` and one
`candidate_snapshot_sha256`; two clean rebuilds from one frozen snapshot share a run identity and
select the same accessions; manifest regeneration reproduces the identical root and identical
document bytes. The offline parse reports zero requests and zero transports. No M3.3 module imports
`socket`, `httpx`, `urllib`, or the HTTP client, and none reads any environment variable — asserted
by AST inspection, not by promise. `EV_ROOT` is named only in prohibitions. **No private evidence,
no real catalog, no real snapshot, no real selection, no real manifest, and no real root was
touched, created, or read.**

## 15. Findings

| ID | Class | Disposition |
|---|---|---|
| **IMP-1** | implementation defect, corrected | `industry_quota_eligible` excluded the engineering-only stratum, making the operating-financial industry quota unsatisfiable **by construction** rather than by evidence. Corrected per Decision 016 §2; accepted by Decision 074 §7 |
| **IMP-2** | implementation defect, corrected | lineage `evidence_kind` values were translated to flag names before **R19** saw them, so §4.5 succession could never fire and an unauthorized §4.9 path existed. Corrected; accepted by Decision 074 §7 |
| **IMP-3** | implementation defect, corrected | candidate accessions were derived for every census accession regardless of the migration-`0009` `reference_form_types` foreign key, so an ordinary `10-D` or `8-K` would have failed the builder closed. Bounded by that reference family, with excluded counts reported; accepted by Decision 074 §7 |
| **BLK-2** | architecture finding, resolved | E5(a)'s universal-coverage requirement was production-invalid. Resolved by Decision 074 **R31** |
| **FND-1** | real-path condition | no accepted source field resolves `amendment_relationship`. Accepted as **R32**; gate **OPEN** |
| **FND-2** | implementation-order defect, corrected | `cohort_boundary_crossed` required an earlier persisted resolution. Corrected by **R33** as a same-build derivation; the fixture stipulation is removed |
| **FND-3** | verification condition | acceptance-date ordering adequacy on the real corpus. Recorded as **R34**; **PENDING FUTURE AUTHORIZED E0 VERIFICATION** |
| **OBS-G** | nonblocking | the private `_stable_id` import stands as owner-accepted; no public alias was created |
| **OBS-H** | covered | full-index corroboration reaches the registrant rows, and a full-index disagreement is a **diagnostic** that never overwrites the higher-authority value |

**BLOCKER 0 · MAJOR 0 · MINOR 0** for the implementation and rehearsal target. The two open
real-path gates are **not** implementation defects.

## 16. Authorization state

```text
M3_3_I_R_IMPLEMENTED_AND_REHEARSED_READY_FOR_INDEPENDENT_REVIEW
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```

**Success does not mean real feasibility, and it authorizes no real execution.** The next action is
to return to Sol/GPT for a frozen-target read-only review, a fresh independent I/R acceptance, and a
separate owner resolution of **both** real-path feasibility gates — which are never merged into one
flag. Only after that may real E0 authority even be considered.
