# M3.3-I/R Corrected-Target Rehearsal Evidence — frozen target `06bb47a`

```text
ARTIFACT: IMPLEMENTER CORRECTION AND REHEARSAL EVIDENCE RECORD — NOT AN INDEPENDENT REVIEW
DATE: 2026-08-14
AUTHOR: the correction-authoring session (Claude Opus 5, maximum effort, single fresh epoch)
AUTHORITY: accepted Decision 075, under accepted Decisions 070, 071, 072, 073, and 074

ULTRAREVIEW_FINDINGS_CORRECTED: MIN-1, MIN-2, MIN-3 — ALL CLOSED
OBSERVATION_STRENGTHENINGS_ADOPTED: OBS-1, OBS-3 — BOTH TEST-ONLY
CORRECTED_TARGET_REREVIEW_STATUS: NOT YET PERFORMED — PENDING FRESH READ-ONLY REREVIEW
FORMAL_ACCEPTANCE: NOT COMPLETE

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

**This is the correction author's own evidence record.** It is **not** an independent review and it
accepts nothing. It **supersedes** [`m3_3_i_r_rehearsal_6f87abc.md`](m3_3_i_r_rehearsal_6f87abc.md)
**only as evidence for the corrected executable target** — that artifact is byte-unchanged and
remains the historical implementer evidence for target `6f87abc`.

**The corrected target has not passed an ultrareview.** The next act is a **fresh read-only
ultrareview-rereview** against the corrected SHA; only if it returns **B0 / M0 / MIN0** does the
fresh independent formal-acceptance packet follow. **No E0.**

---

## 1. Corrected executable target

| Fact | Value |
|---|---|
| Corrected executable target | `06bb47a89eafc597c295a40eefd49cc71b50b0ec` |
| Tree | `360e778ddee91c6cf7388b93355fdcddf6442ca7` |
| Parent | `6b8968f3a9ea3502471d3e9efb1268ce8cdb7385` (the implementer evidence commit) |
| Original ultrareview target | `6f87abc6a8601bb5dc9029d2b113351e34f9e948` (tree `f1dc77269eeac12f4fd2432d5aa4e45acbcd28f1`) |
| Original ultrareview verdict | **BLOCKER 0 · MAJOR 0 · MINOR 3 · OPTIMIZATION 0 · OBSERVATION 6** |
| Branch | `main`, `HEAD == origin/main`, working tree clean |
| `m3.2-complete` | unmoved (tag object `2865a1479e4576dc18a4098c928b278812f38d00`) |
| Migration chain | `0001`–`0013`, unchanged — **no migration was created** |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

## 2. Governing record

Accepted **[Decision 075](../../Decisions/decision_075_m3_3_i_r_ultrareview_bounded_correction.md)**
records the ultrareview verdict, accepts its architectural conclusion **in full**, and authorizes
**only** the bounded corrections its three MINOR findings require. Decisions 070–074 remain accepted,
immutable, and controlling for everything they govern. **No architecture and no methodology was
reopened.**

Confirmed correct by the ultrareview and **not** reopened here: **R31** / **E5**, **R32**, **R33**,
**R34**, **IMP-1**, **IMP-2**, **IMP-3**, Track A, Track B, **R28**, the accepted joint selector,
the 2009/2010 pair, persistence / run identity / reconstruction, **R3** replay, the seal / manifest
separation, Decision 023 **O1**, the CLI real-gate refusals, and the network / private-data boundary.

## 3. MIN-1 — decision-index stale pointers — **CLOSED**

Two rows in [`Docs/decision_index.md`](../../decision_index.md) read as current while stating
positions later accepted records had moved.

| Row | Correction |
|---|---|
| **R18** full-index disposition | The category-**C** claim is now visibly superseded by accepted **Decision 072 §2 R22**, using the same narrow-supersession model the M3.3 contract already uses: `sec_full_index_company` is **candidate-substantive** — each plan-bound full-index source is category **A** when usable and category **B** when accepted unavailable, and **never category C**. R18's report-level disposition mechanics otherwise stand, and **Decision 068 is not rewritten historically** |
| `coverage_policy_version` | The row still records that Decision 067 §8 alone did not fix the executable home, and now carries the **current** pointer to accepted **Decision 070 §4**: `PILOT_COVERAGE_POLICY_VERSION` in `src/disclosure_drift/pilot_policy.py` at `pilot-coverage/1.0` — an engineering/provenance version only, with no config setting, no environment variable, no `reference_policy_versions` seed row, and no migration |

**The index was not restructured.** No other row was rewritten.

**The same two current-state questions were then closed across every surface §14 of the correction
packet names**, so a reader cannot land on an uncorrected statement: the decision registry (both the
Decision 068 index row's `Superseded by` column — which had recorded Decision 069 but **not**
Decision 072 — the Decision 067 row's executable-home clause, and the "controlling record by topic"
row for Decision 068), `Milestones/STATUS.md`, `Milestones/contracts/README.md`, the active M3.3
contract (its **R18** ruling-status row and its **OQ-6** row), and the master plan.

**Deliberately left byte-unchanged:** the `DECISION_068_STATUS` marker in `Milestones/STATUS.md`. It
is a **historical per-decision record**, and STATUS's own convention is that a later marker carries
the current position — `DECISION_072_STATUS` states the supersession explicitly and prominently.
Editing it would rewrite Decision 068's history, which Decision 075 §3.1 forbids.

## 4. MIN-2 — contract README links — **CLOSED**

The five Decision 070–074 links in the current-state banner of
[`Milestones/contracts/README.md`](../../../Milestones/contracts/README.md) used `../Docs/Decisions/…`
where the file's directory depth requires `../../Docs/Decisions/…`. All five are corrected.

Mechanically verified: **792 relative markdown links** across every markdown file in the original
I/R delta plus this correction resolve on disk; **0 broken**. No link text and no decision semantics
was altered for style, and `grep` confirms **no** remaining `](../Docs/Decisions/` anywhere under
`Milestones/contracts/`.

## 5. MIN-3 — generated real-gate payload completeness — **CLOSED**

`ExecutionRehearsalReport.as_payload()` generated `real_amendment_purpose_feasibility_gate` but
omitted the independently governed second gate.

- `real_linked_amendment_feasibility_gate: "OPEN"` is added **immediately beside** it.
- **The two gates remain separate.** They are **never** replaced by a generic `real_feasibility_gate`
  or any merged field — asserted by test, which also proves the payload's set of `*_feasibility_gate`
  keys is **exactly** those two.
- `real_builder_feasibility_proved` is retained as a **third, separate** claim.
- The fixture-only `m3 rehearse-execution` summary prints **both** gates **by name**, on their own
  lines, read from the generated payload so the printed summary and the evidence report can never
  disagree.

Observed on the corrected target:

```text
  real builder feasibility proved        : no
  real amendment-purpose feasibility gate: OPEN
  real linked-amendment feasibility gate : OPEN
```

**Report-schema version — Decision 075 §4 owner ruling applied.** The version is **NOT** bumped and
remains `m3-3a-execution-rehearsal-report/1.0`, asserted by test. MIN-3 is an **additive completion**
of an already-governed real-gate status block: it reinterprets no key, removes no key, renames no
key, alters no scenario semantics, alters no selector behavior, alters no persisted database schema,
and grants no authority.

**No real execution command changed.** All four gated real commands still refuse at **exit 3**:
`m3 offline-parse`, `m3 build-candidate-snapshot`, `m3 execute-selection`, `m3 manifest-output`.

## 6. OBS-1 — direct IMP-3 proof — **ADDED**

`test_the_candidate_form_universe_is_the_reference_family` now proves all three sides directly
rather than inferring them from a passing build, on **both** tracks' frozen snapshots:

* the unrelated synthetic `10-D` **exists** in the census / source-history layer (exactly one row);
* it does **not** appear in `pilot_candidate_accessions` — neither by its own accession identity nor
  by form;
* it **is reported** in `excluded_form_counts` with the expected deterministic count, `10-D: 1`
  (CLAUDE.md rule 11);
* and **R20** §6.2 still reads the same row as source-history evidence — the asset-backed control it
  establishes is present in `pilot_candidate_entities` under the same anchor CIK.

**Test-only.** The direct test exposed **no** defect, so no IMP-3 production code was changed.

## 7. OBS-3 — direct strict-subset E5 proof — **ADDED**

`test_a_subset_replacement_bundle_is_rejected` sits beside the existing strict-superset test and
proves the narrowing direction through the **same** accepted `build_reserve_packages` entry point
E5 uses:

* an **exact-match control** first — a two-accession target with a two-accession replacement yields
  **exactly one** package covering exactly that replacement's bundle, proving the target shape *is*
  coverable;
* then, with the replacement narrowed to a **strict subset** of that bundle and nothing else about
  the pool changed, **no compatible package** is produced and the target receives **exactly one**
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition.

`reserve_selector.py` is **untouched** and **no reserve-signature logic is duplicated**. The M3.3
suite now directly proves **both** directions:

| Direction | Test |
|---|---|
| Strict **subset** rejected | `test_a_subset_replacement_bundle_is_rejected` |
| Strict **superset** rejected | `test_a_superset_replacement_bundle_is_rejected` |

## 8. Corrected-target validation

Run once against the exact committed corrected target.

| Gate | Result | Elapsed |
|---|---|---|
| `ruff check .` | **All checks passed** | 0.08 s |
| `ruff format --check .` | **163 files already formatted** | 0.01 s |
| `mypy src` | **Success — 87 source files** | 0.29 s |
| `pytest` | **3949 passed, 1 skipped** (the pre-existing intentional skip) | 219.58 s |
| `make sqlite-check` | Python 3.12.13, SQLite 3.53.4 | 0.05 s |
| `make secrets` | **passed** — 344 files, 0 findings | 0.69 s |
| `make hygiene` | **passed** — 346 paths, 0 findings | 0.18 s |
| `make context` | clean tree, `HEAD == origin/main` | — |
| `git diff --check` | clean | — |
| Link check (delta + correction) | **792 links, 0 broken** | — |

**Zero failures. Nothing hidden.** The suite grows by exactly one net test (`3948 → 3949`), the new
strict-subset E5 proof; the other additions strengthen existing tests in place.

## 9. Corrected-target E1–E8 rehearsal

| Scenario | Track | Feasibility source | Result |
|---|---|---|---|
| **E1** | A | `BUILDER_DERIVED` | **PASS** |
| **E2** | A | `BUILDER_DERIVED` | **PASS** |
| **E3** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | **PASS** |
| **E4** | A | `BUILDER_DERIVED` | **PASS** |
| **E5** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | **PASS** — (a) positive compatible path, (b) zero-compatible, (c) mixed |
| **E6** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | **PASS** |
| **E7** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | **PASS** |
| **E8** | B | `EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` | **PASS** |

**R28 bridge: PASS — 1932 rows compared, 48 differences, 0 violations.**

Corrected-target run: all eight pass, evidence reference
`m3-3a-execution-rehearsal-report-72dc52bc70d2cf0fc1b5de5ee0cd2b50f414aef00c48cb2bd3fb6ef259f09391`,
receipt `7f1b74d2465e7b59c2728992c8a3edc6fff8cdf7651e59961357e8050f32097c`, token
`M3_3A_EXECUTION_REHEARSAL_PASSED_NO_REAL_EXECUTION_AUTHORIZED`.

```text
BUILDER_DERIVED_SELECTION_DISPOSITION = INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE
ACCEPTED_SELECTOR_FEASIBLE_ON_CONFORMING_EXPLICIT_REHEARSAL_SNAPSHOT = YES
REAL_BUILDER_FEASIBILITY_PROVED = NO
```

**These coexist by design. Track-B success does not imply real feasibility.**

## 10. Both generated real-gate fields

Read back from the corrected target's own generated evidence report:

```json
"report_schema_version": "m3-3a-execution-rehearsal-report/1.0",
"real_builder_feasibility_proved": false,
"real_amendment_purpose_feasibility_gate": "OPEN",
"real_linked_amendment_feasibility_gate": "OPEN",
"real_private_parse_authorization": "NO",
"actual_network_requests": 0,
"transports_constructed": 0
```

## 11. Mutation campaign

The M1–M38 campaign was re-run in full against the corrected executable target: **38 killed, 0
survivors, 0 skipped, zero residual mutation, positive control passing on all 11 distinct test
selections**, with the working tree verified clean and `HEAD` unchanged afterwards. The durable
per-mutation record required by Decision 075 §6 is
[`m3_3_i_r_mutation_campaign_06bb47a.md`](m3_3_i_r_mutation_campaign_06bb47a.md).

## 12. Findings

**BLOCKER 0 · MAJOR 0 · MINOR 0 · OPTIMIZATION 0 · OBSERVATION 0** for this bounded correction.

| ID | Class | Disposition |
|---|---|---|
| **MIN-1** | ultrareview finding | **CLOSED** — narrow supersession and current pointer applied across every current-state surface; index not restructured; Decision 068 not rewritten historically |
| **MIN-2** | ultrareview finding | **CLOSED** — five links corrected, 792 links verified, 0 broken |
| **MIN-3** | ultrareview finding | **CLOSED** — second gate generated beside the first, never merged, schema version deliberately not bumped |
| **OBS-1** | adopted strengthening | **ADDED** — direct IMP-3 proof; test-only, no defect exposed |
| **OBS-3** | adopted strengthening | **ADDED** — direct strict-subset E5 proof through the accepted entry point; `reserve_selector.py` untouched |
| **OBS-6** | adopted requirement | **SATISFIED** — durable per-mutation M1–M38 record created and bound to the corrected SHA; all 38 definitions recovered exactly, **0** recorded `NOT_DURABLY_RECOVERABLE` |

**The two open real-path gates are not implementation defects and are not closed by this
correction.**

## 13. Authorization state

```text
M3_3_I_R_ULTRAREVIEW_BOUNDED_CORRECTION_READY_FOR_REREVIEW
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```

**No real execution occurred.** No private evidence, no `EV_ROOT`, no real catalog, no real snapshot,
no real selection, no real manifest, and no real root was touched, created, or read; no SEC request,
no network, no reacquisition, no migration, and no tag.

**A passing correction, a green suite, a passing E1–E8 rehearsal, a fully killed campaign, a commit,
and a push are — individually and together — not an ultrareview pass and not a formal acceptance.**
The next action is to return to Sol/GPT for a **fresh read-only ultrareview-rereview** of the
corrected executable target `06bb47a`. Only if that returns **B0 / M0 / MIN0** does the fresh
independent formal-acceptance packet follow, and only after a **separate** owner resolution of
**both** real-path feasibility gates — which are never merged into one flag — may real E0 authority
even be considered.
