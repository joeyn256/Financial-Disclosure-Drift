# Decision 104 — Bounded Correction of the Decision 103 Stale-Writer-Lease Recovery Activation

```text
STATUS: ACCEPTED — OWNER BOUNDED CORRECTION AUTHORIZATION
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D104_RECOVERY_ACTIVATION_CORRECTED_TO_DISABLED
CORRECTS: Decision 103 §8 — the shipped VALUE of STALE_WRITER_LEASE_RECOVERY_AUTHORITY, and nothing else
SHIPPED_STALE_WRITER_LEASE_RECOVERY_AUTHORITY: None — NOT ENABLED
REAL_LEASE_RECONCILIATION_EXECUTION: NOT AUTHORIZED BY THIS RECORD
E0_V2_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record corrects exactly one MAJOR found in the Decision 103 acceptance review. It changes one
executable value and the assertions consequential on it. It creates no research architecture,
changes no frozen definition, reads no outcome value, redesigns no recovery mechanism, and grants
no execution authority of any kind. Decisions 091–103 remain binding on every point they name.

## 1. The defect

Decision 103 authorizes the *implementation* of the governed stale-writer-lease reconciliation
surface, and its own header states the boundary without qualification:

```text
REAL_LEASE_RECONCILIATION_EXECUTION: NOT AUTHORIZED BY THIS RECORD
```

Its §12 repeats the prohibition, and `Milestones/STATUS.md` records the same position: the recovery
is "a separate, explicitly invoked action that Decision 103 implements but does not authorize anyone
to run against the real evidence root."

The implementation shipped the surface's activation constant **live**:

```text
STALE_WRITER_LEASE_RECOVERY_AUTHORITY = "M3_3_D103_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED"
```

That is the whole defect, and it is a governance defect rather than a design one. Decision 103 §8's
ruling — that `execute` is gated by its own source-bound constant, held independently of the
transition and E0 constants, read through the same `_require_activation` door — is correct and is
not disturbed here. What §8 additionally did was *display the token literal*, and the implementation
read that display as an instruction to ship it. The result contradicted the record's own header: the
one remaining barrier between a governed capability and the accepted private evidence root was
removed by the same commit that built the capability.

Three observations fix why this is a MAJOR and not a cosmetic mismatch.

**An activation constant that arrives pre-activated is not a gate.** Every other execute surface in
this repository ships disabled and is activated later by an exact owner instrument that names its
token — the pattern Decision 094 §7.2 established, that Decision 095 restated as "both execute
constants `None`", and that Decision 101 §§7–8 exercised for the transition and E0 constants in two
separate acts. A constant whose enabling act is the implementation commit records no owner decision
at all.

**The barrier was the only one left.** The `L1`–`L12` ladder is an eligibility test, not an
authorization: every one of its predicates was, by Decision 102's accepted findings, already true of
the real lease. With the constant live, a single `m3 reconcile-writer-lease --mode execute` against
a resolvable private root would have reconciled the real lease and created the real recovery record
— both expressly prohibited — with no further human act.

**The two states are indistinguishable to a later reader.** A durable recovery record binds
`owner_authority_sha256`. Had one been created under the shipped literal, its digest would have
attested to a "Decision 103 authorization" that Decision 103 does not contain, and no auditor
reading the record afterwards could have told the difference.

## 2. Ruling R113 — the recovery activation constant ships disabled

`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` is `None` in production source. `execute` is therefore
**not enabled** and returns exit `3` through the existing `_require_activation` door, ahead of
private-root resolution, so the refusal is unconditional: it does not depend on whether the private
root is set, resolvable, or populated, and it consults no lease, catalog page, or namespace before
answering. On that refusal path no private state is read, created, locked, or written.

The refusal is reachable no other way. No flag, environment value, configuration field, preflight
result, catalog state, lease state, namespace, or receipt substitutes for the constant, and Decision
103 §8's prohibition on `--force`, `--pid`, `--lease-id`, `--host`, `--catalog`, `--lease-file`,
`--evidence-root`, `--ignore-lock`, `--skip-check`, `--run-namespace`, and `--network` is unchanged.

`preflight` remains exactly what Decision 103 §8 made it: strictly read-only, writing nothing,
running every applicable predicate, and reporting a sanitized verdict. R113 adds one thing to say
about it — **a passing preflight neither activates the surface nor implies that it is available.**
The report renders `reconciliation_enabled` as a measured fact, so an operator who reads a `PASS`
reads alongside it that the reconciliation is not enabled. A passing preflight is a measurement, not
permission and not a reservation; the `execute` immediately following it still refuses.

A later exact owner instrument may replace **only** this literal with its governed token, authorizing
**exactly one** real stale-lease reconciliation, and create a new local commit. That instrument does
not exist. Nothing in this record is it.

## 3. Ruling R114 — the durable record binds the authority actually active

Decision 103 §9 (R111) requires the recovery record to bind the authority identity as
`owner_authority_sha256`. R114 states the property that requirement depends on, and requires it to
remain true: the digest is taken from the token **actually active for that execution** — the value
`_require_activation` returns and `_lease_recovery_record` receives — and never from a literal
carried inside the record builder.

The distinction is not academic now that the shipped constant is `None`. A record builder holding a
hardcoded Decision 103 token would emit a record attesting to an authority the run did not hold,
which is precisely the confusion §1's third observation describes. The implementation already
threads the returned value through, so R114 is a preservation ruling and requires no redesign; it is
stated because it is the property a future change could silently lose, and it is now asserted
adversarially rather than positively — the test requires the bound digest to equal the injected
token's *and* to differ from the Decision 103 literal's.

## 4. What this record does not change

Every element of the Decision 103 recovery architecture is preserved exactly: the fixed
`m3_3_e0_offline_parse_v2` successor generation (§3, R105); v1's status as immutable interrupted
evidence and the predecessor validation the successor performs (§4, R106); the conjunctive
fail-closed `L1`–`L12` eligibility ladder (§5, R107); the under-lock reassertion of every mutable
predicate (§§5, 7); the truthful `held -> released` reconciliation that withholds `released_at_utc`
and records `reconciliation_reason` (§6, R108); the continuously held `flock` and the documented
lock-continuity-over-rename trade (§7, R109); measured catalog nonmutation through
`SQLITE_OPEN_READONLY` (§7, R109); the operator surface's exact option set and exit table (§8,
R110); the create-once namespace and the write-once recovery record (§9, R111); the fail-closed v2
successor preflight and successor gating (§10, R112); and zero network or request semantics
throughout.

Decision 103 §1's two implementation gaps **F1** (the unreachable successor namespace) and **F2**
(the unreconcilable stale lease) keep their §§3–4 dispositions unchanged.

The Decision 103 acceptance review that produced this correction is an owner-side artifact and is
not a repository record; its findings are named here only to bound what this correction touches.
**Exactly one** of them — the MAJOR that the surface ships with its activation constant live — is
dispositioned, by §§2–3 above. The review's findings **F1**, **F2**, **F3**, **F4**, **F6**, **F7**,
**F8**, and **F9** are **not** reopened, re-argued, or re-dispositioned by this record, and nothing
here should be read as accepting, rejecting, or modifying any of them.

The other two activation constants are untouched and remain exactly as Decision 101 §§7–8 set them:
`PRE_E0_CATALOG_TRANSITION_AUTHORITY` and `M3_3_E0_EXECUTION_AUTHORITY` are both active, each under
its own governed token, and neither is affected by this correction in either direction. Ordinary E0
and transition authority is unchanged. The ordinary E0 preflight, execute, and verify surfaces
continue to refuse a persisted lease state of `held`, which is the refusal the recovery surface
exists to avoid softening.

No migration is added or altered; the catalog head remains `0015` and `0016` remains absent and
unauthorized. No SQLite schema, no `configs/project.yaml` value, and no `cohorts.py` or
`pilot_policy.py` constant is touched.

## 5. Accepted-test disposition

One accepted assertion pinned the shipped constant to the Decision 103 literal:

```text
tests/unit/test_m3_stale_writer_lease_recovery.py::test_the_shipped_activation_constant_matches_the_governing_record
```

It is **restated**, not deleted or skipped, per this record's §2, as
`test_the_shipped_activation_constant_is_disabled`: it asserts the disabled definition against the
source file, asserts the module attribute is `None`, and additionally requires the Decision 103
token to be absent from the whole module — so the value cannot be reintroduced under another name,
as a default argument, or in a comment a later reader could mistake for the shipped state.

Tests that exercise successful `execute` behaviour against disposable fixtures **must inject their
own disposable activation token explicitly**, through the module's `activated` fixture or a direct
`monkeypatch` where the token's identity is itself the subject. None may rely on the shipped
constant. The complement is asserted directly:
`test_execute_is_unreachable_under_the_shipped_activation_constant` reads the shipped value rather
than setting it, and proves refusal with the private root unset *and* set, with the complete
evidence-root file inventory byte-identical afterwards and no recovery namespace created.
`test_a_passing_preflight_neither_activates_nor_implies_mutation_authority` proves R113's preflight
clause end to end.

No other accepted test conflicted with this record.

## 6. What remains prohibited

Unchanged and still unauthorized: modifying, deleting, or reconciling the real stale lease; creating
the real recovery receipt; executing E0 v2; modifying v1 evidence; restoring the catalog; migration
`0016`; the persistence bridge; E1; E2; M3.4; network enablement; SEC, HTTP, or DNS access; a push;
and a tag. Request ceiling remains 0.

## 7. Exact next action

One local correction commit, and nothing further. The Decision 103 implementation review resumes
against the corrected commit. Only after owner acceptance of that review may a separate owner
instrument activate `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` and authorize exactly one real
stale-lease reconciliation, and only after a complete and verified reconciliation may a further
separate owner instrument authorize one E0 v2 invocation.
