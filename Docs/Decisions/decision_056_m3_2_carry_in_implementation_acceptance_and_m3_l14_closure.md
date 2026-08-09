# Decision 056 — M3.2 Carry-In Implementation Acceptance and M3-L14 Closure

**Date:** 2026-08-09
**Status:** ACCEPTED — OWNER APPROVED 2026-08-09
**Authority classification:** `M3_2_CARRY_IN_IMPLEMENTATION_ACCEPTED_AND_M3_L14_CLOSED`
**Type:** Governance-only acceptance of the bounded offline Decision 055 implementation candidate,
its independent review, the single owner-adjudicated MAJOR remediation, and the final owner
verification. This record closes **M3-L14** on its complete evidence list and records the implemented
portion of **M3-L16** as accepted. It changes no executable or test byte and performs no operational
state mutation.
**Amends:** nothing in place. Decisions 001–055 remain byte-unchanged.
**Narrowly supersedes:** only the current-state statements in Decision 055, the decision registry,
`Milestones/STATUS.md`, and `Docs/m3/limitations_register.md` that the candidate was not implemented,
reviewed, or accepted and that M3-L14 remained open pending those steps. They were accurate when
written and are preserved as historical statements.
**Preserves unchanged:** ceiling **801**; historical seed **1**; the frozen 75-logical-request plan
and SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`;
the old run's permanent no-resume status; recovery `UNDETERMINED`; the absence of a terminating
receipt; the Path-B orphan-adoption requirement; M3-L15; every network, SEC, transport, recovery,
provenance, and live-operation stop condition; and the rule that M3-L16 blocks every clean or live
run until the orphan is adopted and the limitation is separately closed.
**Related:** [Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md),
[Decision 052](decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md),
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md),
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md), and
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).

---

## 1. Owner determination

The owner determines:

```text
M3.2 — DECISION 056
CARRY-IN IMPLEMENTATION ACCEPTANCE AND M3-L14 CLOSURE

Accept the corrected Decision 055 offline implementation candidate at commit
2c18e89b73048a6cf7ce8cd528325f2a0c50a9ac and tree
6f77deaf0aaf4be3e365d3d0be8c22a89c737802.

Accept the fresh independent review, the owner reclassification of its first
MINOR as MAJOR, the single bounded remediation of that MAJOR, and the final
owner verification. The final accepted candidate has zero unresolved BLOCKER
and zero unresolved MAJOR findings.

Close M3-L14. Keep M3-L16 ACTIVE and blocking: its implementation limb is now
satisfied, but the separately authorized, offline, one-time verified orphan
adoption and a later separate owner closure act remain mandatory.

Exhaust Decision 055's implementation authority. Authorize publication of this
accepted lineage by one normal fast-forward push, with no tag. Authorize next
only a fresh read-only orphan-adoption architecture discovery. No orphan
mutation, operational-state mutation, transport construction, network, SEC,
clean run, T6, M3.2B, or Gate H action is authorized.
```

## 2. Accepted candidate identity

| Fact | Accepted value |
|---|---|
| Published Decision 055 baseline / parent | `5f4fbc479034c71eabacc9470ebd5df396335eb2` |
| Candidate commit | `2c18e89b73048a6cf7ce8cd528325f2a0c50a9ac` |
| Candidate tree | `6f77deaf0aaf4be3e365d3d0be8c22a89c737802` |
| Candidate subject | `Implement M3.2 carry-in authority and receipt v3` |
| Full candidate diff SHA-256 | `4b44e8344175468ec87c04db5c3a244012fdf64b25007e097059617bef1904ad` |
| Path count | exactly **16**, with no seventeenth |
| Push / tag state at acceptance | unpushed; untagged |

The candidate is SHA- and tree-specific. Acceptance does not transfer to changed bytes.

The final two files changed by the independent-review remediation have these identities:

| Path | SHA-256 |
|---|---|
| `src/disclosure_drift/m3/acquisition.py` | `16329e479c2242e5e1fb2086f5460ea4753d2c029d80cbcabe34aaa392501d37` |
| `tests/unit/test_m3_acquisition.py` | `7a9d551c759e1c7ff2c29f51f680d36a44d9bdd4c6a2c4d7805e2ac7c8fca09a` |

The complete candidate path set is exactly Decision 055 §10's four production, six documentation,
and six test paths. No migration, configuration, dependency, reason-code, or seventeenth path is in
the candidate.

## 3. Accepted implementation

The candidate correctly implements the Decision 055 architecture:

1. The cumulative ceiling remains **801**, seeded at **1**, with the global ceiling as the sole
   runtime enforcement and no per-route refusal.
2. A canonical `m3-carry-in-authority/1.0` artifact supplies the clean-root run id, is never a
   resume, refuses coexistence with `--resume-from`, and is validated before transport.
3. Its single use is burned by a deterministic `ops_checkpoints` primary key in the same existing
   `BEGIN IMMEDIATE` transaction as run registration, with rollback leaving neither row and later
   pre-wire failure never auto-reissuing it.
4. Writer schema `m3-execution-receipt/3.0` is backward-compatible; `2.0` remains readable and
   byte-unchanged; mixed chains count the root carry-in exactly once.
5. Checkpoint and root receipt cross-check fail closed to `UNDETERMINED`.
6. Receiptless reservation matching is globally one-to-one; the one-reservation/two-segment
   counterexample returns `UNDETERMINED`, never `1`/`UNSAFE`.
7. Network containment, deterministic behavior, provenance, reason codes, migrations, and the old
   run's permanent no-resume status are preserved.

## 4. Independent review and owner adjudication

The required fresh Claude Opus 5 Max non-author review inspected the frozen pre-remediation candidate
at `8ba11e04a8b4f6b205fd46a8367a9c0b5bc5d538` and returned `PASS_WITH_FINDINGS`:

```text
BLOCKER:      0
MAJOR:        0 as reported by reviewer
MINOR:        2
OPTIMIZATION: 4
```

The owner reproduced the first MINOR and reclassified it **MAJOR**: execution and burn re-proof
recomputed the public integrity digest and checked fixed bindings but did not repeat the prohibited-
content scan. A directly constructed, self-consistent authority could therefore put a private
absolute path into `ops_checkpoints`. The normal CLI loader stayed safe, so the finding was MAJOR,
not BLOCKER.

One bounded remediation corrected that exact finding. The same closed-document content scan now
runs at byte ingestion and at every execution/burn re-proof, before a value-quoting binding check.
Non-vacuous pre-fix evidence produced **6 failures and 2 positive-control passes**; post-fix evidence
refused both boundaries, constructed no transport, and left **zero checkpoint rows and zero job
rows**. No signature or authentication mechanism was invented: the digest remains an integrity
identity and evidence-root provenance remains procedural.

The second reviewer MINOR — `--show-scope` silently ignoring `--carry-in-authority` — is accepted as
a real, nonblocking CLI diagnostic observation. It creates no transport or state mutation and does
not weaken execution, receipt-chain, or recovery enforcement. It is deferred without a new
limitations-register entry. The four optimizations are likewise deferred under the bounded-review
stop rule.

The remediation's nested-key location echo is a pre-existing diagnostic behavior and not a checkpoint
or transport defect. It does not reopen the accepted correction.

## 5. Validation accepted

The final corrected bytes passed Decision 055 §11.2 in order:

| Gate | Result |
|---|---|
| Ruff lint | pass |
| Ruff format check | 145 files already formatted |
| mypy | no issues in 76 files |
| full pytest | **3,471 passed, 1 pre-existing unrelated skip** |
| SEC HTTPX transport proof | **30 passed, 0 skipped** |
| SQLite check | Python 3.12.13; SQLite 3.53.4 |
| secrets scan | 300 files; 0 findings |
| hygiene scan | 302 paths; 0 findings |
| context | exact authorized dirty two-path remediation before freeze |

The owner then independently inspected the final diff, verified the exact 16-path envelope and
one-commit rule, ran the two changed files through Ruff lint and format checks, and reran the focused
re-proof set: **21 passed, 336 deselected**. `git diff --check` passed before the amend, and the amend
produced a clean worktree with the required subject and original parent.

No network, DNS, SEC contact, real operational-catalog access, live acquisition, orphan adoption,
resume, replacement run, T6, M3.2B, or Gate H action occurred in implementation, review,
remediation, or owner verification.

## 6. M3-L14 closure

M3-L14 is **CLOSED — DECISION 056**. Every closure-evidence item is satisfied:

- Decision 055 selected the fail-closed global one-to-one rule;
- the accepted candidate implements it;
- the non-vacuous counterexample test fails against the old per-manifest behavior and passes against
  the candidate;
- targeted and full validation pass;
- a fresh non-author independent review completed;
- the owner separately accepts the candidate and closes the limitation here.

Receiptless inspection remains inspection-only, can never return `SAFE`, and authorizes no
continuation.

## 7. M3-L16 disposition

M3-L16 remains **ACTIVE** and continues to block every clean-run and live authorization.

Its architecture, implementation, test, validation, and independent-review limbs are now satisfied.
Its remaining closure requirements are not:

1. a separately authorized, offline, one-time verified adoption of the historical orphan;
2. independent verification and owner acceptance leaving zero unresolved orphan mismatch;
3. a later separate owner closure act for M3-L16.

No carry-in authority may be minted or consumed before those requirements are complete. The project
is not live-ready.

## 8. Authority exhausted and withheld

Decision 055's implementation authority is exhausted by the accepted candidate. No further source,
test, documentation, migration, configuration, or reason-code change is authorized by Decisions 055
or 056.

This record grants no orphan adoption, operational-state mutation, raw/lineage/catalog/receipt
mutation, transport construction, network, SEC contact, live acquisition, resume, retry, replacement
run, T6, M3.2B, Gate H, tag, or live-readiness authority.

## 9. Recording and publication boundary

Exactly four governance paths are authorized for this record, with no fifth:

1. this Decision 056 file;
2. `Docs/Decisions/decision_registry.md`;
3. `Milestones/STATUS.md`;
4. `Docs/m3/limitations_register.md` — M3-L14 closure, M3-L16 accepted-implementation status, and
   summary arithmetic only; M3-L15 remains byte-unchanged.

One governance commit is authorized with exact subject:

```text
Accept M3.2 carry-in implementation
```

One normal fast-forward push of the candidate and governance commit is authorized. No tag is
authorized.

## 10. Formal outcome and exact next action

```text
FORMAL_OUTCOME: M3_2_CARRY_IN_IMPLEMENTATION_ACCEPTED_AND_M3_L14_CLOSED
CANDIDATE: 2c18e89b73048a6cf7ce8cd528325f2a0c50a9ac
M3_L14: CLOSED — DECISION 056
M3_L16: ACTIVE — IMPLEMENTATION ACCEPTED; ORPHAN ADOPTION AND OWNER CLOSURE OUTSTANDING
LIVE_READINESS: NOT_CLAIMED
NETWORK_OR_SEC_AUTHORITY: NONE
NEXT_AUTHORIZED_ACTION: CLAUDE_M3_2_ORPHAN_ADOPTION_ARCHITECTURE_DISCOVERY_PACKET
```

The next action is fresh, read-only, offline architecture discovery only. It may inspect accepted
repository authority and the preserved facts, but it may not open or mutate the real operational
catalog, raw object, lineage, or private evidence; perform the adoption; create a checkpoint or
receipt; contact the network or SEC; or authorize its own implementation or execution.
