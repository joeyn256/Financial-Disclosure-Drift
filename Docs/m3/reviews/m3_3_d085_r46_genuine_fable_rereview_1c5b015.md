# M3.3 — D085 Corrected R46 Genuine Fable 5 Formal Independent Rereview — target `1c5b015`

```text
REVIEW_KIND: GENUINE CLAUDE FABLE 5 FORMAL INDEPENDENT ACCEPTANCE REREVIEW (R49 condition B, first half)
REVIEW_TARGET: 1c5b0150ecfc5e4695842e330d83f1ce2148c643 (tree 1994e8bfe54b8db03da765980f5df2d6dff822ba)
ORIGINAL_FAILED_TARGET: 09ee44223cfebf247f7ae32a59c3f95c4d06bb79 (tree e13c55ae…)
GOVERNANCE_HEAD_AT_REVIEW: c6cd1dfdcae12453129b007c72503ea88d1f4660 (Decision 086, governance only)
VERDICT: PASS
FINDINGS: BLOCKER 0 / MAJOR 0 / MINOR 0 / OPTIMIZATION 0 / OBSERVATION 3
RESULT_TOKEN: M3_3_D085_R46_GENUINE_FABLE_REREVIEW_PASSED_READY_FOR_OWNER_ACCEPTANCE
REVIEWER: Claude Fable 5 (harness model identifier `claude-fable-5`), maximum effort
MODEL_IDENTITY_GATE: PASSED — genuine Fable 5 epoch
DATE: 2026-08-15
OWNER: Sol/GPT (review commissioned by owner packet under accepted Decision 086)
```

**Verdict basis in one paragraph.** The full corrected R46 implementation is formally acceptable.
This epoch independently reproduced the acceptance-gating M-1 sequence end to end — the exact
derivation-layer mutant (absent establishment evidence silently read as a sole registrant from the
census scalar) **SURVIVED all 207** builder-invoking tests of the original failed target `09ee4422…`,
is **KILLED** by exactly the four new MR-M10A / Group-R59 builder-level protections on the corrected
target `1c5b015…`, and the real implementation passes clean — so
`MR_M10_DERIVATION_MUTANT = KILLED`. MIN-1's corrected migration comments now state the true R67
binding mechanism and the underlying mechanics were independently proven true; MIN-2's four-door
establishment invariant refuses every false `established`-with-zero-substantive-relations state while
the lawful E0 ingest shape was exercised end to end on disposable catalogs; MIN-3's replacement
"before" literal `03e8736e…` was reproduced from the genuine pre-correction parent's own fixture at
chain head `0013` (`UNVERIFIABLE_PRECORRECTION_DIGESTS = 0`); MIN-4's reserve per-CIK cap now charges
every truthful substantive registrant with accession-domain totals counting one joint filing once,
fail-closed on an unreadable set. The correction diff is **bounded** to those five findings plus the
truthful governance and current-state publication; the four sensitive modules are blob-identical to
the failed target; and the entire original acceptance boundary — R58/R59/R60, R61/E1–E5, R62, R65,
R66, R67, manifest item 48, the multi-registrant quota, MR-M1…MR-M14, E1–E8, single-registrant
nonchange, persistence/reload/reconstruction/write-free replay, migration `0014` complete review, and
prohibited nonchange — was revalidated rather than inherited. R68's migration-policy identity
movement is exactly as claimed: of the fixture's eight manifest components precisely one
(`selector_policy_sha256`) moved, the other seven are byte-identical, `selection_result_sha256` and
the canonical-JSON length are unchanged, and root/`manifest_id` moved only as derived identities.
One routine `make check-fast` returned exit 0. **BLOCKER 0 / MAJOR 0 / MINOR 0 → PASS.**

---

## 1. Model-identity gate and independence attestation

- **Model identity (gate, checked before substantive review):** the harness environment declares
  "You are powered by the model named Fable 5. The exact model ID is `claude-fable-5`." That is the
  unambiguous Fable 5 identifier Decision 086 §5 requires. **No Opus identifier was observed and no
  substitution occurred.** Gate PASSED; substantive review proceeded.
- **Effort:** maximum.
- **Fresh epoch:** a genuinely fresh `/clear` epoch whose first action was the `/clear`; no prior
  conversational state was inherited. The frozen target commit predates this epoch.
- **Authorship:** this epoch authored **none** of: Decisions 082–086, migration `0014`, the R46
  implementation, the R65/R66 corrections, the D085 correction, any test, or any identity baseline.
- **No delegation:** one session; no subagents, no delegation, no parallel Claude workflows; the
  Workflow facility was not used.
- **No network:** no SEC request, no HTTP request, no fetch, no pull (`REQUEST_CEILING 0`
  respected). The single authorized network act is the one review-publication push after the verdict
  was frozen.
- **No implementation edit before verdict:** the authoritative working tree remained byte-clean at
  the frozen surface throughout (verified before and after validation; `git status` clean, 0 paths).
  Every mutation, migration, and catalog experiment ran in disposable clones and disposable SQLite
  catalogs under the session scratchpad; the accepted private M3.2 catalog was never opened and no
  `EV_ROOT` / `DISCLOSURE_DRIFT_*` environment was set.
- **Claim provenance discipline:** conclusions below are labelled
  `[INDEPENDENTLY_REPRODUCED]` (this epoch executed it), `[COMMITTED_EVIDENCE_VERIFIED]` (checked
  against committed artifacts/blob identity), or `[SOURCE_INSPECTION_ONLY]`. Prior-review
  conclusions were treated as leads, not proof; the load-bearing ones were re-executed.

## 2. Repository state, frozen target, and authority chain — verified

`scripts/verify_target.py` **8/8 PASS** on the governance HEAD (branch `main`;
`HEAD == origin/main == c6cd1df…`; tree `fbfb11eb…`; parent `1c5b015…`; working tree clean;
`m3.2-complete` tag object `2865a147…`) and **3/3 PASS** on the frozen target (`1c5b015…`, tree
`1994e8bf…`, parent `a93d5b8…`). Migrations `0001`–`0014` contiguous; `0015` **ABSENT**; no tag at
HEAD; tracked network switches `false`/`false`. No fetch, pull, reset, clean, or stash was performed.
`git diff --name-only 1c5b015 -- src tests scripts configs Makefile pyproject.toml` is **empty** at
the governance HEAD, so the reviewed implementation surface **is** the frozen target's.
`[INDEPENDENTLY_REPRODUCED]`

**Authority chain, corroborated by parent links and direct reads of Decisions 082–086:**
`5231359f` (D082 pre-E0 contracts) → `8da08e48` (D083 R58–R64 + implementation authority) →
`6fdec2ed` (D084 R65–R67 bounded continuation) → `09ee4422` (original R46 implementation) →
`2d4e2ea1` (formal independent FAIL review publication) → `a93d5b80` (D085 correction authority) →
`1c5b0150` (corrected implementation target) → `c6cd1dfd` (D086 owner adjudication / Fable rereview
authority). Every recorded parent matches. Decision 086 is evidence and authority **about**
`1c5b015…` and was not treated as the implementation target. `[INDEPENDENTLY_REPRODUCED]`

## 3. Correction scope — bounded to the five accepted findings

The D085 governance publication (`2d4e2ea`→`a93d5b8`) touches only `Docs/Decisions/decision_085…`,
`decision_registry.md`, `decision_index.md`, and `Milestones/STATUS.md` (registry purely additive:
0 removed lines across the whole chain; no historical Decision 001–084 file modified). The
implementation-correction commit (`a93d5b8`→`1c5b015`) touches exactly the packet-expected set:
migration `0014`, `sec/reserve_selector.py`, `tests/unit/test_m3_candidate_snapshot.py`,
`tests/unit/test_m3_3_multi_registrant_correction.py`, `tests/unit/test_m23_reserve_selector.py`,
`tests/unit/test_m23_pilot_manifest_store.py`, plus `Milestones/STATUS.md` (truthful current-state
documentation) — and nothing else. Line-level reading attributes every hunk to M-1, MIN-1, MIN-2,
MIN-3, MIN-4, or the R68-accepted fixture re-baseline. **Byte-unchanged from `09ee442` (git blob
identity):** `m3/candidate_identity.py`, `m3/candidate_snapshot.py`, `m3/acquisition.py`,
`m3/offline_execution.py` — all four SAME. No unrelated executable change exists.
`[INDEPENDENTLY_REPRODUCED]`

## 4. M-1 — MR-M10 exact mutant execution (acceptance-gating)

Disposable clones `clone-old` (= `09ee442`, tree verified `e13c55ae…`) and `clone-new`
(= `1c5b015`, tree verified `1994e8bf…`). **Module provenance was proven in-session for every
run**: the editable-install hazard was neutralized with `PYTHONPATH=<clone>/src`, and a provenance
probe test executing inside the same pytest process asserted (a) `candidate_snapshot`/
`accession_selector` loaded from the clone and (b) the mutation marker present/absent as declared —
the prior editable-install mistake was not repeated. The exact mutant class:
`derive_candidate_snapshot`'s `associations is None` branch rewritten to treat silence as an empty
set falling through to the census scalar, i.e. absent establishment evidence silently interpreted as
a sole registrant.

| Step | Target | Suite | Result | Elapsed |
|---|---|---|---|---|
| **A** | `09ee442` + mutant | all 205 builder-invoking tests of the failed target + 2 provenance probes | **207 passed — mutant SURVIVED** (reproduces prior M-1) | 26 s |
| **B** | `1c5b015` + same mutant | corrected candidate-snapshot + MR suites + probes | **4 failed / 73 passed — mutant KILLED**, by exactly `test_mr_m10a_…` and the three Group-R59 builder tests | 7 s |
| **C** | `1c5b015` clean | same suites + absent-marker probe | **77 passed** | 7 s |

```text
MR_M10_DERIVATION_MUTANT = KILLED
```

**MR-M10A vs MR-M10B, inspected:** MR-M10A runs the real `build_and_freeze_candidate_snapshot` over
a census world whose otherwise-eligible accession carries a **populated** census scalar and no
establishing evidence; MR-M10B hand-seeds an `unestablished` candidate row past the builder and
proves freeze refusal. The layers are non-redundant — the derivation mutant's output is lawful
`established` state MR-M10B structurally cannot see (Step A proved exactly that), and MR-M10B
catches a hand-seeded row MR-M10A never constructs. Both present, both effective.
`[INDEPENDENTLY_REPRODUCED]`

## 5. M-1 — builder semantics (packet §9 control)

Executed through the **real** builder on disposable catalogs `[INDEPENDENTLY_REPRODUCED]`: an
otherwise-eligible accession with populated census scalar (CIK 2) and no accepted establishment
evidence is **excluded before snapshot entry** with
`excluded_unestablished_registrant_set = 1` reported; `PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED`
is registered with `requires_manual_review`; **zero** candidate accession rows and **zero**
candidate registrant rows exist for it; and the frozen snapshot is **byte-identical**
(`snapshot_id`, `candidate_snapshot_sha256`, all seven family digests, counts) to one built over a
census that never carried the accession — no entity, history, or quota credit. Adding exactly the
establishing full-index evidence makes the **same** accession a lawful single-registrant candidate:
`anchor_cik_numeric = 2`, `registrant_set_completeness = 'established'`, `multi_registrant = 0`, one
`anchor` role row. The mandatory control holds.

## 6. MIN-1 — migration comment / R67 truth

The corrected §5 comments state that **neither** new column enters `REGISTRANT_TABLE_COLUMNS` and
describe the actual accepted R67 binding: membership through the digest's key columns, the
substantive/submitter split through the `role`↔`association_class` CHECK equivalence
(`CHECK ((role = 'submitter_only') = (association_class = 'submitter_only'))` — read in the final
schema), and completeness bound by the freeze trigger making it constant inside any frozen snapshot.
Independently verified against `candidate_identity.py` (byte-unchanged across the entire chain):
`REGISTRANT_TABLE_COLUMNS`, `ACCESSION_TABLE_COLUMNS`, and `SNAPSHOT_CONTENT_FIELDS` carry neither
new column and are unchanged. The underlying mechanics are **true**, not merely truthfully
described: the §8 R67 binding experiments prove relation membership is governed through the digest,
and completeness carries no unbound degree of freedom in a frozen snapshot because the freeze
trigger refuses any non-`established` accession and any registrant row disagreeing with its
accession (probed). No executable semantics changed for MIN-1. `[INDEPENDENTLY_REPRODUCED]`

## 7. MIN-2 — establishment invariant and the lawful transition

**31/31 disposable-catalog probes PASS (0.5 s)**, covering the full packet lifecycle A–N
`[INDEPENDENTLY_REPRODUCED]`:

- **Lawful transitions:** create-unestablished (A/E), attach one/two substantive relations (B/F),
  transition to `established` with factual scalar (C) and with NULL scalar (G) — all inside one
  transaction, the exact shape the FK forces (relation-before-accession refused: proven); both
  states **persist across close/reopen** (D/H). Truthful downgrade-then-delete stays open (L).
- **Refused false states:** INSERT asserting `established` with zero relations (I); deleting the
  final substantive relation while established (J); reclassifying it to `submitter_only` while
  established (K); UPDATE to `established` without a relation (M). All four doors shut with the
  same refusal message; none invents a registrant.
- **R58 guards unaffected:** a second substantive relation under a non-NULL scalar and a scalar
  write-back onto a two-member set both abort.
- **Migration guard (N):** a `0013` catalog seeded with one census row **refuses** `0014`
  (`requires an empty census_accessions`), leaving the catalog intact at head 13 with the row
  untouched.

**Future E0 writer statement (explicit, as required):** the schema **permits** the lawful future E0
transaction shape without another schema change — proven by executing that exact shape (accession
first as the FK requires, relation rows second, the completeness claim last, one transaction) on the
final corrected schema. The **current** writer (`sec/census.py`) inserts census rows at the default
`'unestablished'` and never asserts establishment, so it is untouched by the new guards; **no
current writer performs the establish transition**, correctly, because E0 is unauthorized and the
builder derives establishment from evidence presence at snapshot-build time. Migration `0014`
therefore does not make the accepted future write ordering impossible or self-contradictory.

## 8. MIN-3 — historical digest provenance

Reproduced from a disposable checkout of the genuine pre-correction parent `6fdec2ed…` (module
provenance printed; chain head applied there: **13**) `[INDEPENDENTLY_REPRODUCED]`:

- Running the pre-correction commit's own recorded recipe —
  `s5.write_plan(connection, s5.feasible_plan())` at chain `0013` — persisted exactly
  `anchor=17 / multi=1 / 8ac3c01e…` and `anchor=18 / multi=1 / 03e8736e…` for the two joint fixture
  accessions. The corrected target's "before" literals **equal the values the pre-correction
  implementation actually produced**; the false `5f3f6a57…` literal is **gone** from every test and
  source file (it survives only inside the immutable prior-review artifact, Decision 085, and
  STATUS.md history, which correctly describe it as the abolished false value).
- The three MR-M13 pinned single-registrant literals authenticate against the genuine pre-correction
  `accession_selection_rank(anchor_cik_padded, dashed, seed)` — parameter observed literally named
  `anchor_cik_padded` at `6fdec2ed` — and a **fourth, non-pinned** case
  (CIK 2, `0000000002-19-000003`) produces byte-identical values under old and corrected code.
- The same fixture at chain `0014` reproduces the "after" values (`anchor NULL`, `29f00d58…` /
  `ae4e0091…`), and the standing test re-derives **both** columns from their stated preimages, so
  `before != after` is a consequence, not the assertion.

```text
UNVERIFIABLE_PRECORRECTION_DIGESTS = 0
```

## 9. MIN-4 — reserve per-CIK joint cap

`_caps_preserved` now reads every bundle accession's `substantive_registrants_padded` from the
candidate pool (fail-closed `ValueError` when absent) and `_usage_from` charges `max_base_per_cik`
per truthful registrant while the three accession-domain totals stay keyed by accession. Scenario
probes `[INDEPENDENTLY_REPRODUCED]`: **A** joint accession charges both registrants and counts once
in the accession domain; **B/C** a co-registrant at the cap refuses the joint replacement and one
below the cap admits it; **E** reversed association order gives the identical decision; **F**
single-registrant behaviour unchanged (foreign cap irrelevant, own cap binds); **G** a bundle
accession absent from the governed pool fails closed; plus a **novel three-registrant** case in
which every member is charged and a third member's cap binds. The standing MIN-4 test group (A–G)
also passes. **Residual-path search:** all three per-CIK cap sites — the in-search DFS
(`attachments` = the substantive registrant set), the final usage builder, and reserve
`_usage_from` — attribute a joint filing to every substantive registrant; no reachable
single-attribution cap path remains `[SOURCE_INSPECTION_ONLY]`. Base per-CIK cap value (4) and
research policy unchanged (`pilot_policy.py`, migration `0010` blob-identical across the chain).

## 10. MR-M1…MR-M14 full effectiveness

All fourteen protections inspected against their exact Decision 082 §10.13 definitions (order and
membership invariance asserted on content, not digests alone; each prohibited heuristic's output
asserted unequal to production at the consumer property and the digest; schema-layer cases proven at
the CHECK/trigger level). Executed mutants beyond MR-M10 `[INDEPENDENTLY_REPRODUCED]`:

| Mutant | Killer | Result | Elapsed |
|---|---|---|---|
| first-member primary CIK for a multi set (`_registrant_rows`) | builder co-registrant tests | **KILLED** (2 failures) | 5 s |
| membership-dependent tie-break slot (`accession_registrant_slot`) | **MR-M14** + MR-M8 | **KILLED** (2 failures) | 2 s |
| historical **M20** / **M22** through the accepted campaign runner (source isolation proved by the tool) | — | **KILLED / KILLED**, 38/38 anchors resolved, 0 residue | 23 s / 22 s |

Schema-enforced cases (MR-M7/M9/M12/M10B) re-probed directly: the anchor+multi and
anchor+unestablished states are unrepresentable (CHECK matrix), the submitter is never promotable,
and the freeze counts only `association_class = 'substantive'` rows. **MR-M1…MR-M14 = EFFECTIVE;
MR-M10A = EFFECTIVE; MR-M10B = EFFECTIVE.** No protection is reduced to a later backstop where its
definition requires an earlier layer — MR-M10's load-bearing layer is now the builder.

## 11. R67 relational digest binding

Reproduced with real digest computations `[INDEPENDENTLY_REPRODUCED]`: REMOVE / CHANGE / ADD one
substantive association each change `candidate_registrant_table_sha256` (E3); REORDER leaves it
unchanged; anchor↔associated demotion changes E3. E3 sits inside `SNAPSHOT_CONTENT_FIELDS`, an E3
change moves `candidate_snapshot_sha256` (E4), and an E4 change moves `selection_input_sha256` and
`selection_run_id` through the **real** `build_joint_selection_run_identity` (E5).
`candidate_identity.py` is byte-unchanged across the entire chain, and pure single-registrant
snapshots carry no R46-induced identity delta (§12). The store loader re-derives every stored
tie-break from persisted anchor + completeness and refuses divergence and anchorless-unestablished
rows. **The relational set is genuinely governed and bound; no STOP.**

## 12. Single-registrant nonchange

`SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0` — authenticated against the **genuine
pre-correction implementation** at `6fdec2ed` (not against corrected code reproducing itself): the
three pinned literals plus one non-pinned case are byte-identical old↔new (§8); the sole-registrant
slot is the padded CIK exactly as before; scalar CIK, tie-break, candidate membership, history
attribution, reserve cap (§9 F), and manifest semantics for single-registrant fixtures are
unchanged (targeted battery + fixture component literals `source_observation_set_sha256`,
`candidate_tables_sha256`, `quota_definitions_sha256` unchanged in the reserve-bearing fixture).
`[INDEPENDENTLY_REPRODUCED]`

## 13. R58 / R59 / R60 / R61 / R62 — full representation boundary

- **R58.** Established cardinality 1 → one `anchor` row and the factual scalar; established
  cardinality >1 → scalar/anchor NULL (schema-enforced, probed), all substantive rows `associated`;
  the residual-heuristic sweep over min/max/first-write/`[0]`/submitter/hash selection found only
  R62-correct cap arithmetic and the validated exactly-one-anchor read — **no reachable fabricated
  primary**. The pool validator refuses an accession with neither anchor nor association set.
- **R59.** Unestablished blocks candidacy entirely at the builder (M-1 sequence, §§4–5), the freeze
  trigger, and the loader; fail-closed with the registered reason; never evidence of a sole
  registrant.
- **R60.** The sentinel is the exact string `MULTI_REGISTRANT_NO_SINGLETON`, serialization-only
  (tie-break slot + stored-digest verification), never persisted (INTEGER CIK columns; no writer),
  never an entity/locator/quota contributor, non-digit and length ≠ 10 so it cannot collide with the
  padded-CIK domain; an unestablished set is refused rather than hashed.
- **R61 / manifest item 48.** The affected inventory is exactly **E1–E5**; `snapshot_id`
  (field-tuple carries no registrant value), `entity_tie_break_sha256`, and the R15/R16 preimages
  are registrant-free (asserted against the frozen tuples). Item 48 is the factual sole CIK or NULL
  with no fabricated anchor; Decision 021 not rewritten.
- **R62.** Entity-domain aggregation (history, eligible forms, FYE contributions, entity witnesses,
  conflicts, per-CIK caps, pair support/targets) reaches every substantive registrant; the
  accession-domain totals (`base_total`, `stress_total`, `accession_total`, the multi-registrant
  quota keyed on the dashed accession, pair legs) count one joint filing once — verified in the
  selector's witness derivation, the DFS and final cap accounting, reserve `_usage_from`, and the
  R66 end-to-end test (two entities from exactly two accessions). No row-join multiplication found.
- **Multi-registrant quota** hard at **2**, accession-keyed, domain unchanged
  (`CROSS_CUTTING_QUOTAS` inspected; `pilot_policy.py`/migration `0010` blob-identical).

`[INDEPENDENTLY_REPRODUCED]` for the probed/behavioural rows; `[SOURCE_INSPECTION_ONLY]` for the
sweep conclusions, corroborated by the green targeted battery.

## 14. R65 / R66

**R65:** the `acquisition.py` delta at `6fdec2ed`→`09ee442` is the constant
`FINAL_MIGRATION_VERSION 13 → 14` plus documentation and nothing else (diff read); the standing test
proves the disposable machinery recognizes head `0014` (`chain_is_exact` true, versions 1..14); the
file is byte-unchanged since. No network/M3.2 authority reopened; tracked switches remain
`false`/`false`. **R66:** the `offline_execution.py` delta is strictly the caller — one governed
read at `association_class = 'substantive'` feeding `paired_accessions_from_rows`'s fourth argument,
plus documentation; proofs A–E pass, the joint pair reaches entities `(1, 901)` with two legs
counting as two accessions, and an absent association set yields zero pair credit.
`[COMMITTED_EVIDENCE_VERIFIED + INDEPENDENTLY_REPRODUCED via the standing tests]`

## 15. R68 — migration-policy identity movement

Measured by building the reserve-bearing manifest fixture at **both** targets and enumerating every
identity-bearing value `[INDEPENDENTLY_REPRODUCED]`:

- The fixture's `ManifestComponents` carries **eight** components. Exactly **one** moved:
  `selector_policy_sha256` `29783a60…` → `cd237060…` (matching the claimed literals). The **other
  seven** — `source_observation_set_sha256`, `candidate_tables_sha256`, `quota_definitions_sha256`,
  `selected_entities_sha256`, `selected_accessions_sha256`, `reserves_sha256`,
  `quota_report_sha256` — are **byte-identical**.
- `root_manifest_sha256` `afe6fd9e…` → `129b8636…` and `manifest_id` `44de5d26…` → `b07f4965…`
  moved as **derived** identities of the moved component. `selection_result_sha256` is
  **unchanged** (`1c7d8b8c…`), and the canonical-JSON length is 275547 on both sides.
- The causal path is source-verified: migration `0014` bytes → provenance `checksum_sha256`
  (stored checksum equals `sha256` of the final corrected file bytes — recomputed) →
  `migration_chain_sha256` over `MIGRATION_CHAIN_COLUMNS` → `selector_policy_sha256` → root /
  `manifest_id`.
- **No unclaimed component moved.** The movement is confined to E5's policy binding and is
  separately attributable from R46 registrant semantics (whose single-registrant identities are
  byte-identical, §12), exactly as Decision 086 R68 accepts.

## 16. Persistence / reload / reconstruction / replay, and E1–E8

`run_execution_rehearsal` executed directly on a disposable workspace: **E1–E8 = 8/8 PASS**
(complete; builder-derived disposition `INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE` as designed; bridge
violation count 0), exercising freeze, refusal, feasible selection, fail-closed infeasibility,
reserve/disposition totality, reconstruction-mismatch refusal, seal/manifest atomicity, and
write-free replay over single **and** multi state. The selection-store suite (persist → reload →
reconstruct → replay; loader re-derivation of every tie-break; unestablished refusal) passed in the
targeted battery, so no first-write-dependent state can reappear after persistence.
`[INDEPENDENTLY_REPRODUCED]`

## 17. Migration 0014 — complete review

Position exactly `0014`; `0001`–`0013` byte-identical to the accepted `m3.2-complete` baseline
blobs (13/13). Fresh-build (`0001`–`0014`) and upgrade-path (`0013` then `0014`) schemas are
**byte-identical over all 225 objects**; `PRAGMA foreign_key_check` 0 violations and
`integrity_check` ok on both; `legacy_alter_table` restored to 0 after migration; all intended
tables/relations/CHECKs/triggers present (the R58 relation + index, the four establishment doors,
the two scalar guards, the replaced freeze trigger, the selection-attachment trigger); the
Decision-021 §15.1 selection-run triggers and every unrelated index/guard survive; the empty-state
precondition is operational (probe N); and the provenance chain recognizes the final corrected
`0014` bytes (stored checksum == file hash). The accepted private M3.2 catalog was never opened.
`[INDEPENDENTLY_REPRODUCED]`

## 18. Prohibited nonchange

Blob-verified across the chain (`5231359f` → HEAD unless stated): `cohorts.py`, `pilot_policy.py`,
migrations `0001`–`0013`, `Docs/preregistration.md` — unchanged (`cohorts.py`/`preregistration.md`
also identical to the `m3.2-complete` baseline; `pilot_policy.py`'s baseline delta predates this
chain in the owner-accepted M3.3-I/R commit `6f87abc`). Historical Decisions 001–084 byte-unchanged;
the registry is purely additive. The frozen prior-review artifact and the accepted M1–M38 campaign
artifact are blob-identical since their publication commits. `candidate_identity.py` and the
production `candidate_snapshot.py` are byte-unchanged; `acquisition.py` beyond accepted R65 and
`offline_execution.py` beyond accepted R66 are unchanged. No network/SEC transport module changed
anywhere in the chain. The D081 private evidence and accepted M3.2 evidence root were never
referenced or resolved (no relevant environment set). Decisions 085 and 086 are the expected new
governance records. Migration `0015` **ABSENT**; **no real E0 state** was created (all
`census_accession_registrants` writes occurred in disposable scratchpad catalogs); no SEC/HTTP
request was made; `m3.2-complete` unmoved; no tag exists at HEAD. `[COMMITTED_EVIDENCE_VERIFIED]`

## 19. Validation executed (with elapsed times)

| Step | Result | Elapsed |
|---|---|---|
| `verify_target.py` (HEAD 8/8 + target 3/3) + `make context` | PASS | ~1 s |
| Three disposable clones created and tree-verified | — | 2 s |
| **Step A** — exact MR-M10 mutant vs old target's tests | 207 passed — **SURVIVED** | 26 s |
| **Step B** — same mutant vs corrected suites | 4 failed / 73 passed — **KILLED** | 7 s |
| **Step C** — corrected suites clean | 77 passed | 7 s |
| First-member-anchor mutant | **KILLED** | 5 s |
| Membership-dependent-slot mutant | **KILLED** (MR-M14 + MR-M8) | 2 s |
| Campaign `--verify-only` (38 anchors) | 38/38 resolved | <1 s |
| Historical M20 / M22 live re-execution | **KILLED / KILLED**, 0 residue | 23 s / 22 s |
| Independent probes (MIN-2 A–N, builder control, R67 binding, MIN-4 caps) | **31/31 PASS** | 0.5 s |
| MIN-3 reproduction at `6fdec2ed` (chain 13) and corrected tree (chain 14) | all literals reproduced | <1 s each |
| R68 fixture dump at both targets + full component diff | 1 moved / 7 identical / derived ids as claimed | ~8 s |
| Migration fresh-vs-upgrade equivalence + integrity + checksum probes | all clean (225 objects) | <1 s |
| Targeted battery — 16 affected test files, serial | **1568 passed / 1 pre-existing skip** | 90 s |
| Direct `run_execution_rehearsal` (E1–E8) | **8/8 PASS** | 8 s |
| `make check-fast` (WORKERS=7) — the one routine run | **exit 0** — every gate green | 72 s |

The `make check-fast` terminal summary scrolled past this reviewer's own output capture; per the
R69 rule it was **not** re-run to recover cosmetic output — exit 0 on the unchanged tree is the
acceptance fact (see OBS-R3). After verdict freeze, only the documentation/publication gates were
run for the review commit itself (`make links`, `make decision-refs`, `make secrets`,
`make hygiene`, `git diff --check`), recorded in the publication commit.

## 20. Findings

| ID | Severity | Finding |
|---|---|---|
| OBS-R1 | OBSERVATION | Prior-review observations OBS-1…OBS-6 remain recorded and remain unauthorized for correction (D085 §3); spot-rechecked and still accurate and non-gating — e.g. `AccessionDiagnostic.registrant_slot_padded` still names the sentinel "padded" (in-memory only), and `Docs/sec_data_dictionary.md` remains truthfully self-scoped "through migration `0013`" while `0014` exists. |
| OBS-R2 | OBSERVATION | The abolished false literal `5f3f6a57…` correctly survives **only** inside immutable governance/evidence records (the frozen prior review, Decision 085, STATUS.md history) that describe it as false; it is absent from every test and source file. |
| OBS-R3 | OBSERVATION | This session's single `make check-fast` returned exit 0 but its terminal summary line was truncated by the reviewer's own output capture; consistent with R69 it was not re-run merely to recover the summary. The independently counted evidence is the serial 16-file battery (1568 passed / 1 pre-existing skip) plus exit 0 across every gate. |

**BLOCKER 0 / MAJOR 0 / MINOR 0 / OPTIMIZATION 0 / OBSERVATION 3.**

## 21. Formal acceptance conditions — disposition

| Condition | Disposition |
|---|---|
| Model-identity gate: genuine Fable 5 | SATISFIED (`claude-fable-5`) |
| Target/authority chain valid; correction bounded to M-1, MIN-1–MIN-4 | SATISFIED |
| M-1: exact derivation mutant SURVIVES old tests, KILLED by corrected tests, real code passes | SATISFIED — `MR_M10_DERIVATION_MUTANT = KILLED` |
| MR-M10A and MR-M10B both present, non-redundant, effective | SATISFIED |
| Builder-semantics control (exclude → establish → candidate) | SATISFIED |
| MIN-1: comments truthful AND mechanics true | SATISFIED |
| MIN-2: false state unpersistable; lawful lifecycle A–N; E0 shape possible without schema change | SATISFIED |
| MIN-3: `UNVERIFIABLE_PRECORRECTION_DIGESTS = 0`; false literal gone; recipes reproducible | SATISFIED |
| MIN-4: cap charges every substantive registrant; accession-domain counts once; fail-closed pool miss; A–G | SATISFIED |
| MR-M1…MR-M14 all effective at exact definitions | SATISFIED |
| R67 binding: remove/change/add move E3→E4→E5; reorder does not; `candidate_identity.py` unchanged | SATISFIED (no STOP) |
| R68: only the claimed migration-policy values moved; other seven components byte-identical | SATISFIED |
| `SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0` (authenticated against genuine old code) | SATISFIED |
| R58/R59/R60 representation; no fabricated primary anywhere | SATISFIED |
| R61 inventory exactly E1–E5; four preserved identities registrant-free | SATISFIED |
| R62 entity/accession domains; quota hard at 2 accession-keyed; no double counting | SATISFIED |
| R65 constant-only; R66 caller-only; proofs pass | SATISFIED |
| Manifest item 48 factual-or-NULL, no replacement anchor | SATISFIED |
| E1–E8 = 8/8 PASS; persistence/reload/reconstruction/write-free replay | SATISFIED |
| Migration `0014` complete review (position, equivalence, integrity, guards, provenance) | SATISFIED |
| Prohibited nonchange (incl. `0015` absent, tag unmoved, no network, no real E0 state) | SATISFIED |
| One routine `make check-fast`, zero failures | SATISFIED (exit 0) |

**VERDICT: PASS.**

```text
M3_3_D085_R46_GENUINE_FABLE_REREVIEW_PASSED_READY_FOR_OWNER_ACCEPTANCE
```

## 22. Next owner action

Return to Sol/GPT. This review corrected nothing and authorizes nothing. **A PASS does not itself
satisfy R49 condition B**: condition B becomes satisfied only when Sol/GPT explicitly owner-accepts
the corrected R46 implementation on the strength of this passed rereview. M3.3-E0, E1, E2, M3.4,
migration `0015`, Review A, Review B, and the document adjudication all remain unauthorized;
network, SEC, and HTTP authority remains NONE at `REQUEST_CEILING 0`; `m3.2-complete` is unmoved
and no tag was created.
