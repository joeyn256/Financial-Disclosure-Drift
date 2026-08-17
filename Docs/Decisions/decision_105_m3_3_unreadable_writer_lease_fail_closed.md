# Decision 105 — An Existing but Unreadable Persisted Writer Lease Must Fail Closed

```text
STATUS: ACCEPTED — OWNER BOUNDED CORRECTION AUTHORIZATION
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D105_UNREADABLE_WRITER_LEASE_FAILS_CLOSED
CORRECTS: the ordinary PRE-E0 transition / E0 lease predicate only — no Decision 103 or Decision 104 ruling is reopened
SHIPPED_STALE_WRITER_LEASE_RECOVERY_AUTHORITY: None — NOT ENABLED
REAL_LEASE_RECONCILIATION_EXECUTION: NOT AUTHORIZED BY THIS RECORD
E0_V2_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record corrects exactly one defect in the ordinary lease predicate that both bounded state
machines share. It changes one refusal path and the reader that feeds it. It creates no research
architecture, changes no frozen definition, reads no outcome value, redesigns no recovery mechanism,
and grants no execution authority of any kind. Decisions 091–104 remain binding on every point they
name.

## 1. The finding, and why it is a MAJOR

The final Decision 103 + Decision 104 technical review is accepted as technical evidence and
otherwise **PASSED**. It reported one finding at MINOR severity. The owner **reclassifies that
finding as MAJOR** and disposes of it here; every other finding in that review is owner-classified
non-blocking and is not reopened.

The finding is this. Decision 103 §7 (R109) rewrites the lease **in place**, on the descriptor whose
`flock` is held continuously, and accepts the documented trade that lock continuity outranks
rename-atomicity. A consequence the record states plainly is that the rewrite has a crash window: a
process that dies between the truncation and the completed write leaves a lease file that is not a
structurally readable document.

The ordinary predicate that both the PRE-E0 transition and E0 consult — Decision 094 §5.2 predicate
9 — read that file leniently. Its reader parsed the bytes with a permissive `json` probe and returned
the recorded state as `None` whenever it could not establish one, and its consumer refused only on
the exact comparison `state == "held"`. An unreadable lease therefore arrived as a value that is not
`"held"`, and a value that is not `"held"` read as permission to proceed.

Measured on the shipped tree before this correction, over a disposable catalog beneath a synthetic
root, with a torn lease file present:

```text
PreflightReport(passed=True, refusals=(), facts={... 'writer_lease': 'unreadable' ...})
```

Both ordinary gates returned that. The report even *named* the document unreadable in its facts and
passed anyway, which is the sharpest possible statement of the defect: the fact was measured, and
nothing acted on it.

Three observations fix why the owner treats this as MAJOR rather than cosmetic.

**It becomes load-bearing precisely when the recovery is used.** Today no reconciliation may run —
Decision 104 §2 (R113) ships `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` as `None` — so no in-place
rewrite occurs and no torn lease can be produced by this repository. The moment a separate owner
instrument authorizes one real reconciliation, the crash window opens, and the gap stops being
theoretical for exactly the operation that immediately follows it.

**The failure direction is the wrong one.** Every other predicate in the ladder and in the preflight
fails closed. This one failed *open*: the less the reader could establish about the lease, the more
freely the machine proceeded. A reader that grows more permissive as its input grows more damaged
inverts the property the whole surface is built on.

**An unaccountable lease is not an absent one.** Decision 094 finding m1 established that an
**absent** lease passes the predicate — a read-only preflight must not create the lock file to find
out whether it could take it. That ruling is about absence. It was never a ruling about a lease that
exists and cannot be accounted for, and the two must not be collapsed.

## 2. Ruling R115 — an existing lease clears the predicate only by being valid and released

An **existing** persisted writer lease clears Decision 094 §5.2 predicate 9 in exactly one way: it is
a structurally valid lease document, read through the same production reader the Decision 103 §5
(R107) eligibility ladder uses, recording exactly the state `released`. Anything else the file can
contain refuses:

* torn by an interrupted Decision 103 §7 in-place rewrite, or truncated to zero;
* not readable UTF-8 JSON, or not a JSON object;
* missing a required field, or carrying a field this repository never writes;
* carrying a field value the reader will not accept — a non-positive writer PID, an empty
  identifier, a timestamp outside the accepted UTC form;
* recording a state that is neither `held` nor `released`.

The four states the predicate distinguishes, stated so no later reader has to infer them:

| Lease on disk | Ordinary transition / E0 |
|---|---|
| valid, `held` | **refuses** — unchanged, with its own unchanged refusal |
| valid, `released` | proceeds, subject to every other predicate |
| exists, unreadable or structurally invalid | **refuses** — this record |
| absent | proceeds — unchanged, and still never created |

The invariant, stated as the thing a future change must not lose:

```text
EXISTING INVALID LEASE != RELEASED LEASE
EXISTING INVALID LEASE -> FAIL CLOSED
```

Two boundaries are part of the ruling rather than incidental to it.

**Absence keeps its accepted semantics exactly.** The refusal is conditioned on the lease being
present, so Decision 094 finding m1 is untouched: an absent lease passes, and the preflight still
does not create the file it inspects. Solving the unreadable case by tightening the absent case would
have traded one defect for a different one.

**`held` keeps its own refusal, word for word.** "A writer holds this lease" and "this is not a lease
I can read" are different facts about the world, and an operator acts differently on each. They are
reported as two distinct refusals and are never merged into one.

No new lease-state vocabulary is created. `storage/catalog.py` remains the module that defines
`held` and `released`, and the predicate imports those two constants rather than re-spelling them —
a second literal would be a second contract. `read_persisted_lease` is **not** weakened in any
direction; it is the reader the corrected predicate now uses, and a malformed document is never made
to look released.

## 3. What this record does not change

Every element of the Decision 103 recovery architecture is preserved exactly, and none of it is
reopened: the fixed `m3_3_e0_offline_parse_v2` successor generation (§3, R105); v1's status as
immutable interrupted evidence and the predecessor validation the successor performs (§4, R106); the
conjunctive fail-closed `L1`–`L12` eligibility ladder (§5, R107); the under-lock reassertion of every
mutable predicate (§§5, 7); the truthful `held -> released` reconciliation that withholds
`released_at_utc` and records `reconciliation_reason` (§6, R108); the continuously held `flock`, the
in-place-write decision, and the documented lock-continuity-over-rename trade (§7, R109); measured
catalog nonmutation through `SQLITE_OPEN_READONLY` (§7, R109); the operator surface's exact option
set and exit table (§8, R110); the create-once recovery namespace and the write-once recovery record
(§9, R111); the fail-closed v2 successor preflight and successor gating (§10, R112); and zero network
or request semantics throughout. **No rename-based lease replacement is added**, and the R109
in-place-write decision is not disturbed.

Decision 104 is preserved entire: `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` remains `None` (§2, R113),
and the durable recovery record still binds the authority actually active for the execution (§3,
R114). This record grants no reconciliation authority, activates nothing, and is not the separate
owner instrument Decision 104 §2 reserves.

The Decision 103 stale-lease eligibility ladder already refused a malformed lease at `L1`/`L2`,
through this same production reader, and that behaviour is unchanged — it is re-proved here rather
than modified.

`PRE_E0_CATALOG_TRANSITION_AUTHORITY` and `M3_3_E0_EXECUTION_AUTHORITY` are untouched and remain
exactly as Decision 101 §§7–8 set them. Transition and E0 activation semantics are unchanged; the
correction sits on the refusal path only, and a valid released lease still carries the successor
generation through to a complete terminal.

No migration is added or altered; the catalog head remains `0015` and `0016` remains absent and
unauthorized. No SQLite schema, no `configs/project.yaml` value, and no `cohorts.py` or
`pilot_policy.py` constant is touched. No accepted private evidence is read, resolved, named, or
opened, and no real lease is inspected or modified.

## 4. Accepted-test disposition

No accepted test conflicted with this record and none was deleted, skipped, or relaxed. The
regression family is additive, drives the shipped predicate rather than a test-local
reimplementation, and covers: the preserved `held` refusal; both released forms, including the
Decision 103 §6 reconciled document, which the ordinary gate must still accept; twelve unreadable or
structurally invalid documents refused at **both** ordinary gates; the reader-level proof that no
such document is ever reported as `released`; the unchanged absent-lease semantics, asserted as the
exact `(present, state, shareable)` triple and as the file still not existing afterwards; the shipped
recovery authority still `None`, asserted against the source file; and a complete successor execution
over a released lease.

Non-vacuity was demonstrated rather than assumed: restoring the pre-correction behaviour — deleting
the new refusal so an unreadable lease again produces no refusal — makes every one of the twenty-four
unreadable-lease assertions fail, and the source was restored byte-exactly afterwards.

## 5. What remains prohibited

Unchanged and still unauthorized: activating `STALE_WRITER_LEASE_RECOVERY_AUTHORITY`; modifying,
deleting, or reconciling the real stale lease; creating the real recovery receipt; executing E0 v2;
modifying v1 evidence; restoring the catalog; migration `0016`; the persistence bridge; E1; E2; M3.4;
network enablement; SEC, HTTP, or DNS access; a push; and a tag. Request ceiling remains 0.

## 6. Exact next action

One local correction commit, and nothing further, then return to Sol for owner acceptance. A
successful D105 correction closes the final recovery-implementation acceptance issue; no additional
independent review of the Decision 103 implementation is required. Only after owner acceptance may a
separate owner instrument activate `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` and authorize exactly one
real stale-lease reconciliation, and only after a complete and verified reconciliation may a further
separate owner instrument authorize one E0 v2 invocation.
