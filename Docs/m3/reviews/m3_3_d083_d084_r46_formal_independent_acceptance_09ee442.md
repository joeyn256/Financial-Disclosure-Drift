# M3.3 — D083/D084 R46 Formal Fresh Independent Acceptance Review — target `09ee442`

```text
REVIEW_KIND: FORMAL FRESH INDEPENDENT ACCEPTANCE REVIEW (R49 condition B, first half)
REVIEW_TARGET: 09ee44223cfebf247f7ae32a59c3f95c4d06bb79
VERDICT: FAIL
FINDINGS: BLOCKER 0 / MAJOR 1 / MINOR 4 / OPTIMIZATION 0 / OBSERVATION 6
RESULT_TOKEN: M3_3_D083_D084_R46_INDEPENDENT_REVIEW_FAILED_READY_FOR_OWNER_CORRECTION
REVIEWER: Claude Fable 5 (claude-opus-5 lineage identifier reported by harness: Opus 5), maximum effort
DATE: 2026-08-15
OWNER: Sol/GPT (review commissioned by owner packet)
```

**Verdict basis in one paragraph.** The implementation's *behaviour* is faithful to R58–R62 and
R65–R67 on every surface this review could reach: the schema is safe and complete, the R67 binding
claim is independently proven true, single-registrant identity is byte-identical against the genuine
pre-correction rule, every quota keeps its domain and value, E1–E8 all pass, and every repository
gate is green (4062 passed / 1 pre-existing skip). The verdict is **FAIL** on exactly one **MAJOR**
verification defect: **MR-M10's mutation protection does not kill its intended mutation.** Decision
083 §10 requires all fourteen MR protections "implemented at their exact definitions, not reduced to
representative coverage, and their effectiveness … demonstrated rather than assumed." This review
applied the exact MR-M10 mutant class — the derivation silently reading absent registrant evidence
as a sole registrant — and the suite does not detect it (finding M-1, §7 below). Four bounded
MINOR defects and six observations accompany it. No BLOCKER exists, no code misbehaves today, and
nothing here requires reverting the implementation commit.

---

## 1. Independence attestation

- **Model / effort:** Claude Fable 5 at maximum effort (harness model identifier `claude-opus-5`,
  presented as Opus 5; the owner packet commissioned this epoch as the fresh Fable acceptance
  reviewer and it is reported here exactly as observed).
- **Fresh epoch:** this review ran in a genuinely fresh `/clear` epoch whose first action was the
  `/clear`; no prior conversational state was inherited.
- **Authorship:** this epoch authored **none** of: Decision 082, Decision 083, Decision 084,
  migration `0014`, the R46 implementation, the R65/R66 corrections, the new or modified tests, or
  any correction-stage identity baseline. The reviewed target commit predates this epoch.
- **No delegation:** one session; **no subagents, no delegation, no parallel Claude workflows**; the
  Workflow facility was not used.
- **No network:** no SEC request, no HTTP request, no fetch/pull. All Git reads were local. The one
  authorized network act is the single review-publication push after the verdict was fixed.
- **No implementation edit before verdict:** the authoritative working tree remained byte-clean at
  the frozen target throughout the review (verified before and after validation). All mutation and
  schema experiments ran in a disposable clone and disposable SQLite catalogs under the session
  scratchpad; the clone was restored and discarded.
- **No inherited conclusions:** every claim below was re-derived from the frozen target, the
  governing records, and this review's own experiments. Prior completion reports were treated as
  claims requiring verification, not as evidence — and one of their claims is refuted (M-1).

## 2. Frozen target identity — verified

Verified live by `scripts/verify_target.py` (`1/1 checks passed`) plus direct Git corroboration.
No fetch, pull, reset, clean, or stash was performed.

| Fact | Required | Observed |
|---|---|---|
| Branch | `main` | `main` |
| `HEAD` == `origin/main` | `09ee44223cfebf247f7ae32a59c3f95c4d06bb79` | identical, both refs |
| Tree | `e13c55ae13d8c5ae12ddd7891e92fd946ec799fd` | identical |
| Parent | `6fdec2ed685c3c6248e392b04cdf184e8f3549e3` | identical |
| `m3.2-complete` annotated tag object | `2865a1479e4576dc18a4098c928b278812f38d00` | identical, unmoved |
| Working tree | clean | clean |
| Migrations | `0001`–`0014` contiguous | 14 files, contiguous, `0015` absent |

**Authority chain, corroborated by parent links:**
`5231359f` (D082 governance) → `8da08e48` (D083 governance) → `6fdec2ed` (D084 governance) →
`09ee4422` (implementation). Each recorded parent matches.

## 3. Reviewed diff and scope

**Governance commits.** D083 (`5231359f`→`8da08e48`) and D084 (`8da08e48`→`6fdec2ed`) touch only
`Docs/Decisions/` (one new record each), `decision_registry.md`, `decision_index.md`, and
`Milestones/STATUS.md`. The registry diff across the whole chain is **purely additive** (4 added
lines, 0 removed): no historical Decision 001–082 row was rewritten, and every decision file
001–082 is byte-unchanged across the chain.

**Implementation commit** (`6fdec2ed`→`09ee4422`): 24 files, 3216 insertions / 332 deletions —
9 source files (`acquisition.py`, `candidate_snapshot.py`, `execution_rehearsal.py`,
`offline_execution.py`, `support_target_pairs.py`, `reasons.py`, `accession_selection_store.py`,
`accession_selector.py`, `reserve_selector.py`), the new migration `0014`, and 14 `tests/unit/*`
files including the new `test_m3_3_multi_registrant_correction.py`. Every path is inside Decision
082 §10.14's authorized set (`tests/unit/*` inclusive) plus D084's exactly two additions;
`acquisition.py`'s diff is the R65 constant `13 → 14` plus documentation and nothing else, and
`offline_execution.py`'s diff is strictly the R66 caller (one governed-relation read feeding
`paired_accessions_from_rows`'s new fourth argument) plus documentation. Files §10.14 permitted but
the implementation did not need (`candidate_identity.py`, `rehearsal_world.py`,
`pilot_manifest_store.py`, `release/pilot_manifest.py`, `Docs/sec_data_dictionary.md`) are
byte-unchanged, which R67 makes correct for `candidate_identity.py`. **No prohibited path changed**
(§10 below).

## 4. Migration 0014 — independent schema review

Method: disposable catalogs only. A catalog was built at `0001`–`0013` through the repository's own
`apply_migrations` machinery, its full `sqlite_master` captured, `0014` applied, and the object
inventories diffed; a fresh full-chain build was compared against the upgrade path; and the guard
behaviour was probed directly. **The accepted private M3.2 operational catalog was never opened,
read, or migrated**, and no `EV_ROOT` was resolved.

- **A. Chain position:** exactly `0014`; packaged inventory contiguous 1–14; provenance rows 14
  with matching name and checksum; `verify_applied_migrations` accepts the chain on every reopen
  (**L** satisfied).
- **B. `0001`–`0013` byte-unchanged:** all thirteen blobs are git-identical to the accepted
  `m3.2-complete` baseline.
- **C/D. R58 relation and completeness:** `census_accession_registrants` exists with
  `PRIMARY KEY (accession_plain, registrant_cik_numeric)`, an `association_class` CHECK
  (`substantive`/`submitter_only`), padded-CIK shape CHECK, and provenance columns;
  `registrant_set_completeness` exists on `census_accessions` (default `'unestablished'`) and on
  both candidate tables.
- **E. False scalar unrepresentable:** proven by probe — inserting a second substantive relation row
  while the census scalar is non-NULL **aborts**; writing the scalar back onto a two-member set
  **aborts**; at the candidate layer the CHECK matrix admits exactly
  {established+anchor+multi 0}, {established+NULL-anchor+multi 1}, {unestablished+NULL-anchor}
  and refuses anchor+unestablished, established+NULL-anchor+multi 0, and
  established+anchor+multi 1.
- **F. Single-registrant preservation:** every 0013 column, CHECK, key, index, guard trigger, and
  comment of the four rebuilt tables is reproduced; the only deltas are the two nullability changes
  and the new columns/CHECKs.
- **G/H. Prospective/empty-state safety:** the Section-1 temporary-trigger precondition was proven
  live — a 0013 catalog seeded with one `census_accessions` row **refuses** `0014`
  (`migration 0014 requires an empty census_accessions`), rolls back atomically, and is left with
  `sqlite_master` byte-identical to 0013, provenance still ending at 13, and the seeded row
  untouched. The `'established'` backfill literals in the candidate-table copies are therefore
  provably unreachable over real rows: the same tables are directly checked empty first. All four
  rebuilt tables are directly checked; the remaining §10.12 tables are covered by the checked FK
  roots (`pilot_candidate_snapshots`, `pilot_selection_runs`) plus the census family checks.
- **I. No object lost:** the 0013→0014 `sqlite_master` diff is exactly: 6 objects added (the
  relation, its index, three census guard triggers, the selection-attachment trigger), 0 removed,
  5 changed (the four rebuilt tables and the replaced freeze trigger). Every pre-existing index,
  guard trigger, and the Decision-021 §15.1 selection-run triggers survive with identical SQL.
- **J. Integrity:** `PRAGMA foreign_key_check` 0 violations and `integrity_check` ok after
  migration; the composite `pilot_selected_accessions` FK is reproduced unchanged and its
  MATCH-SIMPLE NULL semantics are correctly replaced by the attachment trigger (probed: a selected
  accession with no co-selected substantive registrant **aborts**; any one co-selected substantive
  registrant satisfies it).
- **K. `legacy_alter_table`:** used only to bypass the transient whole-schema reparse while the
  Decision-021 triggers reference a table mid-rebuild; every rebuilt table is renamed back to its
  original name, the pragma is restored (`0` after migration), and the upgrade-path schema is
  **byte-identical** to a fresh full-chain build — no latent rename defect exists.
- **Freeze trigger:** the unchanged clauses (counts, ≥1-registrant-row, entity and accession
  evidence backing) are reproduced byte-for-byte in original order. The anchor clause is replaced by
  the exact R58 conditions, and the old `multi_registrant` clause — which counted **all** rows and
  carried a reason-code escape (`reason_scope = 'multi_registrant'`) — is replaced by the strict
  Decision 072 R23 §5.3 predicate over **substantive** rows with no escape. That tightening is
  authorized (D082 §10.5 items 7–8; §10.10) and is disclosed in the migration header; the escape's
  legitimate use-case (incomplete evidence) is now the R59 exclusion instead.

Two comment-versus-mechanism inaccuracies inside the migration are findings MIN-1 and MIN-2 below.

## 5. R58 / R59 / R60 — representation, candidacy, sentinel

- **R58.** Established cardinality 1: the builder emits one `role='anchor'` row and the factual
  scalar; every pre-correction call site and digest is reproduced byte-for-byte (§6). Established
  cardinality >1: scalar/anchor NULL (schema-enforced), every substantive row `associated`, full
  set preserved relationally, and **no primary CIK is derivable anywhere** — a broad sweep for
  min/max/first-write/`[0]`-style member selection over registrant sets found only benign cap
  arithmetic, the validated `anchors[0]` under an exactly-one-anchor check, and the deliberate
  reserve single-attribution recorded as MIN-4. Unestablished: cannot masquerade as
  single-registrant (builder excludes before any row exists; the loader's
  `_stored_registrant_slot` refuses an anchorless non-established row; freeze refuses the state
  outright — probed directly).
- **R59.** The completeness state is load-bearing: no fabricated scalar (schema CHECKs), no
  candidate snapshot entry (builder `continue` + freeze trigger + loader refusal), no
  entity/history/quota credit (excluded before aggregation), and the registered reason
  `PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED` exists with `requires_manual_review` and the D083
  decision reference, with the exclusion counted in
  `excluded_unestablished_registrant_set` (CLAUDE.md rule 11). Persistence/reload/replay of an
  unestablished candidate state is unreachable from governed flows (freeze refusal proven). The
  **test demonstration** of the builder half of this rule is the M-1 finding.
- **R60.** The sentinel is the exact string `MULTI_REGISTRANT_NO_SINGLETON`, defined once, used in
  exactly two source sites: the tie-break slot function and the store's slot reconstruction for
  stored-digest verification — both deterministic serialization/verification. It is never persisted
  (no CIK column can hold it — INTEGER columns; no code writes it), never parsed as a CIK, never an
  entity, never a transport locator, never counted toward any quota (the multi-registrant witness is
  the dashed accession; entity witnesses iterate real registrants), and cannot collide with the
  numeric padded-CIK domain (non-digit, length ≠ 10; asserted in tests). It surfaces in exactly one
  reporting object — the in-memory `AccessionDiagnostic.registrant_slot_padded`, which is not
  persisted and is explicitly documented as a slot label (OBS-2). An unestablished set is refused
  rather than hashed (`accession_registrant_slot` raises below two distinct members).
  **Single-registrant tie-break preimages are byte-identical** — proven against the genuine
  pre-correction rule, not against the new code's own output (§6).

## 6. R61 / R67 — identity boundary and binding proof

**Inventory completeness.** The registrant-scalar consumers were independently re-derived from
`candidate_identity.py`, `candidate_snapshot.py`, `accession_selector.py`,
`accession_selection_store.py`, `pilot_manifest.py`, and the seal/manifest layer. The affected set
is exactly **E1–E5** as owner-approved: E1 `accession_tie_break_sha256` (slot in the preimage);
E2 `candidate_accession_table_sha256` (`anchor_cik_numeric`, `accession_tie_break_sha256`,
`multi_registrant` in `ACCESSION_TABLE_COLUMNS`); E3 `candidate_registrant_table_sha256` (row
membership + `role`/`is_anchor`); E4 `candidate_snapshot_sha256` (carries E2/E3);
E5 `selection_input_sha256` → `selection_run_id` → manifest components/root (carries E4 plus the
accession-content records, whose `anchor_cik_padded` and per-accession registrant digest move for a
multi accession). **No additional governed identity consumer moves for registrant reasons.**
`snapshot_id` (`SNAPSHOT_IDENTITY_FIELDS` carries no registrant field), `entity_tie_break_sha256`
(padded CIK + seed only), the **R15** `evidence_sha256` eight-field preimage, and the **R16**
`resolution_sha256` preimage are unaffected — asserted against the frozen field tuples and by test.
One design-inherent, registrant-independent effect is noted as OBS-6: any manifest built at chain
`0014` moves its `selector_policy_sha256` (and therefore the root) because that component
deliberately binds the migration chain; this is the component doing its accepted Decision-021 job,
is disclosed with exact before/after literals in the re-baselined manifest fixture, and is not a
registrant-semantics leak.

**R67 binding proof (the D084 §4 acceptance precondition), executed rather than accepted.** With
real digest computations over a three-member association set, through
`candidate_registrant_table_sha256` → `candidate_snapshot_sha256` →
`build_joint_selection_run_identity`:

| Experiment | E3 | E4 | E5 + `selection_run_id` |
|---|---|---|---|
| REMOVE one substantive association | changes | changes | change |
| CHANGE one substantive association | changes | changes | change |
| ADD one substantive association | changes | changes | change |
| REORDER identical associations (two permutations) | **unchanged** | — | — |

The anchor role state itself is bound (anchor↔associated demotion changes E3). The two new columns
are outside `REGISTRANT_TABLE_COLUMNS`, and that loses nothing: `association_class` is
CHECK-equivalent to the digest-bound `role`, and `registrant_set_completeness` is
freeze-constant (`'established'` for every row of any frozen snapshot — trigger-enforced), so
neither carries information E3 does not already see. **The relational set is genuinely governed and
bound; the R67 claim is TRUE and no STOP is triggered.** `candidate_identity.py` is byte-unchanged
in the implementation commit.

**Single-registrant nonchange (§18 of the packet).** The three MR-M13 pinned literals were
authenticated against the **actual pre-correction implementation** (the preimage rule extracted
from `accession_selector.py` at parent commit `6fdec2ed` and executed independently): all three are
genuine pre-correction digests, and the new path reproduces them byte-for-byte — as does a fourth
representative case outside the pinned set. The frozen production seed is unchanged. E2–E5 carry no
new field for a single-registrant row (the completeness column is excluded from every digest
tuple), the E5 preimage field set is unchanged, and the full suite's single-registrant fixtures and
pinned manifest components (`source_observation_set_sha256`, `candidate_tables_sha256`,
`quota_definitions_sha256`) hold their prior values.
**`SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0` — independently confirmed.**

## 7. Mutation effectiveness — MR-M1…MR-M14 (and the MAJOR finding)

The new campaign lives as fourteen standing tests in `test_m3_3_multi_registrant_correction.py`
(25 tests total with the R60/R65/R66/R67 additions; all pass). Each protection was inspected
against its exact D082 §10.13 definition, and three real code mutants were additionally
hand-applied in a disposable clone:

- **Design-verified as genuine mutant-killers:** MR-M1/M2/M3/M14 (order/membership invariance with
  content-level assertions, not digests alone), MR-M4/M5/M6/M8 (each prohibited heuristic's output
  asserted unequal to production at the consumer-facing property **and** at the digest),
  MR-M7/M9 (proved at the schema layer — the mutant row cannot be written at all; re-probed
  directly in this review), MR-M11 (duplicates collapse; anchor retained), MR-M12 (schema +
  freeze), MR-M13 (byte-identity against pinned genuine literals — the load-bearing test).
- **Hand-applied mutants:** anchor := first substantive member for a multi set → **KILLED**
  (`CandidateSnapshotError`, exact-anchor-cardinality check); tie-break slot made
  membership-dependent → **KILLED** (MR-M14 + traceability tests). Historical **M20** and **M22**
  were re-executed through the accepted campaign runner at the frozen target: **KILLED / KILLED**,
  with all **38/38** accepted M1–M38 anchors still resolving and the accepted campaign document
  byte-unchanged (§9).
- **M-1 (MAJOR).** MR-M10's exact definition is: *mutation* — "derive the association set from a
  source with rows omitted"; *killing assertion* — "`registrant_set_completeness` must be
  `unestablished`; **a silent single-registrant result fails**." The shipped MR-M10 test never
  derives anything: it asserts reason-code registration and that a hand-seeded unestablished
  candidate row cannot freeze — the *persistence backstop*, not the derivation. This review applied
  the exact mutant class to the derivation
  (`candidate_snapshot.derive_candidate_snapshot`: `associations is None` → treat as empty and fall
  through to the scalar, i.e. silence read as a sole registrant — the precise pre-correction
  regression R59 exists to prevent). The mutant produces fully lawful-looking persisted state
  (established sole-registrant rows), so **no schema or freeze guard can catch it**, and it
  **SURVIVED** all 205 tests of every builder-invoking test file (`test_m3_candidate_snapshot`,
  `test_m3_3_multi_registrant_correction`, `test_m3_3_execution` including E1–E8,
  `test_m3_offline_parse`); no other suite file invokes the builder, and no fixture anywhere feeds
  the builder an accession lacking establishment evidence. A dangling pointer corroborates the
  omission: `test_m3_candidate_snapshot.py` line 41 says "see `test_group_r59` for the absent
  case," and no such test exists. The production code itself is correct today (read directly;
  behaviour verified) — the defect is that Decision 083 §10's formal condition ("implemented at
  their exact definitions, not reduced to representative coverage, and their effectiveness …
  demonstrated rather than assumed") is **not satisfied for MR-M10**, on the single most
  consequential regression class of the whole correction: a silent regression here before real E0
  would fabricate sole-registrant candidacy for real R22 category-B accessions, and D082 §10.12
  makes post-E0 rollback unavailable. Under the packet's severity standard this is
  acceptance-gating; per §16, a protection that does not kill its intended mutation must be
  reported, and per §23 it cannot coexist with PASS.

## 8. R62, quota, R65, R66, item 48

- **R62.** Entity-domain aggregation attributes a joint filing to **every** substantive registrant:
  `eligible_forms`, original-annual-report dates/counts, `multi_registrant_annual_filing`,
  `non_ordinary_amendment_lineage`, and material-conflict attribution all iterate the substantive
  set; entity-domain quota witnesses (linked-amendment, transition-report, original-2024/2025-26,
  FYE-change/-distance, pair support/targets) emit one witness per substantive registrant and count
  **distinct** entities; the per-CIK base cap counts a joint base filing for each attached
  registrant. Accession-domain calculations (`base_total`, `stress_total`, `accession_total`, the
  multi-registrant quota, pair leg accession counts) remain keyed by canonical accession and count
  one joint filing once — verified in the selector, the reserve `_usage_from`, and the pair module,
  with the R66 end-to-end test proving two entities from exactly two accessions. Cross-category
  joint attachments fail closed with no primacy (`_attached_category` → not available). No
  accidental double-counting was found in any accession-domain path.
- **Multi-registrant quota.** `QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS` remains hard at **2**, its
  witness remains the dashed accession number (accession-keyed, anchor-free), the flag remains
  distinct-substantive-cardinality ≥ 2 (never a raw row count, never a submitter row), and no quota
  changed value or declared domain. `pilot_policy.py` and migration `0010` are byte-unchanged.
- **R65.** The `acquisition.py` diff is the constant `13 → 14` plus explanatory documentation —
  nothing else in the file. It reopens no network/M3.2/acquisition authority (tracked switches
  remain `false`/`false`; no transport module changed), and nothing migrates the private catalog
  automatically — `prepare_operational_catalog` is invoked by no standing process, and this review
  exercised it only against a disposable pytest root: chain recognized exactly `0001`–`0014`,
  `chain_is_exact` true.
- **R66.** The caller reads the governed candidate relation at
  `association_class = 'substantive'` for the run's snapshot — the same predicate every other
  consumer uses — and hands the mapping to `paired_accessions_from_rows`. Proofs A–E all exist and
  pass: joint pair reaches both substantive entities `(1, 901)`; two legs remain two accessions;
  leg-order and association-order invariance; an absent association set yields zero pair credit
  (fail-closed, quota only gets harder); single-registrant behaviour identical with the set stated
  or implied. Pair quota, eligible forms, the 2009/2010 rule, and accession-domain deduplication
  are untouched.
- **Manifest item 48.** Decision 021 is not rewritten; the crosswalk still binds item 48 "anchor
  CIK" to `anchor_cik_numeric`, which is now the factual sole CIK or NULL with no replacement
  anchor; the re-baselined reserve-bearing manifest fixture (two genuinely anchorless joint
  accessions) builds and seals correctly with NULL flowing through canonical JSON, and the
  relational set stays available through the candidate registrant representation and its digest.

## 9. Rehearsal, persistence, replay

`run_execution_rehearsal` was executed directly on a disposable workspace: **E1–E8 all PASS**
(8/8), with the rehearsal world containing genuine multi-registrant accessions (co-registrant
slots), so freeze (E1), refusal (E2), feasible selection (E3), fail-closed infeasibility (E4),
reserve/disposition totality (E5), reconstruction-mismatch refusal (E6), seal/manifest atomicity
(E7), and write-free replay (E8 — `write_free: true`, durable digest byte-identical before and
after) all exercise single **and** multi state through persist → reload → reconstruct → replay. The
store's loader re-derives every tie-break from persisted anchor + completeness and refuses any
divergence, so no first-write-dependent state can reappear after reload or reconstruction. The
accepted M1–M38 campaign document (`m3_3_i_r_mutation_campaign_06bb47a.md`) is byte-unchanged
across the chain; anchors resolve **38/38** at the frozen target; **M20 KILLED, M22 KILLED**
re-executed live.

## 10. Prohibited-nonchange proof

In the implementation commit, byte-unchanged (git blob identity): `cohorts.py`;
`pilot_policy.py`; migrations `0001`–`0013` (also identical to the accepted `m3.2-complete`
baseline blobs); `Docs/preregistration.md`; every existing record in `Docs/Decisions/` (registry
purely additive across the chain); every network/SEC transport module (no such path appears in the
24-file diff; `acquisition.py`'s only executable delta is the R65 constant); the accepted M3.2
evidence root and D081 private evidence (external; never referenced, opened, or resolved — no
`DISCLOSURE_DRIFT_*`/`EV_ROOT` environment was set during this review); the document-review /
adjudication surface (none exists). **Migration `0015` does not exist.** No tracked database exists
in the repository. `m3.2-complete` is unmoved at tag object `2865a147…`. No SEC request, no HTTP
request, and no real E0 state was created; all experiments used disposable catalogs and a
disposable clone.

## 11. Validation executed (with elapsed times)

| Step | Result | Elapsed |
|---|---|---|
| `scripts/verify_target.py` + Git corroboration | PASS | 0.1 s + 0.5 s snapshot |
| Migration campaign `--verify-only` (38 anchors) | 38/38 resolved | 0.1 s |
| Historical M20 + M22 executed in clone | KILLED / KILLED | 29.7 s |
| Schema diff experiment (0013→0014, fresh-vs-upgrade, FK/integrity) | all clean | 0.4 s |
| Precondition + trigger/CHECK probes (18 probes) | 18/18 PASS | 0.3 s |
| Identity/binding experiment (25 checks; OLD-code literal authentication) | 25/25 (one literal not reproducible → MIN-3) | 0.3 s |
| `pytest tests/unit/test_m3_3_multi_registrant_correction.py` | 25 passed | 1.3 s |
| Rehearsal battery (`test_m3_rehearsal`, `test_m3_3_execution`, `test_m3_offline_parse`) | 201 passed | 23.2 s |
| Direct `run_execution_rehearsal` (E1–E8) | 8/8 PASS | 10.3 s |
| Targeted battery (15 affected test files) | 1525 passed | 104.0 s |
| Hand-applied mutant A (first-member anchor) | KILLED | 3.4 s |
| Hand-applied mutant B (membership-dependent slot) | KILLED | 0.8 s |
| Hand-applied mutant MR-M10-class (silence → sole registrant) | **SURVIVED 205 tests** → M-1 | 24.1 s |
| `make check-fast` (WORKERS=7) — the one routine run | exit 0 — ruff, format, mypy strict (87 files), **4062 passed / 1 pre-existing skip** (7 workers), secrets 0 findings, hygiene 0 findings, links 158 docs / 1570 links, decision-refs 3572 citations / 84 records, config + cohorts + SEC help | 82.6 s |
| `git diff --check` | clean | <0.1 s |

`make links` / `make decision-refs` / `make secrets` / `make hygiene` were not duplicated outside
`make check-fast`, which runs all four (results above).

## 12. Findings

| ID | Severity | Finding |
|---|---|---|
| **M-1** | **MAJOR** | **MR-M10's mutation protection does not kill its intended mutation.** The derivation-layer mutant — absent registrant evidence silently read as a sole registrant in `derive_candidate_snapshot` — survives every builder-invoking test (205 run; full-suite fixtures never omit establishment evidence), while the shipped MR-M10 test exercises only the freeze-layer backstop, which structurally cannot see this mutant. Decision 083 §10's condition that all fourteen protections be implemented "at their exact definitions, not reduced to representative coverage," with effectiveness "demonstrated rather than assumed," is unmet for MR-M10. Corroborated by the dangling `test_group_r59` pointer at `tests/unit/test_m3_candidate_snapshot.py:41`. Production code behaves correctly today; the missing artifact is a builder-level test deriving from a census world with no establishment evidence and asserting exclusion + the reported count. Requires owner correction authority (a new test is outside this review's authority to add). |
| MIN-1 | MINOR | Migration `0014` §5 comment states "Both new columns enter `REGISTRANT_TABLE_COLUMNS`, so Decision 083 R61's requirement … is satisfied by construction." False as to mechanism: R67 deliberately left `REGISTRANT_TABLE_COLUMNS` unwidened and the columns are **not** in the digest. The binding is nevertheless real (proven §6: row membership + role↔class CHECK equivalence + freeze-constant completeness). Non-gating misdocumentation inside a permanent schema artifact, stale from the pre-R67 working tree the D084 continuation preserved. |
| MIN-2 | MINOR | The census `established`-requires-relation guard fires only on UPDATE: a direct INSERT of a `census_accessions` row claiming `'established'` with zero relation rows succeeds (probed), contradicting the migration §3 comment "the claim can never be made by assertion alone." Non-gating: candidacy establishment never reads the census completeness column (the builder derives establishment from evidence presence), the candidate/freeze layers fail closed (proven), and no authorized writer of this column exists pre-E0. |
| MIN-3 | MINOR | In `_REBASELINED_MULTI_REGISTRANT_RANKS`, the second "before" digest (`5f3f6a57…` for `0000000018-18-000002`) is not reproducible as any pre-correction digest (not the old rule at anchor 18 or any CIK ≤ 2,000,000, no plausible synthetic preimage, no provenance anywhere in the parent commit), and the test asserts only `before != after`, so the "before" column is unverified by the suite. The first row's "before" is genuine (independently reproduced), both "after" values are genuine and sentinel-traceable, and no computation consumes the column — but a re-baseline table presented as "the false-singleton digest the correction abolishes" carries one apparently invented value. Non-gating documentation-of-record defect (no genuine pre-correction pinned multi identity existed to misstate). |
| MIN-4 | MINOR | `reserve_selector._caps_preserved` attributes a replacement's bundle accession to `(replacement_cik,)` alone. If a replacement's bundle contains a genuinely joint filing shared with a still-selected co-registrant that is **not** currently selected as an accession, the substituted-world simulation undercounts the co-registrant's `max_base_per_cik` usage, diverging from the R62 entity-domain cap treatment used everywhere else (including this module's own `_usage_from` for retained selections). Bounded: the overlapping (currently-selected) case fails closed; the divergence affects only hypothetical reserve-substitution feasibility simulation, synthetic-only pre-E2; the choice is documented inline. |
| OBS-1 | OBSERVATION | The reserve-bearing manifest test's claim that "E2, E3, and E4 are byte-unchanged for this fixture" is vacuous rather than substantive: that fixture seeds the snapshot-row family digests as synthetic literals, so the statement does not evidence real digest stability (real E2/E3 lawfully move for a multi world under R61). The component-level re-baseline itself is genuine and fully traceable. |
| OBS-2 | OBSERVATION | `AccessionDiagnostic.registrant_slot_padded` is named "padded" but may carry the non-padded sentinel; in-memory diagnostics only, never persisted. |
| OBS-3 | OBSERVATION | `AccessionCandidate` with a non-None anchor silently ignores a supplied larger `substantive_registrant_ciks` set (resolved = anchor alone). Unreachable from governed state (schema CHECKs make anchor+multi unrepresentable; the loader supplies consistent pairs); an in-memory API misuse hazard only. |
| OBS-4 | OBSERVATION | `test_r66_the_persisted_caller_grants_no_credit_without_the_association_set` issues `PRAGMA foreign_keys = OFF` inside an open transaction, where it is a documented SQLite no-op; the DELETE succeeds regardless (child-side delete). Harmless. |
| OBS-5 | OBSERVATION | `Docs/sec_data_dictionary.md` remains accurately self-scoped "through migration `0013`" and does not yet describe `0014`. §10.14 permitted but did not require updating it; a future documentation pass may. |
| OBS-6 | OBSERVATION | Any manifest built at chain `0014` moves `selector_policy_sha256` (and the root) via its `migration_chain_sha256` input, including for pure single-registrant worlds. This is the accepted Decision-021 policy-binding behaviour of that component, disclosed with exact literals in the re-baselined fixture; it is not a registrant-semantics leak and does not touch E1–E4, `selection_input_sha256`, or `selection_run_id`. |

## 13. Formal acceptance conditions — disposition

| Condition | Disposition |
|---|---|
| Target/authority valid | SATISFIED |
| Migration 0014 safe for authorized use (A–L) | SATISFIED (MIN-1/MIN-2 non-gating) |
| R58 relational representation | SATISFIED |
| R59 completeness load-bearing, fail-closed | Behaviour SATISFIED; **demonstration defect M-1** |
| R60 sentinel discipline + byte-identity | SATISFIED |
| R61 inventory exactly E1–E5; four preserved identities | SATISFIED |
| R67 relational set genuinely governed and bound | SATISFIED (proven; no STOP) |
| R62 history/domain semantics; no double-counting | SATISFIED |
| Multi-registrant quota hard at 2, accession-keyed | SATISFIED |
| R65 constant-only; chain 0001–0014 recognized; private catalog untouched | SATISFIED |
| R66 semantics + proofs A–E | SATISFIED |
| Manifest item 48 prospective interpretation | SATISFIED |
| MR-M1…MR-M14 all effective | **NOT SATISFIED — M-1 (MR-M10)** |
| Historical M1–M38 immutable; M20/M22 valid | SATISFIED |
| E1–E8 = PASS | SATISFIED (8/8) |
| SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0 | SATISFIED (independently confirmed) |
| Persistence / replay / reconstruction round trip | SATISFIED |
| Prohibited nonchange (incl. no 0015, tag unmoved, no network, no real E0 state) | SATISFIED |
| `make check-fast` zero failures | SATISFIED (4062 passed / 1 pre-existing skip) |

**BLOCKER 0 / MAJOR 1 → VERDICT: FAIL.**

```text
M3_3_D083_D084_R46_INDEPENDENT_REVIEW_FAILED_READY_FOR_OWNER_CORRECTION
```

## 14. Next owner action

Return to Sol/GPT. The reviewed target `09ee4422…` stands as committed; nothing in this review
modifies, reverts, or re-derives it, and this review corrected no finding. M-1's natural remedy is
small and bounded — one builder-level test deriving from a census world without establishment
evidence (the missing `test_group_r59`), plus owner disposition of MIN-1–MIN-4 — but any correction
requires new owner authority. R49 condition B remains unsatisfied. M3.3-E0, E1, E2, M3.4, migration
0015, Review A, Review B, and the document adjudication all remain unauthorized; network, SEC, and
HTTP authority remains NONE at `REQUEST_CEILING 0`.
