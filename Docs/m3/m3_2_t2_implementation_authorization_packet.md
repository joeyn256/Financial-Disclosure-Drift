# DRAFT T2 IMPLEMENTATION-AUTHORIZATION PACKET — PENDING CHATGPT OWNER REVIEW

```text
STATUS: DRAFT T2 IMPLEMENTATION-AUTHORIZATION PACKET — PENDING CHATGPT OWNER REVIEW
IMPLEMENTATION AUTHORIZATION: NOT GRANTED
NETWORK_AUTHORIZATION: NONE
REVISION: v2 (2026-08-04) — supersedes the v1 draft at this same path (v1 committed at
  60865c044c6d6e005be3cb3ad81da56bff87392b and preserved in history); prepared under
  OWNER_M3_2_T2_PACKET_PREPARATION_AUTHORIZATION: APPROVED (2026-08-04) and revised under the
  owner's detailed preparation instruction of the same date
READINESS CONCLUSION: READY_FOR_OWNER_T2_DECISION (§3)
```

**This packet authorizes nothing.** Drafting it is not approval of it (Decision 034 §9; master
plan global §5 item 13). It grants no implementation authority, changes no executable byte,
enables no network or CompanyFacts, authorizes no SEC contact, connectivity test, acquisition,
operational-catalog creation, ceiling-801 use, M3.2B work, or Gate H execution, and creates no
tag. It returns to the ChatGPT owner for the separate T2 decision, and **no executable byte may
change before that decision is issued**. Where this packet and an accepted record disagree, the
accepted record controls and this packet is corrected.

## 1. Purpose and governing authority

This packet is the proposal for **transition T2** of the accepted M3.2 contract's §8 gate ladder
("Implementation authorization — bounded code/test work on the §16 paths may begin"). It is
written so a later implementation session can operate **without redefining** architecture,
command surfaces, network authority, configuration fields, catalog behavior, attempt accounting,
recovery semantics, completion semantics, evidence requirements, test requirements, stage
boundaries, commit boundaries, or acceptance gates — every one of those is fixed below by
reference to accepted authority or by exact proposal for the owner to approve.

Cited, never restated: [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md)
(`ACCEPTED (T1) — DECISION 034 (2026-08-04) — IMPLEMENTATION NOT AUTHORIZED`; accepted text
SHA-256 `75e7e5a1…`, current file `a5ac0e8d…`) §§5–25;
[Decision 034](../Decisions/decision_034_m3_2_contract_acceptance.md) (T1 acceptance; §6 R1
mandate; §9 authority separation); [Decision 024](../Decisions/decision_024_m2_m3_boundary_governance.md)
§8; Decision 027 v0.2 / [master plan](../../Milestones/milestone_03_master_plan.md) phase M3.2
§§1–36 and global §§5–16; Decision 028 §§7–8; Decision 029 §8; Decision 030 Rulings C and E;
Decision 023 §7 O1; the independent rereview
([artifact](reviews/m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md),
SHA-256 `91235a1a…`, `M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`);
[`Docs/m3/operator_runbook.md`](operator_runbook.md) steps 16–28 and Appendix B;
[`Docs/m3/execution_receipt_spec.md`](execution_receipt_spec.md) (`m3-execution-receipt/2.0`,
frozen); `Docs/leakage_register.md`; CLAUDE.md rules 4, 6, 9, 12.

## 2. Verified baseline and revision provenance

Verified live at v2 preparation, read-only:

| Field | Value |
|---|---|
| Branch / sync | `main`; `HEAD == origin/main == 60865c044c6d6e005be3cb3ad81da56bff87392b` ("Prepare M3.2 T2 implementation-authorization packet" — the v1 draft commit); ahead 0, behind 0 |
| Ancestry | parent `3db7487e…` (T1 acceptance, Decision 034), grandparent `3069b03e…` (independent rereview) |
| Working tree | clean; nothing staged; no non-ignored untracked path |
| Tags | `m3.1-complete` unchanged (`638a02b7…` → `4cd2c72…`); no tag at HEAD |
| Frozen implementation | `git diff 970e050d… HEAD -- src tests` **empty** — no executable byte has changed since the accepted M3.1 freeze |
| Contract / decision identities | contract file `a5ac0e8d…` (accepted text `75e7e5a1…`); Decision 034 `01818600…`; rereview artifact `91235a1a…` |
| M3.2 state | no acquisition implementation; no operational catalog; no live SEC request; ceiling 801 unused |

**Revision provenance.** The owner's detailed preparation instruction expected HEAD `3db7487e…`
and destination `Docs/m3/plans/`. The actual HEAD carries the v1 draft prepared earlier the same
day under the owner's preparation authorization, and no `Docs/m3/plans/` convention exists — the
instruction's own fallback ("use the exact established equivalent") resolves to this file's
established path. v2 therefore supersedes v1 **in place**; v1 remains in Git history. Nothing
else about the expected authority state differed.

## 3. Decision 024 §8 condition matrix and readiness conclusion

Decision 024 §8: "**No Milestone 3 phase may begin implementation without all of:** (1) a
separate accepted governance record where the phase requires one; (2) a bounded implementation
contract for that phase; (3) explicit owner authorization; (4) exact path authorization — the
authorized-path discipline of every prior stage contract; (5) satisfaction of that phase's
inherited prerequisite gates (§5.2)." Milestones 0–2 closeout, the precondition of Decision 024
§9, is complete (Decision 026).

| # | Condition | Satisfied? | Proven by | Remaining owner decision | Unresolved dependency | Evidence required at the T2 approval boundary |
|---|---|---|---|---|---|---|
| 1 | Accepted governance record | **YES** | Decisions 027 v0.2, 028, 029, 030 fix the M3.2 methodology; Decision 034 accepts the contract (§1 here) | none | none | Registry rows 027–030, 034 unchanged |
| 2 | Bounded implementation contract | **YES** | `m3_2.md` accepted at T1 (§2 here) | none | none | Contract status line and hash re-verified live |
| 3 | Explicit owner authorization | **NO — it is the decision this packet requests** | §17 (the proposed instrument) | Issue, amend, or refuse the §17 instrument | none | The issued instrument, quoting this packet's SHA-256 and the baseline commit |
| 4 | Exact path authorization | **PROPOSED** | §5 (allowlist), §7 (per-stage sub-allowlists) | Approve the fifteen-path allowlist and the two declined surfaces | none | The instrument's path clause matching §5 exactly |
| 5 | Inherited prerequisite gates | **YES** | Gate F readiness token recorded; M3.1 owner-accepted (Decision 031) and checkpointed at `m3.1-complete`; plan `19be7bdc…`, budget `2d453e0b…`, ceiling **801** accepted; M3-L11/M3-L12 `CLOSED`; D023-O1 latent | none | none | `make context` green at grant; tag and identity re-verification |

**Conclusion: `READY_FOR_OWNER_T2_DECISION`.** Conditions 1, 2, and 5 are satisfied; condition 3
is exactly the decision the owner is asked to take; condition 4 is fully enumerated for that
decision. One adjudication is **bundled into** the T2 decision rather than blocking it: the
commit-cadence choice of §8 (the accepted contract §22 fixes a one-commit default; the
recommended six-stage cadence requires the owner's instrument to amend it). **This packet does
not and cannot approve T2.**

## 4. Six-command disposition

The complete planned M3.2 command surface (runbook Appendix B; contract §16). Exit-code
convention throughout: `0` success · `1` configuration error · `2` usage · `3` stage not
enabled · `4` gate failure. Every command requires the absolute external `--evidence-root` and
addresses artifacts by paths **relative** to it (existing `m3` convention); none writes any
tracked repository path at runtime.

### 4.1 `m3 acquire` — the only live command

| Aspect | Disposition |
|---|---|
| Purpose | Execute exactly the approved plan for one window (M3.2A now; M3.2B later under its own approval), metadata only, under the explicit shared ceiling |
| Inputs | `--config` (window-local file via `DISCLOSURE_DRIFT_CONFIG` or `--config`); `--evidence-root`; `--plan <rel>` (must hash to the approved plan hash — `19be7bdc…` for M3.2A); `--window {M3.2A,M3.2B}`; `--live` (explicit, no default); `--ceiling <INT>` (must equal the approved integer exactly — 801 for M3.2A); `--catalog <rel>` (operational catalog, created inside the authorized window if absent); `--data-root <rel>` (isolated M3.2 data root); `--receipt-out <rel>`; `--resume-from <rel>` (recovery only, predecessor receipt) |
| Outputs | Stdout progress per route (planned, attempted, succeeded, classified, stored) then totals; immutable raw objects; source observations with redirect chains; quarantine entries; catalog rows in their transaction; JSONL projection; **one receipt** |
| Live/offline | **LIVE** — the only command that may ever construct a transport, and only under the complete §9 conjunction |
| Authority | Operationally: T3 accepted, T4 preflight complete, exact T5 instrument. Code-level: the §9 conjunction, refusing before transport construction |
| Configuration | `network.m3_acquire_enabled: true` **only** in the owner-supplied window-local configuration; tracked default `false`; `network.enabled` remains `false` |
| Receipt | Mandatory, one per invocation, `m3-execution-receipt/2.0`, `invocation_mode = "live"`; a resumed run records `recovery_predecessor_receipt_id` and `consumed_request_count_carried_forward` |
| Refusals | Missing `--live`: `2`. `m3_acquire_enabled` false with `--live`: `3`. Identity invalid / evidence root not external / config invalid: `1`. Plan-hash, window, or ceiling mismatch; prohibited route; ceiling exhaustion with work remaining; blocking drift; unclassifiable response: `4` — all before or instead of any further wire activity |
| Repository paths | Implementation in P3 + P4 (§5); no tracked path written at runtime |
| Test families | `test_m3_acquisition.py`, `test_m3_cli.py`, conjunction tests in `test_config.py` |
| Delivery stage | Refusal skeleton in **T2.1**; storage integration **T2.2**; full state machine **T2.3**; resume path **T2.4**; final integration **T2.6** |

### 4.2 `m3 acquire --show-scope` — offline scope proof

| Aspect | Disposition |
|---|---|
| Purpose | Print allowed hosts (`www.sec.gov`, `data.sec.gov`), method (`GET`), the exact route allowlist for the named window, the denylist families, the approved plan hash, the approved ceiling, and the consumed-count baseline from the receipt chain — and **make zero requests** (runbook step 17; operator compares against Gate F evidence and stops on any difference) |
| Inputs | `--config`; `--evidence-root`; `--plan <rel>`; `--window`; optional `--receipt-chain-head <rel>` for the consumed baseline (baseline 0 when absent and the catalog is empty) |
| Outputs | The scope report on stdout; exit `0` |
| Live/offline | **Offline, read-only, zero requests** — never constructs a transport |
| Authority / configuration | None beyond a valid configuration; works with all network keys `false` |
| Receipt | **None** — read-only inspection is covered by the command it inspects (receipt spec §2; prior review Q43) |
| Refusals | Unreadable/mismatched plan: `4`; invalid config: `1` |
| Test families | `test_m3_cli.py` (output contract; zero-socket proof via the autouse guard) |
| Delivery stage | **T2.5** |

### 4.3 `m3 derive-dependent-plan` — offline M3.2B derivation

| Aspect | Disposition |
|---|---|
| Purpose | Derive the M3.2B plan **offline over the frozen M3.2A objects**: historical-file references from the frozen bulk-submissions object plus the explicit entity reconciliation set; zero requests; no invented count (the sentinel resolves here) |
| Inputs | `--config`; `--evidence-root`; `--from-window M3.2A`; `--catalog <rel>`; `--reconciliation-set <rel>`; `--plan-out <rel>` |
| Outputs | The M3.2B request plan (`m3-request-plan/1.0`) and its SHA-256 on stdout; one **dry-run** receipt (zero actual counts — the same convention as the accepted `m3 plan-requests` runs, EV-M31B-003/004) |
| Live/offline | **Offline, zero requests** |
| Refusals | Transport-capable configuration detected (either network key `true`): `4`; source object absent, unfrozen, or failing `content_sha256`: `4`; derived set disagreeing with what the frozen objects name: `4` (contract §17 item 21) |
| Test families | `test_m3_dependent_plan.py` (frozen-object fixture; determinism; refusals), `test_m3_request_plan.py` (plan-identity nonchange), `test_m3_cli.py` |
| Delivery stage | **T2.5** |

### 4.4 `m3 reconcile-requests` — offline reconciliation and absence enumeration

| Aspect | Disposition |
|---|---|
| Purpose | Planned-versus-actual per route and in total (logical requests, physical attempts, classification totals, raw objects), flagging every divergence, and emitting the **item-level absence enumeration** (§10) |
| Inputs | `--evidence-root`; `--plan <rel>`; `--receipt <rel>` (terminating receipt or chain head); `--catalog <rel>`; `--report-out <rel>` (the private reconciliation-report artifact) |
| Outputs | Deterministic report — identical inputs produce byte-identical output; per-window, transcribed into the Gate H checklist |
| Live/offline | **Offline, read-only** (its only write is the report artifact under the evidence root) |
| Receipt | None (read-only inspection) |
| Refusals / exit | `0` only when every divergence is explained by a plan rule **and** the absence enumeration is empty; non-empty absences or unexplained divergence: `4`; broken plan↔receipt↔catalog linkage: `4` (stop condition, never an adjustment) |
| Test families | `test_m3_acquisition.py` (reconciliation unit), `test_m3_cli.py` |
| Delivery stage | **T2.4** |

### 4.5 `m3 show-drift` — offline drift inspection

| Aspect | Disposition |
|---|---|
| Purpose | List every schema-drift event by kind, field path, affected route, and affected raw-object identity, separating retained-unknown-field events from blocking events |
| Inputs | `--evidence-root`; `--catalog <rel>`; `--run <run-id>` |
| Outputs | The drift listing; exit `0` only when there is **no** blocking event; any blocking event opens `schema_drift_incident.md` and stops the phase for an owner ruling |
| Live/offline | **Offline, read-only**; no receipt |
| Refusals | Blocking drift present: `4`; unknown run: `4` |
| Test families | `test_m3_acquisition.py`, `test_m3_cli.py` |
| Delivery stage | **T2.4** |

### 4.6 `m3 recover` — offline deterministic repair (mutating, separately invoked)

| Aspect | Disposition |
|---|---|
| Purpose | Apply exactly one deterministic repair the read-only inspector reported as required — adopt an orphan through the authoritative catalog reconcile path, quarantine a partial or unverifiable object (move-and-preserve, never delete), remove a stale `.part` as a never-promoted temporary, or rebuild the JSONL projection — then require a fresh `m3 recovery-state` returning `SAFE` before any resume. Inspection itself never repairs (Decision 028 §8) |
| Inputs | `--evidence-root`; `--plan <rel>`; `--receipt-chain-head <rel>`; `--catalog <rel>`; `--data-root <rel>`; `--action <adopt-orphan|quarantine-partial|remove-stale-part|rebuild-projection>` (explicit, no default); `--event <id>` where the action targets one recovery event |
| Outputs | The applied repair, recorded as catalog recovery-event rows; instructions to re-run the inspector |
| Live/offline | **Offline, mutating below the evidence root only**; never constructs a transport |
| Receipt | **None** — `recover` is not a live command and the receipt mode set is frozen; its durable evidence is the catalog recovery-event family plus the completed `interrupted_run_recovery.md` instance (private evidence) |
| Refusals | Inspection `UNDETERMINED`: `4` (owner referral — recovery uncertainty is a stop condition); requested action differing from the deterministically required one: `4`; any action that would delete acquired data: structurally impossible (no deletion path exists) |
| Test families | `test_m3_recover.py`, `test_m3_recovery.py` (inspector unchanged), `test_m3_cli.py` |
| Delivery stage | **T2.4** |

## 5. Exact implementation path allowlist

**Production (8).**

| # | Path | Disposition | Bound |
|---|---|---|---|
| P1 | `configs/project.yaml` | edit | Exactly one added key: `network.m3_acquire_enabled: false` under the existing `network:` block. **Never committed `true`.** No other byte |
| P2 | `src/disclosure_drift/config.py` | edit | Exactly one added field: `m3_acquire_enabled: bool = False` on `NetworkSection`. `_Section` stays `extra="forbid", frozen=True`; no env override is added |
| P3 | `src/disclosure_drift/m3/acquisition.py` | **new — the only new module** | The bounded acquisition driver exactly as contract §16 names it: window execution over the approved plan; the explicit shared ceiling gate; storage, observation, quarantine, and projection orchestration; **and** the reconciliation and drift-reporting logic consumed by `m3 reconcile-requests` / `m3 show-drift` (the contract's own §16 description bundles them into this module; no second new module is proposed) |
| P4 | `src/disclosure_drift/cli.py` | edit | Parser wiring, dispatch entries in the `_m3_command` handlers mapping, and handlers for the six §4 surfaces; receipt-emission call sites for the live command. No existing M3.1 command's behaviour changes; the `sec` group is untouched |
| P5 | `src/disclosure_drift/m3/request_plan.py` | bounded edit | M3.2B dependent-plan derivation beside the frozen builder. `REQUEST_PLAN_SCHEMA_VERSION`, `build_m3_2a_request_plan`, `canonical_plan_bytes`, `derive_a_reachable`, and plan hash `19be7bdc…` must remain behaviourally identical — proven by test |
| P6 | `src/disclosure_drift/m3/recovery.py` | bounded edit | The repair applier for `m3 recover` and the §11 conservative accounting, beside the inspector. `inspect_recovery_state` stays read-only and never calls `observation_catalog.reconcile()` |
| P7 | `src/disclosure_drift/reasons.py` | **reserved — expected untouched** | No new reason code is anticipated (§12 maps every state to a registered code). A genuinely unregistered condition is a **stop-and-return** for a separately owner-approved registry change — never a code invented under T2 |
| P8 | `src/disclosure_drift/m3/__init__.py` | edit | Export surface for the new driver only |

**Tests (7).**

| # | Path | Disposition |
|---|---|---|
| T1 | `tests/unit/test_m3_acquisition.py` | **new** — driver, ceiling boundary, routes, classifications, absences, reconciliation, drift |
| T2 | `tests/unit/test_m3_dependent_plan.py` | **new** — offline derivation from frozen-object fixtures |
| T3 | `tests/unit/test_m3_recover.py` | **new** — repair actions, kill-point matrix, resume boundaries |
| T4 | `tests/integration/test_m3_cli.py` | bounded edit — the six surfaces, exit codes, refusal boundaries |
| T5 | `tests/unit/test_m3_request_plan.py` | bounded edit — plan-identity nonchange + derivation coverage |
| T6 | `tests/unit/test_m3_recovery.py` | bounded edit — inspector still read-only; repair-boundary interaction |
| T7 | `tests/unit/test_config.py` | bounded edit — the one new field, default `false`, `extra="forbid"` intact |

**Dispositioned and DECLINED (remain prohibited).**
`sec/census_orchestrator.py` — the M2.2 census surface; builds its own transport and carries M2.2
gating; the M3.2 driver must not inherit either. `sec/index_retrieval.py` —
`retrieve_instance(client, store, instance, *, on_state=…)` already accepts an injected
`SecClient` (which carries the `PhysicalAttemptCeiling` and runs `before_attempt()` before every
wire attempt) and an `on_state` persistence hook; the driver consumes it unchanged.
`sec/source_registry.py` — all nine route families (seven bootstrap, two dependent) are already
registered under `m2.2-source-registry/1.0`; read-only consumption. `sec/raw_store.py`,
`sec/observation_catalog.py`, `sec/snapshots.py` (`SnapshotStore`), `sec/http_client.py`,
`sec/request_ceiling.py`, `storage/catalog.py` — accepted, injectable, consumed unchanged.
`m3/receipt.py` — **frozen schema; prohibited**. A discovered need to edit any of these is
stop-and-return S1 (§7.8), never self-widening.

**Prohibited (restating contract §16 and the preservation list, binding at every stage).** Every
accepted S4/S5/S6 module; every migration (no `0014`); `cohorts.py`; `pilot_policy.py`;
`paths.py`; `config.py` beyond P2; `configs/` beyond P1; `release/`; `sec/pilot_manifest_store.py`;
`m3/receipt.py`; `m3/rehearsal.py`; `m3/evidence_paths.py`; `.github/`; `Makefile`;
`pyproject.toml`; `scripts/`; `tests/conftest.py` (the autouse `_block_network` socket guard);
**`tests/integration/test_no_network.py` (byte-identical and passing)**; `Docs/preregistration.md`;
Decisions 001–034 and the registry; every completed contract and the accepted M3.2 contract;
both review artifacts; `Docs/decision_index.md`; every `Docs/m3/templates/` file; the accepted
M3.1 evidence and its identities (plan `19be7bdc…`, budget `2d453e0b…`, checklist `34fc0567…`,
token `b06ae373…`); the `m3.1-complete` tag; all private evidence. **No tracked path may ever
contain raw data, a database, a receipt, private evidence, or any part of the SEC identity.**
A needed path outside the allowlist requires **owner adjudication before any edit**.

## 6. Proposed staged implementation — T2.1–T2.6

Six sequential bounded stages, exactly the structure the owner's instruction sketches; the
accepted architecture requires only one adjustment, stated inline at T2.2. **Common to every
stage:** prohibited files = everything outside that stage's authorized files; no network call in
any test (the autouse socket guard proves it); no migration; no receipt-schema change; **a stage
tag is prohibited** (master plan §34 names only `m3.2-complete`, after independent M3.2
acceptance — no accepted rule requires a stage or T3 tag); each stage ends with the CLAUDE.md
completion packet plus the contract §22 field list (operational fields marked not-applicable —
offline); each stage's commit remains **local until the ChatGPT owner reviews the stage
completion report**, and the next stage may not begin before that review boundary passes.

### T2.1 — Configuration and fail-closed authority layer

- **Objective:** the two one-line configuration additions (P1, P2); CLI parser wiring and the
  complete refusal skeleton for all six surfaces (every command parses, and every live-path
  invocation refuses exactly per §4/§9 — no acquisition logic yet); proof that no actual network
  enablement occurs and that the existing M2.2 commands remain unreachable.
- **Authorized files:** P1, P2, P4, P8, T4, T7.
- **Implementation requirements:** `--live` with no default; the §9 conjunction evaluated in the
  stated order with each failure refusing before any transport construction; `network.enabled`
  unconsumed by `m3 acquire`; `sec census`/`sec ingest-pilot` still gated solely by
  `network.enabled`; unknown configuration keys still rejected (`extra="forbid"`).
- **Required tests:** configuration conjunction rows 1–4 and 6–9 of §9.3; CLI refusal tests for
  all six commands; no-network defaults; positive controls (key true without `--live`; `--live`
  with key false; unknown-key rejection).
- **Targeted gates:** `make test PYTEST_ARGS="tests/unit/test_config.py tests/integration/test_m3_cli.py"`;
  Ruff + format on touched files; `mypy src`; `make secrets`; `make hygiene`; protected-path
  diff empty.
- **Stop conditions:** any need outside the authorized files; any test needing a socket; any
  behaviour change to an existing command.
- **Commit subject:** `Implement M3.2 T2.1 network authority layer`.
- **Review boundary:** ChatGPT owner reviews the stage report before T2.2.

### T2.2 — Catalog and immutable-storage integration

- **Objective:** the driver's storage substrate inside `m3/acquisition.py`: operational-catalog
  initialization at migration chain `0013` at the caller-supplied external path via the accepted
  `CatalogWriter(database_path, lock_directory)` → `migrate()` → `seed_reference_data()` idiom;
  external-root containment (`require_external_evidence_root`; artifacts refused outside the
  root); the single-writer lease; content-addressed immutable raw storage through the accepted
  `raw_store` (`.part` staging, atomic no-overwrite hard-link promotion, `O_CREAT|O_EXCL`
  lineage intents); catalog/object transaction ordering (file first, then one transaction for
  observation + reasons + members); duplicate reconciliation (byte-identical body → existing
  object; differing body → new superseding observation, never an overwrite). **No live
  transport anywhere in this stage.**
- **Adjustment, explained:** this stage **writes no storage layer** — the storage and catalog
  modules are accepted M2.2/M3.1 surfaces and are prohibited paths. T2.2 is the *driver-side
  integration* of those surfaces, delivered inside P3 with fixtures.
- **Authorized files:** P3, P8, T1.
- **Required tests:** catalog creation at full chain `0013` in a temp external root; containment
  refusals; single-writer violation; raw-object immutability (no-overwrite promotion); duplicate
  and hash-conflict handling; orphan (object-without-row) and reverse (row-without-object)
  detection; transaction-ordering crash windows leaving no partial visible state.
- **Targeted gates:** `make test PYTEST_ARGS="tests/unit/test_m3_acquisition.py"`; Ruff/format/
  mypy on touched; secrets; hygiene; protected-path diff.
- **Stop conditions:** any apparent need for DDL or a migration (S2); any write outside a temp
  or evidence root.
- **Commit subject:** `Implement M3.2 T2.2 catalog and storage integration`.
- **Review boundary:** owner stage review before T2.3.

### T2.3 — Acquisition state machine and accounting

- **Objective:** the full window state machine in P3 over **scripted transports only**: the
  approved route allowlist and window-scoped separation; per-request execution via the accepted
  `SecClient.fetch` policy loop (5 transient retries, 60 s backoff ceiling, `Retry-After`,
  single 600 s cooldown with one controlled continuation, second cooldown terminal); redirect
  accounting (every hop one physical attempt; loop/depth/family/identity-path stops); the shared
  `PhysicalAttemptCeiling` with stop-before-overflow; six-bucket classification with no
  unclassified residual; **required-object satisfaction tracking and false-success prevention**
  (§12); receipt assembly and emission through the frozen `m3/receipt.py` interfaces.
- **Authorized files:** P3, P4 (live-handler completion), T1, T4.
- **Required tests:** approved-route and prohibited-route/filing-body construction refusals;
  redirect matrix; ceiling C−1/C/C+1 with carried-forward counts; complete physical-attempt
  accounting (retries, hops, cooldown continuation each consume one attempt); retry/cooldown
  sequencing; classification totals summing exactly; per-request terminal states of §12;
  absence detection for 404-absent and quarantined bodies; receipt completeness, mode
  classification, prohibited-field positive control, identity non-contamination.
- **Targeted gates:** as T2.2 plus `tests/unit/test_request_ceiling.py` and
  `tests/unit/test_m3_receipt.py` (unchanged files, executed as regression).
- **Stop conditions:** any response shape the accepted policy cannot classify (S3); any need to
  touch `m3/receipt.py`, the response policy, or the transport (S1/S2).
- **Commit subject:** `Implement M3.2 T2.3 acquisition state machine`.
- **Review boundary:** owner stage review before T2.4.

### T2.4 — Recovery, reconciliation, and inspection

- **Objective:** `m3 recover` (P6 repair applier + P4 wiring); `m3 acquire --resume-from`;
  `m3 reconcile-requests` and `m3 show-drift` (P3 logic + P4 wiring); the §11 conservative
  hard-interruption accounting; SAFE/UNSAFE/UNDETERMINED integration against the unchanged
  inspector; predecessor-receipt chaining; the owner resume/new-run boundary.
- **Authorized files:** P3, P4, P6, T1, T3, T4, T6.
- **Required tests:** the eight kill-point tests of §11.3; SAFE/UNSAFE/UNDETERMINED refusals;
  duplicate-substantive-write prevention on resume; no-headroom stop; reconciliation determinism
  and the absence-enumeration exit contract; drift listing separation; recover-action refusals.
- **Targeted gates:** as before plus `tests/unit/test_m3_recovery.py`.
- **Stop conditions:** recovery semantics requiring inspector changes beyond read-only (S1);
  any state whose accounting cannot be made conservative (owner referral).
- **Commit subject:** `Implement M3.2 T2.4 recovery and reconciliation`.
- **Review boundary:** owner stage review before T2.5.

### T2.5 — Dependent-plan derivation and operator surfaces

- **Objective:** `m3 derive-dependent-plan` (P5 + P4): freeze-input verification (frozen object
  present, hash-verified, provenance-complete), zero-request derivation of the two dependent
  routes from the frozen bulk-submissions object and the explicit reconciliation set, dry-run
  receipt emission, and refusal when transport-capable configuration is detected; **no invented
  M3.2B count** — the sentinel `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` is resolved
  only by this derivation plus the separate owner approval. `m3 acquire --show-scope` (P3/P4):
  the operator-facing zero-request scope proof of §4.2.
- **Authorized files:** P3, P4, P5, T1, T2, T4, T5.
- **Required tests:** derivation determinism over fixtures; zero-request proof (socket guard);
  M3.2A/M3.2B route-separation; plan-identity nonchange (`19be7bdc…` reproduces); show-scope
  output contract and Gate-F-comparison fields; refusal matrix.
- **Targeted gates:** as before plus `tests/unit/test_m3_request_plan.py`.
- **Stop conditions:** derivation requiring any live lookup (S5); reference-set disagreement
  semantics that cannot fail closed.
- **Commit subject:** `Implement M3.2 T2.5 dependent plan and operator surfaces`.
- **Review boundary:** owner stage review before T2.6.

### T2.6 — Integrated offline implementation-acceptance candidate

- **Objective:** complete offline integration — all six surfaces available; the no-network
  default proven end to end; every §14 test category present and green; the full §15 integrated
  validation sequence; the §16 nonchange proof; assembly of the evidence the independent T3
  review needs. **No live execution of any kind.**
- **Authorized files:** any §5 allowlist path, for integration fixes only; no new surface.
- **Required tests / gates:** the complete §15 integrated list, all green.
- **Stop conditions:** any red gate; any diff outside the allowlist; any skipped-instead-of-run
  transport test.
- **Commit subject:** `Complete M3.2 T2.6 integrated offline acceptance candidate`.
- **Review boundary:** this commit is the **implementation-freeze candidate**; next is the
  independent T3 review (§16), then the owner's T3 acceptance decision.

## 7. Commit strategy

- **Recommended: one commit per stage, exactly the six subjects above; no interim commit inside
  a stage** unless recovery from a genuine interruption requires one, in which case the stage
  stops and the owner adjudicates first.
- **Contract §22 adjudication — routed to the owner, not resolved here.** The accepted contract
  fixes "one implementation commit by default," with an intermediate checkpoint only if the
  contract is amended and the owner separately authorizes it. Adopting the recommended cadence
  therefore requires the owner's T2 instrument to **authorize a bounded amendment of contract
  §22** recording the six-stage commit plan (the §17 instrument contains that clause). If the
  owner strikes the clause, the fallback is the contract's single-commit default with the six
  stages as internal validation checkpoints.
- **Publication cadence:** each stage commit remains **local** until the owner's stage review
  passes; on approval it is pushed as a normal fast-forward **before the next stage begins**, so
  every stage starts from a published baseline. No force, pull-merge, rebase, amend of a
  reviewed or pushed commit, reset, or history rewrite — ever.
- **Combining stages:** prohibited without an explicit owner instruction.
- **Pre-T3 checkpoint:** the T2.6 commit SHA is recorded in `Milestones/STATUS.md` and the
  completion report as the **implementation freeze**; the T3 review runs against exactly that
  SHA. **No tag at any stage and no tag at T3** — no accepted rule requires one, and none is
  proposed.

## 8. Stop-and-return conditions (all stages)

Contract §17's twenty-one stop conditions apply in full at every stage. Additionally the
implementation session stops and returns to the owner — never widening its own authority — on:
**S1** any needed edit outside the §5 allowlist (including the declined and consumed surfaces);
**S2** any apparent need for a migration, receipt-schema change, or new reason code;
**S3** any conflict between this packet and an accepted record (the accepted record controls);
**S4** plan hash `19be7bdc…` failing to reproduce; **S5** any test requiring network access, a
real SEC response, or the real identity; **S6** the approved commit cadence proving unworkable;
**S7** any baseline mismatch at stage start or at a nonchange proof.

## 9. Network-enablement architecture

### 9.1 Exact implementation contract

| Element | Contract |
|---|---|
| `configs/project.yaml` | Gains exactly `network.m3_acquire_enabled: false` (tracked default; never committed `true`). `network.enabled: false` is unchanged — the **global kill switch** |
| Configuration model | `src/disclosure_drift/config.py` → `NetworkSection` gains `m3_acquire_enabled: bool = False`. Strict validation is preserved: `_Section` is `extra="forbid", frozen=True`, so before T2.1 lands the key cannot exist in any loadable configuration, and after it lands no other new key can |
| Environment-specific configuration | The owner-authorized **window-local** configuration file, supplied via the allowlisted `DISCLOSURE_DRIFT_CONFIG` (config.py:97) or `--config`, is the only place the key is ever `true`; it is restored or discarded at window end (Gate H items 14.1–14.3 verify). No environment variable can set either boolean directly |
| Canonical consumer | **`m3 acquire --live` alone** reads `m3_acquire_enabled`. No other command consults it; `m3 acquire` never consults `network.enabled` |
| T5 binding | The T5 instrument names the exact command invocation, window, plan hash, ceiling, and the configuration change for `m3 acquire` only; T4 preflight verifies network disabled **before** authorization; enablement before T5 exists is contract §17 stop condition 2 |
| Plan/window/ceiling matching | `--plan` must hash to the approved hash; `--window` must name the approved window; `--ceiling` must equal the approved integer exactly; each mismatch refuses **before transport construction** |
| SEC identity | Validated at the canonical boundary only (`require_sec_user_agent`); value never printed, logged, hashed, or serialized; invalid → exit `1` before any transport |
| Transport construction boundary | The httpx transport is constructed in exactly one place — inside `m3/acquisition.py`'s live path, after every conjunction element passes. `--show-scope` and all §4.3–4.6 commands are structurally incapable of constructing one |

### 9.2 How M2.2 stays disabled

`network_commands = {"census", "ingest-pilot"}` in `cli.py` gate solely on `config.network.enabled`
(cli.py:668), which remains `false` throughout every M3.2 window — so `sec census` and
`sec ingest-pilot` refuse at their existing gates even while `m3_acquire_enabled` is `true`. Two
independent keys, two disjoint consumers; enabling M3.2 acquisition cannot enable M2.2, and
enabling M2.2's key does nothing for `m3 acquire`. A T2.1 positive control proves both directions.

### 9.3 Complete conjunction table

"Transport?" = may an HTTP transport be constructed. Rows 5 and 10 are operationally enforced
(the code cannot read a governance instrument; the discipline that the key is only ever set
`true` in the T5-issued window-local configuration after T3, plus T4 preflight and Gate H items
14.1–14.3, binds them); every other row is code-enforced and refused **before transport
construction**.

| # | `network.enabled` | `m3_acquire_enabled` | `--live` | T5 issued | Plan hash | Window | Ceiling | Identity | T3 accepted | Transport? | Refusing layer / exit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | false | false | any | — | — | — | — | — | — | **NO** | key false → stage not enabled `3` (no `--live` → usage `2`) |
| 2 | **true** | false | any | — | — | — | — | — | — | **NO** for `m3 acquire` | it never reads `network.enabled` → `3`. (M2.2 census would satisfy its own gate — which is why `network.enabled` stays `false` all window) |
| 3 | false | **true** | absent | — | — | — | — | — | — | **NO** | `--live` explicit, no default → `2` |
| 4 | true | true | absent | — | — | — | — | — | — | **NO** | same → `2` |
| 5 | false | true | present | **not issued** | valid | valid | valid | valid | yes | **NO — operationally** | a key set `true` without a T5 instrument is itself contract §17 item 2; T4/Gate H detect and stop |
| 6 | false | true | present | issued | **wrong** | valid | valid | valid | yes | **NO** | plan-hash refusal → `4`, before transport |
| 7 | false | true | present | issued | valid | **wrong** | valid | valid | yes | **NO** | window refusal → `4`, before transport |
| 8 | false | true | present | issued | valid | valid | **≠ 801** | valid | yes | **NO** | ceiling-equality refusal → `4`, before transport |
| 9 | false | true | present | issued | valid | valid | valid | **invalid** | yes | **NO** | identity boundary → `1`, before transport |
| 10 | false | true | present | issued | valid | valid | valid | valid | **no** | **NO — operationally** | no window-local config lawfully exists before T3+T4+T5; preflight refuses |
| 11 | false | true | present | issued | valid | valid | valid | valid | yes | **YES — the only row** | all gates pass; transport constructed; ceiling gate active on every attempt |

Every partial combination refuses before transport construction. Positive controls for rows
1–4 and 6–9 are mandatory tests (§14).

## 10. R1 — mandatory design (Decision 034 §6, carried in full)

Binding constraints first: **receipt v2 remains closed and unchanged unless separately
authorized**; per-item absence identities **do not belong in receipt fields** — the schema
forbids them; the receipt carries **aggregate accounting and immutable references** only;
**`completed_with_absences` is not successful completion**; **no absent object may silently
become satisfied** — satisfaction occurs only through a new authorized acquisition under its own
accounting, never by reclassification or adjudication alone.

1. **Item-level absent-object identities — durable location: the operational catalog, at
   migration chain `0013`, with no new schema.** Quarterly-index instances:
   `census_index_instances` (per-instance key and lifecycle state) joined to
   `census_index_retrieval_accounting` and the instance's registered reason code
   (`INDEX_INSTANCE_UNAVAILABLE` for archival absence; `INDEX_REQUIRED_INSTANCE_MISSING` at
   reconciliation). Singleton bootstrap objects: `census_source_observations` rows (outcome,
   hashes, provenance). Quarantines: `census_quarantined_records` plus the observation outcome.
   The lawful representation **exists**; no migration is invented, and if implementation ever
   concludes otherwise that is stop-and-return S2 for an owner schema decision.
2. **`completed_with_absences` — a window-level governance classification, never a receipt
   value.** Physical representation: the Gate H checklist row for the window; the owner's
   express absence-adjudication record (private evidence); and `Milestones/STATUS.md`. The
   receipt records the run-level status within the frozen five-value enumeration.
3. **Linkage.** The approved plan hash joins plan → receipt → catalog rows;
   `m3 reconcile-requests` derives the item-level reconciliation and the **absence enumeration**
   (per absent object: planned-instance identity, `source_id`, terminal reason code, attempt
   count, catalog row reference — never a body, URL beyond the registered route identity,
   absolute path, or identity) as a private, content-hashed, create-once report; **Gate H
   consumes that reconciled item-level record plus the receipt references** — items 3.1–3.7 per
   window, item 3.3 read under contract §14, the frozen template unedited. Public evidence
   behaviour: the report is indexed only after the §13 vocabulary decision.
4. **Frozen-schema tests** (in T1/T4, all non-vacuous): the `completion_status` enumeration
   equals exactly the five accepted values; a receipt carrying
   `completion_status = "completed_with_absences"` is **refused**; a receipt carrying any
   unknown field (including a would-be `absent_objects` list) is **refused**;
   `receipt_schema_version` remains `m3-execution-receipt/2.0`; the absence enumeration is
   proven derivable byte-identically from plan + catalog alone; `m3/receipt.py` is byte-identical
   at the §16 nonchange proof.

## 11. F3 — conservative interruption accounting

### 11.1 Durable evidence sources

The receipt chain (terminating receipts with actual counts and carried-forward totals); catalog
rows (per-observation attempt accounting committed transactionally); raw-store `.lineage.json`
intents and `.part` staging files; the recovery-event tables. There is deliberately **no
in-flight counter file** — the in-memory ceiling gate's uncommitted state is presumed lost.

### 11.2 Accounting rules

Provably consumed = attempts recorded by committed catalog rows plus any predecessor receipt's
carried-forward count. The **current in-flight logical request** at a hard interruption without
a terminating receipt is charged **conservatively at its full per-route `A_reachable`**
(singletons 6; filing calendar 7; announcement 6; full index 11 — Decision 029 §8). Where even
that bound cannot be established — an unresolvable receipt chain, a catalog row without its
object, an object without its row outside the reconcile path, or any uncertainty about whether a
write committed — the determination is **`UNDETERMINED` and the run does not resume** (owner
referral). Cumulative attempts carry to resume via `consumed_request_count_carried_forward`,
reconstructed as `PhysicalAttemptCeiling(approved_ceiling=801, consumed=carried)` whose
constructor **refuses `consumed > ceiling`**; the ceiling itself is a read-only property with no
raise path, and the resume invocation must pass the same `--ceiling 801`, re-checked for
equality against the plan-bound approval — the original ceiling can never be raised or reset.
Duplicate substantive writes are prevented structurally: the resumed plan excludes
catalog-satisfied instances; byte-identical bodies reconcile to the existing object;
promotion is a no-overwrite hard link. Resume requires, in order: the terminating or
reconstructed accounting, the inspector returning `SAFE`, **and the owner's recorded
resume / new-run / abandonment decision** bound to the predecessor receipt identity (recovery
template §10) — absent that decision, no resume.

### 11.3 Required kill-point tests (T3/T1, all eight)

| # | Injected interruption | Required behaviour |
|---|---|---|
| 1 | Kill before transport construction | Zero attempts consumed; no object, no row; fresh run plans identically |
| 2 | Kill after transport, before object promotion | In-flight request charged at full `A_reachable`; `.part` never treated as complete; quarantine-or-remove per template; no catalog row |
| 3 | Kill after promotion, before catalog commit | Orphan detected; adopted only via the authoritative reconcile path or quarantined; attempts charged conservatively |
| 4 | Kill after catalog commit, before receipt write | Committed rows carry their attempts; in-flight remainder charged at bound; resumed receipt names the predecessor chain correctly |
| 5 | Uncertain durable state (row-without-object) | **`UNDETERMINED`**; resume refused; owner referral |
| 6 | Safe resume | `SAFE`; carried count correct; no duplicate substantive write; satisfied instances excluded |
| 7 | Unsafe resume | `UNSAFE`; resume refused until `m3 recover` applies the deterministic action and a fresh inspection returns `SAFE` |
| 8 | No-headroom resume | Worst-case remainder exceeds remaining ceiling headroom → stop for re-plan and a new exact owner approval; the ceiling is never raised |

## 12. Completion and absence semantics — state mapping (contract §14)

| State | Definition | Catalog record | Receipt | CLI exit | Reason code | Operator output | Public evidence | Owner adjudication |
|---|---|---|---|---|---|---|---|---|
| Terminal classification | Request reached a registered terminal disposition | Row with terminal state | Counted in `response_classification_totals` | — (per-request) | The registered code | Route progress line | none | no — but **never satisfies a request by itself** |
| Satisfied | Validated new object, hash-verified, provenance-complete | Observation row + object | `raw_object_count` | — | none | progress | none | no |
| Reused satisfied | Instance already satisfied in the catalog; not requested | Existing row | `cache_hit_count` | — | none | progress | none | no |
| Required-object absence | 404-absent, quarantined, or terminal failure leaving the required object absent | Terminal row (`INDEX_INSTANCE_UNAVAILABLE` / quarantine / failure code) | Aggregated in `fail`/`quarantine` buckets only | reconcile exits `4` | the registered per-item code | absence enumeration reference | reconciliation report (post-§13 vocabulary) | **YES — express, before freeze and any M3.2B approval** |
| Successful window completion | Every required object present + §14's full conjunction | All rows satisfied | `completion_status="complete"`, reconciled | `0` | none | totals + reconcile `0` | per §13 | no |
| `completed_with_absences` | Terminated, receipt valid, ≥1 unadjudicated absence | As above with absences | run-level `complete` (window state is **not** a receipt value) | reconcile `4` | per-item codes | enumeration | Gate H row + adjudication record | **YES — ineligible for freeze/M3.2B/Gate H until expressly adjudicated** |
| Interrupted | Hard or graceful interruption | Committed rows + recovery events | `interrupted` + `interruption_state` (or absent receipt → §11) | `4` on graceful stop | `SEC_ACQUISITION_INTERRUPTED` | rollback sequence | recovery record | **YES — resume/new-run/abandonment** |
| Failed | Terminal failure of the run | Rows to failure point | `failed` | `4` | the terminal code | failure line | receipt reference | yes (next step) |
| Stopped at ceiling | Equality with planned work remaining | Rows to stop | `stopped_at_ceiling` + `remaining_planned_logical_request_count` | `4` | `SEC_REQUEST_CEILING_EXHAUSTED` | stop line | receipt reference | **YES — re-plan + new exact approval; Gate H failure** |
| Stopped by gate | Pre-transport or mid-run gate refusal | none or rows to stop | `stopped_by_gate` (when a live run began) | `4` | the gate's code | refusal line | — | yes |
| Freeze eligibility | Successful completion only | — | — | — | — | — | frozen identity set (post-§13) | owner freeze step |
| M3.2B-planning eligibility | Freeze complete + transport disabled | — | — | — | — | — | derived reference set (post-§13) | second exact approval |
| Gate H eligibility | Both windows successfully complete or expressly adjudicated | — | — | — | — | — | Gate H checklist | owner sign-off |

**No new reason code is proposed or permitted silently.** Every state above maps to a registered
code; an unregistered condition is stop-and-return S2 for a separately owner-approved registry
change.

## 13. F4 — evidence-index vocabulary recommendation

Current vocabulary (11 types) checked artifact by artifact:

| Artifact | Determination | Recommendation |
|---|---|---|
| Frozen M3.2A bootstrap-object identity set | No existing non-lossy type | **New type `frozen_object_identity_set`** |
| Derived M3.2B reference set | Distinct from the plan it feeds (`request_plan` covers the plan itself) | **New type `derived_reference_set`** |
| Reconciliation report / absence enumeration | No existing type | **New type `reconciliation_report`** |
| Recovery-state report | Existing type **`recovery_state_report`** | **Map — non-lossy, no addition** |
| M3.2A acquisition evidence packet | The master plan §30 packet is a named set of individually typed artifacts | **No aggregate type** — index components individually, as the expected-coverage table already does |

**Gate:** the vocabulary decision (the three additions, or owner-chosen mappings) must be
owner-accepted by an authorized index edit **before the first affected artifact is publicly
indexed, and no later than the T4 preflight boundary** (the freeze artifacts are T4-preflight
evidence for M3.2B). It is **not** part of T2: the template is a prohibited path, this task edits
no template, and the recommendation binds nothing until the owner accepts it.

## 14. Exact test plan

**Files:** new `tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_dependent_plan.py`,
`tests/unit/test_m3_recover.py`; bounded edits `tests/integration/test_m3_cli.py`,
`tests/unit/test_m3_request_plan.py`, `tests/unit/test_m3_recovery.py`,
`tests/unit/test_config.py`. **Byte-identical, mandatory:** `tests/integration/test_no_network.py`
and `tests/conftest.py` (the autouse `_block_network` socket guard covering every test).
Regression-executed unchanged: `tests/unit/test_request_ceiling.py`,
`tests/unit/test_m3_receipt.py`, `tests/unit/test_httpx_transport.py` (running, not skipped).

| Category (owner's list) | File(s) | Stage |
|---|---|---|
| Configuration conjunction | T7, T4 | T2.1 |
| CLI refusals (all six commands) | T4 | T2.1→T2.5 |
| No-network defaults | T4 + suite guard | T2.1 |
| Approved routes / window separation | T1 | T2.3, T2.5 |
| Prohibited routes and filing bodies | T1, T4 | T2.3 |
| Redirects (loop/depth/family/identity) | T1 | T2.3 |
| Ceiling C−1/C/C+1 | T1 (+ existing `test_request_ceiling.py`) | T2.3 |
| Physical-attempt accounting (retries, hops, cooldown continuation) | T1 | T2.3 |
| Retry and cooldown sequencing | T1 | T2.3 |
| Raw-object immutability | T1 | T2.2 |
| Duplicate and hash-conflict | T1 | T2.2 |
| Catalog transaction and orphan | T1 | T2.2, T2.4 |
| Receipt closed-schema + identity-leak (incl. §10.4 controls) | T1, T4 | T2.3 |
| Absence and false-success (`completed_with_absences` refusal; absent ≠ satisfied) | T1, T4 | T2.3, T2.4 |
| Recovery SAFE/UNSAFE/UNDETERMINED + eight kill points | T3, T6 | T2.4 |
| Dependent-plan zero-request derivation | T2, T5 | T2.5 |
| M3.2A/M3.2B separation | T1, T2 | T2.3, T2.5 |
| Operator output and `--show-scope` | T4 | T2.5 |
| Protected-path nonchange | §16 proof (not a pytest) | every stage + T2.6 |
| Suite-level socket guards | `conftest.py` unchanged | continuous |
| Positive controls proving each refusal non-vacuous | every file above | every stage |

**Per-stage targeted sets** are named in each §6 stage. **Complete T3 validation suite:** the full
§15 integrated list.

## 15. Validation strategy

**Every stage:** targeted pytest for touched behaviour; `ruff check` and `ruff format --check`
on touched files; `mypy src`; `make secrets`; `make hygiene`; the protected-path diff
(`git diff --exit-code <stage-baseline> -- <every §5-prohibited path>` empty); zero live SEC
requests (structurally guaranteed by the socket guard).

**Integrated boundary (T2.6, pre-T3):** `ruff check .`; `ruff format --check .`; `mypy src`;
complete `pytest` with the `[sec]` extra installed and `test_httpx_transport.py` **running**;
`make sqlite-check`; `tests/unit/test_migration_provenance.py`; `make secrets`; `make hygiene`;
`make context`; request-plan identity (`19be7bdc…` reproduces); receipt validation over every
fixture receipt; the ceiling stop-before-overflow proof; the no-network proof
(`test_no_network.py` byte-identical and green); the implementation-path proof (the changed-path
set since the T2 baseline ⊆ the §5 allowlist); then the **fresh non-author independent T3
review** (§16).

## 16. T3 freeze, independent review, and owner gates

- **T2 implementation candidate:** the T2.6 commit with every §15 integrated gate green and the
  changed-path proof exact. Its SHA is the **implementation freeze**, recorded in STATUS and the
  completion report; no further implementation byte changes before T3 review.
- **Independent T3 review:** one fresh session that authored none of the M3.2 implementation,
  this packet, or the contract chain — the same independence standard the owner fixed for the
  contract rereview (one session, no subagents, non-authorship attested, every conclusion
  independently re-verified) — producing a durable artifact under `Docs/m3/reviews/` named with
  the frozen SHA. **Findings threshold:** zero BLOCKER and zero unresolved relevant MAJOR to
  recommend acceptance; any BLOCKER or unresolved MAJOR returns the work for bounded correction
  and fresh rereview of the corrected freeze.
- **Owner T3 acceptance:** a separate ChatGPT owner decision recorded as a numbered decision
  (the review recommends; only the owner accepts). **No implementation commit, freeze, review,
  or acceptance grants live authority**: network enablement remains prohibited until the
  separate T4 preflight and the exact per-window T5 instrument, and the §13 vocabulary decision
  must be taken before T4-preflight evidence is indexed.
- **Exact next action after T3 acceptance:** `M3_2_T4_LIVE_OPERATION_PREFLIGHT_PREPARATION` —
  runbook steps 16–18 pre-run state, the owner's off-device-backup decision, and the T5 request,
  each a separate owner-gated step.

## 17. Proposed T2 owner-authorization instrument — NOT ISSUED

```text
OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION: <APPROVED | REFUSED | AMENDED>

The project owner authorizes bounded Milestone 3.2 implementation under the
contract accepted at T1 by Decision 034.

Date: 2026-08-__
Baseline commit for the nonchange proof: <HEAD at issuance>
Contract: Milestones/contracts/m3_2.md (accepted text SHA-256 75e7e5a1...)
Packet: Docs/m3/m3_2_t2_implementation_authorization_packet.md, revision v2
Packet SHA-256: <recorded at issuance>

Authorized paths: exactly the fifteen paths of packet §5 (P1–P8, T1–T7).
The declined surfaces of §5 remain prohibited.

Staging and commits: the six stages T2.1–T2.6 of packet §6, one commit per
stage with the exact §6 subjects, each local until my stage review passes and
pushed fast-forward before the next stage. This clause AMENDS the accepted
contract §22 one-commit default to record this six-commit plan, as §22
requires. [Owner may strike this clause to revert to the single-commit
default with internal stage checkpoints.]

The implementation may NOT: enable network or CompanyFacts or commit any
tracked network.m3_acquire_enabled: true; contact the SEC or place any
request; create or populate the operational catalog outside offline test
fixtures; use the M3.2A ceiling 801 operationally; plan or execute M3.2B;
execute Gate H; create any migration, tag, or schema change; edit the frozen
receipt schema; or widen its own path set (stop-and-return instead).

T3 implementation acceptance, T4 preflight, and each per-window T5 remain
separate later owner acts. This authorization is none of them.

Owner: Joseph Nihill, project owner acting through the ChatGPT owner decision.
A transparent recorded authorization, not a handwritten, cryptographic, or
third-party digital signature.
```

## 18. Negative authority of this packet

This packet does not grant T2 and is not an authorization. It changes no executable byte;
enables no network or CompanyFacts; authorizes no SEC contact, connectivity test, acquisition,
or operational-catalog creation; authorizes no ceiling-801 use, M3.2B work, Gate H, or M3.3+
work; creates no tag; amends no accepted decision, contract, template, or schema; edits no
template and no `Docs/decision_index.md` (whose Decision-029 residue remains open, nonblocking,
and non-authoritative under Decision 033 §5). The formal state is:

```text
M3_2_T2_PACKET_PREPARED_FOR_OWNER_REVIEW
```

**Next action:** `CHATGPT_OWNER_REVIEW_OF_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_PACKET` — the
owner reviews this packet and issues, amends, or refuses the §17 instrument. **No executable
byte changes before that decision.**
