# Decision 107 — Authorization of Exactly One Real Stale-Writer-Lease Reconciliation, and the Capability Separation That Precedes It

```text
STATUS: ACCEPTED — OWNER AUTHORIZATION OF ONE REAL STALE-WRITER-LEASE RECONCILIATION
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D107_REAL_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED
D106_REAL_STATE_PREFLIGHT: OWNER-ACCEPTED — token M3_3_D106_REAL_RECOVERY_PREFLIGHT_OWNER_ACCEPTED
MEASURED_L1_L11: PASS
BLOCKER: 0
MAJOR: 0
REAL_LEASE_RECONCILIATION_EXECUTION: AUTHORIZED — EXACTLY ONCE
STALE_WRITER_LEASE_RECOVERY_AUTHORITY: M3_3_D107_REAL_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED
M3_3_E0_EXECUTION_AUTHORITY: None — SET TO None BY THIS RECORD, BEFORE RECONCILIATION
E0_V2_EXECUTION_AUTHORIZATION: NO
POST_RECOVERY_RECOVERY_AUTHORITY: MUST RETURN TO None
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE — except the two ordinary Git pushes in §7
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
FURTHER_INDEPENDENT_REVIEW: NOT REQUIRED
```

This record authorizes **one** real operation against **one** governed sidecar document, and it
disables a second, unrelated capability first so that the one operation cannot become two. It writes
no research code, changes no frozen research definition, reads no outcome value, applies no
migration, and redesigns nothing. Decisions 091–106 remain binding on every point they name, and the
frozen [Decision 103](decision_103_m3_3_e0_interruption_recovery.md),
[Decision 104](decision_104_m3_3_d103_recovery_activation_correction.md),
[Decision 105](decision_105_m3_3_unreadable_writer_lease_fail_closed.md), and
[Decision 106](decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md)
records are **not rewritten**.

## 1. The accepted D106 real-state preflight

The one read-only real-state preflight
[Decision 106](decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md)
§6 authorized has been executed and its result is **owner-accepted**, under owner token
`M3_3_D106_REAL_RECOVERY_PREFLIGHT_OWNER_ACCEPTED`, at **BLOCKER 0 / MAJOR 0**.

Every applicable [Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §5 predicate was
directly measured against the real private state and **PASSED**:

| Predicate | Measured real result |
|---|---|
| **L1** | persisted writer-lease state is `held` |
| **L2** | the lease document is structurally valid |
| **L3** | the recorded host fingerprint matches this host |
| **L4** | the recorded writer PID is not alive |
| **L5** | no other active catalog writer; the write-ahead log is acceptable |
| **L6** | an exclusive non-blocking advisory lock is obtainable read-only, without creating or mutating the lease |
| **L7** | the lease has passed its recorded expiry |
| **L8** | catalog `quick_check` PASS, `integrity_check` PASS, foreign-key violations `0` |
| **L9** | catalog logical digest and observation-set digest both equal the accepted recovery baseline |
| **L10** | both tracked network switches disabled |
| **L11** | the recovery namespace is **absent** |

**`L12` remains exempt from real-state proof**, exactly as
[Decision 106](decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md)
§6 rules: it is a control-flow property of the execute path — that the exclusive lock is held
continuously across reassertion and mutation — and no read-only measurement can establish it.

The §7 nonmutation obligation was discharged: the measured real state's **byte and logical
identities were unchanged** across the preflight. The catalog measured migration chain `1..15`,
applied head `0015`, migration `0016` **absent**, integrity **PASS**, foreign-key violations `0`,
accepted catalog logical identity **MATCH**, accepted observation-set identity **MATCH**, and a
write-ahead log of **0 bytes**. Both tracked network switches measured `false`.

## 2. The v1 predecessor state, accepted

The read-only v1 predecessor measurement is **owner-accepted as reported**. The
`m3_3_e0_offline_parse_v1` namespace is **present**, is a **real non-symlinked directory**, carries a
**valid two-event ledger**, has **no terminal record**, **no execution receipt**, and **no closing
event**, and is therefore **`UNDETERMINED / NOT COMPLETE`**.

That classification is accepted as the permanent historical status of the interrupted run.
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §4 (**R106**) is unchanged and
controls: v1 is immutable interrupted evidence, and is not repaired, resumed, renamed, overwritten,
deleted, closed, or converted into success evidence by this record or by the operation it
authorizes.

## 3. Ruling R116 — exactly one real stale-lease reconciliation is authorized

The real stale writer lease is **ELIGIBLE**, and exactly **one** reconciliation of it is
**AUTHORIZED**.

The activation constant `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` in
`src/disclosure_drift/m3/e0.py` is set, by reviewed source change and by nothing else, to exactly:

```text
M3_3_D107_REAL_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED
```

This is the "separate owner instrument"
[Decision 104](decision_104_m3_3_d103_recovery_activation_correction.md) §2 (**R113**) and
[Decision 106](decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md)
§8 each reserved. It replaces **only** that literal. Nothing else about the recovery architecture is
touched: the conjunctive fail-closed `L1`–`L12` ladder, under-lock reassertion, the truthful
`held -> released` reconciliation, the continuously held advisory lock, measured catalog
nonmutation, the create-once recovery namespace, and the write-once recovery record are all
preserved exactly as [Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §§5–9 define them.

**Activation is necessary and never sufficient.** The complete `L1`–`L12` ladder still runs, still
conjunctively, still fail-closed. No flag, environment value, configuration field, preflight result,
catalog state, lease state, namespace, or receipt substitutes for any predicate, and a passing
`preflight` remains a measurement rather than permission. `preflight` remains strictly read-only.

Per [Decision 104](decision_104_m3_3_d103_recovery_activation_correction.md) §3 (**R114**), the
durable recovery record binds the authority **actually active** for the execution — the value
`_require_activation` returns — so `owner_authority_sha256` in the real record is the SHA-256 of the
token above and of nothing else. The token's value is never printed, logged, or persisted; only its
digest is.

The authorized operation is exactly:

```text
disclosure-drift m3 reconcile-writer-lease --config configs/project.yaml --mode execute
```

invoked **once**, through that governed operator surface. No direct-library substitute, no second
`execute`, no retry. An `execute` that begins and returns anything other than the accepted successful
outcome is a **stop**, and the resulting evidence is preserved rather than repaired, re-run, or
deleted.

## 4. Ruling R117 — E0-v2 execution is disabled before the lease is touched

This is capability separation, and it is not an architecture redesign.

`M3_3_E0_EXECUTION_AUTHORITY` currently carries the historical
[Decision 101](decision_101_m3_3_d100_owner_acceptance_and_transition_e0_authorization.md) §8 token.
That authorization was issued for the **v1** generation and was consumed by the invocation that was
interrupted; the only thing that has kept E0-v2 from proceeding since is the stale lease this record
authorizes clearing. **Leaving E0 executable across that reconciliation would mean the successful
removal of the blocker silently re-enabled a second, separately governed operation** — which is
precisely what an activation constant exists to prevent.

Therefore, **before any private state is touched**, `M3_3_E0_EXECUTION_AUTHORITY` is set to `None`
by the same reviewed-source-change mechanism. `m3 offline-parse --mode execute` is **NOT ENABLED**
and returns exit `3` through the existing `_require_activation` door, ahead of private-root
resolution, consulting no lease, catalog page, namespace, or receipt.

The intended state immediately before the real recovery is therefore:

| Capability | State |
|---|---|
| `m3 reconcile-writer-lease --mode execute` | **ENABLED** — by the exact R116 token, for exactly one invocation |
| `m3 offline-parse --mode execute` (E0-v2) | **DISABLED** — `M3_3_E0_EXECUTION_AUTHORITY` is `None` |

`PRE_E0_CATALOG_TRANSITION_AUTHORITY` is **untouched** and remains exactly as
[Decision 101](decision_101_m3_3_d100_owner_acceptance_and_transition_e0_authorization.md) §7 set it.
The transition is complete and verified; this record neither re-authorizes nor withdraws it.

**No E0-v2 execution is authorized by this record**, before, during, or after the reconciliation.

## 5. Ruling R118 — the recovery authority is withdrawn after verified completion

The activation granted by **R116** is spent by its one use. **After** the reconciliation has
completed and been fully verified against real state,
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` is set back to `None` by a further reviewed source change,
and `M3_3_E0_EXECUTION_AUTHORITY` **remains** `None`.

Both surfaces therefore ship **disabled** at the end of this record's sequence. A second real
reconciliation of this catalog would require both a new owner instrument and a reviewed source change
to a `…_v2` recovery generation, exactly as
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §3 (**R105**) requires of a second E0.

**A later, separate owner instrument is required to authorize E0-v2.** Verified completion of this
reconciliation is not that instrument, does not imply it, and does not create it.

## 6. Required verification of the real reconciliation

The reconciliation is not complete until it is verified against real state. At minimum:

**The lease.** Persisted state exactly `released`; the original `lease_id` and `writer_pid`
preserved; the governed host fingerprint, acquisition, and expiry provenance preserved;
`released_at_utc` **not** falsely written, so a voluntary release by the dead writer cannot be
inferred; `reconciliation_reason` exactly `owner_authorized_stale_writer_recovery`;
`reconciled_at_utc` present; `reconciled_prior_state` exactly `held`; and the result structurally
valid through the production reader. This is
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §6 (**R108**), measured rather than
assumed.

**The record.** Exactly one recovery namespace and exactly one write-once recovery record; canonical
record bytes; `terminal_record_id` and `result_token` both recomputing; the record binding this
record's active authority digest; the prior lease identity matching the D106-measured and
immediately-pre-execution lease; the resulting lease identity matching the actually released lease;
the eligibility block reflecting measured real facts; logical request count `0`; physical attempt
count `0`; and no private absolute path or secret serialized.

**The catalog.** Before equals after for the file digest and byte length, the catalog logical digest,
the observation-set digest, the applied migration chain, applied head `0015`, integrity,
foreign-key violations, and the governed write-ahead-log content and length. **No catalog mutation is
permitted on any path.**

**v1.** The v1 event ledger byte-identical; no v1 terminal, receipt, or closing event; v1 still
historical `UNDETERMINED / NOT COMPLETE` evidence.

**Exactly-once.** Established without a second `execute`, from read-only inspection alone: a further
reconciliation would now refuse because the lease no longer records `held` and the create-once
recovery namespace already exists.

Any unexpected change to governed real state is a **stop**, classified MAJOR or BLOCKER. On failure,
interruption, an undetermined outcome, a permission block, or verification inconsistency: the
recovery namespace and record are **not** deleted, the lease is **not** repaired by hand, the
recovery is **not** re-run, E0 is **not** activated, and the exact measured state is returned to
Sol/GPT-5.6.

## 7. Publication

Two commits and two ordinary pushes, in this order, and no others.

1. **One activation/governance commit** carrying this record, the minimum registry, index, and status
   navigation, the two constant changes of **R116** and **R117**, and the narrowly restated tests
   that verify them — followed by **one ordinary push of `main` to `origin/main`**. `main` must equal
   `origin/main` **before** any private state is mutated.
2. **One post-recovery deactivation/status commit** carrying the **R118** withdrawal, the restatement
   of the consequential activation tests, and the verified-completion status — followed by **one
   ordinary push of `main` to `origin/main`**.

No force push, no rebase, no amend, no tag. These two pushes are the **only** network activity this
record permits; a failed push or any divergence is a **stop**.

The first commit's gate is one `make check-fast`, captured on its first run. **If it fails, that is a
stop and no private state is touched.** The second commit's gate is the bounded targeted
activation/refusal tests plus touched-file static checks; a second full `make check-fast` is not
required for the constant-restatement alone, and is required if any material executable or test
correction beyond that restatement is made.

## 8. Private evidence root

Bounded read and — for the one authorized operation only — write access to the accepted private
evidence root, resolved through the accepted `DISCLOSURE_DRIFT_EVIDENCE_ROOT` mechanism alone. No
filesystem discovery, no `$HOME` search, no rediscovery of the root, no disclosure of the private
absolute path in any report, and no persistence of it in the repository. Any session-local carrier
used to supply it is deleted after the operation.

The governed durable write set is exactly the writer-lease sidecar and the one recovery record.
Nothing else beneath the private root is created, modified, or removed.

## 9. Read-only E0-v2 preflight

After successful verified recovery **and** after both the recovery and E0 execution authorities are
disabled per **R118**, one **read-only** E0-v2 preflight is authorized, solely to measure whether the
accepted successor predicates now hold — a released and valid writer lease, an available writer lock,
migration head `0015` with no `0016`, a valid immutable v1 predecessor, an absent v2 namespace, an
acceptable catalog identity, network disabled, and every other frozen
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §10 successor predicate.

**That measurement authorizes nothing.** A `PASS` is a fact about the world, not permission to run
E0-v2, and E0-v2 is not executed.

## 10. What remains prohibited

E0-v2 execution; a second real reconciliation; any migration, and migration `0016` specifically; the
persistence bridge; E1; E2; M3.4; SEC; EDGAR; HTTP; DNS; any acquisition; direct SQLite mutation;
manual lease editing; any direct recovery-library substitute for the governed operator surface;
restoring the catalog; modifying v1 evidence; a force push; a rebase; an amend; and a tag. Request
ceiling remains **0**. Network authority is limited to the two ordinary Git pushes §7 authorizes.

## 11. Exact next action

Return the verified reconciliation result and the read-only E0-v2 preflight measurement to
Sol/GPT-5.6. Do not re-review D103, D104, D105, or D106; do not run a further architecture audit,
implementation audit, or optimization pass. Report a new issue only if it is a genuine BLOCKER, or a
MAJOR affecting the real recovery or the immediately subsequent E0-v2 safety.
