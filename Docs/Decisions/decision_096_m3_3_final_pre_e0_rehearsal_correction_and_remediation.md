# Decision 096 — Final Bounded PRE-E0 Rehearsal Correction and Remediation Authority

**Date:** 2026-08-16
**Status:** ACCEPTED — OWNER FINAL BOUNDED CORRECTION AND SINGLE REMEDIATION AUTHORITY
**Outcome:** `M3_3_D096_FINAL_PRE_E0_CORRECTION_OWNER_ACCEPTED`
**Stage:** M3.3 PRE-E0 executability implementation
**Authority:** Sol/GPT owner adjudication on the user's explicit approval

The exact owner approval for this record is:

> APPROVE Decision 096 final bounded PRE-E0 correction, governance edits, one local governance
> commit, and one fresh Claude Opus 5 Maximum remediation. Preserve Decisions 094-095 production
> semantics and the existing uncommitted work as unaccepted WIP. Widen the executor path union only
> to src/disclosure_drift/m3/execution_rehearsal.py; remove the stale candidate-layer non-canonical
> full-index CIK expectation; require an equivalent pre-association E0 projection mutation proof in
> tests/unit/test_m3_e0.py that fails on invalid_cik_rendering_count without observation/scalar
> fallback or entity invention; correct the R28 bridge attribution to the
> canonical-relation/evidence-digest behavior; complete all remaining D094/D095 deliverables and
> proofs; and permit one local implementation commit only after one successful make check-fast.
> Treat the absent CLI-visible effort flag as a disclosed observability limitation, not an
> invalidation, while requiring a Maximum dispatch and actual claude-opus-5 attestation. No further
> autonomous remediation follows this pass. E0, accepted-catalog migrations, linkage diagnostic,
> private-root access, network/SEC/HTTP, execute-constant activation, push, and tag remain
> unauthorized.

This Decision is the final bounded correction of the implementation and rehearsal boundary in
accepted [Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md), as first corrected by
accepted [Decision 095](decision_095_m3_3_d094_bounded_correction_and_remediation.md). It changes no
production transition, membership, candidate, receipt, identity, recovery, privacy, or freeze
semantic. It executes no catalog transition and no E0 operation.

## 1. Entry state and Decision-095 remediation evidence

### 1.1 Repository state

The Decision-095 remediation entered and stopped at exact local governance HEAD
`4643e57e3d296ac546ff720963499bbd76c0dee9`, tree
`924b6f034f544da5eaea6dafe7366d9f8308fb92`, parent
`437d40a41fc95b26ee212728b87d06e919cbe5a7`, on `main`, two commits ahead of and
zero behind recorded `origin/main` `4ed0fc7f67c3f9b4f5750e7c24432269aed9ffc4`.

The fresh ACP session was
`agent:claude:acp:df4d5b19-208b-4048-959e-4a2368d8162b`, run
`49d25bce-7d98-41d7-818d-3a9d21a0fad3`. The harness artifacts attested actual model
`claude-opus-5`, a fresh non-resumed session, and no delegation. The run returned
`M3_3_D095_REMEDIATION_BLOCKED`, created no commit, staged nothing, and left HEAD and its tree
unchanged.

The preserved uncommitted work now consists of exactly ten unstaged tracked files plus one
untracked file:

| Path | SHA-256 |
|---|---|
| `src/disclosure_drift/cli.py` | `e11c1274e8122b235bcbc6ddfe8f2e0657999b7926576f1f11769e2da80fdffd` |
| `src/disclosure_drift/config.py` | `719c83b4c6377a3f37ed798651cdad24bb5f031af5f7215ed4ea7a1fef7c6981` |
| `src/disclosure_drift/m3/candidate_snapshot.py` | `927043e7dc8ec19a6eb031b800b18fd9987925be7f30d164c1438621c3551cfa` |
| `src/disclosure_drift/m3/offline_parse.py` | `4cd022a826a970b40a0982909fa4c5d45cf7428bdc8af0a000557812682ef269` |
| `src/disclosure_drift/m3/receipt.py` | `9b358ed00de5779683be2cb91b52bf90d144ede0ac3322d6bd1980d2bcb7f81d` |
| `src/disclosure_drift/m3/rehearsal_world.py` | `16398c7aad4615bfd734d3c60deb5ac85e20be8fb74a9cda9d7319caf4fa799b` |
| `tests/unit/test_m3_3_execution.py` | `55dd1240f20db680ffce72ab3effb0c8f2a6a1de743fb7fa80066134a618e1e7` |
| `tests/unit/test_m3_candidate_snapshot.py` | `42ebc4c6f5193e385b08176703e3379dfcccc5c517ec60465ebebd77c26fbeca` |
| `tests/unit/test_m3_offline_parse.py` | `92651cd0c9c5759f11f74398b83720634bd9bc29d5fd29e3872f595128d5eeb5` |
| `tests/unit/test_m3_receipt.py` | `16e57f58dbc92e87245ea9c683d26e0e6cd65208aa8196db85908ca6a1ce1b9c` |
| `src/disclosure_drift/m3/e0.py` | `a848e4a9bbdcf6343d624d5a4469c5ece212d55475750e2fef7f75bd6cca8db1` |

These bytes are **unaccepted, unreviewed work in progress**, not a candidate, baseline, or frozen
identity. The final remediation may inspect, retain, rewrite, or discard hunks only inside the
authorized path union and only after independently deriving them from Decisions 094–096. Their
existence, prior static checks, and prior executor report prove neither completeness nor
correctness.

### 1.2 Reproduced blocker

Sol/GPT independently reran the complete `tests/unit/test_m3_3_execution.py` module against the
preserved tree with the evidence-root variable unset and deterministic plugin ordering. The exact
result was 79 passed / 4 failed. The four failures are:

1. the R28 adversarial full-index observation mutation still expects a `multi_registrant`
   violation, but the bridge reports row-presence differences and
   `candidate_accession_evidence_sha256`;
2. the E2 `_corrupt_full_index_cik` variant expects a candidate-snapshot refusal naming
   `non-canonical CIK`, but the canonical consumer correctly does not reread the mutated
   observation after the relation is materialized;
3. the whole E1–E8 rehearsal fails only because that E2 variant fails; and
4. the rehearsal CLI consequently returns gate-failure exit `4`.

The same invalid full-index `cik_padded` mutation, applied before association projection, was
measured to fail in `materialize_census_associations()` with
`invalid_cik_rendering_count`. The invariant remains load-bearing; Decision 094 moved its owner
from candidate derivation to the pre-association E0 projection.

The Decision-095 run also left `tests/unit/test_m3_e0.py`, five executable documentation
deliverables, several direct proof modules, and the final full gate incomplete. It ran no
`make check-fast` and created no implementation commit.

## 2. Authority, precedence, and bounded disposition

Decision 094 remains controlling for every production semantic. Decision 095 R79–R81 remains
controlling for the truthful synthetic support entities, central non-override runtime-root
recognition, and source-local catalog constant. This Decision changes only:

1. the layer that owns the malformed full-index CIK negative proof;
2. the expected R28 attribution of an already-materialized canonical-relation adversarial case;
3. one exact executor-path addition;
4. the effort-observability disposition; and
5. the authority for one **final** user-approved remediation epoch.

This Decision supersedes Decision 095 R82 only on that path/sequencing/observability boundary.
Nothing here accepts any existing WIP byte or reopens Decision 094 §6.2, §6.5, §9.5, §11, or its
production architecture. If an apparent conflict lies outside these exact points, Decision 094 or
Decision 095, as applicable, controls and the executor stops for Sol/GPT.

## 3. Ruling R83 — move the malformed-full-index proof to its E0 owner

Decision 094 §6.5 is preserved: after the canonical association relation and completeness state
exist, candidate and linkage consumers read only that relation and state. They never reread
`census_accession_observations`, fall back to a scalar, infer an anchor, or invent an entity.

Therefore the pre-Decision-094 E2 candidate-layer expectation is removed:

1. `src/disclosure_drift/m3/execution_rehearsal.py` no longer includes the
   `non-canonical full-index CIK` / `_corrupt_full_index_cik` variant among candidate-snapshot
   freeze-refusal obligations;
2. its now-unused helper may be removed;
3. `tests/unit/test_m3_3_execution.py` no longer expects that candidate-layer refusal; and
4. every other E2 obligation and all eight scenario executions remain required.

This is not deletion of the invariant. `tests/unit/test_m3_e0.py` must add an equivalent, stronger
pre-association E0 projection mutation proof that:

1. constructs a disposable accepted-shaped catalog at the boundary after plan-bound parsing,
   full-index observation materialization, and canonical accession resolution but **before**
   `materialize_census_associations()`;
2. has a positive control in which the canonical full-index membership input projects with
   `invalid_cik_rendering_count = 0`;
3. mutates exactly one plan-bound accepted full-index `cik_padded` membership observation to an
   invalid rendering before projection;
4. invokes the production association projection through the E0-owned boundary and fails closed
   with `OfflineParseError` naming exactly `invalid_cik_rendering_count`;
5. proves the failed transaction does not persist an established association projection or an
   invented `census_registrants` entity; and
6. never invokes the candidate builder, observation fallback, scalar fallback, anchor inference,
   or manual entity creation.

The positive and adversarial controls must share every input except the isolated rendering
mutation. A test that succeeds because some unrelated precondition is absent is vacuous and does
not satisfy this ruling.

## 4. Ruling R84 — correct R28 attribution to canonical relation plus evidence digest

R28 remains an explicit allowlist and must still reject a Track-B snapshot rebuilt over divergent
census input. The post-projection adversarial mutation in
`test_the_bridge_fails_on_any_unrelated_difference` is attributed as follows:

1. `multi_registrant` remains derived from the already-materialized canonical relation and must
   **not** change merely because a source observation is later altered;
2. the source-evidence change propagates through the candidate evidence identity, so the bridge
   must fail with a violation of `candidate_accession_evidence_sha256`;
3. row-presence violations may accompany the evidence-key movement, but they are not a substitute
   for the required digest attribution; and
4. the test must assert both that `candidate_accession_evidence_sha256` is present and that the
   stale `multi_registrant` attribution is absent.

No edit to `src/disclosure_drift/m3/rehearsal_snapshot.py` is authorized or needed. The bridge
comparison, its allowlist, and its fail-closed result remain unchanged.

## 5. Ruling R85 — Maximum dispatch with disclosed CLI observability limitation

The final remediation must be dispatched through ACP as one genuinely fresh Claude Opus 5 session
with the parent dispatch setting `thinking = max`. Before substantive reading, tests, or mutation,
the executor must attest the actual running harness/model identifier as exactly
`claude-opus-5`. A configured default, requested name, fallback chain, `/model`, or `/clear` is not
proof. If the actual model differs or cannot be truthfully attested, it stops without mutation.

The current Claude CLI does not expose the parent effort setting on its process arguments,
environment, project settings, or transcript. Absence of a CLI-visible effort flag is an accepted,
disclosed observability limitation and **does not invalidate** an otherwise correct Maximum
dispatch with actual-model attestation. The executor must report the limitation truthfully and
must not fabricate an observed effort value.

No subagent, workflow, second reasoning model, competing session, parallel implementation,
recursive review, or competing worktree is authorized.

## 6. Ruling R86 — one final bounded remediation

### 6.1 Exact executor path union

The executor may edit only the union of:

1. Decision 094 §12.1;
2. Decision 095 §6.2; and
3. exactly this one additional path:

```text
src/disclosure_drift/m3/execution_rehearsal.py
```

`tests/unit/test_m3_3_execution.py` is already enumerated by Decision 095; this Decision extends
its purpose only to the exact R83/R84 assertion corrections. `tests/unit/test_m3_e0.py` is already
authorized by Decision 094 and is the required home of R83's relocated proof. The newly added
`execution_rehearsal.py` authority is limited to removing the stale E2 variant, its unused helper,
and directly corresponding comments or registry text; it is not a broader rehearsal redesign. No
other path is added by this Decision. In particular,
`src/disclosure_drift/m3/rehearsal_snapshot.py`, migrations,
`reasons.py`, `release/hashing.py`, acquisition, census orchestration, transport, network
configuration, accepted evidence, and every historical Decision remain outside the executor set.

Decision, STATUS, contract, registry, index, architecture map, master plan, and other governance
surfaces remain Sol-owned and read-only to Claude.

### 6.2 Full completion, not a four-test patch

The executor must complete the full Decision-094 §§5–11 implementation, all thirteen Decision-094
§12.3 proof families, every Decision-095 §7 proof, and R83/R84 above. This includes completing or
truthfully dispositioning every still-missing direct surface from the Decision-095 report:

```text
tests/unit/test_m3_e0.py
Docs/m3/e0_execution_record_spec.md
Docs/m3/execution_receipt_spec.md
Docs/m3/operator_runbook.md
Docs/sec_data_dictionary.md
Docs/change_impact_map.md
src/disclosure_drift/m3/__init__.py
tests/integration/test_m3_cli.py
tests/unit/test_migration_provenance.py
tests/unit/test_m3_rehearsal.py
tests/unit/test_env_overrides.py
tests/unit/test_config.py
tests/unit/test_cohorts.py
tests/unit/test_sec_user_agent.py
tests/integration/test_cli.py
```

An authorized file need not change merely for ceremony, but every required behavior and mutation
proof must have a direct durable test, and every named executable document must describe the final
implemented contract rather than WIP. A missing required proof, placeholder, untested branch,
stale count, or unimplemented accepted state is a blocker.

Both activation constants must exist and remain exactly:

```python
PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None
M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None
```

Both execute modes must return exit `3` regardless of environment-value presence, preflight or
verify result, catalog state, receipt, namespace, or CLI flag. Tests may use only disposable
temporary catalogs and synthetic temporary roots. No test may open or resolve the accepted private
root or accepted catalog.

### 6.3 Validation and commit law

Use repository Python 3.12, targeted tests while editing, the final touched-code map, and bounded
mutation/non-vacuity proofs. On the complete final tree run one successful:

```text
make check-fast
```

Do not run `make stage-gate`. Repeat an expensive full gate only after a concrete relevant failure,
consequential correction, or nondeterminism. A known failure is reported as failure, never hidden
with a skip, deletion, relaxed assertion, or xfail.

If and only if the implementation and executable documentation are complete, every required proof
passes, and final `make check-fast` succeeds, exactly one local implementation commit is
authorized:

```text
feat: implement Decision 094 pre-E0 execution surfaces
```

The commit may contain only authorized executor paths. Push, tag, branch, worktree, stash, amend,
rebase, force operations, release, and publication remain unauthorized. On any blocker or failed
required gate, preserve the exact worktree, create no success commit, and report the failure.

### 6.4 Finality of this remediation authority

This is the final autonomous implementation/remediation pass. No further correction, continuation,
second executor, or reviewer-driven implementation is implicitly authorized after it. If it returns
blocked, fails validation, or a later owner review finds a consequential defect, Sol/GPT stops and
returns an explicit disposition to the user; it does not launch another repair epoch.

## 7. Governance commit

The owner authorizes one local governance commit containing this Decision and its necessary
navigation/current-state overlays. Only governance files may be staged for that commit; all §1.1
WIP remains unstaged and unaccepted. The commit message is:

```text
docs: accept Decision 096 final pre-E0 correction
```

The later implementation commit is separate under §6.3. Neither commit may be pushed or tagged.
Historical Decisions and evidence artifacts are not rewritten.

## 8. Review and acceptance boundary

A Claude success token is implementation evidence only. It does not accept the implementation,
activate either constant, authorize a catalog transition, apply a migration, start E0, run the
linkage diagnostic, grant linkage credit, or progress the stage.

Sol/GPT must verify the actual model, entry and final Git states, path containment, final gate,
R83/R84 non-vacuity, every Decision-094/095 proof family, receipt compatibility, identities,
recovery, private nonleakage, both disabled constants, and the absence of prohibited acts. The
fresh read-only independent-review boundary in Decision 094 §12.4 remains an owner-controlled later
step; it may review a completed candidate but may not edit it, accept it, or trigger another
remediation under this Decision.

## 9. Acts still prohibited

This Decision does **not** authorize:

- discovering, resolving, opening, naming, printing, logging, or inferring the accepted private
  evidence root or opening the accepted operational catalog;
- applying accepted-catalog migrations `0014` or `0015`, creating `0016`, or editing any migration;
- enabling either execute activation constant;
- running the catalog transition, E0, the Decision-093 linkage diagnostic, the persistence bridge,
  E1, E2, or M3.4;
- SEC, HTTP, DNS, sockets, network, acquisition, reacquisition, package installation, or remote
  fetch; logical request ceiling and physical-attempt ceiling both remain zero;
- changing production membership, candidate, linkage, quota, evidence, receipt, identity,
  recovery, privacy, or freeze semantics;
- push, tag, release, publication, or owner acceptance by the executor.

## 10. Exact next action

1. Commit this accepted governance record and its current-state overlays locally without staging
   the preserved WIP.
2. Dispatch one fresh actual-model-attested Claude Opus 5 remediation with parent effort set to
   Maximum under R83–R86.
3. Return the completed or blocked result to Sol/GPT for independent verification.
4. Launch no further autonomous remediation and do not migrate or run E0.

`RESULT_TOKEN: M3_3_D096_FINAL_PRE_E0_CORRECTION_OWNER_ACCEPTED`
