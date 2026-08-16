# Decision 094 — M3.3 PRE-E0 Executability Redesign

```text
STATUS: ACCEPTED — OWNER PRE-E0 REDESIGN AUTHORITY
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_PRE_E0_EXECUTABILITY_REDESIGN_OWNER_ACCEPTED
M3_3_E0_OPERATIONAL_STATE: HELD
M3_3_E0_EXECUTION_AUTHORIZATION: NO — NOT RELEASED BY THIS DECISION
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: NO — REQUIRES A LATER EXACT OWNER INSTRUMENT
IMPLEMENTATION_AUTHORIZATION: YES — EXACTLY THE BOUNDED PATHS AND PROOF IN §12
GOVERNANCE_COMMIT_AUTHORIZATION: YES — ONE LOCAL D094 ACCEPTANCE COMMIT
GOVERNANCE_PUSH_AUTHORIZATION: NO — NETWORK AUTHORITY IS NONE
IMPLEMENTATION_COMMIT_AUTHORIZATION: YES — ONE LOCAL IMPLEMENTATION COMMIT; NO PUSH
MIGRATION_0016_AUTHORIZATION: NO
LINKAGE_DIAGNOSTIC_AUTHORIZATION: NO — REMAINS POST-E0 AND READ-ONLY
PERSISTENCE_BRIDGE_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

**Acceptance status matters.** This record grants only the bounded implementation and local-commit
authority in §12. It grants no accepted-catalog write, migration execution, E0 execution, push, tag,
network, or progression authority. The later activation constants in §7.2 remain disabled.

**The objective is narrow:** restore a genuinely executable M3.3-E0 path that is internally
consistent with the already-accepted canonical multi-registrant architecture. It does not reopen the
D091 evidence, the purpose-gate closure, the D093 linkage predicate, or the M3.3 research method.

**This Decision executes nothing.** The accepted catalog was inspected through strictly read-only
SQLite handles. No migration was applied; E0 was not started; no repository byte predating this
Decision draft was changed; and no network, SEC, or HTTP action occurred.

---

## 1. Entry state and measured pre-design facts

### 1.1 Repository state

| Fact | Verified value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `4ed0fc7f67c3f9b4f5750e7c24432269aed9ffc4` |
| Tree | `114f3a189fc4084534efe514d7e385d5233fd642` |
| Working tree before this Decision draft | clean |
| Packaged migration chain | contiguous `0001`–`0015`; `0016` absent |
| Migration `0014` SHA-256 | `0490ea4e76cc365f03b851bd44a3b918f37109c97258abf5fb98d8070ccff9f1` |
| Migration `0015` SHA-256 | `d7f22999cb3e6736c765de72a1031c170f2cb5547ccaccf7469a2d3be018835f` |
| Tracked network switches | disabled |

### 1.2 Accepted operational catalog — read-only measurements

The accepted private evidence root was resolved once by the bounded canonical-root mechanism. Its
absolute path and name are neither printed nor persisted here.

| Fact | Verified value |
|---|---:|
| Canonical-root candidates | 1 |
| Catalog relative identity | `OPERATIONAL_CATALOG_RELATIVE_PATH` — exact match |
| Applied migration versions | exactly `0001`–`0013` |
| Applied migration head | `0013` |
| Applied names/checksums versus packaged prefix | exact match — `verify_applied_migrations` PASS |
| `PRAGMA quick_check` | `ok` |
| `PRAGMA integrity_check` | `ok` |
| Foreign-key violations | 0 |
| Catalog bytes | 359,227,392 |
| Free disk available at inspection | more than 32 GiB |
| Plan sources | 76 |
| `parser_state = not_started` | 76 / 76 |
| Source observations | 77 |

The accepted source disposition evidence is unchanged: one bulk-submissions source, one company-
ticker source, one exchange-ticker source, one filing-calendar source, seventy full-index company
sources, and two SIC attempts of which one is accepted usable and one is accepted failed.

### 1.3 Migration empty-state preconditions — measured, not inferred

Every table named by migration `0014`'s executable empty-state guard contains **0** rows:

```text
census_accessions
census_accession_observations
census_parsed_records
census_parser_runs
pilot_candidate_snapshots
pilot_candidate_accessions
pilot_candidate_accession_registrants
pilot_selection_runs
pilot_selected_accessions
pilot_manifest_versions
```

Every table named by migration `0015`'s executable empty-state guard contains **0** rows:

```text
pilot_candidate_snapshots
pilot_candidate_accessions
pilot_candidate_accession_registrants
pilot_candidate_accession_evidence
pilot_candidate_accession_reasons
pilot_selection_runs
pilot_selected_accessions
pilot_reserve_accessions
pilot_manifest_versions
```

These measurements show that the migration window is presently open. They are **not** permission to
consume it, and they must be repeated by the later execution preflight.

## 2. Controlling authority and precedence

The following accepted state is preserved without reopening:

1. Decision 091's Review-A evidence and accepted digests;
2. Decision 092's owner acceptance and purpose-gate closure;
3. Decision 093's durability closure;
4. Decision 093 §§6–7's exact linkage predicate and separate acceptance-ordering rule;
5. the open real linked-amendment feasibility gate;
6. the rule that the post-E0 linkage diagnostic is read-only, grants no quota credit, persists no
   final verified linkage evidence, and returns to Sol/GPT for adjudication.

The statement that all 96 linkage assertions would necessarily become
`UNESTABLISHED_ASSOCIATION_SET` is **not accepted as fact**. It is an unmeasured inference. This
redesign resolves the missing canonical writer; it does not predict the later diagnostic result.

Where the records conflict, the narrow precedence is:

- Decision 083 **R58–R62** is later and more specific than Decision 068 **R17** about the canonical
  multi-registrant representation. The relation and completeness state are therefore required.
- Decision 093 §9 is a read-only preflight finding whose fifteen-table row cites the then-controlling
  Decision 068 R17. It did not issue a later competing footprint ruling. This Decision directly
  amends R17 and the accepted stage contract on the enumerated points in §6.1; D093's citation follows
  that amended authority. No implementation observation supersedes an accepted Decision.
- Decision 093's linkage predicate, evidence identities, and six execution invariants are not
  superseded.
- Historical accepted records remain byte-unchanged and truthful as at their own acceptance.

## 3. The four dispatch-blocking conflicts

### 3.1 C1 — accepted catalog head versus required software head

The accepted operational catalog is at `0013`; current accepted software requires `0015`.
Migrations `0014` and `0015` exist and are accepted software, but no accepted record authorizes
applying them to this catalog. E0-created census rows would trip migration `0014`'s hard empty-state
guard and destroy the presently open prospective-migration window.

### 3.2 C2 — the old E0 footprint omits the canonical relation

Decision 068 R17 and the current `E0_PERMITTED_TABLES` allow exactly fifteen tables. Migration
`0014`, accepted later under Decision 083 R58/R59, created
`census_accession_registrants` and `census_accessions.registrant_set_completeness`; its own comment
assigns the relation's writer to future E0. The current E0 driver writes neither the relation nor the
completeness state.

The candidate builder then falls back from an empty canonical relation to re-deriving membership
from `census_accession_observations`. That fallback is not a durable canonical R58 relation and
cannot serve the D093 complete-association-set consumer.

### 3.3 C3 — no executable operator surface

The only operator-visible `m3 offline-parse` subcommand routes unconditionally to the M3.3 gate
refusal. The parser library exists, but a hidden Python call or manual SQLite manipulation is not a
governed operator command.

### 3.4 C4 — the required durable result is not schema-representable

The existing receipt schema `m3-execution-receipt/3.0` has neither PRE-E0/E0 phases nor truthful
interruption states for migration or offline parsing. Decision 093 names a receipt path but not a
complete E0 result schema, progress record, identity preimage, freeze marker, or independent
reconstruction contract. A complete, failed, interrupted, or hard-killed real E0 cannot presently be
represented without an invented field or a misleading existing value.

## 4. Ruling R70 — operational hold and preservation boundary

```text
M3_3_E0_OPERATIONAL_STATE = HELD
```

Decision 092's historical owner authorization is not erased. Consumption of it is held because the
accepted catalog and current executable surface cannot satisfy the later accepted architecture.

The hold is released only after all of the following occur in order:

1. this redesign is accepted;
2. its bounded implementation is complete and reviewed;
3. Sol/GPT owner-accepts that implementation;
4. a later exact owner instrument authorizes the real `0013 → 0014 → 0015` transition;
5. that transition succeeds, freezes its durable result, and is owner-accepted; and
6. a later owner act explicitly releases one E0 invocation against the accepted `0015` catalog.

No PASS token, implementation commit, review verdict, migration file, preflight result, or catalog
head change self-authorizes the next step.

## 5. Ruling R71 — exact pre-E0 catalog transition

### 5.1 Only lawful target

The only transition this redesign may implement is:

```text
0013
  -> 0014_m33_multi_registrant_relational_correction.sql
  -> 0015_m33_verified_document_evidence.sql
```

The exact migration names and SHA-256 values are those in §1.1. Migration `0016` is absent and
unauthorized. No migration is edited, squashed, reordered, re-checksummed, replaced, or simulated.
The accepted repository migrator remains the only schema writer.

### 5.2 Preflight — all predicates required

The real transition must refuse before opening a writer if any predicate is false:

1. exactly one accepted canonical private root resolves by the bounded mechanism;
2. the catalog is exactly `OPERATIONAL_CATALOG_RELATIVE_PATH` beneath that root;
3. the accepted M3.2 acquisition completion receipt and catalog binding validate;
4. the applied chain is contiguous and exactly `0001`–`0013`, and every applied name/checksum
   matches the packaged migration bytes;
5. packaged `0014` and `0015` match the §1.1 digests, with no `0016` selected;
6. `quick_check = ok`, `integrity_check = ok`, and foreign-key violations = 0;
7. every §1.3 empty-state count is zero;
8. all 76 plan sources remain `parser_state = not_started` and no E0 parser run exists;
9. if `catalog_writer.lease` exists, a non-mutating `flock(LOCK_SH|LOCK_NB)` succeeds and its
   bounded recorded state is not `held`; if it does not exist, the predicate passes without creating
   it — preflight never tests the lock by acquiring the write lease;
10. the exact create-once run namespace is absent and its parent is an existing non-symlink
    directory owned by the operator;
11. available bytes are at least `3 * catalog_bytes + 1_073_741_824`;
12. the per-table release-hash memory estimator in §8.2 passes; and
13. tracked network switches remain disabled.

Preflight is strictly read-only: no directory, lock, backup, receipt, ledger, temp file, schema row,
or catalog page may be created or changed.

### 5.3 Execute and verification state machine

The later authorized execute mode must:

1. acquire one continuous project-scoped writer lease;
2. while holding that lease and before creating any namespace or backup, repeat predicates 1–8 and
   10–13 from §5.2; any divergence refuses without a catalog or run-artifact write;
3. create the fixed run namespace once, with directory mode `0700`, after refusing symlinks and any
   pre-existing path;
4. pre-create the backup with `O_CREAT|O_EXCL` at mode `0600`, use the active writer connection's
   SQLite backup API, close the destination handle, fsync the completed file and parent directory,
   and only then compute its byte digest;
5. independently verify the closed backup's integrity, exact migration chain, foreign keys, and
   full logical catalog digest against the source snapshot;
6. append and fsync `BACKUP_VERIFIED` before any migration;
7. invoke the accepted migrator for exactly `0014`, validate head/checksum/integrity, append and
   fsync `MIGRATION_0014_COMMITTED`;
8. invoke it for exactly `0015`, validate head/checksum/integrity, append and fsync
   `MIGRATION_0015_COMMITTED`;
9. verify the final chain is exactly `0001`–`0015`, all §1.3 tables that existed before remain
   empty, every pre-existing non-schema table has the same logical content digest as before, and
   no non-migration application row changed;
10. independently reconstruct every transition identity from persisted values while the same lease
    remains continuously held; and
11. write the receipt and terminal record in the freeze order of §11, releasing the lease only
    afterward.

The implementation selects the accepted contiguous inventory prefix through `0014`, validates, then
the prefix through `0015`; it never supplies the full pending inventory blindly. The migrator may
create only the schema and migration-ledger changes already encoded in those files. It may not call
`prepare_operational_catalog()`: that helper both selects every pending migration and calls
`seed_reference_data()`, whose timestamped `INSERT OR REPLACE` writes would alter pre-existing
application rows.

The advisory lease's recorded `expires_at_utc` is non-authoritative and is never a takeover,
resumption, or success signal; the operating-system flock is authoritative. The execute path sets a
lease interval longer than the bounded invocation and still refuses any competing flock owner.

### 5.4 Failure, interruption, replay, and rollback

- Before `MIGRATION_0014_COMMITTED`, a failure leaves the accepted catalog at `0013`; retain the
  namespace and evidence and return to Sol/GPT.
- After `0014` but before `0015`, the catalog is a disclosed partial transition at `0014`.
  **Do not auto-continue and do not auto-restore.** Hold E0 and return to Sol/GPT.
- After `0015` but before freeze, preserve the `0015` catalog and evidence; do not call it accepted
  or rerun automatically.
- A run namespace is never reused. `execute` against any non-`0013` head refuses. `verify` is
  read-only and may inspect only the named namespace and catalog.
- Migrations are forward-only. There is no down migration. Restoration from the verified backup is
  a destructive catalog replacement and requires a separate explicit owner recovery instrument.
- No post-E0 rollback is authorized. Once E0 writes census state, migration-window restoration is
  not a lawful substitute for recovery.

This design intentionally preserves evidence and stops rather than hiding a partial transition.

## 6. Ruling R72 — canonical multi-registrant E0 write contract

### 6.1 Exact durable database write set

The corrected E0 database write set is exactly these **sixteen** tables:

```text
census_parser_runs
census_parsed_records
census_structural_observations
census_accessions
census_accession_observations
census_accession_registrants
census_registrants
census_registrant_observations
census_accession_field_resolutions
census_accession_cohort_resolutions
census_quarantined_records
census_historical_references
census_malformed_historical_references
census_candidate_lineage_edges
census_calendar_days
reference_sic_codes
```

The only additional catalog write is the existing
`census_plan_sources.parser_state` transition for category-A sources. No other column of that table
and no other table may be inserted, updated, or deleted. A SQLite authorizer enforces the positive
set and the existing negative set, with a direct test that an attempted write to every excluded
class is refused.

This is an explicit one-table widening of Decision 068 R17, forced by later accepted Decision 083
R58/R59. It is not a general permission to widen E0. This Decision also explicitly and narrowly
amends the accepted M3.3 stage contract as follows:

1. §10.2 item 2 and §19's Storage clause say **sixteen**, not fifteen, and include
   `census_accession_registrants`;
2. §11's former exactly-one-anchor wording is replaced prospectively by the R58/R59 relation,
   completeness, and scalar/cardinality rules here;
3. §19's CLI clause includes the two §7 commands, with execute disabled until the later exact
   activation instrument;
4. §20 permits the version-scoped receipt-v4 work in §10.1 and the association projection in
   `m3/offline_parse.py`; that projection is part of the one E0 `CatalogWriter` invocation, not a
   second catalog writer; and
5. every other §20 prohibition, especially `reasons.py`, acquisition, network, and migration edits,
   remains binding.

### 6.2 Exact membership derivation

For each canonical accession, define two **sets**, never scalars or anchors:

1. `S_submissions` is every distinct CIK that `normalize_cik` accepts from persisted
   `census_accession_observations` membership fields `cik` or `cik_padded`, joined through the exact
   plan-bound accepted usable observation for source `sec_bulk_submissions`,
   `sec_submissions_entity`, or `sec_submissions_historical`; and
2. `S_full_index` is every distinct CIK that `normalize_cik` accepts from persisted field
   `cik_padded`, joined through an exact plan-bound accepted usable
   `sec_full_index_company` observation bound to that canonical accession.

The prospective substantive membership set is
`U = S_submissions union S_full_index`, deduped and ordered by canonical numeric CIK only.
Distinct valid CIKs are co-registrants, not a conflict. The submitter CIK remains a separate
submission fact and is never promoted or inserted as `submitter_only` by this E0 writer. Company
name, ticker, filename, source order, row order, minimum/maximum CIK, accession proximity, filing
proximity, and any scalar-anchor heuristic are prohibited. A full-index row never creates an
accession. Malformed or unbound evidence is reported and never repaired by inference.

`registrant_set_completeness = established` exactly when all of the following hold:

1. both `S_submissions` and `S_full_index` are non-empty;
2. every submissions member is corroborated by the full-index set,
   `S_submissions` is a subset of `S_full_index`;
3. every member of `U` has an already-persisted `census_registrants` row;
4. every source observation and parsed-record reference required for the chosen provenance exists;
5. every membership CIK normalizes exactly and accession binding is exact; for `form` and
   `official_filing_date`, the latest accepted Decision 012 resolution has status `resolved` or
   `resolved_by_correction` and `blocks_dependents = 0`. Multiple distinct valid `registrant_cik`
   observations are co-membership evidence under R58 and are not themselves a conflict.

Otherwise completeness remains `unestablished`. A valid full-index-only member with no existing
`census_registrants` row **does not create an entity**: E0 records the unbindable count, writes only
otherwise-bindable known relation rows, and fails the accession closed under existing reason
`PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED`. This is the R59-consistent bounded disposition; the
research-facing alternative of inventing a registrant is rejected. Known substantive observations
may remain visible as relation rows while completeness is `unestablished`, but no consumer may read
those rows as a complete set.

### 6.3 Relation provenance and deterministic projection

There is one relation row per `(accession_plain, registrant_cik_numeric)`. Where more than one
persisted observation supports that membership, its singular provenance columns select the strongest
accepted membership witness using Decision 012's existing source-authority order, then
`source_observation_id`, then nullable `parsed_record_id` as the deterministic tie-break, with a
missing parsed-record identity sorting after every present identity. The row's
`first_observed_at_utc` and `latest_observed_at_utc` are the minimum and maximum across all supporting
membership observations. All supporting observations remain independently durable in the accepted
observation tables; none is deleted to make the projection singular.

The relation row uses `association_class = substantive`. A valid internally consistent accepted
metadata witness uses `evidence_level = provisional`; weak/conflicting/unavailable states retain the
existing fail-closed vocabulary and never establish completeness.

### 6.4 Lawful transaction order and scalar projection

After all category-A parsing, full-index observation materialization, and
`CensusCatalog.resolve_persisted_accessions()` complete, E0 streams observations ordered by
canonical accession, holds at most one accession's membership/provenance group in memory, and writes
the entire census association projection in one transaction:

1. accession rows already exist with completeness `unestablished`;
2. for a set of cardinality greater than one, set `registrant_cik_numeric = NULL` before inserting
   the second substantive relation;
3. insert every canonical relation row through the create-once E0 path — no replacement write;
4. for an established singleton, set the scalar to that sole CIK — this Decision narrows R58's
   `may` to `must` so scalar/cardinality equality is mechanically testable; for an established
   multi-member set, keep it `NULL`; for an unestablished set, the scalar is not authoritative and
   completeness remains `unestablished`; and
5. update completeness to `established` **last**, after the relation is total.

SQLite rollback makes the projection transaction all-or-nothing. An interruption before it commits
cannot persist an `established` incomplete set. Existing migration-`0014` triggers remain active and
are not weakened.

### 6.5 Canonical consumer rule

The real candidate builder and every later D093 linkage consumer read
`census_accession_registrants` **together with**
`census_accessions.registrant_set_completeness`. They do not fall back to deriving membership from
`census_accession_observations`, a scalar CIK, an anchor, or a heuristic. `unestablished` fails closed.

This applies to **every** candidate- and linkage-layer use, not only the row that sets
`multi_registrant`:

- the scalar census CIK is not unioned into an already-materialized relation;
- `_registrant_rows` receives the complete canonical relation and never adds the scalar as another
  member;
- conflict attribution uses that same complete relation; and
- `_submission_forms` and every candidate/linkage entity-domain history projection attribute one accession's
  form to every substantive member of its **established** relation, while accession-domain counts
  still dedupe by canonical accession. An unestablished accession contributes no entity history and
  is reported fail-closed; a lawful multi-registrant `NULL` scalar is never converted with `int()`.

This rule does not run the D093 diagnostic and does not predict its 96 outcomes.

`sec/census_orchestrator.py`'s legacy submissions-acquisition projection still converts the nullable
scalar with `int()`. It is outside this exact path set and unreachable here because M3.2 acquisition
is closed and no acquisition or network action is authorized. The residual is disclosed, not silently
treated as fixed; any future authorization that makes that path reachable must correct it first.

## 7. Ruling R73 — real operator surfaces

### 7.1 Project/runtime boundary

Both commands run only from `PROJECT_ROOT`, meaning the canonical repository root that contains
`.git`, `pyproject.toml`, and the governed `.venv`, with the repository-managed Python 3.12
environment. The host-specific absolute working directory is supplied to the executor packet and is
never persisted in a governed artifact:

```text
./.venv/bin/disclosure-drift m3 prepare-e0-catalog \
  --config configs/project.yaml \
  --mode {preflight,execute,verify}

./.venv/bin/disclosure-drift m3 offline-parse \
  --config configs/project.yaml \
  --mode {preflight,execute,verify}
```

The exact environment variable `DISCLOSURE_DRIFT_EVIDENCE_ROOT` must already contain the accepted
private root. The process resolves it once, caches the resolved reference, and never prints, logs,
persists, or returns the variable's value. The catalog is always the fixed
`OPERATIONAL_CATALOG_RELATIVE_PATH`; there is no evidence-root value in process arguments and no
`--catalog`, `--data-root`, `--run-namespace`, migration list, force, resume, overwrite, repair,
network, or arbitrary output option. The production namespaces are internal constants exactly
`m3_3_pre_e0_catalog_transition_0013_0015_v1` and `m3_3_e0_offline_parse_v1`; tests may call the
library with separate temporary namespaces matching `\A[a-z0-9][a-z0-9_-]{0,127}\Z`.

### 7.2 Modes

| Mode | Semantics |
|---|---|
| `preflight` | Strictly read-only; validates every predicate and prints only non-secret counts/digests and a pass/refusal. Creates nothing |
| `execute` | The only write mode; refuses unless the exact stage predicates and the source-bound activation constant are true. A governance record, not a CLI flag or ambient file, supplies authority |
| `verify` | Strictly read-only; validates the named durable namespace, receipt, ledger, terminal record, catalog state, and identities. Repairs nothing |

`prepare-e0-catalog execute` requires catalog head `0013` and a later exact transition instrument.
`offline-parse execute` requires accepted catalog head `0015`, a complete owner-accepted transition
token, an absent E0 namespace, and a later one-invocation E0 release. Neither command infers
authority from filesystem state.

The accepted implementation lands with these exact source constants disabled:

```text
PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None
M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None
```

Therefore both `execute` modes return exit `3` after implementation acceptance. A later exact owner
instrument may authorize one bounded source-only activation change that replaces **only** the named
constant with the instrument's governed token, runs the specified validation, and creates a new
local commit. The SHA-256 of that exact token is recorded as `owner_authority_sha256` in the terminal
record. Transition activation cannot enable E0; E0 activation cannot enable any later stage. No
operator flag, environment value, catalog state, receipt, or namespace can substitute for the
constant.

### 7.3 Success, failure, exits, and network

| Exit | Meaning |
|---:|---|
| `0` | requested mode completed and its own predicates pass |
| `1` | configuration or private-root resolution failure |
| `2` | command-line usage error |
| `3` | stage/mode not enabled by the current executable boundary |
| `4` | preflight, integrity, identity, totality, freeze, or verification gate failure |

A refusal or nonzero exit never deletes evidence or restores a catalog. Only a complete terminal
record and independently reproduced token constitute command success. Neither module imports or
constructs a client, transport, socket, HTTP library, SEC route, or acquisition orchestrator. Actual
logical request count and physical attempt count are exactly zero in every record.

## 8. Ruling R74 — transition durable-output contract

The transition's non-empty authorized write set is exactly:

```text
runs/m3_3_pre_e0_catalog_transition_0013_0015_v1/
  catalog_backup_0013.sqlite3
  catalog_transition_events.jsonl
  execution_receipt.json
  catalog_transition_terminal.json
```

Every path is relative to the accepted private root and create-once. The run directory is a
non-symlink directory at mode `0700`; every file is regular, non-symlink, opened with `O_EXCL`, and
mode `0600`. Every completed file and its parent directory are fsynced. No artifact is written in
Git.

The complete operational write boundary additionally permits only: the fixed accepted catalog;
`catalogs/catalog_writer.lease` through `CatalogWriter`'s ordinary held-to-released metadata writes;
and SQLite's ordinary fixed-catalog `-wal`/`-shm` lifecycle and checkpoint effects. The lease is
never unlinked or manually edited. Those companions are operational sidecars, not governed result
artifacts, and no other private-root path may change.

### 8.1 Transition terminal schema

`catalog_transition_terminal.json` is canonical UTF-8 JSON under schema
`m3-3-pre-e0-catalog-transition-terminal/1.0` with this closed key set:

```text
schema_version
record_type                         = catalog_transition
run_namespace
command_name                        = m3 prepare-e0-catalog
command_version
status                              = complete | failed | interrupted
started_at_utc
completed_at_utc
owner_authority_sha256
catalog_relative_path
pre_migration_chain
target_migration_chain
post_migration_chain
packaged_migration_sha256           {"0014": <sha256>, "0015": <sha256>}
precondition_counts                 {<each §1.3 table>: <integer>}
pre_integrity                       {quick_check, integrity_check, foreign_key_violations}
post_integrity                      {quick_check, integrity_check, foreign_key_violations}
pre_catalog_logical_sha256
pre_preexisting_content_sha256
post_preexisting_content_sha256
backup                              {relative_path, byte_length, file_sha256,
                                     catalog_logical_sha256, integrity}
applied_migrations                  ordered list of {version, name, checksum_sha256}
event_ledger                        {relative_path, event_count, head_event_sha256}
execution_receipt_id
actual_logical_request_count        = 0
actual_physical_attempt_count       = 0
failure                             omitted on complete; otherwise {reason_code, reason_detail,
                                     catalog_state_observed, interruption_state?}
terminal_record_id
result_token
```

On `complete`, the post chain must be exactly `0001`–`0015`, both migrations must appear in order,
all integrity fields pass, and `post_preexisting_content_sha256` must equal
`pre_preexisting_content_sha256`. A hard kill may leave no terminal file, which is exactly
`UNDETERMINED / NOT COMPLETE`.

Status/event-conditioned presence is exact:

| Field group | `complete` | `failed` / `interrupted` |
|---|---|---|
| All fields through `pre_preexisting_content_sha256`, ledger, receipt, counts, IDs, token | required | required |
| `applied_migrations` | required, exactly `0014`,`0015` | required iff `failure.catalog_state_observed = true`; otherwise omitted |
| `backup` | required | required iff `BACKUP_VERIFIED` is present; otherwise omitted |
| `post_migration_chain`, `post_integrity` | required | required iff `failure.catalog_state_observed = true`; otherwise omitted |
| `post_preexisting_content_sha256` | required | required iff `POSTCHECK_PASSED` is present; otherwise omitted |
| `failure` | omitted | required, with closed keys `reason_code`, `reason_detail`, `catalog_state_observed`, and `interruption_state` iff status is `interrupted` |

No other omission is valid; no absent value is represented by `null`, zero, `N/A`, or an invented
placeholder. `pre_migration_chain`, `target_migration_chain`, and `post_migration_chain` are ordered
integer arrays. When present, `applied_migrations` contains the actual observed chain delta in order
— zero, one, or two — and never repeats the thirteen predecessor records. On complete it must match
both durable `MIGRATION_*_COMMITTED` events. On failed/interrupted it may lead the ledger by exactly
one migration only in the disclosed commit-before-event crash window; that condition requires the
corresponding `after_migration_*_commit_before_event` interruption state and can never be COMPLETE.

### 8.2 Exact catalog logical digests

The backup comparison does not use SQLite file-byte equality. For a strictly read-only snapshot:

1. enumerate every non-internal table from `sqlite_schema` by name;
2. obtain every live column in `PRAGMA table_xinfo` `cid` order;
3. hash every row and column through the accepted `release.hashing.hash_table` normalization;
4. hash the logical schema as a pseudo-table named `sqlite_schema`, over exactly
   `(type, name, tbl_name, sql)` for non-internal tables, indexes, triggers, and views — never
   `rootpage`; and
5. combine the pseudo-table plus every user-table hash through accepted `hash_release`.

That result is `catalog_logical_sha256`. No current migration contains a view, virtual table,
generated column, `WITHOUT ROWID` table, or BLOB column; the general rules above are retained
deliberately for future-proof refusal rather than because such a case exists today. The transition source and backup values must be identical;
the E0 source and backup values must be identical. `pre_preexisting_content_sha256` is a separate
`hash_release` over the data hashes of every table present at head `0013` except
`ops_schema_migrations`; the post-transition value repeats that exact head-`0013` table-name and
column projection after `0015`. Equality proves the schema transition changed no pre-existing
application row while permitting the migration ledger and schema to change truthfully.

Each table is hashed and released before the next is materialized. Preflight scans row counts and
normalized UTF-8 lengths without buffering rows and computes the conservative peak estimate
`4 * normalized_utf8_bytes + 256 * row_count` for the largest table. It refuses unless that estimate
is at most `2_147_483_648` bytes and at most one quarter of physical memory. Per snapshot, each table
is scanned only once; where both the full and head-`0013` projections are required, both digest
states are updated from that one scan. This keeps the accepted `hash_table` preimage and avoids an
unbounded all-catalog materialization.

## 9. Ruling R75 — E0 durable-output and totality contract

The E0 non-empty authorized private write set is exactly:

```text
runs/m3_3_e0_offline_parse_v1/
  pre_e0_catalog_0015.sqlite3
  e0_events.jsonl
  execution_receipt.json
  e0_terminal.json
```

The backup is a verified mode-`0600` SQLite-native snapshot taken after E0 preflight and before the
first E0 database write. The same directory, file, fsync, operational-sidecar, and write-boundary
rules as §8 apply. It cannot be replaced by the head-`0013` transition backup because recovery after
the transition requires a head-`0015` source.

### 9.1 E0 execution, interruption, and replay state machine

Real preflight is strictly read-only and requires: the one canonical root and fixed catalog; the
owner-accepted COMPLETE transition terminal/token; exact chain `0001`–`0015`; packaged checksum
match; passing integrity/foreign keys; exactly 76 accepted plan rows all still `not_started`; no E0
parser run or production namespace; exact input-observation digest; §8.2 memory and §5.2 disk/lock
predicates; disabled tracked network switches; and no private-path leak. It creates nothing.

Later-authorized execute checks its distinct source constant, acquires one continuous writer lease,
repeats every mutable predicate under that lease, creates the namespace `0700`, and makes/verifies
the closed `0600` head-`0015` backup before the first database write. It then:

1. processes the 76 sources in accepted plan order, appending `SOURCE_DISPOSITION_RECORDED` only
   after each durable source boundary;
2. materializes accepted full-index observations after every category-A parser boundary, then
   appends `FULL_INDEX_OBSERVATIONS_MATERIALIZED`;
3. runs `resolve_persisted_accessions()`, then appends `ACCESSION_RESOLUTIONS_PERSISTED`;
4. writes the §6 association projection and completeness transaction, then appends
   `ASSOCIATIONS_MATERIALIZED`;
5. validates chain, integrity, foreign keys, source totality, association totality, and every
   governed identity, then freezes under §11.

Any failed/interrupted E0 remains a disclosed partial head-`0015` catalog and blocks every later
stage. The namespace is never reused; execute never resumes, repairs, deletes, or restores. A restore
from `pre_e0_catalog_0015.sqlite3` is a destructive catalog replacement requiring a separate owner
recovery instrument. `verify` is strictly read-only and may reconstruct handled and hard-kill states;
absence of a valid terminal is `UNDETERMINED / NOT COMPLETE`, never success.

### 9.2 E0 terminal schema

`e0_terminal.json` is canonical UTF-8 JSON under schema `m3-3-e0-terminal/1.0` with this closed key
set:

```text
schema_version
record_type                         = m3_3_e0_offline_parse
run_namespace
command_name                        = m3 offline-parse
command_version
status                              = complete | failed | interrupted
started_at_utc
completed_at_utc
owner_authority_sha256
catalog_relative_path
pre_migration_chain
post_migration_chain
transition_terminal_record_id
transition_result_token
configuration_fingerprint
input_observation_set_sha256
pre_e0_catalog_logical_sha256
source_results                      ordered list of 76 §9.3 records
source_result_counts
association_totality
table_hashes                        ordered list of §9.4 table records
plan_parser_state_hash
e0_catalog_state_sha256
pre_integrity                       {quick_check, integrity_check, foreign_key_violations}
post_integrity                      {quick_check, integrity_check, foreign_key_violations}
backup                              {relative_path, byte_length, file_sha256,
                                     catalog_logical_sha256, integrity}
event_ledger                        {relative_path, event_count, head_event_sha256}
execution_receipt_id
actual_logical_request_count        = 0
actual_physical_attempt_count       = 0
failure                             omitted on complete; otherwise {reason_code, reason_detail,
                                     catalog_state_observed, interruption_state?}
terminal_record_id
result_token
```

Status/event-conditioned presence is exact:

| Field group | `complete` | `failed` / `interrupted` |
|---|---|---|
| Fields through `pre_e0_catalog_logical_sha256`, `source_results`, `source_result_counts`, ledger, receipt, counts, IDs, token | required | required |
| `source_results` | exactly 76, every `ledger_event_present = true` | zero through 76: every durable event plus any independently observed category-A database boundary lacking its event; no other row |
| `backup` | required | required iff `BACKUP_VERIFIED` is present; otherwise omitted |
| `association_totality` | required | required iff `ASSOCIATIONS_MATERIALIZED` is present; otherwise omitted |
| `table_hashes`, `plan_parser_state_hash`, `e0_catalog_state_sha256`, `post_integrity` | required | required iff `VALIDATION_PASSED` is present; otherwise omitted |
| `post_migration_chain` | required and exactly `0001`–`0015` | required iff `failure.catalog_state_observed = true`; otherwise omitted |
| `failure` | omitted | required under the exact closed shape in §8.1 |

No other omission or placeholder is valid. A complete terminal is a statement that E0 parsed and
froze truthfully; it is **not** a candidate-snapshot pass, linkage result, gate closure, or E1
authorization.

### 9.3 Exact per-source record

On a complete run, `source_results` contains exactly one record for each accepted
`(census_run_id, source_instance_id)`, ordered by that pair. On a failed/interrupted terminal it
contains exactly the durable recorded subset, with no duplicate pair. Every record has this closed
key set:

```text
census_run_id
source_instance_id
source_id
observation_id                       omitted only when accepted unavailable
disposition                          E0_REQUIRED_PARSE |
                                     E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE |
                                     E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY
parser_state_before
parser_state_after
parser_run_id                        required only when a parser run exists
parsed_records
quarantined_records
already_present
ledger_event_present                  boolean; complete requires true
```

Counts are factual zeros where applicable, never omission placeholders. A complete ordered list must
reconcile 76/76 with the accepted plan; a partial list must reconcile exactly with the ledger.
Category C receives no parser-state mutation. Category B is
truthfully unavailable. A category-A parser terminal may be completed, failed, or quarantined under
the accepted R18 mechanics; the terminal record reports rather than launders it.

`input_observation_set_sha256` is SHA-256 over canonical JSON for the 76 plan rows ordered by
`(census_run_id, source_instance_id)`, projecting exactly `census_run_id`, `source_instance_id`,
`source_id`, nullable `observation_id`, and — when bound — the accepted observation's
`request_identity`, `logical_sha256`, `parser_version`, and `outcome`. It is computed before writes
and independently reproduced afterward.

`source_result_counts` is the closed object:

```text
planned_source_count                  must be 76
required_parse_count
accepted_unavailable_count
validation_or_provenance_only_count
parser_completed_count
parser_failed_count
parser_quarantined_count
parsed_record_count
quarantined_record_count
full_index_registrant_observation_count
full_index_unbound_accession_count
accession_resolution_count
submissions_membership_observation_count
substantive_membership_observation_count
```

On complete, the three disposition counts sum to 76; on failed/interrupted, they sum to the recorded
subset length. A `ledger_event_present = false` row is lawful only when persisted category-A parser
or parser-state evidence proves a source commit occurred before its ledger append; the terminal must
use interruption state `after_e0_source_commit_before_event`. Category B/C has no database boundary
and therefore cannot appear without its durable event. The three parser terminal counts reconcile
the sources for which a parser run exists; every aggregate reproduces from `source_results`, the
ledger, and the persisted tables.

### 9.4 Exact governed state identity

`table_hashes` contains one record for every §6.1 table, ordered by table name:

```text
table_name
columns                              every live column in PRAGMA table_xinfo cid order
row_count
normalized_content_sha256
```

Each hash is produced by the accepted `release.hashing.hash_table` normalization over all persisted
rows and columns, one table at a time under §8.2's preflight bound. `plan_parser_state_hash` uses the same algorithm over exactly
`(census_run_id, source_instance_id, observation_id, parser_state)` from
`census_plan_sources`. `e0_catalog_state_sha256` is the accepted `hash_release` of those seventeen
hash records. The identity is recomputed independently through a separate fresh strictly read-only
connection while the writer context remains open solely to retain the continuous flock; no write
transaction remains open and the writer connection performs no later database mutation.

### 9.5 Association totality

`association_totality` is the closed object:

```text
census_accession_count
established_accession_count
unestablished_accession_count
substantive_relation_count
established_zero_relation_count       must be 0
established_singleton_count
established_multi_count
singleton_scalar_mismatch_count        must be 0
multi_nonnull_scalar_count             must be 0
orphan_relation_count                  must be 0
invalid_cik_rendering_count             must be 0
association_provenance_failure_count    must be 0
submissions_member_missing_full_index_count
unbindable_registrant_member_count
unestablished_membership_conflict_count
```

The first three counts must partition every census accession exactly. No assertion is made that all
accessions are established. The last three counts may be nonzero only on accessions whose
completeness remains `unestablished`; an established accession contributing to any of those counts
is a totality failure. Distinct valid CIKs alone never increment a conflict count.

## 10. Ruling R76 — receipt v4 and event-ledger representability

### 10.1 Receipt schema

The implementation may add exactly one backward-compatible reader/writer successor:

```text
m3-execution-receipt/4.0
```

Receipts `2.0` and `3.0` remain byte-unchanged and keep their existing validators and writer
behavior. Existing commands continue to emit `3.0`; only these two new commands call the explicit
v4 builder. The v4 rule table, phase tuple, invocation-mode tuple, zero-network tuple, interruption
tuple, and derived mode sets are version-scoped objects; no v4 vocabulary enters a v2/v3 validator.
The v4 delta is limited to:

1. phase exactly `M3.3B` for both new modes, using the already-accepted real-execution phase rather
   than inventing a new project phase;
2. zero-network modes `offline_catalog_transition` and `offline_parse`;
3. `offline_catalog_transition` permits only the common identity, migration, timing, zero-network,
   completion, reason, interruption, and predecessor fields;
4. `offline_parse` additionally requires parser versions and the cohort-definition digest, and
   does not require selection, quota, manifest, or transport fields; and
5. the interruption states in §10.2.

No terminal-record field is added to the receipt. The relationship is deliberately one-way:
the receipt is written first, and the terminal record binds its `receipt_id`. This prevents a
receipt/terminal identity cycle.

The v4 closed reason-code vocabulary is exact, stage-specific, release-blocking, and
manual-review-required; it does not alter the repository-wide `reasons.py` registry:

```text
PRE_E0_CATALOG_TRANSITION_FAILED
PRE_E0_CATALOG_TRANSITION_INTERRUPTED
M3_3_E0_OFFLINE_PARSE_FAILED
M3_3_E0_OFFLINE_PARSE_INTERRUPTED
```

### 10.2 Event ledger

Each JSONL event has this closed schema:

```text
schema_version                       m3-3-event-ledger/1.0
run_namespace
sequence                             positive contiguous integer
event_type
observed_at_utc
details                              event-type allowlisted non-secret values only
previous_event_sha256                omitted on sequence 1
event_sha256
```

`event_sha256` is SHA-256 over canonical event bytes with `event_sha256` omitted. Every event after
the first binds the preceding hash. Each append is newline-terminated and fsynced before the next
authoritative boundary. Events, receipts, and terminal records all reuse
`m3.receipt.canonical_bytes`: UTF-8 without BOM, Unicode preserved (`ensure_ascii = false`), keys
sorted, compact separators, non-finite numbers refused, LF newline, and exactly one trailing newline.
Every governed SHA-256 preimage includes that trailing newline.

`details` is not an arbitrary JSON escape hatch. Its closed event-type projections are:

| Event | Exact permitted `details` keys |
|---|---|
| `PREFLIGHT_PASSED` — transition | `pre_migration_head`, `catalog_bytes`, `precondition_table_count`, `pre_catalog_logical_sha256` |
| `PREFLIGHT_PASSED` — E0 | `migration_head`, `planned_source_count`, `input_observation_set_sha256`, `pre_e0_catalog_logical_sha256` |
| `BACKUP_VERIFIED` | `relative_path`, `byte_length`, `file_sha256`, `catalog_logical_sha256` |
| `MIGRATION_0014_COMMITTED` / `MIGRATION_0015_COMMITTED` | `version`, `name`, `checksum_sha256`, `integrity_check`, `foreign_key_violations` |
| `POSTCHECK_PASSED` | `post_migration_head`, `post_preexisting_content_sha256`, `integrity_check`, `foreign_key_violations` |
| `SOURCE_DISPOSITION_RECORDED` | `census_run_id`, `source_instance_id`, `source_id`, `disposition`, `parser_state_after`, optional `parser_run_id`, `parsed_records`, `quarantined_records` |
| `FULL_INDEX_OBSERVATIONS_MATERIALIZED` | `full_index_registrant_observation_count`, `full_index_unbound_accession_count` |
| `ACCESSION_RESOLUTIONS_PERSISTED` | `accession_resolution_count` |
| `ASSOCIATIONS_MATERIALIZED` | every key of the §9.5 `association_totality` object |
| `VALIDATION_PASSED` | `e0_catalog_state_sha256`, `integrity_check`, `foreign_key_violations` |
| `IDENTITIES_RECOMPUTED` | `e0_catalog_state_sha256`, `table_hash_count`, `plan_parser_state_hash` |
| `EXECUTION_RECEIPT_WRITTEN` | `execution_receipt_id` |
| `FAILED` | `reason_code`, `reason_detail` |
| `INTERRUPTED` | `reason_code`, `reason_detail`, `interruption_state` |

No value may contain an absolute path, evidence-root name, SEC identity value, secret, raw object,
response body, or free-form exception traceback. `reason_detail` follows the receipt's bounded
non-secret sentence rule.

Allowed transition events are:

```text
PREFLIGHT_PASSED
BACKUP_VERIFIED
MIGRATION_0014_COMMITTED
MIGRATION_0015_COMMITTED
POSTCHECK_PASSED
EXECUTION_RECEIPT_WRITTEN
FAILED
INTERRUPTED
```

Allowed E0 events are:

```text
PREFLIGHT_PASSED
BACKUP_VERIFIED
SOURCE_DISPOSITION_RECORDED           one per durable source boundary
FULL_INDEX_OBSERVATIONS_MATERIALIZED
ACCESSION_RESOLUTIONS_PERSISTED
ASSOCIATIONS_MATERIALIZED
VALIDATION_PASSED
IDENTITIES_RECOMPUTED
EXECUTION_RECEIPT_WRITTEN
FAILED
INTERRUPTED
```

The interruption vocabulary is exact:

```text
before_backup
during_backup
after_backup_before_migration
after_migration_0014_before_0015
after_migration_0014_commit_before_event
after_migration_0015_commit_before_event
after_migration_0015_before_transition_freeze
during_e0_source_parse
after_e0_source_commit_before_event
during_e0_full_index_observation_materialization
after_e0_full_index_observations_before_resolution
during_e0_accession_resolution
after_e0_resolution_before_association_materialization
during_e0_association_materialization
after_e0_materialization_before_validation
after_e0_validation_before_freeze
```

There is deliberately no `TERMINAL_FROZEN` ledger event: the terminal record binds the final ledger
head and is written last. Writing a later ledger event would either create an identity cycle or make
the terminal bind a nonterminal ledger.

## 11. Ruling R77 — identity, freeze, and post-freeze defects

For either terminal document:

1. `terminal_record_id = SHA256(canonical UTF-8 JSON with terminal_record_id and result_token
   omitted)`;
2. `result_token` is derived only after that identity:
   - `M3_3_PRE_E0_CATALOG_TRANSITION_<STATUS>:<terminal_record_id>`; or
   - `M3_3_E0_OFFLINE_PARSE_<STATUS>:<terminal_record_id>`;
3. `<STATUS>` is `COMPLETE`, `FAILED`, or `INTERRUPTED` exactly;
4. recomputation omits exactly the same two fields and must reproduce the persisted ID and token.

No digest, identifier, event hash, receipt ID, terminal ID, catalog-state hash, or token contains its
own value in its preimage.

The freeze order is mandatory:

```text
COMPUTE
-> VALIDATE
-> PERSIST NONTERMINAL STATE
-> COMMIT DATABASE STATE BUT KEEP THE SAME CATALOGWRITER CONTEXT / FLOCK OPEN
-> INDEPENDENTLY RECOMPUTE IDENTITIES FROM A SEPARATE STRICTLY READ-ONLY CONNECTION
-> VERIFY INTEGRITY / FKs / TOTALITY / CONTENT BINDINGS / PROVENANCE
-> WRITE AND FSYNC THE EXECUTION RECEIPT
-> APPEND AND FSYNC EXECUTION_RECEIPT_WRITTEN
-> WRITE-ONCE AND FSYNC THE TERMINAL RECORD LAST
-> REOPEN READ-ONLY AND REPRODUCE THE TERMINAL ID AND TOKEN
-> CLOSE THE WRITER AND RELEASE THE FLOCK
```

If a defect is found after nominal freeze: **STOP; preserve the terminal, catalog, backup, ledger,
receipt, and every disclosed identity; mark none of them accepted; do not overwrite or conceal the
defect; and return to Sol/GPT for disposition.** A correction uses a new namespace and discloses the
superseded identity. No automatic repair or re-freeze exists.

## 12. Ruling R78 — implementation, validation, and acceptance boundary

### 12.1 Bounded implementation paths

The fresh Claude implementation authority is limited to:

```text
src/disclosure_drift/m3/e0.py                         new bounded orchestration module
src/disclosure_drift/m3/offline_parse.py
src/disclosure_drift/m3/candidate_snapshot.py
src/disclosure_drift/m3/receipt.py
src/disclosure_drift/m3/__init__.py
src/disclosure_drift/cli.py
tests/unit/test_m3_e0.py                              new
tests/unit/test_m3_offline_parse.py
tests/unit/test_m3_candidate_snapshot.py
tests/unit/test_m3_3_multi_registrant_correction.py
tests/unit/test_m3_receipt.py
tests/unit/test_m3_rehearsal.py                       only for the exact write-boundary assertions
tests/integration/test_m3_cli.py
tests/unit/test_migration_provenance.py
Docs/m3/e0_execution_record_spec.md                   new executable schema companion
Docs/m3/execution_receipt_spec.md
Docs/m3/operator_runbook.md
Docs/sec_data_dictionary.md
Docs/change_impact_map.md
```

An implementer may return a narrower set. A needed path outside the set is a STOP for Sol/GPT,
except a directly corresponding existing unit-test filename whose ownership is mechanically obvious.
Governance surfaces — this Decision, `Milestones/STATUS.md`, the active contract, registry, index,
architecture map, contract README, and master plan — are Sol-owned acceptance edits and are not
Claude implementation paths. Exactly one local implementation commit is authorized after required
validation; push, tag, amend, rebase, and force operations are not.

### 12.2 Prohibited paths and acts

Prohibited: changing any migration `0001`–`0015`; creating migration `0016`; changing acquisition,
HTTP, transport, rate-limit, SEC-client, network configuration, preregistration, D091 evidence,
accepted review artifacts, or historical Decisions; opening the accepted private root during
implementation tests; applying any migration to the accepted catalog; running E0; running the D093
diagnostic; committing private output; moving `m3.2-complete`; tagging; or beginning E1/E2/M3.4.

### 12.3 Required proof

Implementation uses targeted tests while editing, the touched-file checks from
`Docs/change_impact_map.md`, and one final `make check-fast`. It must also prove, non-vacuously:

1. exact `0013 → 0014 → 0015` selection and refusal at every other head;
2. migration checksums, every empty-state guard, the under-lease recheck, backup precreation at
   `0600`, closed/fsynced backup logical equality, disk/memory failure, lock failure, and failure at
   every commit boundary;
3. the sixteen-table positive write set and refusal of writes outside it;
4. exact `S_submissions`, `S_full_index`, subset/union semantics, one-accession memory bound,
   unbindable-member fail-closed handling without entity creation, canonical relation totality,
   scalar/cardinality invariants, completeness-last ordering, malformed evidence, valid distinct-CIK
   non-conflict, submitter nonpromotion, source-order independence, relational entity-history
   attribution, and lawful multi-registrant `NULL` scalar handling;
5. candidate and linkage consumers cannot use the observation-derived or scalar fallback, cannot
   union a scalar into the canonical relation, and cannot convert a lawful multi-registrant `NULL`
   scalar with `int()`;
6. all 76 source-result rows, category A/B/C semantics, and no-network counts;
7. receipt v2/v3 byte and validator compatibility, including mutation proof that a v3 document with
   a v4-only mode/phase/interruption is refused, plus v4 closed-field enforcement;
8. fixed create-once production namespaces, test-only namespace validation, directory `0700`, file
   `0600`, symlink refusal, lease/WAL/SHM containment, file and parent fsync, ledger
   truncation/reordering/mutation detection, every crash boundary, hard-kill absence semantics, and
   no automatic resume;
9. every identity and token independently reproduces and self-reference mutants fail;
10. post-freeze defect preservation; and
11. private-root, environment value, secret, SEC-identity, raw-object, and absolute-path nonleakage
    using field-aware validation rather than a blanket path detector;
12. the per-table memory refusal fires before a writer opens, and one scan supplies both digest
    projections without changing the accepted preimage; and
13. both execute activation constants remain `None`, both execute modes return exit `3`, and no
    preflight/verify result can enable them.

Required governance validation for this Decision stage is:

```text
make links
make decision-refs
make secrets
make hygiene
git diff --check
```

### 12.4 Review and progression

Normal bounded sequence:

1. one fresh Claude Opus 5 Maximum implementation session with actual-model attestation;
2. Sol/GPT review against this frozen Decision;
3. at most one normal bounded remediation;
4. one genuinely fresh read-only independent review, justified because this change creates an
   accepted-catalog migration surface and governed E0 identities; no second independent reviewer;
5. Sol/GPT implementation acceptance or rejection;
6. only then, a separate exact transition execution instrument plus its bounded constant-only
   activation change, validation, and local commit;
7. transition execution and owner acceptance;
8. only then, a separate one-invocation E0 release plus its distinct constant-only activation
   change, validation, and local commit.

Implementation success is evidence, not owner acceptance. Transition success is not E0 authority.
E0 success is not linkage-gate closure or E1 authority.

## 13. Fresh architecture challenge and owner adjudication

One genuinely fresh Claude Opus 5 Maximum read-only challenge completed against the 976-line
proposal with SHA-256
`b01bd2736db8f10d171b262f064d369debc3159b737f7c83f31ad9d8c2cfab7e`. The session attested
`claude-opus-5`, maximum effort, fresh/not resumed, no delegation and no network. It verified entry
and after state identical at HEAD `4ed0fc7f…`, tree `114f3a189f…`, with only this untracked proposal.
Its verdict was `ACCEPT_WITH_BOUNDED_CORRECTIONS`: BLOCKER 2, MAJOR 6, MINOR 10,
OPTIMIZATION 5.

Sol/GPT adjudicates every finding:

| Finding | Owner disposition |
|---|---|
| B1 submissions membership was a first-write scalar | **ACCEPTED / CORRECTED** — §6.2 freezes set/set union, corroboration, and source-order independence |
| B2 accepted stage contract still capped/prohibited the work | **ACCEPTED / CORRECTED** — §6.1 enumerates the narrow amendments; Sol updates the active contract before dispatch |
| M1 v4 vocabulary could leak into v2/v3 validators | **ACCEPTED / CORRECTED** — §10.1 isolates every v4 object and leaves legacy emitters on v3 |
| M2 closing the writer broke the continuous lease | **ACCEPTED / CORRECTED** — §11 retains the same writer/flock through terminal reproduction |
| M3 implementation observation was used as precedence | **ACCEPTED / CORRECTED** — §2 amends R17/contract directly and does not overrule D093 |
| M4 legacy `census_orchestrator` nullable-scalar crash was outside the path set | **ACCEPTED / DISCLOSED** — §6.5 records the unreachable residual; acquisition remains prohibited |
| M5 no mechanical execute-enablement mechanism | **ACCEPTED / CORRECTED** — §7.2 freezes two independent source constants and later constant-only activation instruments |
| M6 full-index member lacked a `census_registrants` row | **ACCEPTED / FAIL-CLOSED OPTION** — no entity is invented; the accession stays unestablished. The research-facing alternative is rejected, so no Joey-reserved choice remains |
| m1 read-only lease test would create a file | **ACCEPTED / CORRECTED** — §5.2 specifies non-mutating existing/absent behavior |
| m2 backup had a `0644` window/open handle | **ACCEPTED / CORRECTED** — §5.3 uses precreation `0600`, close, fsync, then digest |
| m3 recorded lease expiry could pass during a real run | **ACCEPTED / CORRECTED** — flock is authoritative; expiry cannot authorize takeover/resume |
| m4 wrong integration-test path | **ACCEPTED / CORRECTED** — §12.1 names `test_m3_cli.py` |
| m5 singleton scalar changed R58 `may` to `must` | **ACCEPTED / MADE EXPLICIT** — §6.4 freezes the lawful testable narrowing |
| m6 identity/consistency checks were unnamed | **ACCEPTED / CORRECTED** — §6.2 defines normalization, binding, resolver status, and blocking predicate |
| m7 relation writer versus no-second-writer rule | **ACCEPTED / CORRECTED** — contract amendment makes it one E0 writer invocation |
| m8 unbounded release hash could require an unauthorized path | **ACCEPTED / CORRECTED** — §8.2 adds pre-writer measurement/refusal and per-table lifetime |
| m9 partial transition could not encode two migrations | **ACCEPTED / CORRECTED** — §8.1 permits the exact ledger-backed zero/one/two list |
| m10 projection order relative to canonical resolution | **ACCEPTED / CORRECTED** — §6.4 places it after persisted resolution and tests the dependency |
| O1 duplicate full-catalog scans | **ADOPTED** — one per-table scan updates both required projections |
| O2 operator namespace degree of freedom | **ADOPTED** — production namespaces are fixed constants, not CLI options |
| O3 current schema generality | **ADOPTED AS EXPLANATION** — future-proof checks retained |
| O4 incomplete refusal reason for preparation helper | **ADOPTED** — timestamped reference seeding is named |
| O5 redundant E0 pre/post migration chains | **NOT ADOPTED** — cheap explicit proof that E0 applied no migration |

Sol/GPT also added under-lease preflight repetition, exact status/event-conditioned terminal fields,
run-directory and operational-sidecar boundaries, canonical-byte reuse, one-accession streaming, and
governance/executor path separation. These close race, representability, memory, privacy, and owner-
separation gaps without a new schema, data source, methodology, or network authority. No second
architecture reviewer is justified.

## 14. Complexity challenge and rejected alternatives

The design uses one new orchestration module, two commands, one narrow receipt successor, one
event schema, and two terminal schemas because the accepted architecture requires all five
responsibilities to be representable. It deliberately rejects:

- a new migration or new database table — migration `0014` already represents the canonical set;
- manual SQLite instructions — not an operator surface;
- modifying `prepare_operational_catalog()` — too broad for an exact transition;
- one giant replacement E0 parser — duplicates accepted parsers and persistence;
- a second membership table — conflicts with R58;
- an observation fallback — defeats canonical durability;
- a scalar or anchor fallback — false for multi-registrant accessions;
- a single opaque prose receipt — not independently reconstructable;
- automatic resume or automatic restore — conceals partial authoritative state;
- a generic workflow engine — unnecessary infrastructure for two bounded state machines; and
- full-catalog snapshots after E0 — the pre-E0 backup plus exact table identities is sufficient and
  materially cheaper.

The accepted reductions are fixed production namespaces, version-scoped receipt rules, one scan per
table snapshot, and no global reason-registry edit. The design does not add a workflow engine,
authorization file, signature system, or new database table.

## 15. What remains prohibited

Until later stage-specific owner instruments say otherwise, do not:

- apply `0014` or `0015` to the accepted catalog;
- run E0;
- run the D093 linkage diagnostic;
- run or implement the persistence bridge;
- create or apply migration `0016`;
- run E1, E2, or M3.4;
- enable network, SEC, or HTTP access; or
- treat any result as linkage credit, gate closure, selection authority, or progression authority.

## 16. Exact next action

Sol/GPT updates the current-state surfaces, runs the governance gates, and creates the one authorized
local governance commit. Then one genuinely fresh Claude Opus 5 Maximum implementation session,
with actual-model attestation and the exact §12 path boundary, implements and validates the disabled
operator surface against disposable fixtures only. It must not inspect private evidence, apply a
migration to the accepted catalog, run E0, or enable either activation constant.

```text
RESULT_TOKEN: M3_3_PRE_E0_EXECUTABILITY_REDESIGN_OWNER_ACCEPTED
M3_3_E0_OPERATIONAL_STATE: HELD
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: NO
M3_3_E0_EXECUTION_AUTHORIZATION: NO
IMPLEMENTATION_AUTHORIZATION: YES — §12 ONLY
MIGRATION_0016_AUTHORIZATION: NO
NETWORK / SEC / HTTP: NONE
REQUEST_CEILING: 0
```
