# M3.3 Corrected Contract — Fresh Independent Review (target `c8acfef`)

```text
STATUS: COMPLETE — INDEPENDENT REVIEW RECORD, NO AUTHORITY
DATE: 2026-08-13
REVIEWER: fresh independent Claude session (Fable 5, maximum effort), non-author
REVIEWED TARGET (frozen): c8acfef59006f8812eb5678d3f61d852d6789f07
  tree dbeb9eb6e174833492e516a94b290d85e7d40867
VERDICT: M3_3_CORRECTED_CONTRACT_FRESH_INDEPENDENT_REVIEW_FAILED
FINDINGS: BLOCKER 0 · MAJOR 1 · MINOR 1 · OPTIMIZATION 0 · OBSERVATION 5
```

**What this document is.** The complete record of the fresh independent review of the corrected
M3.3 contract ([`Milestones/contracts/m3_3.md`](../../../Milestones/contracts/m3_3.md)) after accepted
[Decision 067](../../Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md), performed
under the owner's review packet of 2026-08-13. It records findings; it fixes nothing, accepts
nothing, authorizes nothing, and is not itself an authority. Under the packet's verdict standard
(`PASS` requires BLOCKER 0 / MAJOR 0 / MINOR 0), the verdict is **FAIL**: one MAJOR and one MINOR
defect are recorded below with exact reproduction references. Every other reviewed dimension —
Decision 067 faithfulness, the complete OR-1 identity graph, R16, the OR-2 135-column mapping,
fail-closed semantics, the E0/E1/E2/M3.4 separations, OBS-1, migration sufficiency, R3 path
classification, authority-leak audit, and both current-state reviews — passed.

---

## 1. Independence attestation

- **One fresh review epoch.** The session was `/clear`ed; the first user input visible to this
  epoch was the review packet itself. No conclusion was inherited from any prior session; every
  prior artifact read (contract, Decision 067, GV/GR reports, proposal, inventory) was treated as
  evidence and independently verified against migrations, source modules, and accepted decisions.
- **No subagents, no delegation, no parallel Claude workflows, no dynamic workflows** were used at
  any point. All reading, verification, and analysis were performed inline in this one session.
- **No authorship.** This session authored none of: Decision 067; the corrected M3.3 contract; the
  M3.3-G governance foundation; the M3.3-GR proposal; the GV/GV2 reports; any M3.3 implementation,
  test, or execution evidence.
- **Boundaries honoured.** No network access, no SEC request, no reacquisition, no private-evidence
  access, no `EV_ROOT` access, no catalog opened, no offline parser run, no snapshot, no selection,
  no manifest, no root, no M3.3-I/R, no M3.3-E0, no M3.3-E1. No executable code, test, migration,
  configuration, contract, decision, or governance surface was modified. The only repository write
  is this review artifact.

## 2. Frozen entry state — verified live

All values verified by direct read-only `git` inspection before any substantive reading. No fetch,
no pull.

| Fact | Required | Observed | Match |
|---|---|---|---|
| Branch | `main` | `main` | ✓ |
| HEAD | `c8acfef59006f8812eb5678d3f61d852d6789f07` | same | ✓ |
| Tree | `dbeb9eb6e174833492e516a94b290d85e7d40867` | same | ✓ |
| `origin/main` | same as HEAD | same | ✓ |
| Working tree | clean | clean (empty porcelain; no stash) | ✓ |
| Parent | `0401bfdc4669db9237e78548fbd572a0aa14a255` | same | ✓ |
| Subject | `Record M3.3 snapshot authority and offline-parse rulings` | same | ✓ |
| `m3.2-complete` | unchanged/immutable | tag object `2865a147…`, peeled `2185f583…` — matches contract §2 | ✓ |

`scripts/context_snapshot.sh` (read-only) confirmed migrations `0001`–`0013`, latest decision 067,
tracked network switches `false`/`false`, and `NEXT_AUTHORIZED_ACTION` = this review. The
`Milestones/STATUS.md` markers `DECISION_067_STATUS`, `DECISION_067_CURRENT_STATE`,
`M3_3_DECISION_067_GOVERNANCE_STATUS`, `IMPLEMENTATION_AUTHORIZATION`, and
`NEXT_AUTHORIZED_ACTION` match the packet's required authority state exactly: contract acceptance
NO; implementation NO; real private parse NO; real snapshot NO; network NONE; reacquisition NONE;
migration none; M3.4 NO; M3.3-I/R, E0, E1 not authorized; OR-1 and OR-2 resolved by Decision 067.

## 3. Authority read

Read in full: `Milestones/contracts/m3_3.md` (1078 lines); Decision 067 (576 lines);
`Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md` (951 lines, disposition banner and body);
`Docs/m3/m3_3_governance_foundation_inventory.md`; Decisions 013, 016, 023, 065, 066 in full;
Decision 021 §§5–13, 16–19 and Decision 019 §§9–10, Decision 018 §5.2, Decision 029 header/status
(M3.1-scoped; no operative bearing on this contract beyond the rehearsal-spec structure);
`Docs/m3/limitations_register.md` (D021-L2, D021-L7, D023-O1, D067-L1, M3-L02/L03/L15 entries
verbatim); `Docs/m3/operator_runbook.md` §§28a–31 and structure; `Milestones/milestone_03_master_plan.md`
Phase M3.3 §§1–36 and global §§1–14; `Docs/architecture_map.md` §0 and §10;
`Docs/change_impact_map.md` (Decision 067 section); `Docs/decision_index.md` (M3.3 section);
`Docs/Decisions/decision_registry.md` (row 067 and the controlling-record row);
`Milestones/contracts/README.md` (M3.3 entry); `Docs/m3/offline_rehearsal_spec.md` (structure, E1–E8,
§9); `Docs/m3/execution_receipt_spec.md` (modes). `Milestones/STATUS.md` banner, current markers, and
marker-governance rules.

Code and schema inspected read-only for feasibility and factual claims: migrations `0001`–`0009`
and `0010`–`0013` (structure), with `0002`, `0003`, `0004`, `0005`, `0006`, `0007`, `0008`, `0009`
read in full or in the governing parts; `src/disclosure_drift/release/hashing.py` (complete);
`pilot_policy.py` (complete); `cohorts.py` (seed); `sec/census.py` (persist path, ID derivations,
normalization and write set); `sec/census_orchestrator.py` (`_retrieve_and_parse`, transport
construction); `sec/parsers/` (import surface); `sec/entity_selector.py` / `sec/accession_selector.py`
(tie-break implementations); `storage/catalog.py` and `storage/sqlite.py` (connection modes);
`m3/recovery.py` (strict read-only usage); `cli.py` (exit codes; `read_only_connection` call sites);
`sec/source_registry.py` (planned source IDs).

## 4. Findings

### MAJ-1 (MAJOR) — Contract §10.2 item 2's E0 permitted-table list is incompatible with the accepted parse machinery R13 permits E0 to reuse; a compliant real E0 is not executable in principle

**Claim.** The corrected contract's M3.3-E0 definition confines all E0 writes to nine named tables
plus the `census_plan_sources.parser_state` transition, and makes "any attempt to write outside
item 2's table list" a stop condition (contract §10.2 item 2 and item 12; §19; §23 item 23 context).
But the accepted `CensusCatalog` persistence machinery — which contract §1.1 R13 and Decision 067
§4.2 expressly permit E0 to reuse, and which contract §20 forbids modifying or replacing ("not a
second parser, not a second catalog writer, and not a modification of `sec/census.py`…") — writes,
as an inseparable part of parsing the accepted planned sources, at least six further tables that are
**not** in item 2's list. Over the real accepted 76-object corpus these writes are effectively
certain, so a real E0 as specified either stops immediately or must violate a prohibition. Because
§10.2 also rules that an implementation packet "may narrow but never widen" the E0 definition, no
later bounded packet can lawfully repair this; only an owner contract correction can.

**Evidence — the permitted list** (`Milestones/contracts/m3_3.md` §10.2 item 2, lines 410):
`census_parser_runs`, `census_parsed_records`, `census_structural_observations`,
`census_registrants`, `census_registrant_observations`, `census_accessions`,
`census_accession_observations`, `census_accession_field_resolutions`,
`census_accession_cohort_resolutions` — nine tables — "plus the `census_plan_sources.parser_state`
transition", with item 12 (line 420) making "any attempt to write outside item 2's table list" a
stop condition, restated at §19 (lines 614–621).

**Evidence — the actual write set of the reused machinery** (`src/disclosure_drift/sec/census.py`,
all inside `CensusCatalog.persist()`'s single transaction, lines 172–217):

| Table written | Where | Trigger on the real corpus | In item 2's list? |
|---|---|---|---|
| `census_quarantined_records` | `_insert_quarantine`, line 483; loop at 192–193 | any malformed record — the accepted preserve-not-skip handling (migration `0005` header) | **NO** |
| `census_historical_references` | `_insert_historical_references`, line 1123; called at line 195 | the bulk-submissions parse's per-registrant historical file references — the very rows that represent GV2-19's never-acquired state (`retrieval_status = 'not_retrieved'`, migration `0003` lines 61–75); near-certain non-empty over a 2009–2026 corpus | **NO** |
| `census_malformed_historical_references` | line 1096 | any malformed reference entry (migration `0005` lines 40–53: "preserved here instead of being skipped") | **NO** |
| `census_candidate_lineage_edges` | `_candidate_edges`, line 1202; called from `_normalize_registrant` (573–574) and `_normalize_alias` (610–611) | any company name or ticker shared across >1 CIK — the succession/former-name evidence the adopted OR-2 basis reads for `history_class` (proposal §D source read order item 7; §E) | **NO** |
| `census_calendar_days` | `_normalize_calendar`, line 972; dispatch at 518–519 | parsing the planned `sec_edgar_filing_calendar` source (`sec/source_registry.py:251`) — its entire parse product | **NO** |
| `reference_sic_codes` | `_normalize_sic`, line 951 — an `INSERT OR REPLACE` | parsing the planned `sec_sic_code_list` source (`sec/source_registry.py:227`) — its entire parse product | **NO** |

**Why no compliant escape exists.**

1. *Skip the offending sources?* Item 6's completeness proof is per-planned-source ("which planned
   sources parsed, which legitimately produced zero structural rows, and which remain failed or
   unavailable") and R13/§8.1 correction 2 bind "each planned source" to its plan-row
   `observation_id`; no "deliberately skipped" category exists. Even a bulk-submissions-only E0
   would still hit `census_historical_references`, `census_candidate_lineage_edges`, and the
   quarantine path.
2. *Filter inside the driver?* `persist()` is atomic over the whole `ParseOutcome`; suppressing the
   companion writes requires either modifying `sec/census.py` (prohibited, contract §20) or writing
   a second persistence layer ("not a second catalog writer", §20). Passing empty
   `historical_references` is driver-controllable but would silently omit part of the actual parse
   result — contradicting R14's "recomputable from the **actual** authorized offline parse result",
   the completeness proof, and the adopted mapping's own history-class read set — and would still
   leave the lineage-edge, calendar, and SIC-list writes unavoidable.
3. *Fix it in the implementation packet?* §10.2: "The E0 definition this contract fixes, and which
   an implementation packet may narrow but never widen." Widening item 2's list is exactly a
   widening. Only an owner correction to the contract can resolve it.

**Secondary facet — the 70 quarterly full-index sources.** The accepted census machinery parses
full-index content only through the index path (`census_index_instances` /
`census_index_reconciliation` — `sec/census_orchestrator.py` returns no `ParseOutcome` for
`sec_full_index_company` in `_retrieve_and_parse`, lines 473–533). Both destinations are excluded
(item 2 "no `census_index_instances` write"; §8.1 correction 6; the reconciliation table is not in
the list). The contract does not state what "parsed" means for those 70 plan rows — what
`parser_state` transition they receive, or how the per-source completeness proof classifies them.
This is part of the same boundary-definition defect and should be fixed in the same correction.

**Consequences for the contract's own claims.** Internal coherence (review objective A) fails
between §1.1 R13's reuse permission and §10.2 item 2/item 12; executability in principle (objective
H) fails for E0 as specified. No authority leaks, no ambiguous private state can result (every path
fails closed loudly, and E0 sits behind contract acceptance, an I/R packet, a rehearsal, an
independent review, and a separate owner gate), and no migration is needed for the fix (all six
tables already exist — migrations `0001`–`0006`). Hence **MAJOR**, not BLOCKER — but it must be
corrected by the owner before acceptance, because acceptance would freeze an E0 definition that its
own implementation packet is forbidden to repair.

**Suggested shape of the correction (for the owner; not applied here).** Either widen item 2 to the
exact write set of the accepted machinery per source class (naming
`census_quarantined_records`, `census_historical_references`, `census_malformed_historical_references`,
`census_candidate_lineage_edges`, `census_calendar_days`, and the `reference_sic_codes` upsert, with
whatever exclusions the owner intends), or rule explicitly which planned sources E0 parses and how
the remainder (including the 70 index sources) are dispositioned in `parser_state` and the
completeness proof — and synchronize item 12's stop, §19, §26 item 2's target-table containment
test, and §29 accordingly.

### MIN-1 (MINOR) — Contract §1.1 R12 row misstates the ruled and applied architecture-map scope as "§10.2"; the ruling and the applied correction target §10.1

**Claim.** The contract's R12 row (§1.1, line 72) states the stale current-state claims were
corrected "scoped to `Docs/architecture_map.md` and specifically to §0's Milestone 3 row and
**§10.2**'s current `Status` bullet". Every other record of the same ruling says **§10.1**, and the
applied correction is in §10.1.

**Evidence.**

- `Milestones/STATUS.md`, `M3_3_GR_GOVERNANCE_STATUS` marker: "R12 CURRENT-STATE ARCHITECTURE MAP
  (… scoped to Docs/architecture_map.md section 0's Milestone 3 row and section **10.1**'s current
  Status bullet …) — APPLIED 2026-08-13".
- `Docs/m3/m3_3_governance_foundation_inventory.md` §K, closure note: "scoped to
  `Docs/architecture_map.md` §0's Milestone 3 row and **§10.1**'s current `Status` bullet … The
  correction was applied on 2026-08-13"; the original finding names "§10.1's `Status` bullet
  (line 418)"; §G's OR-12 row points at "`Docs/architecture_map.md` §0, §10.1".
- `Docs/architecture_map.md` as corrected: the updated current-state `Status` bullet is in
  **§10.1** (lines 440–445 — "owner-accepted and complete … Gate F has since been signed … see §0's
  Milestone 3 row and Decision 065 …"). §10.2's `Status` bullet (line 460, "accepted and published;
  the grant is exhausted") is one line, was never stale, and was not the correction target.

**Effect.** An operative contract surface misstates the scope of an owner ruling (faithfulness,
objective C; internal coherence, objective A). Harmless to authority and to every preimage, but a
future session auditing R12 compliance against §10.2 would find nothing and could conclude the
correction was mis-applied. One-token correction ("§10.2" → "§10.1") under an authorized bounded
edit. Not downgraded to OBSERVATION because the error is in the contract's operative ruling table,
not in a historical narrative.

### OBS-A (OBSERVATION) — §30 "Both reviews" after three listed reviews

Contract §30 opens "**Three required reviews**…" (M3.3A; post-E0; M3.3B) and then says "**Both
reviews must additionally perform, and report on, two distinct checks**" (residue scan; semantic
review). "Both" is residue of the pre-Decision-067 two-review structure. The referent is
recoverable — `Milestones/milestone_03_master_plan.md` M3.3 §26 states the middle review was added
by Decision 067 §11 and "the two originally specified are unchanged", so "both" = the M3.3A and
M3.3B reviews — and no reading lets either of those two evade the obligation. Recommend rewording
("The M3.3A and M3.3B reviews must additionally…") at the next authorized edit.

### OBS-B (OBSERVATION) — R16's "<the exact candidate evidence rows substantively used>" versus the adopted mechanical row-set rule

Decision 067 §7.2 and contract §1.1 R16 describe `contributing_evidence_sha256`'s row set as "EXACT
candidate evidence rows substantively used to establish this resolution". The adopted normative
OR-1 basis states the mechanical rule: proposal §A.12 — "<that parent's rows for that dimension>" —
and §C.1 step 4 recomputes "from the persisted evidence rows for that parent and dimension". Under
Decision 016 §4 the evidence tables contain exactly the contributing rows ("one row per contributing
observation"), so the two formulations coincide and the digest is recomputable from persisted rows
alone; the recomputability requirement excludes any "rows the in-memory procedure happened to
consult" reading. Governed; recorded because the compressed R16 phrasing could invite a narrower
(winning-only) misreading. Recommend the M3.3-I/R packet pin the membership query verbatim in the
§26 item 3 preimage-pinning tests.

### OBS-C (OBSERVATION) — E1/E2 naming collision between rehearsal scenarios and real-execution gates

"E1–E8" names the offline rehearsal scenarios (`offline_rehearsal_spec.md` Part II) while
"M3.3-E0/E1" and "E2 authorization" name real-execution gates (contract §10.2; §1.2 OR-6; §16).
Every occurrence reviewed is disambiguated by context or prefix, and no obligation is ambiguous;
recorded because future packets will mix both vocabularies. Recommend consistently prefixed forms
(M3.3-E1, M3.3-E2) on future operative surfaces.

### OBS-D (OBSERVATION) — Master plan M3.3 §9's path-category list omits the offline-parse driver category

`Milestones/milestone_03_master_plan.md` M3.3 §9 lists the builder module, rehearsal harness, CLI
subcommand, receipts, and docs — but not the offline metadata parse driver module that the same
plan's §2, contract §6 item 2/§20, and Decision 067 §4.3 place in scope. Decision 067 controls, and
the plan's §2 already includes the driver, so no behavioural conflict exists; a planning-level list
was not extended. Correctable in a later authorized synchronization pass.

### OBS-E (OBSERVATION) — Adopted proposal §B.2 says "the four snapshot timestamps"; the schema and the proposal's own tallies require three

`pilot_candidate_snapshots` carries exactly three timestamp columns (`created_at_utc`,
`frozen_at_utc`, `invalidated_at_utc` — migration `0009` lines 76–78), and §B.2's per-table
excluded tally (7/3/3/2/3/3/3/3 = 27) balances only with three. The narrative words "the four
snapshot timestamps" are a miscount; every column-level disposition in §§A, B, D is correct and was
verified against migration `0009` verbatim (see §6 below). Historical-evidence text, adopted
"subject to every correction"; the hash membership is fixed by the per-column tables, not by this
sentence.

## 5. Decision 067 faithfulness (packet §5)

**PASS**, with the internal-composition caveat recorded as MAJ-1. Verified clause-by-clause:

- **R13** (contract §1.1 = D067 §4.1–4.3): prohibition list identical (no HTTP client, no
  transport, no network, no SEC request, no reacquisition, no re-retrieval, no filing-body work, no
  CompanyFacts, no Frames, no new source evidence, failed/unavailable preserved, no fabrication);
  `census_plan_sources.observation_id` binding incl. the two bulk-submissions objects; reuse list
  identical; driver permitted-in-scope but not authorized. MAJ-1 concerns the contract's own §10.2
  item 2 choice under D067 §11.2's mandate, not a mis-transcription of R13.
- **R14** (contract §1.1/§10.2 = D067 §5): all four post-parse rules present; D021 §8.1's empty-set
  permission retained and not widened.
- **R15** (contract §1.1/§10.1 = D067 §6): ALT-3; the eight Decision 016 §4 fields retained; no
  removal, no surrogate; D067-L1 recorded in the register with the exact non-invariance statement
  and no acquisition authority.
- **R16** (contract §1.1/§10.1/§26 = D067 §7): domain `pilot_candidate_evidence_row` over R15's
  eight fields; canonical representation already produced for persistence, no second normalization,
  no second hashing implementation; exclusions identical (`evidence_id`, `snapshot_id`, parent key,
  `recorded_at_utc`, `detail`, `census_run_id`, paths, physical bytes, approval/publication state);
  content identity not row uniqueness; the two-step candidate-layer resolution digest; census
  digest never substituted; five analogue-less dimensions not exempt; tie-breaks unchanged.
- **OQ-3 / OQ-4 / OQ-6 / OQ-8** (contract §10.1 = D067 §8): fail-closed collision with no
  `INSERT OR REPLACE`/`INSERT OR IGNORE`/silent recognize-and-return; `snapshot_id` excluded from
  the seven family digests and bound once in `candidate_snapshot_sha256`;
  `coverage_policy_version = pilot-coverage/1.0`; roles `winning`/`competing`/`supporting` with
  migration `0009`'s CHECK (lines 299, 320) governing and Decision 016 §4's "e.g." wording recorded
  as illustrative.
- **No operative contradiction** of any ruling was found outside MAJ-1/MIN-1; the E0 gate, the
  independent read-only verification, and the no-automatic-progression rules are carried on every
  operative surface (contract §§2, 6, 7, 10.2, 23, 30, 33, 34, 36; runbook §§28a–29; master plan
  M3.3 §§2, 5, 6, 26, 36).

## 6. OR-1 — complete identity graph (packet §6)

**PASS.** All twenty-three identity constructions verified as governed, against migration `0009`
verbatim, `release/hashing.py`, Decision 021 §§5, 8.1, 8.2, Decision 016 §§1, 4, 8, and the adopted
proposal §§A–C as corrected:

1–2. `coverage_window_sha256` (five fields; `include_open_quarter` forced `0` by the `0009` CHECK)
and `input_observation_set_sha256` (domain `census_source_observation_content`; the six-column
tuple identical to Decision 021 §8.1; the cited set = distinct union of `source_observation_id`
over both evidence tables — §8.1's own definition verbatim; the 34-column
`census_source_observations` classification re-counted against migrations `0002`/`0008`: 5 hashed +
derived fingerprint + 29 excluded, names matching). The **definitional identity** with
`source_observation_set_sha256` is coherent both before `INSERT` (in-memory cited set, required
because `snapshot_id` is content-derived at row creation — `0009` lines 31–37) and as independently
recomputed from persisted candidate evidence inside the same authoritative transaction (R5),
fail-closed on mismatch; the later S6 computation reads the same persisted preimage, so equality is
well-defined. The five-column structural-fingerprint partition rule (D021 §8.1, frozen at v0.3) is
reused unchanged, with R14 governing the real-corpus non-vacuity.
3. `snapshot_id` (five fields; three policy constants verified in `pilot_policy.py:41–43`; both
digest inputs computed strictly earlier; `census_run_id` excluded).
4–10. The seven family digests: frozen tuples checked column-by-column against `0009` — entities
23/26 (excl. `snapshot_id`, `recorded_at_utc`, `detail`), accessions 32/35, registrants 6/8,
evidence 8/13 (excl. `evidence_id`, `snapshot_id`, `recorded_at_utc`; `source_observation_id` and
`parsed_record_id` transitively bound through `evidence_sha256` only), reasons 3/6 each. No
substantive column unbound; none bound twice under two rules; the two deliberate redundancies
(evidence fields alongside `evidence_sha256`; counts alongside the freeze trigger) are
single-derivation, per D021 §7.4's accepted pattern.
11. `candidate_snapshot_sha256` (twelve fields incl. `snapshot_id` once — OQ-4 — and both counts;
excludes itself; `0009`'s frozen-state CHECK independently requires all nine content digests).
12–13. `evidence_sha256` on both evidence tables — R15/R16 as above.
14–21. The eight `*_resolution_sha256` columns (entities: size, industry, history,
primary_universe; accessions: filing_date, cohort, xbrl, amendment_purpose — exactly the schema's
set; `0009` presence-CHECKs tie each to its resolved value, matching R16 §7.4's NULL rule; the
freeze trigger additionally requires winning/supporting evidence backing for every resolved
dimension, lines 874–936). Deterministic ordering is supplied by `hash_table` itself (renders then
sorts rows — `hashing.py:77–87`); tied/duplicate triples hash deterministically; membership is
mechanical (OBS-B).
22–23. Tie-break hashes: `entity_selector.selection_rank` (`SHA256(seed|cik_padded)`,
`entity_selector.py:81–89`) and `accession_selector.accession_selection_rank`
(`SHA256(seed|anchor_cik_padded|accession_number_dashed)`, `accession_selector.py:364–380`) match
their accepted definitions (D018 §5.2 verbatim); dashed form canonical; associated registrants
excluded.

Cross-cutting: no timestamp, path, approval/publication state, operational event ID, `census_run_id`,
`detail`, or physical SQLite byte enters any of the twenty-three (D016 §8 / D021 §5 exclusions
traced per digest); the graph is acyclic (the one apparent back-edge — evidence rows under a
`snapshot_id` that depends on `input_observation_set_sha256` — hashes census content only, and the
cited set is fixed in memory before `INSERT`); no digest depends on SQLite version or file bytes
(`hash_table` is a logical row digest; `hashing.py` touches no file); lowercase-64-hex enforced by
`0009` CHECKs; `NULL_SENTINEL` (`"\x00null"`) keeps SQL NULL distinct. The proposal's 135-column
treatment tally (96 INCLUDED / 12 TRANSITIVE / 27 EXCLUDED) re-added per table and confirmed
arithmetically consistent with the schema (28+26+35+8+13+13+6+6 = 135), with the one narrative
miscount recorded as OBS-E.

## 7. R16 resolution-hash review (packet §7)

**PASS.** Two-step construction verified (D067 §7.2; contract §1.1): step-1 domain
`pilot_candidate_resolution_evidence` over `(evidence_role, precedence, evidence_sha256)`;
step-2 domain `pilot_candidate_resolution` over `(classification_dimension,
contributing_evidence_sha256, evidence_policy_version, resolved_value)`, one canonical row. All
eight dimensions covered; the census `resolution_sha256` (`census_accession_field_resolutions` /
`census_accession_cohort_resolutions`, migration `0006`) is never substituted (contract §8.1
correction 7; §26 item 3 requires the negative test); the five analogue-less dimensions (GV2-18)
are not exempt; required-but-unestablishable values fail closed (§7.4; contract §23 item 27);
`contributing_evidence_sha256` is intermediate, unpersisted, and recomputable from persisted rows.
Row-set membership is mechanically determinable under the adopted basis (OBS-B records the wording
divergence and the recommended pinning).

## 8. OR-2 — 135-column mapping review (packet §8)

**PASS**, as modified by Decision 067 §10 — with the caveat that MAJ-1's resolution will determine
*when* the parse-layer sources become populated, not *how* any column is derived. Verified:

- The 135-column count and every per-table column list re-derived from migration `0009` verbatim
  (28/26/35/8/13/13/6/6); every writable field carries exactly one classification; no field has two
  derivations, an ungoverned fallback, a manual fill, a network fallback, or a source outside
  accepted M3.2 evidence (§D universal rules; §B.3; §G.3).
- The eight GV2 corrections each verified present and controlling (contract §8.1): parse
  prerequisite (the §F "71 of 135 unreachable" conclusion correctly re-scoped to as-at-M3.2);
  plan-row binding (`census_plan_sources.observation_id`, migration `0004` line 26, incl. the two
  bulk-submissions objects; stop condition §23 item 26 covers the absent-ID and two-object cases);
  failed/unavailable preserved; historical documents never retrievable (D023 O1 unchanged); SIC
  fail-closed incl. `industry_family` and `primary_universe_eligible` (with `0009`'s SIC 6000–6999
  and provisional-only CHECKs enforcing the D016 §2 conditions structurally); `census_index_instances`
  AVAILABLE-AS-NONE and never artificially populated (§19 keeps it unwritten); candidate resolutions
  via R16; no blanket nullable fallback (the schema+applicability+methodology conjunction is precise
  enough that SQL nullability alone can never read as permission — reinforced by §23 item 27 and the
  `0009` evidence-backing freeze trigger).
- Spot-verified mapping rows against schema and accepted records: source read order deterministic;
  plain/dashed accession handling (D018 §§5.1–5.3, `UNIQUE (snapshot_id, accession_number_dashed)`);
  amendment linkage (D019 §5 vocabulary = `0009` CHECK lines 225–228, is_amendment implications
  lines 267–268); former-name/name-change (D019 §8; `identity` dimension restricted, forbidden on
  accession evidence per D019 §8.1.1); fiscal-year-end change is selection-layer evidence with no
  candidate column (correctly absent); cohort/date (D010; `filing_date_precedence` CHECK = 2);
  XBRL (iff-CHECK line 262); registrants (exactly-one-anchor partial index + freeze trigger);
  reason rows (FK to `reference_reason_codes`; D019 §9 no-contradiction rule); structural
  fingerprints (D021 §8.1); `coverage_policy_version` (OQ-6/OBS-1, §13 below); `census_run_id`
  operational-excluded everywhere.

## 9. R13 / offline parse boundary (packet §9)

**PASS on the R13 prohibitions and the GR-C1/GR-C2 corrections; the boundary defect is MAJ-1.**
Verified against current code: retrieval/parse coupling exists only at the orchestration entry
points (`census_orchestrator.py` builds `HttpxTransport` at line 187 and couples fetch→parse in
`_retrieve_and_parse`, lines 473–533); the parsers are pure over materialized content
(`sec/parsers/` has no httpx/socket/urllib import; payloads come from `SnapshotStore.load_payload`/
`payload_path` over stored bytes; `iter_members` refuses non-regular members); `CensusCatalog`
persistence takes a writer and no transport; no offline entry point exists (GV2-10 confirmed:
`census_plan_sources` writers are `census_orchestrator.py` and `m3/acquisition.py` only). **GR-C2
confirmed at code level**: `parser_run_id = _stable_id("parser-run", observation_id, parser_id,
parser_version)` (`census.py:144–146, 1461–1463`) and `parsed_record_id = _stable_id("parsed",
observation_id, parser_id, parser_version, native_identity, record_sha256, member_name,
record_path, record_index)` (`census.py:426–436`) are deterministic content/provenance digests;
only re-retrieval mints a new uuid4 `source_observation_id` (`observation_catalog`); the parse layer
cannot fabricate an observation (`_observation_id` requires an existing catalog row,
`census.py:391–417`). Failed/unavailable preservation, no-new-evidence, no-CompanyFacts/Frames, and
no-filing-body rules are stated on every operative surface, and §23 item 22 makes any transport
appearance on an offline-parse path a stop.

## 10. E0 real-private-parse boundary (packet §10)

**Structurally complete; one MAJOR defect (MAJ-1).** The thirteen contract elements cover every
item Decision 067 §11.2 requires, plus prohibited tables (inside item 2), token semantics (item 11:
once, private, never an E1 authorization), independent post-E0 verification (§30 bullet 2; §10.2),
and both owner gates (item 13: before E0, and after E0 before E1). Interruption/partial state fails
closed, is nonauthoritative, blocks E1, and returns to the owner (item 4); deterministic rerun
requires explicit authorization (item 5); the completeness, non-acquisition (zero requests, no new
observation/object, 77-of-801 accounting unchanged), network-construction-prohibition
(proved-by-test), pre/post integrity, and parser-provenance proofs are each mandatory (items 6–10).
The `census_plan_sources.parser_state` transition is coherent with accepted M3.2 history:
`parser_state` is a distinct lifecycle column (migration `0004` lines 18–20; vocabulary
`not_started → completed/quarantined/failed/missing`), currently `not_started` for all 76 rows
(GV2-6), and advancing it records parse progress without touching `retrieval_state`,
`snapshot_state`, `observation_id`, or any acquisition fact — no history rewriting. No ambiguous
private state is reachable: partial E0 is enumerable per-source (`parser_state` + deterministic
`parser_run_id` rows), fails closed, and cannot promote itself. Exact transaction granularity is
left to the implementation packet, bounded by items 4/5/12 — acceptable, but the owner should note
its resolution will interact with MAJ-1's corrected table list. **As written, however, item 2's
table list makes a compliant real E0 impossible (MAJ-1), and the parser_state disposition for the
70 index sources is unspecified (MAJ-1 secondary facet).**

## 11. E0 / E1 / E2 / M3.4 separation (packet §11)

**PASS.** No automatic progression exists at any governed boundary, and no token implicitly grants
the next authority: contract acceptance starts nothing (§1, §34, §36); I/R and rehearsal success
supply no E0 authority (§10.2: "Neither this contract's acceptance, nor a passing rehearsal, nor a
green suite supplies it"; runbook §28a); the E0 result token is "never treated as an E1
authorization" (item 11) and a commit is never the authorizing artifact (§33); E0 requires
completion **and** independent read-only verification **and** a separate owner gate before E1
(items 12–13; §23 items 23–24; §30 bullet 2 "precondition of E1 … never merged"); the real freeze
additionally requires OR-9 after a fresh A1 acceptance (§2, §1.2); selection-result sealing is a
separate hard boundary from manifest construction, and a sealed selection authorizes no automatic
manifest (R5; §17); the six §8.4 arguments are gated at E2 authorization (OR-6); the constructed
root is an output never an approval, the terminal token and the `m3.3-complete` tag confer no M3.4
authority, and no approval/publication field is ever written (§§7, 35, 36; runbook §30; master plan
§36). M3.3B cannot begin before the M3.3A independent review passes (§23 item 2; §34a).

## 12. Missing-evidence / fail-closed review (packet §12)

**PASS.** (A) historical documents: never acquired, never retrievable, genuinely-required
derivations fail closed (§8.1 correction 4; D067 §10.4). (B) SIC: fail closed after parsing, no
alternate external source, incl. `industry_family`/`primary_universe_eligible` (correction 5;
GV2-20). (C) `census_index_instances`: AVAILABLE-AS-NONE, blocks nothing, never populated
(correction 6; §19). (D) structural evidence legitimately empty only from an actual authorized
parse (R14; empty-set digest per D021 §8.1). (E) required candidate resolutions without evidence
fail closed (R16 §7.4; §23 item 27; the `0009` evidence-backing freeze trigger). (F) D023 O1
remains ACTIVE and stop-and-refer (register; OR-11; §23 item 11; §25). (G) D021-L2 remains ACTIVE
with its required owner action DISCHARGED and closure still requiring the implemented, reviewed
recomputation step (register lines 189–210). (H) D067-L1 is a limitation, unreachable inside M3.3,
and grants no acquisition authority (register lines 904–921). The NULL rule (schema AND
applicability AND methodology) is precise enough that SQL nullability alone can never be read as
methodological permission.

## 13. `coverage_policy_version` / OBS-1 (packet §13)

**PASS — the deferral is acceptable for contract acceptance.** Verified: the value and method are
owner-fixed (`pilot-coverage/1.0`, D067 §8; contract §10.1 OQ-6); only the executable location is
deferred. `grep -rn "pilot-coverage" src/ configs/` returns nothing — no `pilot_policy.py` constant
(all nine constants read, `pilot_policy.py:41–49`) and no `reference_policy_versions` seed row
(every `INSERT … INTO reference_policy_versions` statement across migrations `0002`–`0011`
inspected — ten statements, none carrying a coverage key). Critically, migration `0009` declares
`coverage_policy_version TEXT NOT NULL` with **no** foreign key (line 24), so writing the owner-fixed
literal requires **no migration** — the seed row would be a governance home, not a schema
requirement, and the deferral criteria all hold: the location choice cannot change the value or any
methodology; a later bounded I/R packet can authorize the narrow path under the contract's own named
reservation (§20's final paragraph, "requiring its own owner authorization at that gate"); and a
session that reaches the question stops and refers (§23 item 28; §36). The §20-prohibition /
§34-no-widening pair reads coherently with the named reservation: the reservation is the contract's
explicit routing of this one question to a future owner act, not a widening license.

## 14. Migration / schema review (packet §14)

**PASS — `MIGRATION_AUTHORIZED: none` is correct.** The accepted schema represents everything the
phase needs: offline parse output (migrations `0002`/`0003`/`0005`/`0006`, incl. the MAJ-1
companion tables — so even MAJ-1's fix needs no migration); candidate snapshot state, evidence
rows, and all eight resolution SHA columns (`0009`, verified column-by-column); selection state
(`0009`/`0011`/`0012`); manifest/root state (`0009`/`0013`, triggers 1–8); E0's `parser_state`
transition (`0004`'s CHECK vocabulary, no blocking trigger, `updated_at_utc` present). The 22
frozen-immutable snapshot fields, the freeze-validation trigger set, the building-window guards on
all seven child tables, and the nine-digest frozen-state CHECK were each read verbatim. No
convenience migration is mistaken for a required one; a migration appearing necessary correctly
remains a stop condition (§23 item 17).

## 15. R3 read-only path review (packet §15)

**PASS.** Classification of every reusable SQLite path the contract's governed read-only actions
would touch (cross-checked against inventory §K CF4, then verified directly in code):

| Path | Mode | Classification |
|---|---|---|
| `storage/catalog.py:89` `strictly_read_only_connection` → `storage/sqlite.py:68` `connect(read_only=True)` (`mode=ro` URI = `SQLITE_OPEN_READONLY`; cannot checkpoint; missing DB is an error) | strict | **R3-COMPLIANT** |
| `m3/recovery.py:141/156` `read_only_catalog` and its consumers | strict | **R3-COMPLIANT** |
| Accepted S5/S6 entry points — `load_frozen_joint_candidates`, `reconstruct_persisted_joint_selection`, `execute_and_persist_joint_selection` (replay), `seal_selection_result`, `build_and_persist_pilot_manifest` (replay), `verify_pilot_manifest` | caller-supplied `sqlite3.Connection` | **R3-COMPLIANT by injection** — M3.3 chooses the handle per path; no store edit needed |
| `cli.py:2274` `_m3_migration_chain_head` → `read_only_connection` (`catalog.py:84`, read-write OS handle, convention-only) | convention | **REQUIRES-BOUNDED-I/R-HARDENING** — reachable from M3.3 receipt-emitting commands |
| `cli.py:1310` `_migration_chain_head` | convention | **REQUIRES-BOUNDED-I/R-HARDENING** if any M3.3 command reaches it; otherwise NOT-USED-BY-M3.3 |
| `cli.py:2185` `_already_satisfied_index_keys` (M2.2 census index path) | convention | **NOT-USED-BY-M3.3** |
| `storage/sqlite.py:626` `backup_database` (read-write source handle; destination context manager governs the transaction, not the connection) | convention | **NOT-USED-BY-M3.3** for a governed read; if any E0 integrity step ever used it, R8's narrow-hardening rule applies |

Every hardening need satisfies the packet's non-blocker test: the exact call sites are identified,
the required semantics are already governed (R3), no methodology change is involved, R8 scopes the
fix to actually-used paths and forbids repository-wide cleanup, and rehearsal acceptance requires
compliance first. No path's correction requires an unresolved architectural decision. The
contract's statement that `read_only_connection` "is therefore not admissible for a governed M3.3
read" (§14) is verified correct against the code and against Decision 066 §5's root cause.

## 16. Authority-leak audit (packet §16)

**PASS — no leak found.** All negative flags verified on every operative surface (contract header
and §§1, 7, 20, 23, 24, 34, 36; Decision 067 header and §12; STATUS banner and markers; runbook
§§28a–30; master plan M3.3 §§5, 6, 11–16, 36; contracts README; registry row 067; decision index;
architecture map §0; change-impact map). Nothing currently authorizes implementation, real E0, real
E1, network, reacquisition, migration, real snapshot, real selection, manifest construction, root
approval, or M3.4. The contract's imperative-mood scope sections (§6, §26–§29) are bounded four
ways (§1 "authorizes nothing"; §20's "for the later, separately authorized implementation"; §34's
boundary; §36's negative-authorization list), and R13's driver permission is scope-only with an
explicit non-authorization sentence. `REQUEST_CEILING: 0`; both tracked network switches `false`;
no prose reads as granting authority against a NO flag.

## 17. Residue scan and broad semantic current-state review (packet §17)

**A. Known-phrase scan.** Run across the contract, STATUS, Decision 067, the proposal, the
inventory, the runbook, the limitations register, the registry, the index, the architecture map,
the impact map, the contracts README, and the master plan, for the packet's phrase list plus
affirmative-authorization variants ("implementation is authorized", "E0/E1 authorized", "network
authorized", "reacquisition permitted", "coverage policy unresolved", movable-tag phrasing). Every
meaningful hit classified: the inventory's "OR-1 and OR-2 remain open and entry-blocking" (line 10)
is inside a banner explicitly superseded by the next paragraph ("the paragraph above is historical
as at the M3.3-GR packet") — **HISTORICAL**; the contract's and index's "entry-blocking" hits state
the condition's *removal* — **CURRENT-CORRECT**; "cannot run offline…"/"…reparse changes…" appear
only as quoted superseded propositions inside GR-C1/GR-C2 blocks — **HISTORICAL**; "PENDING" hits
are the correct pending-review status; STATUS's historical per-stage markers stating old M3.2
authorizations are governed by the markers section's as-at-own-acceptance rule — **HISTORICAL**. No
**CURRENT-STALE** hit survives.

**B. Broad semantic review** (not bounded by the phrase list) across STATUS ↔ contract; markers ↔
prose; registry ↔ index; Decision 067 ↔ architecture map ↔ change-impact map; README ↔ next
action; runbook ↔ current behaviour; limitations ↔ gates; master plan ↔ disposition; evidence-index
practice ↔ ledger-not-index rule. Contradictions found: **MIN-1** (the R12 §10.1/§10.2 scope
pointer — contract vs STATUS marker vs inventory vs the applied file state); **OBS-A** ("Both
reviews" vs three); **OBS-D** (master plan §9 category list). Everything else is mutually
consistent, including the three-commit distinctness rule (accepted M3.2 baseline `5c4c875e…` /
closeout `2185f583…` + tag / entry baseline `e3e58f93…`), the Gate-H R4 expression on both
operative surfaces with historical references preserved (incl. the negative control at
`tests/integration/test_m3_cli.py`), the E0 gate on every surface, and the
`ACTIVE_STAGE_CONTRACT = m3_2.md` marker (deliberate: a corrected contract is not the active
contract).

## 18. Contract acceptability and next action

**The corrected contract is NOT yet ready for Sol/GPT owner acceptance.** MAJ-1 must be resolved by
a bounded owner correction to §10.2 item 2 (and its dependent rows: item 12, §19, §26 item 2, §29,
and the index-source disposition), and MIN-1 by a one-token §1.1 R12 fix — followed, per the
standing discipline, by a fresh independent rereview and then the separate owner acceptance act.
Neither finding requires a migration, a methodology change, reacquisition, network authority, or
any executable-code change now. The five observations require no pre-acceptance action; OBS-A/OBS-B
are recommended for the same correction pass or the I/R packet respectively.

This review artifact is the only repository write of this session. It changes no authority state:
`CONTRACT_ACCEPTANCE: NO`, `IMPLEMENTATION_AUTHORIZATION: NO`, `REAL_PRIVATE_PARSE_AUTHORIZATION:
NO`, `REAL_SNAPSHOT_AUTHORIZATION: NO`, `NETWORK_AUTHORIZATION: NONE`, `MIGRATION_AUTHORIZED:
none`, `M3_4_AUTHORIZATION: NO` all stand, and the reviewed target remains the frozen parent
`c8acfef59006f8812eb5678d3f61d852d6789f07`.
