# Decision 151 — R2-C Parser 1.3, the Registrant Current-Name Defect, and FailFast-D

```text
STATUS: ACCEPTED BY PROJECT OWNER — PRESERVED WIP; PROSPECTIVELY CORRECTED (V5), THEN
       WAL-PRESERVATION CORRECTED, THEN VALIDATED BY NORMAL CI ON ITS EXACT TREE, THEN INDEPENDENTLY
       RE-REVIEWED (R3) WITH THAT TECHNICAL REVIEW OWNER-ACCEPTED, THEN CLOSED BY AN OWNER-ACCEPTED
       FINAL LOCAL FULL GATE OVER TREE ef0e9e24f39e141191148ec5b282f36003ee343e. THE §7c GOVERNANCE
       DOCUMENTATION CLOSEOUT IS OWNER-ACCEPTED, FINAL_FULL_GATE IS CLOSED AND THE IMPLEMENTATION IS
       OWNER-ACCEPTED; §7d states the governed-publication boundary. R3 MINOR-1 REMAINS DEFERRED AND
       UNREPAIRED
RECORD_TYPE: OWNER RULINGS R1–R6 (FROZEN) + BOUNDED ENGINEERING RECORD — PARSER 1.3 AND FAILFAST-D
DATE: 2026-09-08
FINAL_ACCEPTANCE_AND_PUBLICATION_UPDATE: 2026-09-09 — the date this acceptance and publication state
       was recorded, NOT a date of authority issuance; the frozen rulings and the record's original
       date are unchanged
OWNER: Joey — rulings R1–R6 and the supplied census/outcome-neutrality findings
CANDIDATE_ORIGIN: Claude Fable 5.1 at maximum effort, one session, no subagents, no delegated
       reasoning, USING M3_3_D151_R21_R2C_PARSER13_FAILFAST_ENGINEERING_V3_AUTHORIZED — a token the
       owner had ALREADY SUPERSEDED before that execution. That use is historical fact, not
       authority: V3 was NOT a valid live Phase-B authorization when it was used and the owner does
       NOT retroactively ratify it, so V3 itself conferred no authority and no acceptance on these
       bytes. The owner's later implementation acceptance is a SEPARATE, prospectively issued
       instrument recorded in §7d; it accepts the bytes and it does NOT legitimize V3. Every prior
       V1/V2 engineering token is SUPERSEDED and was NOT consumed; V4 is
       SUPERSEDED_UNCONSUMED and must not be reused; no successor token was minted by an executor
CANDIDATE_STATE: preserved WIP over the Phase-A baseline, owner-accepted at the final local gate
       and published by the single governed commit §7d defines; the accepted bytes are unchanged by
       that publication
INITIAL_INDEPENDENT_TECHNICAL_REVIEW: ACCEPTED BY THE OWNER — zero BLOCKER and zero MAJOR code
       defects in the substantive parser-1.3 / R2-C / FailFast-D design. Its accepted findings are
       its MAJOR-1 (governance/provenance truth) and its MINOR-1 through MINOR-4 — the REVIEW's
       numbering, distinct from the engineering findings §5/§6 number the same way; the corrections
       are cited as C1–C5 in §7b. Review acceptance is NOT implementation acceptance
PROSPECTIVE_CORRECTION_AUTHORITY: M3_3_D151_R21_R2C_PARSER13_FAILFAST_PROSPECTIVE_CORRECTION_V5_AUTHORIZED
       — the fresh owner instrument adopting the Codex-hardened bounded-correction packet (SHA-256
       ab7dcd3632a3dbb53ed8faafe3fa3c346dc7b5e60c58fe20bc155d5fc7bc2b33, 34,673 bytes). It
       authorizes the bounded C1–C5 correction of the preserved WIP and NOTHING ELSE. Executed by
       Claude Opus 5 at maximum effort under the owner's explicit in-session executor substitution
       ("opus authorized instead of fable"), one session, no subagents, no delegated implementation.
       The ORIGINAL Phase-B bytes were NOT produced under this authority and are not relabelled
WAL_PRESERVATION_CORRECTION_AUTHORITY: M3_3_D151_R21_V5_WAL_PRESERVATION_PRODUCTION_CORRECTION_CI_R2_AUTHORIZED
       — a LATER and SEPARATE owner instrument, distinct from V5 and from V5's own correction item
       C2. It authorized exactly one production path (§7c) and the exact-tree CI that validated it.
       Executed by Claude Opus 5 at maximum effort; the packet named Fable and the owner/operator
       explicitly substituted Opus in-session, which is recorded here as a deviation, not concealed
EXACT_CANDIDATE_NORMAL_CI: GREEN — bound ONLY to tree 59e52bb2aedcfcf94cd3282c5ad7e017ccf1d4ca,
       GitHub Actions run 34309408051, attempt 1 (§7c). It is NOT a statement about live main, NOT
       full-gate closure, and NOT a claim about the documentation tree this closeout produces
INDEPENDENT_CORRECTION_REVIEW: M3_3_D151_R21_V5_WAL_C2_POST_CI_OPUS_R3_READONLY_AUTHORIZED — a fresh
       Claude Opus 5 Maximum read-only session ("R3"). COMPLETED. Technical verdict
       POST_CI_C2_CANDIDATE_TECHNICALLY_ACCEPTABLE_FOR_OWNER_ADJUDICATION at zero BLOCKER and zero
       MAJOR. The governing owner ACCEPTED that technical review and its finding classification;
       accepting a review is NOT accepting the implementation
GOVERNANCE_DOCUMENTATION_CLOSEOUT: M3_3_D151_R21_C2_GOVERNANCE_PUBLICATION_CLOSEOUT_R1_AUTHORIZED —
       the bounded five-surface documentation update recorded in §7c, executed by Claude Opus 5 at
       maximum effort under the owner's explicit in-session executor substitution ("opus is owner
       authorized"). It changed NO source or test byte, ran NO test suite, closed NO gate, and exits
       UNCOMMITTED AND UNSTAGED. The governing owner has since ACCEPTED it (§7d)
FINAL_LOCAL_FULL_GATE: M3_3_D151_R21_FINAL_LOCAL_FULL_GATE_R1_ACCEPTED — one make check-fast over
       tree ef0e9e24f39e141191148ec5b282f36003ee343e, seven worksteal workers, all eleven gates PASS,
       6304 passed and 1 skipped. The owner ACCEPTED that gate and its result (§7d)
FINAL_PUBLICATION_AUTHORITY: M3_3_D151_R21_FINAL_PUBLICATION_SINGLE_GOVERNED_COMMIT_R1_AUTHORIZED —
       a BOUNDED historical instrument authorizing exactly one governed local commit of the accepted
       bytes plus this five-file publication-state delta, and exhausted by that commit. It is NOT an
       evergreen permission to commit and it authorizes NO operational execution
PHASE_A_COMMIT: 80c84c81489785c1ed4f78777af5b69dfa924aed (AGENTS.md compatibility pointer ONLY;
       parent 9f71f794e79e225c9e3f298d6428fdd79d3fca31; TREE 8286a60dee66975a2e9f7aa3f1ebb78814f2a2c2)
       — PROSPECTIVELY ADOPTED by the owner as the current baseline; adopting it ratifies nothing
       about the Phase-B execution
PHASE_B_BASELINE: HEAD 80c84c81… / TREE 8286a60d… — clean index and worktree at entry; Phase B and
       the V5 correction pass both exit UNCOMMITTED and UNSTAGED, with ZERO implementation commits
NEW_PARSER_VERSION: submissions-json/1.3 (1.2 is historical, exactly as 1.1 is)
NEW_REASON_CODE: PARSER_REGISTRANT_NAME_DEFICIENT — integrity, requires_manual_review=true, blocks_release=false
INTERMEDIATE_RECEIPT_CONTRACT: m3.3-chunked-f0-intermediate-receipt/1 -> /2 (/1 forensic-only)
DATABASE_MIGRATION: NONE — head remains 0015, 0016 absent
PREREGISTRATION_PROTOCOL_TEXT: UNCHANGED — no §25 deviation required (R4); audit fields retained in §4

C31R2_COMPLETE = NO
C31R3_AUTHORIZED = NO
PRODUCTION_F0_AUTHORIZED = NO
S19_RERUN_AUTHORIZED = NO
H2_EXECUTION_AUTHORIZED = NO
SHADOW_A_EXECUTION_AUTHORIZED = NO
SHADOW_B_EXECUTION_AUTHORIZED = NO
ANY_SHADOW_EXECUTION_AUTHORIZED = NO
STORAGE_RECLAMATION_AUTHORIZED = NO
PHASE_B_SESSION_IMPLEMENTATION_COMMITS = 0 — historical: the Phase-B, V5, WAL-C2, R3 and
    documentation-closeout sessions each exited with zero commits
FURTHER_IMPLEMENTATION_COMMIT_AUTHORIZED = NO — beyond the single governed publication commit of §7d
DECISION_151_COMMITTED_PUBLICATION = the governed-publication boundary of §7d
OWNER_IMPLEMENTATION_ACCEPTED = YES — M3_3_D151_R21_IMPLEMENTATION_ACCEPTED
FINAL_LOCAL_GATE_OWNER_ADJUDICATION = ACCEPTED — M3_3_D151_R21_FINAL_LOCAL_FULL_GATE_R1_ACCEPTED
FINAL_LOCAL_GATE_TREE = ef0e9e24f39e141191148ec5b282f36003ee343e
GOVERNANCE_CLOSEOUT = OWNER_ACCEPTED
V3_OWNER_ACCEPTED = NO
V3_RETROACTIVE_RATIFICATION = NO
V4_STATUS = SUPERSEDED_UNCONSUMED
V5_STATUS = CONSUMED
WAL_C2_CORRECTION_PRODUCTION_PATHS = 1
WAL_C2_TEST_MODIFICATIONS = NONE
WAL_C2_R36_MODIFICATION = NONE
WAL_C2_STORAGE_FLOOR_CHANGE = NONE
WAL_C2_MIGRATION = NONE
WAL_C2_COMPATIBILITY_BRIDGE = NONE
WAL_C2_PARSER_OR_METHODOLOGY_REDESIGN = NONE
C2_NORMAL_CI_TREE = 59e52bb2aedcfcf94cd3282c5ad7e017ccf1d4ca
C2_NORMAL_CI_RESULT = GREEN
LIVE_MAIN_NORMAL_CI = NOT_GREEN — main is red independently (run 34075716227); see §7c
CORRECTION_REVIEW_COMPLETE = YES — R3, COMPLETED
R3_TECHNICAL_REVIEW_OWNER_ACCEPTED = YES
R3_REVIEW_BLOCKER = 0
R3_REVIEW_MAJOR = 0
R3_REVIEW_MINOR_1 = DEFERRED_NONBLOCKING — NOT repaired
R3_REVIEW_MINOR_2 = CLOSED — owner-accepted with the §7c.5 closeout
DOC_CLOSEOUT_NORMAL_CI = NOT_RUN
GOVERNED_CHECKOUT_IMPLEMENTATION_COMMITS = the governed-publication boundary of §7d
FINAL_FULL_GATE = CLOSED
PUSH_AUTHORIZED = NO
TAG_AUTHORIZED = NO
MERGE_AUTHORIZED = NO
CANARY_AUTHORIZED = NO
```

## 1. What this record is, and what it is not

This is the **formal Decision 151**: the owner's frozen rulings R1–R6 on the registrant
current-name defect that stopped the historical level-2 world at S19, and the bounded engineering
record of their implementation — parser 1.3 and the FailFast-D boundaries — prepared locally, held
uncommitted through every validation step, and **owner-accepted** at the end of them. Its first
independent technical review is owner-accepted; the five findings
that review raised have since been corrected under the owner's separate V5 prospective-correction
authority. Three later, separately authorized steps then followed, and §7c records all three: one
further **production** correction — the WAL-preservation guard's activation statement — then normal
CI on the exact corrected candidate tree, then a fresh independent correction review ("R3") whose
**technical** verdict the governing owner has accepted at zero BLOCKER and zero MAJOR. All four steps
that then remained are **done**, and §7d records them: the owner accepted the §7c.5 documentation
closeout, a separately authorized final local full gate passed over tree
`ef0e9e24f39e141191148ec5b282f36003ee343e` and was accepted, the owner accepted the implementation,
and a single bounded publication authority carried it into one governed local commit.

**It is not the `D151` campaign.** Since August 2026 the label `D151` has named the chunked-F0
engineering campaign and its run identities — `D151-C1` through `D151-C31R2` and the `R`-series
recovery packets, for example the predecessor run `d151-c31r2-20260830T150526Z` — whose records are
owner packets and evidence roots outside `Docs/Decisions/`. This record does **not** rename that
campaign, does **not** retroactively authorize any of its runs, and does **not** relabel its
historical evidence; `decision_registry.md` carries the numbering note. Where both could be meant,
"Decision 151" is this record and "D151-…" is the campaign.

**Owner acceptance advances no scientific stage, and this record authorizes nothing operational.**
The negative authorities in the owner packet remain in force: no H2 execution, no historical chunk launch, no real or governed L1/L2 launch, no
S19 resume or rerun on a governed estate, no Shadow-A/Shadow-B or other shadow continuation, no
production F0, no network or acquisition, no SSD movement, no deletion or reclamation of
pre-existing data or evidence, no old-estate mutation, no parser-1.2-to-1.3 compatibility bridge,
no push, no merge, no rebase, no tag, no branch or history change beyond the single governed
publication commit §7d defines, and no further implementation commit after it. Phase A's governance
commit accepted and authorized nothing about Phase B; the owner's later acceptance (§7d) is what
accepted the implementation, and it authorizes no operational step.

## 2. Owner rulings — frozen

**R1 — POLICY_R2_ACCEPTED.** For a primary SEC submissions document with a canonically usable CIK, a
missing, null, non-string or blank current `name` is a **company-name data-quality defect**. That
defect alone MUST NOT make otherwise structurally evaluable `filings`, `filings.recent` or
`filings.files` indeterminate. An invalid or unusable CIK remains blocking. No name may be
fabricated. `formerNames` MUST NOT become the current `company_name`.

**R2 — REPRESENTATION_R2C_ACCEPTED.** For a valid CIK with a deficient current name: persist the
registrant identity by CIK; emit no invalid `company_name` observation; preserve every otherwise
valid registrant observation and all filing metadata; emit exactly one explicit **field-level**
`QuarantinedRecord` at `record_path="name"`; use one NEW registered reason code with
`requires_manual_review=true` and `blocks_release=false`; and distinguish absent / null / non-string
/ blank in its detail. `SEC_SCHEMA_REQUIRED_FIELD_MISSING` is not reused for this non-blocking
defect.

**R3 — PARSER VERSION.** `submissions-json/1.2 -> submissions-json/1.3` is mandatory. The emitted
semantics moved, so the version moves with them; 1.2 output is never presented as 1.3 output.

**R4 — NO_FORMAL_§25_DEVIATION_REQUIRED.** This record carries the §25-style audit fields (§4). The
preregistration protocol text is not modified.

**R5 — FAILFAST_D_ACCEPTED.** Defensive semantic enforcement at the specified boundaries (§6). S19
remains the accepted final assertion with unchanged methodology.

**R6 — RECOMPUTE_H2_REQUIRED.** The authoritative post-correction calibration requires 34 chunks ->
34 retained witnesses -> 5 level-1 intermediates/lifecycle artifacts -> one new level-2 successor
world, under one repository revision and parser 1.3. That campaign, and any parser-version
compatibility bridge, remain **unauthorized** by the packet and by this record.

## 3. The supplied owner findings, and their evidence

The following are **owner-supplied findings**, recorded here as supplied and cited to their existing
evidence. This session performed no census, opened no archive member, read no estate database and
executed nothing against the governed source; it neither confirms nor extends them.

- **Archive identity.** SHA-256 `c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f`
  — the governed bulk source, verified by
  [Decision 150](decision_150_m3_3_final_fable_precanary_review.md) §8 at `1,556,847,020` B,
  `985,834` governed members, `5,337` shards, structural-preflight digest `e58b9100…`.
- **Census (owner-supplied).** `980,497` primary documents; `1` blank-name primary;
  `980,496` valid-name primaries. Evidence: the owner's census evidence root
  `d151_c31r2r21_s19_empty_name_census_20260908T170221Z` under the private run-log root, named
  here as the owner's location and not opened by this session.
- **The affected record.** `CIK0001161343.json` — the one blank-name primary. Its only filing is
  a `POS AM` dated `2001-10-23`; it carries **no filing on or after 2010, no 10-K and no 10-K/A**.
- **Archive-specific outcome-neutrality.** For THIS archive the correction changes **zero cohort
  rows**: the affected registrant contributes no filing to any frozen cohort window. This is a
  finding about archive `c85744be…` and is **not** generalized to any other archive.
- **CIK is the stable identity; `company_name` is an observation.** The registrant row is keyed by
  CIK; the current name is one `census_registrant_observations` kind among several and is never
  part of any identity preimage.
- **No scientific metric was viewed.** The owner attests, and this session confirms for its own
  work, that no transition, test or prospective metric exists or has been viewed: the defect was
  found and adjudicated at the F0 metadata layer, in a calibration world that never reached a
  research table.
- **C31R2 is non-complete forensic evidence.** The historical level-2 world stopped at S19 with
  `parser_state='failed'` because the blank-name primary was document-fatal under parser 1.2; its
  chunk-0012 artifacts were already exact-deleted under group-0001's recorded lifecycle. Nothing in
  that estate is restored, rewritten or relabelled by this record; a corrected calibration is R6's
  unauthorized future campaign.

## 4. Audit fields (the §25-style record, without a §25 deviation — R4)

```text
DATE:                              2026-09-08
OWNER:                             Joey
AFFECTED_HYPOTHESES_ANALYSES:      NONE
REASON:                            parser 1.2 treated a blank current registrant name as
                                   document-fatal; the name is a data-quality observation, not the
                                   document's identity, and the accepted terminal vocabulary already
                                   admits a quarantined parse
SCIENTIFIC_METRICS_VIEWED:         NO
ARCHIVE_SPECIFIC_IMPACT:           zero cohort rows (archive c85744be…; not generalized)
NEW_PARSER_VERSION:                submissions-json/1.3
PROTOCOL_TEXT:                     unchanged (Docs/preregistration.md not modified; §25 register unchanged)
CONFIRMATORY_STATUS:               the confirmatory design is untouched; no §25 deviation is required
```

The change is confined to how one metadata field of one source document is classified before any
research table exists. The cohort windows, maturity gates, primary outcome, hypotheses, thresholds
and bootstrap seed (`src/disclosure_drift/cohorts.py`) are untouched.

## 5. Parser 1.3 and the reason code

`src/disclosure_drift/sec/parsers/submissions.py`, `submissions-json/1.3`:

- **A.** `name` moved from `_REQUIRED_TOP_LEVEL` into the recognized optional top-level set, so
  neither an ordinary nor a deficient name is unknown-field drift and a missing, null or
  non-string name is no longer blocked by `inspect_payload` before the name handling sees it.
- **B.** The combined CIK/name identity failure is split: an unusable CIK keeps its blocking
  `SEC_SCHEMA_REQUIRED_FIELD_MISSING` quarantine and its `_regions_when_document_unusable`
  treatment, decided alone; a concurrent name defect neither rescues nor suppresses it.
- **C.** `classify_current_name` decides absent / null / non-string / blank by key membership,
  `isinstance` and `str.strip` — never truthiness, never `str(value)`.
- **D.** Valid CIK + deficient name ⇒ the registrant record carries **no** `name` key (the census
  therefore emits no `company_name` observation for it), one `QuarantinedRecord` at
  `record_path="name"` under `PARSER_REGISTRANT_NAME_DEFICIENT` with the class in its detail and
  the observed value in its raw excerpt, and one normalization warning naming the class.
- **E.** `filings`, `filings.recent` and `filings.files` are evaluated from their actual values;
  a name-only deficiency never routes through the unusable-document path.
- **F.** Every other valid observation and all filing metadata are preserved; a genuinely
  malformed required structure still refuses on its own terms.
- **G.** No current name, placeholder or `formerNames` value is ever synthesized.

`src/disclosure_drift/reasons.py` registers exactly one code, `PARSER_REGISTRANT_NAME_DEFICIENT`
(integrity, review required, not release-blocking, decision reference this record), raising the
registry to 115 codes. No SQLite migration: the existing field-level quarantine representation and
runtime reason-code seeding carry it.

One additional direct-contract path, found at the full gate: the M3.1 offline rehearsal's scenario
A8 ("Blocking schema drift", `src/disclosure_drift/m3/rehearsal.py`) built its "required field
missing" variant by dropping `name`, which encoded the 1.2 rule. It now drops `cik` — the one
top-level identity the parser still refuses without — so the scenario keeps exactly the blocking
semantics the accepted spec states (`Docs/m3/offline_rehearsal_spec.md` §A8 names no particular
field and is unchanged). The other three A8 variants and every other scenario are untouched.

## 6. FailFast-D — the boundaries

**MAJOR-1 — declaration consistency (bounded closure).** Under 1.3 the narrow extractor
`offline_parse._primary_document_declarations` and the parser agree on every deficient-name parent:
the parser now returns its `filings.files` references for a valid-CIK document whatever its name,
so the extractor's declaration and the parser's declaration are the same. Within the cheap
predicates the extractor checks (decodable object, usable `cik`, `filings` an object,
`filings.files` a list of objects with usable names the archive carries) a parser-refused primary is
never certified as a parent, and no parentage is manufactured: an unusable CIK declares nothing on
both sides, a contradicted or undeclared shard is refused by `_resolve_shard_parent`. **The one
residual, named:** a primary whose only document-fatal defect is a malformed top-level array
(`tickers` / `exchanges` / `formerNames` present and not a list) is declared by the extractor and
refused by the parser. It cannot reach a merged world — F0 builds its parent map from the parser's
own references, so the shard arrives undeclared and the traversal, or the shard chunk before it
parses one member, refuses it. The extractor's docstring states the coverage and the residual; the
extractor's semantics and performance are unchanged.

**Boundary 1 — truthful chunk terminal semantics.** `ChunkReceipt.status="complete"` remains
artifact/execution completion and is never parser-success evidence. The authenticated semantics of
an admitted chunk are read from its manifest-bound `census_parser_runs` row through `immutable=1`
(`chunk_consolidation.chunk_semantics`): the row is looked up by the authenticated source
observation, the accepted `_require_parser_run_truth` holds its parser identity to the execution
contract (the load-bearing site for a unanimous forgery, now asked before any world exists), the
`parser_run_id` must be the accepted preimage, the outcome must be in the accepted vocabulary, the
summary's blocking count must agree with the outcome, and the receipt's summary must agree with the
row. A positive quarantine count is not blocking; the accepted `_STREAMED_PARSER_STATE` and
`BLOCKING_PARSER_STATES` decide, not a new predicate.

**Boundary 2 — all three merge-admission paths.** `require_admissible_chunk_semantics` refuses a
blocking or unverifiable input **before** the output world, the attach, the load and the merge
exist, at `merge_group_body`, `merge_calibration_subset_group_body` and `consolidate_chunks` — in
the worker process itself, so direct worker entry is protected. `_admit_chunk_inputs`,
`resolve_chunk_inputs` and `resolve_contiguous_chunk_inputs` carry no success predicate and remain
usable for read-only inspection of a failed chunk. No forensic merge override, flag or diagnostic
execution route was added; no existing authorized forensic workflow required one.

**Boundary 3 — receipt `/2`, observability, retention.** `INTERMEDIATE_RECEIPT_CONTRACT` moved to
`m3.3-chunked-f0-intermediate-receipt/2`. A `/2` receipt carries four mandatory, mutually
consistency-checked fields measured in the merging process: `observed_run_outcome`,
`observed_quarantined`, `observed_blocking_structural`, `inputs_reached_blocking_terminal`. Ordinary
continuation, calibration and deletion admit a complete, consistent, non-blocking `/2` receipt only
(`require_admissible_intermediate_semantics`, applied in `resolve_intermediate_inputs`, the
retention lifecycle's reuse path, `run_multipass_f0`'s reuse path and
`delete_calibration_group_chunk_worlds`); `/1`, unknown versions, and incomplete or contradictory
`/2` evidence are refused. A separate read-only `read_legacy_intermediate_receipt` returns a
`LegacyIntermediateReceipt` for a `/1` document — original fields, version and byte identity, no
observed semantics invented, nothing written — and is not an `IntermediateReceipt`. **Expected
provenance movement:** the contract literal is folded into the reduced witness-ledger digest, so
`witness_ledger_identity` moves for every new write by design; historical `/1` identities are
untouched. **Prospective retention** is enforced in `delete_calibration_group_chunk_worlds` itself:
the intermediate must be admissible, and every chunk world still carrying its receipt must record a
non-blocking terminal that its own run row agrees with; a blocking or unverifiable world is retained
pending a separately authorized lifecycle. The historical chunk-0012 artifacts deleted under
group-0001's lifecycle are **not** restored and are not presented as retained.

**Boundary 4 — fresh and resumed S2 refusal.** In the level-2 engine, before any statement of any
stage after S2 begins (`_run_stage`, before residue disposition, attach and transaction), the
committed, authenticated S2 reduced run is turned into the accepted outcome object under the
StagePlan-sealed plan state and `require_f0_success` is asked — the accepted mapping,
`BLOCKING_PARSER_STATES` and `BLOCKING_SOURCE_DISPOSITIONS`, no new predicate. A refusal publishes a
create-once `semantic-refusal-<stage>-attempt-NNN.json` record in the stage receipt root and raises
the accepted refusal; the committed S2 world is preserved; an authentic blocking terminal is never a
pause eligible to continue. Enforced on fresh execution, on resume from a committed S2, and after a
crash between the S2 commit and its receipt. S19 remains the separate, unchanged final assertion.

**MINOR-1 — the committed reduced-run witness is authenticated.** `_verify_committed_witness` gains
the S2 branch: the row is looked up by the identity derived from the authenticated plan's source
observation and the authenticated contract's parser and version (the witness's own run id never
authenticates itself); identity, source observation, parser provenance, outcome, both counts, the
blocking count and duplicate identities from the row's summary, the parser state through the
accepted mapping and the row count are held to the witness, and any disagreement enters the
existing committed-state conflict path. The S19 branch re-derives the published counts and the
blocking predicate from the S2 and S18 witnesses. `parser_state` is not a `census_parser_runs`
column and is not pretended to be read.

**MINOR-3 — status legibility.** The receipt docstrings, the admission functions and the touched
tests state that `status="complete"` does not imply parser success. No durable field was renamed.

**S19 — unchanged.** `require_f0_success`, `BLOCKING_PARSER_STATES`, the meaning of
`E0_REQUIRED_PARSE` and the S19 stage are untouched; R2 changes which upstream condition is
document-fatal and nothing about S19's methodology.

## 7. Tests, and the accepted coverage that was re-premised

`tests/unit/test_decision_151_parser_1_3_failfast_d.py` carries the packet's thirty-four proofs.
Accepted coverage moved with the contract, never deleted or neutralized:

- `test_d151_r19_storage_charge.py` — the ALIEN fixture now names `/3` and still exercises a real
  contract refusal (it authorizes no `/3`).
- `test_d151_c13_multipass_plan.py`, `test_d151_c19_corrections.py` — the current contract pins
  assert `/2`; the legacy `/1` literal is pinned as forensic-only.
- `test_d151_r19_legacy_compatibility.py` — the two level-1 GROUP bodies are re-pinned by source
  digest (they now admit semantics and write `/2`); the two finalizers, the staging, the counters
  and the child entry remain byte-identical to the R19A-C2 baseline.
- `test_parser_version_authority.py`, `test_d131_historical_shard_dispatch.py`,
  `test_reasons.py` — the 1.2 pins move to 1.3 and the registry count to 115.
- `test_d151_c29r1_retention_aware_calibration.py` — the committed `parser_run_id` goldens moved
  because the accepted preimage carries the parser version (`de12930b…` under 1.2,
  `a89638…` under 1.3 over the synthetic observation); every other committed value is unchanged.
- `test_d151_c3_corrections.py`, `test_d151_c5_precalibration_hardening.py`,
  `test_d151_c1_equivalence.py`, `test_d151_c13_multipass_semantics.py`,
  `test_d151_r19_cross_store_recovery.py` — tests whose premise was "a failed chunk is admitted
  and the accepted gate refuses after the world is built" (D151-C3 MAJOR-1, D151-C5 INFO-6) are
  re-premised to FailFast-D: the failed chunk is refused at admission and no world exists, the
  failure evidence is compared at the chunk level, and the D140-R12 gate's load-bearing proofs now
  reach it through an injected failed reduction over healthy inputs.

The validation outcome is recorded in the execution report and in the ledger block.

**Validation status, stated exactly.** The original Phase-B validation is that execution's own
report. The V5 correction pass ran only its authorized BOUNDED validation — the Decision 151 proof
module (including the new MINOR-2 / MINOR-3 regressions), `test_reasons.py`, the two named
`test_d151_c5_precalibration_hardening.py` nodes, `ruff check`, `ruff format --check`, `mypy` over
`chunk_consolidation.py`, and the two documentation scanners. **At that pass `FINAL_FULL_GATE` was
`NOT_CLOSED`**; it was closed later, by the separate final local gate of §7d.
The V5 authority expressly does NOT authorize `make check`, `make check-fast`, the full suite or
the storage-heavy canary family, and capacity alone is not authority. The fresh correction reviewer
is therefore NOT required — and is not authorized by this record — to run a full gate; the full
gate is a separately authorized later execution with its own fresh capacity admission.

**What has been validated since, and what that does not close (§7c).** The later WAL-preservation
production correction ran its own bounded validation, and the **exact corrected candidate tree**
`59e52bb2aedcfcf94cd3282c5ad7e017ccf1d4ca` then passed **normal CI** — GitHub Actions run
34309408051 attempt 1, both jobs successful, `6298 passed, 7 skipped`. The R3 independent correction
review is complete and its technical verdict is owner-accepted. The governance documentation
closeout that records all of this ran only the three repository scanners and a focused five-surface
audit. **None of that closed the full gate.** A GREEN CI result on one tree is evidence, not
authority; `FINAL_FULL_GATE` was still `NOT_CLOSED` at that point, `DOC_CLOSEOUT_NORMAL_CI =
NOT_RUN`, and the documentation tree produced by the closeout was itself neither CI-tested nor
R3-reviewed. What closed the gate was the separate final local `make check-fast` of §7d, over the
accepted tree and under its own authority.

## 7b. The V5 prospective correction of the preserved WIP

Under `M3_3_D151_R21_R2C_PARSER13_FAILFAST_PROSPECTIVE_CORRECTION_V5_AUTHORIZED` the owner
authorized a bounded, prospective correction of the preserved WIP — **not** ratification of the
original execution. Five findings from the owner-accepted independent review were corrected, within
an eight-path write allowlist, and the pass exits uncommitted and unstaged.

**Read the finding labels carefully: they are the REVIEW's numbering, not this record's.** §5 and §6
above use `MAJOR-1` for declaration consistency, `MINOR-1` for the authenticated committed
reduced-run witness and `MINOR-3` for status legibility — those are the ORIGINAL owner packet's
engineering findings and are unrelated to the identically numbered review findings below. The
correction items are cited here as `C1`–`C5` precisely so the two sets never have to be told apart
by number alone:

- **C1 (MAJOR-1)** — truthful governance and provenance. Every live claim presenting V3 as valid
  Phase-B authorization is corrected across this record, the decision registry, `Milestones/STATUS.md`,
  the decision index and the change-impact map. Historical references to V3 are preserved where they
  correctly describe superseded origin evidence.
- **C2 (MINOR-1)** — the D151-C5 INFO-6 parity passage in `chunk_consolidation.py` is qualified in
  both the module docstring and the `consolidate_chunks` docstring: a blocking or unverifiable
  **input** chunk is refused at Boundary 2 before any output world exists, so the retained
  consolidated-versus-monolithic diagnostic parity applies only where a **reduction** becomes
  blocking after otherwise-admissible inputs entered consolidation. Documentation only.
- **C3 (MINOR-2)** — `chunk_semantics` builds its immutable read URI with the package's
  `Path.as_uri()` idiom, so the file path is percent-escaped before `?immutable=1` is appended, and
  catalog open/query failures are translated locally into `ChunkConsolidationError` with their
  cause. `uri=True`, `immutable=1`, read-only sidecar-free behaviour and deterministic closure are
  unchanged. **Scope limit:** this is the reader only. The raw URI construction in
  `chunk_consolidation.py::_attach_all` predates this correction, is present in `HEAD`, and is
  recorded by the owner as `DEFERRED_URI_PORTABILITY_MINOR`. This record does **not** claim
  end-to-end merge/attach support for directory names containing `?` or `#`.
- **C4 (MINOR-3)** — the two durable count reads use a local fail-closed validator (`_row_count`)
  instead of `int()`: an integer `>= 0` is valid, and absent, `NULL`, boolean, string, float or
  negative values are refused. No float truncation, string parsing, truthiness or default zero.
- **C5 (MINOR-4)** — the stale `test_reasons.py` test name is renamed to match the pinned
  `_TOTAL_COUNT` of 115. Body, assertions, constants and fingerprints unchanged.

INFO-1 through INFO-6 remain recorded information and were not reopened. No substantive redesign,
no guard movement, no acceptance-predicate change and no unrelated repin was made.

## 7c. The WAL-preservation correction, the exact-tree CI, and the R3 review

Three later steps, each under its own owner authority, followed the V5 correction pass. They are
recorded together because they are easy to confuse, and they must not be collapsed. In particular,
**V5's own correction item `C2`** — the INFO-6 parity docstring qualification in §7b — is a
documentation change and is **not** the **WAL C2 correction** below. The `MINOR-1` and `MINOR-2`
labels used here are the **R3 review's** numbering, unrelated to the engineering findings of the same
number in §5, §6 and §7b, and unrelated to the historical R19A/C2 and SSD-recovery R3 work.

### 7c.1 The one production correction

Authority: `M3_3_D151_R21_V5_WAL_PRESERVATION_PRODUCTION_CORRECTION_CI_R2_AUTHORIZED` — a separate
prospective instrument, not V5. Executed by **Claude Opus 5 at maximum effort**; the packet named
Claude Fable 5.1 and the owner/operator **explicitly substituted Opus in-session**. That deviation is
recorded here rather than concealed.

Exactly one production path changed — `src/disclosure_drift/m3/chunk_multipass.py`, target
`_WalPreservationGuard`:

```text
PRE_C2   chunk_multipass.py  b7f63ec676e9053917eba16b6ade26260707dd663d3b1a019bab9adf66ebd25c
POST_C2  chunk_multipass.py  f33b67ab8634440ab5449a2bfe41656f0f3dabe5e03018376211d891f89714a6
```

The guard's **constant-only `SELECT 1`** activation became `SELECT COUNT(*) FROM main.sqlite_schema`.
That statement has to locate a schema table, so it forces a real **database-backed read** through the
`mode=ro` preservation guard before the production writer opens; if activation fails, the guard is
closed and the operation **fails closed**. The existing preservation boundary, the guard's lifetime
and close ordering, and the existing tests all remain intact.

**Stated without overstatement.** This is **not** only a test-portability change — the production
implementation was corrected. It does **not** hold a permanently open read transaction. It is **not**
a universal proof about every SQLite build; it is the statement form whose database participation
does not depend on which build is running. It is **not** a new checkpoint mechanism.

```text
WAL_C2_TEST_MODIFICATIONS = NONE
WAL_C2_R36_MODIFICATION = NONE
WAL_C2_STORAGE_FLOOR_CHANGE = NONE
WAL_C2_MIGRATION = NONE
WAL_C2_COMPATIBILITY_BRIDGE = NONE
WAL_C2_PARSER_OR_METHODOLOGY_REDESIGN = NONE
```

### 7c.2 The historical CI failure, diagnosed

GitHub Actions run **34075716227** — on `main`, over a tree containing **none** of this candidate —
failed. The primary failure was the **d08** post-recovery assertion on the
`working_catalog.sqlite3-wal` **pathname disappearing**. The sequence is exact: the initial
nonzero/committed-WAL condition had **passed**; the production path then raised the **expected**
unexplained-committed-frame conflict; the later preservation assertion then met the absent WAL path.
The **R36** failure was a **cascade of that same d08 failure**, not an independent defect. The 50-GiB
storage admission was **not** the cause.

**One inference is expressly not drawn.** A failed pathname assertion is not evidence that the main
database file was mutated, nor that any data was lost. This record claims neither.

### 7c.3 The exact-tree CI validation

```text
BASE REF        d151-v5-ci-base-h0-r2  ->  80c84c81489785c1ed4f78777af5b69dfa924aed
CANDIDATE REF   d151-v5-exact-ci-r2
PROVISIONAL     3178abe09ee2eb3cb6c468e3cc38ef2b7c7a132f  (sole parent 80c84c81…)
TREE / T2       59e52bb2aedcfcf94cd3282c5ad7e017ccf1d4ca
DRAFT PR        #1
RUN             34309408051     ATTEMPT  1
CORE ENV        SUCCESS         SEC-ENABLED ENV  SUCCESS
FULL PYTEST     6298 passed, 7 skipped
```

Both relied-upon jobs were authenticated as testing **exactly** that tree.

**What the GREEN result is bound to, and nothing else.** `EXACT_V5_CANDIDATE_NORMAL_CI = GREEN` is
bound to T2, to run 34309408051 and to attempt 1. It is **not** `LIVE_MAIN_NORMAL_CI = GREEN` — main
is red independently at run 34075716227 — and it is **not** `FINAL_FULL_GATE = CLOSED`. The
provisional commit `3178abe0…` exists **only as validation evidence**: it is not the governed
implementation commit, it never enters the governed chain, and at that point the governed checkout
still carried zero implementation commits. That count is now measured by the governed-publication
boundary of §7d.

### 7c.4 The R3 independent correction review, and the owner's dispositions

Authority `M3_3_D151_R21_V5_WAL_C2_POST_CI_OPUS_R3_READONLY_AUTHORIZED`; a fresh Claude Opus 5
Maximum session; **COMPLETED**; technical verdict
`POST_CI_C2_CANDIDATE_TECHNICALLY_ACCEPTABLE_FOR_OWNER_ADJUDICATION` at **zero BLOCKER and zero
MAJOR**. The exact C2 production and test bytes require **no code correction**.

R3 independently authenticated the exact C2 candidate and its tree, the V5 preservation, the
one-path WAL correction, the exact GitHub CI tree and results, parser 1.3 and R2-C, FailFast-D, the
`IntermediateReceipt` `/2` contract, the forensic `/1` reader, retention, S2 restartability, the
reduced-witness authentication, the S19 nonchange, and the WAL correction. **The documentation
closeout of §7c.5 did not re-perform that review** and does not present itself as having done so.

The governing owner **accepted the R3 technical review and its finding classification**. Accepting a
review is not accepting an implementation. The owner disposed of its two findings as follows:

- **R3 MINOR-1 — `DEFERRED_NONBLOCKING`, and NOT repaired.**
  `tests/unit/test_decision_151_parser_1_3_failfast_d.py` lies outside several `test_d151_*` family
  sweeps, because its stem does not match that glob. The owner's disposition is to leave the file
  named as it is, to leave R36 and the family sweeps untouched, and to preserve the module's current
  **direct** coverage. It is recorded as deferred test/CI-infrastructure hygiene. **No claim is made
  here that the coverage gap has been repaired.**
- **R3 MINOR-2 — the governance/documentation remedy, addressed in §7c.5.** On that closeout's
  successful validation the finding was `CLOSED_IN_UNCOMMITTED_DOCUMENTATION`, pending
  governing-owner adjudication. The governing owner has **since accepted** that closeout
  (`GOVERNANCE_CLOSEOUT = OWNER_ACCEPTED`, §7d), so the finding is now simply `CLOSED`. Neither the
  closeout nor this record self-accepted it.

### 7c.5 The boundary of the governance documentation closeout

Authority `M3_3_D151_R21_C2_GOVERNANCE_PUBLICATION_CLOSEOUT_R1_AUTHORIZED`, executed by Claude Opus 5
at maximum effort under the owner's explicit in-session executor substitution. Its write set is
**five documentation paths and nothing else**: this record, the decision registry, the decision
index, the milestone status ledger and the change-impact map. Every other candidate path —
everything under `src/` and `tests/`, `AGENTS.md`, `CLAUDE.md`, `README.md`, the Makefile, the
workflow and configuration files, the preregistration, the frozen methodology and the stage
contracts — is **byte-identical** to the R3-reviewed C2 candidate. Its validation was bounded to the
Markdown link scanner, the decision section-reference scanner, the repository hygiene scanner and a
focused five-surface content/provenance audit; it ran **no** pytest, **no** `make check` or
`make check-fast`, and **no** CI. `DOC_CLOSEOUT_NORMAL_CI = NOT_RUN`.

Stated exactly, the candidate that closeout produced was **the R3-accepted, CI-tested implementation
bytes plus a separately validated five-file governance documentation delta, pending owner
adjudication**. The documentation tree itself was neither tested by run 34309408051 nor reviewed by
R3, and that closeout session exited **uncommitted and unstaged** with zero implementation commits.
Those statements describe that session as at its own date; §7d records what the owner did next.

## 7d. Final owner acceptance, the closed full gate, and the publication boundary

Owner implementation acceptance is recorded under `M3_3_D151_R21_IMPLEMENTATION_ACCEPTED`. The final
local gate over `ef0e9e24f39e141191148ec5b282f36003ee343e` passed and was accepted under
`M3_3_D151_R21_FINAL_LOCAL_FULL_GATE_R1_ACCEPTED`. `FINAL_FULL_GATE = CLOSED`.
`OWNER_IMPLEMENTATION_ACCEPTED = YES`. The §7c.5 governance documentation closeout is
`GOVERNANCE_CLOSEOUT = OWNER_ACCEPTED`, which is what moves its R3 `MINOR-2` from
`CLOSED_IN_UNCOMMITTED_DOCUMENTATION` to `CLOSED`. R3 `MINOR-1` is unchanged: `DEFERRED_NONBLOCKING`,
and **still not repaired**.

**The gate that closed it.** One `make check-fast` over that exact tree, seven `worksteal` xdist
workers, **all eleven gates `PASS`**: `6305` collected, `6304` passed, `1` skipped, zero failed, zero
errors, zero xfail, zero xpass, zero deselected, pytest duration `956.54` s. The one skip is the
unconditional in-test skip at `tests/unit/test_m23_pilot_manifest.py:429`
("`snapshot_state` is a fixed literal asserted before hashing"). No material coverage loss, resource
stop, power loss, worker crash or monitoring failure; complete candidate nonchange `PASS`. Free space
was `95,101,231,104` B at launch and never fell below the minimum observed `74,131,054,592` B
(69.04 GiB) — far above the unchanged `PRE_F2_MINIMUM_FREE_BYTES` production predicate, which was
neither bypassed, skipped, patched nor lowered. Two authentic gate artifacts disagree by `4,763,648` B
on one *post*-gate free-space figure; the owner ruled that
`FINAL_GATE_RESOURCE_REPORT_DISCREPANCY = ACCEPTED_INFO_PRESERVE_BOTH_NO_REPAIR`, both values are
preserved unrepaired in the private publication evidence, and neither is relied on here. That gate
ran on the **accepted implementation tree**, not on the tree this publication produces; the gate's own
terminal correctly recorded the states that were true when it ran, and it was not rewritten.

**The publication boundary.** The first governed commit on `d151-c1-chunked-f0` whose sole parent is
`80c84c81489785c1ed4f78777af5b69dfa924aed` and whose tree contains this final acceptance/publication
block together with the unchanged accepted implementation bytes is the Decision 151
**committed-publication boundary**. The earlier isolated provisional CI commit `3178abe0…` is
validation evidence only and never enters that chain. The authority that carried it,
`M3_3_D151_R21_FINAL_PUBLICATION_SINGLE_GOVERNED_COMMIT_R1_AUTHORIZED`, is a **bounded historical
instrument** exhausted by that single commit — not an evergreen permission to commit. That boundary
authorizes no additional commit and no operational execution.

**What this publication is, and is not.** It changes exactly five governance files — this record, the
decision registry, the decision index, the milestone status ledger and the change-impact map — and
**no source or test byte**. Its validation was bounded to the Markdown link scanner, the decision
section-reference scanner, the repository hygiene scanner, the secret scanner and a focused
five-surface content and byte-freeze audit. It ran **no** pytest, **no** `make check` or
`check-fast`, **no** mypy, **no** Ruff over source, **no** CI and **no** further technical review;
none is required, because the accepted implementation bytes it inherits are the ones the gate ran on.
It makes no claim that the publication tree itself ran `check-fast` or CI. Public-`main`
reconciliation and CI status are **not evaluated** here: the historically recorded `main` failure at
run `34075716227` stands as recorded, and nothing in this publication revalidates a remote.

**What acceptance does not do.** Accepting the implementation advances **no scientific stage**.
`V3_OWNER_ACCEPTED = NO` and `V3_RETROACTIVE_RATIFICATION = NO` are unchanged — the acceptance is a
later, separate, prospective instrument and legitimizes nothing about the superseded V3 execution.
`C31R2_COMPLETE = NO`: that world remains stopped, non-complete forensic evidence, and its
exact-deleted chunk-0012 artifacts are not restored. The storage dispositions are recorded from the
owner's rulings and are **not** re-established by any storage access in this pass:
`HISTORICAL_TERMINAL_SEAL = OWNER_ACCEPTED_COMPLETE`,
`SSD_PRISTINE_L2_PRESERVATION_COPY = OWNER_ACCEPTED_REAUTHENTICATED`,
`INTERNAL_STOPPED_L2_RECLAIM = OWNER_ACCEPTED_COMPLETE`,
`ADMINISTRATIVE_DS_STORE_EVIDENCE = OWNER_ACCEPTED_PRESERVED`.

## 8. Claim boundaries and the next gate

This record claims a local implementation, its validation, the bounded V5 correction of that
candidate, the one-path WAL-preservation correction, the normal CI result on that exact corrected
tree, the completed R3 review whose technical verdict the owner accepted, and — since §7d — the
owner's acceptance of the final local full gate and of the implementation itself, published by one
governed local commit. Nothing more. It does **not** claim a clean committed parser-1.3 execution
revision, public-`main` reconciliation, a revalidated remote, or that CI or any gate ran over the
publication tree §7d defines. Each earlier step's boundary still holds as it was written: acceptance
of an independent technical review was never implementation acceptance; completion of the V5
correction pass accepted nothing; a GREEN CI run on one tree is evidence and not authority; and the
§7c documentation closeout accepted nothing on the owner's behalf — the owner's own later instruments
did. Historical outcome-neutrality remains archive-specific; old parser-1.2 evidence is not
parser-1.3 output; deleted evidence is not restored.

**The sequence is complete.** Steps 1 and 2 of the original V5 §11 sequence — the fresh Claude Opus 5
Maximum independent correction review, and the owner's adjudication of that **review** — are **DONE**
(§7c.4). So are the four that then remained, all of them recorded in §7d:

1. governing-owner adjudication of the §7c.5 governance documentation closeout — **accepted**;
2. the separately authorized final local full gate on adequate host/storage with its own fresh
   capacity admission — **run, passed and accepted**; the remaining storage disposition is recorded
   from the owner's rulings rather than re-established here;
3. governing-owner implementation acceptance — **given**;
4. the separate publication authorization — **issued, bounded to one governed local commit, and
   exhausted by it**.

Nothing follows automatically from any of that. The R6 recompute (H2) needs its own owner instrument,
and so does every other operational step: no H2, historical execution, S19 run or rerun, shadow
execution, production F0, canary, storage reclamation, SSD action, network or acquisition, migration,
compatibility bridge, further commit, push, merge, rebase, tag or release.
