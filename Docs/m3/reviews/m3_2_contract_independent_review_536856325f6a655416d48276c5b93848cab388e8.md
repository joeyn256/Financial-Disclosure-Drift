# Independent M3.2 Contract Review — Draft at 536856325f6a655416d48276c5b93848cab388e8

**Artifact:** `Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md`
**Required by:** the owner's explicit authorization of 2026-08-03
(`OWNER_M3_2_CONTRACT_INDEPENDENT_REVIEW_AUTHORIZATION: APPROVED`) for a fresh, independent review of
the bounded Milestone 3.2 contract draft, and the draft's own §1 acceptance precondition ("independent
contract review by a session that authored none of this draft"). This review is the independent
contract review that precedes owner acceptance (transition T1 of the draft's §8 gate ladder).
**Review type:** independent, adversarial contract review of `Milestones/contracts/m3_2.md` as
committed. It is **not** owner acceptance, **not** implementation authorization, and it authorizes
nothing. No verdict of this review accepts the contract.

---

## 1. Independence and non-authorship attestation

- **Reviewer session:** `session_013AyJ5c15m329AebGZQr7ce`
  (`https://claude.ai/code/session_013AyJ5c15m329AebGZQr7ce`), Claude Code CLI, macOS
  (Darwin 25.5.0).
- **Model and settings:** Claude Fable 5 (`claude-fable-5`), maximum effort, Dynamic Workflows
  enabled, selected by the owner's explicit task instruction. Master plan §13 names "Opus Max" for
  reviews; the owner's explicit selection of Fable 5 Max for this task is an owner instruction and
  controls (owner rulings precede the plan in the accepted hierarchy) — the same adjudication the
  accepted §17 and step-14 review artifacts recorded.
- **Session discipline:** one active session only; no parallel session; no Git worktree. Two
  read-only fact-gathering subagents ran under this session's direction against the disposable
  independent clone (schema/migration enumeration; code-boundary inspection); they modified nothing,
  ran no network access, and returned raw facts only. **Every load-bearing authority document was
  read directly by this session, and the contract-review verdict below was determined directly by
  this session, not by a subagent.**
- **UTC review date:** 2026-08-04 (review executed 2026-08-03 local time, completed 2026-08-04 UTC).
- **Non-authorship attestation.** This session authored none of: `Milestones/contracts/m3_2.md`; the
  Decision 029 §12 step-17 completion work; the M3-L11 or M3-L12 closure updates; the related
  `Milestones/STATUS.md` or `Milestones/contracts/README.md` changes; the draft commit `5368563…`;
  any M3.1 implementation, governance, review, rehearsal, plan, budget, checklist, readiness-token,
  or evidence-index artifact used as a contract input; or any of Decisions 001–031. It began from a
  fresh context clear with the owner's review authorization as its first input. **No verdict,
  finding, or substantive conclusion was inherited from any earlier completion report or review**;
  prior records were treated as claims to locate, then verified independently against the committed
  tree, the accepted decisions, and the code. No authoring session's clone or working state was
  reused.

## 2. Reviewed baseline and contract identity

| Item | Value | Expected | Match |
|---|---|---|---|
| Branch | `main` | `main` | yes |
| Reviewed commit (`HEAD`) | `536856325f6a655416d48276c5b93848cab388e8` ("Draft bounded M3.2 contract") | same | yes |
| `HEAD` tree | `39fd29911a130a07fe58840c3d16e0d34a295575` | same | yes |
| Parent | `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4` ("Record M3.1 acceptance") | same | yes |
| `origin/main` | `536856325f6a655416d48276c5b93848cab388e8`; `HEAD == origin/main` | same | yes |
| Working tree at review start | clean; nothing staged; no non-ignored untracked path; `git diff --check` and `git diff --cached --check` clean | clean | yes |
| `m3.1-complete` tag object | `638a02b780d912ff7b37a2f523277b9d451a015a` (annotated; `git cat-file -t` = `tag`) | same | yes |
| `m3.1-complete` peeled target | `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4` | same | yes |
| Contract under review | `Milestones/contracts/m3_2.md` | same | yes |
| Contract status line | `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE` | same | yes |
| `IMPLEMENTATION_AUTHORIZATION` | `NO` | `NO` | yes |
| `NETWORK_AUTHORIZATION` | `NONE` (draft authorizes zero network access) | `NONE` | yes |
| **Contract SHA-256** | `d53547672f75124a773c17b8b49d29e69f20f2890725df80e67dfc74633ae390` (identical in the primary checkout and the independent clone) | — | — |
| `.env` | ignored (`.gitignore` line 2), present locally, invisible to Git status; **never read, printed, or copied by this review** | ignored | yes |

**Draft-commit path set.** `git show --stat 5368563` changed exactly four paths:
`Milestones/contracts/m3_2.md` (new, 430 lines), `Milestones/contracts/README.md`,
`Milestones/STATUS.md`, `Docs/m3/limitations_register.md` — exactly the authorized step-17 set.

**Implementation and test nonchange.** `git diff 970e050…..HEAD -- src tests scripts Makefile
pyproject.toml configs .github` is **empty**: implementation, test, script, build, and configuration
bytes are byte-identical from the frozen accepted M3.1 implementation
`970e050deb06910adcde8588101564beb7d19c74` (tree `d0c3c94cbf9128eaf0fdb1ef58179d9977d718d3`) through
the reviewed commit. All ten post-freeze commits are governance-only; their union of changed paths
is confined to `Docs/Decisions/`, `Docs/m3/`, and `Milestones/`.

**Baseline-state confirmations.** No M3.2 implementation exists (`m3 acquire` and
`m3 derive-dependent-plan` appear nowhere in `src/` or `tests/`; the `m3` CLI group carries exactly
the six accepted M3.1 commands). No operational catalog exists (no `catalogs/` directory; no tracked
or untracked `*.sqlite3` or `*.part` anywhere in the checkout). No live SEC request has occurred
(every existing receipt is a zero-network rehearsal or dry-run receipt per the accepted governance
records; no acquisition artifact exists). `/.m3-private-evidence` remains ignored (`.gitignore`
line 56) and hygiene enforces the reserved path.

**Public evidence identities re-verified.** The tracked sanitized §17 review re-hashes to
`9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3` and the step-14 acceptance review
to `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e` — both matching Decisions 030
and 031 and the contract's §2. The contract's plan, budget, checklist, and token-record identities
(`19be7bdc…`, `2d453e0b…`, `34fc0567…`, `b06ae373…`, ceiling 801) match accepted Decision 031 §4–§5,
Decision 030 §2/§5, the public evidence index rows `EV-M31B-001`–`EV-M31B-006`, and
`Milestones/STATUS.md`. Private evidence content was not read; bindings were verified through the
accepted public records, which is sufficient here.

## 3. Independent-checkout provenance

A fresh disposable independent clone was created after task start, outside the primary repository
and outside the external evidence root, in a session-scoped temporary working area whose
machine-local absolute path is not recorded here (repository hygiene; Decision 030 Ruling A
precedent). It was cloned from the local primary repository checkout, resolved to commit
`536856325f6a655416d48276c5b93848cab388e8` with tree `39fd29911a130a07fe58840c3d16e0d34a295575`, was
clean with no untracked path, contained **no `.env`** and **no private evidence artifact** (verified
by scan), and did not reuse any authoring checkout. The contract hashed identically in the clone and
the primary checkout. The clone was deleted after the review artifact was committed.

## 4. Controlling authority reviewed

Precedence applied: explicit owner decisions and authorization instruments; accepted numbered
decisions; accepted milestone contracts; the accepted Milestone 3 master plan; runbooks,
specifications, and templates; limitations, status, review, and evidence records; implementation;
prior completion reports as claims only.

Read directly by this session: `CLAUDE.md`; `Milestones/STATUS.md` (full, across targeted passes);
`Milestones/contracts/m3_2.md` (full, twice — primary and clone); `Milestones/contracts/m3_1.md`
(full); `Milestones/contracts/README.md` (full, plus the draft-commit diff of it);
`Milestones/milestone_03_master_plan.md` (global §§4–16 and phase M3.2 §§1–36 in full; M3.1 §§12,
14–15 for the route registry, marker, and formula; the request-budget quantity table);
Decisions 028, 029, 030, 031 (full); Decision 024 §§3–9; Decision 023 §7; Decision 013 §1;
`Docs/Decisions/decision_registry.md` (rows 001–031; 031 is the highest number; statuses of
007–013 and 023–031 confirmed); `Docs/m3/operator_runbook.md` (steps 16–28, Appendices A–C);
`Docs/m3/limitations_register.md` (summary, M3-L11, M3-L12, D023-O1, closing section);
`Docs/m3/execution_receipt_spec.md` (full); `Docs/m3/templates/gate_h_checklist.md` (full);
`Docs/m3/templates/evidence_index.md` (full, live instance); `request_budget.md`,
`interrupted_run_recovery.md`, `schema_drift_incident.md` (templates); `Docs/leakage_register.md`
(full); the accepted M3.1 step-14 review artifact (structure, attestation, baseline, scope).

Verified through directed read-only code inspection (subagent fact-gathering against the clone, with
load-bearing facts confirmed by this session against the same tree): migrations `0001`–`0013`
(complete object inventory), `storage/catalog.py`, `storage/sqlite.py`, `config.py`,
`configs/project.yaml`, `sec/transport.py`, `sec/httpx_transport.py`, `sec/http_client.py`,
`sec/request_ceiling.py`, `sec/source_registry.py`, `sec/urls.py`, `sec/sources.py`,
`sec/raw_store.py`, `sec/observation_catalog.py`, `sec/companyfacts_policy.py`, `reasons.py`,
`cli.py` (m3 group), `m3/request_plan.py`, `m3/receipt.py`, `m3/recovery.py`,
`m3/evidence_paths.py`, `tests/integration/test_no_network.py`, `tests/conftest.py`,
`scripts/check_repo_hygiene.py`, `Makefile`.

## 5. Complete scope

Everything the owner's review instruction names: repository preflight against the expected baseline;
the draft-commit path boundary; implementation/test byte-identity to the accepted M3.1 boundary; the
sixty-five adversarial questions (§7 below); the four preliminary owner concerns (§8); governance
gates (`make context`, `make secrets`, `make hygiene`, diff checks); contract-status and
negative-authorization scans; decision and registry consistency; M3-L11/M3-L12 closure verification;
D023-O1 presence; tag-object and peeled-target verification; contract internal-reference and
section-completeness checks against master plan global §16's twenty mandatory contents;
plan/budget/checklist/token identity checks; private-path and SEC-identity leakage checks; and the
targeted read-only schema and implementation inspection needed for the catalog and recovery
questions. Out of scope and not performed: contract acceptance; any edit to the contract; any
implementation; any network enablement, connectivity test, SEC contact, acquisition, request
planning, budget display, or token recording; any tag; any push. The full pytest suite was not
rerun: executable bytes are byte-identical to the tree the accepted step-14 review validated in full
(2739 passed / 1 pre-existing skip), and no executable claim in this review depends on a result that
proof does not already cover.

## 6. Validation commands and results

| Command | Result |
|---|---|
| `make context` | Green. Branch `main`; HEAD `5368563…` == `origin/main`; clean tree; latest migration `0013_m23_manifest_lifecycle_guards.sql` (13 migrations); latest decision `decision_031_m3_1_acceptance.md`; active contract `Milestones/contracts/m3_2.md`, status `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`; next authorized action `CHATGPT_OWNER_REVIEW_AND_ACCEPTANCE_DECISION_FOR_M3_2_CONTRACT_DRAFT`; network permission NONE; no tag at HEAD |
| `make secrets` | Passed: 264 textual files scanned, 0 findings |
| `make hygiene` | Passed: 266 paths checked, 0 findings (re-run green after this artifact was written) |
| `git diff --check` / `git diff --cached --check` | Clean |
| Tag verification | `refs/tags/m3.1-complete` is an annotated tag object `638a02b7…`, peeled to `4cd2c72…`, matching Decision 031 / STATUS |
| Registry consistency | Registry and directory both end at Decision 031; every decision the contract cites carries the status the contract assumes (007–013 approved; 023–024, 026–031 accepted) |
| M3-L11 / M3-L12 | Both `CLOSED — 2026-08-03` in the register, each on its complete closure-evidence list (see Q5) |
| D023-O1 | Present and latent: register entry, Decision 030 Ruling E, STATUS blocker line, contract §17 item 15 and §23 |
| Leakage scan of this review | No SEC identity, no credential, no `.env` content, no private absolute path, no private evidence content, no response body appears in this artifact |

## 7. The sixty-five-question adversarial matrix

### A. Status and authority

1. **Is the contract unambiguously draft-only?** Yes. The header block, the bolded preamble, §1, §24
   (negative authorizations), and §25 (stop-and-report boundary) each independently state that the
   draft authorizes nothing; STATUS and the contracts README index say the same.
2. **Does any wording accidentally grant implementation or network authority?** No. The one phrase
   that could be misread — the header's `CONTROLLED AND EXPLICITLY AUTHORIZED` — is the master plan
   §7/§11 network-permission *class name* for the future window, and the same sentence immediately
   confines it to "the separate owner instruments in §8". §16 opens "Nothing below is authorized by
   this draft." No grant survives adversarial reading.
3. **Is independent review truly required before owner acceptance?** Yes. §1: acceptance requires
   independent contract review by a non-author session, then explicit owner acceptance. This
   artifact is that review; it does not itself accept anything.
4. **Does the contract apply the correct authority hierarchy?** Yes. §1 ("this contract implements
   accepted records and overrides none of them; where they disagree, the accepted record controls
   and this draft must be corrected") and §25 restate the CLAUDE.md / contracts-README rule.
5. **Were M3-L11 and M3-L12 correctly closed?** Yes. Each register entry is `CLOSED — 2026-08-03`
   under the owner's explicit step-17 closure authorization, on the register's own closure-evidence
   list with every item satisfied — implementation and tests in the frozen accepted tree, full
   validation, the passed §17 and step-14 reviews, owner acceptance recorded by accepted Decision
   031, and the committed checkpoint (verified annotated `m3.1-complete`, tag object `638a02b7…`,
   peeled `4cd2c72…`). The Decision 030 Ruling D sequencing distinction is preserved verbatim in the
   M3-L12 entry, Decision 013 is byte-unchanged, and Decision 031 §6's `CLOSURE-READY PENDING STEP
   16` disposition was correctly superseded only after step 16 completed. The M3-L11 residual note
   (same-device backups; off-device decision deferred to the M3.2 contract's T4) is carried into
   contract §20 — consistent.
6. **Is D023-O1 carried forward without reinterpretation?** Yes. §17 item 15 and §23 restate exactly
   the Decision 023 §7 / Decision 030 Ruling E rule — latent, fail-closed, stop-and-refer, never
   reclassified by a session — with no broadening and no pre-resolution.

### B. Scope and sequencing

7. **Does the contract cover exactly the controlled metadata-acquisition milestone moved from former
   M2.3 S8?** Yes. §3 matches Decision 024 §5.1/§5.2 (S8 row) and master plan M3.2 §1; every S8 row
   inherited gate (Gate H pre-run recovery state, SEC user agent, bounded rate limiting, governed
   response classification, raw-store provenance, fail-closed drift) and prohibition appears in the
   draft; nothing from M3.1 or M3.3+ is pulled in (§13 defers all pilot work to M3.3+).
8. **Are the six transitions genuinely separate?** Yes. §8's T1–T6 table requires a separate,
   explicit owner instrument per consequential transition, forbids inference/combination/
   inheritance, and the T5 instrument must name the exact command invocation, window, plan hash,
   ceiling, and configuration change. T4 is evidence, "no instrument by itself enables anything."
9. **Does any readiness token, ceiling approval, contract acceptance, or implementation acceptance
   implicitly become live-operation authority?** No. §2 (token "readiness only"), §8 preamble
   (each is "not live-operation authorization"), §24 (acceptance "does not … convert the readiness
   token, the ceiling approval, or any M3.1 artifact into operation authority").
10. **Are M3.2A and M3.2B properly separated?** Yes. §6 (route split), §15 (no M3.2B planning,
    budgeting, approval, or start before the freeze; no ceiling inheritance), §17 items 2, 5, 21,
    and §8 ("M3.2B repeats T4–T6 with its own plan, budget, ceiling, and owner approval") — matching
    master plan M3.2 §§2, 3, 11, 16.
11. **Is Gate H correctly positioned after both acquisition windows?** Yes. §14: "Gate H … runs only
    after M3.2B and integrates both windows," matching master plan M3.2 §2 and the Gate H checklist.
12. **Is final M3.2 acceptance correctly separated from implementation acceptance and Gate H
    execution?** Yes. T3 (implementation acceptance, §8/§19) precedes any live operation; the
    post-operation independent M3.2 acceptance review (§19, master plan M3.2 §26) is a distinct
    later act by a session that ran none of the acquisition; the governance acceptance commit and
    the `m3.2-complete` tag (§22) follow it under separate owner authorization.

### C. M3.2A plan and ceiling

13. **Are the plan, budget, and evidence identities exact?** Yes. §5's identities re-verify against
    accepted Decision 031 §4–§5, Decision 030 §2/§5, evidence-index rows EV-M31B-001–006, and
    STATUS: plan `19be7bdc…` (schema `m3-request-plan/1.0`, planner `quarterly-index-instances/2.0`
    — both constants confirmed in code), budget `2d453e0b…`, checklist `34fc0567…`, token record
    `b06ae373…`, ceiling 801 bound to the plan hash.
14. **Are 75 logical requests, 70 quarterly indexes, and ceiling 801 correctly represented?** Yes,
    and independently recomputed: U = (1,1,1,1,1,0,70) over the seven bootstrap routes sums to 75;
    the ceiling is the Decision 029 §8 per-route sum 4×(1×6) + 1×7 + 0×6 + 70×11 = 31 + 770 = 801;
    the 70 required instances are `2009QTR1`–`2026QTR2` with closed 2026 Q2 included exactly as
    Decision 013 §1 requires; maximum new raw objects 75; cache hits 0, excluded before planning and
    never subtracted again (Decision 028 §10; Decision 029 §8's corrected q).
15. **Is every physical retry, redirect, and post-cooldown request counted?** Yes. §9 bullet 4
    matches the master plan §4 definitions and the implemented accounting (`SecClient` counts every
    wire attempt; the ceiling check precedes the limiter and transport; redirect hops and the single
    controlled post-cooldown request each consume one attempt).
16. **Is stop-before-overflow defined correctly at C−1, C, and C+1?** Yes. §9: refuse the attempt
    that would exceed; a complete run may finish exactly at 801; equality with work remaining is
    `stopped_at_ceiling`. §18 requires the C−1/C/C+1 boundary tests. The accepted implementation
    (`PhysicalAttemptCeiling.before_attempt()`) already realizes exactly this semantic, refusing
    before increment and before transport, with the ceiling a read-only property.
17. **Is reaching 801 with unfinished work correctly treated as a failure?** Yes. §9 and §17 item 4:
    `stopped_at_ceiling`, `SEC_REQUEST_CEILING_EXHAUSTED` (registered, `blocks_release=true`), a
    Gate H failure; the ceiling is never raised mid-window; more headroom requires stop, re-plan,
    and a new owner approval — Decision 028 §7 verbatim in substance.
18. **Is contingency completely prohibited?** Yes. §5 ("none — prohibited"), citing Decision 027 §0
    (the withdrawn 10% contingency) and master plan §§15–16; §15 prohibits invented M3.2B counts.
19. **Is the 200-second value correctly described only as a spacing floor?** Yes. §5 gives the exact
    Decision 028 §10 formula (max(0, 801−1) ÷ 4.0 = 200.0 s), labels it "a floor, never a claimed
    maximum duration," and §23 carries the elapsed-time factors as acknowledged, never estimated —
    matching the budget template's "minimum floor, not a maximum or prediction."
20. **Is stale-budget reconfirmation at live authorization sufficient and correctly scoped?** Yes.
    §5's closing rule ("a stale budget is not an approved budget"; exact integers re-confirmed at
    the §8 T5 instrument, restated against the same plan hash) implements master plan M3.2 §5.2, and
    T5's required contents (command, window, plan hash, ceiling, configuration change) make the
    reconfirmation concrete and per-window.

### D. Route and content boundary

21. **Are exactly the seven M3.2A bootstrap route families permitted?** Yes. §6 lists the seven
    families with per-route U×A_reachable, matching master plan M3.2 §12, the registered source
    registry (`m2.2-source-registry/1.0`, nine families total), and the planner's
    `M3_2A_BOOTSTRAP_ROUTES` constant.
22. **Are the two dependent submissions routes excluded from M3.2A?** Yes. §6 and §15 exclude
    `sec_submissions_historical` and `sec_submissions_entity`; §17 item 5 makes a dependent request
    in M3.2A a stop condition; the planner deliberately excludes both routes in code.
23. **Are host, method, path, redirect, and content-type restrictions complete?** Yes. Hosts
    `www.sec.gov`/`data.sec.gov` only; method GET only; per-route exact paths or anchored patterns
    (registry-enforced); expected content types per route (§6 citing master plan M3.2 §12); redirect
    loop/over-depth/out-of-family/identity-path-change all stop (§17 item 5), matching the
    implemented URL-family validation and `MAX_REDIRECT_DEPTH`.
24. **Can any accepted route accidentally reach filing bodies, accession archives, XBRL,
    CompanyFacts, Frames, or a non-SEC source?** No. No registered template can construct
    `/Archives/edgar/data/`; the two permitted `/Archives/edgar/` paths (`daily-index/bulkdata`,
    `full-index/…/company.idx`) are explicitly outside the filing-body marker set; the filing-body
    guard runs before URL validation on every fetch; CompanyFacts is not a registered source, its
    URL helper is unreachable from `SecClient.fetch`, Frames is refused unconditionally by policy
    code; non-SEC hosts fail the origin allowlist; out-of-family redirects stop. The legacy URL
    constructors in `sec/sources.py` that can build archive paths have no call path from the fetch
    surface and are exercised as denied probes in rehearsal A6.
25. **Is the announcement route correctly manifest-resolved and zero-plan in the current M3.2A
    plan?** Yes. §6: `0×6 — manifest-resolved only, never arbitrary-URL; U = 0 lawfully from the
    explicitly empty operator manifest`. The implementation refuses caller-supplied URLs for the
    route, the in-repo manifest is provably empty, the planner counts approved entries in the
    explicitly named operator manifest (empty, per Decision 029 §4.2), and the zero-U route still
    carries its independently tested A_reachable = 6 witness (Decision 029 §4.1 — a zero U never
    waives the witness).
26. **Are permitted metadata fields exact and sufficient?** Yes. §6's field list is the master plan
    M3.2 §12 list verbatim in substance (canonical CIK through operating-calendar evidence), which
    is the already-approved Decision 007/008/010/011/012 family; sufficiency for the M3.3 snapshot
    is inherited from those accepted records.

### E. Storage and catalog architecture

27. **Is the operational-catalog path correct?** Yes, as a specification. `catalogs/
    m3_2a_operational.sqlite3` relative to the external evidence root is a new name (it appears
    nowhere in code — correct, since no implementation exists) and is convention-consistent: every
    M3 command already addresses artifacts by evidence-root-relative paths that are refused if they
    escape the root, and the `m3 recovery-state`/`m3 plan-requests` `--catalog` arguments accept
    exactly such paths.
28. **Can the proposed M3.2A catalog be created and operated at migration chain `0013` without a new
    migration?** Yes. The existing initializer idiom (`CatalogWriter(database_path, lock_directory)`
    → `migrate()` → `seed_reference_data()`) creates a fresh catalog at any caller-supplied path,
    creating parent directories, applying `0001`–`0013` with per-migration provenance rows and
    checksum verification on every later open; migrations contain no filesystem path; nothing
    requires the database inside the repository, and the M3 CLI actively refuses one there. The
    accepted M3.1A rehearsal already exercises exactly this pattern against an isolated root.
    Creating the catalog at the **full** chain is in fact required, not merely permitted: the
    accepted `m3 recovery-state` inspector unconditionally queries `census_recovery_states` and
    `pilot_selection_runs`, and migration verification fails closed on a truncated chain.
29. **Does "M3.2A adds no migration" conflict with any required new table, constraint, projection,
    receipt, recovery, or catalog state?** No. Every required record family already exists at
    `0013`: retrieval observations with full provenance (`census_source_observations`, rebuilt by
    `0008` — content/transport/stored/logical SHA-256, sizes, relative path, storage
    representation, redirect chains, validator metadata, supersession lineage, attempts,
    `retrieved_at_utc`); parser identity/status (`census_parser_runs`); quarterly-index state and
    accounting (`census_index_instances` + events + `census_index_retrieval_accounting`);
    reconciliation (`census_index_reconciliation`); quarantine (`census_quarantined_records`,
    observation outcomes); recovery (`census_recovery_events`, `census_recovery_states`,
    `census_projection_recovery_events`); and archive-member lineage. Receipts are content-named
    files under the evidence root, never database rows (receipt spec §7). JSONL projections are
    derived artifacts with a projection flag and incident tables. Two design consequences are noted,
    neither requiring DDL: the per-observation schema fingerprint is derived from the
    `census_structural_observations` evidence family rather than stored as a column, and the
    cumulative physical-attempt count is carried by the receipt chain rather than a table (finding
    F3). No `0014` is needed or implied.
30. **Is the operational catalog properly isolated below the external evidence root?** Yes.
    `require_external_evidence_root` refuses a root equal to, inside, or an ancestor of the
    checkout, with symlinks resolved on both sides and case-folded comparison; every M3 artifact
    path is refused if it escapes the root; tracked databases are hygiene-forbidden suffixes; the
    reserved in-checkout path is ignored and hygiene-refused. The mode-700/600 regime §20 describes
    is the owner-prepared evidence-root regime validated at Decision 029 §12 step 8 (private
    evidence; not re-verified here), with code-side symlink resistance (`O_NOFOLLOW`, 0o600 lineage
    intents) where code writes.
31. **Are raw-object hashing, immutability, append-only behavior, lineage, and duplicate
    reconciliation implementable as written?** Yes — they are already implemented and accepted at
    the M2.2/M3.1 layer the contract binds to: streaming SHA-256 over decoded entity bytes plus
    stored-byte hashes; `.part`-file staging with fsync; **hard-link promotion that cannot
    overwrite**; deduplication only after the existing object's stored hash verifies; a differing
    body becoming a superseding **new observation** (`REMOTE_CONTENT_CHANGED`) never an overwrite;
    `.lineage.json` recovery intents (`O_CREAT|O_EXCL|O_NOFOLLOW`, 0o600); quarantine that moves
    and preserves, never deletes.
32. **Are content-addressed storage and SQLite transaction boundaries mutually consistent?** Yes.
    The ordering is file-first, then one catalog transaction covering the observation row, its
    reasons, and archive members; a crash between promotion and commit yields an orphan (object
    with lineage intent, no row) — an explicitly modeled state with its own receipt
    `interruption_state`, a rehearsed recovery scenario (A11), verified adoption only via the
    authoritative catalog reconcile path, and the reverse condition (row without object) a hard
    `UNDETERMINED` stop. The audit projection is a third, later step that never makes an
    observation appear unrecorded.

**Section E gate:** no BLOCKER or MAJOR is required — the catalog lawfully supports the contract at
migration chain `0013` without any unapproved schema or migration decision (Concern 2, §8 below).

### F. Completion semantics

33. **Is M3.2A allowed to be called "complete" merely because an unsatisfied request was terminally
    classified?** As drafted, **yes** — §14's first clause accepts "satisfied, reused, or terminally
    classified with a registered reason" as completion-satisfying. This is finding **F1 (MAJOR)**.
34. **Must required metadata actually be obtained for M3.2A to complete successfully?** Not as
    drafted. §5 names 70 "Required quarterly-index instances" and §3 states the acquisitive purpose,
    but no operative clause conditions *successful* completion on the required objects actually
    being present and verified, or on owner adjudication of any absence. **F1.**
35. **Does the current wording distinguish execution termination, terminal classification,
    successful window completion, and Gate H eligibility?** Only partially. The receipt vocabulary
    distinguishes run-level statuses (`complete`/`failed`/`interrupted`/`stopped_at_ceiling`/
    `stopped_by_gate`), and Gate H is a separate later gate; but §14 collapses "every planned
    request reached a terminal disposition" into "M3.2A completes," and Gate H checklist item 3.3
    ("each window completed its whole approved plan") inherits the same ambiguity. **F1.**
36. **Could a widespread 403, block page, or terminal SEC failure technically satisfy the current
    completion wording despite leaving required metadata absent?** A widespread 403/block-page
    cannot — §17 item 7 (second cooldown / block page after the controlled retry) stops the run
    first. But sustained archival `404`s ("recorded as absent evidence" under the accepted response
    policy) and quarantined non-block-page bodies are *terminal classifications that trigger no stop
    condition*, so a window missing many — in the limit, most — required quarterly-index objects
    could technically satisfy §14's wording, be frozen, and proceed toward a second owner approval.
    The bulk-submissions object is the one absence caught structurally (derivation would fail).
    **F1.**
37. **Are blocking drift and missing required objects treated strongly enough?** Blocking drift:
    yes (§17 item 12, §19, incident record, owner ruling). Missing required objects: no — absence
    via lawful terminal classification is not a stop, not an owner-adjudication trigger, and not a
    successful-completion bar as drafted. **F1.**

### G. Recovery and interruption

38. **Is the M3.1 `m3 recovery-state` inspector sufficient for M3.2 recovery, or must M3.2
    implementation extend or specialize it?** The inspector is sufficient *as the read-only
    inspection gate*: it is generic over caller-supplied plan/receipt-chain/catalog/data-root
    inputs, evaluates the eleven safe-resume conditions including per-route worst-case headroom,
    and was designed for the M3.2 shapes. What M3.2 must **add** — per Decision 028 §8's ownership
    split — is the repair-application and resume surface (the runbook's planned `m3 recover`, plus
    `m3 acquire --resume-from`); the inspector itself never repairs. The contract's §12 correctly
    requires SAFE-before-resume; its §16 omission of the repair surface is folded into **F2**.
39. **Are attempt counts correctly carried across resumes?** Yes in design: the receipt chain
    carries `consumed_request_count_carried_forward`; the resume constructor refuses
    `consumed > ceiling`; the inspector sums actual physical attempts across the resolved
    predecessor chain and checks worst-case remainder against remaining headroom (condition 8.8);
    Gate H items 9.4 and the recovery template §§7, 11 reconcile cumulatively. One bounded gap: a
    hard-kill segment that wrote no terminating receipt leaves its in-flight attempts recorded
    nowhere (the ceiling gate is in-memory; committed observations record only their own attempts).
    The fail-closed backstop exists — an unresolvable chain is `UNDETERMINED` and stops — but the
    conservative accounting rule should be made explicit at T2. **F3 (MINOR).**
40. **Are partial files, orphaned records, uncertain commits, and receipt predecessors handled
    deterministically?** Yes. `.part` files are never treated as complete (quarantined or removed
    only as never-promoted temporaries per the template); orphans are adopted only through the
    verified catalog reconcile path or quarantined, never deleted; a row without its object and an
    unresolvable receipt chain are the two hard `UNDETERMINED` triggers; interruption states are a
    fixed five-value enumeration.
41. **Is explicit owner resume-or-new-run authorization sufficient and correctly positioned?** Yes.
    §12 requires it after the terminating receipt and before any resume, with SAFE and
    duplicate-prevention proof as further preconditions — matching master plan §§27–28 and the
    recovery template §10.
42. **Can any resume exceed the original ceiling or silently repeat a substantive write?** No, as
    specified: the same ceiling binds the chain cumulatively (constructor refusal, condition 8.8,
    Gate H 9.1/9.4); the resumed plan excludes committed requests; byte-identical bodies reconcile;
    differing bodies become new observations; §18 requires the resumability-without-duplicate-write
    tests; and a remainder that does not fit the headroom forces stop, re-plan, and a new exact
    approval — never a raised ceiling.

### H. Receipts and evidence

43. **Is one receipt per live command sufficient?** Yes. It matches the accepted receipt spec §2 and
    master plan M3.2 §22; read-only inspection helpers are covered by the command they inspect;
    resumed runs chain receipts; "no receipt" is not an available outcome for a command that ran.
44. **Does receipt v2 contain every required field for attempts, classifications, raw objects,
    drift, interruption, and recovery?** Yes. §10's field summary maps one-to-one onto the
    implemented `m3-execution-receipt/2.0` rule table: plan identity and window; live-only ceiling;
    planned and actual logical/physical counts (per route and total); the six-bucket classification
    totals with no unclassified residual; raw/duplicate/cache/not-modified/quarantined counts;
    drift outcome and count; completion status; registered reason code; interruption state;
    predecessor receipt and carried-forward count on resume.
45. **Are prohibited fields and identity leakage adequately blocked?** Yes. Construction-time
    redaction (the builder never receives a secret), a closed field set, mode-class enforcement, a
    prohibited-content scan over keys and values (credential fragments, email pattern,
    absolute-path pattern), fail-closed rendering/inspection, and the A12 positive contaminated
    control — plus §7's boundary-only identity validation and the evidence-index prohibition table.
46. **Is the evidence-index vocabulary sufficient for M3.2 artifacts?** Almost. Receipts, plans,
    budgets, Gate H checklist, drift incidents, and recovery records all have types and expected-
    coverage rows. The between-windows **frozen bootstrap object-identity list** and **derived
    dependent reference set** — private evidence per master plan M3.2 §§8, 30 — have no artifact
    type and no expected-coverage row. **F4 (MINOR).**
47. **Are same-device backup boundaries sufficient as an interim safeguard?** Yes, as accepted:
    Decision 031 accepted same-device snapshots as accidental-deletion protection only, the
    register's M3-L11 residual note carries it, and §20 restates it verbatim with the required
    window-boundary and governance-recording cadence.
48. **Is the mandatory off-device-backup decision correctly required before live execution?** Yes.
    §20 and §8's T4 preflight both require the owner's recorded off-device-backup decision at T4,
    before any live operation — exactly where the M3-L11 closure note deferred it.
49. **Is `.env` excluded everywhere it must be?** Yes. §7 (ignored; excluded from every snapshot,
    scan, and evidence set) and §20 (excluded from every backup and every scan); `.gitignore` line
    2; the secret scan covers tracked and untracked-not-ignored text; the accepted backup
    verifications recorded `.env` excluded. This review never read the file.

### I. Implementation boundary

50. **Are expected implementation paths narrow enough for later T2 authorization?** Directionally
    yes — every named surface falls inside master plan M3.2 §9's categories, and §16 requires T2 to
    enumerate the exact final set. But the draft's surface list is materially less exact than the
    accepted standard requires of the *contract* (master plan global §16 item 3 "exact authorized
    paths, enumerated"; M3.2 §§9–10 "where the contract names them"; the M3.1 contract §6
    precedent): the acquisition-driver module and every new test file are unnamed, and three of the
    six planned M3.2 commands are omitted (Q52). **F2 (MAJOR).**
51. **Is the "single named network-enable configuration change" sufficiently precise, or must the
    accepted contract name the exact configuration path and field?** It must name it, and the draft
    does not. Runbook step 16 — accepted authority the contract itself binds to — states "The M3.2
    contract names the exact configuration path and the exact command." The command is named
    (`m3 acquire`); the configuration path is not. Concretely, at the reviewed tree the only
    network switch is `configs/project.yaml` key `network.enabled` (default `false`; no environment
    override can reach it; `config.py` is frozen/extra-forbid) — and that key is **not
    command-scoped**: setting it `true` also satisfies the M2.2 `sec census` CLI network gate,
    whose client path carries no attempt-ceiling gate. "Enabling network for `m3 acquire` only"
    (T5) is therefore not realizable by the existing key alone; the accepted contract must name the
    exact change and its scoping mechanism. **F2 (MAJOR); Concern 3.**
52. **Are any required implementation surfaces omitted?** Yes, three CLI surfaces the contract's own
    operator workflow requires: runbook steps 23, 24, and 27/Appendix B plan `m3
    reconcile-requests`, `m3 show-drift`, and `m3 recover` as M3.2 commands, and §21 binds the
    operator to steps 16–28 "exactly as written once the commands exist" — yet §16 names CLI wiring
    only for `m3 acquire`, `--show-scope`, and `m3 derive-dependent-plan`, and §4 cites only those
    three interface contracts. `m3 recover` is load-bearing: Decision 028 §8 assigns repair
    application and resume to M3.2, and §12's recovery flow is unimplementable without a mutating
    repair surface. **F2.**
53. **Are any prohibited paths likely to require modification for lawful implementation?** No. The
    §16 prohibited list was checked against the implementation architecture: the live path needs
    the CLI, a new driver module, the named configuration change, receipt call sites, and bounded
    census-orchestration/index-retrieval edits — none of which is prohibited. Transport, HTTP
    client, rate-limit, response-policy, raw-store, and observation-catalog modules are neither
    expected nor prohibited (T2 may name them); `test_no_network.py` byte-identity is compatible
    (Q54); `config.py`/`configs/` are prohibited *beyond the named change*, which is exactly where
    the named change must be named (Q51).
54. **Is keeping `tests/integration/test_no_network.py` byte-identical compatible with introducing
    one authorized live command?** Yes. The file never enumerates the CLI command set — it asserts
    the socket guard works and that `validate-config`, `show-cohorts`, `--help`, module execution,
    and the invalid-config path succeed with sockets blocked. The suite-wide autouse socket-blocking
    fixture lives in `tests/conftest.py` (not in this file) and will equally cover new offline M3.2
    tests. A new `m3 acquire` command requires no edit to the file, and its assertions continue to
    hold for every non-authorized path.
55. **Does the future T2 packet need to subdivide implementation into multiple stages rather than
    one commit?** No requirement found. The one-implementation-commit default (§22; master plan
    M3.2 §32) is workable for the M3.2 surface as scoped; an intermediate checkpoint already has a
    lawful route (contract amendment plus separate owner authorization) if T2 design work shows the
    diff would otherwise be unreviewable. No correction needed.

### J. Validation and review

56. **Are the minimum test categories complete?** Yes — §18 contains every master plan M3.2 §24
    category and adds more (ceiling-argument equality refusals, `--show-scope` zero-request
    printing, 304 handling, retained-unknown-field logging, identity non-contamination, recovery
    SAFE/UNSAFE/UNDETERMINED integration, the `[sec]` extra with the transport test running, the
    no-Git/clock/identity/machine-path/network/real-response test constraints).
57. **Does the contract require non-vacuous positive controls for every critical refusal
    boundary?** Substantially. Refusal boundaries are framed as refusal tests (allowlist/denylist,
    `--live` explicitness, plan-hash binding, ceiling equality, blocking-drift refusal, C+1), and
    the prohibited-field scan carries an explicit positive contaminated control. An explicit
    blanket "one positive control per refusal boundary" sentence would strengthen §18 —
    **F7 (OPTIMIZATION)**, nonblocking.
58. **Is the full T3 validation sequence sufficient?** Yes. §19 carries the master plan §25 fixed
    sequence in order, plus migration-provenance, receipt validation, request-plan validation, and
    the ceiling/stop-before-overflow validations.
59. **Is the fresh non-author implementation review correctly required before live operation?**
    Yes. §19's T3 clause requires a focused independent review by a session that authored none of
    the M3.2 work, with a durable artifact under `Docs/m3/reviews/`, before any live operation —
    matching §8's T3 row and the project's review discipline.
60. **Are post-operation validation and final independent acceptance review correctly separated?**
    Yes. §19 separates per-window/Gate H post-operation validation from the independent M3.2
    acceptance review (master plan M3.2 §26) by a session that ran none of the acquisition; §22
    places the acceptance commit and the tag after that review under separate owner authorization.

### K. Stop conditions and negative authority

61. **Are all consequential mismatches fail-closed?** Yes. §17's twenty-one conditions close every
    consequential mismatch surfaced by this review (identity, enablement, hashes, ceiling, routes,
    classification, cooldown, counters, receipts, raw-object integrity, immutable-identity change,
    drift/plan expansion, evidence-root/symlink, disk/part/orphan/recovery, D023-O1, filing-body,
    clock/as-of, Git baseline, review findings, catalog checks, M3.2B preconditions), ending with
    the no-workaround/no-widening sentence (CLAUDE.md rule 12).
62. **Does any stop condition lack an associated observable or reason code?** No gap that requires
    correction. Every runtime stop maps to a registered reason code (`SEC_REQUEST_CEILING_
    EXHAUSTED`, `SEC_ACQUISITION_INTERRUPTED`, `SEC_BLOCK_PAGE`, `SEC_RETRIES_EXHAUSTED`, redirect
    and schema codes, `RAW_*`, `INDEX_*`, source-mutation codes — all present in the registry) or
    to a fail-closed refusal with exit code 4 and a validated receipt `completion_status`
    (`stopped_by_gate`/`failed`); pre-run refusals lawfully precede any receipt because no live
    command ran. Receipt validation refuses unregistered codes.
63. **Are disk-space, symlink, Git-baseline, identity, route, hash, ceiling, recovery, and
    prohibited-content failures covered?** Yes — §17 items 14, 13, 18, 1, 5, 3/10, 4, 12/14, and 16
    respectively.
64. **Can any default, coercion, fallback, or manual substitution widen scope?** No. `--live` has no
    default; the ceiling is supplied explicitly and refused on inequality (and the implemented gate
    takes a required argument with no default and a read-only ceiling property); the plan is
    consumed, never re-derived; drift is never resolved by defaulting or coercing; no environment
    variable can enable the network; §17's closing sentence forbids every workaround class; §24
    withholds every authority not separately granted.
65. **Does the contract clearly prohibit live SEC access until a separate, exact T5 owner
    instrument?** Yes. Header, §8 (T5's required exact contents; network disabled outside
    authorized windows), §17 item 2 (enablement before the T5 instrument exists is a stop
    condition), §24, and §25.

## 8. The four owner-concern determinations

**Concern 1 — successful-completion semantics: CONFIRMED as finding F1 (MAJOR; correction required
before acceptance).** §14's first clause ("satisfied, reused, or terminally classified with a
registered reason") permits a window to be declared complete when required metadata was not
acquired. The worst SEC-side failure modes are stopped earlier (block page/second cooldown, §17
item 7; unclassifiable responses, item 6; blocking drift, item 12), and the bulk-submissions object
specifically cannot be absent without the between-windows derivation failing loudly — but archival
`404` absent-evidence classifications and quarantined non-block-page bodies are lawful terminal
classifications that trigger no stop condition, so up to all 70 required quarterly-index instances
(and the ticker/SIC/calendar objects) could be absent while §14's completion wording is satisfied,
the freeze proceeds, and the owner is asked for a second approval. Gate H does not reliably catch
it: the checklist is a boundary-compliance gate, its item 3.3 ("completed its whole approved plan")
inherits the same ambiguity, and its raw-store reconciliation (6.1) reconciles against a maximum,
not a required-presence list; the receipt vocabulary likewise allows `completion_status =
"complete"` with a non-zero `fail` bucket. Recommended exact corrective language is given under F1
in §9. **Not** a BLOCKER: the run never exceeds its authority (the defect is false *success*
labeling, not unsafe acquisition), every absence is visible in classification totals and receipts,
and the fix is bounded contract language.

**Concern 2 — migration and catalog sufficiency: PASSES.** Existing schema and migration authority
support all required M3.2A catalog, projection, recovery, and provenance records at chain `0013`
with no new migration and no unapproved schema decision (Q28–Q32, with the evidence enumerated
there). Three design notes, none requiring DDL or a decision: the schema fingerprint is derived
from the structural-evidence family rather than stored per observation; the cumulative
physical-attempt count lives in the receipt chain, not a table (F3's conservative-accounting rule
belongs in the T2 packet); and the catalog must be created at the **full** chain because the
accepted recovery inspector and migration verification require it — which is exactly what the
contract specifies.

**Concern 3 — exact network-enable change: CONFIRMED as part of finding F2 (MAJOR; correction
required before acceptance).** The contract is not sufficiently bounded as drafted. Accepted
authority places the naming obligation on the contract itself (runbook step 16: "The M3.2 contract
names the exact configuration path and the exact command"; master plan M3.2 §10: "`configs/` beyond
the explicitly authorized network-enable change **the contract names**"), and the draft's own §16
prohibition ("`config.py` beyond the one named network-enable change") is self-referentially
indeterminate while nothing is named. Additionally, the only existing switch
(`configs/project.yaml` key `network.enabled`) is not command-scoped — enabling it also satisfies
the M2.2 `sec census` network gate, a path with no attempt-ceiling gate — so the accepted contract
must name both the exact file/key and the scoping mechanism that makes enablement effective for
`m3 acquire` only. Recommended exact corrective language is given under F2 in §9.

**Concern 4 — M3.2B unresolved-marker terminology: the marker is CORRECT as used; nonblocking
(F6, MINOR).** `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` remains the accepted project-wide
sentinel for a deliberately unresolved count: Decision 027 §§15–16 define it; the accepted master
plan applies it to the M3.2B counts verbatim ("Both M3.2B counts are `EXACT_COUNT_RESOLVED_BY_
GATE_F_ZERO_REQUEST_PLAN` until M3.2A completes," M3.1 §15); and Decision 030 Ruling C confirmed
its nonblocking semantics for the three response-outcome expectations. The contract's §5 and §15
usages therefore follow accepted vocabulary exactly, and both are accompanied by the correct
resolution mechanics (derived by the future zero-request `m3 derive-dependent-plan` run over frozen
objects; a separate exact owner approval; no integer invented). The Gate-F-specific wording is a
legacy of the marker's origin and is mildly misleading in the M3.2B and response-outcome contexts —
but renaming it is a decision-level vocabulary change across accepted records, not a contract edit.
Recommendation: keep the marker; optionally add a one-line gloss at acceptance; a phase-neutral
rename (e.g., `EXACT_COUNT_RESOLVED_BY_ZERO_REQUEST_PLAN`) would require its own bounded decision
and is not required.

## 9. Findings

| # | Severity | Finding | Corrective action |
|---|---|---|---|
| F1 | **MAJOR** | §14 completion wording permits false success: terminal classification substitutes for acquisition; no required-object completeness gate before the freeze, the second approval, or Gate H eligibility | Required before acceptance — see below |
| F2 | **MAJOR** | §16 does not enumerate the exact authorized boundary: the network-enable configuration change is unnamed (and the existing switch is not command-scoped); the driver module and test files are unnamed; three of the six planned Appendix-B M3.2 commands (`m3 reconcile-requests`, `m3 show-drift`, `m3 recover`) are omitted although §21 binds the operator to the runbook steps that use them | Required before acceptance — see below |
| F3 | MINOR | Crash-segment attempt accounting: a hard-kill segment that wrote no terminating receipt leaves its in-flight physical attempts recorded nowhere; the fail-closed `UNDETERMINED` backstop exists, but the conservative accounting rule (charge the interrupted in-flight request at its full per-route `A_reachable`, or stop) is unstated | Recommended at T2; may also be added to §12 at acceptance |
| F4 | MINOR | The evidence-index artifact-type vocabulary and §5 expected-coverage rows omit the between-windows freeze artifacts (frozen bootstrap object-identity list; derived dependent reference set), which master plan M3.2 §§8, 30 make private evidence | Recommended: extend the index vocabulary (authorized edit) or state in the contract which existing artifact carries them |
| F5 | MINOR | Stale navigation text: `Milestones/contracts/README.md` retains pre-acceptance prose ("M3.1 implementation … NOT accepted"; "the M3.2A budget and ceiling are unapproved"; "Two active corrections block Gate F"; an index bullet still reading `IMPLEMENTATION_AUTHORIZATION: YES` with an active blocker) contradicting its own updated index paragraphs; `m3_1.md`'s "Current state (2026-08-03)" block is likewise frozen pre-acceptance. All contradictions are neutralized by the completed-contract rule, STATUS, and the registry, and none grants authority | Recommended: a bounded owner-authorized navigation cleanup at or after acceptance |
| F6 | MINOR | The `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` marker's Gate-F-specific name is misleading in its M3.2B and response-outcome uses, though the usage follows accepted vocabulary exactly (Concern 4) | Nonblocking; optional gloss at acceptance; rename only via its own decision |
| F7 | OPTIMIZATION | §18 could state a blanket non-vacuous positive-control requirement for every critical refusal boundary (one exists explicitly only for the prohibited-field scan); §19 could name the exact nonchange-proof command over the §16 prohibited set | Optional wording strengthening |

**Zero BLOCKER findings.** Both MAJOR findings are bounded contract-language corrections; neither
makes the proposed T1–T6 boundary, the per-window separation, the negative-authority set, or the
stop-condition regime unsound.

### F1 — required correction (recommended exact language; this review edits nothing)

Amend §14's first sentence to distinguish termination from success and to add a required-object
gate, for example:

> M3.2A **terminates** when every planned logical request has reached a terminal disposition.
> M3.2A **completes successfully** only when, additionally: **every required object is present in
> the raw store, hash-verified, and fully provenanced** — the bulk-submissions object, both ticker
> files, the SIC list, the calendar-year filing-calendar page, every approved announcement-manifest
> entry (zero in the approved plan), and all 70 required quarterly-index instances; any planned
> request whose terminal disposition left its object absent (an absent-evidence `404`, a
> quarantined body, or any terminal failure) is enumerated in the window's receipt and
> **expressly adjudicated by the owner before the between-windows freeze and before any M3.2B
> budget approval**; and the remaining §14 conditions hold unchanged. A window that terminates with
> any required object absent and unadjudicated is **not** successfully complete, is not eligible
> for the freeze/derivation step, and is not Gate H-eligible.

At acceptance, a one-line gloss that Gate H checklist item 3.3's "completed its whole approved
plan" means this successful-completion standard would close the inherited ambiguity without
editing the frozen template.

### F2 — required correction (recommended exact language; this review edits nothing)

1. **Name the network-enable change.** State in §16 (and correspondingly in §8's T5 row) the exact
   configuration change — as of the reviewed tree, `configs/project.yaml` key `network.enabled`
   (`false` → `true`) is the only existing switch and no environment override can reach it — and
   the scoping mechanism that makes enablement effective for `m3 acquire` only. Either (a) name
   that key as the single change and require, within the same named-change boundary, that while it
   is enabled during an M3.2 window every other network-capable command (`sec census`,
   `sec ingest-pilot`) refuses; or (b) name a new acquire-scoped configuration field as the single
   change. Whichever form the owner selects must appear in the accepted contract text (runbook step
   16; master plan M3.2 §10).
2. **Enumerate the exact expected path set** to the M3.1 §6 standard: name the acquisition-driver
   module file and each new test file, and extend the CLI-wiring list to the full planned
   Appendix-B M3.2 surface — `m3 acquire` (including `--show-scope` and `--resume-from`),
   `m3 derive-dependent-plan`, `m3 reconcile-requests`, `m3 show-drift`, and `m3 recover` — or
   state expressly which of the six are absorbed into other surfaces or deferred, and where their
   §21/§12 duties land. T2 then confirms the exact final set, as §16 already provides.

## 10. Residual limitations

- All 35 open limitations-register entries remain active and are correctly inherited by §23
  (5 × D020, 10 × D021, D022-L1, 4 × D023-O, 2 × D024, 3 × D026, 10 open M3 entries — count
  verified against the register). D023-O1 remains the sole unresolved owner-ruling condition,
  latent and stop-and-refer.
- Same-device-only backups persist until the owner's T4 off-device decision (§20; M3-L11 residual
  note; accepted Decision 031 MINOR finding 2).
- The three response-outcome expectations remain deliberately unresolved under Decision 030 Ruling
  C, resolved only by the actual controlled acquisition.
- Elapsed-time factors above the 200.0 s spacing floor remain acknowledged and unestimated; SEC-side
  variability (drift, blocks, calendar events) fails closed under §17.
- This review verified private-evidence bindings through the accepted public records (Decisions
  030/031, the evidence index, STATUS) and did not read private evidence content; the mode-700/600
  evidence-root regime is owner-prepared state validated at Decision 029 §12 step 8 and was not
  re-verified here.
- F3's crash-segment accounting rule and F4's index vocabulary remain open recommendations for T2
  and the acceptance pass respectively.

## 11. Explicit implementation and live-SEC boundary

This review changes no byte of the contract, closes no finding, accepts nothing, and authorizes
nothing. After this review: the M3.2 contract remains `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`
and is **not accepted**; M3.2 implementation authorization remains **`NO`** (T2 has not occurred and
requires all five Decision 024 §8 conditions after T1); network and CompanyFacts remain **disabled**;
**no live SEC access, no SEC contact, no connectivity test, no controlled acquisition, no
operational-catalog creation or population, and no use of the M3.2A request ceiling is authorized
or occurred**; the `m3.1-complete` tag is unchanged and no new tag exists; nothing was pushed by
this review's authorized commit instruction beyond what the owner separately directs. The next
decision belongs to the owner: accept, correct, or decline the draft (T1), for which this review
recommends correction first (§12).

## 12. Verdict

Zero BLOCKER findings; two MAJOR findings (F1 completion semantics; F2 boundary exactness including
the unnamed network-enable change), both bounded contract-language corrections; four MINOR; one
OPTIMIZATION. The draft is fundamentally sound — it implements the accepted master plan M3.2 §§1–36
and global §16 faithfully in every other material respect, carries exact and verified frozen
inputs, preserves the six-transition owner gate ladder with airtight negative authority, and
contains no catalog/migration contradiction — but the owner's own PASS bar (no false-success
completion semantics; an unambiguous implementation boundary) is not met until F1 and F2 are
corrected.

```text
M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS
```

**Recommended owner disposition:** correct §14 and §16 per F1/F2 (with the F3–F6 recommendations at
the owner's option), then either order a focused re-review of the corrected draft or proceed
directly to the T1 acceptance decision on the corrected text, as the owner directs. Do not accept
or implement the contract, enable network access, or perform live SEC acquisition on the basis of
this review.

## 13. Reviewer signature

Independent contract review performed and recorded by Claude Code session
`session_013AyJ5c15m329AebGZQr7ce` (Claude Fable 5, maximum effort), 2026-08-04 UTC, at reviewed
commit `536856325f6a655416d48276c5b93848cab388e8`, under the owner's 2026-08-03 independent-review
authorization. Non-authorship attested in §1. This artifact records a review verdict only; every
acceptance, authorization, and enablement decision remains the owner's.
