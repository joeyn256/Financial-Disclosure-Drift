# Change Impact Map — Disclosure Drift

**Purpose:** a manually curated, minimum-credible-validation lookup for the highest-value modules and
file classes in this repository. Given "I am about to change file X," this map answers: which tests
must pass, which static gates apply, whether a migration/SQLite integrity gate applies, and whether
this class of change normally requires an Opus methodological review before being accepted.

**This map does not claim automated dependency completeness.** It is curated by hand from the module
docstrings, the test suite's own imports, and the decision records that govern each area — not by a
dependency-graph tool. A module can have callers or effects this map does not list.

> **The map selects the minimum credible validation set; it never prohibits running additional tests
> when behavior crosses subsystem boundaries.** If a change plausibly touches more than the module
> you started in, run the broader set — this map is a floor, not a ceiling.

Static gates referenced below (`ruff`, `ruff format`, `mypy`) are always `make lint`, `make
format-check`, `make typecheck` respectively, unless noted otherwise. See the Makefile for exact
invocations.

| Module / file class | Direct test files | Relevant integration tests | Static gates | SQLite/migration integrity gate | Opus review normally required |
|---|---|---|---|---|---|
| `src/disclosure_drift/cohorts.py` | `tests/unit/test_cohorts.py` | `tests/integration/test_cli.py` (cohorts surfaced via CLI) | ruff, ruff format, mypy | none (no schema) | **Yes** — frozen research definition; CLAUDE.md rule 3 requires an approved decision record first, and any change is methodologically load-bearing. |
| `src/disclosure_drift/config.py` | `test_config.py`, `test_config_errors.py`, `test_env_overrides.py` | `tests/integration/test_cli.py`, `test_no_network.py` | ruff, ruff format, mypy | none | No, unless the change touches which fields validate against `cohorts.py` (then yes, by the cohorts rule above). |
| SEC response/retry/rate-limit modules (`sec/response_policy.py`, `sec/rate_limit.py`, `sec/transport.py`, `sec/httpx_transport.py`, `sec/http_client.py`) | `test_response_policy.py`, `test_rate_limit.py`, `test_sec_http_client.py`, `test_httpx_transport.py`, `test_optional_dependencies.py` | `tests/integration/test_no_network.py`, `test_sec_cli.py` | ruff, ruff format, mypy | none directly; verify no live network access is introduced (`make check` core-job assertions) | No, unless changing the 403/429 aggregate-cooldown or rate-ceiling policy itself (then yes — SEC-access-policy behavior). |
| `sec/census_orchestrator.py` | none dedicated — covered via `test_sec_parsers_and_census.py` | `tests/integration/test_r2_census_end_to_end.py` | ruff, ruff format, mypy | yes — writes through `storage/catalog.py`; run `test_storage_catalog.py` and `test_migration_provenance.py` | No, unless changing restart/resume state semantics (then yes — durability-affecting). |
| `sec/amendments.py` | `test_inventory_and_amendments.py` | none beyond the unit test | ruff, ruff format, mypy | none directly | No, unless changing parentage-evidence rules (Decision 008 §2) — then yes. |
| Temporal/availability modules (`sec/temporal.py`, `sec/availability.py`) | `test_temporal.py`, `test_availability_boundary.py` | `test_operating_calendar_evidence.py` (calendar-adjacent) | ruff, ruff format, mypy | none directly | **Yes** — leakage-boundary logic (Decision 010 §5–6); consult `Docs/leakage_register.md` before any change. |
| Inventory/catalog modules (`sec/inventory.py`, `storage/catalog.py`, `storage/sqlite.py`) | `test_inventory_and_amendments.py`, `test_storage_catalog.py` | `tests/integration/test_r2_census_end_to_end.py` | ruff, ruff format, mypy | **yes** — `test_migration_provenance.py` and a live `sqlite-check` (`make sqlite-check`, floor 3.37) | No, unless changing the single-writer invariant (Decision 009 §8) — then yes. |
| `src/disclosure_drift/pilot_policy.py` | `test_m23_pilot_schema.py` (policy-version-row agreement), `test_m23_entity_selection_store.py` | none | ruff, ruff format, mypy | **yes** — asserts agreement with `reference_policy_versions` seeded by migrations `0009`/`0010` | **Yes** — every constant here is owned by an approved decision (016, 017); a new or changed constant needs a decision record first. |
| `sec/entity_selector.py` (S4.1) | `test_m23_entity_selector.py`, `test_pilot_selection.py` | none (pure, in-memory — no integration surface) | ruff, ruff format, mypy | none (no SQLite access by design) | **Yes** — deterministic constrained-selector design is explicitly an Opus-review area (Decision 013 §5; milestone plan §17). |
| `sec/entity_selection_store.py` (S4.2) | `test_m23_entity_selection_store.py` | none | ruff, ruff format, mypy | **yes** — writes migration-`0009` tables; run `test_migration_provenance.py` alongside | **Yes** — persistence adapter for the frozen selector policy; changes affect run-state lifecycle (Decision 016 §5). |
| `sec/accession_selector.py` (S5.1 — accepted, committed at `m2.3-s5-complete`) | `test_m23_accession_selector.py` | none (pure, in-memory — no SQLite access by design) | ruff, ruff format, mypy | none (no SQLite access by design) | **Yes** — same class as `entity_selector.py` above; the joint selector is frozen by Decision 018 and accepted. It is the **sole methodological selector**, was **not modified by S5.2**, and its expected outputs are never relaxed to accommodate persistence. |
| `sec/accession_selection_store.py` (S5.2 — accepted, committed at `m2.3-s5-complete`) | `test_m23_accession_selection_store.py` | none | ruff, ruff format, mypy | **yes** — writes migration-`0009` tables and carries migration `0011`; run `test_migration_provenance.py` and `make sqlite-check` alongside | **Yes** — same class as `entity_selection_store.py` above; persistence adapter for the frozen joint selector, affecting run-state lifecycle (Decision 016 §5, Decision 018 §§18, 27), with storage-to-pure-input mappings governed by Decision 019. Identity, same-ID idempotence, and reconstruction are the highest-risk surface here: both public entry points must fail closed on the same stored corruption through the single `JointSelectionRunIdentity` comparison — a change that bypasses or narrows it is a review-class change. |
| `src/disclosure_drift/reasons.py` (machine-readable reason-code registry) | `test_reasons.py` (code registry and per-code metadata), `test_storage_catalog.py` (catalog/storage reason references), `test_m23_pilot_schema.py` (pilot reason-scope FKs) | `tests/integration/test_r2_census_end_to_end.py` (reason codes written through a real census flow) | ruff, ruff format, mypy | **yes** — every reason code is an FK target of `reference_reason_codes`, seeded/referenced by migrations `0001`, `0002`, and `0009`. Run `test_migration_provenance.py` and `make sqlite-check`; a removed or renamed code can orphan persisted rows and break a foreign key that no unit test exercises. | **Yes, when the change alters methodological or fail-closed semantics** — e.g. adding, removing, or redefining a code that gates eligibility, review, or an affirmative quota (Decisions 013/014/016). Adding a purely descriptive code to an existing family is not an Opus-review class. |
| `release/hashing.py` | `test_m23_pilot_schema.py`, `test_release_forecast_and_audit.py` | none | ruff, ruff format, mypy | none directly (pure hashing over already-read content) | **Yes** — the canonical-JSON/normalization contract is reused by every future manifest hash (Decision 009 §10, Decision 013 §7); a change ripples everywhere that reuses it. |
| Migrations (`storage/migrations/*.sql`) | `test_migration_provenance.py`, plus the schema's own dedicated test file (e.g. `test_m23_pilot_schema.py` for `0009`/`0010`) | `tests/integration/test_r2_census_end_to_end.py`, `test_sec_cli.py` | ruff/mypy not applicable to SQL; `sqlite-check` | **yes, always** — full migration-provenance suite and a live SQLite-version check | **Yes** — schema is a persisted contract (CLAUDE.md rule 3/9); a new migration requires a preceding approved decision (see Decision 016 for the S3 precedent). |
| Decision records (`Docs/Decisions/*.md`) | none (not code) | none | Markdown link-check only | not applicable | **Yes, always** — a decision record is itself the output of project-owner + Opus methodological review; it is never edited by an engineering session (CLAUDE.md rule 3, rule 14). |
| CLI (`src/disclosure_drift/cli.py`) | `test_cli_coverage_arguments.py` (coverage/`--as-of` argument parsing and validation); the remaining surface is exercised through the integration tests to its right | `tests/integration/test_cli.py`, `test_sec_cli.py`, `test_no_network.py` | ruff, ruff format, mypy | none directly; exercises whatever subcommand touches storage | No, unless a subcommand's behavior (not just its wiring) changes — then follow the review rule for the underlying module. |
| Makefile and validation scripts (`Makefile`, `scripts/*.py`, `scripts/ruff_changed.sh`, `scripts/context_snapshot.sh`) | `scripts/check_no_secrets.py` / `scripts/check_repo_hygiene.py` are self-validating (run them directly). `scripts/ruff_changed.sh` backs `make lint-changed` / `make fast`, so a change there must be verified by running `make fast`; `scripts/context_snapshot.sh` by running `make context` from both the repository root and a nested directory | none | `bash -n` for shell scripts; ruff/mypy for Python scripts under `scripts/` | not applicable | No — these are process tooling, not methodology, unless a change would weaken a gate CI depends on (then treat as a CI-semantics change and flag it explicitly). |

## Stage S5.2 impact paths (implemented and accepted)

Stage S5.2 is **`ACCEPTED_AND_COMPLETE`** — implemented under a bounded prompt inside the exact set
[`../Milestones/contracts/m23_s5_2.md`](../Milestones/contracts/m23_s5_2.md) authorizes, reviewed
independently under S5.3, and owner-accepted 2026-07-29 at the combined S5.1–S5.3 checkpoint (tag
`m2.3-s5-complete`). The storage-to-pure-input mappings the loader depends on are governed by
[Decision 019](Decisions/decision_019_m23_s5_storage_to_pure_input_mapping.md),
**`APPROVED — OWNER APPROVED 2026-07-28`**.

The table records which gates each path triggers **when it is changed again**. It authorizes no
further change: the S5.2 contract is complete and authorizes no new implementation, so a change to
any path below needs its own authorization.

| Path | Kind | Gates it triggers |
|---|---|---|
| `src/disclosure_drift/sec/accession_selection_store.py` | production module (S5.2) | ruff, ruff format, mypy; `test_m23_accession_selection_store.py`; `test_migration_provenance.py`; `make sqlite-check`; S5.1 and S4 regression suites |
| `src/disclosure_drift/pilot_policy.py` | policy constants — carries `PILOT_JOINT_SELECTOR_POLICY_VERSION` | ruff, ruff format, mypy; `test_m23_pilot_schema.py` (policy-version-row agreement), `test_m23_entity_selection_store.py`; SQLite/migration integrity gate |
| `src/disclosure_drift/reasons.py` | reason registry — carries the five Decision 018 §21 codes | ruff, ruff format, mypy; `test_reasons.py`, `test_storage_catalog.py`, `test_m23_pilot_schema.py`; `test_migration_provenance.py` and `make sqlite-check` (reason codes are FK targets of `reference_reason_codes`) |
| `src/disclosure_drift/storage/migrations/0011_m23_joint_selector_policy_reference.sql` | migration — INSERT-only, **no DDL** | `test_migration_provenance.py`, `test_m23_pilot_schema.py`, `make sqlite-check`; ruff/mypy not applicable to SQL |
| `tests/unit/test_m23_accession_selection_store.py` | primary S5.2 test module | ruff, ruff format, mypy |
| `tests/unit/test_m23_pilot_schema.py` | covers the `0011` policy row | ruff, ruff format, mypy |
| `tests/unit/test_migration_provenance.py` | extends provenance/ordering coverage to `0011` | ruff, ruff format, mypy |
| `tests/unit/test_reasons.py` | asserts the five S5 codes and that existing codes are unchanged | ruff, ruff format, mypy |

Run as regression **without editing**: `test_m23_accession_selector.py` (S5.1),
`test_m23_entity_selector.py` and `test_m23_entity_selection_store.py` (S4), plus the lifecycle and
catalog integrity tests named in the table above.

Reserve paths (Stage S5.4) are implemented and accepted — see the next section. Manifest paths
(Stage S6) are **implemented and accepted** — see "Stage S6 impact paths" below. **Publication,
approval, live-metadata, and CLI paths remain unimplemented and unauthorized** — **Milestone 3
phases M3.1–M3.4**, formerly Stages S7–S10 (Decision 024 §5.1).

## Stage S5.4 impact paths (implemented and accepted)

Stage S5.4 is **complete and owner-accepted** (2026-07-30, final independent recommendation
`ACCEPT_M23_S5_4_FOR_CHECKPOINT`, accepted suite 1899 passed and 1 skipped), checkpointed at
`m2.3-s5.4-complete`. Its contract,
[`../Milestones/contracts/m23_s5_4.md`](../Milestones/contracts/m23_s5_4.md), is now
`ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`.
[Decision 020](Decisions/decision_020_m23_s5_4_reserve_architecture.md) is
**`APPROVED — OWNER APPROVED 2026-07-30`** and records the final acceptance in §19 and the five
accepted methodological limitations in §19.1.

**All twelve paths below now exist**, and migration `0012` is created and accepted. They are exactly
the set the contract authorized — nothing widened it. This section records which gates each triggers,
so a future change to any of them runs the right suites. **It authorizes no edit**: S5.4 is closed, and
changing any of these paths requires a new explicit owner authorization and a new contract.

Three structural constraints govern every path below and should be read before planning any change to
them. Migration `0009` requires each reserve package's quota-contribution set to equal its target
entity's **exactly**, checked on the `running -> feasible` transition; every reserve,
quota-contribution, and quota-member write requires `run_state = 'running'`, with `feasible ->
running` an illegal transition, so **reserves cannot be added to an already-feasible run** and all of
this work lands inside the S5 joint run's single existing transaction; and **no table in the schema
can durably record a target-specific no-compatible-reserve outcome** — none carries all three of
`selection_run_id`, a selected entity, and a `reference_reason_codes` foreign key, which is why the
owner authorized migration `0012` in principle (Decision 020 §8).

| Path | Kind | Gates it triggers |
|---|---|---|
| `src/disclosure_drift/sec/accession_selector.py` | bounded edit — one additive public quota-contribution membership output; no policy, objective, ordering, or quota change | ruff, ruff format, mypy; `test_m23_accession_selector.py`; `test_m23_accession_selection_store.py`; S4 regression |
| `src/disclosure_drift/sec/reserve_selector.py` | new pure module — reserve ranking, package assembly, signature computation | ruff, ruff format, mypy; `test_m23_reserve_selector.py`; S5.1 regression |
| `src/disclosure_drift/sec/accession_selection_store.py` | bounded edit — persist and reconstruct contributions, members, and reserves in the existing single transaction | ruff, ruff format, mypy; `test_m23_accession_selection_store.py`; `test_m23_pilot_schema.py`; `test_migration_provenance.py`; `make sqlite-check` |
| `src/disclosure_drift/reasons.py` | bounded edit — register exactly **one** code, `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` (`REVIEW_PILOT_RESERVE_POOL_EXHAUSTED` is **not** authorized) | ruff, ruff format, mypy; `test_reasons.py`, `test_storage_catalog.py`, `test_m23_pilot_schema.py`; `test_migration_provenance.py` and `make sqlite-check` |
| `tests/unit/test_m23_reserve_selector.py` | new primary test module | ruff, ruff format, mypy |
| `tests/unit/test_m23_accession_selector.py` | bounded edit — membership emission and the achieved-count invariant | ruff, ruff format, mypy |
| `tests/unit/test_m23_accession_selection_store.py` | bounded edit — contribution, member, and reserve persistence and reconstruction | ruff, ruff format, mypy |
| `tests/unit/test_reasons.py` | bounded edit — the one new code | ruff, ruff format, mypy |
| `src/disclosure_drift/storage/migrations/0012_m23_selection_entity_reasons.sql` | **new migration — DDL-only**, reproducing the complete SQL frozen in Decision 020 §8.2: one new STRICT `pilot_selection_entity_reasons` table plus four triggers — fail-closed INSERT/UPDATE/DELETE lifecycle guards whose UPDATE form checks **both** the OLD and the NEW associated run and holds `selection_run_id`/`snapshot_id`/`cik_numeric` immutable, and one additive feasible-transition disposition-completeness trigger. Seeds no policy row; edits, replaces, and reinterprets no existing migration | `test_migration_provenance.py`, `test_m23_pilot_schema.py`, `make sqlite-check` (floor 3.37, required for STRICT); ruff/mypy not applicable to SQL |
| `tests/unit/test_m23_pilot_schema.py` | bounded edit — the new table's keys, foreign keys, CHECKs; the fail-closed lifecycle guards including the OLD-and-NEW run check and immutable target identity; and the feasible-transition disposition trigger | ruff, ruff format, mypy |
| `tests/unit/test_migration_provenance.py` | bounded edit — extends contiguous-chain, ordering, and byte-immutability coverage to `0012` | ruff, ruff format, mypy |
| `tests/unit/test_storage_catalog.py` | bounded edit — the one new reason code through existing registry/catalog conventions | ruff, ruff format, mypy |

**Migrations: exactly one, `0012`, created and accepted.** For the reserve,
contribution, and member families no migration is needed — migration `0009` already contains every
table, and `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION` and its `pilot_replacement_signature`
reference row both already exist. Registering the one new reason code needs none either, since
`reference_reason_codes` is seeded at runtime from `reasons.py`. **But the durable
no-compatible-reserve record has no lawful location in migration `0009`**, so the owner authorized
`0012_m23_selection_entity_reasons.sql` rather than weakening the durability requirement. Its design
is frozen by Decision 020 §8.2 — table plus all four triggers — and that exact DDL passed the focused
independent governance re-review that preceded approval, closing the 2026-07-29 lifecycle defect. **The
frozen SQL was reproduced verbatim**, and the final independent acceptance review confirmed the
migration's statement region is byte-identical to it, that it adds exactly one `STRICT` table and four
triggers, and that it alters no existing object. **No migration other than `0012` is authorized**, new
or edited. Migrations `0009`–`0011` are unmodified and byte-identical, including their inherited
OLD-only guard behaviour. **The migration chain now ends at `0012`.**

**Test scoping (Decision 020 §8.3, binding).** Each invariant is exercised at the layer that enforces
it: unauthorized reserve scope or reason code at the `pilot_selection_entity_reasons` CHECK
constraints; duplicate no-compatible-reserve disposition rows at that table's primary key; duplicate
rank-1 reserve packages at migration `0009`'s existing
`UNIQUE (selection_run_id, snapshot_id, target_cik_numeric, reserve_rank)`. The feasible-transition
trigger is not tested against states those constraints make unconstructible, but its tests still cover
every constructible invalid state. This changes no gate in the table above — it determines which
assertions land in `test_m23_pilot_schema.py`, not which suites run.

**Membership rows.** All three families are emitted from **one** S5.1 output, with no S5.2 or
reserve-module re-derivation. Only `pilot_selected_entity_quota_contributions` is load-bearing for the
reserve trigger; `pilot_selected_accession_quota_contributions` and `pilot_quota_result_members` are
provenance (Decision 020 §6).

Run as regression **without editing**: `test_m23_entity_selector.py` and
`test_m23_entity_selection_store.py` (S4). `tests/unit/test_m23_pilot_schema.py` carries the S3-era
reserve schema tests — rank uniqueness per target, target/package signature mismatch, and independent
signature recomputation from normalized content — which the accepted S5.4 implementation satisfies
rather than replaces.

**Accepted limitations recorded against these paths** (Decision 020 §19.1), relevant when planning any
future change to them: cross-anchor amendment-family resolution follows resolved-root accession
identity without an anchor-equality condition; provenance-oriented union member sets may exceed a
minimal witness; the exact target-selected versus complete-replacement bundle comparison may reduce
reserve availability; the seven named signature contribution values are counts of achieved units, not
Boolean presence; and the schema-layer subset/superset/empty transition-test observation is nonblocking
and was independently validated at acceptance.

## Stage S6 impact paths (implemented and accepted)

**Everything in this section now exists, and nothing here authorizes an edit.** Stage S6 is
**implemented, independently accepted, and checkpointed** at `m2.3-s6-complete`.
[Decision 021](Decisions/decision_021_m23_s6_manifest_construction.md) is at **v0.5** and
**`ACCEPTED`** (owner approved 2026-07-30) and remains the controlling architecture record;
[`../Milestones/contracts/m23_s6.md`](../Milestones/contracts/m23_s6.md) is now
`ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO` and authorizes nothing further; and
[Decision 023](Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) records acceptance,
outcome `M23_STAGE_S6_ACCEPTED_AND_COMPLETE`. **Changing any path below requires a new explicit owner
authorization and its own contract.** The table records which gates each path triggers when it is
changed again.
[Decision 022](Decisions/decision_022_m23_s6_reserve_rank_applicability.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) additionally clarifies Decision 021 §13.2.1 item 46:
reserve rank is applicable **once per persisted reserve package** and is **structurally not
applicable** for a selected target that carries the persisted `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`
disposition instead, so a zero-package run stays manifest-eligible. Touching item-46 applicability
therefore means touching `release/pilot_manifest.py` and `sec/pilot_manifest_store.py` and running
both S6 test modules **plus** the reserve, disposition, reconstruction, and replay regressions listed
below — a zero-package or mixed-coverage run is a first-class case, not an edge case.

**The delivered path set is ten, not seven.** The contract authorized seven and that authorization is
unchanged by the v0.2, v0.3, v0.4, and v0.5 corrections. Migration `0013` then forced three further
test edits, which Decision 023 §4 **ratifies retroactively** — they are marked **(ratified)** in the
table. Every other production, test, migration, decision, and contract path remains prohibited unless
later owner-authorized, and the ratification is of three named paths only, never a general widening.

Six structural constraints govern the whole stage and should be read before planning any change to
it. `pilot_manifest_versions` has **no `INSERT` guard and consults no run state**, so a manifest over
a `running` or `infeasible` run — including the permanently-`running` S4 draft — is accepted and
approvable today; `pilot_selection_runs.selection_result_sha256` has **no trigger at all**, so it is
writable, overwritable, and clearable on any run in any state, **and the table has no `INSERT` guard
either, so a run can be created already `feasible` and already sealed**; **no existing trigger
protects any `pilot_manifest_versions` identity column**, so `manifest_id`, `manifest_schema_version`,
`ordinal_version`, and `supersedes_manifest_id` are all rewritable after insert; and the accepted
S5.2 reconstruction path **does not read the seal**, so a sealed digest is invisible to it; and
**`INSERT OR REPLACE` rewrites a `pilot_manifest_versions` row wholesale past every existing guard**,
because all four of migration `0009`'s manifest triggers are `BEFORE UPDATE` or `BEFORE DELETE` and
SQLite does not fire a delete trigger for replacement unless `PRAGMA recursive_triggers` is on, which
this repository never sets. Decision 021 §§3.1–3.3 and §3.5 record the direct probes, §15 the
authorized **eight-trigger** migration, and §12 the S6-owned verification that closes the S5.2 gap
without reopening S5.2. The sixth constraint, closed at v0.5: **`pilot_selection_runs` itself had no
row-replacement guard, no delete guard, and no guard on any identity column**, so a sealed terminal
digest could be cleared by `INSERT OR REPLACE`, the run removed by `DELETE`, and `selection_run_id`,
`snapshot_id`, or `selection_input_sha256` rewritten by direct `UPDATE` — under either
`recursive_triggers` setting. Decision 021 §3.6 records those probes, triggers 6, 7, and 8 close
them, and **§15.5 states the resulting append-once and recomputability guarantee**.

| Delivered path | Kind | Gates it triggers |
|---|---|---|
| `src/disclosure_drift/release/pilot_manifest.py` | new pure module — the eight component digests, the five-column structural-fingerprint reduction, `selection_result_sha256`, the root, `manifest_id`, the §13.2 document schema and the §13.2.1 81-item §10 crosswalk, and its canonical JSON | ruff, ruff format, mypy; `test_m23_pilot_manifest.py`; release regression (`test_release_forecast_and_audit.py`) |
| `src/disclosure_drift/sec/pilot_manifest_store.py` | new persistence adapter — row loading, eligibility, sealing, one `proposed` manifest row plus its document, verification; six required explicit arguments (Decision 021 §8.4) | ruff, ruff format, mypy; `test_m23_pilot_manifest_store.py`; `test_m23_pilot_schema.py`; `test_migration_provenance.py`; `make sqlite-check`; S5.1/S5.2/S5.4 and S4 regression |
| `src/disclosure_drift/storage/migrations/0013_m23_manifest_lifecycle_guards.sql` | **new migration — DDL-only**, **eight** new triggers and no table, column, or index, reproducing the Decision 021 §15.1 eight-block SQL byte-for-byte and its nine §15.3 digests | `test_migration_provenance.py`, `test_m23_pilot_schema.py`, `make sqlite-check` (floor 3.37); ruff/mypy not applicable to SQL |
| `tests/unit/test_m23_pilot_manifest.py` | new primary test module | ruff, ruff format, mypy |
| `tests/unit/test_m23_pilot_manifest_store.py` | new test module | ruff, ruff format, mypy |
| `tests/unit/test_m23_pilot_schema.py` | bounded edit — the **eight** new triggers adversarially, including the `INSERT OR REPLACE` routes on both tables, the `DELETE` refusals in every run state, the three selection-run identity fields, and the byte-preservation assertions, all under every pragma combination, plus the `_insert_manifest` fixtures a sealed feasible run now requires | ruff, ruff format, mypy |
| `tests/unit/test_migration_provenance.py` | bounded edit — extends contiguous-chain, ordering, and byte-immutability coverage to `0013` | ruff, ruff format, mypy |
| `tests/unit/test_storage_catalog.py` | **(ratified)** forced consequence — the canonical migration chain is asserted by exact version **and** name, so `(13, "m23_manifest_lifecycle_guards")` had to be added | ruff, ruff format, mypy |
| `tests/unit/test_m23_entity_selection_store.py` | **(ratified)** forced consequence — its accepted S4 corruption fixture built its precondition with a plain `UPDATE` on `selection_input_sha256`, which trigger 8 now refuses | ruff, ruff format, mypy |
| `tests/unit/test_m23_accession_selection_store.py` | **(ratified)** forced consequence — same cause at four call sites, plus narrowing `_corrupt_sealed_row`, whose wildcard guard-drop would otherwise have swallowed the new `pilot_selection_run_delete_guard` | ruff, ruff format, mypy |

**The three ratified paths changed no production module, no S4 or S5 methodology, and no assertion's
strength**; the rewritten corruption fixtures are narrower and more fail-closed than the code they
replaced — a scratch-catalog allowlist, exactly one trigger dropped per statement, restoration from
the captured `sqlite_master` definition in a `finally` with reinstallation asserted, and foreign keys
left enabled except where the modelled corruption is itself a broken reference (Decision 023 §4.1).

**Migration: exactly one, `0013`.** Its complete **eight-block** SQL is frozen
in Decision 021 §15.1 with per-block and concatenation SHA-256 digests, byte counts, line counts, and
the exact concatenation rule in §15.3; a difference between the written file's statement region and
that SQL is a defect in the file, never a correction to the record — and the final independent
acceptance review confirmed byte-for-byte identity, all nine digests, the 10939-byte and 186-line
counts, exactly eight triggers, and no table, index, column, or data statement. The v0.4 **five-block** region
(7436 bytes, 129 lines, `6bfb897c…`), the v0.3 **four-block** region (4990 bytes, 88 lines,
`51151767…`), and the v0.1 three-block region are all **withdrawn as compositions** and must not be
reproduced; the individual digests of blocks 1–5 are **not** withdrawn and carry forward unchanged. Migrations `0009`–`0012` must remain
byte-identical. **No migration other than `0013` is authorized.**

**Behaviour-neutrality (Decision 021 §3.4).** No accepted S4 or S5 statement names
`selection_result_sha256`, `selection_run_id`, or `snapshot_id` in an `UPDATE … SET` list; none names
`selection_result_sha256` in an `INSERT` column list; and none writes `pilot_manifest_versions` at
all, and none uses `INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, or `DELETE` against
either table. The accepted replay path `SELECT`s the run first and reconstructs and returns when it
exists, inserting only when it does not. None of the eight new triggers can fire on any accepted code
path, and migration `0013` changes no accepted **production** behaviour. **The consequences landed in
tests, and were wider than foreseen.** Decision 021 §20 anticipated that `test_m23_pilot_schema.py`'s
`_insert_manifest` helper would need a `feasible` run sealed by a **later `UPDATE`** — a pre-sealed
`INSERT` is refused — which is why that module was a bounded-edit path; §20 states the three fixture
changes and the two legitimate routes. The same mechanism additionally reached three modules §20 did
not name: the migration-chain assertion in `test_storage_catalog.py`, and the plain-`UPDATE`
corruption fixtures in `test_m23_entity_selection_store.py` and
`test_m23_accession_selection_store.py`, all three ratified by Decision 023 §4. **When adding a
lifecycle trigger, search the suite for fixtures that construct the state the trigger now forbids** —
that is the generalizable lesson this row records.

**Not authorized, and appearing nowhere in this map:** owner approval of a manifest, publication,
Gate F live-metadata safety work, live SEC metadata execution, a real candidate snapshot, the exact
real-data manifest instance, **any CLI surface**, and any projection-recovery writer. Those are
**Milestone 3 phases M3.1–M3.4** and later operational work — the stages Decision 021 §§16 and 17
called S7–S10, renamed without substantive change by Decision 024 §5.1. `release/hashing.py`,
`release/manifest.py`, `paths.py`, `pilot_policy.py`, `reasons.py`, `cli.py`, and every accepted
S4/S5 module are **reused or regressed, never edited**.

## Decision 024 — the Milestone 2 / Milestone 3 boundary (governance only, zero impact)

[Decision 024](Decisions/decision_024_m2_m3_boundary_governance.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) fixes accepted M2.3 S6 as the end of Milestone 2
implementation and transfers the obligations formerly called S7–S10 into Milestone 3 as **M3.1–M3.4**,
adding **M3.5** for integrated real-pilot acceptance and Milestone 3 closeout.

**It is governance only, and its impact set is empty.** The boundary session changed exactly these
files, all of them governance or navigation:

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_024_m2_m3_boundary_governance.md` | new decision record | Markdown link-check only |
| `Docs/Decisions/decision_registry.md` | registry — index row and controlling-record row | Markdown link-check only |
| `Docs/decision_index.md` | topic index — Decision 024 section and the S7–S10 → M3.x retargeting | Markdown link-check only |
| `Docs/architecture_map.md` | new §0 governance-boundary layer; S7–S10 references retargeted | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | current-state ledger and machine-readable markers | `make context` resolves the markers |
| `Milestones/contracts/README.md` | contract index — Decision 024 identified as governance, not a contract | Markdown link-check only |
| `README.md` | the single live `**Status:**` line, which named M2.2 as Milestone 2's furthest completed stage and became false at accepted S6 | Markdown link-check only |

**Zero impact, stated explicitly:** no production module, test, migration, or configuration file
changed; no methodology, hash preimage, canonicalization rule, crosswalk row, or classification total
changed; no data was read, written, acquired, or published; no network boundary moved; no publication
or approval path was created; and **no implementation authority was granted** — implementation
authorization is `NO` for every Milestone 3 phase, and assignment to Milestone 3 is not authorization
to begin it (Decision 024 §8).

**The accepted S6 delivered-path record above is unchanged** and remains the authority on what Stage
S6 shipped and which gates each of its ten paths triggers.

## Decision 025 — integrated-audit documentation corrections (documentation only, zero impact)

[Decision 025](Decisions/decision_025_integrated_audit_documentation_corrections.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) records the final integrated Milestones 1–2 audit result
`REQUIRES_BOUNDED_INTEGRATED_FIXES` — **nine categories confirmed
`INTEGRATED_ACCEPTANCE_CONFIRMED`, with no implementation, methodology, migration, hashing,
selection, manifest, leakage, security, or test defect** — and authorizes the one bounded
documentation correction it required. Formal outcome
`INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED`.

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_025_integrated_audit_documentation_corrections.md` | new decision record | Markdown link-check only |
| `Docs/sec_data_dictionary.md` | **the correction** — scope moved from migrations `0001`–`0008` to `0001`–`0013`, adding §§9–14 covering the 22 `pilot_*` tables, the `0012` and `0013` trigger inventories, the digest dependency map, and a migration coverage table | Markdown link-check; verify against `sqlite_master` on a scratch `0001`–`0013` catalog |
| `Docs/decision_index.md` | Decision 025 section + the deviation-register pointer | Markdown link-check only |
| `Docs/Decisions/decision_registry.md` | index row + two controlling-record rows | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | current-state ledger and machine-readable markers | `make context` resolves the markers |
| `Milestones/contracts/README.md` | next-authorized-action pointer | Markdown link-check only |
| `CLAUDE.md` | reading order gains pointers to `Docs/preregistration.md` §25 and the data dictionary | Markdown link-check only |

**Zero impact:** no production module, test, migration, configuration, or CI file changed; no
methodology, hash preimage, canonicalization rule, crosswalk row, or classification total changed;
no data read, written, acquired, or published; no network boundary moved; **no implementation
authority granted**. `Docs/preregistration.md` was **not** edited — the deviation register is
pointed at, not altered. Decisions 021–024 and every completed contract are byte-unchanged.

**When Milestone 3 introduces schema, `Docs/sec_data_dictionary.md` must be extended in the same
pass** — that is the standing lesson this correction records.

## Bounded verification fix — completing the pilot data-dictionary coverage (documentation only, zero impact)

The fresh independent verification required by [Decision 025](Decisions/decision_025_integrated_audit_documentation_corrections.md)
§§8–9 confirmed Decisions 023, 024, and 025 independently and found the engineering, migrations,
tests, methodology, hashing, reproducibility, security, and leakage controls sound. It returned
`REQUIRES_BOUNDED_VERIFICATION_FIXES` on **one** closeout blocker and one cosmetic issue, both
documentation-only, and both corrected here under the authority Decision 025 §6.1 already granted.
**No new decision record is required, and none was created.**

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/sec_data_dictionary.md` | **DOC-1** — new §13.5 giving `pilot_projection_recovery_events` the complete per-table schedule §6.1 requires (migration `0009`; purpose; owning stage; `Operational-only` state class; 12 columns; PK `event_id`; FK `manifest_id` → `pilot_manifest_versions`; the exact uniqueness position; every material CHECK; append-only lifecycle and both immutability triggers; writer none; reader none; digest role none; the explicit input exclusions; the future-stage boundary). Plus three precision corrections — the `uq_pilot_candidate_accession_single_anchor` partial predicate, the candidate-entity strata index's leading `snapshot_id`, and the migration-`0012` feasible-transition trigger's declared event | Markdown link-check; verify against `sqlite_master` and `PRAGMA` output on a scratch `0001`–`0013` catalog |
| `Docs/Decisions/decision_registry.md` | **DOC-2** — removes only the three blank lines that terminated the Markdown Index table before rows `023`, `024`, and `025`, so rows `001`–`025` render as one continuous table. No row content, status, title, date, supersession field, or summary changed | Markdown link-check; mechanical table-structure check |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | current-state ledger and machine-readable markers | `make context` resolves the markers |
| `Milestones/contracts/README.md` | next-authorized-action pointer | Markdown link-check only |

**Zero impact:** no production module, test, migration, configuration, or CI file changed; no
methodology, schema, database behaviour, hash preimage, canonicalization rule, crosswalk row, or
classification total changed; no data read, written, acquired, or published; no network boundary
moved; **no implementation authority granted**. Decisions 021–025, every completed contract, and
`Docs/preregistration.md` are byte-unchanged. The migration chain remains contiguous through `0013`
with nothing beyond it, and migration `0013`'s normative region remains 10939 bytes over 186 lines
at `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595`.

**The count distinction this correction preserves:** migration `0009` introduced **21** `pilot_*`
tables, migration `0012` introduced **one** more (`pilot_selection_entity_reasons`), and the catalog
through `0013` therefore holds **22**. All 22 now carry the complete §6.1 schedule.

**That rereview has since run and passed** — see the Decision 026 section below, which records formal
closeout.

## Decision 026 — final closeout of Milestones 0, 1, and 2 (governance and navigation only, zero impact)

[Decision 026](Decisions/decision_026_milestones_0_1_2_final_closeout.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) records the final fresh independent rereview outcome
`ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT` and the formal closeout of
**Milestone 0**, **Milestone 1**, and **all of Milestone 2** — M2.1, M2.2, and M2.3 through accepted
Stage S6. Formal outcome `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`.

**It is governance and navigation only, and its impact set is empty.** The closeout session changed
exactly these files:

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md` | new decision record | Markdown link-check only |
| `Docs/Decisions/decision_registry.md` | registry — Index row `026` (added without a preceding blank line, so rows `001`–`026` stay one continuous table) + one controlling-record row | Markdown link-check; mechanical table-structure check |
| `Docs/decision_index.md` | topic index — Decision 026 section and the closeout-sequence wording | Markdown link-check only |
| `Docs/architecture_map.md` | §0 milestone-status layer only — Milestone 0 added, Milestones 0/1/2 marked formally closed, Milestone 3 marked next planning phase; plus the closing lifecycle note's stale next-action sentence | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | current-state ledger and machine-readable markers | `make context` resolves the markers |
| `Milestones/contracts/README.md` | contract index — closure recorded; Decision 026 identified as a decision record, not a contract | Markdown link-check only |
| `README.md` | the live `**Status:**` block, whose "one final independent integrated audit … remains" sentence became false at this commit; plus the stale `Decisions 001-010` navigation line in "Repository structure" | Markdown link-check only |

**Zero impact, stated explicitly:**

- **zero production impact** — no module under `src/` changed;
- **zero test impact** — no file under `tests/` changed;
- **zero migration impact** — migrations `0001`–`0013` are byte-identical to `m2.3-s6-complete`, the
  chain is contiguous with nothing beyond `0013`, and `0013`'s normative region remains 10939 bytes
  over 186 lines at `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595`;
- **zero configuration impact** — `configs/`, `pyproject.toml`, `Makefile`, and `.github/` unchanged;
- **zero methodology impact** — no hypothesis, cohort window, maturity gate, outcome definition,
  threshold, seed, selection rule, reserve rule, or manifest rule changed;
- **zero identity impact** — no hash preimage, digest, `manifest_id`, run identity, canonicalization
  rule, crosswalk row, or classification total changed;
- **zero data impact** — no data was read, written, acquired, or derived;
- **zero network impact** — no network boundary moved and no SEC access occurred;
- **zero publication impact** — no root was approved and nothing was published;
- **three annotated completion tags** — `m0-complete`, `m1-complete`, and `m2-complete`, all created
  at the closeout commit; every earlier tag is immutable and unmoved, and `m2.3-s6-complete` remains
  at `5c53412d820fe20a7bd727eac333ae2fb8724cd6`;
- **next action `MILESTONE_3_MASTER_PLANNING`**;
- **no Milestone 3 implementation authority** — closure satisfies only the precondition Decision 024
  §8 imposed; its five entry conditions all still apply, implementation authorization remains `NO`
  for every phase, and no Milestone 3 contract exists or was created.

`Docs/preregistration.md`, `Docs/sec_data_dictionary.md`, Decisions 001–025, `CLAUDE.md`, and every
completed contract are **byte-unchanged**. **Every prior delivered-path record above is preserved**
and remains the authority on what each stage shipped and which gates each of its paths triggers.

## Decision 027 — Milestone 3 master plan and operational readiness (planning only, zero impact)

[Decision 027](Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) records the complete Milestone 3 master plan and
operational-readiness design. Formal outcome
`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`.

**It is planning and navigation only, and its impact set is empty.** The planning session changed
exactly these files:

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md` | new decision record | Markdown link-check only |
| `Milestones/milestone_03_master_plan.md` | new — the five-phase roadmap, 36 fields per phase, the request-volume policy, and the mandatory future-contract contents | Markdown link-check only |
| `Docs/m3/operator_runbook.md` | new — the 31-step Mac operator sequence with per-command status labels | Markdown link-check; command-status label check |
| `Docs/m3/offline_rehearsal_spec.md` | new — the twenty-scenario offline rehearsal, **specified, not implemented and not run** | Markdown link-check only |
| `Docs/m3/execution_receipt_spec.md` | new — the versioned receipt design, **creating no code and no table** | Markdown link-check; prohibited-field scan |
| `Docs/m3/limitations_register.md` | new — every inherited limitation plus ten new M3 entries, **closing none** | Markdown link-check only |
| `Docs/m3/templates/request_budget.md` | new template | Markdown link-check only |
| `Docs/m3/templates/gate_f_checklist.md` | new template | Markdown link-check only |
| `Docs/m3/templates/gate_h_checklist.md` | new template | Markdown link-check only |
| `Docs/m3/templates/schema_drift_incident.md` | new template | Markdown link-check only |
| `Docs/m3/templates/interrupted_run_recovery.md` | new template | Markdown link-check only |
| `Docs/m3/templates/real_snapshot_evidence_packet.md` | new template | Markdown link-check only |
| `Docs/m3/templates/root_hash_approval_packet.md` | new template | Markdown link-check only |
| `Docs/Decisions/decision_registry.md` | registry — Index row `027` (added with no preceding blank line, so rows `001`–`027` stay one continuous table) + one controlling-record row | Markdown link-check; mechanical table-structure check |
| `Docs/decision_index.md` | topic index — the Decision 027 section and the planning-artifact locations | Markdown link-check only |
| `Docs/architecture_map.md` | §0 Milestone 3 row and the planning-artifact layer; the closing lifecycle note | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | current-state ledger and machine-readable markers | `make context` resolves the markers |
| `Milestones/contracts/README.md` | contract index — Decision 027 identified as a decision record, not a contract; next-action pointer | Markdown link-check only |
| `README.md` | the live `**Status:**` block's next-phase wording | Markdown link-check only |

**Zero impact, stated explicitly:**

- **zero production impact** — no module under `src/` changed;
- **zero test impact** — no file under `tests/` changed;
- **zero migration impact** — migrations `0001`–`0013` are byte-identical, the chain is contiguous
  with nothing beyond `0013`, and `0013`'s normative region remains 10939 bytes over 186 lines at
  `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595`;
- **zero configuration impact** — `configs/`, `pyproject.toml`, `Makefile`, and `.github/` unchanged;
- **zero CLI impact** — no subcommand added, removed, or changed. Every Milestone 3 command named in
  the runbook is labelled `PLANNED — NOT YET IMPLEMENTED`;
- **zero methodology impact** — no hypothesis, cohort window, maturity gate, outcome definition,
  threshold, seed, selection rule, reserve rule, or manifest rule changed;
- **zero identity impact** — no hash preimage, digest, `manifest_id`, run identity, canonicalization
  rule, crosswalk row, or classification total changed. **The execution receipt the planning pack
  designs enters no governed identity** (Decision 027 §§17–18);
- **zero data impact** — no data read, written, acquired, or derived;
- **zero network impact** — no network boundary moved and no SEC access occurred;
- **zero publication impact** — no root approved and nothing published;
- **no tag** — none created, moved, or deleted;
- **next action `INDEPENDENT_M3_MASTER_PLAN_REVIEW`**;
- **no Milestone 3 implementation authority** — planning a phase is not authorization to begin it,
  all five Decision 024 §8 entry conditions still apply, implementation authorization remains `NO`,
  and **no Milestone 3 contract exists or was created**.

`Docs/preregistration.md`, `Docs/sec_data_dictionary.md`, Decisions 001–026, `CLAUDE.md`, and every
completed contract are **byte-unchanged**. **Every prior delivered-path record above is preserved**
and remains the authority on what each stage shipped.

**When Milestone 3 implementation is eventually authorized, its impact paths get their own section
here** — written by that phase's session, under its own contract, and never in advance.

## Notes on reading this table

- **"Direct test files"** are the tests whose primary subject is the listed module — run these first,
  always.
- **"Relevant integration tests"** exercise the module as part of a larger flow — run these when the
  change could affect cross-module behavior, not only the module's own unit contract.
- **"SQLite/migration integrity gate"** means: if yes, run `test_migration_provenance.py` and (for
  schema changes) `make sqlite-check` in addition to the module's own tests, because a passing unit
  test does not prove the persisted schema stayed internally consistent.
- **"Opus review normally required"** reflects the pattern already established in this repository
  (`Milestones/milestone_2_3_pilot_selection_plan.md` §17: schema/migration architecture, selector
  design, and final integration/adversarial review are Opus-assigned; bounded implementation from an
  already-frozen decision is not). It is a norm this map records, not a rule this map creates — the
  actual requirement comes from CLAUDE.md rule 3 (frozen definitions) and the decision records
  themselves, not from this table.

## What this map does not do

It does not replace `make check` (the full acceptance gate) as the final bar before accepting work.
It does not enumerate every test in the suite — see the test directory itself for that. It does not
resolve which specific tests a not-yet-written module will need beyond the categories a governing
decision and stage contract name — for S6, now written and accepted, those were
[Decision 021](Decisions/decision_021_m23_s6_manifest_construction.md) §20 and
[`Milestones/contracts/m23_s6.md`](../Milestones/contracts/m23_s6.md)'s "Required tests", with
[`m23_s5_4.md`](../Milestones/contracts/m23_s5_4.md), [`m23_s5_2.md`](../Milestones/contracts/m23_s5_2.md),
and [`m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md) as the accepted precedents for what a stage
contract must state.
