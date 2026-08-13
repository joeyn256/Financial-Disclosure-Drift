# Decision 065 — M3.2 Final Acceptance, M3.2B Disposition, and Milestone Closeout

**Date:** 2026-08-13
**Status:** ACCEPTED — OWNER FINAL M3.2 CLOSEOUT 2026-08-13
**Authority classification:** `M3_2_FINAL_OWNER_ACCEPTANCE`
**Type:** Owner **final acceptance and closeout** record. It accepts the fresh independent final M3.2
milestone acceptance review, issues the owner's final M3.2 acceptance and Gate H acceptance, fixes
the disposition of M3.2B, records the dispositions of the review's four observations and two
deferred optimizations, and authorizes exactly one bounded governance closeout commit and the
annotated `m3.2-complete` completion tag. It is **governance and documentation only.**

**Grants no live authority.** No SEC request was made, no network switch changed, no CompanyFacts
access was opened, no acquisition was invoked, no recovery action was run, no private evidence was
read or mutated, and no M3.2B or M3.3 work is authorized. **No further M3.2 SEC acquisition
authority exists under any published record.**

**Amends:** nothing in place. Decisions 001–064 remain **byte-unchanged**.

**Narrowly supersedes** the following current-state statements, and nothing else:

1. that Gate H is a *candidate* result with owner final acceptance **pending** (§3 below);
2. that M3.2 is **not complete** and that no `m3.2-complete` tag is authorized (§3, §9);
3. that **M3.2B** is a remaining prerequisite of M3.2 completion or of Gate H (§4);
4. that the operator runbook's already-implemented M3.1 evidence-output protections do not yet
   exist (§5, OBS-1).

**Preserves unchanged:** the cumulative M3.2A ceiling **801** and the consumed **77**; the successor
plan at SHA-256 `f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a`; the retired
predecessor plan at `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; the immutable
T6 and T7 receipts and every committed observation; the permanently `stopped`, non-resumable,
`UNDETERMINED`, receiptless historical run; the one-use carry-in authority's permanent consumption;
the live source registry `m2.2-source-registry/1.1`; the receipt writer `m3-execution-receipt/3.0`
with readers accepting `2.0` and `3.0`; migrations `0001`–`0013`; every limitation's current state,
including **M3-L15** `ACTIVE` and byte-unchanged; and every leakage, filing-body, pilot-use,
CompanyFacts, and Frames prohibition.

---

## 1. The fresh independent final milestone acceptance review

A genuinely fresh, non-author Claude Fable 5 session at maximum effort performed the final
independent M3.2 milestone acceptance review over the accepted implementation state.

| Fact | Value |
|---|---|
| Verdict | **PASS** |
| BLOCKER | **0** |
| MAJOR | **0** |
| MINOR | **0** |
| Review token | `M3_2_FINAL_INDEPENDENT_MILESTONE_ACCEPTANCE_REVIEW_B0_M0_MIN0_PASS` |

The owner accepts that review under
`M3_2_FINAL_INDEPENDENT_MILESTONE_ACCEPTANCE_REVIEW_OWNER_ACCEPTED`.

The review raised four observations, **none of them blocking**: OBS-1 (a stale operator-runbook
paragraph), OBS-2 (M3.2B current-state references), OBS-3 (sidecar / released-lease residue), and
OBS-4 (the public evidence index carrying no M3.2 rows). Each is adjudicated in §§5–8 below. It also
identified two optional optimizations, adjudicated in §10.

---

## 2. Accepted baseline

The owner's closeout authorization is bound to this exact repository state, verified live before any
edit:

| Fact | Value |
|---|---|
| Branch | `main` |
| Accepted implementation HEAD | `5c4c875e89ea588acd7c04414a05e566c647b39c` |
| Accepted tree | `fcb0bfa3cf8a17ff6a52309eb6131a1f259e41eb` |
| `origin/main` | `5c4c875e89ea588acd7c04414a05e566c647b39c` |
| Working tree | clean |
| Tag at HEAD | none |

`5c4c875e…` is the **accepted M3.2 implementation baseline**. This record's own closeout commit is
governance-only and introduces **no executable difference** after it.

---

## 3. Final accepted M3.2 facts and the owner's final acceptance

Recorded as accepted, without reinterpretation:

| Fact | Value |
|---|---|
| T7 | **completed** |
| T6 | **failed** — immutable historical predecessor |
| Historical first run | **stopped** |
| Successor logical request identities | **75** |
| Satisfied | **75** |
| Unsatisfied | **0** |
| Predecessor identities replayed | **0** |
| Cumulative physical attempts | **77 / 801** |
| Audit projection | **77 / 77** |
| Stored raw objects | **76 / 76**, hash-valid |
| Quarterly full-index objects | **70 / 70**, present and hash-valid |
| Recovery state | **SAFE** / fully resolved |
| Continuation permitted | **NO** |
| Continuation remaining | **0** |
| Network | **disabled** |
| CompanyFacts | **disabled** |
| M3.3 | **not begun** |

**Gate H: OWNER ACCEPTED.** The Gate H candidate was reproduced offline on 2026-08-11 with **30 of
30** applicable items `PASS` (Decision 064; `M3_2_GATE_H_CANDIDATE_STATUS`), the final independent
milestone audit independently accepted the resulting state at BLOCKER 0 / MAJOR 0 / MINOR 0, and the
owner now issues final Gate H acceptance. Gate H is **PASSED and owner-accepted**.

**Final owner acceptance:** `M3_2_FINAL_OWNER_ACCEPTANCE`. Milestone 3.2 is **COMPLETE and
OWNER-ACCEPTED**.

**Closeout and tag authorization:** `M3_2_CLOSEOUT_AND_TAG_OWNER_AUTHORIZED`. The owner authorizes
exactly one bounded governance closeout commit and the annotated `m3.2-complete` completion tag on
that closeout commit (§9). **No implementation work remains authorized in M3.2.**

**Acceptance is not acquisition authority.** `SAFE` reports evidence certainty, never permission to
acquire again (Decision 064 §4); a `complete` head is non-resumable and refuses before a transport is
constructed; the Decision 062 §21, Decision 063 §9, and Decision 064 §10 one-shot authorities are
permanently spent and are never reissued; and **no further M3.2 SEC acquisition authority exists.**

**Decision 064's recovery semantics are final.** Its §2 root-plan cross-check, §3 successful-terminal
condition 8.2, §4 SAFE-is-not-permission separation, §5 action-specific `rebuild-projection`
eligibility, §6 per-identity remainder, §7 transition-aware reconciliation, and §8 receipt storage
policy stand unamended as the accepted M3.2 recovery and operator semantics.

---

## 4. M3.2B disposition

**Owner ruling:** `M3_2B_OWNER_DISPOSITION_NOT_REQUIRED_FOR_M3_2_COMPLETION`

**M3.2B is CLOSED AS NOT EXECUTED / NOT REQUIRED for the accepted M3.2 completion state.**

Decisions 063 and 064 established the applicable Gate H mechanism over the completed M3.2A evidence
state, and the final independent milestone audit independently accepted that resulting state at
BLOCKER 0, MAJOR 0, MINOR 0.

M3.2B therefore:

- **was not executed**;
- **is not pending**;
- **is not a prerequisite** remaining before M3.2 completion;
- **carries no latent acquisition or network authority**;
- **may not be resurrected** from any historical M3.2 authorization.

Any future acquisition resembling the previously described M3.2B work requires a **new explicit owner
authorization** under the milestone or stage that actually requires it. Neither the M3.2A ceiling
801, nor the accepted contract's §15 dependency boundary, nor the master plan's phase map, nor the
`m3 derive-dependent-plan` command's existence is any part of such an authorization.

**Historical descriptions are preserved.** The master plan's and contract's descriptions of the
two-window architecture, and the runbook's step 18a, remain on record exactly as accepted. Where such
a description could be mistaken for a **current pending action**, this record's disposition is
annotated narrowly in place, in the form:

> Disposition: NOT EXECUTED / NOT REQUIRED FOR ACCEPTED M3.2 COMPLETION — Decision 065.

No historical rationale is rewritten.

---

## 5. OBS-1 — operator runbook residue

The final audit identified one conservative stale paragraph in
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md), under the already-implemented M3.1
evidence-output protections. It stated that "None of these three protections exists yet" and that
"no M3 evidence-output command exists", and the paragraph above it described the protections in the
future tense.

**All three protections exist and are accepted, and M3-L11 is `CLOSED` (2026-08-03):**

| Protection | Where it is implemented |
|---|---|
| Reserved `.gitignore` rule `/.m3-private-evidence` | `.gitignore` |
| Repository-hygiene refusal | `scripts/check_repo_hygiene.py` (`RESERVED_EVIDENCE_DIRNAME`) |
| Resolved-path evidence-root check | `src/disclosure_drift/m3/evidence_paths.py` |

**Ruling.** The paragraph is corrected to state the truth. The correction is **documentary only**: it
redesigns nothing in the runbook, changes no command, argument, exit code, or label, and grants no
authority. No test, migration, or executable byte is touched.

---

## 6. OBS-2 — M3.2B current-state references

**Ruling.** The §4 disposition is applied to current-state surfaces where a reader could otherwise
take M3.2B to be a remaining required action — `Milestones/STATUS.md`,
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md),
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md), and this repository's governance
navigation surfaces — by **narrow annotation only**.

Historical descriptions remain historical. Statements that M3.2B is **not authorized** remain true
and are preserved: the disposition closes M3.2B as not required; it does not license it.

---

## 7. OBS-3 — sidecar and released-lease residue

The final audit found the known sidecar and released-lease shape — SQLite `-wal` and `-shm` sidecars
and released lease artifacts under the private evidence root — and determined it **nonblocking**,
with the database and evidence bytes stable.

**Ruling.** The finding is recorded as **accepted, intentional, and nonblocking**. **No cleanup action
is required and none is authorized.** No private-state mutation is authorized by this record: no
`-wal`, `-shm`, released lease artifact, or any other private evidence file is deleted, moved,
renamed, or rewritten, and no catalog is opened — not even read-only — under this closeout.

---

## 8. OBS-4 — the public evidence index

The final audit observed that [`Docs/m3/templates/evidence_index.md`](../m3/templates/evidence_index.md)
contains **no M3.2 rows**, while M3.2 artifact identities are durably published through the accepted
decision records and the accepted contract under this repository's established **ledger-not-index**
practice — the same treatment the Gate F readiness token and the T4 preflight attestation received
(Decision 049; evidence index §4 and §8).

**Ruling.** The existing ledger-not-index architecture is **retained**. **No second, competing
indexing convention is invented during closeout.**

**M3.2 private evidence identity and provenance are discoverable through
[Decision 062](decision_062_m3_2_terminal_failure_and_sic_endpoint_remediation.md),
[Decision 063](decision_063_m3_2_cross_namespace_receipt_chain_recovery.md),
[Decision 064](decision_064_m3_2_final_recovery_semantics_and_precloseout_hardening.md), this
record, the accepted M3.2 contract, and the governed private evidence references those records
carry.** Each binds an exact identity — run ids, receipt identities, plan hashes, the carry-in
authority digest, object and attempt counts — without publishing any artifact's contents.

The evidence index's own note explaining this practice is updated narrowly to record the M3.2
disposition, including for its §5 expected-coverage table. The index is otherwise left
**structurally unchanged**: no row is added, edited, deleted, or superseded, its append-only rule
(§6) is untouched, and **no private absolute path, SEC identity, credential, response body, or
secret is published**.

---

## 9. Closeout commit and the `m3.2-complete` tag

The owner authorizes, under `M3_2_CLOSEOUT_AND_TAG_OWNER_AUTHORIZED`, and nothing else:

1. **Exactly one** bounded governance closeout commit — subject `Close M3.2 after final acceptance` —
   containing this record and the narrow current-state synchronizations §§4–8 and §11 require. **No
   executable source, test, migration, configuration, or private evidence change.** No amend, no
   force, no history rewrite.
2. One normal push to `origin/main`.
3. Exactly one **annotated** tag `m3.2-complete`, created on the **closeout commit** — not on the
   `5c4c875e…` implementation baseline — with the annotation
   `Complete M3.2 controlled SEC metadata acquisition and Gate H acceptance`, then pushed once.

**If `m3.2-complete` already exists locally or remotely, the closeout stops.** No existing tag is
moved, retargeted, deleted, or overwritten. No other tag is authorized.

The accepted implementation baseline `5c4c875e89ea588acd7c04414a05e566c647b39c` remains recorded as
such and is an ancestor of the closeout commit.

---

## 10. Deferred optimizations

The final independent review's disposition is preserved. Both remain **DEFERRED**, and **neither is
implemented during closeout**:

| ID | Optimization | Disposition |
|---|---|---|
| **OPT-1** | Richer reconciliation item states carried by recovery inspection | **DEFERRED** |
| **OPT-2** | Standalone `rebuild_projection_eligibility` performs one additional cheap read-only inspection | **DEFERRED** |

**Reason.** Neither creates a correctness, recovery, operator-safety, auditability, or M3.3-boundary
defect. Deferral is a disposition, not an open blocker.

---

## 11. Scope, prohibitions, and what happens next

**Governance and documentation only.** This record changes no executable source, no test, no
migration, no configuration, and no private evidence. It runs no recovery action, opens no catalog,
takes no snapshot, performs no selection, and constructs no manifest.

**No live authority.** No SEC request, no transport construction, no network use, no CompanyFacts, no
Frames, no filing bodies. Tracked network switches remain `false` / `false`.

**Unchanged:** migrations `0001`–`0013`; the source registry; the request plans; the SEC client; the
parsers; the catalog schema; every frozen research definition; every limitation's current state.

**Still unauthorized:** any further M3.2 live acquisition; M3.2B (closed under §4, and never
resurrectable from a historical M3.2 authorization); **M3.3 implementation**; any snapshot, selection,
manifest, or root approval; and any tag other than the single `m3.2-complete` tag §9 authorizes.

**M3.3 has not begun and is not authorized.** It requires its own separate owner packet and its own
accepted stage contract. Nothing in this record, in the completion tag, or in the closed M3.2
contract begins it.

**Next:** return to the owner for the M3.3 entry and contract packet.
