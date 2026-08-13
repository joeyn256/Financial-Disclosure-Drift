# M3.3 Decisions 067–068 Corrected Contract — Fresh Independent Rereview (target `7bb36b8`)

```text
STATUS: COMPLETE — INDEPENDENT REREVIEW RECORD, NO AUTHORITY
DATE: 2026-08-13
REVIEWER: fresh independent Claude session (Fable 5, maximum effort), non-author
REVIEWED TARGET (frozen): 7bb36b80b6a7f3cb28eb28947ee2908c08672f50
  tree e99b527c120c5a3abd8f416f7f7c2f7211225c33
VERDICT: M3_3_DECISIONS_067_068_CORRECTED_CONTRACT_FRESH_REREVIEW_B0_M0_MIN0_PASS
FINDINGS: BLOCKER 0 · MAJOR 0 · MINOR 0 · OPTIMIZATION 0 · OBSERVATION 1
```

**What this document is.** The complete record of the fresh independent rereview of the
Decisions-067–068-corrected M3.3 contract ([`Milestones/contracts/m3_3.md`](../../../Milestones/contracts/m3_3.md)),
performed under the owner's rereview packet of 2026-08-13, after the first independent review of the
Decision-067-corrected contract FAILED (B0/M1/MIN1) and accepted
[Decision 068](../../Decisions/decision_068_m3_3_e0_contract_correction.md) applied the bounded
corrections. It records conclusions; it fixes nothing, accepts nothing, and authorizes nothing.
Under the packet's verdict standard (`PASS` requires BLOCKER 0 / MAJOR 0 / MINOR 0), the verdict is
**PASS**. One OBSERVATION is recorded (§14). **This rereview is not owner acceptance**: a separate
Sol/GPT acceptance act is still required, and no M3.3-I/R, E0, E1, E2, or M3.4 authority exists or
is created by this record.

---

## 1. Independence attestation

- **One fresh review epoch.** The session was `/clear`ed; the first substantive input to this epoch
  was the owner's rereview packet. No conclusion was inherited from the prior review epoch — that
  epoch found MAJ-1/MIN-1 and then authored the Decision 068 correction, and is disqualified; this
  session treated its artifact only as a checklist of previously reported issues and independently
  re-verified every material conclusion against accepted decisions, the corrected contract,
  migrations, current source, and the governance surfaces.
- **No subagents, no delegation, no parallel Claude workflows, and no Workflow/Agent invocations**
  were used at any point. All reading, verification, and analysis were performed inline in this one
  session.
- **No authorship.** This session authored none of: Decision 067; Decision 068; the corrected M3.3
  contract at the target commit; the M3.3-G foundation; the M3.3-GR proposal; GV/GV2; any M3.3
  implementation, candidate snapshot, selection, or manifest.
- **Boundaries honoured.** No contract, governance, executable, test, migration, config, or CI edit;
  no private-evidence access and no `EV_ROOT` use; no parser execution; no E0/E1/E2 action; no
  snapshot, selection, manifest, or root; no network access, no SEC request, no reacquisition; no
  fetch and no pull during review. The only repository write is this review artifact, created after
  the verdict was final.

## 2. Frozen entry state — verified live before substantive reading

| Fact | Required | Observed | Match |
|---|---|---|---|
| Branch | `main` | `main` | ✓ |
| HEAD | `7bb36b80b6a7f3cb28eb28947ee2908c08672f50` | same | ✓ |
| Tree | `e99b527c120c5a3abd8f416f7f7c2f7211225c33` | same | ✓ |
| `origin/main` | same as HEAD | same (no fetch, no pull) | ✓ |
| Working tree | clean | clean (empty porcelain) | ✓ |
| Subject | `Correct M3.3 E0 contract boundary after independent review` | same | ✓ |
| `m3.2-complete` | unchanged / immutable | tag object `2865a1479e4576dc18a4098c928b278812f38d00`, present and unmoved; matches contract §2 | ✓ |

Additional target-integrity facts established: `git diff e3e58f9..7bb36b8 -- src/ tests/ configs/
.github/ Makefile pyproject.toml scripts/` is **empty** — the Decision 066 R3 entry software
baseline is byte-intact at the review target, and only fifteen governance documents changed since
it. The correction commit `7bb36b8` itself changed exactly the twelve surfaces Decision 068 §9
declares, did **not** touch Decision 067, and did **not** touch the immutable failed-review
artifact (`git log --follow` shows exactly its creation commit `8cbb77e`; `git diff 8cbb77e
7bb36b8` on that path is empty). The GR proposal's change is **+8 lines, 0 deletions** — the OBS-E
erratum note only, body preserved.

## 3. Required authorization state — independently verified

Contract header, `Milestones/STATUS.md` markers (`DECISION_068_STATUS`,
`DECISION_068_CURRENT_STATE`, `M3_3_CONTRACT_FRESH_REVIEW_STATUS`,
`M3_3_DECISION_067_GOVERNANCE_STATUS`, `IMPLEMENTATION_AUTHORIZATION`, `NEXT_AUTHORIZED_ACTION`),
`configs/project.yaml`, and `make context` all agree, with no contradiction found:

`CONTRACT_ACCEPTANCE: NO` · `IMPLEMENTATION_AUTHORIZATION: NO` ·
`REAL_PRIVATE_PARSE_AUTHORIZATION: NO` · `REAL_SNAPSHOT_AUTHORIZATION: NO` ·
`NETWORK_AUTHORIZATION: NONE` · `REACQUISITION_AUTHORIZATION: NONE` · `MIGRATION_AUTHORIZED: none` ·
`REAL_SNAPSHOT_FREEZE_AUTHORIZATION: NO` · `REAL_SELECTION_AUTHORIZATION: NO` ·
`MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO` · `M3_4_AUTHORIZATION: NO` · `REQUEST_CEILING: 0` ·
M3.3-I/R, M3.3-E0, M3.3-E1, M3.3-E2 **not authorized** · tracked network switches
`network.enabled false` / `network.m3_acquire_enabled false` · `OR_1: RESOLVED — OWNER RULED BY
DECISION 067` · `OR_2: RESOLVED — OWNER RULED BY DECISION 067` · contract status `CORRECTED —
DECISIONS 067–068 OWNER RULINGS RECORDED — PENDING FRESH INDEPENDENT REREVIEW AND OWNER
ACCEPTANCE` · `NEXT_AUTHORIZED_ACTION` names **only** this rereview followed by a separate owner
acceptance act. **No authority leak found** (§16 below).

## 4. Authority set read

Read in full: `Milestones/contracts/m3_3.md` (1143 lines); Decision 067 (576 lines); Decision 068
(253 lines); `Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md` (958 lines — disposition
banner, body, GR-C1/GR-C2 annotations, OBS-E erratum); `Docs/m3/m3_3_governance_foundation_inventory.md`
(487 lines); the prior failed review
[`m3_3_corrected_contract_independent_review_c8acfef.md`](m3_3_corrected_contract_independent_review_c8acfef.md)
(as a checklist only). Read in governing part: Decisions 013 (§§1, 2, 5–7), 016 (§§1, 4, 8 verbatim;
structure), 018 (§§5.2, 17–19 anchors; tie-break verified in code), 019 (§9, §9.1, §10), 021 (§§5–13
structure; §8.1 verbatim), 023 (§7 O1), 029 (header/status — M3.1-scoped, historically relevant
only), 065 (§3), 066 (R1–R4); `Milestones/STATUS.md` (banner, current markers, marker-governance
rules); `Milestones/milestone_03_master_plan.md` (M3.3 §§1–36 focus: §2, §6, §9, §10, §26);
`Milestones/contracts/README.md` (required sections; M3.3 entry; 2026-08-13 update);
`Docs/Decisions/decision_registry.md` (rows 066–068; both controlling-record rows);
`Docs/decision_index.md` (M3.3 Q&A block); `Docs/architecture_map.md` (§0 Milestone 3 row; §10.1 and
§10.2 `Status` bullets); `Docs/change_impact_map.md` (Decision 067 and 068 sections);
`Docs/m3/operator_runbook.md` (§§28a–30); `Docs/m3/limitations_register.md` (D021-L2, D067-L1 and
the register summary).

## 5. Code and schema surfaces inspected (read-only; no parser executed, no private evidence)

`sec/census.py` (all 1527 lines); `sec/census_orchestrator.py` (structure, `_retrieve_and_parse`
lines 473–533, `_parse_bulk`, `_retrieve_historical`, plan/parser_state lifecycle 1262–1382,
index-side writers 982–1173, `qa_metrics` call at line 425, transport construction at line 187);
`sec/accession_resolution.py`, `sec/raw_store.py`, `sec/snapshots.py`, `sec/archive.py`,
`sec/index_retrieval.py`, and every module under `sec/parsers/` (durable-write and transport-import
scans: zero writes, zero network imports); `sec/source_registry.py` (source IDs, incl.
`sec_sic_code_list`:227, `sec_edgar_filing_calendar`:251, `sec_full_index_company`:293);
`storage/catalog.py` (complete — `CatalogWriter`, file-based flock lease, `read_only_connection`,
`strictly_read_only_connection`); `storage/sqlite.py` (`connect` modes, `mode=ro` URI);
`release/hashing.py` (complete); `pilot_policy.py` (complete); `cohorts.py` (seed);
`sec/entity_selector.py` `selection_rank` and `sec/accession_selector.py` `accession_selection_rank`
(verbatim); `m3/recovery.py` (`read_only_catalog`); `cli.py` (`network_commands`, the three
`read_only_connection` call sites 1310/2185/2274); `sec/observation_catalog.py` (uuid4 minting).
Migrations `0001`–`0013` mapped; `0004` (plan-sources schema, `parser_state` CHECK) and `0009`
(all eight candidate tables verbatim, snapshot lifecycle triggers, building-window guards, freeze
trigger with evidence-backing) read in full for the governing parts; `0008` triggers read verbatim;
every `CREATE TRIGGER` in `0001`–`0013` enumerated and classified.

## 6. Decision 067 / 068 faithfulness (packet §6) — PASS

Verified clause-by-clause between the records and the corrected contract:

- **R13** (contract §1.1/§10.2/§6 item 2/§20 = D067 §4): complete prohibition list identical;
  `census_plan_sources.observation_id` binding incl. the two bulk-submissions objects; reuse list
  identical; driver permitted-in-scope with the explicit non-authorization sentence.
- **R14** (contract §1.1/§10.2/§26 item 2 = D067 §5): all four post-parse rules; D021 §8.1's
  empty-set permission retained, not widened.
- **R15** (contract §1.1/§10.1 = D067 §6): ALT-3; the eight Decision 016 §4 fields retained
  verbatim; D067-L1 recorded in the register, `ACTIVE`, no acquisition authority.
- **R16** (contract §1.1/§10.1/§26 item 3 = D067 §7): domain, field tuple, exclusions, two-step
  candidate-layer resolution digest, never the census digest, five analogue-less dimensions not
  exempt, tie-breaks unchanged — all identical.
- **OR-1 / OR-2 final dispositions** (contract §10.1/§8.1/§21 = D067 §§9–10): the eleven-digest and
  135-column normative bases with every correction (OQ-3/OQ-4/OQ-5/OQ-6/OQ-7/OQ-8; the eight GV2
  corrections) carried exactly; proposal held to historical-evidence status on every surface.
- **M3.3-E0 boundary** (contract §10.2 = D067 §11): all thirteen §11.2 required elements present,
  plus R18's item 14 — an owner-authorized extension, not an implementation-packet widening.
- **R17** (contract §1.1/§10.2 item 2/§19/§23 item 12(§10.2)/§26 item 2/§29/§30 = D068 §3): the
  fifteen-table set carried identically everywhere it appears, with the `parser_state` transition
  scoped to category-A only, `census_qa_metrics` excluded with its exact writer named, all four
  index-side tables excluded, and the no-second-writer prohibition intact.
- **R18** (contract §1.1/§10.2 items 6 and 14/§19/§26 item 2/§29/§30 = D068 §4): the A/B/C
  report-level vocabulary, the 70-full-index category-C rule with its "unless an already accepted
  field-level OR-2 mapping proves otherwise" guard, category-C untouched semantics, the
  no-enum/no-migration rule, and the completeness-proof clauses all carried exactly. The A/B
  boundary is a determinate partition: category B's definition exactly covers the
  candidate-substantive-but-already-failed case, and category A's "unless already
  failed/unavailable" clause cedes that case to B rather than overlapping it — exactly-one
  assignment is well-defined, and the unassignable case is a stop condition (§10.2 item 12).
- **R16-C1** (contract §1.1/§26 item 3 = D068 §8): identical, including the stop-and-refer branch.
- **Auxiliary-output semantics** (contract §10.2 closing paragraph = D068 §5): clause-for-clause
  identical (§8 below).
- **MIN-1 fix** (contract §1.1 R12 row = D068 §6): pointer now "§10.1", with a visible
  correction-note; historical records not rewritten (§9 below).
- **OBS dispositions** (D068 §7): each verified applied (§9 below).

No omission, changed meaning, contradictory wording, broadened authority, or narrowed fail-closed
behavior found.

## 7. MAJ-1 closure — the exact E0 write footprint, independently derived (packet §7) — PASS

**This review did not accept Decision 068's enumeration; it re-derived the footprint from the code
at the frozen target.**

**Mechanical enumeration.** `sec/census.py` was read in full and every `.execute(` call classified.
It contains **exactly 19 durable-write execute statements** (23 counting the four embedded
`ON CONFLICT … DO UPDATE` upsert clauses at lines 677, 840, 876, and 996 as separate statements),
**resolving to exactly sixteen distinct tables** — the fifteen R17 tables plus `census_qa_metrics`:

| Reachable from | Tables (write sites) |
|---|---|
| `persist()` — the reusable parse-persistence entry | `census_parser_runs` (:174 INSERT, :206 UPDATE), `census_parsed_records` (:441), `census_quarantined_records` (:483), `census_accessions` (:667 + upsert :677), `census_accession_observations` (:683, :1237 conflict-flag UPDATE), `census_registrants` (:994 + upsert :996), `census_registrant_observations` (:1028), `census_malformed_historical_references` (:1096), `census_historical_references` (:1123), `census_structural_observations` (:1152), `census_candidate_lineage_edges` (:1202), `reference_sic_codes` (:951 `INSERT OR REPLACE`), `census_calendar_days` (:972) — **13 tables** |
| `resolve_persisted_accessions()` — the accepted Decision 012 resolution pass | `census_accession_field_resolutions` (:833 + upsert :840), `census_accession_cohort_resolutions` (:870 + upsert :876), `census_accessions` (:912 canonical-projection UPDATE) — **+2 tables** |
| `qa_metrics()` — a separate entry point | `census_qa_metrics` (:376) — **not** reachable from `persist()` or `resolve_persisted_accessions()` |

Every other `.execute(` in the module is a SELECT (verified line by line, including the
allowlist-guarded QA read helpers).

**The packet's six proof obligations, each independently established:**

- **A — legitimacy.** Each of the fifteen permitted tables has its writer inside the
  `persist()`/`resolve_persisted_accessions()` chain, exercised by the accepted parser outcomes for
  the authorized source families (submissions/tickers → registrants, observations, accessions,
  histories, historical references, quarantine, structural, lineage; SIC list → `reference_sic_codes`;
  calendar → `census_calendar_days`; resolution pass → the two resolution tables and the canonical
  projection).
- **B — completeness/minimality.** No other durable table is written anywhere in `census.py`;
  `grep` confirms **zero** references to `census_plan_sources`, `census_index_*`, `record_reasons`,
  or `record_event` in the module. The `CatalogWriter` the path requires takes its lease as an
  **flock file** (`catalog_writer.lease`), not a database row, so holding the writer writes no
  table; its unrelated helpers (`seed_reference_data`, `migrate`, `insert`, `record_reasons`,
  `record_event`) are not part of the reused path and are fenced by the contract's containment stop
  (§10.2 item 12) and required containment test (§26 item 2).
- **C — `census_qa_metrics`.** Its **sole caller in `src/` is
  `sec/census_orchestrator.py:425`**, inside the network-gated orchestration run; it is not
  reachable from the reused persistence path, and the contract keeps it unwritten at E0 on every
  surface (§1.1 R17, §10.2 item 2, §19, §26 item 2's negative assertion).
- **D — index-side tables.** All four (`census_index_instances`, `census_index_reconciliation`,
  `census_index_instance_events`, `census_index_retrieval_accounting`) are written **only** by
  `census_orchestrator.py` (write sites at 1001/1048/1077/1112/1158) and are excluded from E0 on
  every surface.
- **E — no second writer needed.** `persist()` + `resolve_persisted_accessions()` cover all fifteen
  tables; the driver adds only the `census_plan_sources.parser_state` transition, whose accepted
  lifecycle and vocabulary (`not_started`/`completed`/`quarantined`/`failed`/`missing`) exist in
  migration `0004` and in the orchestrator's `_after_observation`/`_persist_plan` lifecycle.
- **F — no hidden side effects.** Every `CREATE TRIGGER` in migrations `0001`–`0013` was
  enumerated: all are `SELECT RAISE(ABORT, …)` guards; **no trigger writes any table**; the only
  census-side triggers (migration `0008`) sit on `census_source_observations`, which E0 never
  writes. `_stable_id` is a pure SHA-256; `transaction()` writes no table.

**Fifteen is exact.** The permitted set is precisely the write footprint of the reusable accepted
path — no less (E0 executable in principle) and no more (no widened authority). MAJ-1 is closed.

One numeral in Decision 068 §3.1's narrative does not reconcile with this derivation and is
recorded as **OBS-R1** (§14): "exactly twenty-four durable-write statements". The operative halves
of the same sentence and section — sixteen distinct tables; the fifteen-table permitted set; every
per-table line reference — are exactly correct.

## 8. R18 source-disposition and auxiliary-output review (packet §§8–9) — PASS

**Exactly one report-level disposition per planned source** (A `E0_REQUIRED_PARSE` / B
`E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE` / C `E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY`) is
carried at contract §10.2 items 6 and 14, §19, §26 item 2 (disposition test incl. the fail-closed
unclassifiable case), §29 (rehearsal branch), and §30 (post-E0 review question); it is **report
vocabulary only** — no schema enum and no migration, verified against migration `0004`'s unchanged
`parser_state` CHECK.

**The 70 full-index sources' category C was traced, not assumed.** Mechanically:
`census_orchestrator._retrieve_and_parse` returns a `ParseOutcome` only for `sec_bulk_submissions`,
the two ticker sources, `sec_sic_code_list`, and `sec_edgar_filing_calendar`; **every other source
— `sec_full_index_company` included — falls through to `return observation, None, ()` (line 533)**.
The accepted machinery therefore defines **no parse-layer output at all** for a full-index source;
its content is consumed only by the index path, whose destinations are the four excluded
`census_index_*` tables. On the mapping side, the adopted OR-2 basis's deterministic source read
order contains no `census_index_*` table; `census_index_instances` is AVAILABLE-AS-NONE /
DELIBERATELY NOT USED (§8.1 correction 6), and `census_index_reconciliation` is VALIDATION-ONLY —
**no authoritative candidate field consumes an index-side parser output**, and no required field's
evidence floor demands full-index corroboration (full-index field names appear in
`CANONICAL_FIELD_BY_SOURCE_FIELD` only as lower-authority corroboration that no accepted path ever
persists). Category C is therefore correct for the 70 full-index sources, and the category-C
protections (no fabricated parser run, no `parser_state` mutation, no index-table population,
acquisition/provenance evidence preserved, explicit enumeration in the completion report) are
present on every surface.

**Auxiliary outputs — inclusion is not licence** (contract §10.2 closing paragraph ≡ D068 §5):
quarantine stays governed by the accepted parser/QA rules and blocking conditions continue to block
E0 success (`persist()` records `failed` / `completed_with_quarantine` states verbatim); the
historical-reference tables may remain empty and no missing per-registrant historical document may
be retrieved (§8.1 correction 4; D023 O1 unchanged); lineage edges only from accepted stored
metadata (`_candidate_edges` derives only from persisted registrant observations); calendar only
from the authorized parse (`_normalize_calendar` gate); `reference_sic_codes` only from the
plan-bound accepted SIC source (R13 binding); **no evidence floor lowered and no missing-source
substitution** — all clauses present and none weakened.

## 9. Finding-specific closure of the prior review (packet §20) — ALL CLOSED

| Prior finding | Closure verified |
|---|---|
| **MAJ-1** (E0 table list incomplete; index-source disposition unspecified) | Closed by R17 + R18; independently re-derived at §7–§8 above. The corrected list is exact; the disposition rule is determinate; every dependent surface (§10.2 items 2/6/12/14, §19, §23, §26 item 2, §29, §30) is synchronized |
| **MIN-1** (contract R12 row said "§10.2") | Closed: contract §1.1 R12 row now reads "§10.1's current `Status` bullet" with a visible correction note naming Decision 068 §6 and MIN-1. Verified against the file state: the applied R12 correction lives in `Docs/architecture_map.md` §10.1's `Status` bullet (line 440); §10.2's one-line bullet was never stale. STATUS's `M3_3_GR_GOVERNANCE_STATUS` marker and the inventory §K both already said §10.1; no historical record was rewritten |
| **OBS-A** ("Both reviews" after three) | Closed: contract §30 now reads "**All three §30 reviews** must additionally perform…" with the correction note. The phrase "Both reviews" survives only inside Decision 068 §7's OBS-A disposition row, describing what was replaced — historical |
| **OBS-B** (contributor membership) | Closed as clarification **R16-C1**, and verified **mechanical, not methodological**: Decision 016 §4 defines the evidence tables as "one row per contributing observation" and the resolution hash as tying the resolved value to "the specific evidence rows … that produced it", so the deterministic membership selection (the persisted candidate evidence rows for that parent and dimension, as substantively used by the accepted resolution) is already determined by accepted methodology — no new role filter and no new resolution semantics are needed. R16-C1's guards (never role-inferred; never unrelated-row inclusion; independently recomputable; deterministic) plus the stop-and-refer branch and the §26 item 3 I/R test obligation (one explicit deterministic membership selection/query, tested) complete the closure. **Required I/R obligation noted:** the membership query must be pinned verbatim and tested per contract §26 item 3 |
| **OBS-C** (E-label collision) | Closed: on current operative surfaces, real gates are always the prefixed `M3.3-E0`/`M3.3-E1`/`M3.3-E2`, and bare `E1–E8` appears only immediately qualified as rehearsal ("rehearsal scenarios E1–E8", "execution rehearsal … across E1–E8"); bare `E0` is collision-free (no rehearsal scenario E0 exists). A word-boundary scan of the contract, runbook, and master plan found no unqualified gate-meaning `E1`/`E2` |
| **OBS-D** (master-plan path-category list) | Closed: master plan M3.3 §9 now lists "a new bounded offline metadata-parse driver / entry point module and its tests" with the explicit "**descriptive only** — it grants no implementation, E0, private-mutation, or network authority" clause, citing Decision 068 §7 OBS-D. No authority leak |
| **OBS-E** ("four snapshot timestamps") | Closed as a historical erratum: the proposal §B.2 keeps its historical sentence verbatim and now carries a clearly delimited erratum note ("should read the **three** snapshot timestamps"), added as +8 lines with zero deletions. The per-table tally (7/3/3/2/3/3/3/3 = 27) was independently re-verified to balance with three timestamps against migration `0009` |

No correction rewrote history inaccurately: Decisions 001–067 are byte-unchanged by the correction
commit, the failed-review artifact is byte-unchanged since its creation, and the proposal body is
preserved.

## 10. R13 / R14 / R15 / R16 / OR-1 / OR-2 — independent re-verification (packet §§10–16)

**R13 offline-parse boundary — PASS.** Parsers are pure over materialized content (zero durable
writes and zero network imports across `sec/parsers/`, `accession_resolution.py`, `raw_store.py`,
`snapshots.py`, `archive.py`, `index_retrieval.py`); retrieval/parse coupling exists only at the
orchestration entry (`HttpxTransport` constructed at `census_orchestrator.py:187`; `sec census` is
in `cli.py`'s `network_commands` and refused when `network.enabled` is false); loading/verification
(`SnapshotStore.payload_path`/`load_payload`/`verify_payload`) and `CensusCatalog` persistence are
offline-capable, so the new I/R scope needs only a bounded offline driver with no HTTP client and
no transport; the parse layer cannot fabricate an observation (`_observation_id` requires an
existing `census_source_observations` row); the plan-row binding is mechanically supported —
`census_plan_sources.observation_id` is a single-valued FK column (migration `0004`), so the
two-bulk-object case resolves through the plan row alone, and recency/size/path/`source_id`/
operator choice are refused (§8.1 correction 2; stop §23 item 26); failed sources stay failed
(correction 3); E0 is separately owner-gated; I/R is fixtures/disposable-copies only and cannot
grant E0 (§7, §10.2, runbook §28a).

**R14 — PASS.** A uniformly empty fingerprint merely-because-unparsed is barred; the offline parse
precedes any authoritative snapshot; the legitimate empty-row-set digest is scoped to a legitimate
zero-row parse result; failed/unavailable is never converted to fabricated-empty; fingerprints are
recomputable from the actual parse result; required-unavailable structural evidence fails closed
(§1.1 R14; §10.2; §26 item 2's two dedicated tests). D021 §8.1 declares the five-column tuple "the
only structural-fingerprint tuple" (three-column form withdrawn) — no competing definition exists.

**R15 — PASS.** Decision 016 §4's eight fields retained verbatim; code mechanics verified:
observation IDs are minted `uuid4` at retrieval (`observation_catalog.py:1124/1129`), while
`parser_run_id = _stable_id("parser-run", observation_id, parser_id, parser_version)` and
`parsed_record_id = _stable_id("parsed", observation_id, …, record_index)` are deterministic
content/provenance digests — a reparse of the same accepted observation reproduces both (GR-C2;
`persist()` additionally short-circuits idempotently on an existing `parser_run_id`); only
re-retrieval mints new identity, and M3.3 forbids it. D067-L1 is recorded accurately as a bounded
limitation with no acquisition authority.

**R16 / hash graph — PASS.** `release/hashing.py` is the single implementation (logical row digest;
sorts rendered rows; `NULL_SENTINEL "\x00null"`; no file bytes); `evidence_sha256` at domain
`pilot_candidate_evidence_row` over exactly the eight fields, no second normalization, canonical
NULL preserved; exclusions verified (`evidence_id`, `snapshot_id`, parent key, `recorded_at_utc`,
`detail`, `census_run_id`, paths, physical bytes, approval/publication state); content identity not
row uniqueness; all eight `*_resolution_sha256` columns (entities: size/industry/history/
primary_universe; accessions: filing_date/cohort/xbrl/amendment_purpose — exactly migration
`0009`'s set) use the two-step candidate-layer construction and never the census
`resolution_sha256` (a genuinely distinct digest in `census_accession_field_resolutions`/
`census_accession_cohort_resolutions`, migration `0006`); `0009`'s presence-CHECKs tie each
resolution SHA to its resolved value exactly as R16 §7.4's NULL rule requires, and the freeze
trigger additionally demands winning/supporting evidence backing per resolved dimension.

**R16-C1 — PASS** (§9 above, OBS-B row): mechanical under Decision 016 §4; the I/R test obligation
is already mandated by contract §26 item 3.

**OR-1 full identity graph — PASS.** All twenty-three constructions re-verified: the eleven
snapshot-level digests (coverage window five-field set with `include_open_quarter` forced 0 and the
D013 §1 constants; `input_observation_set_sha256` **definitionally identical** to Decision 021
§8.1's `source_observation_set_sha256` — same declared content, same six-column tuple, same cited-set
definition, computed pre-`INSERT` and independently recomputed from persisted evidence inside the
same R5 transaction, fail-closed on mismatch; `snapshot_id` over the two digests plus the three
`pilot_policy.py` constants, `census_run_id` excluded; the seven family digests with `snapshot_id`
excluded per OQ-4 and bound once in `candidate_snapshot_sha256`'s twelve fields), the two
`evidence_sha256` families, the eight resolution families, and the two accepted tie-breaks
(`SHA256(seed|cik_padded)` and `SHA256(seed|anchor_cik_padded|accession_number_dashed)`, verified
verbatim in code against D013 §6 / D018 §5.2). **The 135-column treatment tally was independently
re-added and balances**: 96 INCLUDED (13/23/32/6/8/8/3/3) + 12 TRANSITIVE (8/0/0/0/2/2/0/0) + 27
EXCLUDED (7/3/3/2/3/3/3/3, with **three** snapshot timestamps per the OBS-E erratum) = 135. OQ-3
fail-closed collision, OQ-6 `pilot-coverage/1.0` (with its executable home an explicitly recorded
open path question — no `pilot_policy.py` constant and no seed row exists, verified by grep; §20 /
§23 item 28 stop-and-refer), and OQ-8 roles `winning`/`competing`/`supporting` (migration `0009`
CHECKs at lines 299/320) all verified. The graph is acyclic; no timestamp, path, `detail`,
operational event ID, `census_run_id`, approval/publication state, or physical SQLite byte enters
any identity.

**OR-2 135-column mapping — PASS.** The writable-column count re-derived from migration `0009`
verbatim: 28 + 26 + 35 + 8 + 13 + 13 + 6 + 6 = **135 exactly**. Every field carries exactly one
accepted derivation or an explicit fail-closed gap under the adopted basis as corrected; the eight
GV2 corrections each verified present and controlling (contract §8.1), with the GV2 corrections
controlling over the older proposal text wherever they differ (GR-C1/GR-C2 annotations in place).
Spot checks against schema and records: plain/dashed accession dual identity with the
`UNIQUE (snapshot_id, accession_number_dashed)` constraint and fail-closed disagreement; amendment
linkage five-value CHECK and `is_amendment` implications; SIC 6000–6999 and provisional-only CHECKs
on `primary_universe_eligible`; cohort vocabulary; XBRL iff-CHECK; single-anchor partial unique
index plus the freeze trigger's exactly-one-anchor and `multi_registrant` consistency checks;
`filing_date_precedence` CHECK = 2. No best-effort, discretionary fallback, manual fill, outcome
data, S4-draft input, CompanyFacts, Frames, or network fallback anywhere in the mapping.

## 11. Missing-evidence / fail-closed audit (packet §17) — PASS

The NULL rule (schema **and** applicability **and** accepted substantive methodology) is retained
verbatim (§8.1 correction 8), and the refuse-the-snapshot rule covers hard eligibility, hard
quotas, required classifications, required provenance, and manifest/root requirements (§23 item
27). Specifically re-verified: per-registrant historical documents (never acquired, never
retrievable, genuinely-required derivations fail closed; D023 **O1 retained exactly** — §23 item
11, §25, OR-11); SIC / `industry_family` / `primary_universe_eligible` (correction 5; GV2-20;
structural CHECKs); XBRL (evidence-level iff-CHECK); `census_index_instances` AVAILABLE-AS-NONE.
No source gap can silently degrade to lower evidence.

## 12. E0 lifecycle, owner gates, and E1/E2/M3.4 separation (packet §§18–19) — PASS

The E0 definition fixes all fourteen elements (input set; R17 write set; binding; fail-closed
interruption with a nonauthoritative partial state that blocks M3.3-E1 and returns to the owner;
explicitly-authorized deterministic rerun (never automatic — and mechanically deterministic:
`persist()` is idempotent per `parser_run_id`); R18 completeness proof; non-acquisition proof
(zero requests, no new observation/object, 77-of-801 unchanged); network-construction prohibition
proved by test; pre/post integrity; parser provenance; once-only private result token **never
treated as an E1 authorization**; stop conditions; the double owner gate — before E0 **and** after
verified E0 before E1). No token grants the next stage: contract acceptance starts nothing (§1,
§34, §36); I/R and rehearsal supply no E0 authority; E0 completion supplies no E1 authority (§10.2;
§23 items 23–24; §30 bullet 2 never merged into the M3.3A review); the freeze additionally needs
OR-9; sealing is a separate hard boundary from manifest construction (R5); OR-6 gates E2; the root
is an output never an approval; the terminal token and `m3.3-complete` confer no M3.4 authority; a
commit is never the authorizing artifact (§33). Rehearsal labels are distinguishable from real
gates on every current operative surface (§9, OBS-C row).

## 13. R3 read-only path review (packet §21) — PASS

| Path | Mode | Classification |
|---|---|---|
| `storage/catalog.py:89` `strictly_read_only_connection` → `storage/sqlite.py:68` `connect(read_only=True)` (`mode=ro` URI = `SQLITE_OPEN_READONLY`; mutually exclusive with `writer`; cannot checkpoint) | strict | **R3-COMPLIANT** |
| `m3/recovery.py:141` `read_only_catalog` (uses `strictly_read_only_connection` at :156) and its consumers | strict | **R3-COMPLIANT** |
| Accepted S5/S6 entry points (`load_frozen_joint_candidates`, `reconstruct_persisted_joint_selection`, `execute_and_persist_joint_selection` replay, `seal_selection_result`, `build_and_persist_pilot_manifest`, `verify_pilot_manifest`) — caller-supplied `sqlite3.Connection` | injected | **R3-COMPLIANT by injection** — M3.3 chooses the handle; no store edit needed |
| `cli.py:2274` (M3 migration-chain-head helper) → `read_only_connection` (convention-only read-write OS handle) | convention | **REQUIRES_BOUNDED_I/R_HARDENING** — reachable from M3.3 receipt-emitting commands |
| `cli.py:1310` (migration-chain-head helper) | convention | **REQUIRES_BOUNDED_I/R_HARDENING** if reached by an M3.3 command; otherwise NOT_USED_BY_M3_3 |
| `cli.py:2185` (`census_index_instances` satisfied-keys, M2.2 census path) | convention | **NOT_USED_BY_M3_3** |
| `storage/sqlite.py` `backup_database` | convention | **NOT_USED_BY_M3_3** for a governed read; R8's narrow rule would apply if ever used |

Every hardening need passes the entry test: exact call sites identified; required behavior fully
governed by R3 (true OS-level `SQLITE_OPEN_READONLY`, durable-byte equality, no writer lease; a
logical `query_only` convention insufficient — and the contract §14 says so explicitly); no
methodology choice remains; contract §20 explicitly authorizes the narrow hardening during I/R and
forbids repository-wide cleanup (R8). **No UNRESOLVED path.** No private catalog was opened.

## 14. Findings

**BLOCKER: none. MAJOR: none. MINOR: none. OPTIMIZATION: none.**

### OBS-R1 (OBSERVATION) — Decision 068 §3.1's "exactly twenty-four durable-write statements" numeral does not reconcile with the code or with the same record's own site enumeration

Decision 068 §3.1's first bullet states *"`sec/census.py` contains exactly **twenty-four**
durable-write statements, resolving to exactly **sixteen distinct tables**"*. This review's
independent mechanical enumeration of the same file at the frozen target finds **19** durable-write
execute statements (**23** when the four embedded `ON CONFLICT … DO UPDATE` upsert clauses at
lines 677/840/876/996 are counted as separate statements); summing Decision 068 §3's own per-table
"Written by (verified)" site list — including its separately listed upserts and UPDATEs, plus
`census_qa_metrics` — also yields **23**, not 24. **Every operative claim in the same sentence and
section is exactly correct and was independently re-verified**: sixteen distinct tables; the
fifteen-table permitted set; `census_qa_metrics` excluded with its sole caller at
`census_orchestrator.py:425`; every per-table line reference; the zero-write status of the loader,
archive, resolution, and parser modules; and the zero references to `census_plan_sources` /
`census_index_*` / `record_reasons` / `record_event`. The numeral changes no table membership, no
permitted write, no prohibition, no preimage, no boundary, and no authority, and the corrected
contract nowhere repeats it. Classified **OBSERVATION**, not MINOR, by the standard the prior
review applied to OBS-E (a narrative numeral contradicted by the same record's correct
itemization, in a record whose operative dispositions are verified right): the error is not on an
operative contract surface, requires no owner methodology decision, and needs no pre-acceptance
contract action. Accepted decisions are immutable (Decisions 001–068 are prohibited paths), so the
available vehicle — at the owner's discretion, not required for acceptance — is a narrow visible
erratum in a future owner record, exactly the OBS-E precedent. Recommended for the next authorized
owner record's housekeeping; nothing else.

## 15. Residue scan (packet §24)

Run across the contract, both decisions, STATUS, the registry, the index, the architecture map, the
change-impact map, the contracts README, the master plan, the runbook, the limitations register,
the inventory, and the proposal, for the packet's phrase list plus affirmative-authorization
variants. Every material hit classified; **no CURRENT-STALE hit survives**:

- "Decision 067/068 pending", "MAJ-1 open", "MIN-1 open" — **no hits** (the review statuses say
  ACCEPTED / findings adopted-and-corrected).
- "Both reviews" — one hit, inside Decision 068 §7's OBS-A disposition row describing the replaced
  wording — **HISTORICAL**.
- Architecture-map §10.2-as-R12-target — eliminated from the contract (now §10.1 with correction
  note); the STATUS marker and inventory already said §10.1 — **CURRENT-CORRECT**.
- "four snapshot timestamps" — only the preserved proposal sentence plus its erratum note, and
  D068 §7's description — **HISTORICAL** with the erratum visible.
- Old nine-table E0 list — survives only as descriptions of the corrected defect (D068 §3, the
  STATUS fresh-review marker, registry row 068) — **HISTORICAL**; the operative surfaces all carry
  fifteen.
- Bare `E1`/`E2` gate-meaning without the `M3.3-` prefix — **no hits** on current operative
  surfaces (word-boundary scan; §9 OBS-C row).
- Full-index `parser_state` completion language — every hit is the R18 negative form ("not 'mutate
  parser_state for every planned source'"; "deliberately untouched with parser_state unmutated") —
  **CURRENT-CORRECT**.
- `census_index_*` / `census_qa_metrics` as authorized E0 output — every hit states exclusion —
  **CURRENT-CORRECT**.
- "implementation authorized" / "E0 authorized" / "network authorized" / "contract accepted"
  affirmatives — the only affirmative hits are the completed M3.2 contract's own historical status
  lines (T1/Decision 034; T2/Decision 035 — authority exhausted) — **HISTORICAL**; every M3.3
  surface is negative.
- "entry-blocking" as current — the inventory's first banner paragraph retains "OR-1 and OR-2
  remain open and entry-blocking", explicitly superseded by its own next paragraph ("the paragraph
  above is historical as at the M3.3-GR packet") — **HISTORICAL**; all other hits state the
  condition's resolution or are the STATUS banner's own historical-marking rule.
- Fresh-review-pending wording — present and **CURRENT-CORRECT** (it is the actual pending state).

## 16. Broad semantic current-state review (packet §25) — PASS

Independent of the phrase list, the substantive current meaning was compared across all thirteen
required surfaces: (1) the active M3.3 contract ↔ (2) Decisions 067/068 (§6 above); ↔ (3) STATUS
(banner, `DECISION_067/068_*`, `M3_3_*` markers, `NEXT_AUTHORIZED_ACTION` — all agree with the
contract header, including the deliberate `ACTIVE_STAGE_CONTRACT = m3_2.md` rule that a corrected
contract is not the active contract); ↔ (4) the decision registry (rows 067/068 and the two
controlling-record rows, cleanly split); ↔ (5) the decision index (the M3.3 Q&A block: fifteen
tables, R18, R16-C1, "neither record accepts or authorizes"); ↔ (6) the architecture map (§0
Milestone 3 row current through Decision 068; §10.1/§10.2 bullets correct); ↔ (7) the change-impact
map (Decision 067/068 sections, governance-only, zero impact, correct surface lists); ↔ (8) the
contracts README (2026-08-13 update naming the fresh rereview by a non-author epoch as the next
act; the m3_3.md entry carrying the corrected status and both correction chains); ↔ (9) the
operator runbook (§28a carries the R17 fifteen-table footprint and the R18 dispositions; §29
carries the R4 Gate-H proof and the E0 precondition; §30 never-approve-implicitly); ↔ (10) the
limitations register (D021-L2 and D067-L1 `ACTIVE`; no limitation closed); ↔ (11) the master plan
(M3.3 §2/§6/§9/§26 all synchronized — the three-review structure with the post-E0 review asking the
fifteen-table and R18 questions; the R4 token note; the OBS-D descriptive-only driver category);
↔ (12) the GR proposal disposition (owner-disposed historical evidence, erratum visible, cite the
decision never the proposal); ↔ (13) the governance inventory (three dated banner layers, each
superseding the previous as current state; §G dispositions current through R17/R18/R16-C1).
Contradictions found that do not share the same words: **none**, beyond OBS-R1 (§14). The
three-commit distinctness rule (accepted M3.2 baseline `5c4c875e…` / closeout `2185f583…` + tag /
entry baseline `e3e58f93…`) is stated consistently everywhere it appears, and the entry software
baseline was proven byte-intact at the target (§2).

## 17. Migration / schema review (packet §22) — `MIGRATION_AUTHORIZED: none` is CORRECT

All fifteen R17 tables exist in migrations `0001`–`0006` (mapped table-by-table:
`reference_sic_codes` `0001`; ten tables `0003`; `census_structural_observations` and
`census_malformed_historical_references` `0005`; the two resolution tables `0006`); the four
index-side tables (`0006`/`0007`) exist and stay unwritten; `census_plan_sources.parser_state` and
its vocabulary exist in `0004`; the candidate/selection/manifest surfaces exist in `0009`–`0013`
with the lifecycle guards read verbatim (snapshot insert-must-be-building, transition guard,
22-field frozen immutability, no-delete, freeze validation incl. per-dimension evidence backing,
building-window guards on all seven child tables). R17, R18, and R16-C1 intrinsically require **no
new table, column, enum, or migration** — R18 is expressly report-level, R16-C1 is a derivation
clarification, and R17 names only existing tables. `coverage_policy_version` is `TEXT NOT NULL`
with no FK, so writing the owner-fixed literal needs no migration; its executable home remains the
recorded open path question (§20; §23 item 28). A migration appearing necessary correctly remains a
stop condition (§23 item 17).

## 18. Validation (packet §26) — all green, timed

| Gate | Result | Elapsed |
|---|---|---|
| `make secrets` | PASS — 317 textual files scanned, 0 findings | 0.75 s |
| `make hygiene` | PASS — 319 paths checked, 0 findings | 0.21 s |
| `make context` | PASS — live state matches §2/§3; switches `false`/`false`; migrations `0001`–`0013`; `NEXT_AUTHORIZED_ACTION` = this rereview | 0.72 s |
| `git diff --check` (worktree and index) | clean — no whitespace or conflict markers | 0.07 s |
| Repository-relative link/navigation validation | **688 links across 15 governance documents, 0 broken** | 0.26 s |

No pytest was run: this is a read-only contract rereview, no executable byte changed since the
accepted entry baseline (proven by diff, §2), and the packet prohibits parser/private-evidence
execution. Pre-artifact re-verification: working tree clean; HEAD and `origin/main` still
`7bb36b80…`; no target-tree mutation.

## 19. Contract acceptability, authorization state, and next action

**The Decisions-067–068-corrected contract passes this fresh independent rereview** at BLOCKER 0 /
MAJOR 0 / MINOR 0 (one OBSERVATION, §14, requiring no pre-acceptance contract action). Every prior
finding is closed (§9); the E0 boundary is now executable in principle within exactly the
mechanically verified footprint of the accepted machinery; and no implementation, parse, snapshot,
selection, manifest, root, network, reacquisition, migration, or M3.4 authority leaked anywhere.

**This review does not accept the contract and starts nothing.** The authorization state is
unchanged from §3 in every particular. The next action is Sol/GPT's alone: a separate owner
acceptance act for the corrected contract, and — only after and separately — any M3.3-I/R
implementation authorization. The review target remains frozen at
`7bb36b80b6a7f3cb28eb28947ee2908c08672f50`; this artifact's own commit is a review-record commit
and changes no authority.
