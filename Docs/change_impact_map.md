# Change Impact Map — Disclosure Drift


> **CURRENT STATE, 2026-08-14 — M3.3-I/R IS COMPLETE AND OWNER-ACCEPTED, AND THE NEXT ACT IS
> THE DECISION-078 PRE-E0 READ-ONLY REAL-FEASIBILITY SOURCE AUDIT. NO REAL EXECUTION IS
> AUTHORIZED AND E0 DOES NOT BEGIN.** Accepted
> [Decision 070](Decisions/decision_070_m3_3_i_r_implementation_authorization.md) issued the bounded
> M3.3-I/R authority; accepted Decisions
> [071](Decisions/decision_071_m3_3_i_r_methodology_gap_adjudication.md),
> [072](Decisions/decision_072_m3_3_full_index_multi_registrant_source_correction.md),
> [073](Decisions/decision_073_m3_3_rehearsal_snapshot_bifurcation_and_amendment_purpose_blocker.md),
> and [074](Decisions/decision_074_m3_3_e5_reserve_rehearsal_and_real_linkage_gate.md) govern that same
> stage. **The M3.3A execution rehearsal E1–E8 has been run and passes**, the **R28** bridge is
> clean, and the mutation campaign M1–M38 is fully killed. The independent read-only ultrareview
> of the frozen executable target `6f87abc…` returned BLOCKER 0 / MAJOR 0 / MINOR 3; accepted
> [Decision 075](Decisions/decision_075_m3_3_i_r_ultrareview_bounded_correction.md) authorized and
> applied that bounded correction; **the corrected-target rereview is COMPLETE and MIN-A is
> CLOSED.** Accepted
> [Decision 076](Decisions/decision_076_m3_3_preacceptance_infrastructure_optimization.md) then completed
> the test, governance, and audit infrastructure and returned RET-1, **now CLOSED**. The **first**
> formal Fable 5 Maximum acceptance review returned **BLOCKER 0 / MAJOR 0 / MINOR 2**, which is
> **not an acceptance**; accepted
> [Decision 077](Decisions/decision_077_m3_3_i_r_fable_acceptance_findings_correction.md) authorized and
> applied that bounded correction. **The fresh Fable 5 Maximum formal M3.3-I/R acceptance review
> then ran and PASSED at BLOCKER 0 / MAJOR 0 / MINOR 0 / OPTIMIZATION 0 / OBSERVATION 1** —
> immutable artifact
> [`m3_3_i_r_formal_independent_acceptance_feaeaa4.md`](m3/reviews/m3_3_i_r_formal_independent_acceptance_feaeaa4.md),
> evidence commit `8c43edd…` — and **accepted
> [Decision 078](Decisions/decision_078_m3_3_i_r_owner_acceptance_and_real_feasibility_audit.md) records
> Sol/GPT's formal owner acceptance: M3.3-I/R is COMPLETE and OWNER-ACCEPTED at accepted executable
> target `feaeaa4…` (tree `3d33454a…`).** **The next act is the Decision-078 pre-E0 read-only,
> zero-network real-feasibility source audit of the already-accepted M3.2 material — NOT E0**, and
> a further Opus ultrareview is neither authorized nor required. Every
> statement below that says M3.3 has not begun, that its implementation is unauthorized, that the
> next act is a separate M3.3-I/R packet or a fresh Fable acceptance review, that the E1–E8
> rehearsal has not been run, or that the corrected target is pending a fresh read-only rereview
> is **historical**. **Still true and
> unchanged:** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 each remain a separate owner gate and **none is
> authorized**; the census parse layer is untouched; network, SEC, reacquisition, and
> private-evidence authority remain NONE; migration remains none; **two real-path feasibility gates
> are OPEN** — `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
> `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — which are never merged into one flag; and
> real acceptance-ordering adequacy remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.


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
S4/S5 module are **reused or regressed, never edited under Milestone 2**.

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

## Decision 027 v0.2 — Milestone 3 planning corrections (planning only, zero impact)

[Decision 027](Decisions/decision_027_m3_master_plan_and_operational_readiness.md) was revised in
place to **v0.2** on 2026-07-31, applying eleven bounded owner corrections issued after the required
independent review of v0.1. **The record has been `ACCEPTED` since v0.1; v0.2 does not change that**,
and creates no second numbered decision. Formal outcome unchanged:
`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`.

**It is planning and navigation only, and its impact set is empty.** The correction session changed
exactly these files:

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md` | in-place revision to v0.2 — new §0 revision history; corrected §§5, 6, 8, 10, 15, 16, 22, 23, 24, 25 | Markdown link-check only |
| `Milestones/milestone_03_master_plan.md` | corrected phase map and subdivisions; withdrawn counts and `A_max`; two-layer evidence model; corrected root re-derivation | Markdown link-check only |
| `Docs/m3/offline_rehearsal_spec.md` | **restructured** — twenty `R` scenarios become **A1–A12** (M3.1A acquisition) and **E1–E8** (M3.3A execution) | Markdown link-check only |
| `Docs/m3/execution_receipt_spec.md` | single integrity identity; per-mode field classification; zero actual network counts outside `live`; private storage | Markdown link-check; prohibited-field scan |
| `Docs/m3/operator_runbook.md` | two-layer evidence section; step 18a between-windows freeze/derive/approve; corrected budget and approval wording | Markdown link-check; command-status label check |
| `Docs/m3/limitations_register.md` | **M3-L10** rewritten; **M3-L11** and **M3-L12** added | Markdown link-check only |
| `Docs/m3/templates/evidence_index.md` | **new** — the public index of private evidence artifacts | Markdown link-check only |
| `Docs/m3/templates/request_budget.md` | per-window; `A_reachable` derivation; contingency removed | Markdown link-check only |
| `Docs/m3/templates/gate_f_checklist.md` | A1–A12; `A_reachable`; §12 planner-discrepancy gate | Markdown link-check only |
| `Docs/m3/templates/gate_h_checklist.md` | per-window reconciliation; §2.1 between-windows freeze and derivation | Markdown link-check only |
| `Docs/m3/templates/schema_drift_incident.md` | window scoping | Markdown link-check only |
| `Docs/m3/templates/interrupted_run_recovery.md` | window scoping; ceiling never raised mid-window | Markdown link-check only |
| `Docs/m3/templates/real_snapshot_evidence_packet.md` | M3.3A/M3.3B split; deterministic re-derivation | Markdown link-check only |
| `Docs/m3/templates/root_hash_approval_packet.md` | deterministic re-derivation; M3.4A entry point; manual SQL prohibited | Markdown link-check only |
| `Docs/Decisions/decision_registry.md` | row `027` marked v0.2 with the correction summary; controlling-record row updated | Markdown link-check; table-structure check |
| `Docs/decision_index.md` | Decision 027 v0.2 section and the corrected topic table | Markdown link-check only |
| `Docs/architecture_map.md` | §0 Milestone 3 row and planning-artifact layer; the determinism and planner-discrepancy notes | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | current-state ledger and machine-readable markers | `make context` resolves the markers |
| `Milestones/contracts/README.md` | v0.2 correction summary; next-action pointer | Markdown link-check only |
| `README.md` | the live `**Status:**` block's Milestone 3 sentence | Markdown link-check only |

**Zero impact, stated explicitly:**

- **zero production impact** — no module under `src/` changed;
- **zero test impact** — no file under `tests/` changed;
- **zero migration impact** — migrations `0001`–`0013` byte-identical, chain contiguous with nothing
  beyond `0013`, and `0013`'s normative region still 10939 bytes over 186 lines at
  `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595`;
- **zero configuration impact** — `configs/`, `pyproject.toml`, `Makefile`, `.github/`, **and
  `.gitignore`** unchanged. The private-evidence-root ignore entry is deliberately **not** made here
  and is carried as limitations-register entry **M3-L11**;
- **zero CLI impact** — every Milestone 3 command remains `PLANNED — NOT YET IMPLEMENTED`;
- **zero methodology impact** — no hypothesis, cohort window, maturity gate, outcome definition,
  threshold, seed, selection rule, reserve rule, or manifest rule changed. **`Docs/Decisions/decision_013_pilot_selection_mechanics.md`
  is byte-unchanged**, and the planner discrepancy is recorded rather than resolved;
- **zero identity impact** — no hash preimage, digest, `manifest_id`, run identity, canonicalization
  rule, crosswalk row, or classification total changed;
- **zero data impact**, **zero network impact**, **zero publication impact**;
- **no tag** — none created, moved, or deleted;
- **next action `INDEPENDENT_M3_MASTER_PLAN_REREVIEW`**;
- **no Milestone 3 implementation authority** and, at the Decision 028 correction checkpoint, no
  contract created and no M3.1 contract drafted.

**What the corrections withdrew, and why it matters to a future reader.** The v0.1 derived request
counts, subtotal, plan hash, `A_max = 12`, `planned × 12`, and the 10% contingency **no longer appear
as accepted values anywhere in the planning pack.** Two were wrong in different ways: the counts were
faithful to the accepted planner but **not** to Decision 013 §1, and `A_max` was inferred by reading
three guards rather than derived from and tested against the implemented state machine. **Neither
class of value may be reintroduced without deriving it and testing it.**

## Accepted Decision 028 and the M3.1 contract draft (zero runtime impact)

[Decision 028](Decisions/decision_028_m3_1_readiness_corrections.md) is
`ACCEPTED — OWNER APPROVED 2026-08-01` after `INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`. It responds
to the independent Decision 027 v0.2 rereview outcome `NEEDS_CORRECTION`, is binding for its bounded
owner rulings, and authorizes no implementation or network access. The exact-path
[`Milestones/contracts/m3_1.md`](../Milestones/contracts/m3_1.md) now exists as
`DRAFT_PENDING_INDEPENDENT_REVIEW` with implementation authorization `NO`.

The proposed correction package changes exactly these documentation paths:

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_028_m3_1_readiness_corrections.md` | accepted decision status and completed review/checkpoint sequence | Markdown link-check; registry consistency |
| `Docs/Decisions/decision_registry.md` | accepted Decision 028 registry and topic rows | Markdown link-check; mechanical table-structure check |
| `Docs/decision_index.md` | accepted Decision 028 topic index and M3.1 state | Markdown link-check only |
| `Docs/architecture_map.md` | Milestone 3 state, receipt-v2, M3-L11, and M3-L12 navigation | Markdown link-check only |
| `Docs/change_impact_map.md` | this exact-path and zero-impact record | Markdown link-check only |
| `Docs/m3/execution_receipt_spec.md` | pre-first-receipt v2 field timing and validation | Markdown link-check; prohibited-field scan |
| `Docs/m3/limitations_register.md` | M3-L09 v2; M3-L11 and M3-L12 owner rulings recorded, both still active | Markdown link-check only |
| `Docs/m3/offline_rehearsal_spec.md` | corrected A1–A12 expectations | Markdown link-check; scenario-matrix check |
| `Docs/m3/operator_runbook.md` | planner-v2, evidence-root, receipt-v2, budget, ceiling, and recovery wording | Markdown link-check; command-status label check |
| `Docs/m3/templates/gate_f_checklist.md` | planner-v2, receipt-v2, budget, ceiling, and M3-L11 entry gates | Markdown link-check only |
| `Docs/m3/templates/gate_h_checklist.md` | ceiling equality plus complete-plan requirement | Markdown link-check only |
| `Docs/m3/templates/interrupted_run_recovery.md` | read-only inspection, separate repair, and cumulative-ceiling rules | Markdown link-check only |
| `Docs/m3/templates/request_budget.md` | no double-subtracted cache hits; maximum objects; spacing floor | Markdown link-check only |
| `Milestones/STATUS.md` | accepted Decision 028 and draft-contract state | `make context` marker check |
| `Milestones/contracts/README.md` | contract index and draft-review gate | Markdown link-check only |
| `Milestones/contracts/m3_1.md` | exact-path bounded contract draft; implementation authorization `NO` | fresh independent contract review; all master-plan §16 fields |
| `Milestones/milestone_03_master_plan.md` | corrected M3.1 scope, formulas, receipt v2, scenarios, and progression gates | five-phases × 36-fields check; Markdown link-check |
| `README.md` | live Milestone 3 status | Markdown link-check only |

Zero impact is explicit:

- no production module, test, migration, configuration, CI workflow, or `.gitignore` byte changes;
- Decision 013 and Decision 024 remain byte-unchanged and controlling;
- no historical v1 plan or hash is rewritten and no receipt migration exists because no receipt has
  yet been produced;
- no hypothesis, cohort window, cutoff, seed, selection rule, reserve rule, hash preimage,
  canonicalization rule, accepted S5/S6 identity, or publication boundary changes;
- no data is read, written, acquired, or derived; no transport is constructed and no SEC request is
  placed;
- the M3.1 contract is drafted but unaccepted, no Milestone 3 implementation is authorized, and no
  Gate F or Gate H passes; and
- no commit, push, or tag occurs unless the rereview passes and a later acceptance/checkpoint step
  separately authorizes it.

`INDEPENDENT_M3_1_CONTRACT_REVIEW` is discharged — the contract is accepted with
`IMPLEMENTATION_AUTHORIZATION: YES`, and the M3.1 implementation exists in the tree without being
accepted. The Decision 029 §11 code remediation is implemented and the disposable-clone validation
run on the corrected tree is complete; the next action is a frozen commit and the **first durable §17
review** by a session that wrote none of the M3.1 work, which reproduces and records that validation.
No durable review artifact exists today and none covers the current tree; a fix commit never converts
a prior `FAIL` into a `PASS`.

## Milestone 3.2 stage T2 impact paths (accepted stages T2.1, T2.2–T2.3, and T2.4)

Added under [Decision 043](Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md)
§7. **This section is navigation, not authority, and it authorizes no edit.** Every path below sits
inside a stage whose grant is exhausted; changing any of them needs its own owner authorization and
its own stage envelope. What a stage was allowed to touch is stated by its authorizing decision
(035 for T2.1; 035 as amended by [038](Decisions/decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md)
for T2.2–T2.3; [040](Decisions/decision_040_m3_2_t2_4_implementation_authorization.md) as amended by
[041](Decisions/decision_041_m3_2_t2_4_recovery_state_primitive_authority.md) for T2.4), never by
this map.

Two constraints hold across the whole stage family and should be read before planning any change to
it. **The migration chain is fixed at `0001`–`0013`** — Decisions 040 and 041 both record
`NO_NEW_MIGRATION_REQUIRED`, so a change here that appears to need a migration is a stop condition,
not a migration. **The execution receipt was frozen at `m3-execution-receipt/2.0` for the T2 stages**
(`NO_RECEIPT_SCHEMA_CHANGE_REQUIRED`), and receipt assembly and operator wiring belonged to the
then-unauthorized combined stage T2.5–T2.6, so no accepted **T2** stage emits a receipt. Both
statements are historical now: T2.5–T2.6 was authorized by Decision 045 and accepted by Decision
046, and Decision 055 §7 moved the writer to `m3-execution-receipt/3.0` with readers accepting `2.0`
and `3.0`. Plan a receipt change against the current version, not against the T2 freeze.

| Path | Stage that delivered it | Nearest tests | Principal validation / gate surface | Architectural role |
|---|---|---|---|---|
| `configs/project.yaml` (`network.m3_acquire_enabled`), `src/disclosure_drift/config.py` | T2.1 (Decision 036) | `tests/unit/test_config.py` | ruff, ruff format, mypy; `make validate`; **both tracked switches must stay `false`** and `make context` now reports them | The command-scoped acquisition switch, independent of `network.enabled` in both directions, under strict unknown-field rejection with no environment fallback |
| `src/disclosure_drift/cli.py` (the M3.2 command surfaces) | T2.1 (Decision 036), extended since | `tests/integration/test_m3_cli.py` | ruff, ruff format, mypy; `tests/integration/test_no_network.py` for the standing no-network boundary | Parser and dispatch for `m3 acquire`, `recover`, `reconcile-requests`, `show-drift`, `show-budget`, `derive-dependent-plan`, `recovery-state`, and `show-receipt` — every one fail-closed at exit 3, with no transport constructible from this layer. `reconcile-requests` carries the paired plan-transition flags and `recover` carries `--check-only` (Decision 064 §§5, 7) |
| `src/disclosure_drift/m3/acquisition.py` | T2.2–T2.3 (Decision 039), extended by T2.4 (Decision 042) | `tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_recover.py`; `tests/integration/test_m3_cli.py` | ruff, ruff format, mypy; full suite before handoff — this is the largest single production surface in M3.2 | Driver-side integration only. Catalog preparation and containment, immutable storage binding, logical-request derivation, the injected-transport acquisition engine, plus the T2.4 catalog-authoritative reconstruction, deterministic reconciliation and drift listing, continuation proposal, and the explicit recovery-action library (no CLI exposure) |
| `src/disclosure_drift/sec/observation_catalog.py` | T2.2–T2.3 (Decision 038/039) and T2.4 (Decision 041) | `tests/unit/test_observation_catalog.py`, `tests/unit/test_observation_lineage.py` | ruff, ruff format, mypy; **yes — SQLite/migration integrity gate**: `test_migration_provenance.py` and `make sqlite-check` | Durable observation persistence and reconciliation. T2.2–T2.3 widened `ObservationRecorder.record`'s members boundary to a single-pass iterable; T2.4 added exactly the two recovery-state primitives `open_recovery_state` and `resolve_recovery_state`. Every other accepted semantic is unchanged |
| `src/disclosure_drift/reasons.py` | T2.4 (Decision 040) | `tests/unit/test_reasons.py` (plus the registry's existing coverage in the main table above) | ruff, ruff format, mypy; **yes** — reason codes are FK targets of `reference_reason_codes`: `test_migration_provenance.py` and `make sqlite-check` | Exactly one registered code added, `SOURCE_REQUIRED_OBJECT_UNAVAILABLE`. A condition with no registered code is a stop condition under T2, never a code invented in the stage |
| `src/disclosure_drift/m3/__init__.py` | T2.1, T2.2–T2.3, and T2.4 | covered through the tests of what it re-exports | ruff, ruff format, mypy | Public export surface for the M3 package. It adds no behaviour; a name appearing here is the accepted way to reach it |

**Accepted M3 surfaces that T2 governs but has not modified.** Each is consumed unchanged by
`acquisition.py`, which is exactly why it stays a prohibited path — a change here is not a T2 change
and needs its own authorization.

| Path | Nearest tests | Why it is listed |
|---|---|---|
| `src/disclosure_drift/m3/recovery.py` | `tests/unit/test_m3_recovery.py`, `tests/unit/test_m3_recover.py` | The **read-only** recovery inspector (M3.1). It was inside the Decision 041 ten-path T2.4 maximum and was deliberately left unedited, which the maximum-not-requirement rule permits. **Decision 062** then edited it (condition 8.2's terminal-establishment predicate; the frozen plan-transition bindings), **Decision 063** the cross-namespace chain walk, and **Decision 064** condition 8.12's root-versus-head semantics, the successful-terminal 8.2 path, the identity-level 8.8 remainder, and the continuation-permission report. Still read-only — it imports no writer, imports no `RawStore`, and opens the catalog `query_only` |
| `src/disclosure_drift/m3/request_plan.py` | `tests/unit/test_m3_request_plan.py` | The deterministic zero-request plan. **Two** accepted hashes are now bound to it — the original `19be7bdc…` and the Decision 062 successor `f77e003c…` — along with the owner-approved ceiling **801**; any change must reproduce all of them |
| `src/disclosure_drift/m3/receipt.py` | `tests/unit/test_m3_receipt.py` | Frozen at `m3-execution-receipt/2.0` for all of T2; the current writer is `3.0` with readers accepting both (Decision 055 §7). It also owns predecessor-receipt resolution — by recorded identity, across the accepted receipt locations (Decisions 063 and 064 §8) |
| `src/disclosure_drift/sec/request_ceiling.py` | `tests/unit/test_request_ceiling.py` | The cumulative physical-attempt gate the engine consumes. Ceiling semantics are outside G1 and outside every accepted T2 stage |
| `src/disclosure_drift/m3/rehearsal.py`, `src/disclosure_drift/m3/evidence_paths.py` | `tests/unit/test_m3_rehearsal.py`, `tests/unit/test_m3_evidence_paths.py` | Accepted M3.1 surfaces (A1–A12 rehearsal; the evidence-root boundary). No T2 stage touches either |

**Declined and prohibited for the whole of T2:** `src/disclosure_drift/sec/census_orchestrator.py`
and `src/disclosure_drift/sec/index_retrieval.py`. The accepted T2 packet declined both, and no
later decision has released either — their rows earlier in this map describe them as Milestone 2
surfaces, which is the only capacity in which they may be changed.

**What no accepted T2 stage has produced:** no real operational catalog, no raw object, no receipt,
no evidence artifact, no request, no attempt, no SEC contact. **T2 built the surfaces; it never ran
them.** That statement is scoped to the implementation stages and stays true.

**Current state, which the T2-stage statement above does not describe.** The later authorized live
windows did run: M3.2A acquisition is complete at **75 of 75** successor request identities and
**77 of 801** cumulative physical attempts, real objects and receipts exist as **private** evidence
outside the repository, **Gate H is passed and owner-accepted**, and Milestone 3.2 is complete and
owner-accepted (accepted
[Decision 065](Decisions/decision_065_m3_2_final_acceptance_and_closeout.md), 2026-08-13). Both
tracked network switches remain `false`, and **no further SEC acquisition or network authority
exists**. **A validation run that appears to need a network switch, a real catalog, a real raw
object, an SEC contact, or any private evidence is still a stop condition** — tests use temporary
paths and fixtures only.

## Decision 067 — M3.3 snapshot authority and the offline parse prerequisite (governance only, zero impact)

[Decision 067](Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md)
(`ACCEPTED — OWNER M3.3 GOVERNANCE RULINGS 2026-08-13`) resolves **OR-1** and **OR-2**, issues
**R13**–**R16**, records the OQ-3/OQ-4/OQ-6/OQ-8 dispositions, corrects the M3.3-GR proposal at
**GR-C1** and **GR-C2**, and fixes the **M3.3-E0** real-offline-parse boundary.

**Its impact set is empty.** It changed **no** executable source, test, migration, configuration, or
CI file, read and mutated **no** private evidence, and made no request. It is a **governance
authority record and is not implementation authorization**; the M3.3 contract is **corrected and not
accepted**.

| Path | Kind | Gates it triggers |
|---|---|---|
| `Docs/Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md` | **new** — the record itself | Markdown link-check only |
| `Milestones/contracts/m3_3.md` | corrected — §1.1 gains R13–R16; §8.1 and §10.1 carry the resolved OR-2 and OR-1; new §10.2 fixes the offline parse and the M3.3-E0 gate; §§2, 4, 6, 7, 9, 19, 20, 21, 23, 26, 29–34, 36 synchronized | Markdown link-check only |
| `Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md` | owner-disposition banner and inline GR-C1/GR-C2 annotations; **body preserved as historical proposal evidence** | Markdown link-check only |
| `Docs/m3/m3_3_governance_foundation_inventory.md` | §§B, F, G, H updated for the dispositions | Markdown link-check only |
| `Docs/m3/limitations_register.md` | **D067-L1** added (Group 8); **D021-L2** annotated and left `ACTIVE`; register summary recount | Markdown link-check only |
| `Docs/m3/operator_runbook.md` | new step **28a** (M3.3-E0); §29 gains the E0 prerequisite; banner and Appendix B updated | Markdown link-check; command-status label check |
| `Docs/Decisions/decision_registry.md` | row `067`; new controlling-record row | Markdown link-check; table-structure check |
| `Docs/decision_index.md` | new M3.3 topic section | Markdown link-check only |
| `Docs/architecture_map.md` | §0 Milestone 3 row; §2 current-state note; §4 candidate-snapshot status and prerequisite | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |
| `Milestones/STATUS.md` | Decision 067 markers and the new `NEXT_AUTHORIZED_ACTION` | Markdown link-check; marker-format check |
| `Milestones/milestone_03_master_plan.md` | M3.3 §§2, 5, 6 synchronized with R13 and the E0 gate | Markdown link-check only |
| `Milestones/contracts/README.md` | `m3_3.md` index entry; corrected next-action pointer | Markdown link-check only |

**Which tests to run for it: none of the code suites.** No module changed, so no module's direct or
integration tests are implicated. **Documentation-only changes never justify a full `pytest` run**,
and this map does not turn a governance record into a test trigger.

**What it implies for future work, and does not yet trigger.** When M3.3-I/R is separately
authorized, the new **candidate-snapshot builder** and **offline metadata parse driver** arrive with
their own test modules, and the impact set is the one the corrected contract §§26–27 names — the
`pilot_manifest`, `pilot_schema`, accession- and entity-selector, reserve, migration-provenance, and
`test_m3_cli` / `test_no_network` suites, plus the new modules' own tests. **Neither module exists
today, and neither is authorized.**

## Decision 068 — M3.3 E0 write-set and contract-consistency correction (governance only, zero impact)

[Decision 068](Decisions/decision_068_m3_3_e0_contract_correction.md)
(`ACCEPTED — OWNER BOUNDED CONTRACT CORRECTION 2026-08-13`) adopts the failed fresh independent
review's findings (verdict `M3_3_CORRECTED_CONTRACT_FRESH_INDEPENDENT_REVIEW_FAILED`, B0/M1/MIN1 —
artifact `Docs/m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md`, immutable), issues
**R17** (the exact fifteen-table E0 persistence footprint, mechanically verified against
`sec/census.py`) and **R18** (report-level per-planned-source E0 dispositions), clarifies
**R16-C1** (resolution contributor membership), and applies the MIN-1 and OBS-A–E consistency
fixes. **It changes no executable source, test, migration, configuration, or CI byte**, authorizes
nothing, and — as at that record — the contract remained **not accepted**, pending a fresh
independent rereview (since run and passed; see the Decision 069 section below).

| Surface touched | Change | Checks |
|---|---|---|
| `Docs/Decisions/decision_068_m3_3_e0_contract_correction.md` | **new** — the record itself | Markdown link-check only |
| `Milestones/contracts/m3_3.md` | corrected — §1.1 gains R17/R18/R16-C1 and the MIN-1 §10.1 pointer fix; §10.2 items 2, 6, 12 corrected and item 14 added; §19, §21, §26 items 2–3, §29, §30, §36 synchronized; gate names M3.3-E0/E1/E2 disambiguated from rehearsal-scenario labels | Markdown link-check only |
| `Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md` | OBS-E erratum note in §B.2; **body preserved as historical proposal evidence** | Markdown link-check only |
| `Docs/m3/m3_3_governance_foundation_inventory.md` | current-state banner and §G dispositions updated | Markdown link-check only |
| `Docs/m3/operator_runbook.md` | §28a gains the R17 write-footprint and R18 disposition statements | Markdown link-check; command-status label check |
| `Docs/Decisions/decision_registry.md` | row `068`; controlling-record row updated | Markdown link-check; table-structure check |
| `Docs/decision_index.md` | M3.3 topic section updated for R17/R18/R16-C1 | Markdown link-check only |
| `Docs/architecture_map.md` | §0 Milestone 3 row's next-act clause updated | Markdown link-check only |
| `Milestones/STATUS.md` | Decision 068 markers and the new `NEXT_AUTHORIZED_ACTION` | Markdown link-check; marker-format check |
| `Milestones/milestone_03_master_plan.md` | M3.3 §5 item 1 status, §9 driver category (OBS-D), §26 R17/R18 synchronization | Markdown link-check only |
| `Milestones/contracts/README.md` | `m3_3.md` index entry and next-action pointer | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |

**Which tests to run for it: none of the code suites** — documentation-only, same rule as the
Decision 067 section above. The review artifact itself is **not modified** by this or any later
correction.

## Decision 069 — M3.3 corrected-contract final owner acceptance (governance only, zero impact)

[Decision 069](Decisions/decision_069_m3_3_contract_final_owner_acceptance.md)
(`ACCEPTED — OWNER FINAL M3.3 CONTRACT ACCEPTANCE 2026-08-13`) records the owner's acceptance of
the fresh independent rereview (`M3_3_DECISIONS_067_068_CORRECTED_CONTRACT_FRESH_REREVIEW_B0_M0_MIN0_PASS`,
frozen target `7bb36b8…`, immutable artifact
`Docs/m3/reviews/m3_3_decisions_067_068_corrected_contract_fresh_rereview_7bb36b8.md`, committed
`033d0d9…`) and of the corrected M3.3 contract (`M3_3_CORRECTED_CONTRACT_FINAL_OWNER_ACCEPTED`),
and disposes rereview observation **OBS-R1** as a **nonblocking historical narrative erratum** on
Decision 068 §3.1 — without editing Decision 068. `ACTIVE_STAGE_CONTRACT` transitions to the
accepted `Milestones/contracts/m3_3.md`; **activation is navigation, not authorization**. **It
changes no executable source, test, migration, configuration, or CI byte** and authorizes nothing:
no M3.3-I/R, no E0/E1/E2, no network, no reacquisition, no migration, no M3.4. The next act is a
**separate owner M3.3-I/R implementation + rehearsal authorization packet**.

| Surface touched | Change | Checks |
|---|---|---|
| `Docs/Decisions/decision_069_m3_3_contract_final_owner_acceptance.md` | **new** — the record itself | Markdown link-check only |
| `Milestones/contracts/m3_3.md` | status transition to `ACCEPTED — OWNER FINAL CONTRACT ACCEPTANCE — DECISION 069` (`CONTRACT_ACCEPTANCE: YES`; frozen accepted target and rereview result recorded; §1, §21, §36 synchronized; **every executable-authority flag kept closed**) | Markdown link-check only |
| `Milestones/STATUS.md` | banner acceptance paragraph; `ACTIVE_STAGE_CONTRACT` → `m3_3.md`; Decision 069 markers; new `NEXT_AUTHORIZED_ACTION` | Markdown link-check; marker-format check |
| `Milestones/contracts/README.md` | index update paragraph and `m3_3.md` entry — accepted / active / blocker | Markdown link-check only |
| `Milestones/milestone_03_master_plan.md` | M3.3 §5 item 1 status | Markdown link-check only |
| `Docs/Decisions/decision_registry.md` | row `069`; rows 067/068 `Superseded by` amended narrowly; controlling-record row added | Markdown link-check; table-structure check |
| `Docs/decision_index.md` | M3.3 section — Decision 069 paragraph and acceptance/erratum Q&A rows | Markdown link-check only |
| `Docs/architecture_map.md` | §0 Milestone 3 row and §4 candidate-family `Status` bullet — acceptance state | Markdown link-check only |
| `Docs/m3/operator_runbook.md` | banner M3.3 row — accepted contract, next act | Markdown link-check only |
| `Docs/m3/limitations_register.md` | 2026-08-13 nothing-closed note extended through Decision 069 | Markdown link-check only |
| `Docs/m3/m3_3_governance_foundation_inventory.md` | fourth current-state banner update | Markdown link-check only |
| `Docs/change_impact_map.md` | this section | Markdown link-check only |

**Which tests to run for it: none of the code suites** — documentation-only, same rule as the
Decision 067 and 068 sections above. Decisions 067 and 068, both review artifacts, and the GR
proposal are **not modified**.

## Decision 087 — the verified document-evidence schema and migration `0015` (real impact)

[Decision 087](Decisions/decision_087_m3_3_r46_owner_acceptance_and_verified_evidence_schema.md)
(`ACCEPTED — OWNER FINAL R46 ACCEPTANCE AND VERIFIED-EVIDENCE SCHEMA IMPLEMENTATION AUTHORIZATION
2026-08-15`) records the final owner acceptance of the corrected **R46** implementation and lifts the
implementation deferral on the Decision 082 §11 verified-evidence schema contract. Unlike the
governance-only sections above, **this one has real impact**: it adds migration `0015`, four new
relations, and the narrow policy module they need.

**What it does not touch.** No research definition, quota, selector, cohort, or seed. No
candidate-selection methodology, offline parse, reserve selector, or manifest construction. No
network, acquisition, or transport module. `cohorts.py`, `pilot_policy.py`, `candidate_identity.py`,
and migrations `0001`–`0014` are byte-unchanged.

| Surface touched | Change | Checks |
|---|---|---|
| `src/disclosure_drift/storage/migrations/0015_m33_verified_document_evidence.sql` | **new** — the four relations, twenty-three triggers, and the two-constraint evidence-level widening (corrected under accepted Decision 088 for M-1, MIN-1, MIN-2, MIN-3, OBS-2, and OBS-3) | `tests/unit/test_m3_3_verified_document_evidence.py`, `test_migration_provenance.py`, `test_storage_catalog.py`, `test_m23_pilot_schema.py` |
| `src/disclosure_drift/m3/document_evidence.py` | **new** — frozen vocabularies, the verified-applicability gate, the private-path validator, and the new hash domains | `tests/unit/test_m3_3_verified_document_evidence.py` |
| `src/disclosure_drift/m3/acquisition.py` | `FINAL_MIGRATION_VERSION` **14 → 15**, that constant and nothing else (accepted Decision 084 **R65** interpretation) | `tests/unit/test_m3_acquisition.py`, `test_m3_3_multi_registrant_correction.py` |
| `tests/unit/test_m3_3_verified_document_evidence.py` | **new** — VE-M1…VE-M14 plus the migration-safety and identity-nonchange proofs | itself |
| `tests/unit/test_migration_provenance.py`, `test_storage_catalog.py`, `test_m23_pilot_schema.py`, `test_m3_3_multi_registrant_correction.py` | chain-head expectations `0014` → `0015` | themselves |
| `tests/unit/test_m23_pilot_manifest_store.py` | the **R68** migration-chain re-baseline: `selector_policy_sha256`, `root_manifest_sha256`, `manifest_id`, and the canonical-JSON length | `tests/unit/test_m23_pilot_manifest_store.py` |
| `Docs/sec_data_dictionary.md` | new §15 and the coverage table | Markdown link-check only |
| `Docs/architecture_map.md`, `Docs/decision_index.md`, `Docs/Decisions/decision_registry.md`, `Milestones/STATUS.md`, `Docs/change_impact_map.md` | navigation and current state | Markdown link-check only |

**Which tests to run for it.** Direct: `tests/unit/test_m3_3_verified_document_evidence.py`.
Chain-head neighbours: `test_migration_provenance.py`, `test_storage_catalog.py`,
`test_m23_pilot_schema.py`, `test_m3_3_multi_registrant_correction.py`, `test_m3_acquisition.py`.
Identity neighbours: `test_m23_pilot_manifest_store.py`, `test_m23_pilot_manifest.py`,
`test_m3_candidate_identity.py`. Rehearsal, because the migration chain binds the manifest:
`test_m3_3_execution.py` (**E1**–**E8**).

**Expected identity movement, and its exact bound.** Migration `0015` adds one
`ops_schema_migrations` row, so the accepted Decision 086 §3 (**R68**) path moves three digests and
one document length in the reserve-bearing fixture — `selector_policy_sha256`,
`root_manifest_sha256`, `manifest_id`, and the canonical-JSON length. **Nothing else moves**, and in
particular `candidate_tables_sha256` and `selection_result_sha256` are byte-identical. That movement
is caused **solely by the migration chain**; **no verified evidence content exists anywhere**, which
is the distinction Decision 087 §9 requires to be stated rather than assumed.

## Decision 088 — the D087 review corrections (real impact)

[Decision 088](Decisions/decision_088_m3_3_d087_verified_evidence_review_corrections.md)
(`ACCEPTED — OWNER ADJUDICATION OF THE D087 INDEPENDENT REVIEW AND BOUNDED CORRECTION AUTHORIZATION
2026-08-15`) adjudicates the **failed** independent review of the Decision 087 implementation and
authorizes a bounded correction. Migration `0015` is corrected **in place**; **no migration `0016`**
is authorized, and **no new relation, column, or evidence dimension is added**.

**What it does not touch.** No research definition, quota, selector, cohort, or seed. No
candidate-selection methodology, offline parse, reserve selector, or manifest construction. No
network, acquisition, or transport module. `cohorts.py`, `pilot_policy.py`, `candidate_identity.py`,
`candidate_snapshot.py`, `release/hashing.py`, `acquisition.py`, `src/disclosure_drift/m3/document_evidence.py`,
and migrations `0001`–`0014` are **byte-unchanged**.

| Surface touched | Change | Checks |
|---|---|---|
| `src/disclosure_drift/storage/migrations/0015_m33_verified_document_evidence.sql` | **corrected in place** — four `BEFORE INSERT` replacement guards (M-1); two registered-accession binding triggers (MIN-1); the `agreed`-consistency trigger (MIN-2); `accession_plain` added to the verified-candidate `UPDATE OF` list (MIN-3); the §1 precondition comment (OBS-2); strict decimal `span_location` (OBS-3) | `tests/unit/test_m3_3_verified_document_evidence.py`, `test_migration_provenance.py`, `test_storage_catalog.py`, `test_m23_pilot_schema.py` |
| `tests/unit/test_m3_3_verified_document_evidence.py` | **VE-R1…VE-R10** added; four VE-M assertions repaired where the new guards changed which refusal arrives first; OBS-1 pinned as **open** | itself |
| `tests/unit/test_m23_pilot_manifest_store.py` | the **R68** policy-chain re-baseline: `selector_policy_sha256`, `root_manifest_sha256`, `manifest_id` | itself |
| `Docs/sec_data_dictionary.md`, `Docs/architecture_map.md`, `Docs/change_impact_map.md`, `Docs/decision_index.md`, `Docs/Decisions/decision_registry.md`, `Milestones/STATUS.md` | truthful current state, including OBS-1's open status | Markdown link-check only |

**Which tests to run for it.** Exactly the Decision 087 set — the correction changes no module and
no interface, only the migration's guards. Direct:
`tests/unit/test_m3_3_verified_document_evidence.py`. Identity neighbour, because the migration bytes
move the policy chain: `test_m23_pilot_manifest_store.py`.

**Expected identity movement, and its exact bound.** Correcting `0015` changes its
`checksum_sha256` (`c5328894…` → `d7f22999…`), so the accepted **R68** path moves
`selector_policy_sha256`, `root_manifest_sha256`, and `manifest_id`. **The canonical-JSON length does
NOT move** — it stays `275721`, because this re-baseline changes an existing block-5 row's value
rather than adding a row. The eight components Decision 088 §11 names — including
`candidate_tables_sha256` and `selection_result_sha256` — are **byte-identical**, and no frozen
identity tuple is widened.

## Decisions 094–099 — the PRE-E0 executability implementation (real impact)

[Decision 094](Decisions/decision_094_m3_3_pre_e0_executability_redesign.md)
(`ACCEPTED — OWNER PRE-E0 REDESIGN AUTHORITY 2026-08-15`), as corrected by
[Decision 095](Decisions/decision_095_m3_3_d094_bounded_correction_and_remediation.md) **R79–R81**,
[Decision 096](Decisions/decision_096_m3_3_final_pre_e0_rehearsal_correction_and_remediation.md)
**R83–R84**,
[Decision 097](Decisions/decision_097_m3_3_m19_live_anchor_supersession_correction.md) **R87–R89**,
and [Decision 099](Decisions/decision_099_m3_3_post_d098_bounded_correction.md) **R96–R98**,
restores a genuinely executable M3.3-E0 path. It implements two operator state
machines, **both of whose `execute` modes are disabled**, and it runs neither.

**What it does not touch.** No research definition, cohort, quota, seed, or selector. No migration —
`0001`–`0015` are byte-unchanged and `0016` does not exist. No `reasons.py`, `release/hashing.py`,
`paths.py`, `cohorts.py`, `pilot_policy.py`, acquisition, census orchestrator, transport, HTTP,
rate-limit, or network-configuration path. No accepted private evidence is read, resolved, named, or
opened, and both tracked network switches stay `false` at `REQUEST_CEILING = 0`.

| Surface touched | Change | Nearest tests |
|---|---|---|
| `src/disclosure_drift/m3/e0.py` | **new** — the two bounded state machines: preflight predicates, the `0013 -> 0014 -> 0015` transition, the E0 driver, the hash-chained ledger, both closed terminal schemas, identity/freeze, and `verify`. Both activation constants ship as `None`. **D099 R96–R98** add: failure terminals projected from the durable event ledger, §5.2 predicate 3's source-local M3.2 completion/catalog binding (`M3_2_COMPLETION_BINDING`), catalog-aware `verify`, the explicit `lease_check` policy, and predicate 10's full parent existence/ownership check | `tests/unit/test_m3_e0.py`; `tests/integration/test_m3_cli.py` |
| `src/disclosure_drift/m3/offline_parse.py` | the Decision 094 §§6.2–6.4 canonical association projection, the §9.5 totality object, the sixteen-table footprint, and the named `materialize_source_layer()` pre-projection boundary | `tests/unit/test_m3_offline_parse.py`, `tests/unit/test_m3_e0.py` |
| `src/disclosure_drift/m3/candidate_snapshot.py` | §6.5 consumer rule: the canonical relation plus persisted completeness is the **only** membership source. The observation-derived derivation, the scalar union, and the scalar-keyed entity history are removed | `tests/unit/test_m3_candidate_snapshot.py`, `tests/unit/test_m3_3_multi_registrant_correction.py` |
| `src/disclosure_drift/m3/receipt.py` | the isolated `m3-execution-receipt/4.0` reader/builder. `2.0`/`3.0` bytes, validators, vocabularies, and emitters are unchanged | `tests/unit/test_m3_receipt.py`, `tests/unit/test_m3_e0.py` |
| `src/disclosure_drift/m3/execution_rehearsal.py` | **R83 only** — the stale E2 non-canonical full-index CIK variant and its now-unused helper are removed. Every other E2 obligation and all eight scenarios remain | `tests/unit/test_m3_3_execution.py` |
| `src/disclosure_drift/m3/rehearsal_world.py` | **R79 only** — the two support-only co-registrants get accepted-shaped submissions objects with zero filings of their own | `tests/unit/test_m3_3_execution.py` |
| `src/disclosure_drift/config.py` | **R80 only** — `EVIDENCE_ROOT_ENV` is a recognized **runtime root**, never an override, secret, or tracked value | `tests/unit/test_env_overrides.py`, `tests/unit/test_config.py` |
| `src/disclosure_drift/cli.py` | the two `--config … --mode {preflight,execute,verify}` subcommands, routed before the shared evidence-root resolution because neither takes a path option | `tests/integration/test_m3_cli.py` |
| `scripts/dev/mutation_campaign.py` and `Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md` | **D097 R87–R89 only** — neither is edited; the M19 live anchor is recorded superseded. D097 left the audit proof at 38 recovered / 37 resolved / `['M19']` superseded; accepted [Decision 114](Decisions/decision_114_m3_3_m21_live_anchor_supersession.md) later disposed M21 as well, so the **current** live partition the proof asserts against the shipped tree is 38 recovered / 36 resolved / `['M19', 'M21']` superseded | `tests/unit/test_audit_tooling.py` |
| `Docs/m3/e0_execution_record_spec.md` | **new** — the executable record specification; **D099** adds §5a (predicate 3), the durable-event failure projection table, the predicate-10 parent rule, and what `verify` reads from the catalog | Markdown link and decision-reference gates |
| `Docs/m3/execution_receipt_spec.md`, `Docs/m3/operator_runbook.md`, `Docs/sec_data_dictionary.md` | §12.2 `4.0`; step 28a's implemented-and-disabled state, plus the **D099** operator-visible refusals; §16 for the canonical relation | Markdown link and decision-reference gates |

**Which tests to run for it.** Direct: `tests/unit/test_m3_e0.py`,
`tests/unit/test_m3_offline_parse.py`, `tests/unit/test_m3_candidate_snapshot.py`,
`tests/unit/test_m3_receipt.py`, `tests/unit/test_m3_3_execution.py`. Identity and schema
neighbours, because the association projection and the sixteen-table footprint move what a snapshot
is built from: `tests/unit/test_m3_3_multi_registrant_correction.py`,
`tests/unit/test_migration_provenance.py`. Campaign-audit truthfulness, because D097 R88's live
anchor partition is asserted against the shipped tree: `tests/unit/test_audit_tooling.py`. Receipt
mechanics, because D099 R97's predicate-3 binding reuses `inspect_receipt` and the Decision-063
predecessor resolver: `tests/unit/test_m3_receipt.py`, `tests/unit/test_m3_recovery.py`,
`tests/unit/test_m3_recover.py`. Operator surface:
`tests/integration/test_m3_cli.py`, `tests/integration/test_cli.py`. Central configuration:
`tests/unit/test_env_overrides.py`, `tests/unit/test_config.py`.

**Expected identity movement: none.** No accepted preimage, digest, policy chain, or frozen identity
tuple changes. The relation and completeness column already existed in migration `0014`; this work
supplies their writer and their consumer rule, and writes neither to the accepted catalog.

**What it does not authorize.** Applying `0014`/`0015` to the accepted catalog, enabling either
activation constant, running the transition, running E0, the Decision 093 linkage diagnostic, the
persistence bridge, migration `0016`, E1, E2, M3.4, network, SEC, HTTP, a push, or a tag.

## Decision 116 — the disposable single-source compact canary execution path (real impact)

[Decision 116](Decisions/decision_116_m3_3_disposable_single_source_canary_path.md)
(`ACCEPTED — OWNER IMPLEMENTATION INSTRUMENT, RULINGS R6–R13`) adds an **additive, canary-only**
path that runs exactly one governed planned source under `e0-compact-evidence/2` into a disposable
world and stops. It is a second entry point, never a second parser: every parse call, identity,
digest, and durable row comes from the accepted modules.

**What it does not touch.** No research definition, cohort, quota, seed, or selector. No migration —
`0001`–`0015` are byte-unchanged and `0016` does not exist. No E0 authority constant, no E0 run
namespace, no `m3/e0.py` import, no acquisition, transport, HTTP, or network path. Nothing is
promoted, the accepted operational catalog is opened `SQLITE_OPEN_READONLY` on every path with no
writer lease taken on it, and the private evidence root receives no write.

| Surface touched | Change | Nearest tests |
|---|---|---|
| `src/disclosure_drift/m3/single_source_canary.py` | **new** — the whole canary path: one-source selection by `census_plan_sources.source_instance_id` with no path argument and no all-source fallback; the create-once disposable world; the Decision 111 `WorkingCatalog` wiring; the **explicit** `e0-compact-evidence/2` binding at the one `CensusCatalog` constructed; the Decision 112 §8 sidecar and digest emission; and the write-once result document. **§21 (R11)**: the work-root invariant is enforced by `run_single_source_canary()` itself through the accepted `require_disposable_work_root()` primitive, before any world exists — not only by the operator wrapper | `tests/unit/test_d116_single_source_canary.py` |
| `src/disclosure_drift/m3/offline_parse.py` | the one-source entry point beside the accepted whole-plan driver — `select_planned_source`, `materialize_one_planned_source`. The whole-plan driver, its traversal, and its semantics are unchanged | `tests/unit/test_m3_offline_parse.py`, `tests/unit/test_d116_single_source_canary.py` |
| `src/disclosure_drift/m3/compact_evidence.py` | one additive read-only accessor: the member-manifest identity over rows the sidecar already holds, folded by the **same** rule its own identity uses. **§22 (R12)**: a single-payload source is one logical member named by its frozen `relative_storage_path`. Nothing persisted changes and no accepted digest semantics move | `tests/unit/test_d112_compact_evidence.py`, `tests/unit/test_d116_single_source_canary.py` |
| `src/disclosure_drift/cli.py` | the `m3 canary-source --mode {preflight,run}` operator surface, sitting apart from the two PRE-E0 surfaces. Routing and rendering only; it takes no path option and prints no absolute path | `tests/integration/test_m3_cli.py`, `tests/unit/test_d116_single_source_canary.py` |
| `Docs/change_impact_map.md`, `Milestones/STATUS.md` | **R6 and R9 status-truth corrections only** — the live mutation-anchor partition is 38 recovered / 36 resolved / `['M19', 'M21']` superseded per [Decision 114](Decisions/decision_114_m3_3_m21_live_anchor_supersession.md), and the active blocker is acceptance of the execution path rather than `LOCAL_CAPACITY_INSUFFICIENT_AFTER_D113`. Historical prose is preserved | `tests/unit/test_audit_tooling.py` |

**Which tests to run for it.** Direct: `tests/unit/test_d116_single_source_canary.py`. Compact
evidence and bounded-parse neighbours, because the canary reuses their fixtures and their contract:
`tests/unit/test_d112_compact_evidence.py`, `tests/unit/test_d110_bounded_parse_memory.py`. The
one-source entry point's own module: `tests/unit/test_m3_offline_parse.py`. Operator surface:
`tests/integration/test_m3_cli.py`. Campaign-audit truthfulness, because the R9 correction is
asserted against the shipped tree: `tests/unit/test_audit_tooling.py`.

**Expected identity movement: none.** No accepted preimage, digest, policy chain, or frozen identity
tuple changes, and semantic compaction stays closed.

**What it does not authorize.** Running any real source, creating a D115 disposable world or run
identity, enabling any activation constant, an E0-v3 namespace, migration `0016`, the persistence
bridge, E1, E2, M3.4, network, SEC, HTTP, a push, or a tag.

## Decision 119 — the cache-bound persistence correction and the prefix surface (real impact)

[Decision 119](Decisions/decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md)
(`ACCEPTED — OWNER IMPLEMENTATION INSTRUMENT, RULINGS R21–R28`) makes exactly **one** performance
change and adds a diagnostic-only way to measure it. The single change is an explicit **512 MiB**
page cache — `PRAGMA cache_size = -524288` — on the **run-local writable** Decision 111 working
catalog, correcting the [Decision 118](Decisions/decision_118_m3_3_read_only_performance_diagnosis.md)
§1 cause of the [Decision 117](Decisions/decision_117_m3_3_first_source_canary_throughput_failure.md)
throughput failure. The diagnostic surface is `m3 canary-source --mode profile-prefix
--member-limit N`, which runs the exact accepted path over the first *N* governed members and
stops before any source-level finalization.

**What it does not touch.** No research definition, cohort, quota, seed, or selector. No
migration — `0001`–`0015` are byte-unchanged and `0016` does not exist. No evidence contract, no
digest, no capacity constant, no schema, and no index. No sidecar transaction semantics,
`synchronous`, `journal_mode`, batch size, checkpoint cadence, `cache_spill`, `mmap_size`, parser,
lookup, or source ordering — Decision 119 §3 states that list, and Decision 118 §§5–7's deferrals
stay deferred. No E0 authority constant, no E0 run namespace, no acquisition, transport, HTTP, or
network path. The governed operational catalog, every read-only connection, and SQLite's global
defaults receive **no cache mutation**, and the preserved D117 world is not opened.

| Surface touched | Change | Nearest tests |
|---|---|---|
| `src/disclosure_drift/m3/working_catalog.py` | the optional `cache_bytes` budget on `WorkingCatalog`, defaulting to `None` so every existing caller is behaviourally unchanged; the `cache_size_pragma` primitive that converts a byte budget to SQLite's negative kibibyte form and refuses one it cannot state exactly; and read-back accessors for the requested and **effective** setting | `tests/unit/test_d119_cache_and_prefix.py`, `tests/unit/test_d111_bounded_persistence.py` |
| `src/disclosure_drift/m3/offline_parse.py` | the **internal** `max_members` cap on the accepted bulk member stream (default `None`); `materialize_planned_source_prefix` and `DiagnosticPrefixOutcome`; `DIAGNOSTIC_PREFIX_CLASSIFICATION`; and the §5 (R27) `CompactSourceEvidence._seen` residency correction, which is documentation only. `materialize_one_planned_source` is **unchanged** and does not expose the cap | `tests/unit/test_d119_cache_and_prefix.py`, `tests/unit/test_m3_offline_parse.py`, `tests/unit/test_d110_bounded_parse_memory.py` |
| `src/disclosure_drift/m3/single_source_canary.py` | the accepted 512 MiB binding on the canary's working catalog; the preflight's requested-cache report; and `run_single_source_prefix_profile` with `CanaryPrefixResult` and its own create-once result document | `tests/unit/test_d119_cache_and_prefix.py`, `tests/unit/test_d116_single_source_canary.py` |
| `src/disclosure_drift/cli.py` | the third `canary-source` mode `profile-prefix` and the `--member-limit` argument. Routing and rendering only; `run` refuses a limit | `tests/unit/test_d119_cache_and_prefix.py`, `tests/integration/test_m3_cli.py` |

**Which tests to run for it.** Direct: `tests/unit/test_d119_cache_and_prefix.py`. The canary path
it extends: `tests/unit/test_d116_single_source_canary.py`. The working catalog and the streamed
traversal it touches: `tests/unit/test_d111_bounded_persistence.py`,
`tests/unit/test_d110_bounded_parse_memory.py`, `tests/unit/test_m3_offline_parse.py`. The evidence
contracts whose digests must not move: `tests/unit/test_d112_compact_evidence.py`,
`tests/unit/test_d113_compact_derived_evidence.py`. Operator surface and boundaries:
`tests/integration/test_m3_cli.py`, `tests/unit/test_m3_3_boundaries.py`.

**Expected identity movement: none.** No accepted preimage, digest, policy chain, or frozen
identity tuple changes. Two canaries over one accepted catalog differing only in the cache budget
are required to produce identical identities and identical durable counts, and do.

**What it does not authorize.** Running any real source, retrying the D117 canary, opening the
preserved D117 world for parsing, creating a real prefix world, the three-source canary, the real
replay proof, enabling any activation constant, an E0-v3 namespace, migration `0016`, the
persistence bridge, E1, E2, M3.4, network, SEC, HTTP, a push, or a tag.

## Decision 127 — the pre-F2 free-space admission guard (real impact)

[Decision 127](Decisions/decision_127_m3_3_pre_f2_admission_guard.md) implements the one thing
[Decision 126](Decisions/decision_126_m3_3_complete_first_source_final_preflight.md) §7 (D126-R6)
authorized: the [Decision 124](Decisions/decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5)
`>= 30 GiB` free-space predicate, taken **immediately before F2 opens its single transaction**. The
complete-source path had no such predicate — F1 returned and F2 was the next statement — and
Decision 126 recorded that as the sole blocker on an otherwise passing live preflight.

**It has to be in-path, and that is the whole design.** Decision 126 §7 rules that no external
sampler can satisfy the predicate: no enforceable pause exists at the boundary, ledger state does not
distinguish F1 from impending F2, an external process can signal but cannot decline admission
atomically, and a sampling race survives any cadence. **Only the code about to open the transaction
can decline to open it.**

**What it deliberately does not add.** No `105 GiB` launch gate and no continuous `10 GiB` monitor in
production code — Decision 126 §8 (D126-R5) makes both wrapper/monitor-enforced. No change to
`create_world`, temporary-directory handling, the F1 or F2 algorithms, write-ahead log, checkpoint,
cache, or `synchronous` settings, schemas, migrations, E0, any activation constant, or the network
switches.

| Surface touched | Change | Nearest tests |
|---|---|---|
| `src/disclosure_drift/m3/single_source_canary.py` | three additions, `57` lines, nothing removed or modified: the frozen `PRE_F2_MINIMUM_FREE_BYTES = 30 * 1024**3` = `32,212,254,720` bytes, exported in `__all__`; the `_require_pre_f2_free_space()` guard measuring `shutil.disk_usage(...).free` on the disposable world's own volume, comparing with a **strict `<`** so the floor itself admits, and raising `SingleSourceCanaryError` naming the actual free bytes, the required minimum, and that F2 was refused before its single transaction opened; and the call site placed **between** F1 and F2 inside `_materialize`. The [Decision 094](Decisions/decision_094_m3_3_pre_e0_executability_redesign.md) §6.4 resolution-before-projection ordering is unchanged | `tests/unit/test_d127_pre_f2_admission_guard.py`, `tests/unit/test_d116_single_source_canary.py`, `tests/unit/test_d119_cache_and_prefix.py` |

**Which tests to run for it.** Direct: `tests/unit/test_d127_pre_f2_admission_guard.py`. The canary
path it guards, in both its complete-source and prefix shapes:
`tests/unit/test_d116_single_source_canary.py`, `tests/unit/test_d119_cache_and_prefix.py`. The
traversal and evidence contracts on either side of the boundary:
`tests/unit/test_m3_offline_parse.py`, `tests/unit/test_d112_compact_evidence.py`. Operator surface
and boundaries: `tests/integration/test_m3_cli.py`, `tests/unit/test_m3_3_boundaries.py`.

**Expected identity movement: none.** The guard is an admission predicate, not a budget. It moves no
row, no ordering, no digest, and no identity, and F2's behaviour at or above the floor is exactly what
it was before. A run that clears the floor produces byte-identical evidence to one taken before the
change.

**One consequence is recorded rather than smoothed** (Decision 127 §5). The guard applies to every
run of the path, including the Decision 116 and Decision 119 three-member synthetic worlds, so on a
machine with less than `30 GiB` free those suites would refuse at the admission gate rather than fail
at anything they test. Making the floor injectable or test-overridable is scope expansion, and a
test-overridable safety floor is weaker than what D124-R5 asked for. The new proofs pin free space
explicitly so that they never depend on the measuring machine.

**What it does not authorize.** Running any real source, the complete-source run, the D117 retry, the
three-source canary, the real replay proof, creating any disposable world, enabling any activation
constant, an E0-v3 namespace, migration `0016`, the persistence bridge, E1, E2, M3.4, network, SEC,
HTTP, or a tag. **Closing the Decision 126 §7 gap does not open the run**: Decision 127 is ready for
independent review and is not owner-accepted, and Decision 126 §10 (D126-R8) still requires a
regenerated run identity and a new final live preflight before any execution.

## Decision 131 — the D128 semantic and operational repair (real impact)

[Decision 131](Decisions/decision_131_m3_3_d128_semantic_and_operational_repair.md) repairs the two
blocking `PARSER_IMPLEMENTATION_DEFECT` findings
[Decision 129](Decisions/decision_129_m3_3_d128_semantic_adjudication.md) recorded — historical
shards dispatched to the primary parser (§5, D129-R3) and historical references stamped with one
observation-wide registrant CIK (§6, D129-R4) — together with the recognized optional fields
(D129-R7), watchdog `SIGINT` delivery (D129-R10), and post-traversal monitoring (D129-R11) that
record required alongside them.

**It is published with its code, in the same commit.** The record, the implementation, and the tests
are verifiable against each other by inspection rather than by trusting a later narrative.

**What it deliberately does not change.** No performance tuning of any kind — SQLite cache, batching,
checkpoint cadence, WAL mode, `synchronous` durability, index architecture, multiprocessing or writer
topology, and the [Decision 127](Decisions/decision_127_m3_3_pre_f2_admission_guard.md) pre-F2 gate
are all untouched. No schema, no migration (`registrant_cik_padded` already existed on both reference
tables and is already part of the primary key), no activation constant, and neither network switch.
**`CensusOrchestrator._parse_bulk` is deliberately NOT repaired** and is recorded as an explicit
pre-network blocker (D131-R4).

| Surface touched | Change | Nearest tests |
|---|---|---|
| `src/disclosure_drift/m3/offline_parse.py` | the corrected bulk dispatch: `_DeferredHistoricalShard` (name and ordinal, **no payload**), `_shard_filename_cik`, `_is_historical_shard_member`, `_historical_shard_member_names`, `_declare_shard_parents`, `_resolve_shard_parent`, and `_stream_deferred_historical_shards`. A shard never reaches `parse_submissions_document(...)`; parents come from the explicit `filings.files[].name` declaration; deferred shards are reopened by exact member name in original archive ordinal order after the traversal ends; **every parent is resolved before any member is reopened**; and a missing, ambiguous, or contradicted binding **fails closed**. Under a diagnostic cap the deferred phase does not run (D131-R7) | `tests/unit/test_d131_historical_shard_dispatch.py`, `tests/unit/test_m3_offline_parse.py`, `tests/unit/test_d119_cache_and_prefix.py`, `tests/unit/test_d110_bounded_parse_memory.py` |
| `src/disclosure_drift/sec/parsers/submissions.py` | `HistoricalFileReference.registrant_cik_padded` — **required, no default** — set by the declaring document and carried into `as_mapping()`; `KNOWN_OPTIONAL_RECENT_FIELDS` and the `RECOGNIZED_RECENT_FIELDS` union, with shape enforcement still reading `ACCESSION_ARRAY_FIELDS` alone; `lei` registered as a known optional top-level field; `PARSER_VERSION` `submissions-json/1.1` → **`1.2`** | `tests/unit/test_r2_submissions_structure.py`, `tests/unit/test_sec_parsers_and_census.py`, `tests/unit/test_parser_version_authority.py`, `tests/unit/test_d131_historical_shard_dispatch.py` |
| `src/disclosure_drift/sec/parsers/historical.py` | the unknown-field basis moves from `ACCESSION_ARRAY_FIELDS` to `RECOGNIZED_RECENT_FIELDS`, so a shard carrying `core_type` or `isXBRLNumeric` no longer reports either as drift; `PARSER_VERSION` `submissions-historical/1.0` → **`1.1`**, because that changes every emitted record's `unknown_fields` and the persisted `unknown_fields_json` | `tests/unit/test_parser_version_authority.py`, `tests/unit/test_d131_historical_shard_dispatch.py`, `tests/unit/test_sec_parsers_and_census.py` |
| `src/disclosure_drift/sec/census.py` | `CensusCatalog._insert_historical_references` normalizes **each reference's own** `registrant_cik_padded` instead of resolving one value per observation from the lowest-`parsed_record_id` registrant record; valid and malformed persistence both preserve parent identity; an unusable parent CIK raises rather than substituting a value. The per-part write-ordering comment is corrected: references no longer *need* to run last, and the position is retained only because it is the accepted write order | `tests/unit/test_sec_parsers_and_census.py`, `tests/unit/test_d131_historical_shard_dispatch.py`, `tests/unit/test_m3_offline_parse.py` |
| `src/disclosure_drift/sec/archive.py` | `iter_named_members(...)` added to `__all__` — a bounded, targeted read of exactly the requested canonical member names, in the requested order, applying the same per-member type, size, ratio, and traversal defences as `iter_members` and holding one payload at a time. Absent, ambiguous, and repeated names are refused. The archive-level *cumulative* expansion cap is deliberately not re-applied to a subset | `tests/unit/test_sec_archive.py`, `tests/unit/test_d131_historical_shard_dispatch.py` |
| `scripts/m3/canary_launch.py` (new) | the corrected governed launch surface: foreground, `exec`-based, **refuses** an inherited `SIGINT = SIG_IGN`, and records the `exec`-preserved PID in `--pid-file`. It holds no authority constant, reads no catalog, takes no lease, and enables no network | `tests/unit/test_d131_signal_and_monitor.py` |
| `scripts/m3/canary_watchdog.py` (new) | the corrected stop, probe, and monitor: exact PID and command authentication with an empty expectation refused; `SIGINT` only; verified termination with **no `SIGTERM`/`SIGKILL` escalation**; `ProcessLookupError` → already gone and `PermissionError` → failure; `lsof -nP -a -p PID -i` **intersection**; the strict `pid > 0` domain stated once in `non_targetable_pid_detail(...)` and refused before inspection, `lsof` construction, or signalling; and the three member-count relations with `MEMBER_COUNT_INCONSISTENT` at exit `5` | `tests/unit/test_d131_signal_and_monitor.py` |
| `Docs/m3/operator_runbook.md` | §28b the corrected launch/stop/probe/monitor contract with its full exit-code table including both non-positive-PID refusals (D131-R11), and §28c what a bounded prefix does **not** prove about historical shards plus the `CensusOrchestrator._parse_bulk` pre-network blocker | operator surface — no direct test file; the behaviours it documents are pinned by `tests/unit/test_d131_signal_and_monitor.py` |

**Which tests to run for it.** Direct: `tests/unit/test_d131_historical_shard_dispatch.py` (`46`),
`tests/unit/test_d131_signal_and_monitor.py` (`42`),
`tests/unit/test_parser_version_authority.py` (`35`), `tests/unit/test_sec_archive.py` (`66`). The
parser and persistence contracts either side of the change:
`tests/unit/test_sec_parsers_and_census.py`, `tests/unit/test_r2_submissions_structure.py`,
`tests/unit/test_m3_offline_parse.py`. The traversal residency and prefix surfaces the deferral must
not disturb: `tests/unit/test_d110_bounded_parse_memory.py`,
`tests/unit/test_d119_cache_and_prefix.py`, `tests/unit/test_d112_compact_evidence.py`. Operator
surface and boundaries: `tests/integration/test_m3_cli.py`, `tests/unit/test_m3_3_boundaries.py`.

**Expected identity movement: yes, and it is the point.** A corrected run parses members D128 never
parsed and writes reference rows under registrants D128 never wrote, so a future run's counts and
evidence will not match D128's. **That is the repair, not a regression** — and it is also why both
parser versions move: a version that stayed put while its parser's output changed would let a
pre-D131 artifact be judged compatible with an implementation that no longer produces it.

**Provenance already recorded under prior parser versions is never rewritten.** No `UPDATE` of any
`parser_version` exists anywhere in `src/`. What changes is reuse: `versions_agree(...)`,
`require_parser_version(...)`, and `evaluate_reuse(...)` all fail closed on a version mismatch, in
**both** directions.

**What it does not authorize.** A bounded real semantic proof against the real source, the corrected
complete-source canary, any canary, any disposable world, creating any world, enabling any activation
constant, an E0-v3 namespace, migration `0016`, network, SEC, HTTP, or a tag. **Repairing the defect
is not proving the repair**: D131-R7 rules that an ordinary `--member-limit` prefix parses **zero**
deferred shards, so the semantic proof requires a separately authorized fixture or mode and is the
next stage.

**That proof has since been performed, and it changed no code.**
[Decision 132](Decisions/decision_132_m3_3_bounded_real_semantic_proof.md) records the bounded real
semantic proof of the repair described in this section, over seven byte-exact real SEC members drawn
from the accepted bulk archive: `0` historical shards reached the primary parser and `4` of `4`
reached the historical one; explicit parent binding held across three distinct registrants; archive
order changed no semantic output; and an orphaned-shard fixture was refused fail-closed. **It has no
impact entry of its own because no source changed for it** — no production code, test, script,
configuration, or migration moved — so every path and test named above stands exactly as written.
The proof makes **no source-wide claim** and **certifies no D128 count**.

**One line of that watchdog row has since been repaired, and the row otherwise stands.**
[Decision 133](Decisions/decision_133_m3_3_watchdog_linux_portability_repair.md) records a
cross-platform conformance defect in `scripts/m3/canary_watchdog.py`'s command probe: `/bin/ps -o
command= -p PID` is truncated by Ubuntu/`procps` at `80` columns when its stdout is a pipe, so the
expected target substring fell off the end and every legitimate long-command target on Linux
authenticated as `STOP_REFUSED_TARGET_MISMATCH` and was **never signalled**. macOS BSD `ps` does not
truncate in that condition, so the local gate could not observe it. The repair is `/bin/ps -ww -o
command= -p PID` — one argv for both platforms, **no platform branch and no `/proc` fallback** — and
**every other contract in the watchdog row above is unchanged**: the `pid > 0` domain, the `-o
state=` liveness probe, exact-target authentication, `SIGINT` only, `STOP_FAILED`,
`ProcessLookupError`, `PermissionError`, the `lsof` intersection, and `MEMBER_COUNT_INCONSISTENT` at
exit `5`.

| Surface touched | Change | Nearest tests |
|---|---|---|
| `scripts/m3/canary_watchdog.py` | `process_command(...)` asks `ps` for **unlimited width** (`-ww`). Nothing else in the stop, probe, or monitor contract moves | `tests/unit/test_d131_signal_and_monitor.py` |
| `tests/unit/test_d131_signal_and_monitor.py` | one additive test, `test_the_command_probe_asks_ps_for_unlimited_width`, asserting the **actual `ps` argv** rather than the observed behaviour — the four originally Linux-failing tests still pass on macOS without `-ww`, so only the request distinguishes the two implementations. Removing `-ww` is killed by this test | itself |

**Which tests to run for it.** `tests/unit/test_d131_signal_and_monitor.py`, and nothing else is
implicated — **no production package code, configuration, schema, or migration changed**, so no
research-pipeline surface in this map is affected and no test selection elsewhere in it changes.
Proven on Linux by CI run `32605572777` at `977a811b…`: `4899` passed, `1` skipped, `0` failed, with
all four previously failing nodes green under `ubuntu-latest`/`procps`.

**A bounded performance A/B has since been run against that same runtime, and it changed nothing
here either.** [Decision 134](Decisions/decision_134_m3_3_bounded_performance_ab.md) measured two
low-risk runtime candidates — `PRAGMA mmap_size` and a relaxed F0/F1 checkpoint cadence — at two
bounded operating points, and the owner **rejected both for adoption** (D134-R1). **It has no impact
entry of its own because no source changed for it**: neither candidate was implemented, the accepted
[Decision 131](Decisions/decision_131_m3_3_d128_semantic_and_operational_repair.md) runtime
configuration and the accepted
[Decision 119](Decisions/decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md) pragma
surface are **byte-unchanged**, and the record's executable change set is **empty** — so every path
and test named in this map stands exactly as written and **no test selection anywhere in it
changes**.

**One durable finding from it belongs in this map, because it forecloses a plausible future change.**
Relaxing the F0/F1 checkpoint cadence by `32×` (`5,120` → `160` checkpoints issued, `4,960`
suppressed) left the **WAL high-water mark byte-identical at `768,054,552` bytes**
([Decision 134](Decisions/decision_134_m3_3_bounded_performance_ab.md) §5, D134-R3). Peak WAL is set
entirely by **F2's single association transaction, which neither arm checkpoints inside** — the
F0/F1 cadence never governed the peak at all. **A future change proposing to control peak WAL by
tuning `BoundedTransaction` checkpoint cadence in F0 or F1 is answered in advance: it cannot work**,
and it would need to target F2 instead. The `>= 30` GiB pre-F2 admission gate
([Decision 127](Decisions/decision_127_m3_3_pre_f2_admission_guard.md)) is **untouched** by that
finding and remains in code as written.

**The measurements bound their own reach.** They describe two fixtures of `3,520` and `6,871` archive
members drawn from a source holding `985,835` — under `0.7%` — and authorize **no complete-source
performance claim**. The mmap benefit **declined** as the catalog grew (`12.84%` → `9.775%`, map
coverage `80.64%` → `45.33%`), which trends the wrong way for a larger run.

**The capacity model that followed it changed no source either — but it carries one live finding
about a constant in this map.**
[Decision 135](Decisions/decision_135_m3_3_corrected_run_capacity_reconciliation.md) constructs the
corrected-run capacity reconciliation that
[Decision 129](Decisions/decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12) required,
and accepts a **`185` GiB start floor** and a **`50` GiB pre-F2 floor**. **It has no impact entry of
its own because no source changed for it**: its executable change set is **empty**, the accepted
[Decision 131](Decisions/decision_131_m3_3_d128_semantic_and_operational_repair.md) runtime
configuration is byte-unchanged, and no path or test selection anywhere in this map changes.

**The finding that belongs here: the `>= 30` GiB pre-F2 admission gate is now known to be
inadequate, and it is deliberately still in code.**
`PRE_F2_MINIMUM_FREE_BYTES = 30 * 1024**3` in `src/disclosure_drift/m3/single_source_canary.py`
([Decision 127](Decisions/decision_127_m3_3_pre_f2_admission_guard.md)) is **unchanged and must stay
unchanged until separately authorized** — D135 §8 (D135-R3) rules the constant insufficient but
**explicitly does not authorize editing it**. The corrected projection consumes **`27.5539` GiB of
that `30` GiB gate outright**, leaving `2.4461` GiB with **zero safety reserve**. **A future session
that edits this constant as an obvious follow-up would be acting outside D135**, and a session that
reads the `30` and assumes it is a validated threshold would be reading a superseded planning value.
Both readings are wrong; the constant is live, known-low, and frozen pending its own instrument.
Deferring the edit is safe **because no run is authorized** — a gate never reached cannot be reached
at the wrong value. Its **nearest tests are unchanged**, since neither the guard nor its constant
moved.

**The external-volume qualification that followed changed no source either — and it names the
constant above as the next thing to change, under its own instrument.**
[Decision 136](Decisions/decision_136_m3_3_external_ssd_active_volume_qualification.md) qualified one
exact external volume (`/Volumes/SSK SSD`, **Volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049`**,
ExFAT via Apple FSKit) against the six requirements
[Decision 135](Decisions/decision_135_m3_3_corrected_run_capacity_reconciliation.md) §10 (D135-R5)
set, and returned `D136_EXTERNAL_SSD_PASS_WITH_ARCHIVE_ISOLATION_REQUIRED`. **It has no impact entry
of its own because no source changed for it**: its executable change set is **empty**, the accepted
[Decision 131](Decisions/decision_131_m3_3_d128_semantic_and_operational_repair.md) runtime
configuration is byte-unchanged, and no path or test selection anywhere in this map changes.
`PRE_F2_MINIMUM_FREE_BYTES` is **still `30 * 1024**3` and still frozen** — D136 §16 repeats that it
is not edited here and not authorized to be. **Replacing its behaviour is Decision 137 work**
(D136-R11 item 6), and until that instrument exists the paragraph above still governs the constant.

**What a D137 session will touch, stated here so the surface is known before it is opened.**
D136-R11 requires external working-root selection **using an existing supported surface if one
already exists, otherwise the smallest new surface necessary**; a **fail-closed candidate-volume
identity guard keyed on the stable Volume UUID rather than the attach-time `disk4s2` identifier**;
**refusal if the selected working root resolves inside the D130 archive tree**; a `>= 185` GiB launch
floor and a `>= 50` GiB pre-F2 floor; D135-R7-consistent phase-boundary and F2 capacity monitoring;
operator and runbook requirements for external power and `caffeinate`/no-sleep execution; and
**targeted tests with independent validation**. The nearest affected paths are
`src/disclosure_drift/m3/single_source_canary.py` (the pre-F2 admission guard and its constant) and
whatever working-root surface D137 selects; **its nearest tests are the pre-F2 admission-guard tests
plus whatever new guard D137 adds**. **None of that is authorized yet** — D136 grants no
implementation authority, and a session that starts any of it without the D137 packet is acting
outside D136.

**Two D136 findings foreclose plausible future changes, in the same shape as the D134 and D135
findings above.** First, **`mmap_size` was deliberately left unset** during qualification and read
back as `0`; D134's mmap and relaxed-checkpoint candidates **remain rejected** and D136 adopts
neither. Second, **the `128` KiB ExFAT allocation block makes many-small-file layouts expensive** —
an `8,192`-byte SQLite database allocated `131,072` bytes — so a future change that scatters many
small files onto that volume would pay a cost the `185` GiB floor does not model. **`SQLITE_TMPDIR`
placement stays explicit** ([Decision 124](Decisions/decision_124_m3_3_capacity_reconciliation.md)
§9, D124-R5, untouched), and its behaviour on ExFAT is **unmeasured** — D136 §8 carries that forward
to D137 rather than resolving it.


**One further D135 finding forecloses a plausible future change, in the same shape as the D134 WAL
finding above.** The `10` GiB continuous floor, the no-`VACUUM` rule, and explicit `SQLITE_TMPDIR`
placement ([Decision 124](Decisions/decision_124_m3_3_capacity_reconciliation.md) §9, D124-R5) are
**untouched by D135** and remain exactly as written. **Only the `105` GiB start gate and the `30` GiB
pre-F2 gate are superseded, and only for planning purposes** — no gate is relaxed, in code or on
paper, and D135 relaxes nothing anywhere.



## Decision 137 — the external working-root guards and the capacity-safety implementation (real impact)

[Decision 137](Decisions/decision_137_m3_3_external_working_root_and_capacity_safety.md) implements
the nine items [Decision 136](Decisions/decision_136_m3_3_external_ssd_active_volume_qualification.md)
§11 (D136-R11) assigned to it. **It adopts nothing and starts nothing**, and it creates **no second
root-selection mechanism**: the existing operator-supplied `--work-root` is reused unchanged, and
the new work is *authentication* rather than *naming*.

| Path | What changed | Direct test files |
|---|---|---|
| `src/disclosure_drift/m3/external_working_root.py` | **new** — the whole D137 guard surface: the frozen Volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049`; the `185`/`20`/`10` GiB constants; `mount_point_of` (an `st_dev` walk, because `diskutil` will not answer for a subdirectory) and `macos_volume_identity` (a **property list**, never the human-oriented table); `require_qualified_volume`, `require_outside_d130_archive`, `require_launch_free_space`, `f2_capacity_state`, `CapacityObservation`/`observe_capacity`, `require_external_sqlite_tmpdir`, the D130 §6 compact proofs with `verify_d130_archive`, and the composed `external_canary_preflight`. Every guard resolves its identity provider from module globals **at call time**, which is the test seam | `tests/unit/test_d137_external_working_root.py` |
| `src/disclosure_drift/m3/single_source_canary.py` | `PRE_F2_MINIMUM_FREE_BYTES` `30 * 1024**3` → `50 * 1024**3` (D137-R5) — **the constant only**; the strict `<`, the call site between F1 and F2, and the Decision 094 §6.4 ordering are byte-unchanged. One optional `require_volume_uuid` (with `environ`) on `run_single_source_canary`, `run_single_source_prefix_profile`, and `run_canary_source_command`; the `_PhaseObserver` seam and five in-process phase observations; `CanaryResult.capacity_observations`, **rendered only when non-empty** so an internal run's result document is byte-unchanged | `tests/unit/test_d137_external_working_root.py`, `tests/unit/test_d127_pre_f2_admission_guard.py`, `tests/unit/test_d116_single_source_canary.py`, `tests/unit/test_d119_cache_and_prefix.py` |
| `src/disclosure_drift/cli.py` | one optional flag, `m3 canary-source --require-volume-uuid`. Omitted, the command behaves exactly as before | `tests/integration/test_m3_cli.py` |
| `scripts/m3/canary_watchdog.py` | the `capacity` subcommand and exit `6`; thresholds **imported** from the package rather than restated, so a monitor cannot drift from the gate it monitors. **No signal, no deletion, no cleanup**, and the accepted D131 no-escalation invariant is untouched | `tests/unit/test_d137_external_working_root.py`, `tests/unit/test_d131_signal_and_monitor.py` |
| `Docs/m3/operator_runbook.md` | §28d — the external-volume preflight, the twelve operator conditions with **four mechanically verified and eight not**, the monitoring table, the D130 archive postcheck, and the launch command marked **not authorized** | — |

**Which tests to run for it.** Direct: `tests/unit/test_d137_external_working_root.py`. The pre-F2
constant change reaches `tests/unit/test_d127_pre_f2_admission_guard.py`, which is **updated in
place rather than deleted or skipped** — every Decision 127 claim is re-proved at the floor that now
controls, and the superseded `30` GiB amount is retained as a named constant so its refusal can be
tested against the exact number that used to admit. The canary threading reaches
`tests/unit/test_d116_single_source_canary.py` and `tests/unit/test_d119_cache_and_prefix.py`, whose
byte-level evidence-equivalence is preserved by rendering `capacity_observations` **only when
non-empty**. The watchdog addition reaches `tests/unit/test_d131_signal_and_monitor.py`, and the CLI
flag reaches `tests/integration/test_m3_cli.py`.

**No migration, no schema change, and no parser or runtime-semantics change.** Migration head stays
`0015`; `0016` is absent and unauthorized. `mmap` and the relaxed checkpoint cadence remain rejected
(D134). `CensusOrchestrator._parse_bulk` remains an open PRE-NETWORK blocker and was **not** touched.

**What the D137 guards do not cover, so a reader does not infer more.** `DURING_F2` cannot be
sampled in-process — F2 is one blocking call inside one transaction — so it belongs to the
watchdog's `capacity` subcommand and depends on the operator running it. The external requirement is
**opt-in**: omitting `--require-volume-uuid` restores the pre-D137 behaviour exactly, which is what
keeps every existing internal-volume canary path working. `macos_volume_identity` is macOS-only and
**fails closed** elsewhere. And nothing here claims journaled filesystem semantics, power-loss
safety, surprise-removal safety, or USB-bridge cache-flush correctness — Decision 136 §9 (D136-R6)
established **process-crash recovery only**, and that boundary is preserved exactly.


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
