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

Reserve paths (Stage S5.4) are implemented and accepted — see the next section. Manifest, release,
and publication paths (Stage S6) are **not implemented** and appear nowhere in this map. No S5
selection and no reserve is a manifest or publication input.

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
resolve which specific tests a not-yet-written module (such as the future S6 manifest modules) will
need beyond the categories a governing stage contract names — see
[`Milestones/contracts/m23_s5_2.md`](../Milestones/contracts/m23_s5_2.md)'s "Required tests" for
S5.2, and [`m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md)'s "Required adversarial test
categories" for the accepted S5.1 core, as the precedent for what an S5.4 contract must state.
