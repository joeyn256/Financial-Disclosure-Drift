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
| `sec/accession_selector.py` (future, S5.1 — **does not exist**) | none exist | none exist | not applicable — no file to lint | not applicable | **Yes, when created** — same class as `entity_selector.py` above, and additionally blocked by `BLOCKED_PENDING_DECISION_018` (see `Milestones/contracts/m23_s5_1.md`) until Decision 018 is approved. |
| `sec/accession_selection_store.py` (future, S5.1 — **does not exist**) | none exist | none exist | not applicable | not applicable | **Yes, when created** — same class as `entity_selection_store.py` above, same block. |
| `src/disclosure_drift/reasons.py` (machine-readable reason-code registry) | `test_reasons.py` (code registry and per-code metadata), `test_storage_catalog.py` (catalog/storage reason references), `test_m23_pilot_schema.py` (pilot reason-scope FKs) | `tests/integration/test_r2_census_end_to_end.py` (reason codes written through a real census flow) | ruff, ruff format, mypy | **yes** — every reason code is an FK target of `reference_reason_codes`, seeded/referenced by migrations `0001`, `0002`, and `0009`. Run `test_migration_provenance.py` and `make sqlite-check`; a removed or renamed code can orphan persisted rows and break a foreign key that no unit test exercises. | **Yes, when the change alters methodological or fail-closed semantics** — e.g. adding, removing, or redefining a code that gates eligibility, review, or an affirmative quota (Decisions 013/014/016). Adding a purely descriptive code to an existing family is not an Opus-review class. |
| `release/hashing.py` | `test_m23_pilot_schema.py`, `test_release_forecast_and_audit.py` | none | ruff, ruff format, mypy | none directly (pure hashing over already-read content) | **Yes** — the canonical-JSON/normalization contract is reused by every future manifest hash (Decision 009 §10, Decision 013 §7); a change ripples everywhere that reuses it. |
| Migrations (`storage/migrations/*.sql`) | `test_migration_provenance.py`, plus the schema's own dedicated test file (e.g. `test_m23_pilot_schema.py` for `0009`/`0010`) | `tests/integration/test_r2_census_end_to_end.py`, `test_sec_cli.py` | ruff/mypy not applicable to SQL; `sqlite-check` | **yes, always** — full migration-provenance suite and a live SQLite-version check | **Yes** — schema is a persisted contract (CLAUDE.md rule 3/9); a new migration requires a preceding approved decision (see Decision 016 for the S3 precedent). |
| Decision records (`Docs/Decisions/*.md`) | none (not code) | none | Markdown link-check only | not applicable | **Yes, always** — a decision record is itself the output of project-owner + Opus methodological review; it is never edited by an engineering session (CLAUDE.md rule 3, rule 14). |
| CLI (`src/disclosure_drift/cli.py`) | `test_cli_coverage_arguments.py` (coverage/`--as-of` argument parsing and validation); the remaining surface is exercised through the integration tests to its right | `tests/integration/test_cli.py`, `test_sec_cli.py`, `test_no_network.py` | ruff, ruff format, mypy | none directly; exercises whatever subcommand touches storage | No, unless a subcommand's behavior (not just its wiring) changes — then follow the review rule for the underlying module. |
| Makefile and validation scripts (`Makefile`, `scripts/*.py`, `scripts/ruff_changed.sh`, `scripts/context_snapshot.sh`) | `scripts/check_no_secrets.py` / `scripts/check_repo_hygiene.py` are self-validating (run them directly). `scripts/ruff_changed.sh` backs `make lint-changed` / `make fast`, so a change there must be verified by running `make fast`; `scripts/context_snapshot.sh` by running `make context` from both the repository root and a nested directory | none | `bash -n` for shell scripts; ruff/mypy for Python scripts under `scripts/` | not applicable | No — these are process tooling, not methodology, unless a change would weaken a gate CI depends on (then treat as a CI-semantics change and flag it explicitly). |

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
resolve which specific tests a not-yet-written module (like the future accession selector) will need
beyond the categories already named in
[`Milestones/contracts/m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md)'s "Required adversarial
test categories."
