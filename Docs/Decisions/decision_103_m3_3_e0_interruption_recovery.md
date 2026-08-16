# Decision 103 — M3.3-E0 Interruption Recovery: Fixed Successor Generation and Governed Stale-Writer-Lease Reconciliation

```text
STATUS: ACCEPTED — OWNER IMPLEMENTATION AUTHORIZATION
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D103_RECOVERY_IMPLEMENTATION_AUTHORIZED
SUPERSEDES: Decision 094 §7.1 — the E0 run-namespace literal only
E0_RUN_NAMESPACE: m3_3_e0_offline_parse_v2
E0_PREDECESSOR_RUN_NAMESPACE: m3_3_e0_offline_parse_v1 — IMMUTABLE INTERRUPTED EVIDENCE
V1_CLASSIFICATION: UNDETERMINED / NOT COMPLETE
STALE_LEASE_RECONCILIATION: IMPLEMENTED — SEPARATE, EXPLICITLY INVOKED, NEVER AUTOMATIC
REAL_LEASE_RECONCILIATION_EXECUTION: NOT AUTHORIZED BY THIS RECORD
E0_V2_EXECUTION_AUTHORIZATION: NO — REQUIRES A SEPARATE OWNER INSTRUMENT
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record implements the capability an interrupted M3.3-E0 run left the repository without. It
creates no research architecture, changes no frozen definition, reads no outcome value, and grants
no execution authority beyond the one it names. Decisions 091–102 remain binding on every point they
name, and nothing below reopens, weakens, or reinterprets any of them except the single
run-namespace literal §3 identifies.

## 1. Entry state

Decision 102 established, and this record accepts, the following live state.

The authorized Decision 101 sequence ran the `0013 -> 0014 -> 0015` transition to completion and
then began the M3.3-E0 offline parse under namespace `m3_3_e0_offline_parse_v1`. That run was
interrupted. Its durable state is:

| Fact | Value |
|---|---|
| E0 run namespace | `m3_3_e0_offline_parse_v1` |
| Classification | **UNDETERMINED / NOT COMPLETE** |
| Durable events | 1 `PREFLIGHT_PASSED`, 2 `BACKUP_VERIFIED` — a valid chain |
| Terminal record | absent |
| Execution receipt | absent |
| Backup | `pre_e0_catalog_0015.sqlite3`, file SHA-256 `00a808ab…59c973c` |
| Catalog migration head | `0015`; chain exactly `1..15`; migration `0016` absent |
| Catalog logical SHA-256 | `5c823d216957c0035babd4956f9d9e0c3c0b8ea54455231436a514191c6ad306` |
| Input observation-set SHA-256 | `b1122bb9fbb084411ce3cb3b7d192c7874c8969aadbb29f6ca313543b8e533be` |
| Integrity | `quick_check` ok, `integrity_check` ok, 0 foreign-key violations |
| Planned sources | 76, all `parser_state = not_started`; 0 census parser runs |
| Write-ahead log | 0 bytes |
| Persisted writer lease | `state = held`, pid `43427`, lease `4a327881…3b46`, expired `2026-08-16T22:00:35Z` |
| Network | `network.enabled = false`, `network.m3_acquire_enabled = false`, 0 requests, 0 attempts |

Decision 102 independently established that PID `43427` is dead, that no E0 process, catalog writer,
or advisory lock holder remains, and that the persisted `held` state is stale interruption residue
that no existing governed repository mechanism could reconcile. Those are accepted findings.

They leave two implementation gaps, and this record closes exactly those two:

**F1.** The successor namespace `m3_3_e0_offline_parse_v2` is unreachable, because `E0_RUN_NAMESPACE`
is frozen in source to `…_v1` and a run namespace is create-once.

**F2.** A stale persisted writer lease cannot be reconciled through any governed operator surface,
even after owner-process death, advisory-lock freedom, same-host confirmation, and catalog
nonchange are all established.

## 2. What this record does not do

It does not execute anything against the accepted private evidence root. The real stale lease is not
modified, deleted, or reconciled; the real recovery receipt is not created; E0 v2 is not run; v1
evidence is not touched; the catalog is not restored; and migration `0016`, E1, E2, M3.4, network,
SEC, and HTTP remain unauthorized at request ceiling `0`.

## 3. Ruling R105 — the fixed-namespace design is preserved, and the generation advances

The E0 run namespace advances to:

```text
E0_RUN_NAMESPACE = "m3_3_e0_offline_parse_v2"
```

and the interrupted generation is named separately and kept:

```text
E0_PREDECESSOR_RUN_NAMESPACE = "m3_3_e0_offline_parse_v1"
```

**No operator mechanism is added.** There is no `--run-namespace`, no namespace environment
override, no configuration field, no arbitrary namespace selection, and no force, resume, or
overwrite namespace control. The accepted design principle is unchanged and is the reason the
generation advanced this way rather than another: *E0's operative namespace is fixed by reviewed
source code, not chosen by an operator at runtime.* A create-once namespace an operator can name is
not create-once.

**Supersession, stated exactly.** Decision 094 §7.1 names the two production namespaces as
`m3_3_pre_e0_catalog_transition_0013_0015_v1` and `m3_3_e0_offline_parse_v1`. This record supersedes
**that E0 literal and nothing else** in §7.1: the project/runtime boundary, the absent options, the
fixed catalog path, and the test-only namespace pattern are all unchanged, and the transition
namespace is untouched. Decision 094's architecture is what made this a one-constant change.

Two documentation pointers still show the v1 literal illustratively and are **not** authority:
Decision 094 §7.1 and §5.3's example tree, and `Docs/m3/e0_execution_record_spec.md` §"Where E0
writes". Neither is a decision this record reopens; the source constant and this ruling control.

## 4. Ruling R106 — v1 remains historically visible and is validated, not ignored

Changing the current generation to v2 does not reinterpret v1. It remains namespace
`m3_3_e0_offline_parse_v1`, classification **UNDETERMINED / NOT COMPLETE**, with an immutable event
chain, no terminal, and no receipt. It may never become current-success evidence, and it is never
repaired, resumed, overwritten, deleted, renamed, or treated as a prefix of v2.

Because the successor's preflight depends on predecessor history, v1 is **validated explicitly**
rather than skipped. `_predecessor_refusals` requires, at E0 preflight and again under the writer
lease before anything is created:

1. the v1 namespace is present and is a real, non-symlinked directory;
2. it carries **no** terminal record;
3. it carries **no** execution receipt;
4. its event ledger verifies — chain, ordering, contiguity, and every digest; and
5. it records no closing event (`EXECUTION_RECEIPT_WRITTEN`, `FAILED`, or `INTERRUPTED`).

Each closes a distinct way history could be laundered. An absent v1 would mean the interrupted run
had been deleted or renamed, so absence **stops** the successor rather than reading as a clean
start. A terminal record or receipt in v1 would be a manufactured completion. A ledger that does not
chain would mean the immutable evidence had been edited.

## 5. Ruling R107 — stale-lease eligibility is conjunctive and fail-closed

A narrow stale-writer-lease reconciliation exists. It is **never automatic**: the ordinary E0
preflight, execute, and verify surfaces continue to refuse a persisted `state = held` exactly as
before, and the recovery is a separate, explicitly invoked action.

A stale held lease is eligible only when **all** of the following hold together:

| # | Predicate |
|---|---|
| L1 | persisted state is `held` |
| L2 | the persisted lease is structurally valid — every required field present, correctly typed, and no unrecognized field |
| L3 | the recorded host fingerprint matches this host, compared through the same function that wrote it |
| L4 | the recorded writer PID is not alive; a platform that will not answer reports *alive* |
| L5 | no other active catalog writer is detected — the advisory lock is free, the recorded writer is gone, and the write-ahead log is empty |
| L6 | an exclusive non-blocking advisory lock is acquired through the accepted `flock` mechanism, on a descriptor that never creates the file |
| L7 | the lease has passed its own recorded `expires_at_utc` |
| L8 | the catalog opens `SQLITE_OPEN_READONLY` and passes `quick_check`, `integrity_check`, and zero foreign-key violations |
| L9 | the catalog's logical digest **and** input observation-set digest both equal the fixed accepted recovery baseline in §1 |
| L10 | both tracked network switches are disabled |
| L11 | no conflicting recovery operation is active — the create-once recovery namespace does not exist |
| L12 | the exclusive advisory lock is held continuously across the reassertion and the mutation |

Any failure or ambiguity refuses **before** any write. No elapsed-time condition, no PID-death
condition, and no free advisory lock authorizes takeover on its own.

`L9` is answered by fixed source constants, never by operator input: Decision 103 R6 forbids a
`--catalog` or digest option, so "which catalog is this lease over" is settled by reviewed source or
not at all. The constants are keyword defaults so a disposable test can supply its own temporary
catalog's identity; production supplies neither.

`L12` is not a measurement but a control-flow property, and is implemented as one: the reassertion
and the mutation occur inside one `with` block holding one lock.

Because the ladder runs **before** the lock, everything it observed is a claim about a past instant.
The under-lock reassertion makes those claims good in two parts: the lease is required to be the
same lease — identical bytes, then identical `lease_id`, `writer_pid`, `host_fingerprint`,
`expires_at_utc`, and `state` — and `L3`, `L4`, and `L7` are then **re-measured** rather than
carried forward. `L4` is the one that can genuinely flip without a byte changing: a PID is a
reusable number, so a process that took `43427` after the ladder ran would make "the recorded writer
is gone" false at the moment the lease is rewritten even though it was true when it was checked.

## 6. Ruling R108 — the reconciled lease records the truth

The lease is **not** deleted, emptied, or made to look like a voluntary release.

The transition is `held -> released` — the state the ordinary holder-release path already writes, so
every existing reader understands it without a vocabulary change. What makes it truthful is what is
added and what is withheld:

* `released_at_utc` is **not** written. That field means "the holder released this", and the holder
  did not; it died.
* `reconciliation_reason = "owner_authorized_stale_writer_recovery"`, `reconciled_at_utc`, and
  `reconciled_prior_state = "held"` are added. No ordinary release writes any of them.
* `lease_id`, `writer_pid`, `host_fingerprint`, `acquired_at_utc`, and `expires_at_utc` are carried
  through **unchanged**.

**Interpretation of the `prior_*` provenance requirement, stated for the reviewer.** Because the
holder's own fields are preserved in place, they *are* the prior values; separate `prior_writer_pid`
and `prior_lease_id` keys in the lease file would be exact duplicates rather than new provenance,
and R4 asks for the smallest representation compatible with the existing format. The durable
recovery record binds them under explicit `prior_lease.*` names, where the two documents are
genuinely distinct. An auditor reading the reconciled lease sees `state: released`, no
`released_at_utc`, an explicit owner-recovery reason, and PID `43427` still named as the holder —
from which voluntary release cannot be inferred.

No new lease-state vocabulary is introduced.

## 7. Ruling R109 — atomicity, and the lock-continuity trade it required

Lease reconciliation is a sidecar action. It mutates no SQLite catalog page, no WAL, no migration
state, no observation, no parser state, no parser run, no E0 v1 evidence, no E0 run namespace, no
raw object, and no acquisition evidence. The catalog is opened only through
`SQLITE_OPEN_READONLY`, before and after, so the record's before/after digests are measured by a
handle that could not have changed them, and equality is *required* rather than assumed.

The rewrite preserves private-file permissions, refuses a symlink or non-regular file before the
descriptor is used, verifies the expected before-identity under the lock, re-reads and structurally
revalidates after the write, and fsyncs.

**The one place R5's wording could not be satisfied literally, and why.** R5 asks for atomic
replacement "where supported" *and* for the exclusive advisory lock to remain continuously held
across the check-and-reconcile section. For this file the two are mutually exclusive: `flock` is
held on the **inode**, so a temporary-file-plus-`rename` replacement would leave the exclusive lock
on an orphaned inode while the new file sat unlocked and open to any writer. Lock continuity wins,
and the implementation uses the in-place locked rewrite `CatalogWriter._release_lease` already
performs — the repository's existing lease-mutation pattern. The crash window is bounded rather than
eliminated:

* the replacement payload is required to be **no shorter** than the document on disk, so the file is
  never truncated first and no window exists in which it is legitimately empty;
* the write is fsynced before the caller re-reads and revalidates it; and
* a torn write leaves a document that fails structural validation, which every reader of this file
  refuses rather than interprets — so an interrupted reconciliation fails closed into owner
  adjudication, never into a false success.

**One further accepted read-side artifact.** Opening a WAL-mode SQLite database materializes an
empty `-wal` and a `-shm` index file even through a strictly read-only handle. That is the existing
behaviour of `strictly_read_only_connection` and of the accepted E0 preflight, not something this
record introduces; the database file itself stays byte-identical, and a **non-empty** WAL is refused
by `L5`.

## 8. Ruling R110 — the operator surface

```text
./.venv/bin/disclosure-drift m3 reconcile-writer-lease \
  --config configs/project.yaml \
  --mode {preflight,execute}
```

It takes exactly `--config` and `--mode`. It has no `--force`, `--pid`, `--lease-id`, `--host`,
`--catalog`, `--lease-file`, `--evidence-root`, `--ignore-lock`, `--skip-check`, `--run-namespace`,
or `--network`, because each would be a way to *assert* a predicate instead of establishing it.

There is no `verify` mode. The two Decision 094 §7 surfaces have one because a run namespace is a
durable multi-artifact state machine worth revalidating; this operation's entire result is one lease
document and one record, and `preflight` already reads both.

`preflight` is strictly read-only, runs every applicable predicate, reports a sanitized PASS or
REFUSE, and writes nothing. `execute` repeats every load-bearing predicate, acquires the exclusive
lock, reasserts the mutable eligibility immediately before mutation, performs exactly one
reconciliation, verifies the result, and exits. It is deliberately **not** idempotent: a second
`execute` refuses on two independent grounds — the lease no longer records `held`, and the
create-once recovery namespace already exists.

`execute` is gated by its own source-bound activation constant, held independently of the transition
and E0 constants and read through the same `_require_activation` door:

```text
STALE_WRITER_LEASE_RECOVERY_AUTHORITY = "M3_3_D103_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED"
```

Reconciling a stale lease is not transition authority and is emphatically not E0 authority. The
exit table is Decision 094 §7.3's, unchanged.

## 9. Ruling R111 — the durable recovery record

The action is not provable only from the changed lease JSON. One write-once record is created in a
create-once namespace:

```text
runs/m3_3_stale_writer_lease_recovery_v1/writer_lease_recovery_record.json
```

It reuses the accepted evidence primitives rather than starting a second framework: `canonical_bytes`
for serialization, `compute_terminal_record_id` for the identity over everything except the two
self-referential fields, `result_token` for the token that contains that identity, `write_once` for
`O_EXCL` immutability at mode `0600`, `create_run_namespace` for the create-once directory at mode
`0700`, and `scan_for_prohibited_content` for the §5 content guard.

The record binds the operation type, the Decision 103 authority identity as `owner_authority_sha256`
(the digest, never the token's value), the prior and resulting lease digests, byte lengths, and
states, the prior `lease_id` and `writer_pid`, every eligibility result, the catalog's logical, byte,
input observation-set, WAL, integrity, and applied-chain measurements **before and after**, the
configuration fingerprint, zero logical requests, zero physical attempts, timestamps, and the
outcome. No secret and no private absolute path is written; the only paths recorded are the two
fixed root-relative names.

**One documented scan scope.** `owner_authority_sha256` is the field name the accepted transition
and E0 terminal records already use, and §5's key-fragment guard rejects any key containing `auth`
— a guard that exists to stop an `authorization` header riding in under a plausible name. The key is
renamed **for the scan only**, so the guard's purpose is preserved while the field's value, a
64-character SHA-256 of a governed public token, is still scanned. Nothing else is exempted.

## 10. Ruling R112 — the successor preflight remains fail-closed

E0 v2's preflight keeps every existing Decision 094 §9.1 predicate and adds the predecessor gate of
§4. Before a future v2 `execute` may proceed it requires: the fixed namespace is
`m3_3_e0_offline_parse_v2`; that namespace does not already exist; v1 is present, terminal-free,
receipt-free, chain-valid, and UNDETERMINED / NOT COMPLETE; the catalog matches the accepted
successor input baseline; the writer lease is no longer `held`; the advisory writer lock is
available; the migration head is `0015` with no `0016`; and the network remains disabled.

v2 does not continue from v1's event sequence. It starts its own ledger at sequence 1 with no
inherited head, creates its own backup in its own namespace, and creates its own terminal and
receipt if it completes.

## 11. Accepted-test conflict and its disposition

One accepted assertion pinned `m3_3_e0_offline_parse_v1` as the *current* E0 namespace:

```text
tests/unit/test_m3_e0.py::test_the_production_namespaces_are_fixed_constants_of_the_accepted_shape
```

It is **updated**, not deleted or skipped, per this record's §3 supersession, and v1's separate
identity as the immutable predecessor is asserted in a new adjacent test. No other accepted test
conflicted with this record.

## 12. What remains prohibited

Unchanged and still unauthorized: modifying, deleting, or reconciling the real stale lease;
creating the real recovery receipt; executing E0 v2; modifying v1 evidence; restoring the catalog;
migration `0016`; the persistence bridge; E1; E2; M3.4; network enablement; SEC, HTTP, or DNS
access; a push; and a tag.

## 13. Exact next action

One fresh independent read-only review of the local implementation commit, against this frozen
record. Only after owner acceptance of that review may a separate owner instrument authorize the
real stale-lease reconciliation, and only after a complete and verified reconciliation may a further
separate owner instrument authorize one E0 v2 invocation.
