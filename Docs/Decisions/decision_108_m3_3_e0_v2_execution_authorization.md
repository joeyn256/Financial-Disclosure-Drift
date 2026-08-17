# Decision 108 — Authorization of Exactly One Real M3.3-E0 (v2) Execution, and the Withdrawal of the Spent Transition Grant

```text
STATUS: ACCEPTED — OWNER AUTHORIZATION OF ONE REAL M3.3-E0 (v2) EXECUTION
DATE: 2026-08-17
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D108_E0_V2_EXECUTION_AUTHORIZED
D107_REAL_STALE_LEASE_RECOVERY: OWNER-ACCEPTED AND CLOSED — token M3_3_D107_REAL_STALE_LEASE_RECOVERY_OWNER_ACCEPTED
BLOCKER: 0
MAJOR: 0
E0_V2_EXECUTION: AUTHORIZED — EXACTLY ONCE
M3_3_E0_EXECUTION_AUTHORITY: M3_3_D108_E0_V2_EXECUTION_AUTHORIZED
STALE_WRITER_LEASE_RECOVERY_AUTHORITY: None — SPENT, REMAINS DISABLED
PRE_E0_CATALOG_TRANSITION_AUTHORITY: None — SPENT, WITHDRAWN BY THIS RECORD
POST_INVOCATION_E0_AUTHORITY: MUST RETURN TO None
MIGRATION_0016_AUTHORIZATION: NO
PERSISTENCE_BRIDGE_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE — except the two ordinary Git pushes in §7
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
R52_LINKAGE_DIAGNOSTIC: AUTHORIZED — READ ONLY, POST-VERIFICATION ONLY
FURTHER_INDEPENDENT_REVIEW: NOT REQUIRED
```

This record authorizes **one** real offline operation against the accepted private evidence root, and
it leaves every other governed capability shut — two of them shut *by this record*, because their
grants are spent. It writes no research code, changes no frozen research definition, reads no outcome
value, applies no migration, contacts no network, and redesigns nothing. Decisions 091–107 remain
binding on every point they name, and the frozen
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md),
[Decision 104](decision_104_m3_3_d103_recovery_activation_correction.md),
[Decision 105](decision_105_m3_3_unreadable_writer_lease_fail_closed.md),
[Decision 106](decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md),
and [Decision 107](decision_107_m3_3_real_stale_writer_lease_reconciliation.md) records are **not
rewritten**.

## 1. The accepted entry state

The one real stale-writer-lease reconciliation
[Decision 107](decision_107_m3_3_real_stale_writer_lease_reconciliation.md) §3 (**R116**) authorized
has been executed **exactly once**, verified against real state on every §6 obligation, and is
**OWNER-ACCEPTED AND CLOSED** under owner token
`M3_3_D107_REAL_STALE_LEASE_RECOVERY_OWNER_ACCEPTED`, at **BLOCKER 0 / MAJOR 0**.

The accepted published state is `0d699a149cd74dedbbcae1b907a431ff6ba35fd6` on `main` and
`origin/main` alike. The accepted measured private state is:

| Fact | Accepted state |
|---|---|
| Writer lease | `released` |
| Recovery namespace | present, spent, create-once |
| Catalog | migration head `0015`, `0016` absent, integrity PASS |
| Accepted catalog logical identity | MATCH |
| Accepted observation-set identity | MATCH |
| v1 predecessor | present, valid event ledger, 2 events, no terminal, no receipt, no closing event |
| v1 classification | `UNDETERMINED / NOT COMPLETE` |
| Latest real read-only E0-v2 preflight | PASS across every frozen successor predicate |

**No additional recovery work is authorized**, and none is needed. `STALE_WRITER_LEASE_RECOVERY_AUTHORITY`
is `None` and **remains** `None` under this record;
[Decision 107](decision_107_m3_3_real_stale_writer_lease_reconciliation.md) §5 (**R118**) withdrew
that grant on verified completion, the ladder would refuse a second reconciliation independently
because the lease no longer records `held` and the create-once namespace exists, and nothing here
reactivates it. A second real reconciliation would still require both a new owner instrument and a
reviewed source change to a `…_v2` recovery generation.

The §9 read-only E0-v2 preflight that record authorized was a **measurement**, and a PASS was a fact
about the world rather than permission to run E0-v2. This record is the separate owner instrument
[Decision 107](decision_107_m3_3_real_stale_writer_lease_reconciliation.md) §5 reserved. It is issued
**on** that evidence; it was not granted **by** it.

## 2. Ruling R120 — exactly one real E0-v2 execution is authorized

Exactly **one** real M3.3-E0 (v2) execution is **AUTHORIZED**.

The activation constant `M3_3_E0_EXECUTION_AUTHORITY` in `src/disclosure_drift/m3/e0.py` is set, by
reviewed source change and by nothing else, to exactly:

```text
M3_3_D108_E0_V2_EXECUTION_AUTHORIZED
```

The authorized operation is exactly:

```text
disclosure-drift m3 offline-parse --config configs/project.yaml --mode execute
```

invoked **once**, through that governed operator surface. No direct-library substitute, no second
`execute`, no retry, no manual catalog edit, no manual namespace edit, no migration, no network.

**Activation is necessary and never sufficient.** Every frozen
[Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md) §5 predicate and every
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §10 successor predicate still runs,
still conjunctively, still fail-closed. No flag, environment value, configuration field, preflight
result, catalog state, lease state, namespace, or receipt substitutes for any predicate, and a
passing `preflight` remains a measurement rather than permission. `preflight` remains strictly
read-only.

Per [Decision 104](decision_104_m3_3_d103_recovery_activation_correction.md) §3 (**R114**), the
durable terminal record binds the authority **actually active** for the execution — the value
`_require_activation` returns — so `owner_authority_sha256` in the real E0-v2 terminal is the SHA-256
of the token above and of nothing else. The token's value is never printed, logged, or persisted;
only its digest is.

The E0 run namespace remains exactly `m3_3_e0_offline_parse_v2`, per
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §3 (**R105**). There is no
`--run-namespace`, no environment override, and no configuration field. The interrupted
`m3_3_e0_offline_parse_v1` predecessor is immutable evidence under
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §4 (**R106**): it is **validated** by
the successor, and it is not repaired, resumed, renamed, overwritten, deleted, closed, or read as a
prefix of v2.

**This record authorizes no second E0-v2 invocation.** If the process starts, the grant is spent
regardless of outcome — see §5.

## 3. Ruling R119 — the spent PRE-E0 catalog transition grant is withdrawn

`PRE_E0_CATALOG_TRANSITION_AUTHORITY` is set to `None` by the same reviewed-source-change mechanism,
and the [Decision 101](decision_101_m3_3_d100_owner_acceptance_and_transition_e0_authorization.md) §7
literal is not retained anywhere in the module.

That grant authorized exactly one `0013 -> 0014 -> 0015` transition. The transition ran to a COMPLETE
and verified terminal, so the authorization was **consumed by its one use**, and a consumed grant
left lying in source is a value a later reader can mistake for a live one — the same reason
[Decision 104](decision_104_m3_3_d103_recovery_activation_correction.md) removed Decision 103's
illustrative literal and [Decision 107](decision_107_m3_3_real_stale_writer_lease_reconciliation.md)
§5 removed its own spent token. `m3 prepare-e0-catalog --mode execute` therefore returns exit `3`
through the ordinary `_require_activation` door, ahead of private-root resolution.

This withdrawal is **safe for E0** and is not a change to E0's inputs. E0 reads the *completed
transition terminal record* as a predicate; it does not re-derive that terminal from this constant,
and no verification path recomputes an authority digest from it. The digest already bound in the
transition terminal is historical evidence of the authority that ran, and it is unaffected.

The intended capability state immediately before the real execution is therefore:

| Capability | State |
|---|---|
| `m3 offline-parse --mode execute` (E0-v2) | **ENABLED** — by the exact R120 token, for exactly one invocation |
| `m3 prepare-e0-catalog --mode execute` | **DISABLED** — `PRE_E0_CATALOG_TRANSITION_AUTHORITY` is `None` |
| `m3 reconcile-writer-lease --mode execute` | **DISABLED** — `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` is `None` |

The two spent capabilities remain disabled for the whole of this record's sequence and are not
reactivated by it, by the execution, or by the execution's success.

## 4. Ruling R121 — required preflight and required verification

**Immediately before execution, and after publication**, exactly one fresh real read-only E0-v2
preflight is run, and **every** frozen predicate must PASS — including a valid and released writer
lease, an available exclusive writer lock, migration chain exactly `1..15` at applied head `0015`
with `0016` absent, `quick_check` PASS, `integrity_check` PASS, foreign-key violations `0`, accepted
catalog logical identity MATCH, accepted observation-set identity MATCH, a present COMPLETE and valid
transition terminal, a present immutable v1 predecessor with a valid 2-event chain and no terminal,
no execution receipt and no closing event, an absent v2 namespace, all thirteen precondition tables
satisfying the frozen empty-state requirement, planned source count `76` with all `76`
`parser_state = not_started`, census parser-run count `0`, satisfied disk headroom, both network
switches disabled, and E0 `execute` enabled by exactly the R120 authority. **If any predicate fails
or changes, that is a stop and E0 is not executed.**

The execution is not complete until it is verified against real state through the accepted production
verification surfaces. At minimum: the v2 run namespace exactly `m3_3_e0_offline_parse_v2` with a
COMPLETE terminal whose `terminal_record_id` and result token both recompute, a valid event ledger
contiguous from `1` whose head identity recomputes, a canonical execution receipt where governed, and
**no sequence or head inheritance from v1**; the catalog still at chain `1..15`, head `0015`, `0016`
absent, `quick_check` and `integrity_check` ok, foreign-key violations `0`, and the governed
catalog-state identity recomputing; planned source count `76` with source-result totality satisfying
accepted [Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md),
[Decision 099](decision_099_m3_3_post_d098_bounded_correction.md), and
[Decision 100](decision_100_m3_3_commit_before_event_representability.md) semantics, every durable
source disposition represented exactly once, disposition counts reconciling, parser state and result
identities reproducing, **no invented source and no observation or scalar fallback**; a valid
canonical relational association materialization with the complete association-set rules enforced and
`association_totality` valid, **no entity invention and no scalar anchor used as canonical
association scope**; all governed table hashes, the parser-state hash, and the E0 catalog-state hash
reproducing, FK/integrity/content validations PASS, freeze identities independently recomputing, and
**no self-referential identity preimage**; E0-v2 owning its own backup with v1 backup and evidence
untouched and the required provenance identities reconciling; and
`actual_logical_request_count = 0`, `actual_physical_attempt_count = 0`, with no SEC, EDGAR, HTTP, or
DNS activity of any kind.

Any unexpected change to governed real state is a **stop**, classified MAJOR or BLOCKER. On failure,
interruption, an undetermined outcome, a permission block, or verification inconsistency: the run is
**not** re-run, **not** resumed, and **not** manufactured into completion; v2 evidence is **not**
removed or overwritten; v1 evidence is **not** modified; the catalog is **not** repaired by hand; and
the exact measured state is returned to Sol/GPT-5.6 after the §5 shutdown.

## 5. Ruling R122 — the execution authority is withdrawn after the one invocation

The activation granted by **R120** is spent by its one use. **After the single real E0-v2 invocation
has returned — whether COMPLETE or not — `M3_3_E0_EXECUTION_AUTHORITY` is set back to `None`** by a
further reviewed source change, and both `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` and
`PRE_E0_CATALOG_TRANSITION_AUTHORITY` **remain** `None`.

All three governed execute surfaces therefore ship **disabled** at the end of this record's sequence.
A second real E0 execution would require both a new owner instrument and a reviewed source change to
a `…_v3` generation, exactly as
[Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §3 (**R105**) requires of a second E0.

No spent capability is reactivated. A verified E0-v2 is not linkage-gate closure, migration `0016`
authority, persistence-bridge authority, E1 authority, E2 authority, or M3.4 authority; each remains a
separate owner act.

## 6. Ruling R123 — the post-E0 R52 linkage diagnostic, read only

**Only if** E0-v2 is COMPLETE **and** independently verified, the accepted post-E0 R52 linkage
diagnostic is authorized as **READ ONLY**. It authorizes no methodology change and no persistence
write.

It runs against the accepted
[Decision 091](decision_091_m3_3_single_pass_document_evidence_protocol.md) durable Review-A
evidence, in the canonical export
[Decision 093](decision_093_m3_3_review_evidence_durability_and_linkage_resolution.md) §§3-5 fixes. The input denominator is **exactly the 96 accepted form+date assertions**;
the six form-only partials remain visible but stay **outside** the linkage denominator. Resolution is
through the canonical relational association E0 establishes, and each eligible assertion is classified
only under the accepted exact resolver as `ZERO`, `EXACTLY_ONE`, `MULTIPLE`, or
`UNESTABLISHED_ASSOCIATION_SET`. **No name inference, ticker inference, fuzzy matching, scalar
fallback, observation fallback, or entity invention.**

For `EXACTLY_ONE` cases, acceptance ordering is assessed separately and only from accepted native
authority. Where the native original acceptance timestamp remains unavailable, the reported result is
`ORDERING_UNAVAILABLE`, per
[Decision 093](decision_093_m3_3_review_evidence_durability_and_linkage_resolution.md) §§7-8.
**Missing ordering evidence is never converted into a PASS.**

The report states at minimum the eligible denominator of 96, the count in each linkage
classification, the count eligible for acceptance-order evaluation, the acceptance-order
PASS / FAIL / `ORDERING_UNAVAILABLE` counts as supported, the six form-only partials separately, and
the exact diagnostic evidence or output identity where governed.

**The executing session does not make the owner linkage-gate ruling.** The diagnostic is measurement
returned to the owner.

## 7. Publication

Two commits and two ordinary pushes, in this order, and no others.

1. **One activation/governance commit** carrying this record, the minimum registry, index, and status
   navigation, the constant changes of **R119** and **R120**, and the narrowly restated tests that
   verify them — followed by **one ordinary push of `main` to `origin/main`**. `main` must equal
   `origin/main` **before** any private state is mutated.
2. **One post-invocation shutdown/status commit** carrying the **R122** withdrawal, the restatement of
   the consequential activation and refusal tests, and the truthful outcome — followed by **one
   ordinary push of `main` to `origin/main`**.

No force push, no rebase, no amend, no tag. These two pushes are the **only** network activity this
record permits; a failed push or any divergence is a **stop**.

The first commit's gate is one `make check-fast`, captured on its first run. **If it fails, that is a
stop, and the real E0 state is neither accessed nor mutated.** The second commit's gate is the bounded
targeted activation/refusal tests plus touched-file static checks; a second full `make check-fast` is
not required for the constant-to-`None` shutdown alone, and is required if any material executable
correction beyond that deactivation is made.

## 8. Private evidence root

Bounded read and — for the one authorized execution only — write access to the accepted private
evidence root, resolved through the accepted `DISCLOSURE_DRIFT_EVIDENCE_ROOT` mechanism alone. No
filesystem discovery, no `$HOME` search, no rediscovery of the root, no disclosure of the private
absolute path in any report, and no persistence of it in the repository. Any session-local carrier
used to supply it is deleted after the operation.

The governed durable write set is exactly what the accepted E0 design already fixes: the
[Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md) §6.1 sixteen-table footprint plus
the category-A `census_plan_sources.parser_state` transition inside the operational catalog, and the
E0-v2 run namespace with its own backup, event ledger, terminal record, and execution receipt.
Nothing else beneath the private root is created, modified, or removed, and v1 evidence is untouched.

## 9. What remains prohibited

A second E0 execution; any migration, and migration `0016` specifically; the persistence bridge; E1;
E2; the final M3.3 manifest or root; M3.4; SEC; EDGAR; HTTP; DNS; any acquisition; direct SQLite
mutation; manual catalog or namespace editing; any direct-library substitute for the governed
operator surface; restoring the catalog; modifying v1 evidence; modifying completed v2 evidence; a
force push; a rebase; an amend; and a tag. Request ceiling remains **0**. Network authority is limited
to the two ordinary Git pushes §7 authorizes.

## 10. Exact next action

Return the verified E0-v2 result and the read-only R52 linkage diagnostic to Sol/GPT-5.6, and stop. Do
not re-review D103–D107; do not run a further architecture audit, implementation audit, independent
second review, or optimization pass. MINOR, OBSERVATION, and OPTIMIZATION findings do not delay
execution and are reported rather than acted on. Report a new issue only if it is a genuine BLOCKER,
or a MAJOR affecting execution correctness or the verification of this run.
