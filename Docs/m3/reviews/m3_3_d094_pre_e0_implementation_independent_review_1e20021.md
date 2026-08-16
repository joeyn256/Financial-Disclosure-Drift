All evidence gathered; disposable artifacts removed; authoritative repository verified byte-identical. Report follows.

---

# 1. RESULT TOKEN AND VERDICT

```
M3_3_D094_PRE_E0_IMPLEMENTATION_INDEPENDENT_REVIEW_FAIL
```

**Verdict:** FAIL — 0 BLOCKER, **2 MAJOR**, 4 MINOR, 1 OPTIMIZATION, 4 OBSERVATION.

This is a *narrow* FAIL against a candidate that is otherwise of unusually high quality. Both MAJOR findings are bounded, reproducible, and correctable inside the already-authorized path set; neither invalidates the architecture, the membership semantics, the write footprint, the identity law, or the operator boundary, all of which I independently verified as correct. No finding reads as a false success: every defect I reproduced fails closed.

I recommend **REJECT-WITH-BOUNDED-CORRECTION**, not rejection of the design. Owner adjudication is Sol/GPT's; I authorize nothing.

---

# 2. MODEL / EFFORT / FRESHNESS / NO-DELEGATION ATTESTATION

| Item | Attestation |
|---|---|
| Actual running model | **MEASURED FACT** — `claude-opus-5`. Attested as the actual running harness/model identity, emitted as the first output line before any substantive repository read. |
| Effort | **REPOSITORY OBSERVATION / disclosed limitation** — Maximum was *requested/configured* by the parent ACP dispatch. The Claude CLI does not expose the parent effort setting on process arguments, environment, project settings, or transcript. Per accepted D096 **R85**, that absence is a disclosed observability limitation and not an invalidation. I did not fabricate an observed effort value. |
| Freshness | **MEASURED FACT** — new ACP review record, not resumed. I used **no** conclusion from the D094–D097 implementer epochs. Every implementer/Sol claim I relied on was independently re-measured (D097 §2 WIP hashes, D095 §3 counts, migration digests, gate log digest, 38/37/M19 partition). |
| Delegation | **MEASURED FACT** — one session, one model. No subagent, Agent tool call, workflow, delegated task, parallel model call, cloud review, second reviewer, worktree, or branch. All tool use was Bash/Read/Write-to-`/tmp` from this session. |
| Role boundary | I edited nothing, accepted nothing, and authorized nothing. |

---

# 3. FROZEN TARGET AND FINAL GIT STATE

**MEASURED FACT.** Verified before any substantive read, after every experiment, and at handoff.

| Fact | Expected | Observed | |
|---|---|---|---|
| branch | `main` | `main` | ✅ |
| HEAD | `1e200218be82702e55396a5afab579203a1545a9` | identical | ✅ |
| tree | `7d5f3aa9ba9b84c8fe041d0e9f8c8cd12f0133cd` | identical | ✅ |
| parent | `0920bc29e2a1c28a692105416a8f5d605507b9b0` | identical | ✅ |
| subject | `feat: implement Decision 094 pre-E0 execution surfaces` | identical | ✅ |
| recorded `origin/main` | `4ed0fc7f67c3f9b4f5750e7c24432269aed9ffc4` | identical | ✅ |
| relation | ahead 5 / behind 0 | `git rev-list --left-right --count origin/main...HEAD` → `0  5` | ✅ |
| worktree + index | clean | `git status --porcelain=v1` empty; `git diff --stat` and `git diff --cached --stat` both empty; no untracked | ✅ |
| tags at HEAD | none | `git tag --points-at HEAD` empty | ✅ |
| migrations | `0001`–`0015`, `0016` absent | exactly 15 files, `0016` count 0; `git diff HEAD~1 HEAD -- .../migrations/` empty | ✅ |
| stashes / worktrees | — | `git stash list` empty; one worktree (the checkout) | ✅ |
| reflog | — | `HEAD@{0}` is still the candidate commit; this session added no entry | ✅ |

**Final state at handoff is byte-identical to entry.**

**Full-gate log.** `/tmp/d097_checkfast.log` SHA-256 = `9e0a3a6ae299f008d3e47001e28f7cc4e7f1f0dcdebd02e5bf5a982a7aa31865` — **exact match** to the expected value. Its content records `4351 passed, 1 skipped in 79.40s`, plus secret scan (391 files, 0 findings), hygiene (393 paths, 0 findings), Markdown links (176 docs, 1669 links), and decision section references (4086 citations against 97 records). I did **not** rerun `make check-fast`.

---

# 4. EXACT DIFF SCOPE AND AUTHORITY

**MEASURED FACT — the commit is exactly 23 paths**, matching the supplied set element-for-element (`git diff --name-only HEAD~1 HEAD | wc -l` → 23).

Diff magnitude: 8,395 insertions / 280 deletions. Largest: `m3/e0.py` (+3463, new), `tests/unit/test_m3_e0.py` (+2035, new), `m3/offline_parse.py` (+950).

**Authority derivation.** The authorized union is D094 §12.1 ∪ D095 §6.2 ∪ D096 §6.1 (`execution_rehearsal.py`) ∪ D097 R88 (`tests/unit/test_audit_tooling.py`). All 23 paths fall inside it. Seven paths lie outside D094 §12.1 alone and each is separately authorized: `config.py`, `rehearsal_world.py`, `test_m3_3_execution.py`, `test_env_overrides.py`, `tests/integration/test_cli.py` (D095 §6.2); `execution_rehearsal.py` (D096 §6.1); `test_audit_tooling.py` (D097 R88). Nothing outside the union was touched.

**D097 R89's exact commit-content rule is satisfied precisely.** R89 permits "only the 22 preserved D096 WIP paths in section 2 plus `tests/unit/test_audit_tooling.py`" = 23. The commit is that exact set.

**Strongest independence evidence — MEASURED FACT.** I recomputed SHA-256 for all 22 D097 §2 preserved-WIP paths at HEAD (`git show HEAD:<path> | shasum -a 256`). **All 22 match the D097 §2 table byte-for-byte**, including `e0.py` = `6de8aae9…`, `test_m3_e0.py` = `8b063a1d…`, `offline_parse.py` = `2b0011e0…`, `candidate_snapshot.py` = `927043e7…`. This independently proves the D097 executor edited **only** `tests/unit/test_audit_tooling.py`, exactly as R88/R89 required — no WIP byte was altered under cover of the M19 correction.

Governance surfaces (`Docs/Decisions/`, `Milestones/`, registry, index, architecture map) are untouched by the implementation commit.

---

# 5. D094/D095/D096/D097 SEMANTIC PRESERVATION

**REPOSITORY OBSERVATION / MEASURED FACT — preserved, with the two MAJOR exceptions in §12.**

| Semantic | Finding |
|---|---|
| Migrations `0001`–`0015` unchanged; `0016` absent | ✅ MEASURED — migration diff vs parent is empty; `0014`/`0015` file digests are `0490ea4e…` / `d7f22999…`, **exactly** D094 §1.1 and exactly `PACKAGED_MIGRATION_SHA256` in `e0.py:186-189` |
| D094 §6.1 sixteen-table write set | ✅ MEASURED — `set(E0_PERMITTED_TABLES) == D094 §6.1` returns `True`, len 16, zero extra, zero missing; `E0_PERMITTED_PLAN_COLUMNS == {'census_plan_sources': ['parser_state']}` |
| D094 §6.2 fail-closed / no-invented-entity (§13 M6) | ✅ PRESERVED and load-bearing — proven by mutation (§11, M8b) |
| D094 §6.5 consumer rule | ✅ `_read_full_index_registrants` deleted; scalar union removed from `_registrant_rows`, from conflict attribution, and from `_submission_forms`; `census_registrants.get()` + `established_sets` is the only membership source |
| D094 §6.5 disclosed residual | ✅ `sec/census_orchestrator.py:943` still does `int(row['registrant_cik_numeric'])` — unchanged, exactly as D094 §6.5 discloses and as the closed acquisition path requires |
| D094 §7.2 both constants `None` | ✅ MEASURED — `e0.py:150` and `e0.py:163` are literally `Final[str | None] = None` |
| D095 R79 fixture-only correction | ✅ MEASURED — support-only CIKs are exactly `[917, 918]`, each with `accessions=()`; production rule untouched |
| D095 R80 central non-override root | ✅ `EVIDENCE_ROOT_ENV` in `RUNTIME_ROOT_ENV_VARS` → `RECOGNIZED_ENV_VARS`; absent from `ENV_OVERRIDES` and `SECRET_ENV_VARS`; no `cli.py` filtering bypass |
| D095 R81 source-local catalog literal | ✅ `e0.py:136` == `acquisition.py:242` == `"catalogs/m3_2a_operational.sqlite3"`; no acquisition import in `e0.py` |
| D096 R83 stale E2 variant removed | ✅ Only the `non-canonical full-index CIK` variant and `_corrupt_full_index_cik` removed; the other four E2 obligations and all eight `E1`–`E8` scenarios remain in the registry |
| D096 R84 R28 attribution | ✅ Third parametrization asserts `candidate_accession_evidence_sha256` **present** and `multi_registrant` **absent** |
| D097 R87 M19 partition | ✅ MEASURED — 38 recovered in exact `M1..M38` order; `verify_anchors` → exactly `['M19']` |
| Historical D094–D097 not rewritten | ✅ Governance diff empty |

---

# 6. TRANSITION PREFLIGHT / EXECUTE / VERIFY / RECOVERY REVIEW

## 6.1 Preflight — 12 of 13 §5.2 predicates implemented

**MEASURED FACT.** I enumerated every `refusals.append` in `e0.py` and mapped each to §5.2:

| §5.2 predicate | Implementation | |
|---|---|---|
| 1 exactly one canonical root | one env var, one `require_external_evidence_root` → one root by construction | ✅ |
| 2 fixed catalog path | `resolve_within(…, OPERATIONAL_CATALOG_RELATIVE_PATH)` + `_refuse_symlinked_descent` | ✅ |
| **3 M3.2 acquisition completion receipt + catalog binding** | **absent — see MAJOR-2** | ❌ |
| 4 contiguous `0001`–`0013` + applied name/checksum match | versions checked in `_shared_preflight`; names/checksums enforced structurally — `storage/sqlite.connect()` calls `verify_applied_migrations()` on **every** open, so a drifted ledger raises before inspection | ✅ |
| 5 packaged `0014`/`0015` digests, no `0016` | `_packaged_target_migrations()` selects by exact version and compares to §1.1; plus an explicit "a packaged migration beyond 0015 exists" refusal | ✅ |
| 6 quick_check / integrity_check / FK = 0 | ✅ | ✅ |
| 7 every §1.3 empty-state count zero | `EMPTY_STATE_TABLES` = sorted union of both guards | ✅ |
| 8 76 plan sources `not_started`, no parser run | ✅ | ✅ |
| 9 lease non-mutating | `_lease_state` never creates the file; absent → passes outright (finding m1 honored) | ✅ |
| 10 namespace absent, parent sound | namespace + symlink checked; **ownership and parent-existence not checked — MINOR-4** | ⚠️ |
| 11 `3×catalog + 1 GiB` | ✅ | ✅ |
| 12 §8.2 memory estimator | `estimate_release_hash_memory` scans without buffering; `_physical_memory_bytes()==0` refuses | ✅ |
| 13 network switches disabled | read from loaded config, not YAML | ✅ |

**Strictly read-only: MEASURED.** Preflight opens through `strictly_read_only_connection` (`SQLITE_OPEN_READONLY`), so a WAL close-checkpoint cannot rewrite durable bytes. My CLI sweep against a synthetic empty root left it containing **zero** entries.

## 6.2 Execute state machine — §5.3 items 1–11

All eleven items are implemented and correctly ordered: one continuous `CatalogWriter` lease wrapping everything; `_recheck_under_lease` before any namespace/backup; `create_run_namespace` at `0700` with symlink and pre-existence refusal via atomic `mkdir`; `_precreate_exclusive` at `0600` **before** SQLite opens the destination (finding m2 honored), SQLite backup API, `PRAGMA journal_mode=DELETE` so the run's write set stays exactly four files, close → fsync file → fsync parent → **then** digest; independent backup verification of chain/integrity/logical digest; `BACKUP_VERIFIED` fsynced before any migration; per-migration **accepted contiguous prefix** (`item.version <= migration.version`) rather than the full pending inventory; `prepare_operational_catalog()` correctly avoided (adopted O4 rationale is stated in-line); post-chain, empty-state-regain, and pre-existing-content equality checks; identity recomputation through a separate read-only connection while the flock is retained.

**Crash-boundary disclosure** is genuinely tracked: `interruption` is advanced to `after_migration_{NNNN}_commit_before_event` *between* the commit and the append, which is the exact §8.1 window.

## 6.3 Recovery — fail-closed, no automatic resume

`create_run_namespace` refuses any pre-existing path; there is no resume, repair, restore, force, or overwrite option anywhere; `_disclose_failure` never restores or deletes and always re-raises; `execute` at a non-`0013` head refuses under the lease. `KeyboardInterrupt`/`SystemExit` → `interrupted`, domain error → `failed`. Correct.

## 6.4 Verify

Strictly read-only, repairs nothing, and treats absence as `UNDETERMINED / NOT COMPLETE`. **MINOR-2:** it never opens the catalog, so the "catalog state" element of D094 §7.2's verify row is not validated. The code docstrings are honest (they list "namespace, receipt, ledger, terminal, and identities" and omit catalog state); the gap is against §7.2's wording, not a false claim.

---

# 7. E0 WRITE SET / SOURCE DISPOSITIONS / CANONICAL RELATION REVIEW

## 7.1 Write set and authorizer

**MEASURED FACT** — exactly the sixteen D094 §6.1 tables plus `census_plan_sources.parser_state`. The SQLite authorizer in `write_containment` fires at statement-prepare time and returns `SQLITE_DENY` for any `INSERT`/`UPDATE`/`DELETE` outside the positive set; because SQLite invokes the authorizer once per updated column, `UPDATE census_plan_sources SET parser_state=?, other=?` is denied on the second column. Neutering it (mutant M6) kills three parametrized refusal cases — the guard is load-bearing, not decorative.

## 7.2 76 source dispositions

`_source_result_records` builds one closed record per accepted `(census_run_id, source_instance_id)`, sorted by that pair, with factual zeros rather than omissions, `ledger_event_present` derived from what was actually appended, and every aggregate recomputed from the records. `planned_source_count = len(plan_rows)`; the three disposition counts partition the record list. `test_e0_completes_and_reconciles_all_76_planned_sources` asserts 76/76 and the three-way sum, and it passes.

## 7.3 Canonical membership — D094 §6.2/§6.3/§6.4

This is the strongest part of the candidate. Verified point by point:

- **`S_submissions` / `S_full_index`** are derived only through `census_plan_sources.observation_id` (`membership_observation_sources`), restricted to the exact accepted source IDs and field names. A non-plan-bound observation contributes nothing.
- **`U`** is `frozenset | frozenset`, `tuple(sorted(...))` — deduped and ordered by canonical numeric CIK only.
- **Corroboration** (`S_submissions ⊆ S_full_index`) is enforced via `uncorroborated = group.submissions - group.full_index`, counted **in members** (the §9.5 name's meaning), and blocks establishment.
- **Bindability**: `bindable = tuple(cik for cik in members if cik in known_registrants)`; unbindable members are counted and fail the accession closed. **No entity is ever created** — there is no `INSERT INTO census_registrants` anywhere in the projection.
- **Provenance** uses D012 `AUTHORITY_LEVEL` → `source_observation_id` → nullable `parsed_record_id` with missing sorting last (`1 if parsed_record_id is None else 0`), exactly §6.3. `first/latest_observed_at_utc` are `min`/`max` across supporting witnesses. No supporting observation is deleted.
- **Ordering / one-accession memory bound**: `_stream_membership_groups` consumes the cursor lazily and resets the accumulator at each accession boundary. Source-order independence follows from set semantics plus rank sorting.
- **Scalar/cardinality**: scalar cleared to `NULL` before the first insert when `len(bindable) > 1`; set to the sole member for an established singleton (R58's `may` narrowed to `must`); `NULL` for established multi.
- **Completeness last**: the establishment `UPDATE`s run after the whole relation loop, inside the same transaction.
- **Create-once**: `_existing_relation_row` — a byte-identical row is a collision by identity and left alone; a differing row **fails closed** with an explicit "the relation is create-once and a correction is a new run" message. No replacement write.
- **Rollback**: totality is measured and `require()`d **inside** the transaction, so an `established` completeness can never be persisted beside a broken §9.5 invariant.
- **Non-conflict of distinct valid CIKs**: `conflicting` is driven solely by the observation's `conflict_indicator`, never by cardinality.
- **Submitter non-promotion**: nothing reads a submitter field; `test_the_submitter_is_never_promoted_into_the_relation` passes.
- **Malformed evidence**: `_membership_cik` returns `None` on any value that does not normalize exactly, increments `invalid_renderings`, and never repairs by inference.

`AssociationTotality.MUST_BE_ZERO` is exactly the six §9.5 zero-fixed counts, plus the two partition identities in `violations()`.

---

# 8. R79 / R80 / R81 / R83 / R84 / R87-R89 REVIEW

**R79 — MEASURED FACT, fully satisfied.** Support-only CIKs are exactly `917`/`918`, derived from the design (not hardcoded), each an `EntitySpec` with `accessions=()`, named identically to what `company.idx` renders, created by the **production parser** from an accepted-shaped submissions object. `_R79_RECONCILIATION` is asserted as a single dict comparison and matches D095 §3's ten values exactly: `65 / 26 / 65 / 0 / 63 / 2 / 67 / 0 / 2 / 4`, with quota feasibility asserted separately. The required negative controls exist as `test_removing_a_support_only_object_fails_its_joint_accession_closed[0|1]` — one object at a time — and assert unbindable = 1, unestablished = 1, `census_registrants` count for the withdrawn CIK = 0, and that the unestablished set is **exactly** `[joint]`. These two tests are the ones that kill the true guard-removal mutant (§11).

**R80 — satisfied.** Exact constant, in `RUNTIME_ROOT_ENV_VARS` only, never applied. Mutant M5 kills exactly the two R80 tests while the other 27 `test_env_overrides.py` tests (unknown-name rejection) still pass — precisely D095 §7 item 5.

**R81 — satisfied.** Equality test present and load-bearing: mutant M4 kills exactly `test_the_catalog_constant_equals_the_acquisition_constant`. AST proof confirms `e0.py` declares no acquisition/transport import.

**R83 — satisfied.** Stale E2 variant and helper removed with a decision-citing comment; no other scenario dropped. The relocated proof exists as `test_a_malformed_full_index_cik_fails_the_projection_closed`, with the positive control `test_the_pre_association_boundary_projects_cleanly_as_the_positive_control` and `test_the_relocated_proof_uses_no_candidate_builder_or_fallback`. Mutant M2 (removing `invalid_cik_rendering_count` from `MUST_BE_ZERO`) kills exactly that test on the exact `match="invalid_cik_rendering_count"` assertion — **non-vacuous**.

**R84 — satisfied.** Asserts both the required `candidate_accession_evidence_sha256` attribution and the absence of the stale `multi_registrant` attribution.

**R87/R88/R89 — satisfied; the semantic-locus assertion is sufficiently exact.** MEASURED: 38 definitions recover in exact order; `verify_anchors` → `['M19']`; `M19.source_path == 'src/disclosure_drift/m3/candidate_snapshot.py'` (exact equality), `M19.old_anchor` == the frozen query (exact equality), `M19.semantic_locus == 'function _read_full_index_registrants (line 333)'`.

On the review question: the locus assertion is `in` (substring) rather than `==`. **I judge it sufficiently exact**, for three independently sufficient reasons: (a) `superseded` is fetched by exact key `"M19"`; (b) `source_path` and `old_anchor` are pinned by **exact equality**, and no other M1–M38 definition carries that anchor string; (c) the value is read from the immutable historical artifact D097 forbids editing, so it cannot drift. The substring form is also what R88 item 3's own wording asks for. Additionally, the test proves an **additional or different** missing anchor is rejected, using a disposable mirror with M20 deliberately drifted — asserting both `[M19, M20]` and `[M20]` cases so the equality discriminates by identity, not length. Mutant M1 (expect `M18`) kills it. This is a genuinely strong, non-vacuous correction.

---

# 9. RECEIPT V4 / IDENTITY / FREEZE / POST-FREEZE REVIEW

**Receipt v4 isolation — satisfied, structurally.** `ExecutionReceiptV4` is a **separate class**, not a mode; `_RULES_V4` is written out in full rather than derived from `_RULES_V3`, so every selection/quota/manifest/transport field is absent from the closed set entirely. `zero_network_modes` and `reason_codes` were moved **onto `_Schema`** so the shared `_check_accounting` checker consults version-scoped vocabularies — the coupling that would have made v4 global was deliberately avoided. `REASON_CODES_V4` does not enter `reasons.py`. `2.0`/`3.0` byte behavior, validators, and emitters are untouched. `test_a_v3_document_carrying_v4_only_vocabulary_is_refused` injects each of the three v4-only objects into a valid `3.0` document and requires refusal — the §12.3 item 7 mutation proof.

**Identity — satisfied.** `_IDENTITY_EXCLUDED = {"terminal_record_id", "result_token"}`; `result_token` is derived *after* the identity and contains it, so both must be excluded. `_event_digest` omits `event_sha256` from its own preimage. Mutant M7 (re-including `terminal_record_id`) kills three identity tests plus one error — the exclusion is load-bearing.

**Ledger — satisfied.** Hash-chained, contiguous-sequence, canonical-form, closed event vocabulary, closed per-event `details` projection (required *and* forbidden keys both checked), and a structural non-leak check on detail values with a correct carve-out for `relative_path`. `read_event_ledger` detects truncation (missing trailing newline; count mismatch against the terminal), reordering (non-contiguous sequence), and mutation (recomputed digest / predecessor mismatch).

**Freeze order — correct.** Receipt → fsync → `EXECUTION_RECEIPT_WRITTEN` → terminal bound to a ledger head that will not move → `write_once` → **reopen read-only and reproduce** identity and token from persisted bytes. `_load_terminal` verifies the ledger *first*, then the record — correct dependency direction. No `TERMINAL_FROZEN` event, per §10.2.

**Post-freeze defect preservation** is covered by `test_a_post_freeze_defect_is_preserved_and_never_repaired`.

**However — MAJOR-1 lives here.** The freeze tail is correct; the *failure* tail is not. See §12.

---

# 10. OPERATOR / CLI / PRIVATE-PATH / NETWORK CONTAINMENT

**MEASURED FACT — exit boundary, exercised through the real CLI** (`.venv/bin/disclosure-drift`, `DISCLOSURE_DRIFT_EVIDENCE_ROOT` unset, and separately set to a synthetic `mktemp` root; the accepted private root was never resolved or opened):

| Invocation | env unset | synthetic root |
|---|---|---|
| `m3 prepare-e0-catalog --mode execute` | **3** | **3** |
| `m3 offline-parse --mode execute` | **3** | **3** |
| `… --mode preflight` (both) | 1 | 4 |
| `… --mode verify` (both) | 1 | 4 |
| `--mode force` | 2 | — |

Exit `3` is returned **with and without** the environment variable — because `_operator_command` performs the activation check *before* `resolve_evidence_root`, with an in-code rationale that is exactly right: resolving first would let a set variable become a precondition for learning the stage is disabled. `StageNotEnabledError` is its own class so no generic handler can convert "not authorized" into "gate failed". The synthetic root contained **zero** entries afterward — preflight and verify created nothing.

**No enabling door exists.** `_require_activation` is the single gate; no flag, environment value, ambient file, preflight result, verify result, catalog state, receipt, or namespace reaches it. Mutant M3 (setting the constant to a token) kills `test_both_activation_constants_are_none_in_the_shipped_source` and the `exit 3` test.

**Private-path non-leakage.** The resolved root is never returned to `cli.py`; `PreflightReport.lines` and `VerifyReport.lines` render counts, digests, enum tokens, and root-relative names only; `EvidenceRootUnsetError` names the *variable* and the rule, never a value; `OSError` is reported by class name only because it ordinarily carries a filename. Ledger `details` are checked field-aware (not by a blanket path detector), per §12.3 item 11.

**Network — request/attempt ceiling 0.** I made zero network, SEC, HTTP, DNS, socket, package-installation, fetch, pull, or remote-Git requests. In the code: AST-verified that `e0.py` declares no prohibited import at module or function scope. See OBSERVATION-1 for the honest transitive-closure nuance.

**Docs describe the executable code exactly.** I spot-checked the exit table, write sets, namespaces, both-constants-`None`, the read-only preflight/verify claim, and the sixteen-table footprint in `e0_execution_record_spec.md`, `operator_runbook.md` (step 28a), and `sec_data_dictionary.md` §16 against the code. All matched. The docs notably *avoid* overclaiming about verify's catalog-state validation.

---

# 11. TARGETED TESTS AND DISPOSABLE MUTATION EXPERIMENTS

All test execution used repository Python 3.12 (`.venv/bin/python`, 3.12.13) with `DISCLOSURE_DRIFT_EVIDENCE_ROOT` unset via `env -u`. All mutation used a `git archive HEAD | tar -x` copy under a `mktemp -d` directory, import-shadowed via `PYTHONPATH` (verified: `disclosure_drift.__file__` resolved into the copy). **No repository byte was written.** Copy and all `/tmp` artifacts deleted at the end.

## 11.1 Targeted suite — MEASURED FACT

```
env -u DISCLOSURE_DRIFT_EVIDENCE_ROOT .venv/bin/python -m pytest \
  tests/unit/test_m3_e0.py tests/unit/test_m3_3_execution.py tests/unit/test_audit_tooling.py \
  tests/unit/test_m3_receipt.py tests/unit/test_m3_candidate_snapshot.py \
  tests/unit/test_m3_offline_parse.py tests/unit/test_env_overrides.py \
  tests/unit/test_migration_provenance.py tests/integration/test_m3_cli.py \
  tests/integration/test_cli.py -p no:randomly -q
```
→ **727 passed, 0 failed. Elapsed 147.36 s.**

## 11.2 Mutation battery — MEASURED FACT

| # | Mutation | Expected | Observed | Tests killed |
|---|---|---|---|---|
| M1 | `_SUPERSEDED_LIVE_ANCHOR` `M19`→`M18` | FAIL | **FAIL** | `test_every_live_anchor_but_the_superseded_m19_resolves_against_the_live_target` |
| M2 | drop `invalid_cik_rendering_count` from `MUST_BE_ZERO` | FAIL | **FAIL** | `test_a_malformed_full_index_cik_fails_the_projection_closed` (on the exact `match=` string) |
| M3 | `PRE_E0_CATALOG_TRANSITION_AUTHORITY = "OWNER-TOKEN"` | FAIL | **FAIL** | `test_both_activation_constants_are_none_in_the_shipped_source`, `test_execute_returns_exit_three…` |
| M4 | drift `OPERATIONAL_CATALOG_RELATIVE_PATH` | FAIL | **FAIL** | `test_the_catalog_constant_equals_the_acquisition_constant` |
| M5 | remove `EVIDENCE_ROOT_ENV` from `RUNTIME_ROOT_ENV_VARS` | FAIL + unrelated still rejected | **FAIL**, exactly 2 R80 tests; other 27 pass | `test_the_evidence_root_is_a_recognized_runtime_root_and_not_an_override`, `…changes_no_configuration_value_and_is_never_rendered` |
| M6 | authorizer `SQLITE_DENY`→`SQLITE_OK` | FAIL | **FAIL** | 3× `test_every_excluded_write_class_is_refused_by_the_authorizer` |
| M7 | re-include `terminal_record_id` in its own preimage | FAIL | **FAIL** | `test_the_transition_verify_reproduces_the_frozen_identity`, `test_a_terminal_record_validates_and_its_identity_reproduces` (+1 error) |
| M8 | drop `and unbindable == 0` only | FAIL | **PASS** — *see below* | none |
| **M8b** | drop **both** `unbindable == 0` **and** `len(bindable) == len(members)` | FAIL | **FAIL** | `test_removing_a_support_only_object_fails_its_joint_accession_closed[0]` and `[1]` |

**M8 requires honest reporting.** My first mutant did not kill anything — but the cause is not a coverage gap. `unbindable = len(members) - len(bindable)`, so `unbindable == 0` and `len(bindable) == len(members)` are logically **identical** conditions; removing one leaves the guard fully intact. Removing **both** (M8b, 303 tests, 30.83 s) kills exactly the two R79 negative controls. The unbindable fail-closed rule is genuinely load-bearing. The redundancy is recorded as OPTIMIZATION-1.

**Two baseline "failures" in the disposable copy are harness artifacts, not defects:** `test_the_real_head_tree_and_parent_verify_against_this_repository` and `test_the_helper_exits_nonzero_when_a_check_fails` require a `.git` directory, which `git archive` extraction does not produce. Both pass in the authoritative repository. I state this rather than let the counts read as failures.

## 11.3 Two bounded failure-window experiments — MEASURED FACT

**Experiment A — transition postcheck window.** Made the `POSTCHECK_PASSED` append fail (the same window the pre-existing-content equality refusal occupies). Observed:
```
POSTCHECK_PASSED durable: False
post_preexisting_content_sha256 present: True
VALIDATOR VERDICT: REFUSED -> TerminalValidationError
  post_preexisting_content_sha256 is present but this status and event set does not permit it
transition_verify: determined=True passed=False
```
Elapsed 0.46 s.

**Experiment B — E0 `VALIDATION_PASSED` window, triggered through a *genuine gate*** (no ledger injection): forced the input-observation-set digest reproduction check to fail. Observed:
```
VALIDATION_PASSED durable: False
TERMINAL status: failed;  post_integrity present: True
VALIDATOR VERDICT: REFUSED -> TerminalValidationError
  post_integrity is present but this status and event set does not permit it
e0_verify: determined=True passed=False
```
Elapsed 0.56 s.

## 11.4 Elapsed time per process

| Process | Elapsed |
|---|---|
| Targeted suite (10 modules, 727 tests) | 147.36 s |
| Mutation battery (7 baselines + 8 mutants) | ≈35 s total; individual runs 0.14–3.16 s |
| M8b true guard-removal (4 modules, 303 tests) | 30.83 s |
| Experiment A (transition window) | 0.46 s |
| Experiment B (E0 window) | 0.56 s |
| CLI operator-boundary sweep (13 invocations) | < 5 s |
| Candidate's own `make check-fast` pytest (inspected, **not** rerun) | 79.40 s |

---

# 12. FINDINGS BY SEVERITY

## MAJOR-1 — A failure inside a status/event-conditioned window writes a durable terminal record that its own §8.1/§9.2 validator refuses, and the write failure is silently suppressed

**CONFIRMED — reproduced twice, once through a genuine production gate.**

`src/disclosure_drift/m3/e0.py:2731` (transition), `:3098` and `:3107-3112` (E0).

D094 §8.1 and §9.2 make presence *exact*: `post_preexisting_content_sha256` is permitted only when `POSTCHECK_PASSED` is durable; `post_integrity`/`table_hashes`/`plan_parser_state_hash`/`e0_catalog_state_sha256` only when `VALIDATION_PASSED` is durable; `association_totality` only when `ASSOCIATIONS_MATERIALIZED` is. In all three cases the implementation assigns the field to the terminal dict **before** appending the conditioning event. `_disclose_failure` (`:2513-2515`) clears only `post_migration_chain`/`post_integrity`/`applied_migrations`, and only when `catalog_state_observed` is **False** — so none of these windows is cleaned up. `_freeze` then writes the record `write_once` and *does* reopen and validate it, but `_disclose_failure` wraps `_freeze` in `with suppress(E0Error, OSError)` (`:2539`), so the `TerminalValidationError` is swallowed and the malformed record is left durable and **create-once**.

**Failure scenario (E0, no injection required):** E0 executes; the post-parse reproduction of `input_observation_set_sha256` disagrees with the pre-write value — a first-class E0 identity gate. `post_integrity` has already been set; `VALIDATION_PASSED` has not been appended. `e0_terminal.json` is written and cannot be validated by `validate_e0_terminal`. `e0_verify` returns `determined=True, passed=False`. The run's durable record of *why it failed* is itself unreadable, and being create-once it can never be corrected in place.

**Transition analogue:** the refusal "the transition changed a pre-existing application row" — precisely the anomaly the pre-existing-content digest exists to detect — lands in the same window.

**Why MAJOR, not BLOCKER:** nothing reads as success, no catalog state is corrupted or concealed, the exception still propagates, and verify fails closed. **Why MAJOR, not MINOR:** exact representability of every complete/failed/interrupted/hard-killed run is D094 §3.4's conflict **C4** — one of the four the redesign exists to resolve — and §12.3 family 8 requires proving "every crash boundary". The only failure test (`test_a_failure_after_the_namespace_exists_is_disclosed_and_preserved`) injects at the *backup* boundary, where `catalog_state_observed` is False; the entire `catalog_state_observed = True` disclosure path is untested.

**Correctable inside the authorized path set** (`e0.py` + `test_m3_e0.py`): clear each conditioned field in `_disclose_failure` whenever its conditioning event is absent from the ledger — mechanically, by deriving presence from the ledger's actual event set rather than from assignment order — and stop suppressing a terminal-validation failure in `_freeze`, or at minimum surface it.

## MAJOR-2 — D094 §5.2 predicate 3 is not implemented, while the code claims complete predicate coverage

**CONFIRMED.**

`src/disclosure_drift/m3/e0.py:2168` (`transition_preflight`), `:2791` (`_recheck_under_lease`).

D094 §5.2 predicate 3 requires that "the accepted M3.2 acquisition completion receipt and catalog binding validate", and §5.3 item 2 requires predicates **1–8** and 10–13 to be repeated under the lease — so predicate 3 is required in both places. I enumerated every `refusals.append` in `e0.py` and mapped all thirteen predicates: twelve are implemented; predicate 3 has **no** implementation. `rg` over `src/` finds no `completion_receipt`, `acquisition_completion`, or `catalog_binding` surface anywhere, and `e0.py` references no receipt other than the v4 builder and `inspect_receipt` inside `_verify`. The omission is **not disclosed** in `Docs/m3/e0_execution_record_spec.md`, `Docs/m3/operator_runbook.md`, or any code comment.

Meanwhile `transition_preflight`'s docstring states: *"Evaluate every Decision 094 §5.2 predicate."* That claim is false as written.

**Failure scenario:** an operator runs `m3 prepare-e0-catalog --mode preflight` against a private root whose M3.2 acquisition completion receipt is missing, invalid, or bound to a different catalog. Preflight returns exit `0` and prints "preflight: PASS". Sol/GPT relies on that PASS when drafting the later exact transition instrument, believing all thirteen predicates were validated. The under-lease recheck reproduces the same twelve and also passes, and the transition proceeds against a catalog whose acquisition provenance was never bound.

**Why MAJOR:** it is one of thirteen predicates in an accepted ruling whose own heading is "**Preflight — all predicates required**"; it is a provenance/governance binding, not a convenience check; the docstring overclaims; and it is exactly the kind of item D094 §12.1 says to STOP on rather than silently omit. **Why not BLOCKER:** both execute modes are unreachable today, preflight creates nothing, and the twelve implemented predicates are individually sound.

**Note on predicate 4:** I initially suspected the applied name/checksum half was also missing. It is not — `storage/sqlite.connect()` calls `verify_applied_migrations()` on every open, so a drifted ledger raises before inspection. I record this so Sol does not re-derive it.

## MINOR-1 — `transition_preflight`'s docstring asserts coverage the function does not have

`e0.py:2174`. Distinct from MAJOR-2's substance: even after predicate 3 is implemented or formally dispositioned, a docstring asserting complete coverage of an accepted thirteen-predicate list should either be true or name its exception. Low cost to fix; carries real reviewer-trust weight in this repository's idiom.

## MINOR-2 — `verify` does not validate catalog state

`e0.py:3224-3289`. D094 §7.2's verify row lists "catalog state" among what verify validates; `_verify` never opens the catalog. A complete terminal therefore verifies PASS even if the accepted catalog has since drifted from the recorded `post_migration_chain`. Practical exposure is limited (E0 preflight independently re-measures the chain, and §5.4's "may inspect" is permissive), and the code docstrings honestly omit the claim — which is why this is MINOR and not a MAJOR overclaim.

## MINOR-3 — the under-lease recheck suppresses a refusal by English substring match

`e0.py:2810-2812`: `if "writer holds the catalog lease" not in refusal`. The filter's correctness depends on message text, and its *sufficiency* depends on an unasserted platform property: the second lease refusal ("the recorded catalog writer lease state is 'held'") is unreachable only because `flock(LOCK_SH|LOCK_NB)` fails first against the process's own exclusive lock on a different descriptor. Both drift modes fail **closed** (every real execute would refuse), so this is MINOR — but a structural signal (e.g. a typed refusal code, or passing `under_lease=True` into `_shared_preflight`) would remove a fragile coupling from the one path that must not spuriously refuse a real authorized transition.

## MINOR-4 — §5.2 predicate 10 is partially implemented

`e0.py:2147-2153`. The predicate requires the namespace parent to be "an existing non-symlink directory **owned by the operator**". The implementation checks symlink-ness and directory-ness *only if the parent exists* (`create_run_namespace` creates it otherwise), and performs no ownership (uid) check. Both deviations are in the permissive direction relative to the stated predicate.

## OPTIMIZATION-1 — redundant establishment condition

`offline_parse.py`: `and unbindable == 0` and `and len(bindable) == len(members)` are logically identical, since `unbindable = len(members) - len(bindable)`. Measured: removing either alone kills no test; removing both kills the two R79 negative controls. Harmless defensive duplication — reported only because it made one mutant read as a false negative, which a future reviewer would otherwise have to re-derive.

## OBSERVATION-1 — transitive network closure

`e0.py` and `offline_parse.py` declare **no** prohibited import (AST-verified, module and function scope). Transitively, importing either reaches `disclosure_drift.m3.acquisition`, `sec.http_client`, `sec.transport`, `sec.rate_limit`, `socket`, and `urllib` — via `disclosure_drift/m3/__init__.py`, which eagerly re-exports the acquisition foundation. **MEASURED:** `closure(m3.e0) == closure(m3)` is `True` and `closure(m3.offline_parse) == closure(m3)` is `True`, so these modules add **no new** edge; and no HTTP client library (`httpx`, `requests`, `urllib.request`) is reachable at all. The implementation discloses this explicitly in its own test docstring rather than asserting a bare `sys.modules` claim that would have been untrue. Importing is not constructing; both terminal validators refuse a nonzero request or attempt count. Not a defect — recorded so Sol is not surprised by a naive `sys.modules` probe.

## OBSERVATION-2 — no `AGENTS.md`

The review packet names "Repository AGENTS.md" as controlling authority at precedence 5. **MEASURED:** no `AGENTS.md` exists in the repository (D095 §2 item 4 also cites it). `CLAUDE.md` occupies that role and I applied it. No impact on any finding; flagged because the packet's authority list should match the tree.

## OBSERVATION-3 — `change_impact_map.md` predates D097

The new section is headed "Decisions 094–096" and does not name D097 or `tests/unit/test_audit_tooling.py` as a touched surface. This is a *correct* governance consequence — D097 R88 restricted the executable edit to that one test file, so the map could not be updated — but it leaves the map incomplete relative to the shipped commit. Owner-owned to resolve.

## OBSERVATION-4 — the D094 §6.5 residual is intact

`sec/census_orchestrator.py:943` still converts the nullable scalar with `int()`. Unchanged and unreachable, exactly as D094 §6.5 discloses. Correct handling; recorded so it is not mistaken for a miss.

---

# 13. PROHIBITED-ACTION PROOF

| Prohibition | Proof |
|---|---|
| No repository byte or Git ref altered | MEASURED — HEAD `1e20021…`, tree `7d5f3aa9…`, `git status --porcelain` empty, `git diff --stat` and `--cached --stat` empty, no untracked files, no tags at HEAD, `git stash list` empty, one worktree. `git reflog -3` head is still the candidate commit — this session added no entry. Verified at entry, between experiments, and at handoff. |
| No Edit/Write/patch to the repository | MEASURED — every `Write` call in this session targeted `/tmp` only (`/tmp/rev_mutants.sh`, `/tmp/exp_postcheck_window.py`, `/tmp/exp_e0_window.py`). No `Edit` call was made. |
| Disposable experiments contained | MEASURED — `mktemp -d` → `git archive HEAD \| tar -x`; import shadowed via `PYTHONPATH`; a pristine sibling copy restored every mutated file; the copy and all `/tmp/mut_*.log`, `/tmp/exp_*.py`, `/tmp/rev_mutants.sh` were deleted. `ls -d /tmp/d094rev.*` → no matches. Exact mutations recorded in §11.2. |
| No accepted private-root discovery/resolution/print/access | MEASURED — `DISCLOSURE_DRIFT_EVIDENCE_ROOT` was `env -u` unset for every test command. The only root-set invocations used a fresh `mktemp -d` synthetic directory, whose path was never printed and which was removed. No accepted private path appears anywhere in this report. |
| No accepted catalog open, migration, transition, E0, linkage diagnostic, persistence bridge, E1/E2/M3.4, or migration `0016` | MEASURED — no accepted catalog was located or opened. All catalog work used disposable `tmp_path` fixtures inside the copy. Migration inventory is unchanged at `0001`–`0015`; `0016` absent. |
| Activation constants never enabled in authoritative source | MEASURED — `e0.py:150` and `:163` remain literally `None` at HEAD; the file's SHA-256 still matches D097 §2's `6de8aae9…`. The M3 mutant existed only inside the deleted disposable copy. |
| No network / SEC / HTTP / DNS / socket / acquisition / package install / fetch / pull / remote Git | MEASURED — zero such actions. No `WebFetch`/`WebSearch`, no `pip`/`uv`, no `git fetch`/`pull`/`push`/`ls-remote`. Request ceiling 0, attempt ceiling 0. |
| No `make check-fast` rerun, stage-gate, push, tag, release, publication | MEASURED — `/tmp/d097_checkfast.log` was **inspected only**; its SHA-256 matched the expected `9e0a3a6a…`. No `make` target was invoked. |
| No implementation fix | MEASURED — every finding is reported here; none was corrected. |
| No subagent / workflow / delegation / second reviewer | MEASURED — no Agent, Workflow, or Task tool call in this session. |
| No raw evidence, secret, identity value, or private absolute path in output | Verified by inspection of this report. |
| Did not write the durable review path | MEASURED — `Docs/m3/reviews/m3_3_d094_pre_e0_implementation_independent_review_1e20021.md` was not created. |

---

# 14. OWNER RECOMMENDATION AND EXACT NEXT ACTION

**RECOMMENDATION (advisory only — I make no acceptance, transition, or E0 authorization):**

> **Do not owner-accept this implementation as-is. Return it for one bounded correction of MAJOR-1 and an owner disposition of MAJOR-2.**

The candidate is substantively strong. The membership derivation, the sixteen-table footprint and its authorizer, the consumer rule, the identity and freeze law, the receipt-v4 isolation, the R79 fixture correction with real negative controls, the R83 relocated proof, and the operator boundary are all independently verified correct and — importantly — **non-vacuously proven**: eight of nine mutants killed exactly the tests they should, and the ninth was my error, not a coverage gap. On the packet's mandatory questions A–K the answer is "yes, correctly implemented" everywhere except the two MAJOR items and the four MINOR gaps.

But D096 §6.4 declared the autonomous loop exhausted, and D097 R89 was an explicit one-file exception. So the disposition of these findings is an owner decision that I cannot pre-empt, and I deliberately do not recommend which instrument Sol should use.

**Suggested exact next action, for Sol/GPT to adjudicate:**

1. **Preserve the candidate.** HEAD `1e20021…` is intact, clean, and unpushed. Nothing needs undoing.
2. **Adjudicate MAJOR-2 first**, because it is a *ruling-interpretation* question, not a coding one: either (a) D094 §5.2 predicate 3 is implementable and must be implemented, or (b) it is superseded/inapplicable (e.g. because the E0-side transition-terminal binding already carries the provenance chain) and should be **explicitly dispositioned in a bounded correction record**, with the `transition_preflight` docstring corrected either way. A silent omission is the one outcome that should not stand.
3. **Adjudicate MAJOR-1** as a bounded, mechanical correction confined to `src/disclosure_drift/m3/e0.py` and `tests/unit/test_m3_e0.py` — both already inside D094 §12.1 — deriving conditional-field presence in `_disclose_failure` from the ledger's actual event set, and adding the missing `catalog_state_observed = True` failure-boundary tests that §12.3 family 8 implies.
4. **Consider folding MINOR-1 through MINOR-4** into whatever instrument covers the above; each is small and none requires a new path.
5. **Do not** activate either constant, apply `0014`/`0015` to the accepted catalog, run the transition, run E0, run the D093 linkage diagnostic, create `0016`, or begin E1/E2/M3.4. E0 remains **HELD**. Network, SEC, and HTTP authority remain **NONE** at request and attempt ceilings **0**.

If Sol judges MAJOR-1 and MAJOR-2 to be acceptable residuals under an explicit disclosed disposition rather than defects requiring code change, then the remainder of this review supports acceptance — but that judgment is the owner's, and this report does not make it.

```
M3_3_D094_PRE_E0_IMPLEMENTATION_INDEPENDENT_REVIEW_FAIL
BLOCKER: 0   MAJOR: 2   MINOR: 4   OPTIMIZATION: 1   OBSERVATION: 4
M3_3_E0_OPERATIONAL_STATE: HELD
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: NO
M3_3_E0_EXECUTION_AUTHORIZATION: NO
NETWORK / SEC / HTTP: NONE      REQUEST_CEILING: 0
REVIEWER AUTHORIZED NOTHING; OWNER ADJUDICATION REQUIRED
```
