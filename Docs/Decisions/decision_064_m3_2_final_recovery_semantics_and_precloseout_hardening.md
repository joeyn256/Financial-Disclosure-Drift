# Decision 064 — M3.2 Final Recovery Semantics and Pre-Closeout Hardening

**Date:** 2026-08-11
**Status:** ACCEPTED — OWNER FINAL M3.2 HARDENING 2026-08-11
**Authority classification:** `M3_2_FINAL_RECOVERY_SEMANTICS_AND_PRECLOSEOUT_HARDENING_ACCEPTED`
**Type:** Owner **remediation and hardening** record with an accompanying implementation. It records
the owner's acceptance of the Decision 063 resolver result, adjudicates every remaining known M3.2
recovery defect, adopts the identified operator-surface optimizations, and reconciles the
current-state documentation that Decision 063 deliberately deferred. It is **offline governance and
implementation only.**

**Grants no live authority.** No SEC request was made, no network switch changed, no CompanyFacts
access was opened, no acquisition was invoked, no M3.2B work was authorized, and **Gate H is not
passed and is not claimed by this record.** SEC acquisition for M3.2A is **complete**: 75 of 75
successor request identities are satisfied at a cumulative 77 of 801 physical attempts, and no
further SEC request is authorized under any published record.

**Amends:** nothing in place. Decisions 001–063 remain **byte-unchanged**.

**Narrowly supersedes** four current-state statements, and nothing else:

1. that condition 8.12's carry-in cross-check compares the **head** receipt's plan (§2 below);
2. that condition 8.2 can be met only by an interruption state or a terminal **non-success** (§3);
3. that every recovery action shares one undifferentiated determination prerequisite (§5);
4. that `Milestones/contracts/m3_2.md` §6's stale registry and receipt-version wording remains
   deliberately unreconciled — Decision 063's preamble reserved that reconciliation for this pass,
   and §9 performs it.

**Preserves unchanged:** the cumulative M3.2A ceiling **801**; the successor plan at SHA-256
`f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a`; the frozen predecessor plan at
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; the accepted 70-quarter coverage,
as-of date, calendar year, and evidence manifest; every route's `A_reachable`; the live source
registry `m2.2-source-registry/1.1`; the historical run's permanent non-resumability; the immutable
T6 and T7 receipts and every committed observation; the one-use carry-in authority's permanent
consumption; and every leakage, filing-body, and CompanyFacts/Frames prohibition.

---

## 1. Accepted entry state

The owner accepts Decision 063's implementation result under the token
`M3_2_DECISION_063_CROSS_NAMESPACE_RECEIPT_CHAIN_IMPLEMENTATION_OWNER_ACCEPTED`.

| Fact | Value |
|---|---|
| Cross-namespace chain resolution | works |
| Real chain length | 2 |
| Cumulative physical attempts | **77 / 801** |
| Missing predecessor | none |
| Ambiguity | none |
| Cycle | none |
| Receipt bytes | unchanged |
| Resolver implementation | committed and pushed |
| Full validation | passed |
| Projection rebuild authority | **not exercised** |
| Audit projection | 76 rows against 77 authoritative observations |

Decision 063 §9's one-shot rebuild authority is **superseded by §10 of this record**, which mints
its replacement. It is not reissued and is never available twice.

---

## 2. Condition 8.12 compares the chain's ROOT, never its head

**Accepted finding:** `M3_2_RECOVERY_8_12_ROOT_PLAN_CROSSCHECK_DEFECT_OWNER_ACCEPTED`

**The defect.** Condition 8.12 cross-checks the receipt chain's carry-in root against the
operational catalog's consumption checkpoint. Every fact it compares is a fact about the *carry-in*
— the window it was granted for, the ceiling it was bound to, the baseline it carried, the plan it
was minted under. All but one were read from the chain's **root**. The plan hash was read from the
chain's **head**.

For every chain whose plan never moved, root and head carry the same hash and the error is
invisible. They diverge exactly once: when an accepted owner plan transition (Decision 062 §7) moves
a later invocation in the same chain onto a successor plan. The M3.2A carry-in was minted under
`19be7bdc…`; the successful T7 head executed `f77e003c…`. Both facts are true, and the comparison
reported them as a disagreement — turning an intact chain into `UNDETERMINED`.

**The ruling.** Condition 8.12's carry-in cross-check compares the checkpoint's plan, window,
ceiling, and carried-forward facts against the **receipt chain root's** corresponding facts. The
root's own recorded plan hash is carried as `chain.root_request_plan_sha256`; `chain.request_plan_sha256`
remains the head's and remains what condition **8.10** asks a supplied plan to match. The two
questions are different and are each asked of the receipt they are about.

**Generality.** The rule is stated over the chain's structure, not over any pair of hashes. Nothing
in the implementation names, or is reachable only by, the Decision 062 plans; a root recording no
plan at all refuses rather than passing; and an ordinary single-receipt chain, where root and head
are the same receipt, compares exactly as it always did.

---

## 3. Condition 8.2 admits a successful terminal state

**Accepted finding:** `M3_2_RECOVERY_SUCCESSFUL_TERMINAL_HEAD_SEMANTICS_DEFECT_OWNER_ACCEPTED`

**The defect.** Condition 8.2 could establish a genuine interruption, or a terminal *non-success*.
It could not establish a successful `complete` head. While recovery was synonymous with
continuation, that was harmless — a successful window had nothing to resume. It stopped being
harmless once the accepted lifecycle placed deterministic post-success maintenance (the derived
projection rebuild) **before** Gate H: the inspection's only vocabulary for a successful head was
"no terminal end state is established", which is not conservative but false.

**The ruling.** Condition 8.2 means "the terminal or interruption state is established, not
guessed". A validated `complete` receipt satisfies the state-establishment predicate when its
durable run row, pre-send attempt ledger, receipt chain, catalog integrity, and store state all
agree — the same ten conditions every other terminal head is held to, with one adjustment: a
successful window is not required to carry a reason code, because it has no terminal cause to
classify. A reason code that *is* present must still be registered.

No interruption state is fabricated. A `complete` window is never classified as a failure.

---

## 4. A complete head is never resumable, and SAFE is not permission

**Two separate concepts, and they are never merged:**

| Concept | Question | Surface |
|---|---|---|
| **Recovery state / evidence certainty** | Is the state established, or is it being guessed? | `determination` ∈ {`SAFE`, `UNSAFE`, `UNDETERMINED`} |
| **Continuation eligibility** | May a further live acquisition lawfully be proposed? | `continuation_permitted` |

`SAFE` describes **evidence**, not permission. A successfully completed window is `SAFE` — nothing
about it is unresolved — and is **not** resumable. The two are reported side by side and are never
derived from one another.

**The invariant.** A continuation proposal against a head receipt recording `complete` is refused,
explicitly, on its own, and not as a consequence of an empty remainder. "Nothing remains" is a fact
about the reconciliation that a plan change or a counting correction could move; "this window
already completed" is a fact the head receipt recorded and nothing downstream can rearrange. The
refusal is re-asserted in the live driver adjacent to the transport-construction site, so a caller
several frames away — one holding a proposal object it built itself — cannot bypass it.

**Required post-T7 behaviour:**

| Fact | Value |
|---|---|
| Recovery determination | `SAFE` |
| Continuation needed | no |
| Continuation permitted | **no** |
| Continuation remaining | **0** |
| Reason | the head acquisition is already complete; no successor request is unsatisfied |
| `m3 acquire --resume-from <complete receipt>` | **refused before transport**; no network constructed |

---

## 5. Action-specific eligibility for `rebuild-projection`

**Accepted ruling:** `M3_2_RECOVERY_ACTION_SPECIFIC_ELIGIBILITY_OWNER_RULING`

**The circularity.** Condition 8.7 can fail because the derived audit projection has fallen behind
authoritative SQLite. The accepted deterministic repair for that is `rebuild-projection`. The
applier refused every action from an `UNDETERMINED` determination — a determination computed partly
*from* the projection. The condition the action exists to repair was gating the action.

**The ruling.** `rebuild-projection`, and only `rebuild-projection`, is governed by an explicit
action-specific eligibility gate in place of the blanket determination test. It may proceed only
when every one of the following holds:

| # | Condition |
|---|---|
| 1 | the requested action is exactly `rebuild-projection` |
| 2 | the receipt chain resolves (8.1) |
| 3 | the terminal or interruption state is established (8.2) |
| 4 | catalog integrity passes (8.3) |
| 5 | the authoritative observation set is unambiguous (8.4; no row without its object) |
| 6 | no orphan, partial, or object uncertainty exists (8.5, 8.6) |
| 7 | no blocked recovery state exists (8.9) |
| 8 | the receipt and carry-in accounting resolve (8.12) |
| 9 | the projection mismatch is a deterministic reconstruction, not a divergence |
| 10 | the network is disabled |
| 11 | the exclusive writer lease is safely obtainable |

**This is a narrowing, not a widening.** Every protection the blanket test provided appears above,
plus one it never made: condition 9. No other action inherits it, and `UNDETERMINED` arising from
evidence unrelated to the projection still refuses everything.

Condition 11 is discharged by mechanism rather than by a second opinion: the applier acquires the
exclusive writer lease for its write-ahead block *before* the mutation, and a lease held elsewhere
refuses there with nothing written. A read-only re-implementation of the lease rule could disagree
with the real one, and the weaker of two disagreeing checks is the one that would matter.

### 5.1 Reconstruction versus divergence

The dividing question is one thing only: **does the file on disk assert anything the authoritative
catalog contradicts?**

**Reconstruction** (repairable): the file is absent, empty, or a byte-exact prefix of the
authoritative serialization; or what disagrees is the derived `projected_to_audit` bookkeeping
rather than the bytes; or what is present is the durable marker recording that a rebuild is owed.
Rebuilding from SQLite loses nothing, because SQLite is the authority and nothing on disk claims
otherwise. The condition names explain; the byte-level prefix equality is the proof.

**Divergence** (referred): a payload whose bytes disagree, a reordering, a duplicate or unknown
identity, a malformed or truncated line, appended garbage, or a file outside its accepted location.
Bytes the catalog cannot account for are evidence about what wrote to the audit trail, and
reconstructing over them would destroy exactly what an owner would need to rule on.

**Accepted consequence.** This narrows `rebuild-projection`, which previously reconstructed over any
invalid projection on the argument that a derived file holds nothing authoritative. That argument is
right about the file's *content* and wrong about its *existence*. The repair is not lost, only
gated: a separate owner ruling can still authorize it once a divergence is understood.

### 5.2 The composed repair ordering

Condition 6 above and the accepted `adopt-orphan` prerequisite would deadlock if both were read at
full strength: adoption would require a projection the rebuild cannot produce while an orphan
exists, and the rebuild would require an absence of orphans that adoption cannot deliver. That state
is reachable from an ordinary interruption between a raw write and its catalog commit.

`adopt-orphan`'s prerequisite is therefore narrowed from "the projection is valid" to "the projection
is not **divergent**", under the same reconstruction/divergence rule as §5.1. The prerequisite exists
because the accepted reconciliation primitive persists a projection incident when it finds one, which
would be an unrequested mutation. That reasoning is exact for a diverging projection, where the
incident records an unadjudicated corruption; it does not hold for a lagging one, where the incident
records the already-known, already-true, idempotent fact that a rebuild is owed.

**The accepted order is: adjudicate store uncertainty, then reconstruct the derived projection.**
Neither state is unreachable from the other.

---

## 6. Condition 8.8 counts per identity

**The defect.** The remainder condition 8.8 reports was counted **per route**: a route planning one
logical request and holding one committed row read as complete, whatever that row was and whichever
identity it belonged to. Under an accepted plan transition that is exactly wrong — the retired SIC
identity's committed *failure* made the successor SIC identity look satisfied. Pre-T7, condition 8.8
reported `0` logical requests and `0` worst-case attempts remaining while continuation enforcement,
which has always counted per identity, reported `1` and `6`. Two numbers describing one state,
disagreeing, with the misleading one on the operator's screen.

**The ruling.** The displayed logical remainder and worst-case attempt remainder derive from the
same identity-level reconciliation continuation enforcement uses. Both surfaces expand the plan
through one implementation and derive request identities through one function, so they are the same
count of the same requests by construction rather than by agreement.

| State | Logical remaining | Worst-case attempts |
|---|---|---|
| Pre-T7, successor plan, retired SIC identity committed failed | **1** | **6** |
| Post-T7, complete | **0** | **0** |

No route is special-cased. The 801 physical-attempt ceiling semantics are unchanged, and a remainder
that does not fit the remaining headroom is still not met.

---

## 7. Transition-aware `m3 reconcile-requests`

`m3 reconcile-requests` gains `--plan-transition-predecessor`, using the **same** seventeen-condition
verifier the recovery inspection, the acquisition continuation, and the plan-transition check
already use. No second transition implementation exists.

Because the transition's registry-version condition asks what the *predecessor run recorded*, and a
reconciliation performed after the successor run completed has the successor's receipt as its chain
head, the flag is paired with `--plan-transition-predecessor-receipt`. Both are supplied together or
neither is; half a binding establishes nothing and is a usage failure.

| Invocation | Result |
|---|---|
| Without the flags | the retired SIC observation is an ordinary **blocking** out-of-plan observation |
| With the exact authorized pair | it is reported under `superseded_out_of_plan`: still stored, still visible, still failed historical evidence, satisfying nothing |
| Any other out-of-plan observation | remains blocking, with or without the flags |
| An unauthorized predecessor/successor pair | **refused** |

A transition is never inferred. Reconciliation remains read-only except for its accepted report
artifact, and constructs no network.

The reconciliation report schema moves to `m3-2-reconciliation-report/1.1`, adding exactly one field,
`plan_transition`, and changing nothing else. A reconciliation that moves an observation out of the
blocking set records under what authority, or the report states a clean result while omitting the
reason a stranded identity stopped counting. `null` is the ordinary case, and the only case a `1.0`
reader ever saw.

---

## 8. Receipt storage policy

Decision 063 found that `execution_receipt.json` is a real, accepted operator convention while
`Docs/m3/execution_receipt_spec.md` documented only the content-derived naming convention. The
specification is synchronized to describe **both** legitimate cases:

- the **operator-selected, create-once** receipt location a live command writes through
  `--receipt-out`, which is where the T6 and T7 receipts actually live; and
- the **content-derived** `receipt-<receipt_id>.json` name, which the specification's own conventions
  and the chain resolver both use.

The specification must not imply that every receipt physically exists at
`receipt-<receipt_id>.json`, because the real T6 and T7 evidence proves otherwise. **No receipt is
moved, copied, renamed, or rewritten.** This is a documentation correction only.

The predecessor resolver's failure diagnostics are improved in the same spirit: a sanitized refusal
now states the requested identity (truncated), the number of candidate files examined, the
zero/one/ambiguous classification, the relative search scopes, and an exact fail-closed category. It
never prints the private evidence root, an absolute path, an SEC identity, a secret, or any response
body, and no semantic guard is weakened.

---

## 9. Contract and runbook synchronization

Decision 063's preamble reserved this reconciliation for the final closeout pass. It is performed
here. `Milestones/contracts/m3_2.md`'s **current-state** statements are corrected to agree with the
accepted decisions and the final implementation:

| Statement | Corrected to |
|---|---|
| Source registry current authority | `m2.2-source-registry/1.1` (Decision 062 §5) |
| Execution receipt current authority | `m3-execution-receipt/3.0`, readers accepting `2.0` and `3.0` (Decision 055 §7) |
| Plan semantics | the Decision 062 successor plan and its one authorized substitution |
| SIC exact path | the successor path SEC published |
| Recovery semantics | Decisions 063 and 064 |

`Docs/m3/operator_runbook.md`'s stale `PLANNED — NOT YET IMPLEMENTED` labels are corrected for
functionality that is implemented and accepted, and its guidance must not instruct a reader toward
source registry `1.0`, receipt schema `2.0`, the retired SIC URL, successor-plan-unaware recovery,
non-transition-aware reconciliation, replaying the 74 satisfied retrievals, or any further live SEC
invocation.

**Historical statements remain historical.** No prior decision, review, receipt, or completion
record is edited; only statements purporting to describe the *current* rule are reconciled.

The final M3.2 recovery lifecycle is described truthfully as:

> acquisition → network closure → authoritative SQLite verification → deterministic derived-projection
> synchronization if needed → Gate H.

---

## 10. One-shot final audit-projection rebuild authority

**Authority:** `M3_2_DECISION_064_ONE_SHOT_FINAL_AUDIT_PROJECTION_REBUILD_OWNER_AUTHORIZED`

The owner authorizes **exactly one** invocation of `m3 recover --action rebuild-projection` against
the real T7 state, and nothing else:

- no other recovery action;
- no direct private primitive;
- no manual SQLite mutation;
- no `projected_to_audit` edit;
- no receipt copying, rewriting, or fabrication;
- no network.

**Preconditions.** Before the authority is consumed, the action's §5 eligibility must be proved
unequivocally permitted through the read-only surface. If it is not, the invocation does not happen
and the authority is not spent.

**Required result.**

| Fact | Required value |
|---|---|
| SQLite observations | 77 |
| Projection rows | 77 |
| `projected_to_audit = 1` | 77 |
| Projection | exact deterministic SQLite reconstruction |
| Recovery event | recorded |
| Recovery state | resolved |
| T6 and T7 receipts | unchanged |
| Raw objects, lineage | unchanged |
| Cumulative attempts | 77 / 801 |
| Run states | unchanged |
| Network | disabled |

This authority is single-use. It is never reissued, and a refused invocation consumes it exactly as
a successful one does.

---

## 11. Scope, prohibitions, and the final audit target

**No live authority.** No SEC request, no transport construction, no network use, no CompanyFacts,
no Frames, no filing bodies, no snapshot, no selection, no manifest, and no tag are authorized by
this record. Tracked network switches remain `false`/`false`.

**Unchanged:** migrations `0001`–`0013`; the source registry; the request plans; the SEC client; the
parsers; the catalog schema. No migration is created.

**Still unauthorized:** M3.2B, M3.3, any snapshot, any selection, any manifest, any tag, and any
further M3.2 live acquisition.

**Gate H is not passed and is not claimed by this record.** A Gate H *candidate* result may be
reproduced offline and reported; final Gate H acceptance is a separate owner act.

**Final self-review target for this stage:** BLOCKER 0, MAJOR 0, MINOR 0.

**Next:** owner Gate H acceptance, then one fresh independent final M3.2 milestone audit.
