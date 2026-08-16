# Decision 101 — D100 PRE-E0 Owner Acceptance, Catalog-Transition Authority, and E0 Execution Authority

```text
STATUS: ACCEPTED — OWNER ACCEPTANCE AND EXECUTION AUTHORIZATION
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT-5.6 owner acceptance and technical ruling
OUTCOME: M3_3_D100_PRE_E0_IMPLEMENTATION_OWNER_ACCEPTED
ACCEPTED_IMPLEMENTATION: 3e8c82d1ec411bf667c0c8eb37603306a86e6dc4
ACCEPTED_TREE: 67564d3f4c677548bfaff27e62e15df9c64dbc8e
PRE_E0_IMPLEMENTATION_ACCEPTANCE: ACCEPTED — REMEDIATION CHAIN CLOSED
M3_3_E0_OPERATIONAL_STATE: AUTHORIZED — CONDITIONAL ON A COMPLETE AND VERIFIED TRANSITION
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: YES — 0014 AND 0015 ONLY
MIGRATION_0016_AUTHORIZATION: NO
M3_3_E0_EXECUTION_AUTHORIZATION: YES — ONE INVOCATION
CHECKPOINT_PUSH_AUTHORIZATION: YES — ONE ORDINARY PUSH OF main TO origin/main
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record closes the PRE-E0 remediation chain and issues the two execution instruments that
Decision 094 §12.4 steps 6 and 8 reserved for a later exact owner act. It creates no architecture.
Decisions 091–100 remain binding on every point they name, and nothing below reopens, weakens, or
reinterprets any of them.

## 1. Owner acceptance of the Decision 100 implementation

Sol/GPT-5.6 performed the Decision 099 §9 corrected-target review directly, as that record
requires, and accepted the result. The verbatim owner instrument is:

```text
OWNER_TOKEN: M3_3_D100_PRE_E0_IMPLEMENTATION_OWNER_ACCEPTED
ACCEPTED IMPLEMENTATION: 3e8c82d1ec411bf667c0c8eb37603306a86e6dc4
ACCEPTED TREE: 67564d3f4c677548bfaff27e62e15df9c64dbc8e
```

The accepted target carries zero BLOCKER and zero MAJOR findings. **The PRE-E0 remediation chain is
CLOSED.** No further independent review, acceptance review, architecture review, optimization pass,
or speculative hardening precedes the transition or E0, and the owner has expressly declined a
re-run of the already-accepted validation evidence — the Decision 100 epoch's `make check-fast`
together with the independent review's reproduced targeted and adjacent passing tests, its
production-validator probe, and its static checks.

Decision 100's three rulings are accepted as issued: **R99** (the reproduced category-A
commit-before-event gap), **R100** (membership derived from durable evidence alone, with the
existing `after_e0_source_commit_before_event` value and no vocabulary amendment), and **R101** (the
tail `INTERRUPTED` event projected to Decision 094 §10.2's exact key set).

Unlike Decisions 094–098, this acceptance rests on the owner's direct review rather than on a
separate durable independent-review artifact; Decision 099 §9 is the record that made a direct
review sufficient here, and no artifact under `Docs/m3/reviews/` covers the Decision 100 target.

## 2. Ruling R102 — the catalog-observed correction is ratified

The independent review's MINOR-1 concerned the correction that made
`failure.catalog_state_observed` and its conditioned field group become available **together**: the
whole group is derived, validated by `_catalog_observation`, exposed, and only then is the in-memory
claim set. Deriving the group after the claim was what left a window in which a raising read
produced a true claim over an absent group.

That correction is **ratified as valid work inside Decision 100's authorized scope.** It preserves
Decision 099 R96 rather than competing with it: R96 derives the permitted conditional set from the
durable ledger, and this projection ensures that a claim which survives that derivation is backed by
a complete measurement. The change is fail-safe, alters no methodology, and requires no further code
correction.

## 3. Ruling R103 — the failure-only aggregate limitation, deferred

The independent review's MINOR-2 concerned two aggregates,
`submissions_membership_observation_count` and `substantive_membership_observation_count`, which can
appear as zero on a **failed or interrupted** E0 terminal.

The owner accepts this as a **non-blocking limitation, deferred to a post-E0 correction.** It does
not delay the transition or E0. Its exact scope:

1. On a failed or interrupted terminal, those two zero values **must never be read as authoritative
   measured quantities.** Authoritative evidence on such a terminal remains the durable
   `source_results`, the durable event ledger, the persisted catalog state, `association_totality`,
   and the other specifically governed durable evidence.
2. **COMPLETE-run semantics are unaffected.** On a complete run these values are governed by their
   accepted success semantics, and this limitation is simply not applicable to them. Canonical
   persisted data, source-result membership, and the E0 success gate are likewise unaffected.

A reader of a failed or interrupted terminal record must apply clause 1; a reader of a COMPLETE
record must not apply it.

## 4. Ruling R104 — regression-test hardening, deferred

The independent review's MINOR-3 noted a missing regression test for the valid-but-wrong
interruption-state case. The invariant itself was demonstrated against the production validator and
the guard exists and is active in production code, so the gap is **deferred test hardening**, not a
defect. It does not delay the transition or E0.

## 5. Checkpoint publication

One ordinary push of `main` to `origin/main` is authorized, and is required **before** any private
catalog state is touched, so the accepted governance baseline is durable off this machine first. No
force push, no rebase, no amend, and no tag. If the ordinary push fails or the remote state
conflicts, the sequence stops there and the private catalog is not mutated.

## 6. Private evidence root

After a successful checkpoint publication, private evidence root access is authorized **solely** for
the Decision 094 transition and the E0 sequence. It is resolved through the accepted mechanism —
the fixed unlogged `DISCLOSURE_DRIFT_EVIDENCE_ROOT` variable, through the external-root boundary,
resolved once per process and cached, with no `$HOME` traversal (Decision 093 §10; Decision 095
R80). The root's value is never printed, logged, persisted, copied, or otherwise disclosed.

Network authority remains **NONE**. SEC, HTTP, DNS, socket, and fetch authority remain **NONE**.
`REQUEST_CEILING` remains **0**.

## 7. Transition instrument — `0013 -> 0014 -> 0015`

The exact Decision 094 §5 transition is **authorized**, through the accepted operator surface and no
other mechanism. Migration `0016` remains unauthorized and is never selected.

The activation is the bounded, constant-only source change Decision 094 §7.2 reserves. Exactly one
constant changes, to exactly this governed token:

```text
PRE_E0_CATALOG_TRANSITION_AUTHORITY = "M3_3_D101_PRE_E0_CATALOG_TRANSITION_AUTHORIZED"
```

Its SHA-256 is recorded as `owner_authority_sha256` in the transition terminal record. Because the
shipped-source assertions in `tests/unit/test_m3_e0.py` pin the pre-activation literals, the exact
consequential test updates that restate those assertions against the activated state are authorized
with the constant change, and nothing else in the suite may be altered to accommodate it.

Every frozen Decision 094 §5.2 preflight predicate is required, and the under-lease recheck is
required before mutation — including catalog identity and head exactly `0013`, the empty-state and
representability preconditions, all three integrity gates, lease policy, the already-existing
operator-owned namespace parent, the Decision 099 R97 M3.2 completion-receipt/catalog binding with
its exact T7 → T6 chain, receipt digests and ids, run rows, terminal states and timestamps,
attempt-ledger agreement at cumulative **77** physical attempts, the T7 observation attribution, and
the backup and recovery prerequisites. A failed predicate, in preflight or under lease, stops the
sequence; E0 does not follow.

Governed backup, ledger, postcheck, terminal, receipt, and verification behaviour is required as
Decision 094 §§5.3 and 8 specify. After execution, the transition is independently verified: a
COMPLETE terminal, a verify PASS, a migration chain exactly through `0015`, integrity PASS, backup
and provenance binding PASS, no unauthorized migration, no network or request activity, and an
unambiguous recovery state. A FAILED, INTERRUPTED, or UNDETERMINED result, or any verification that
is not PASS, stops the sequence.

## 8. E0 instrument — one invocation

**If and only if** the transition completes and verifies under §7, one M3.3-E0 execution is
authorized under the already-accepted Decision 093–100 architecture. This is the separate
one-invocation release Decision 094 §12.4 step 8 reserves; the owner's conditional authorization in
the same instrument that accepted Decision 100 supplies step 7's acceptance for the transition
result. No further architecture review or optimization step is inserted.

The activation is again constant-only, to exactly this governed token:

```text
M3_3_E0_EXECUTION_AUTHORITY = "M3_3_D101_E0_EXECUTION_AUTHORIZED"
```

Its SHA-256 is recorded as `owner_authority_sha256` in the E0 terminal record. Transition activation
never enabled E0, and E0 activation enables no later stage.

Everything the accepted architecture requires is preserved without exception: the exact Decision 091
document, review, and span evidence; the canonical relational association model; complete
association sets; no observation or scalar fallback; no entity invention; the Decision 096
pre-association invalid-CIK protection; the Decision 097 M19 disposition; Decision 099 R96 durable
failure-terminal projection, R97 provenance binding, and R98 catalog-aware verification; and
Decision 100 commit-before-event representability. Every accepted freeze and identity rule stands,
including the Decision 093 §10 invariants — project Python 3.12, the storage context-manager API,
one cached root resolution, the order compute → validate → independently recompute every identity
from persisted rows → verify integrity → then freeze, no self-referential identity preimage, and
field-aware private-path validation.

E0 remains **OFFLINE**. On any failure the accepted fail-closed semantics govern: no auto-resume, no
manufactured success or completeness, and no migration `0016`.

## 9. Post-E0 boundary

After verified E0 completion the sequence **stops** before any new write-stage architecture. No
migration `0016`, no persistence bridge, no M3.3-E1, no M3.3-E2, and no M3.4. The already-designed
read-only post-E0 R52 linkage diagnostic may run after E0 verification only if existing accepted
authority unambiguously permits it, must remain read-only, and its results are never converted into
a new owner ruling by the executing session.

Both request counts — actual logical requests and actual physical attempts — remain exactly **0**
across this entire sequence.

## 10. Governance recording

This record, one `Docs/Decisions/decision_registry.md` row, one `Docs/decision_index.md` block, and
the truthful synchronization of [`Milestones/STATUS.md`](../../Milestones/STATUS.md) are recorded
together in one minimal governance commit, before the checkpoint push. No earlier accepted Decision
is rewritten. The two constant-only activation changes are separate later local commits, each in its
own place in the sequence above, and neither is pushed by this instrument.

```text
RESULT_TOKEN: M3_3_D100_PRE_E0_IMPLEMENTATION_OWNER_ACCEPTED
NEXT_ACTION: GOVERNANCE COMMIT, CHECKPOINT PUSH, TRANSITION 0013 -> 0015, THEN ONE E0 INVOCATION
M3_3_E0_OPERATIONAL_STATE: AUTHORIZED — CONDITIONAL ON A COMPLETE AND VERIFIED TRANSITION
```
