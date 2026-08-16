# Milestone 3.3 — PRE-E0 Execution-Record Specification

**Governing record:** accepted
[Decision 094](../Decisions/decision_094_m3_3_pre_e0_executability_redesign.md), as corrected by
accepted [Decision 095](../Decisions/decision_095_m3_3_d094_bounded_correction_and_remediation.md),
accepted
[Decision 096](../Decisions/decision_096_m3_3_final_pre_e0_rehearsal_correction_and_remediation.md),
and accepted
[Decision 099](../Decisions/decision_099_m3_3_post_d098_bounded_correction.md) **R96–R98**.

**Implementing module:** `src/disclosure_drift/m3/e0.py`.
**Executable companion of:** [`execution_receipt_spec.md`](execution_receipt_spec.md), which governs
the receipt this stage writes, and [`operator_runbook.md`](operator_runbook.md), which governs how an
operator invokes it.

## 0. The one rule that governs everything below

**A record describes what happened. It never authorizes what happens next.**

A passing preflight is a measurement. A COMPLETE transition terminal is not E0 authority. A COMPLETE
E0 terminal is not a candidate-snapshot pass, a linkage result, a gate closure, or M3.3-E1
authorization. Every one of those is a separate owner act, and no artifact this document describes
can substitute for one.

## 1. Scope

Two bounded state machines, and nothing else:

| Command | What it does | Durable result |
|---|---|---|
| `m3 prepare-e0-catalog` | The exact `0013 -> 0014 -> 0015` accepted-catalog transition (Decision 094 §5) | `catalog_transition_terminal.json` |
| `m3 offline-parse` | The real M3.3-E0 offline metadata parse (Decision 094 §9) | `e0_terminal.json` |

Each has three modes — `preflight`, `execute`, `verify` — and each takes exactly `--config` and
`--mode`. There is no `--evidence-root`, `--catalog`, `--data-root`, `--run-namespace`, migration
list, force, resume, overwrite, repair, network, or output option, because **none of those is an
operator choice**: there is one catalog, one namespace per command, and one lawful transition.

## 2. Current executable state — both `execute` modes are disabled

The implementation ships with these exact source constants:

```python
PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None
M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None
```

While each is `None`, its `execute` mode returns exit `3` — **unconditionally**. No CLI flag,
environment value, catalog state, receipt, namespace, preflight result, or verify result can
substitute for the constant, and the activation check runs *before* the private root is even
resolved, so an unset root cannot mask the answer.

A later exact owner instrument may replace **only** the named constant with its governed token, run
the specified validation, and create a new local commit. Transition activation cannot enable E0; E0
activation cannot enable any later stage.

## 3. The private-root boundary

The accepted private root is read once per process from the fixed environment variable
`DISCLOSURE_DRIFT_EVIDENCE_ROOT`, resolved through the accepted external-root boundary, and cached.
Accepted Decision 095 **R80** makes that name a **centrally recognized runtime root**: it is in
`RUNTIME_ROOT_ENV_VARS`, and therefore in `RECOGNIZED_ENV_VARS`, so the central configuration loader
does not reject the process before dispatch. It is **not** a configuration override — it appears in
no `ENV_OVERRIDES` entry, no secret set, no Pydantic model, no configuration fingerprint, no `repr`,
no receipt value, no log record, and no CLI output — and filtering it out at `cli.py` dispatch is
prohibited.

**The value is never rendered.** Refusal messages name the *variable* and the rule that was broken,
never the path. An `OSError` ordinarily carries the offending filename, so only its class is
reported.

## 4. Exit codes

| Exit | Meaning |
|---:|---|
| `0` | the requested mode completed and its own predicates pass |
| `1` | configuration or private-root resolution failure |
| `2` | command-line usage error |
| `3` | stage or mode not enabled by the current executable boundary |
| `4` | preflight, integrity, identity, totality, freeze, or verification gate failure |

A refusal or nonzero exit **never** deletes evidence and never restores a catalog. Only a complete
terminal record with an independently reproduced token constitutes command success.

## 5. The authorized write sets

Every path is relative to the accepted private root, and every one is create-once.

```text
runs/m3_3_pre_e0_catalog_transition_0013_0015_v1/
  catalog_backup_0013.sqlite3
  catalog_transition_events.jsonl
  execution_receipt.json
  catalog_transition_terminal.json

runs/m3_3_e0_offline_parse_v1/
  pre_e0_catalog_0015.sqlite3
  e0_events.jsonl
  execution_receipt.json
  e0_terminal.json
```

The run directory is a non-symlink directory at mode `0700`; every file is regular, non-symlink,
opened with `O_EXCL`, and mode `0600`. Every completed file **and its parent directory** are fsynced,
because the file's *name* lives in the parent and an unsynced parent can lose it.

The complete operational write boundary additionally permits only the fixed accepted catalog,
`catalogs/catalog_writer.lease` through `CatalogWriter`'s ordinary held-to-released metadata writes,
and SQLite's ordinary fixed-catalog `-wal`/`-shm` lifecycle. Those are operational sidecars, not
governed artifacts. **No artifact is written in Git.**

**Preflight and verify create none of it.** Both open the catalog through `SQLITE_OPEN_READONLY`,
which is not convention: a read-write handle to a WAL-mode database checkpoints on close and would
rewrite durable bytes with no statement having written anything. Preflight inspects the writer lease
without creating or acquiring it — an absent lease passes the predicate outright.

**Neither creates the `runs/` parent either.** Accepted Decision 099 **R98** implements Decision 094
§5.2 predicate 10 in full: the parent must **already** exist, be a real non-symlink directory, and be
owned by the effective operator before preflight passes. A platform that will not report the
effective identity refuses rather than silently passing.

## 5a. Predicate 3 — the accepted M3.2 completion binding

Decision 094 §5.2 is headed "Preflight — all predicates required", and its predicate 3 is *the
accepted M3.2 acquisition completion receipt and catalog binding validate*. Accepted Decision 099
**R97** implements it as a strictly read-only, **source-local** validation in `m3/e0.py`, reusing only
`inspect_receipt` and the Decision-063 `resolve_predecessor_receipt` from `m3/receipt.py`. It imports
no recovery module, acquisition orchestrator, request-plan builder, source registry, client,
transport, socket, HTTP library, or SEC route.

Nothing about the binding is discovered. The two receipt paths, their file digests and identities,
their run identities, the acquisition window, the head's completion facts, the accepted head
observation, and the cumulative attempt total are all fixed literals of
`M3_2_COMPLETION_BINDING` (accepted Decision 099 §3, restating accepted Decisions 061–063). It
requires, and refuses otherwise:

- both receipts to be regular, non-symlinked, contained files whose stored bytes hash to the exact
  accepted digests, whose closed schema, canonical form, and self-derived identity the accepted
  loader accepts, and whose derived identities are the accepted ones;
- the head to record `complete`, the window, its exact plan digest, one logical request, one physical
  attempt, and the accepted predecessor identity;
- the root to record `failed`, the window, its exact plan digest, and **no predecessor** — which is
  what makes the chain exactly two receipts to root and a cycle unconstructible;
- the accepted predecessor identity to resolve, through the Decision-063 resolver, to exactly that
  root receipt at its fixed name;
- cumulative accounting of exactly **77** physical attempts — the chain's own attempts plus the
  single no-predecessor root's carried-forward baseline, added exactly once;
- exactly one `ops_ingestion_jobs` row per fixed run identity, with `job_kind = 'm3_2_acquisition'`,
  the receipt's window as its stage, the truthful terminal job state for the receipt's completion
  status, and boundary instants exactly equal to the receipt's;
- a durable `ops_retrieval_attempts` count equal to that receipt's own
  `actual_physical_attempt_count`; and
- the accepted head observation to exist exactly once and to be attributed, through
  `census_plan_sources`, to the accepted head run and to no other.

The same binding runs in transition preflight **and** in the under-lease recheck, because Decision
094 §5.3 item 2 repeats §5.2's predicates before a namespace or backup exists. It is **not** an E0
predicate: Decision 094 §9.1 states E0's own list and names the §5.2 disk and lock predicates only.
The binding reports non-secret enums, counts, digest prefixes, and fixed public relative names; no
private absolute path is rendered.

## 6. The E0 database write set — sixteen tables

```text
census_parser_runs                   census_registrant_observations
census_parsed_records                census_accession_field_resolutions
census_structural_observations       census_accession_cohort_resolutions
census_accessions                    census_quarantined_records
census_accession_observations        census_historical_references
census_accession_registrants         census_malformed_historical_references
census_registrants                   census_candidate_lineage_edges
                                     census_calendar_days
                                     reference_sic_codes
```

The only additional catalog write is the existing `census_plan_sources.parser_state` transition for
category-A sources. This is Decision 068 **R17**'s fifteen tables plus exactly one — the Decision 083
**R58** canonical relation whose writer migration `0014`'s own comment assigns to E0. It is a narrow
amendment forced by a later accepted decision, **not** a general permission to widen E0.

A SQLite authorizer enforces the set at statement-prepare time, so a prohibited write never reaches
the file: the containment proof does not depend on noticing damage afterwards.

## 7. Membership derivation — sets, never scalars

For each canonical accession:

- `S_submissions` — every distinct CIK `normalize_cik` accepts from persisted
  `census_accession_observations` fields `cik` or `cik_padded`, joined through the exact plan-bound
  accepted usable observation for `sec_bulk_submissions`, `sec_submissions_entity`, or
  `sec_submissions_historical`;
- `S_full_index` — every distinct CIK `normalize_cik` accepts from field `cik_padded`, joined through
  an exact plan-bound accepted usable `sec_full_index_company` observation.

`U = S_submissions ∪ S_full_index`, deduplicated and ordered by canonical numeric CIK **only**.
Distinct valid CIKs are co-registrants, not a conflict. The submitter is never promoted. Company
name, ticker, filename, source order, row order, minimum/maximum CIK, and every proximity heuristic
are prohibited. A full-index row never creates an accession.

`registrant_set_completeness = established` exactly when all of:

1. both sets are non-empty;
2. `S_submissions ⊆ S_full_index`;
3. every member of `U` already has a persisted `census_registrants` row;
4. every required source observation and parsed-record reference exists;
5. every membership CIK normalizes exactly, accession binding is exact, and the latest Decision 012
   resolutions for `form` and `official_filing_date` are `resolved` or `resolved_by_correction` with
   `blocks_dependents = 0`.

Otherwise it stays `unestablished`. **A valid full-index-only member with no `census_registrants` row
does not create an entity**: E0 records the unbindable count, writes the otherwise-bindable known
relation rows, and fails the accession closed under existing reason
`PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED`.

### 7.1 Transaction shape

The projection runs strictly after every category-A parse, after full-index observation
materialization, and after `resolve_persisted_accessions()` — a dependency the implementation makes
structural rather than commented, by naming that boundary
`materialize_source_layer()`. It then writes the whole projection in **one transaction**:

1. accession rows already exist with completeness `unestablished`;
2. for cardinality greater than one the scalar is set `NULL` before the second substantive relation
   row is inserted;
3. every relation row is inserted through the create-once path — never a replacement write;
4. an established singleton's scalar **must** equal its sole member; an established multi-member set
   keeps `NULL`; an unestablished set's scalar is not authoritative;
5. completeness becomes `established` **last**, after the relation is total.

The §9 totality is measured **and required inside that same transaction**, so neither an interruption
before commit nor a broken invariant can leave an `established` incomplete set, a partial relation, or
any persisted projection behind.

### 7.2 The canonical consumer rule

The candidate builder and every later Decision 093 linkage consumer read
`census_accession_registrants` **together with** `census_accessions.registrant_set_completeness`.
There is no fall back to `census_accession_observations`, no scalar CIK, no anchor, and no heuristic.
`unestablished` fails closed. The scalar is never unioned into a materialized relation, conflict
attribution uses the same complete relation, and an established joint filing's form is attributed to
**every** substantive member — so a lawful multi-registrant `NULL` scalar is never converted with
`int()`, because the read that would convert it is gone.

**Accepted Decision 096 R83** follows from that rule: a malformed full-index CIK is no longer a
candidate-layer refusal, because the candidate layer no longer reads the observation. It fails closed
one layer earlier, at this projection, on `invalid_cik_rendering_count`.

## 8. The event ledger

One append-only hash-chained JSONL file per run, schema `m3-3-event-ledger/1.0`:

```text
schema_version   run_namespace   sequence   event_type   observed_at_utc
details          previous_event_sha256 (omitted on sequence 1)          event_sha256
```

`event_sha256` is SHA-256 over the canonical event bytes **with `event_sha256` omitted**. Every event
after the first binds its predecessor's hash. Each append is newline-terminated and fsynced before
the next authoritative boundary, so a crash can lose at most the event for a boundary that had
already committed — which is exactly the disclosed commit-before-event window the terminal schemas
model.

`details` is a **closed per-event-type projection**, not a JSON escape hatch: a key outside the
projection is refused, and so is a missing required key. No value may carry an absolute path, an
evidence-root name, an SEC identity, a secret, a raw object, a response body, or a traceback.
`relative_path` is the one field that legitimately contains separators, and it is checked for being
root-relative rather than for the absence of a slash.

| Machine | Allowed events |
|---|---|
| transition | `PREFLIGHT_PASSED`, `BACKUP_VERIFIED`, `MIGRATION_0014_COMMITTED`, `MIGRATION_0015_COMMITTED`, `POSTCHECK_PASSED`, `EXECUTION_RECEIPT_WRITTEN`, `FAILED`, `INTERRUPTED` |
| E0 | `PREFLIGHT_PASSED`, `BACKUP_VERIFIED`, `SOURCE_DISPOSITION_RECORDED`, `FULL_INDEX_OBSERVATIONS_MATERIALIZED`, `ACCESSION_RESOLUTIONS_PERSISTED`, `ASSOCIATIONS_MATERIALIZED`, `VALIDATION_PASSED`, `IDENTITIES_RECOMPUTED`, `EXECUTION_RECEIPT_WRITTEN`, `FAILED`, `INTERRUPTED` |

**There is deliberately no `TERMINAL_FROZEN` event.** The terminal record binds the final ledger head
and is written last; a later event would either create an identity cycle or make the terminal bind a
nonterminal ledger.

## 9. The terminal records

`catalog_transition_terminal.json` is schema `m3-3-pre-e0-catalog-transition-terminal/1.0`;
`e0_terminal.json` is schema `m3-3-e0-terminal/1.0`. Both are canonical UTF-8 JSON with a **closed**
key set, and both carry `actual_logical_request_count = 0` and `actual_physical_attempt_count = 0`.
Their exact key sets are Decision 094 §8.1 and §9.2 and are enforced by
`validate_transition_terminal()` and `validate_e0_terminal()`.

**Conditional presence is exact in both directions.** A field required for a status or a durable
event must be present; a field that status and event set does not permit must be **absent**. No
absent value is represented by `null`, `0`, `"N/A"`, `"-"`, or any other placeholder — an
inapplicable field is omitted, because the conditional-presence table can prove an absence lawful and
can prove a placeholder nothing at all.

**A failed or interrupted record's permitted fields are read from the durable ledger, never from
assignment order** (accepted Decision 099 **R96**). The execute paths necessarily assign an
event-conditioned value *before* appending the event that permits it, because the event's own
`details` carry that value. Before a failure terminal is written, the ledger is therefore read back
and fully verified from disk, and each conditioned group is kept only when its event is durably
present:

| Kind | Field or group | Permitted on failure only when durable |
|---|---|---|
| transition | `backup` | `BACKUP_VERIFIED` |
| transition | `post_preexisting_content_sha256` | `POSTCHECK_PASSED` |
| E0 | `backup` | `BACKUP_VERIFIED` |
| E0 | `association_totality` | `ASSOCIATIONS_MATERIALIZED` |
| E0 | `table_hashes`, `plan_parser_state_hash`, `e0_catalog_state_sha256`, `post_integrity` | `VALIDATION_PASSED` |

`applied_migrations`, `post_migration_chain`, and the transition's `post_integrity` stay governed by
`failure.catalog_state_observed` exactly as before — `applied_migrations` deliberately so, since §8.1
lets it lead the ledger by one migration inside the disclosed commit-before-event window. Each
execute path records its catalog-observed fields at the moment that flag becomes true, so a refusal
*after* a commit discloses the state it observed instead of leaving a record its own validator
refuses.

**If the ledger itself cannot be verified, no terminal is manufactured over it.** A truncated,
malformed, reordered, or unchained ledger means the durable event set is unknown; the surviving
artifacts stay `UNDETERMINED / NOT COMPLETE` and the original exception still propagates.

The E0 terminal additionally carries `source_results` — one closed record per accepted
`(census_run_id, source_instance_id)` pair, ordered by that pair, **76/76 on a complete run** — the
closed `source_result_counts` object, the §9.5 `association_totality`, one `table_hashes` record per
§6 table in name order, `plan_parser_state_hash`, and `e0_catalog_state_sha256`.

`association_totality` fixes six counts at zero: `established_zero_relation_count`,
`singleton_scalar_mismatch_count`, `multi_nonnull_scalar_count`, `orphan_relation_count`,
`invalid_cik_rendering_count`, and `association_provenance_failure_count`. A nonzero one is a
**totality failure**, never a reportable state. The first three counts must partition every census
accession; **no assertion is made that all accessions are established** — `unestablished` is a
lawful, expected, fail-closed outcome.

## 10. Identity and freeze

```text
terminal_record_id = SHA256(canonical JSON with terminal_record_id and result_token omitted)
result_token       = M3_3_PRE_E0_CATALOG_TRANSITION_<STATUS>:<terminal_record_id>
                   | M3_3_E0_OFFLINE_PARSE_<STATUS>:<terminal_record_id>
```

`<STATUS>` is `COMPLETE`, `FAILED`, or `INTERRUPTED`. The token is derived **only after** the identity
it names, so the identity cannot contain the token. **No digest, identifier, event hash, receipt id,
terminal id, catalog-state hash, or token contains its own value in its preimage.**

The freeze order is mandatory:

```text
COMPUTE -> VALIDATE -> PERSIST NONTERMINAL STATE
-> COMMIT THE DATABASE BUT KEEP THE SAME CATALOGWRITER CONTEXT / FLOCK OPEN
-> INDEPENDENTLY RECOMPUTE IDENTITIES FROM A SEPARATE STRICTLY READ-ONLY CONNECTION
-> VERIFY INTEGRITY / FKs / TOTALITY / CONTENT BINDINGS / PROVENANCE
-> WRITE AND FSYNC THE EXECUTION RECEIPT
-> APPEND AND FSYNC EXECUTION_RECEIPT_WRITTEN
-> WRITE-ONCE AND FSYNC THE TERMINAL RECORD LAST
-> REOPEN READ-ONLY AND REPRODUCE THE TERMINAL ID AND TOKEN
-> CLOSE THE WRITER AND RELEASE THE FLOCK
```

The lease is held continuously across all of it. Releasing and reacquiring between steps would open a
window in which another writer could change what an earlier step measured. The identity is reproduced
from the **persisted bytes**, because an identity only ever computed in memory has not been proved to
be the one on disk.

**If a defect is found after nominal freeze:** stop; preserve the terminal, catalog, backup, ledger,
receipt, and every disclosed identity; mark none of them accepted; do not overwrite or conceal the
defect; and return to Sol/GPT. A correction uses a **new namespace** and discloses the superseded
identity. There is no automatic repair and no re-freeze.

## 11. Failure, interruption, and recovery

- Before `MIGRATION_0014_COMMITTED`, a failure leaves the accepted catalog at `0013`; the namespace
  and evidence are retained and returned to the owner.
- After `0014` but before `0015`, the catalog is a **disclosed partial transition at `0014`**. Do not
  auto-continue and do not auto-restore. E0 is held and the run returns to the owner.
- After `0015` but before freeze, the `0015` catalog and evidence are preserved and are not called
  accepted.
- A run namespace is **never reused**; `execute` refuses a namespace that exists. `execute` against
  any non-`0013` head refuses.
- Migrations are forward-only. Restoration from a verified backup is a **destructive catalog
  replacement** and requires a separate explicit owner recovery instrument.
- A hard kill may leave a ledger and no terminal. That is exactly `UNDETERMINED / NOT COMPLETE`, and
  it is never read as success. `verify` still validates the surviving ledger so the operator learns
  how far the run got.

`verify` also **reads the fixed catalog** (accepted Decision 099 **R98**, implementing Decision 094
§7.2's "catalog state" row). Strictly read-only, it compares the catalog's current applied chain and
integrity report with what the terminal froze wherever the terminal asserts them, re-hashes the run's
verified backup against the byte length, file digest, and logical catalog digest the terminal
recorded, and — for E0, whenever `VALIDATION_PASSED` made them lawful — independently reproduces the
§9.4 governed-state identities from the catalog itself. A post-freeze catalog-state or identity
mutation therefore makes `verify` refuse instead of passing on a recorded claim. It still repairs
nothing.

The interruption vocabulary is closed and is listed in
[`execution_receipt_spec.md`](execution_receipt_spec.md) §12.2 alongside the `4.0` schema that
carries it.

## 12. What this document does not do

It does not authorize a transition, an E0 run, a migration, an activation change, a linkage
diagnostic, a persistence bridge, E1, E2, M3.4, network access, a push, or a tag. It describes the
records those acts would produce **if** a later exact owner instrument authorized them.
