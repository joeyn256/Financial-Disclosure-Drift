# Decision 099 — Post-D098 Bounded Correction and Final PRE-E0 Acceptance Boundary

```text
STATUS: ACCEPTED — OWNER-AUTHORIZED EXCEPTIONAL BOUNDED CORRECTION
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT technical ruling
OUTCOME: M3_3_D099_POST_D098_BOUNDED_CORRECTION_AUTHORIZED
CORRECTION_BASELINE: e4950cc9b0466e3b08436ae81508475627ba8860
REJECTED_IMPLEMENTATION_BASELINE: 1e200218be82702e55396a5afab579203a1545a9
PRE_E0_IMPLEMENTATION_ACCEPTANCE: PENDING CORRECTION, PROOF, AND SOL REVIEW
M3_3_E0_OPERATIONAL_STATE: HELD
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: NO
M3_3_E0_EXECUTION_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

Joey explicitly authorizes the one post-Decision-098 correction. This is that correction
instrument. It preserves Decisions 094–098 and the clean, unpushed implementation candidate those
records produced, corrects the two Decision-098 MAJOR findings and the directly implicated frozen
contract defects, and creates no new architecture or provenance method.

This is the final PRE-E0 implementation correction. Optional cleanup remains deferred. A passing
gate authorizes no private-root access, migration, transition, or E0 by itself.

## 1. Ruling R95 — preserved baseline and exact objective

The correction starts from repository HEAD
`e4950cc9b0466e3b08436ae81508475627ba8860`, tree
`a00f88f9bdc1d8306e7c89f60d43aa1e2f772e74`. Its embedded implementation candidate remains the
Decision-097 commit `1e200218be82702e55396a5afab579203a1545a9`, tree
`7d5f3aa9ba9b84c8fe041d0e9f8c8cd12f0133cd`.

The correction objective is exactly:

1. make every handled transition/E0 failure terminal conform to the durable event ledger that
   conditions its permitted fields;
2. implement Decision 094 §5.2 predicate 3 in transition preflight and the under-lease recheck by
   validating the accepted M3.2 T7 completion receipt, its T6 predecessor chain, and their exact
   catalog binding;
3. correct the four Decision-098 MINOR findings only where they directly implement frozen
   Decision-094 requirements; and
4. prove the corrected target and, on success, permit Sol/GPT to owner-accept the PRE-E0
   implementation without another opinion or optimization pass.

Decisions 094–097 production semantics remain unchanged. In particular, the canonical relation,
complete association set, no-fallback/no-entity-invention rules, Decision-096 R83 mutation proof,
Decision-097 M19 disposition, sixteen-table write set, source-bound disabled execute constants,
forward-only recovery law, and non-self-referential identity rules all remain binding.

## 2. Ruling R96 — durable-event-derived failure terminals

Decision 098 R91 is corrected by one rule: before `_freeze()` writes a failed or interrupted
terminal, the implementation reads and fully verifies the durable event ledger and derives the
terminal's permitted conditional field set from the event types actually present there. In-memory
assignment is never evidence that an event became durable.

The derivation covers every event-conditioned group, not only the two reproduced examples:

| Kind | Field/group | Permitted on failure only when durable |
|---|---|---|
| transition | `backup` | `BACKUP_VERIFIED` |
| transition | `post_preexisting_content_sha256` | `POSTCHECK_PASSED` |
| E0 | `backup` | `BACKUP_VERIFIED` |
| E0 | `association_totality` | `ASSOCIATIONS_MATERIALIZED` |
| E0 | `table_hashes`, `plan_parser_state_hash`, `e0_catalog_state_sha256`, `post_integrity` | `VALIDATION_PASSED` |

Catalog-observed transition and E0 fields that Decision 094 conditions on
`failure.catalog_state_observed` remain governed by that exact condition. The accepted
commit-before-event transition exception remains only in its already-frozen interruption state and
is not widened.

If the durable ledger itself is truncated, malformed, or otherwise unverifiable, the implementation
must not manufacture a terminal over it. The surviving artifacts remain
`UNDETERMINED / NOT COMPLETE`, as Decision 094 already requires.

Load-bearing tests must inject failure at each conditioning-event append boundary, reopen the
persisted failure terminal through the production loader, and prove the corresponding field group
is absent when its event is absent and present when its event is durable. Removing the
ledger-derived pruning must make the tests fail.

## 3. Ruling R97 — exact M3.2 completion-receipt/catalog binding

Decision 094 §5.2 predicate 3 is implemented as a source-local, strictly read-only validation in
`m3/e0.py`. It reuses the accepted low-level receipt loader and Decision-063 predecessor resolver
from `m3/receipt.py`; it does not import or call `m3/recovery.py`, `m3/acquisition.py`, a request-plan
builder, source registry, client, transport, socket, HTTP library, or SEC route.

The production binding is fixed to the accepted M3.2 evidence:

| Fact | Required value |
|---|---|
| T7 receipt path | `runs/m3_2_decision_062_sic_continuation/execution_receipt.json` |
| T7 file SHA-256 | `ae8ace5dc62155c9dca395af238290b0bb5b99dc4e3f1741e3d8ff1c9ab9c3dd` |
| T7 receipt id | `7d72a5501f66d36af9024b80a64060668da315b8880fb5add028917d36ad12e1` |
| T7 run id | `m3-2-acquisition-b6f8bc7f48b94e6080038db575b204e5` |
| T7 completion | `complete`; `M3.2A`; one logical request; one physical attempt |
| T7 plan SHA-256 | `f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a` |
| T7 accepted observation | `6e9d92c859bc48faa6c1c5e47c36fd8e` bound to the T7 run |
| T6 receipt path | `runs/m3_2a_clean_carry_in/execution_receipt.json` |
| T6 file SHA-256 | `0278c857d7816a79907068513fe09d5b78fc3973ba415149fbc9d73605b5359c` |
| T6 receipt id | `37dd811497d4a57e8b911917ed6c0426a22f443c3ddd5aeba8d4da3e076f6a7c` |
| T6 run id | `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44` |
| T6 completion | `failed`; immutable predecessor |
| T6 plan SHA-256 | `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` |
| Exact chain | T7 → T6 → root; no missing, substituted, extra, ambiguous, or cyclic receipt |
| Cumulative accounting | exactly 77 physical attempts including the root carry-in once |

Both receipt files must be regular, non-symlink files under the accepted root; their stored bytes
must match the fixed SHA-256 values; `inspect_receipt()` must validate their closed schema,
canonical bytes, and self-derived identities; and the T7 predecessor id must resolve through the
accepted Decision-063 resolver to the exact T6 receipt.

For each receipt, the fixed catalog must contain exactly the accepted run row at the fixed run id,
with `job_kind = 'm3_2_acquisition'`, the receipt's acquisition window, the truthful terminal job
state, and boundary instants exactly equal to the receipt. The run's durable
`ops_retrieval_attempts` count must equal that receipt's `actual_physical_attempt_count`. The exact
accepted T7 observation must exist and be attributed to the T7 run. Zero matching rows, duplicates,
state/timestamp/count disagreement, a wrong observation attribution, or any receipt/chain mismatch
refuses. Catalog integrity remains independently required by predicate 6.

This exact binding runs in both transition preflight and the under-lease recheck. It reports only
non-secret enums/counts/digest prefixes or fixed public relative names; no private absolute path is
rendered. Disposable tests may replace the fixed pins only in memory to construct a synthetic
accepted-shaped chain; the shipped source retains the exact accepted pins above.

## 4. Ruling R98 — direct disposition of Decision-098 MINOR findings

| Finding | Disposition |
|---|---|
| MINOR-1, preflight overclaim | Corrected by R97; the docstring may claim every predicate only after predicate 3 is genuinely present |
| MINOR-2, verify omits catalog state | Correct: transition and E0 `verify` must strictly read the fixed catalog, compare current chain and integrity with the terminal, compare the transition's persisted content identity when available, and for E0 independently reproduce the persisted governed-state identities when available. A post-freeze catalog mutation must make verify fail |
| MINOR-3, English-substring lease filtering | Correct structurally: the shared preflight takes an explicit lease-check policy, and the under-lease recheck omits only predicate 9 through that typed/control-flow choice, never by filtering refusal text |
| MINOR-4, namespace parent | Correct exactly: the `runs/` parent must already exist, be a real non-symlink directory, and be owned by the effective operator before preflight passes |

No Decision-098 optimization is authorized. The duplicate unbindable-establishment condition remains
deferred. No package import cleanup or unrelated documentation cleanup is part of this correction.

## 5. Exact implementation paths

The fresh executor may edit only:

```text
src/disclosure_drift/m3/e0.py
tests/unit/test_m3_e0.py
Docs/m3/e0_execution_record_spec.md
Docs/m3/operator_runbook.md
Docs/change_impact_map.md
```

No migration, receipt/recovery/acquisition module, CLI, configuration, mutation runner, historical
artifact, accepted evidence export, contract, decision, review artifact, or unrelated test may be
edited by the executor. The governance recording paths for this Decision are separate from the
executor path union and are committed before dispatch.

## 6. Model, epoch, and two-system accountability

Use one genuinely fresh Claude Opus 5 session at Maximum effort. Before any substantive repository
work, its first output line must attest exactly:

```text
ACTUAL_MODEL: claude-opus-5
```

The absent CLI-visible effort flag remains the accepted Decision-096 R85 observability limitation;
Maximum must still be requested at dispatch. A different actual model stops before substantive
work. No subagent, second Claude, parallel reviewer, workflow, branch, or worktree is authorized.

Claude must challenge unsafe or contradictory mechanics, but may not replace R96–R98. Sol/GPT must
reject over-engineering, vacuous tests, scope expansion, weak recovery, and unsupported claims.
Evidence controls.

## 7. Required targeted and mutation proof

Before the full gate, the executor must run the closest unit tests and touched-file static checks.
The targeted evidence must prove at least:

1. all R96 conditioning-event failure windows produce a persisted failure terminal accepted by the
   production loader whenever the ledger itself remains valid;
2. deleting the durable-event projection or keeping any pre-event field makes the proof fail;
3. the exact two-receipt chain and catalog binding pass on a disposable accepted-shaped fixture;
4. wrong/missing/ambiguous receipt, wrong file digest/id/predecessor, chain extension/cycle, wrong
   run state/window/timestamps, attempt-count disagreement, wrong T7 observation attribution, and
   cumulative count other than 77 each refuse;
5. the same binding is rerun under the held lease, while predicate 9 alone is structurally omitted;
6. a missing/symlinked/wrong-owner namespace parent refuses;
7. transition and E0 verify detect a post-freeze catalog-state/identity mutation;
8. preflight and verify remain read-only and leak no private path;
9. the Decision-096 pre-association `invalid_cik_rendering_count` mutation proof and Decision-097
   37-live-plus-M19-superseded audit proof remain present and passing; and
10. both shipped execute constants remain exactly `None` and both execute modes still return 3.

A passing nominal test is insufficient if deleting the intended guard leaves it passing. Bounded
monkeypatch or source mutation is acceptable; no tracked mutation artifact is created.

## 8. Validation and one correction commit

After targeted proof passes, run exactly one final:

```text
make check-fast
```

Do not rerun it on an unchanged failing tree. One local implementation correction commit is
authorized only if targeted proof passes, `make check-fast` passes completely, both execute
constants remain `None`, the exact path ceiling is satisfied, and the tree is otherwise acceptable.
Its exact subject is:

```text
fix: close Decision 098 PRE-E0 review findings
```

No push, tag, amend, rebase, force operation, stash manipulation, migration, or private-state
operation is authorized.

## 9. Corrected-target review and acceptance boundary

No additional independent reviewer or opinion pass follows this bounded correction. Decision 098
already supplies the independent review that identified the exact defects; Joey's milestone-first
instruction rejects another optimization/architecture/second-opinion stage. The corrected-target
review evidence is the fresh executor's exact diff and targeted mutation results, the single full
gate, and Sol/GPT's direct independent inspection of the changed bytes and Git state.

If any BLOCKER, MAJOR, failed required proof, nondeterminism affecting acceptance,
migration/recovery-safety failure, provenance/durability failure, or frozen-contract violation
remains, stop and return to Joey. There is no further automatic correction.

If none remains, Sol/GPT may issue
`M3_3_D099_PRE_E0_IMPLEMENTATION_OWNER_ACCEPTED`. MINOR, OBSERVATION, and OPTIMIZATION findings do
not delay progression unless they directly violate a frozen acceptance requirement. Once accepted,
stop optimizing this stage and proceed immediately to the separately governed transition/E0
sequence already required by Decision 094 §4 and §12.4. Acceptance does not itself activate either
constant or authorize the accepted-catalog transition.

## 10. Governance recording

Sol/GPT may record this Decision and its seven current-state navigation overlays in one local
governance commit before executor dispatch, with exact subject:

```text
docs: authorize Decision 099 PRE-E0 correction
```

That commit changes no source, test, migration, configuration, accepted evidence, historical
Decision, review artifact, or private state. It is separate from the one conditional implementation
correction commit in §8.

## 11. Acts still prohibited during this correction

No accepted private-root discovery or access; no accepted-catalog open; no migration `0014`, `0015`,
or `0016`; no transition; no E0; no linkage diagnostic; no persistence bridge; no E1, E2, or M3.4;
no activation-constant change; no network, SEC, HTTP, DNS, socket, acquisition, package installation,
fetch, pull, push, or tag; no receipt/evidence rewrite; and no history rewrite.

```text
RESULT_TOKEN: M3_3_D099_POST_D098_BOUNDED_CORRECTION_AUTHORIZED
NEXT_ACTION: RECORD GOVERNANCE, THEN ONE FRESH ATTESTED CLAUDE OPUS 5 MAXIMUM CORRECTION
M3_3_E0_OPERATIONAL_STATE: HELD
```
