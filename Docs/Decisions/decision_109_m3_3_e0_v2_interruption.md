# Decision 109 — The Interrupted M3.3-E0 (v2) Execution, Its Measured Termination Cause, and Owner Acceptance of the Interruption Handoff

```text
STATUS: ACCEPTED — OWNER ACCEPTANCE OF THE E0-v2 INTERRUPTION HANDOFF
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D109_E0_V2_INTERRUPTION_OWNER_ACCEPTED
E0_V2_STATE: UNDETERMINED / NOT COMPLETE
LAST_DURABLE_E0_V2_BOUNDARY: BACKUP_VERIFIED, sequence 2
TERMINAL_RECORD: ABSENT
EXECUTION_RECEIPT: ABSENT
CLOSING_EVENT: ABSENT
CATALOG: UNCHANGED FROM THE ACCEPTED PRE-E0 BASELINE
BLOCKER: 0
MAJOR: 2 — F1 AND F2, BOTH ACCEPTED
M3_3_E0_EXECUTION_AUTHORITY: None
PRE_E0_CATALOG_TRANSITION_AUTHORITY: None
STALE_WRITER_LEASE_RECOVERY_AUTHORITY: None
E0_V3_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
PERSISTENCE_BRIDGE_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record exists because the numbering would otherwise skip 109. The single real M3.3-E0 (v2)
execution [Decision 108](decision_108_m3_3_e0_v2_execution_authorization.md) §2 (**R120**)
authorized was invoked exactly once, was interrupted, and its handoff was accepted by the project
owner — but that acceptance was issued as an owner ruling and, until now, was carried only by
`Milestones/STATUS.md`. This record commits the accepted facts and the two accepted MAJOR findings
so a later session reads them from `Docs/Decisions/` rather than from a status file or a prior
session's narrative.

It **grants nothing**. Every execution authority is `None`, and it neither authorizes nor designs a
successor. The remediation the two MAJOR findings require is
[Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md); this record is the finding, not
the fix.

## 1. Owner acceptance

The E0-v2 interruption handoff is **OWNER-ACCEPTED** under the owner token

```text
M3_3_D109_E0_V2_INTERRUPTION_OWNER_ACCEPTED
```

The accepted published state at acceptance was `HEAD` `c96406984209ebd13b6a9021615c3960850ba4e0`,
`origin/main` the same commit, and a clean worktree.

## 2. The accepted interruption facts

Measured rather than inferred, and accepted as stated:

- **E0-v2 is `UNDETERMINED / NOT COMPLETE`.** It is not complete, not failed, and not durably
  interrupted: no `INTERRUPTED` and no `FAILED` event was ever written, because the process ran no
  handler.
- **The last durable boundary is `BACKUP_VERIFIED`, sequence 2.** The `m3_3_e0_offline_parse_v2`
  namespace exists as a real non-symlinked directory holding exactly `e0_events.jsonl` and
  `pre_e0_catalog_0015.sqlite3`; the ledger is chain-valid with sequences 1 and 2 continuous and
  event types `PREFLIGHT_PASSED` then `BACKUP_VERIFIED`.
- **There is no terminal record, no execution receipt, and no closing event of any kind.** The
  governed verifier classifies the run `UNDETERMINED / NOT COMPLETE` at exit 4.
- **The termination cause is established, not guessed.** The macOS unified log records the E0
  process as `python3.12` PID 67381, started 2026-08-17 20:40:46.287 EDT and terminated by the
  kernel at 2026-08-17 21:44:13.694 EDT with `memorystatus: killing largest compressed process
  Python [67381] 33911 MB`, 1.4 seconds after `memorystatus: System is unhealthy` with `swap_low 1`.
  That is a kernel memory-pressure (jetsam) kill on an 8 GiB host: SIGKILL-class, running no Python
  `except` or `finally`, which is exactly why no terminal, receipt, or closing event exists. It was
  not disk space (17 GiB free) and not an I/O error, and no crash or jetsam report names the process.
- **No catalog byte was changed by that run**, measured: file SHA-256
  `57e36a788dc8e03ea4d1a4c722418de4c4244d73590c6643feace93c80af2ded` at 359,378,944 bytes, a 0-byte
  write-ahead log, migration chain exactly 1..15 at applied head `0015` with `0016` absent,
  `quick_check` ok, `integrity_check` ok, 0 foreign-key violations, accepted catalog logical identity
  `5c823d216957c0035babd4956f9d9e0c3c0b8ea54455231436a514191c6ad306` MATCH, accepted observation-set
  identity `b1122bb9fbb084411ce3cb3b7d192c7874c8969aadbb29f6ca313543b8e533be` MATCH, all 13
  precondition tables at 0 rows, all 76 `census_plan_sources.parser_state` still `not_started`, and
  `census_parser_runs` count 0.
- **The v2 backup is present and verified** — 359,378,944 bytes, file SHA-256
  `00a808ab3ba43ace829532f9ee81a5cf47f53b31e24d80adf6026652359c973c`, logical digest matching the
  accepted pre-E0 identity and matching the `BACKUP_VERIFIED` event exactly, and byte-identical to
  the v1 backup.
- **v1 and v2 are both immutable `UNDETERMINED / NOT COMPLETE` evidence.** Neither may be deleted,
  renamed, edited, or normalized. No v3 namespace exists or is authorized.
- **[Decision 108](decision_108_m3_3_e0_v2_execution_authorization.md) §5 (R122) is applied**:
  `M3_3_E0_EXECUTION_AUTHORITY` is `None` in shipped source and the spent D108 literal is retained
  nowhere in it; `PRE_E0_CATALOG_TRANSITION_AUTHORITY` and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY`
  both remain `None`.

## 3. Finding F1 — MAJOR, accepted

**The offline parser as shipped at `c964069` is not executable safely on this 8 GiB host.**

The measured evidence: the process ran approximately 63 minutes; the kernel killed Python under
memory pressure; the kernel reported approximately 33.9 GB of compressed process memory; the host was
under `swap_low`; and **not one of 76 planned sources reached a durable catalog boundary**.

A v3 retry using materially identical parser mechanics is **PROHIBITED**.

## 4. Finding F2 — MAJOR, accepted

**Ordinary `CatalogWriter` acquisition can overwrite a persisted stale `held` lease after obtaining a
free advisory `flock`, and does so *before* the ordinary E0 predicates refuse.**

That destroys interruption provenance before the governed stale-lease recovery path can act. It is
what happened here: the stale `held` lease the jetsam kill left behind was overwritten 3.96 seconds
later by a post-kill attempt that was itself then refused by create-once namespace gating, and the
original lease is **unrecoverable**. That refused attempt is durable evidence in its own right — it
acquired the lease at 01:44:17.650826Z, passed the full under-lease recheck of every mutable
predicate, was refused, and released the lease at 01:44:33.497032Z; it did not restart E0 and it
wrote no catalog byte.

This evidence-loss class must be fixed before another real E0 generation.

## 5. Findings F3-F5 — non-blocking

The owner accepted F3, F4, and F5 as **non-blocking observations and governance debt as reported**.
Their text was issued in the owner's review of the interruption handoff and was not supplied to the
session that wrote this record, so this record deliberately **does not reproduce them**: recording a
paraphrase of a finding whose wording is authoritative elsewhere would create a second, weaker copy.
This section states only their accepted disposition. Nothing in
[Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) depends on them; D110 §3 scopes
the remediation to F1 and F2 alone.

## 6. What this record does not do

- It does not authorize E0-v3, and no v3 namespace exists.
- It does not authorize migration `0016`, the persistence bridge, E1, E2, R52, SEC, EDGAR, HTTP, or
  DNS. `REQUEST_CEILING` remains 0.
- It does not modify, delete, restore, or normalize the v1 or v2 namespaces or either backup.
- It does not reopen any execution authority. All three remain `None`.
- It does not design the remediation. That is
  [Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md).

## 7. Numbering

The registry's "Open items" section already records that the index skips **102**, disposed of as an
accepted numbering gap by
[Decision 106](decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md)
§2 finding F7. **109 is not a second such gap**: this record closes it. The two are different
situations — 102 was an owner-side determination never committed as a record, and this one is a
committed record written after the fact for an acceptance that had been carried only by
`Milestones/STATUS.md`.
