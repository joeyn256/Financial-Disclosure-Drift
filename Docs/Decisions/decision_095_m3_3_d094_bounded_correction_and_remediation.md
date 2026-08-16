# Decision 095 — Decision 094 Bounded Correction and Remediation Authority

**Date:** 2026-08-15
**Status:** ACCEPTED — OWNER BOUNDED CORRECTION AND SINGLE REMEDIATION AUTHORITY
**Outcome:** `M3_3_D095_BOUNDED_CORRECTION_OWNER_ACCEPTED`
**Stage:** M3.3 PRE-E0 executability implementation
**Authority:** Sol/GPT owner adjudication on the user's explicit approval

The exact owner approval for this record is:

> APPROVE D095 bounded correction, governance edits, one local governance commit, and one fresh
> Claude Opus 5 Maximum remediation. Preserve D094 §6.2/M6 fail-closed semantics; correct only the
> synthetic co-registrant fixture; centrally recognize DISCLOSURE_DRIFT_EVIDENCE_ROOT as a
> non-override runtime root; and permit the e0.py catalog-path restatement with an equality test.
> E0, accepted-catalog migrations, linkage diagnostic, network/SEC/HTTP, execute-constant
> activation, push, and tag remain unauthorized.

This Decision is a bounded correction of the implementation authority in accepted
[Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md). It does not amend Decision 094's
production methodology, schema, transition design, write footprint, identities, recovery law, or
freeze law. It executes nothing.

## 1. Entry state and first-run evidence

### 1.1 Repository state

The Decision-094 implementation run entered at exact clean HEAD
`437d40a41fc95b26ee212728b87d06e919cbe5a7`, tree
`75f139c16fa0833b062574bf8cd775e88021055b`, parent
`4ed0fc7f67c3f9b4f5750e7c24432269aed9ffc4`, on `main`, one commit ahead of the recorded
`origin/main`. It returned
`M3_3_PRE_E0_REDESIGN_IMPLEMENTATION_BLOCKED` and created no commit.

The preserved working tree contains exactly these two unstaged, uncommitted source edits:

| Path | SHA-256 | Diff |
|---|---|---:|
| `src/disclosure_drift/m3/candidate_snapshot.py` | `927043e7dc8ec19a6eb031b800b18fd9987925be7f30d164c1438621c3551cfa` | +75 / -85 |
| `src/disclosure_drift/m3/offline_parse.py` | `a273ce45130771e11dd374ae06bacaac1d97911a6ce09721263d32d8299e88f3` | +696 / -7 |

Those bytes are **unreviewed work in progress**, not an implementation candidate, accepted baseline,
or frozen identity. The remediation may inspect, reuse, rewrite, or discard individual hunks only
after independently deriving and validating them against Decisions 094–095. It must not treat their
presence as evidence of correctness.

### 1.2 Finding F1 — synthetic co-registrant fixture conflict

The first executor measured the clean-HEAD targeted baseline at 238 passed / 0 failed. With the
preserved Decision-094 §6 implementation, the same bounded set collected one additional
sixteen-table parameter and returned 208 passed / 31 failed. Twenty-one failures are ordinary
expected Decision-094 test corrections within the original path set. Ten failures share one
fixture-level cause outside that set.

The synthetic rehearsal's two joint filings have substantive co-registrant CIKs `917` and `918` in
the accepted-shaped `company.idx`, but the fixture supplies submissions documents only for CIKs
`1`–`20` and `101`–`104`. Therefore `census_registrants` has no row for `917` or `918`. Decision 094
§6.2 condition 3 and §13 M6 correctly require both accessions to fail closed as unbindable; the hard
`multi_registrant_accessions = 2` quota then becomes genuinely infeasible.

The executor's disposable in-memory control added one accepted-shaped submissions entity for each
of `917` and `918` without changing the production rule. It restored exactly: established
multi-registrant accessions 2, unestablished accessions 0, unbindable members 0, candidate
multi-registrant accessions 2, associated candidate rows 4, and feasible selection. This establishes
the correction's sufficiency; it does not accept the preserved source implementation.

### 1.3 Finding F2 — required runtime variable rejected

Decision 094 §7.1 requires `DISCLOSURE_DRIFT_EVIDENCE_ROOT`. The central configuration loader
currently rejects every unrecognized `DISCLOSURE_DRIFT_*` name before command dispatch. A disposable
probe with a synthetic value therefore returned configuration exit `1` before any root resolution.
The required variable is a runtime root, not a configuration override, but it is absent from
`RUNTIME_ROOT_ENV_VARS` and consequently from `RECOGNIZED_ENV_VARS`.

### 1.4 Finding F3 — fixed catalog constant behind a prohibited import boundary

The accepted catalog-relative value is
`catalogs/m3_2a_operational.sqlite3`, currently defined as
`OPERATIONAL_CATALOG_RELATIVE_PATH` in `src/disclosure_drift/m3/acquisition.py`. Decision 094
forbids the new E0 surface from importing an acquisition orchestrator. The value must remain exact
without creating that import edge.

## 2. Authority and precedence

Decision 094 remains controlling except for the exact implementation-boundary corrections stated
here. In particular:

1. Decision 094 §6.2 condition 3 and §13 M6 remain byte-for-byte authoritative in meaning;
2. the R58/R59 fail-closed rule, no-invented-entity rule, hard quota, sixteen-table footprint,
   transition, operator, receipt, terminal, identity, recovery, and freeze contracts are unchanged;
3. Decision 094 §12.1's executor path set is widened only by §6.2 below;
4. Decision 094's first implementation epoch is complete with a blocked result; this Decision
   authorizes the one normal bounded remediation contemplated by Decision 094 §12.4 and AGENTS.md;
5. no finding from the blocked run is promoted to owner acceptance of the preserved code.

If this Decision and Decision 094 appear to conflict outside these exact corrections, Decision 094
controls and the executor stops for Sol/GPT.

## 3. Ruling R79 — preserve production fail-closed semantics; correct only the fixture

Decision 094 §6.2 condition 3 is **PRESERVED**: every member of the prospective association union
must already have a persisted `census_registrants` row. A full-index-only member with no such row
remains unbindable, no entity is invented, completeness remains `unestablished`, and R59 blocks
candidacy.

The synthetic base-case fixture is corrected instead:

1. CIKs `917` and `918` each receive exactly one accepted-shaped
   `sec_submissions_entity` stored object in the disposable rehearsal world;
2. each is a support-only synthetic registrant with a canonical CIK and name and **zero filings of
   its own**; no accession, quota witness, event, or selection candidate is invented for it;
3. the existing `company.idx` remains the only source that associates `917` with accession
   `000000001725000001` and `918` with accession `000000001825000001`;
4. the production offline parser, not hand-written SQL, creates the two `census_registrants` rows;
5. production code remains forbidden to synthesize a missing registrant from a full-index row;
6. the correction is fixture-only, zero-network, disposable, deterministic, and source-order
   independent.

The corrected base case must mechanically reconcile to:

```text
census_accessions                              65
census_registrants                             26
established_accessions                         65
unestablished_accessions                        0
established_singleton_accessions               63
established_multi_registrant_accessions         2
substantive_association_rows                    67
unbindable_registrant_members                    0
candidate_multi_registrant_accessions            2
candidate_associated_rows                        4
hard multi_registrant_accessions quota      feasible
```

Removing either support-only submissions object must fail its corresponding joint accession closed;
the test must prove this negative control rather than merely assert the positive counts.

## 4. Ruling R80 — centrally recognized non-override evidence root

`DISCLOSURE_DRIFT_EVIDENCE_ROOT` is a recognized runtime root under the central configuration
contract:

1. `src/disclosure_drift/config.py` defines the exact public constant
   `EVIDENCE_ROOT_ENV: Final = "DISCLOSURE_DRIFT_EVIDENCE_ROOT"`;
2. `EVIDENCE_ROOT_ENV` is included in `RUNTIME_ROOT_ENV_VARS`, and therefore in
   `RECOGNIZED_ENV_VARS`;
3. it is **not** included in `ENV_OVERRIDES`, `SECRET_ENV_VARS`, tracked YAML, a Pydantic model, a
   configuration fingerprint, a repr, a receipt value, a log record, or CLI output;
4. `load_config` recognizes the name but does not read, normalize, persist, or apply its value;
5. only the Decision-094 operator surface resolves the value, once per process, through the accepted
   external-root boundary and caches the resolved reference;
6. every other unknown `DISCLOSURE_DRIFT_*` name remains rejected exactly as before;
7. filtering or deleting this variable from the environment mapping at `cli.py` dispatch is
   prohibited. The central contract, not a command-local bypass, owns recognition.

Tests must prove recognition, non-override behavior, unknown-name rejection, and nonleakage of the
synthetic value on both success and refusal paths.

## 5. Ruling R81 — source-local catalog constant with drift detection

The new `src/disclosure_drift/m3/e0.py` module restates:

```python
OPERATIONAL_CATALOG_RELATIVE_PATH: Final = "catalogs/m3_2a_operational.sqlite3"
```

It does not import `src/disclosure_drift/m3/acquisition.py`. A direct unit test imports the two
constants independently and requires exact equality; a mutation of either value must fail that test.
This is a deliberate source-boundary duplication of one frozen literal, not a second operator choice,
configuration field, path-discovery rule, or permission to edit the acquisition constant.

## 6. Ruling R82 — one fresh bounded remediation

### 6.1 Model, session, and role

One genuinely fresh Claude Opus 5 session at Maximum effort is authorized as the single remediation
executor. Before substantive reading or work it must attest the actual running harness/model
identifier. A configured default, requested model, fallback chain, `/model`, or `/clear` is not
proof. If the actual model is not exactly Claude Opus 5, or cannot be truthfully attested, it stops
without mutation.

No subagent, delegated workflow, second reasoning model, parallel implementation, competing
worktree, or recursive review is authorized.

### 6.2 Exact path widening

Every Decision 094 §12.1 implementation path remains authorized. This Decision adds exactly:

```text
src/disclosure_drift/config.py
src/disclosure_drift/m3/rehearsal_world.py
tests/unit/test_m3_3_execution.py
tests/unit/test_env_overrides.py
tests/unit/test_config.py
tests/unit/test_cohorts.py
tests/unit/test_sec_user_agent.py
tests/integration/test_cli.py
```

The additions authorize only R79/R80 and their direct tests. A needed edit outside the union of
Decision 094 §12.1 and this list is a STOP for Sol/GPT. Reading the acquisition constant for the R81
equality test is permitted; editing or importing the acquisition module from production E0 code is
not.

Every Decision, STATUS, contract, registry, index, architecture map, master plan, and other
governance surface remains Sol-owned and read-only to the remediation executor.

### 6.3 Preserved WIP and commit law

The executor enters with the two §1.1 source files dirty and the Decision-095 governance commit at
HEAD. It must verify those exact facts before edits. It may preserve correct hunks, but must derive
their semantics from Decisions 094–095 and independently validate all retained code. It must not
reset, overwrite, conceal, or describe the WIP as accepted merely because it predates the session.

If and only if the full implementation is complete, every required proof passes, and the final
`make check-fast` succeeds, exactly one local implementation commit is authorized:

```text
feat: implement Decision 094 pre-E0 execution surfaces
```

No partial or misleading success commit is allowed. On a blocker or failed required gate, preserve
the exact worktree and report it. Push, tag, branch, worktree, stash, amend, rebase, and force
operations remain unauthorized.

## 7. Required correction and full-boundary proof

The remediation must complete **all** Decision 094 §§5–11 and all thirteen proof families in
Decision 094 §12.3; this is not a fixture-only patch. In addition it must prove:

1. R79's exact positive counts and one-object-at-a-time negative controls;
2. support-only CIKs have no own accessions and contribute no independent quota or event credit;
3. the production unbindable-member path still fails closed and creates no entity;
4. R80 recognizes only the exact runtime-root name, applies no config override, and leaks no value;
5. removing `EVIDENCE_ROOT_ENV` from `RUNTIME_ROOT_ENV_VARS` kills the relevant test while unrelated
   unknown variables remain rejected;
6. R81's equality test fails if either source-local constant drifts;
7. `e0.py` imports no acquisition, network, SEC client, HTTP, transport, or orchestrator module;
8. both activation constants exist and remain exactly `None`;
9. both execute modes return exit `3`, and no preflight, verify result, environment value, catalog
   state, receipt, namespace, or CLI flag can enable them;
10. no private root or accepted catalog is opened by any test.

Use targeted tests while editing and the touched-code map in `Docs/change_impact_map.md`. Run one
final successful `make check-fast` on the final tree. Do not repeat the full gate without a concrete
failure, correction, or nondeterminism reason.

## 8. Governance commit and repository history

The owner authorizes one local governance commit containing this Decision and its necessary
navigation/current-state overlays. Only governance files may be staged for that commit; the two
preserved source files remain unstaged. The commit message is:

```text
docs: accept Decision 095 bounded correction
```

The remediation's later implementation commit is separate under §6.3. Neither commit may be pushed
or tagged. Historical Decisions and evidence artifacts are not rewritten.

## 9. Review and acceptance boundary

The remediation result returns to Sol/GPT. A Claude success token is implementation evidence only;
it does not accept the candidate, activate either constant, authorize a migration, or start E0.

Sol/GPT verifies the model, entry/final Git states, exact paths, full-gate result, mutation evidence,
identity reconstruction, private nonleakage, and remaining authority. The Decision-094 sequence then
permits at most its one justified genuinely fresh read-only independent review before owner
acceptance. No reviewer may edit, accept its own target, or authorize progression.

## 10. Acts still prohibited

This Decision does **not** authorize:

- discovering, resolving, opening, naming, printing, logging, or inferring the accepted private
  evidence root during implementation or tests;
- opening or modifying the accepted operational catalog;
- applying migrations `0014` or `0015` to the accepted catalog, or creating `0016`;
- enabling either execute activation constant;
- running the catalog transition, E0, the D093 linkage diagnostic, the persistence bridge, E1, E2,
  or M3.4;
- SEC, HTTP, DNS, network, acquisition, reacquisition, package installation, or remote fetch;
- any logical request or physical attempt: both ceilings remain zero;
- modifying migration `0001`–`0015`, acquisition, transport, network configuration, reasons,
  accepted evidence, or historical review artifacts;
- push, tag, release, publication, or owner acceptance by the executor.

## 11. Exact next action

1. Commit this accepted governance record and its current-state overlays locally, without staging the
   preserved WIP.
2. Dispatch one fresh attested Claude Opus 5 Maximum remediation under R82.
3. Return the completed or blocked candidate to Sol/GPT for verification.
4. Do not apply a migration or run E0.

`RESULT_TOKEN: M3_3_D095_BOUNDED_CORRECTION_OWNER_ACCEPTED`
