# Independent Rereview of the Corrected M3.2 Contract — at 3bf9987dd72e1531da2f678fbbef735f37aefcf4

**Artifact:**
`Docs/m3/reviews/m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md`
**Required by:** accepted [Decision 032](../../Docs/Decisions/decision_032_m3_2_contract_corrections.md)
§§6 and 10 and accepted
[Decision 033](../../Docs/Decisions/decision_033_m3_2_correction_pass_adjudication.md) §10
(`NEXT_AUTHORIZED_ACTION: FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT`), under
the owner's explicit rereview instruction of 2026-08-04, which is this session's authorizing input.
**Review type:** fresh, independent, adversarial rereview of the corrected
`Milestones/contracts/m3_2.md` as committed, deciding whether it may now be accepted unchanged. It
is **not** owner acceptance, **not** implementation authorization, and it authorizes nothing. No
verdict of this review accepts the contract, and this review edits no byte of it.

---

## 1. Independence and no-subagent attestation

- **Reviewer session:** `session_013AyJ5c15m329AebGZQr7ce`
  (`https://claude.ai/code/session_013AyJ5c15m329AebGZQr7ce`), Claude Code CLI, macOS
  (Darwin 25.5.0). **Container-continuity disclosure, made explicit for the owner:** this is the
  persistent CLI conversation container's identifier, and the durable repository record shows the
  same identifier on two earlier, separately cleared review epochs — the accepted independent M3.1
  step-14 acceptance review and the preserved prior M3.2 contract review. The repository's
  owner-accepted convention, applied in both of those artifacts and ratified by Decisions 031 and
  032, treats a **cleared conversation epoch** as the independence unit: an epoch beginning from a
  fresh context clear, with every boundary commit predating it, is a fresh non-author session.
  Decision 032 §6 faulted the prior review epoch **only** for its use of two fact-gathering
  subagents — the defect this rereview exists to cure — and for no other property of its execution.
- **This epoch is genuinely fresh.** It began from a `/clear` context clear with the owner's
  rereview instruction as its **first and only** input; no conversational context, working state,
  clone, note, or persistent memory crossed the clear (the session memory index is empty). Every
  commit under review — the draft `5368563…`, the prior review `3fbaa12…`, the correction commit
  `96dea2b…`, and the cleanup commit `3bf9987…` — predates this epoch.
- **Non-authorship attestation.** This session (this cleared epoch) authored **none of**: the
  original M3.2 contract draft; the prior M3.2 contract review; Decision 032; the corrected
  contract text; Decision 033; any related status, registry, or navigation update; or the M3.1
  implementation or evidence used as contract inputs. It wrote nothing in this repository before
  this artifact. No verdict, finding, or substantive conclusion was inherited: the prior review
  artifact was used only to identify the findings F1–F7, and **every conclusion below was
  independently re-verified by this session against the committed tree, the accepted decisions,
  the templates, and the code.**
- **No-subagent attestation.** **One active session only.** This rereview invoked **no subagents,
  no delegated agents, no background agents, no parallel workflows, no Git worktrees, and no other
  Claude conversation.** Dynamic Workflows remain enabled in the environment and were **not used**.
  All reading, analysis, validation, and the verdict in §11 were performed **directly by this
  session**.
- **Model and settings:** Claude Fable 5 (`claude-fable-5`, stated by the session environment),
  maximum effort, selected by the owner's task instruction. Master plan §13 names "Opus Max" for
  reviews; the owner's explicit selection controls (owner rulings precede the plan in the accepted
  hierarchy) — the same adjudication the accepted §17, step-14, and prior contract-review artifacts
  recorded.
- **UTC review date:** 2026-08-04.
- `.env` is ignored (`.gitignore` line 2), present locally, and was **never read, printed, or
  copied** by this review. No private evidence content was read; private-evidence bindings were
  verified through the accepted public records.

## 2. Reviewed baseline and corrected-contract identity

| Item | Value | Expected | Match |
|---|---|---|---|
| Branch | `main` | `main` | yes |
| Reviewed commit (`HEAD`) | `3bf9987dd72e1531da2f678fbbef735f37aefcf4` ("Clean up Decision 032 governance record") | same | yes |
| `HEAD` tree | `69e84ab8eb3d5e8c1f1be3844c04113a1ce0fe89` | — | — |
| Parent | `96dea2b50b7e87243aad29032946ef8447033eb9` ("Correct M3.2 contract and record Decision 032") | same | yes |
| `origin/main` | `3bf9987d…`; `HEAD == origin/main` | same | yes |
| Working tree at review start | clean; nothing staged; no non-ignored untracked path; `git diff --check` and `git diff --cached --check` clean | clean | yes |
| Tags at `HEAD` | none | none | yes |
| `m3.1-complete` tag object | `638a02b780d912ff7b37a2f523277b9d451a015a` | same | yes |
| `m3.1-complete` peeled target | `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4` | same | yes |
| **Corrected-contract SHA-256** | `75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3` (identical in the primary checkout and the independent clone) | same | yes |
| Contract status line | `DRAFT — CORRECTED (DECISION 032) — PENDING INDEPENDENT REREVIEW AND OWNER ACCEPTANCE` | same | yes |
| `IMPLEMENTATION_AUTHORIZATION` | `NO` | `NO` | yes |
| `NETWORK_AUTHORIZATION` | `NONE` (draft authorizes zero network access) | `NONE` | yes |
| Prior review artifact SHA-256 | `fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57` — preserved unchanged | same | yes |
| Frozen implementation | `git diff 970e050d…..HEAD -- src tests` **empty**; every change since the frozen SHA is confined to `Docs/Decisions/`, `Docs/m3/`, and `Milestones/` | unchanged | yes |
| Decision numbering | directory and registry both end at **Decision 033**; rows 032 and 033 match the decision files | consistent | yes |

**Baseline-state confirmations.** No M3.2 implementation exists: the `m3` CLI group carries exactly
the six accepted M3.1 subcommands (`rehearse`, `rehearse-report`, `plan-requests`, `show-budget`,
`show-receipt`, `recovery-state`); `src/disclosure_drift/m3/acquisition.py` does not exist; none of
the six planned M3.2 command strings resolves to an implementation (the only `m3 acquire`
occurrences under `src`/`tests` are receipt-fixture field values); the three planned new test files
do not exist. No operational catalog exists (no tracked or untracked `*.sqlite3`, `*.part`, or
`catalogs/` path anywhere in the checkout). No live SEC request artifact exists; every accepted
receipt is a zero-network rehearsal or dry-run receipt per the accepted governance records.
`network.m3_acquire_enabled` appears **only** in governance text (Decision 032, the registry,
STATUS, the contract) and in **no executable byte** — and `config.py`'s `_Section` base is
`extra="forbid"`, so the key cannot even be smuggled into a local configuration before the lawful
T2 schema addition. `configs/` (exact name, plural) exists and `configs/project.yaml` carries
`network.enabled: false`.

**Public evidence identities re-verified by this session:** the sanitized §17 review re-hashes to
`9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3` and the step-14 acceptance
review to `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, both matching
Decisions 030/031 and contract §2. The contract's §5 identities match accepted Decision 031 §4
verbatim (plan `19be7bdc…`, budget `2d453e0b…`, checklist `34fc0567…`, token record `b06ae373…`,
ceiling **801** bound to the plan hash) and the evidence-index rows `EV-M31B-001`–`EV-M31B-006`.

## 3. Independent-checkout provenance

A fresh disposable independent clone was created after task start, outside the primary repository
and outside the external evidence root, in a session-scoped temporary working area whose
machine-local absolute path is not recorded here (repository hygiene; Decision 030 Ruling A
precedent). It was cloned from the local primary checkout with no hard links, resolved to commit
`3bf9987dd72e1531da2f678fbbef735f37aefcf4` with tree `69e84ab8eb3d5e8c1f1be3844c04113a1ce0fe89`,
was clean with no untracked path, contained **no `.env`** and **no private evidence artifact**, and
reused no other checkout. The corrected contract hashed identically
(`75e7e5a1…`) in the clone and the primary checkout, proving the reviewed bytes are the committed
bytes. The clone was deleted after this artifact was committed.

## 4. Authority reviewed — directly by this session

Precedence applied: explicit owner instruments; accepted numbered decisions; accepted contracts;
the accepted master plan; runbook, specifications, and templates; limitations, status, review, and
evidence records; implementation; prior completion reports and the prior review as claims only.

Read directly: `CLAUDE.md`; `Milestones/STATUS.md` (head, current stage, next authorized action,
machine-readable markers); `Milestones/contracts/m3_2.md` (full); `Milestones/contracts/m3_1.md`
(§6 exact-path standard and structure); `Milestones/contracts/README.md` (full);
`Milestones/milestone_03_master_plan.md` (phase M3.2 §§1–36 in full; global §§5–8, 16, 17; M3.1
§15's M3.2B-sentinel rule); Decisions 032 and 033 (full); Decision 031 §§1–9 (verbatim instrument
and bindings); Decision 030 (Rulings A–E); Decision 029 (§§3, 4, 8, 12); Decision 028 (§§7, 8);
Decision 027 (§0 corrections; §20); Decision 026 (§21); Decision 024 (§8 and headings); Decision
023 (§7); Decision 013 §1; `Docs/Decisions/decision_registry.md` (full — rows 001–033 and quick
lookup); `Docs/decision_index.md` (restoration check and the stale sentence);
`Docs/m3/operator_runbook.md` (steps 16–27; Appendices A–C); `Docs/m3/execution_receipt_spec.md`
(field tables §§4–5, completion/recovery fields, validation rules);
`Docs/m3/limitations_register.md` (summary totals; M3-L12 closure entry; D023-O1; closing
section); `Docs/m3/templates/gate_h_checklist.md` (items 3.1–3.7, 13.x, 14.1–14.3);
`Docs/m3/templates/evidence_index.md` (live instance — vocabulary, coverage, rows);
`Docs/m3/templates/interrupted_run_recovery.md` (ceiling-accounting fields; condition 8.8);
`Docs/leakage_register.md` (L-table); the prior M3.2 contract review artifact (full, as the
findings source); and the accepted M3.1 step-14 and §17 review artifacts (attestation and identity
sections, plus SHA-256 re-verification).

Code inspected directly (read-only): `config.py` (`_Section` strictness; `NetworkSection`;
`DISCLOSURE_DRIFT_CONFIG` at `config.py:97`; the M2.2 network-requirement error path);
`configs/project.yaml`; `cli.py` (the `m3` subcommand set; the `network_commands =
{"census", "ingest-pilot"}` gate refusing when `config.network.enabled` is false);
`sec/request_ceiling.py` (`PhysicalAttemptCeiling` — atomic `before_attempt` refusal, read-only
ceiling, resume constructor refusing `consumed > ceiling`); `sec/urls.py` and `sec/http_client.py`
(the filing-body guard on the fetch path); `sec/companyfacts_policy.py` (Frames always refused);
`sec/raw_store.py` (`.part` staging; atomic no-overwrite hard-link promotion;
`O_CREAT|O_EXCL` lineage intents); `m3/recovery.py` (SAFE/UNSAFE/UNDETERMINED; full-chain catalog
queries); `storage/catalog.py` (`CatalogWriter.migrate()` / `seed_reference_data()`);
`storage/migrations/` (contiguous `0001`–`0013`; no `0014`); presence of
`tests/integration/test_no_network.py`, `tests/unit/test_httpx_transport.py`, and
`tests/unit/test_request_ceiling.py`.

## 5. Validation commands and results

| Command / check | Result |
|---|---|
| `make context` | Green. Branch `main`; HEAD `3bf9987d…` == `origin/main`; clean tree; latest migration `0013_m23_manifest_lifecycle_guards.sql` (13 migrations); latest decision `decision_033_m3_2_correction_pass_adjudication.md`; active contract `Milestones/contracts/m3_2.md` with status `DRAFT — CORRECTED (DECISION 032) — PENDING INDEPENDENT REREVIEW AND OWNER ACCEPTANCE`; next authorized action resolves to `FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT` |
| `make secrets` | Passed: 267 textual files scanned, 0 findings |
| `make hygiene` | Passed: 269 paths checked, 0 findings (re-run green after this artifact was written) |
| `git diff --check` / `git diff --cached --check` | Clean |
| Next-action marker | The exact string `NEXT_AUTHORIZED_ACTION: FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT` occurs exactly once in `Milestones/STATUS.md`, and the ledger's dependent prose, `CURRENT_STAGE`, `ACTIVE_BLOCKER`, and `IMPLEMENTATION_AUTHORIZATION: NO` markers agree with it |
| Registry consistency | Registry and directory both end at Decision 033; the 032 and 033 rows and quick-lookup entries match the decision files; every decision the contract cites carries the status the contract assumes |
| Tag verification | `m3.1-complete` is the annotated tag object `638a02b7…`, peeled to `4cd2c72…`, matching Decision 031, STATUS, and contract §2 |
| Protected-byte proof | `git diff 970e050d… HEAD -- src tests` empty; the full `--name-status` delta since the frozen SHA touches only `Docs/Decisions/`, `Docs/m3/`, and `Milestones/` |
| Leakage scan of this artifact | No SEC identity, credential, `.env` content, private absolute path, private-evidence content, or response body appears here |

Not run, per the rereview instruction: connectivity tests, SEC requests, acquisition, request
planning, budget display, rehearsal, token recording, catalog creation. The full pytest suite was
not rerun: implementation and test bytes are byte-identical to the tree the accepted step-14 review
validated in full (2739 passed, 1 pre-existing skip), and no executable claim in this rereview
depends on a result that proof does not already cover.

## 6. F1–F7 correction matrix

Every Decision 032 §5 correction was independently verified in the corrected contract text and,
where it makes claims about the repository, against the repository itself.

| # | Directed correction (Decision 032 §5) | Where applied | Independently verified | Status |
|---|---|---|---|---|
| F1 | Termination vs successful completion; required-object gate; enumerated, owner-adjudicated absences; `completed_with_absences` ineligible for freeze/Gate H; Gate H item 3.3 read under the standard, template unedited | §14; §15 first bullet; §17 items 4, 19, 21 | Yes — see F1 analysis below | **CORRECTED** |
| F2 (boundary) | Named command-scoped network-enable change: `network.m3_acquire_enabled`, default `false`, in `configs/project.yaml`, mirrored one-field in `NetworkSection`; read only by `m3 acquire --live`; `network.enabled` stays `false`; window-local config via `DISCLOSURE_DRIFT_CONFIG`; tracked default never `true` | §16 first bullet; §8 T5 row; §9 | Yes — see F2 analysis below | **CORRECTED** |
| F2 (surface) | Complete expected implementation and test surface, all six planned Appendix-B commands dispositioned | §16 implementation and test bullets; §4 (runbook citation) | Yes — matches runbook Appendix B exactly; every named existing path exists; every named new path is absent, as required | **CORRECTED** |
| F3 | Conservative crash-segment accounting: charge the in-flight request at full per-route `A_reachable`; else `UNDETERMINED`; no resume | §12 | Yes — and consistent with receipt-chain carry-forward fields, the resume-constructor refusal in `request_ceiling.py`, and recovery condition 8.8 | **CORRECTED** |
| F4 | Evidence-index vocabulary gate before public indexing of the between-windows freeze artifacts | §20 | Yes — the live index vocabulary (11 artifact types) contains no type for the frozen bootstrap object-identity list or the derived dependent reference set, so the gate is real and necessary | **CORRECTED (gate recorded; vocabulary item deliberately open)** |
| F5 | Stale current-state prose corrected in the authorized navigation documents | `Milestones/contracts/README.md` | Yes — the README's pre-acceptance blocks and the `m3_1.md`/`m3_2.md` index bullets now state the completed/corrected-draft state accurately. `Docs/decision_index.md` was **restored, not corrected** — see §9 | **CORRECTED as adjudicated by Decision 033** |
| F6 | `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` retained unrenamed, with the historical-name gloss | §5 (expectations row); §15 | Yes — exact string present in both places, glossed, never renamed; matches Decision 027 §§15–16, master plan M3.1 §15, Decision 030 Ruling C | **CORRECTED** |
| F7 | Blanket non-vacuous positive-control requirement; exact nonchange proof named | §18 (closing requirement with enumerated violating-input examples); §19 (`git diff --exit-code <T2-baseline> -- <every §16-prohibited path>` plus the S5/S6 identity non-contamination suite proof) | Yes — reproducible as stated; parameterized only by the T2 baseline, which is fixed at T2 | **CORRECTED** |

### F1 — completion-semantics verification (finding F1, MAJOR — fully corrected)

The corrected §14, with §15 and §17, now distinguishes all seven required states, each with its own
operative condition: (1) **execution termination** — every planned logical request at a terminal
disposition and the terminating receipt validated; (2) **terminal response classification** — a
registered-reason disposition that, by the express sentence "Termination alone is never success,"
**never** satisfies a required request by itself; (3) **per-request satisfaction** — a validated
new or reused object; (4) **successful window completion** — additionally, **every required
object** (the bulk-submissions object, both ticker files, the SIC list, the calendar-year
filing-calendar page, every approved announcement-manifest entry — zero in the approved plan — and
all 70 required quarterly-index instances: 1+2+1+1+0+70 = the 75 planned logical requests exactly)
present in the raw store, hash-verified, and fully provenanced, with actual counts reconciled,
zero overflow, zero prohibited-route attempts, zero unresolved blocking drift, network disabled
again, and receipts validated; (5) **freeze eligibility** and (6) **M3.2B-planning eligibility** —
§14 makes a window with any unadjudicated required-object absence (`completed_with_absences`)
ineligible for the freeze/derivation step, and §15 forbids planning, budgeting, approving, or
beginning M3.2B before M3.2A completes and the objects are frozen; (7) **Gate H eligibility** —
the same §14 bar, with checklist item 3.3 expressly read under the successful-completion standard
and the frozen template unedited.

Adversarial checks, each confirmed: an absent-evidence `404`, a quarantined body, and any terminal
failure are expressly named as absences that must be **enumerated in the window's receipt and
expressly adjudicated by the owner before the between-windows freeze and before any M3.2B budget
approval** — adjudication is express, never silent, so absence is never silently transformed into
success; an incomplete terminal run cannot be frozen as the successful M3.2A input, cannot enable
M3.2B planning, and cannot reach Gate H; widespread non-success cannot create false success — a
block page or second cooldown stops the run first (§17 item 7), an unclassifiable response stops it
(item 6), blocking drift stops it (item 12), and lawful terminal absences bar successful completion
under §14. **No remaining false-success path was found.** One wording-level observation about where
the item-level enumeration physically lives is recorded as MINOR finding R1 (§8) — it does not
reopen any false-success path.

### F2 — network-boundary verification (finding F2, MAJOR — fully corrected)

The contract now names, exactly: the configuration file `configs/project.yaml` (the directory is
`configs/`, verified); the global network kill-switch field `network.enabled` (the only existing
switch, default `false`, verified in the file and in `NetworkSection`); the new command-scoped key
`network.m3_acquire_enabled` with default `false`, mirrored by the one-field addition
`m3_acquire_enabled: bool = False` to `NetworkSection`; the single consuming command
`m3 acquire --live`; and the delivery mechanism (the owner-authorized window-local configuration
supplied via the real `DISCLOSURE_DRIFT_CONFIG` environment variable, the tracked default never
committed `true`, restored or discarded at window end, verified by Gate H items 14.1–14.3, which
exist in the frozen template).

**The complete conjunction before transport construction** is exact: the acquire-scoped
configuration permission **and** the explicit `--live` flag with no default **and** `--plan`
matching hash `19be7bdc…` **and** `--window M3.2A` **and** `--ceiling 801` exactly equal to the
approved integer (each mismatch refusing before any transport construction, §9) **and** an accepted
contract (T1) **and** accepted implementation (T3) **and** the exact per-operation T5 owner
instrument naming the command invocation, window, plan hash, ceiling, and configuration change
**and** a valid SEC identity at the canonical boundary **and** the complete T4 preflight. **No
individual gate or partial combination permits transport**: §17 item 2 makes enablement before the
T5 instrument a stop condition, and today the key cannot even exist — `_Section` is
`extra="forbid"`, so a configuration carrying it is rejected at load until the lawful T2 schema
addition. **Enabling M3.2 acquisition cannot accidentally authorize the M2.2 surfaces**: the census
gate (`cli.py`, `network_commands = {"census", "ingest-pilot"}`) consults `config.network.enabled`
only, which the contract holds `false` throughout every M3.2 window, so `sec census` and
`sec ingest-pilot` remain refused at their existing gates; no other command consults the new key.

### F2 — command and path surface

All six planned interfaces are explicitly dispositioned in §16 and match runbook Appendix B
one-to-one: `m3 acquire` (with `--show-scope` and, for recovery, `--resume-from`, carrying the
explicit `--live` flag), `m3 derive-dependent-plan`, `m3 reconcile-requests`, `m3 show-drift`, and
`m3 recover`. The expected surfaces are named exactly: CLI wiring in `cli.py`; the **new**
acquisition driver `src/disclosure_drift/m3/acquisition.py`; bounded edits to `m3/request_plan.py`
(M3.2B derivation) and `m3/recovery.py` (repair application, inspection unchanged — Decision 028
§8's ownership split); bounded edits to `sec/census_orchestrator.py` and `sec/index_retrieval.py`
where the T2 packet confirms them (both exist); receipt-emission call sites with `m3/receipt.py`
itself unchanged and its schema frozen; the one-field configuration schema addition; new unit
tests `test_m3_acquisition.py`, `test_m3_dependent_plan.py`, `test_m3_recover.py` (all absent
today, as required); and bounded edits to `test_m3_cli.py`, `test_m3_request_plan.py`,
`test_m3_recovery.py`, and `test_config.py` (all present today). Refusal-boundary tests are
required by §18 with non-vacuous positive controls. **No required surface is omitted, and no
§16-prohibited surface must be modified for lawful implementation** — the prohibited list excludes
`config.py`/`configs/` only *beyond the named change*, which is now named, resolving the initial
draft's self-referential indeterminacy.

## 7. Full contract regression review

Independently confirmed, beyond F1–F7:

1. **Identities.** Plan `19be7bdc…` (schema `m3-request-plan/1.0`, planner
   `quarterly-index-instances/2.0`); budget `2d453e0b…`; checklist `34fc0567…`; token record
   `b06ae373…` (readiness only); ceiling **801** bound to the plan hash — all matching accepted
   Decision 031 §4 verbatim, Decision 030, STATUS, and evidence-index rows EV-M31B-001–006. The
   arithmetic re-verified: U = (1,1,1,1,1,0,70) sums to 75 planned logical requests; per-route
   `A_reachable` (6,6,6,6,7,6,11) per Decision 029 §8 gives 4×6 + 7 + 0×6 + 70×11 = 31 + 770 =
   **801**; the spacing floor 200.0 s = max(0, 801 − 1) ÷ 4.0, a floor and never a duration claim;
   70 instances `2009QTR1`–`2026QTR2` with closed 2026 Q2 per Decision 013 §1; cache hits 0,
   excluded before planning and never subtracted again; contingency prohibited (Decision 027 §0
   item 2; master plan M3.2 §3).
2. **M3.2A / M3.2B separation.** §6 splits the routes; §15 forbids M3.2B planning, budgeting,
   approval, or start before the freeze; §8 repeats T4–T6 per window; §17 items 2, 5, and 21 stop
   cross-window requests; the M3.2A ceiling may not be inherited, reused, or extended — matching
   master plan M3.2 §§2, 3, 11, 16, 17.
3. **No invented M3.2B count.** Both M3.2B counts carry the accepted sentinel until derived
   offline from the frozen objects with a separate exact owner approval (master plan M3.1 §15;
   Decision 027 §§15–16).
4. **Gate H position.** §14: Gate H runs only after M3.2B and integrates both windows — matching
   the master plan and the frozen checklist.
5. **Migration-chain-0013 catalog conclusion.** Still valid at this tree: migrations are contiguous
   `0001`–`0013` with no `0014`; the accepted initializer idiom
   (`CatalogWriter(...)` → `migrate()` → `seed_reference_data()`) creates a catalog at any
   caller-supplied path; the accepted recovery inspector queries `census_recovery_states` and
   `pilot_selection_runs`, requiring the full chain — exactly what §11 specifies
   (`catalogs/m3_2a_operational.sqlite3` below the external evidence root, created only inside an
   authorized window, **no migration effects**). No schema need is implied.
6. **Raw objects.** Immutable, content-addressed, external, append-only: `.part` staging, atomic
   no-overwrite hard-link promotion, `O_CREAT|O_EXCL` lineage intents verified in
   `sec/raw_store.py`; a differing body is a new observation, never an overwrite (§10; CLAUDE.md
   rule 6).
7. **Receipts.** One `m3-execution-receipt/2.0` receipt per live command, closed schema,
   prohibited-field table enforced fail-closed, no sensitive content; receipts contaminate no
   governed identity, and the suite-level S5/S6 non-contamination proof must keep passing (§§10,
   11, 19).
8. **Recovery and resume.** Fail-closed: terminating receipt, explicit owner resume-or-new-run
   decision, `SAFE`-before-resume via the read-only inspector, `UNDETERMINED` a hard stop,
   consumed counts carried forward under the same never-raised ceiling (constructor-refused if
   exceeded), duplicate prevention proven before resume (§12; Decision 028 §§7–8; the recovery
   template's per-window ceiling accounting and condition 8.8).
9. **D023-O1.** Unchanged: latent, fail-closed, stop-and-refer, never reclassified (§17 item 15;
   §23; Decision 030 Ruling E; register entry present).
10. **No instrument becomes live authorization.** The readiness token (readiness only, §2), the
    ceiling approval, contract acceptance (T1), and implementation acceptance (T3) are each
    expressly not live-operation authorization (§8 preamble; §24); contract acceptance does not
    authorize implementation (T2 separate, all five Decision 024 §8 conditions); implementation
    acceptance does not authorize live operation (T5 separate, per window); **T5 remains an exact
    per-operation owner instrument** naming command, window, plan hash, ceiling, and the
    configuration change.
11. **Prohibited content.** Zero filing-body access (no `/Archives/edgar/data/`, `-index.htm`, or
    filing-document suffixes), zero CompanyFacts, zero Frames, no financial-outcome source, no
    non-SEC host, GET only, no external corpus, no arbitrary URL (the announcement route is
    manifest-resolved only, `U = 0` lawfully from the explicitly empty operator manifest with its
    `A_reachable = 6` witness retained) — §§6, 13; the runtime guards verified on the fetch path.
12. **Mandatory contents.** All twenty master-plan global §16 items are present and exact
    (baseline and tag; cited decisions; exact authorized and prohibited paths; the two
    authorization lines; ceiling 801; CLI interface via §16/§21 and the cited Appendix-B
    contracts; storage, migration (`none`), and identity effects; test requirements; targeted and
    phase-end validation; the named nonchange proof; failure/rollback; commit, tag, and
    completion-report policy; the exact completion token
    `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED`).
13. **Stop conditions.** §17's twenty-one conditions survive the corrections intact, ending with
    the no-workaround sentence; every consequential mismatch this rereview probed maps to one.
14. **Header negative authority.** The corrected header confines `CONTROLLED AND EXPLICITLY
    AUTHORIZED` to the master-plan network-permission class name for the one named command,
    grantable only by the §8 instruments; §16 opens "Nothing below is authorized by this draft";
    §§24–25 withhold every authority not separately granted. No wording grants implementation,
    network, acquisition, or catalog authority under adversarial reading.

## 8. Findings

Zero BLOCKER. Zero MAJOR. One MINOR. One OPTIMIZATION.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| R1 | MINOR | §14 says required-object absences are "enumerated in the window's **receipt**," and labels an unadjudicated-absence window `completed_with_absences`. The accepted `m3-execution-receipt/2.0` schema — which the contract itself freezes (§16) — is a closed field set carrying per-route accounting **counts** (`actual_per_route`, `response_classification_totals`, `status_code_totals`), not per-item object identities, and its `completion_status` enumeration does not contain `completed_with_absences`. The contract text follows accepted Decision 032 §5.1 verbatim, so this is not a contract infidelity, and no false-success path results: the receipt's per-route accounting exposes every absence count, the item-level identities are lawfully enumerated by `m3 reconcile-requests` (which "flags every divergence"), the catalog's per-instance state, and the Gate H item-by-item reconciliation (§9), and `completed_with_absences` reads naturally as the window's governance classification, not a receipt field value | Nonblocking for T1 acceptance unchanged. The T2 packet should state expressly where the item-level enumeration and the window classification physically live (receipt accounting + reconciliation output + Gate H record), under the contract's own §1 hierarchy rule that accepted records (the frozen receipt schema) control |
| R2 | OPTIMIZATION | §16's prohibited list reads "Decisions 001–032"; Decision 033 postdates the correction commit and is not named. No exposure exists — CLAUDE.md rule 14, the Decision 030 §10 no-in-place-edit convention, the contract's §1 hierarchy, and §24 ("nor alter … any prior decision") all independently protect Decision 033 | No correction required; a future authorized edit could say "and every later accepted decision record" |

Neither finding is a new contradiction or an authority expansion introduced by the corrections;
neither reopens F1 or F2.

## 9. F5 residue and residual limitations

- **`Docs/decision_index.md` navigation staleness — known, recorded, nonblocking.** Verified: the
  file is byte-identical to its bytes at commit `3fbaa12d…` (empty `git diff` between that commit
  and HEAD for the path), exactly as accepted Decision 033 §5 directs, and it therefore again
  carries the stale Decision-029 next-action sentence. Verified that the stale sentence grants no
  implementation, network, acquisition, or other competing operational authority: it is M3.1-era
  workflow prose, long discharged, in a document that CLAUDE.md, STATUS, and the registry all
  subordinate as a navigation aid "never consulted to establish that a decision exists or is
  approved," while `Milestones/STATUS.md` carries the authoritative next action. Accepted Decision
  032 §§5.5 and 7 still name this path as an F5 correction target and authorized path although the
  restoration removed that correction — Decision 033 §5 and the registry record both facts
  truthfully and are the controlling records; nothing was silently reconciled. **This rereview did
  not edit the file, did not reopen Decision 032 or Decision 033, and does not classify the
  corrected contract as defective for this navigation residue. No new finding is required — the
  item is already adjudicated, open, and nonblocking. Correcting the index later requires its own
  separate explicit path authorization** (Decision 033 §5).
- The F4 evidence-index vocabulary extension remains deliberately open, gated by contract §20
  before any public indexing of the between-windows freeze artifacts.
- All **35 open** limitations-register entries remain active and are inherited by §23 (D020 ×5,
  D021 ×10, D022 ×1, D023 ×4, D024 ×2, D026 ×3, open M3 ×10 — totals verified against the
  register; M3-L11 and M3-L12 are `CLOSED` 2026-08-03). D023-O1 remains the sole unresolved
  owner-ruling condition, latent and stop-and-refer.
- Same-device-only backups persist until the owner's T4 off-device decision (§20; M3-L11 residual
  note; Decision 031 accepted MINOR finding 2).
- The three response-outcome expectations remain deliberately unresolved under Decision 030 Ruling
  C, resolved only by the actual controlled acquisition; elapsed-time factors above the 200.0 s
  spacing floor remain acknowledged and unestimated; SEC-side variability fails closed under §17.
- Private-evidence bindings were verified through the accepted public records (Decisions 030–031,
  the evidence index, STATUS); private evidence content was not read, and the mode-700/600
  evidence-root regime is owner-prepared state validated at Decision 029 §12 step 8, not
  re-verified here.
- Finding R1 (receipt-enumeration surface) is carried to the T2 packet.

## 10. Explicit contract, implementation, and live-SEC status

This rereview changes no byte of the contract, closes no finding, accepts nothing, and authorizes
nothing. After this rereview: the M3.2 contract remains `DRAFT — CORRECTED (DECISION 032) —
PENDING INDEPENDENT REREVIEW AND OWNER ACCEPTANCE` and is **not accepted** — T1 is a separate
owner act that only the owner may now take; M3.2 implementation authorization remains **`NO`** (T2
has not occurred and requires all five Decision 024 §8 conditions after T1); **network and
CompanyFacts remain disabled; no live SEC access, no SEC contact, no connectivity test, no
controlled acquisition, no operational-catalog creation or population, and no use of the M3.2A
request ceiling 801 is authorized or occurred**; the `m3.1-complete` tag is unchanged and no new
tag exists. The only repository change made by this session is this artifact and its authorized
commit.

## 11. Verdict

All Decision 032 corrections were fully and correctly applied; no correction introduced a new
contradiction or authority expansion; the contract remains draft-only with complete negative
authorization; the implementation and network boundaries are exact and implementable;
successful-completion semantics cannot produce false success; live operation remains separately
and explicitly owner-gated per window; every required governance validation passed. Zero BLOCKER
findings; zero MAJOR findings; **F1 fully corrected; F2 fully corrected**; one MINOR and one
OPTIMIZATION finding, both nonblocking for acceptance unchanged. The corrected contract is ready
for the owner's T1 acceptance decision.

```text
M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS
```

**Recommended owner disposition:**
`RETURN_FOR_CHATGPT_OWNER_M3_2_CONTRACT_ACCEPTANCE_DECISION` — Do not accept or implement the
contract, enable network access, or perform live SEC acquisition.

## 12. Reviewer signature

Independent rereview performed and recorded directly — with no subagents — by Claude Code session
`session_013AyJ5c15m329AebGZQr7ce` (Claude Fable 5, maximum effort), 2026-08-04 UTC, at reviewed
commit `3bf9987dd72e1531da2f678fbbef735f37aefcf4`, under the owner's 2026-08-04 rereview
instruction, with independence and container-continuity disclosed and attested in §1. This
artifact records a review verdict only; every acceptance, authorization, and enablement decision
remains the owner's.
