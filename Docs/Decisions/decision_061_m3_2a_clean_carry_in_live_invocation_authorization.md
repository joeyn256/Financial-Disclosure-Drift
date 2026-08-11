# Decision 061 — M3.2A Clean Carry-In Live-Invocation Authorization (T5)

**Date:** 2026-08-10
**Status:** ACCEPTED — OWNER LIVE-OPERATION AUTHORIZATION 2026-08-10
**Authority classification:** `M3_2A_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZED`
**Type:** Owner **live-operation authorization** record. It is the separate, explicit instrument the
accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §8 requires at
rung **T5**, and it is the act
[Decision 060](decision_060_m3_2_carry_in_authority_mint.md) §15 named as
`OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET`. It authorizes **exactly one**
future **T6** clean carry-in M3.2A acquisition invocation, under a frozen command contract, frozen
paths, a frozen materialization procedure, and a frozen network transition. It changes no executable,
test, migration, configuration, contract, template, or reason-code byte, opens no private or governed
operational state, touches no USB archive, makes no network or SEC contact, and performs no
operational act.

**Non-self-executing.** **T5 authorizes; T5 does not execute.** This record **consumes no carry-in
authority, materializes no artifact, starts no run, enables no network, and contacts no SEC host.**
The authorized invocation is performed only under a **separate later owner execution packet**
(§20), exactly as [Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md)
separated its own authorization from its execution. **Authorization is not execution, and
"T5 authorizes T6" never means "T6 has occurred."**

**Amends:** nothing in place. Decisions 001–060 remain **byte-unchanged**; Decision 050, Decision 055,
Decision 059, and Decision 060 specifically are preserved **byte-identical**.
**Narrowly supersedes:** exactly two things, and nothing else (§12, §15) — the **current-state
statements that no T5 clean carry-in instrument exists** and that **issuing it is the next authorized
action**, in [Decision 060](decision_060_m3_2_carry_in_authority_mint.md) §§14–15, in
[`Docs/Decisions/decision_registry.md`](decision_registry.md), and in
[`Milestones/STATUS.md`](../../Milestones/STATUS.md); and those
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §9 **pre-live
conditions rendered impossible by accepted history**, **for this clean carry-in run only** (§12).
Every superseded statement was accurate when written and is preserved as **historical**; **nothing
else in any accepted record is superseded, weakened, or reopened.**
**Preserves unchanged:** the cumulative M3.2A ceiling **801** and the frozen 75-logical-request plan
at SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; the accepted
historical seed **1** and **SEC request consumption 1 of 801**; the historical run's **permanent
non-resumability** and its `UNDETERMINED` recovery classification; the absence of a terminating
receipt; Decision 050 §8's predecessor-receipt requirement for **every resume**; Decision 051 §9's
permanent no-resume ruling; Decision 055 §§5–9 in full, including burn-before-wire; Decision 057
§12's permanent prohibition on re-adoption; the minted authority of Decision 060 and its
**UNCONSUMED** state; **M3-L14 `CLOSED — DECISION 056`**; **M3-L16 `CLOSED — DECISION 059`**;
**M3-L15** byte-for-byte; migrations `0001`–`0013`; and every route, host, method, spacing, content,
provenance, leakage, evidence-preservation, determinism, and fail-closed rule not expressly addressed
here.
**Related:** [Decision 060](decision_060_m3_2_carry_in_authority_mint.md) §§5–9, 14, 15;
[Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md) §§3, 6, 11;
[Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) §§5, 6.1–6.5, 7, 9;
[Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) §§5–7;
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) §§5, 6, 9, 12;
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §§5–10;
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §§5, 8, 9, 11, 12, 16, 17, 20, 21;
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) steps 16–18, 26, 27, 27a;
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md) **M3-L15**, **M3-L16**;
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** what this record does and does not do (§1); the owner instrument, the stop adjudication,
and the private-parameter ruling (§2); authority verification (§3); the independently derived current
action (§4); ruling **061-A**, the frozen public command contract (§5); ruling **061-B**, the private
parameter rule (§6); ruling **061-C**, the fixed public relative paths (§7); ruling **061-D**,
carry-in materialization (§8); ruling **061-E**, the network window (§9); ruling **061-F**,
burn-before-wire and the one-invocation boundary (§10); ruling **061-G**, the T6 preflight (§11);
ruling **061-H**, Decision-050 T5 exhaustion and narrow supersession (§12); ruling **061-I**,
historical request accounting (§13); ruling **061-J**, executor exclusivity and the writer lease
(§14); ruling **061-K**, the bounded operator-runbook correction (§15); what T5 does not authorize
(§16); the limitations disposition (§17); the path and publication boundary (§18); the recorded status
(§19); and the formal outcome and exact next authorized action (§20).

---

## 1. What this record does, and what it does not

**It does:**

- record the owner instrument, the owner's adjudication of the prior underivability stop, and the
  owner's **private-parameter and path-binding ruling** that supersedes the earlier over-strict
  literal-path requirement (§2);
- verify the controlling authority live, at exact identities, before authorizing (§3);
- confirm **independently from repository authority** that the current authorized action is
  `OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET` (§4);
- **freeze the exact public command contract** for the one future T6 invocation, verified against the
  frozen CLI by parse-only inspection (§5);
- fix the **two named private T6 parameters**, their uniquely constrained meanings, and their
  resolution and validation rules — **without disclosing any private absolute path** (§6);
- **fix every public evidence-root-relative path** the invocation uses: plan, data root, catalog,
  receipt, and carry-in authority (§7);
- fix the exact **carry-in materialization procedure** and its fail-closed conditions (§8);
- fix the exact **network transition**, its scope, its enable and disable points, and its failure-path
  withdrawal (§9);
- restate **burn-before-wire** and bound the authorization to **exactly one** invocation with no
  retry, no reissue, and no second clean run (§10);
- freeze the **complete T6 preflight**, waiving none of it (§11);
- record that Decision 050's T5 grant is **EXHAUSTED and NON-REUSABLE**, and narrowly supersede only
  those of its §9 pre-live conditions that accepted history has made impossible (§12);
- preserve **SEC consumption 1 of 801** and forbid any zero-baseline restatement (§13);
- carry the **project-scoped executor exclusivity** definition and the writer lease into T6 (§14);
- authorize and bound the **operator-runbook command-form correction** (§15);
- state the authority boundary after T5 and name the exact next bounded owner action (§§16, 20).

**It does not:**

- **execute** the authorized invocation, or any part of it;
- **consume** the carry-in authority, or create its consumption checkpoint;
- **materialize** the carry-in artifact bytes anywhere;
- **create** the operational catalog, the data root, the clean-run directory, or any receipt;
- enable network, DNS, HTTP, or SEC contact, or change one tracked configuration byte;
- authorize **M3.2B**, **Gate H**, a **second adoption**, a **retry**, a **replay**, a **second clean
  run**, or a **resume** of the historical run;
- open, read, or mutate the operational catalog, data root, raw object, lineage intent, projection
  file, private evidence bundle, or USB archive;
- alter any limitation's state, close any limitation, or reopen a closed one;
- resolve the `9475eb3d…` publication-1 ratification question, which remains a **separate standing
  owner matter**, unresolved and non-blocking (Decision 060 §12, preserved);
- create any production, test, migration, configuration, reason-code, contract, or template byte;
- claim M3.2 completion or live readiness. **M3.2 is NOT COMPLETE**, and **live readiness is NOT
  CLAIMED.**

## 2. The owner instrument, the stop adjudication, and the private-parameter ruling

The authorization proceeds under the owner instrument:

```text
OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET
```

issued by the project owner (Sol/GPT role) on **2026-08-10**, and naming this stage as **one** bounded
owner live-operation authorization act with **no execution content**.

### 2.1 The prior stop, adjudicated

A first attempt at this stage **stopped before publication** and wrote **zero repository bytes**,
created no Decision 061, created no commit, and performed no push. Its result token was
`M3_2_DECISION_061_T5_CLEAN_CARRY_IN_LIVE_AUTHORIZATION_STOPPED`. The owner adjudicated it:

```text
M3_2_DECISION_061_T5_UNDERIVABILITY_STOP_OWNER_ACCEPTED
```

The stop **correctly obeyed** its packet. Its three substantive findings are resolved here rather than
dismissed: **BLK-1** (the exact command was underivable) is resolved by §§5–7; **MAJ-1** (the carry-in
materialization path was unfixed) is resolved by §8; **MIN-1** (the operator runbook's command forms
omitted mandatory CLI arguments) is resolved by §15.

### 2.2 The private-parameter and path-binding ruling

```text
M3_2_DECISION_061_T5_PRIVATE_PARAMETER_AND_PATH_BINDING_OWNER_RULING
```

The earlier requirement that a **tracked** T5 instrument contain a literal, placeholder-free command
**including private absolute paths** was over-strict and is **superseded**. It could not be satisfied
without violating standing authority: contract §16 forbids any tracked path from containing private
evidence, contract §20 confines evidence to the owner-controlled external root, Decision 047-I forbids
the identity or private values entering an artifact, and `make hygiene` enforces it.

**Public T5 governance MUST NOT disclose private absolute paths.** A T5 instrument **may and should**
freeze an executable **parameterized** command in which private T6-local paths are represented by
owner-defined shell variables, provided all five conditions hold — and here they do:

1. the semantic value behind each variable is **uniquely constrained** (§6);
2. its **creation or resolution procedure is frozen** (§6);
3. **T6 validates it before use** (§6, §11);
4. **substitution cannot change any governed public binding** — window, plan hash, ceiling, seed,
   route allocation, run id, and every relative path are literal in §§5 and 7 and are not reachable by
   either variable;
5. **literal private path values never enter Git and never enter a sanitized report.**

This follows the accepted M3.2 live-operation precedent: Decision 050 §6 item 7 — the only prior T5
grant — recorded the invocation as
`python -m disclosure_drift m3 acquire … --window M3.2A --live …`, deliberately omitting private
values from public governance.

### 2.3 The ratified prerequisites

The six prerequisite facts the instrument recorded are **already owner-accepted** and are
independently confirmed by the repository surfaces cited at §3:

```text
M3_2_DECISION_057_ONE_SHOT_ORPHAN_ADOPTION_SUCCESS
M3_2_DECISION_057_FRESH_POST_EXECUTION_VERIFICATION_OWNER_ACCEPTED
M3_2_DECISION_059_FRESH_ZERO_MINOR_PUBLICATION_VERIFICATION_OWNER_ACCEPTED
M3_2_DECISION_060_CARRY_IN_AUTHORITY_MINT_SUCCESS
M3_2_DECISION_060_FRESH_ZERO_MINOR_CARRY_IN_MINT_VERIFICATION_PASS
M3_2_DECISION_060_FRESH_ZERO_MINOR_CARRY_IN_MINT_VERIFICATION_OWNER_ACCEPTED
```

Decision 055 §9 (Path B) required the executed, verified, and accepted orphan adoption **before a
carry-in artifact may be minted or consumed**; Decision 059 §5 records that condition satisfied, and
Decision 060 minted the authority on that basis. The remaining contract §8 rung is this one.

## 3. Authority verification

The controlling authority was re-read **in full** before this record was written, at these exact
identities, verified live at the recording baseline `cabfbe8dea91aa7fb8126933a87ccdfa4640606d`
(branch `main`, `HEAD == origin/main` from the local ref, clean index and worktree, ahead/behind
`0/0`, no tag at `HEAD`, tree `ae141a87b51e4417874de57da7859f67df364426`, parent
`fabd86ac0f881c416f77b5b3e5d7cad6f0383576`):

| Authority | SHA-256 |
|---|---|
| [Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) | `16d2445676db0c80d4e356bc3db01a2c2e667864e9f03de3a9c1cf500e0ea13e` |
| [Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) | `0de413af2f284f46bf1f213bb1cccc3c871701b88678cc64d8c5b161ebb3cff0` |
| [Decision 053](decision_053_m3_2_interrupted_run_closure_procedure_authorization.md) | `1380324b52c8597a605e625683d2780bac72d8459de12081e9e874ee7f110f78` |
| [Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) | `43c5ae4612a4e22f06ba53cf20913ba456c8a4e0f0e33397c012cdd32966727c` |
| [Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md) | `6af4a8c8392542cfae7d1454747778cfb3fe4c12be8bb50becc3d6d29cee0ff5` |
| [Decision 060](decision_060_m3_2_carry_in_authority_mint.md) | `2ef2c31fc49d81ada9909563499e5fb202b504e4b2c692f4ad4099108c259c23` |
| [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) | `f8398a146b08476a270fd30f3bd53b557564ebbb9aa577ad32d72434361b4875` |
| [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) | `bb2398aea327edc7186aa2d500e2ea6200e127cd8c3dcdc4ab205516057be5e7` |
| [`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) | `90520f3af9339937da740e0278b54a04b5a2aa9b85635a8105d19b7037a872ea` |
| [`Docs/Decisions/decision_registry.md`](decision_registry.md) | `edbc8be105a26973aac8646c29c8e64931ab861a38d78c49a510fc4145f94e4d` |
| [`Milestones/STATUS.md`](../../Milestones/STATUS.md) | `027ec674280c55b73207f28a3f813ec492657ff57a2dfc62a99f1fadceb584da` |

**The chain is self-checking, not merely restated.** Five of those recompute exactly to values a prior
accepted record independently fixed: Decision 055 §3 records the Decision 050, 051, and 053 hashes
`16d2445676…`, `0de413af2f…`, and `1380324b52…`; Decision 060 §3 records the Decision 055 and
Decision 059 hashes `43c5ae4612…` and `6af4a8c839…`, and the contract hash `f8398a146b…`. All match,
confirming that no accepted record drifted between Decision 060's publication and this one.

The register, the registry, the ledger, and the runbook are inside this recording's authorized
envelope (§18), so their identities necessarily change with the commit that publishes this record;
the register is nonetheless **not edited** (§17). That is the same convention Decision 055 §3,
Decision 059, and Decision 060 §3 followed, and it is a property of self-reference rather than a drift.

Tracked network configuration was verified in [`configs/project.yaml`](../../configs/project.yaml):
`network.enabled: false`, `network.m3_acquire_enabled: false`, and `companyfacts.enabled: false` — all
three still `false`.

The frozen CLI was read **read-only** and exercised **parse-only** to bind this authorization to the
code that will run it: `src/disclosure_drift/cli.py` (the `m3 acquire` parser, the mutual-exclusion
dispatch, and the live gate ladder), `src/disclosure_drift/config.py` (configuration resolution and
`DISCLOSURE_DRIFT_CONFIG`), `src/disclosure_drift/paths.py` (the data tree), and
`src/disclosure_drift/m3/acquisition.py` (the carry-in loader, verifier, and baseline requirement).
**No source, test, configuration, or migration byte was modified.** **No operational catalog, private
evidence artifact, raw object, lineage record, projection file, lease, receipt store, operational
checkpoint, or USB archive was opened by this recording — not even read-only.** Path composition was
checked against a **disposable temporary directory**, never a governed evidence root.

## 4. The independently derived current action

The current authorized action was derived from repository authority rather than assumed from the owner
instrument:

- accepted Decision 060 §15 records
  `NEXT_AUTHORIZED_ACTION: OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET`;
- `Milestones/STATUS.md` carries the same marker, and its `ACTIVE_BLOCKER` names the exact binding set
  this instrument must carry;
- the decision registry's Decision 060 row names the same next action;
- the **M3-L16** register entry names the same act as a related future act sitting outside that
  (closed) entry;
- contract §8 rung **T5** independently demands exactly this instrument.

All five agree. There is no disagreement between repository authority and the owner instrument, so the
authorization proceeds.

## 5. Ruling 061-A — the frozen public command contract

**Exactly one** future T6 invocation is authorized, and it is exactly this command. It is frozen here
in full; T6 does not compose, infer, extend, or shorten it.

```bash
python -m disclosure_drift m3 acquire \
  --config "$WINDOW_LOCAL_CONFIG" \
  --evidence-root "$EV_ROOT" \
  --plan runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json \
  --window M3.2A \
  --live \
  --ceiling 801 \
  --data-root . \
  --catalog catalogs/m3_2a_operational.sqlite3 \
  --receipt-out runs/m3_2a_clean_carry_in/execution_receipt.json \
  --carry-in-authority runs/m3_2a_clean_carry_in/carry_in_authority.json
```

**`$EV_ROOT` and `$WINDOW_LOCAL_CONFIG` are the only non-literal tokens**, and they are **not open
placeholders** — they are uniquely constrained private T6 parameters governed by §6. Every governed
binding in the command is **literal**.

### 5.1 Argument-by-argument binding

| Argument | Value | Authority |
|---|---|---|
| `--config` | `"$WINDOW_LOCAL_CONFIG"` | contract §16 (window-local configuration); §6.2 below |
| `--evidence-root` | `"$EV_ROOT"` | required by the CLI; contract §20; §6.1 below |
| `--plan` | `runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json` | §7.1 |
| `--window` | `M3.2A` | contract §5, §8; Decision 060 §5.3 |
| `--live` | present, explicit | contract §9; no default, and nothing stands in for it |
| `--ceiling` | `801` | contract §5; Decision 055 §5; Decision 060 §5.3 |
| `--data-root` | `.` | §7.2 |
| `--catalog` | `catalogs/m3_2a_operational.sqlite3` | contract §11, §16; §7.2 |
| `--receipt-out` | `runs/m3_2a_clean_carry_in/execution_receipt.json` | §7.3 |
| `--carry-in-authority` | `runs/m3_2a_clean_carry_in/carry_in_authority.json` | §7.4, §8 |

### 5.2 What the command must never contain

- **No `--run-id`.** The frozen CLI exposes no such option, and inventing one would be inventing
  syntax. The authorized new run id `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44` comes
  **from the carry-in authority artifact**, which replaces random generation for that invocation
  (Decision 055 §6.2; Decision 060 §6).
- **No `--resume-from`.** A carry-in root is **never** a resume. The two are refused together at the
  top of the dispatch, before a configuration is consulted, a plan is read, an artifact is opened, or
  any durable state is touched (Decision 055 §6; contract §12).
- **No `--show-scope`** in this invocation — `--live` and `--show-scope` are mutually exclusive. The
  separate zero-request scope check of runbook step 17 is a distinct command that places no requests.
- **No additional route, host, ceiling, plan, window, spacing, or contingency argument**, and no
  second invocation of any kind.

### 5.3 Parse verification performed before this record was written

The exact token list above was verified **parse-only** against the frozen CLI: the parser was built
and `parse_args` was called; **the dispatcher was never invoked**, no configuration was loaded, no
evidence root was resolved, no catalog was opened, no transport was constructed, and **no acquisition
ran**. It established that the command parses cleanly; that `--ceiling` yields the integer `801`; that
every member of the live gate ladder's required set — `plan`, `window`, `ceiling`, `catalog`,
`data_root`, `receipt_out` — is supplied; that `resume_from` and `receipt_chain_head` are both `None`;
and that **no `--run-id` option exists on the acquire parser at all**.

**Parsing is not authorization to run, and the command was not executed.**

## 6. Ruling 061-B — the private parameter rule

Decision 061 **does not publish** the literal absolute governed evidence-root path, the literal
absolute temporary configuration path, the SEC contact identity, or any other private machine-local
absolute path. It publishes **two named private parameters** and binds their meaning and validation
instead.

### 6.1 `EV_ROOT`

**Meaning, uniquely constrained:** the **exact governed external M3 private-evidence root** already
used by the accepted M3.1/M3.2 sequence — the same root beneath which the accepted M3.1B plan
artifacts, the T4 attestation and backup manifest, the historical M3.2A raw object and lineage, and
the operational catalog live. It is **not** a new location, and **no alternative root is authorized.**

At T6 it **must**, before any use:

- be supplied locally, outside Git and outside this record;
- resolve to an **absolute** path;
- pass `require_external_evidence_root`;
- be **outside the repository checkout**;
- be local and non-network storage, per the governing preflight;
- carry the required ownership and mode (`700`, artifacts `600`);
- contain **no disallowed symlink condition** at any governed path;
- **match the already accepted governed evidence root** — a different root is a stop, not a choice;
- **never be printed** in the public completion report, a log, a receipt, an artifact, an evidence
  index entry, or any governed identity.

### 6.2 `WINDOW_LOCAL_CONFIG`

**Meaning, uniquely constrained:** a **one-operation temporary configuration file** created during T6
solely to enable network for this single authorized `m3 acquire` invocation.

It **must**:

- be **outside Git**;
- be **outside the governed evidence root**;
- be a **regular file**, and **not a symlink**;
- be mode **`0600`**;
- contain **no SEC identity** value;
- be **derived from the accepted safe configuration**, changing only what §9 permits;
- set **only** `network.enabled: true` and `network.m3_acquire_enabled: true`;
- keep **`companyfacts.enabled: false`**;
- be **destroyed or withdrawn on every termination path** (§9).

**Its literal path is ephemeral and is deliberately NOT an identity bound by this record.** Decision
061 binds its **generation and validation procedure** instead. Configuration resolution is the
accepted one: an explicit `--config` takes precedence over `DISCLOSURE_DRIFT_CONFIG` and over the
upward search, so naming it explicitly on the command line is exact rather than ambient.

### 6.3 Why substitution cannot weaken a binding

Neither parameter can reach a governed public binding. The window, the plan hash, the ceiling, the
historical seed, the route allocation, the authorized run id, and every relative path are **literal**
in §§5 and 7 and are re-proved at runtime against module constants and against the carry-in authority's
own recomputed digest. A wrong `EV_ROOT` cannot produce a valid plan hash, a valid authority digest, or
a valid run id; a wrong `WINDOW_LOCAL_CONFIG` cannot enable a route, raise a ceiling, or supply an
identity. Every such divergence **refuses before transport construction**.

## 7. Ruling 061-C — the fixed public relative paths

All four paths below are **evidence-root-relative**, contain safely beneath `EV_ROOT` under the
existing escape-refusing discipline, and are **frozen**.

### 7.1 The request plan

```text
PLAN_REL: runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json
PLAN_SHA256: 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68
```

**Independently verified against accepted repository evidence, not assumed.** The durable independent
M3.1 acceptance review artifact
`Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md`
records, in a table expressly headed *"Artifact (evidence-root-relative)"*, that
`runs/m3_1b_plan_970e050…/plan_first.json` **and** `plan_second.json` both recompute to
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, are **byte-identical** by `cmp`,
and match the accepted identity. `Milestones/STATUS.md` independently records the full directory name
`runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/` under the external evidence root, with
both plans at that same hash. The directory's `970e050deb06910adcde8588101564beb7d19c74` component is
the frozen accepted implementation SHA of contract §2, so the name is derived, not invented.

`plan_first.json` is named because the owner fixed it; because the two plan files are **byte-identical**
the choice changes no byte the command consumes, and the plan-hash gate is what binds. Contract §5's
"two byte-identical zero-request plans" is exactly this pair.

### 7.2 The data root and the operational catalog

```text
DATA_ROOT_REL: .
CATALOG_REL:   catalogs/m3_2a_operational.sqlite3
```

The frozen CLI composes the catalog as `--data-root` / `--catalog` beneath `EV_ROOT`. The owner fixes
the decomposition above, which resolves to exactly the contract's accepted composed location
`catalogs/m3_2a_operational.sqlite3` beneath the evidence root (contract §11, §16). The alternative
split `--data-root catalogs --catalog m3_2a_operational.sqlite3`, and every other decomposition, is
**not authorized**; this removes the ambiguity the prior stop identified.

**Independently corroborated by accepted evidence.** With `--data-root .` the accepted data tree
places the bulk raw store at `raw/sec/bulk` relative to the evidence root — exactly the path at which
Decision 059 §3 records the intact accepted raw object
`raw/sec/bulk/sec_bulk_submissions-9ca4642200dbcc45.zip`. The ruling therefore matches the layout the
accepted M3.2A history already produced; it does not relocate anything.

### 7.3 The clean-run namespace and the receipt

The historical `m3_2a_initial` output namespace is **not reused**. The owner fixes a **new** clean-run
namespace:

```text
CLEAN_RUN_NAMESPACE_REL: runs/m3_2a_clean_carry_in/
RECEIPT_OUT_REL:         runs/m3_2a_clean_carry_in/execution_receipt.json
```

The receipt remains **create-once**, immutable, schema-governed, emitted **only** by the accepted
acquisition path, and **never** manually fabricated. **No receipt is created by this record.**

### 7.4 The carry-in authority artifact

```text
CARRY_IN_AUTHORITY_REL: runs/m3_2a_clean_carry_in/carry_in_authority.json
```

This is the **single authority-of-record location**, consistent with Decision 060 §9 item 3: there is
no repository copy and no second, differently located copy, because a second copy would create an
ambiguous authority-of-record that Decision 055 §6.1's single-identity rule does not permit.

The directory `runs/m3_2a_clean_carry_in/` may be created **only** during the later T6 operator
procedure, under the governed evidence-root containment and permission rules. **T5 does not create
it**, and it is expected to be absent now.

## 8. Ruling 061-D — carry-in materialization, a future T6 step

Decision 060 validly minted the authority through owner-fixed canonical bytes and digest, and
expressly deferred **materialization** — the delivery of those bytes to the governed evidence root —
to this instrument. That path is now fixed (§7.4), which resolves the prior stop's **MAJ-1**.

### 8.1 The authority being materialized

```text
SCHEMA:                 m3-carry-in-authority/1.0
CANONICAL_LENGTH:       571 bytes
AUTHORITY_SHA256:       d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d
CANONICAL_BYTE_SOURCE:  Decision 060 §5.1, verbatim and unaltered
```

The exact canonical bytes are those fixed at Decision 060 §5.1 and are **not restated here**, so that
exactly one public preimage of record exists and no transcription can diverge from it. They were
independently reverified at this recording: recomputed from Decision 060's committed bytes to **571
bytes** and **`d7aa206b…`**; admitted by the accepted `load_carry_in_authority`; re-proved by
`require_admitted_carry_in_authority`; and passed by `verify_carry_in_authority` against window
`M3.2A`, plan `19be7bdc…`, ceiling `801`, and `resuming=False`. **That verification created nothing,
consumed nothing, opened no catalog, and made no invocation.**

### 8.2 The exact T6 materialization procedure

At T6, write those exact bytes to:

```text
$EV_ROOT/runs/m3_2a_clean_carry_in/carry_in_authority.json
```

The write **must** be:

1. **create-once** — it **fails if the target already exists**;
2. mode **`0600`**, enforced by umask and explicitly applied, under a parent contained beneath
   `EV_ROOT` at mode `700`;
3. a **regular file**, and **not a symlink**, with no symlinked ancestor;
4. the **exact canonical 571 bytes** of Decision 060 §5.1, with exactly one trailing LF, no BOM, and
   no re-serialization;
5. followed by **SHA-256 re-verification**, requiring exactly
   `d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d`;
6. followed by **accepted loader admission** (`load_carry_in_authority`);
7. followed by **exact binding verification** against window `M3.2A`, plan `19be7bdc…`, ceiling `801`,
   seed `1`, route allocation `{"sec_bulk_submissions": 1}` compared as a whole mapping, `Decision 055`,
   `Decision 059`, evidence-manifest `981b5e42…`, and run id
   `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44`;
8. **performed before carry-in consumption**, and before any transport is constructed.

### 8.3 Fail-closed conditions

The procedure **must stop before consumption** on any of: the target already existing; existing bytes
differing; wrong permissions; wrong path; a symlink or symlinked ancestor; a path escaping `EV_ROOT`;
a digest mismatch; a canonicality mismatch; a missing or altered binding; or loader refusal.

**If the materialized bytes ever fail to hash to `d7aa206b…`, they are not this authority**, and the
invocation must refuse and stop rather than proceed on an artifact that was not minted by Decision 060.

**No materialization occurs during T5.** No file is created by this record.

## 9. Ruling 061-E — the network window

### 9.1 During T5 — unchanged

```yaml
network:
  enabled: false
  m3_acquire_enabled: false
companyfacts:
  enabled: false
```

**No configuration mutation is authorized now, and none occurred.** Tracked
`configs/project.yaml` is byte-unchanged by this record.

### 9.2 For T6 only — the exact transition

`WINDOW_LOCAL_CONFIG` (§6.2) is constructed from the accepted safe configuration with **exactly**:

| Key | Tracked value | Window-local T6 value |
|---|---|---|
| `network.enabled` | `false` | `true` |
| `network.m3_acquire_enabled` | `false` | `true` |
| `companyfacts.enabled` | `false` | **`false` — unchanged** |

**Tracked `configs/project.yaml` remains `false` / `false` / `false` throughout.** The tracked default
is **never** committed `true`.

- **Scope:** the single authorized `m3 acquire --live` invocation of §5, and nothing else. Only that
  command reads `network.m3_acquire_enabled`; the global switch never enables acquisition on its own,
  and the M2.2 census surfaces stay refused at their existing gates.
- **Enable point:** immediately before that one invocation, and no earlier.
- **Disable point:** immediately after termination, before any freeze, derivation, or further work.
- **Failure-path withdrawal:** the T6 wrapper must withdraw the temporary configuration on **every**
  termination path — normal exit, `EXIT`, `INT`, `TERM`, `HUP`, failure, gate stop, ceiling stop, and
  interruption.
- **After-run proof:** the safe `false` / `false` state must be verified after termination, before any
  further work, and recorded for Gate H items 14.1–14.3.

**No broad or general network enablement is authorized. CompanyFacts and Frames remain disabled and
prohibited; no M3.2A authority requires them.**

## 10. Ruling 061-F — burn-before-wire and the one-invocation boundary

Decision 055's accepted burn-before-wire semantics are preserved **exactly** and are not
reinterpreted.

**T6 must not contact the SEC unless the carry-in checkpoint has first been successfully committed.**
The ordering is:

1. materialize and verify the authority bytes (§8);
2. verify every exact binding;
3. verify the authority is **unconsumed** — no `ops_checkpoints` row exists under the deterministic key
   `m3_2_carry_in_authority:d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d`;
4. register the new run **and** insert that deterministic checkpoint in the **same**
   `BEGIN IMMEDIATE` transaction — both rows commit, or neither exists;
5. **only after that commit** may a transport be constructed or any contact occur.

**If the authority is consumed and a later pre-wire or live step fails, the authority remains
CONSUMED even with zero attempts placed.** There is **no automatic reissue, no retry, no replacement,
and no second clean run.** Evidence is preserved untouched, and the matter returns to Sol/GPT. A
replacement authority is a **new owner act** — never automatic, never silent, never a session's
initiative, and never implied by any failure.

**Exactly one invocation is authorized**, bound to the exact new run id, authority digest, plan hash,
ceiling, historical seed, route allocation, command, and network transition frozen here. No automatic
retry, no second live invocation, and no resume of the historical run.

## 11. Ruling 061-G — the T6 preflight

The following preflight is **frozen and complete**. **No item may be waived.** Any mismatch,
ambiguity, or unavailable proof is a **STOP before live entry**.

| # | Item |
|---|---|
| 1 | Decision 061 published, accepted, and current, at its exact identity |
| 2 | branch `main` |
| 3 | clean worktree — staged 0, unstaged 0, untracked 0 |
| 4 | `HEAD == origin/main`, compared from the **local ref** — no fetch, no pull |
| 5 | tracked `network.enabled: false` and `network.m3_acquire_enabled: false` at entry |
| 6 | tracked `companyfacts.enabled: false` |
| 7 | plan path exactly `runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json` |
| 8 | plan SHA-256 exactly `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` |
| 9 | window exactly `M3.2A` |
| 10 | ceiling exactly `801` |
| 11 | historical seed exactly `1` — never `0` |
| 12 | carry-in canonical length exactly **571** bytes |
| 13 | carry-in SHA-256 exactly `d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d` |
| 14 | carry-in artifact at exactly `runs/m3_2a_clean_carry_in/carry_in_authority.json` (§7.4, §8) |
| 15 | carry-in **UNCONSUMED** — no `ops_checkpoints` row under the deterministic key |
| 16 | authorized new run id exactly `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44` |
| 17 | historical run `m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0` still `stopped` and permanently non-resumable, with recovery `UNDETERMINED` and no receipt |
| 18 | no existing conflicting registration for the new run id |
| 19 | project-scoped executor exclusivity satisfied (§14) |
| 20 | SQLite single-writer lease held |
| 21 | catalog migration chain head `0013`, and the SQLite quick, integrity, and foreign-key gates pass |
| 22 | no stale `.part` file, and no unresolved blocking recovery condition |
| 23 | free disk at or above the accepted **50.00 GiB** entry floor |
| 24 | the accepted backup requirement satisfied and the private backup recoverable |
| 25 | SEC contact identity valid at the canonical boundary, **without disclosure** |
| 26 | **M3-L16 `CLOSED — DECISION 059`** |
| 27 | **M3-L15** `ACTIVE` and its condition acknowledged (§17) |
| 28 | Decision 060 finally owner-accepted |
| 29 | Decision 061 finally owner-accepted |
| 30 | the exact T6 execution-packet identity present (§20) |
| 31 | `EV_ROOT` validated against every §6.1 condition |
| 32 | `WINDOW_LOCAL_CONFIG` generated and validated against every §6.2 and §9.2 condition |
| 33 | the exact §5 command, verbatim, with no added or removed argument |
| 34 | the isolated M3.2 data root, quarantine and staging paths, and recorded available storage established for Gate H pre-run state |

Contract §17's twenty-one stop conditions and Decision 050 §8's interruption rule apply in full and
are not narrowed. Where governing authority requires an additional item at execution time, it is
added, never removed.

## 12. Ruling 061-H — Decision-050 T5 exhaustion and narrow supersession

Decision 050's original grant:

```text
ONE_INITIAL_M3_2A_LIVE_INVOCATION
```

was **exercised**. It **ended non-successfully**. It is:

```text
EXHAUSTED
NON-REUSABLE
```

It is **never** reused, extended, replayed, or read as covering the clean carry-in run. **Decision
061's clean-run authority is a NEW T5 authority**, granted on the current accepted state, and it
reinterprets nothing.

**Narrow supersession, for this clean carry-in run only.** Decision 050 §9 required the later
execution packet to reverify, among other things, **consumed count `0`**, the real operational catalog
**absent**, **no prior M3.2 live run**, **no prior live receipt**, and **no prior raw or live object**.
Accepted history has made each of those impossible and, in some cases, the opposite of what governance
now requires: consumption stands at **1 of 801** and a zero-baseline start is **never lawful**
(contract §12; Decision 055 §5; Decision 060 §8); the historical run exists and is permanently
`stopped`; and the adopted raw object and lineage are intact and must never be deleted. For **this
run only**, those specific §9 conditions are superseded by the §11 preflight above.

**Everything else in Decision 050 remains fully binding**, including §8's predecessor-receipt
requirement for **every resume** — which a carry-in root is not — its no-automatic-resume rule, the
conjunctive live gate of §10, the withheld authorities of §7, and the frozen scope of §5.

**Decision 050 is not amended in place.** Its bytes are unchanged, and the historical chronology is
preserved exactly.

## 13. Ruling 061-I — historical request accounting

```text
SEC_PHYSICAL_REQUEST_CONSUMPTION_BEFORE_T5:  1 / 801
T5_EFFECT_ON_CONSUMPTION:                    NONE — NO REQUEST, NO RESERVATION, NO WIRE ACTIVITY
SEC_PHYSICAL_REQUEST_CONSUMPTION_AFTER_T5:   1 / 801
HISTORICAL_SEED_H:                           1 — CARRIED FORWARD EXACTLY, NEVER RESET TO 0
REMAINING_TOTAL_HEADROOM:                    800
REMAINING_BULK_ROUTE_HEADROOM:               5 — ACCOUNTING AND REPORTING ONLY, NEVER A RUNTIME REFUSAL
```

The authorized invocation begins from `historical_consumed_request_count = 1`. The global
`PhysicalAttemptCeiling` is constructed with `approved_ceiling` **801** and `consumed` **1**;
cumulative consumption is `1 + N`, where `N` is that invocation's own wire attempts. There is **no
`802`, no additive ceiling, no shadow ceiling, no reset, and no reinterpretation**, and the ceiling is
**never** described as consumed `0`. The accepted historical request is **not** restored, replayed, or
re-attempted, and **801 new physical attempts are never granted in addition to it**.

The frozen 75-logical-request plan is unchanged and is never trimmed or re-derived to fit the reduced
headroom. There is **no pre-run fit gate**, and a stop at cumulative **801** with planned work
remaining remains a lawful `stopped_at_ceiling` outcome and a Gate H failure, exactly as before.

The clean carry-in root receipt carries **1** in `consumed_request_count_carried_forward`, names this
authority in `carry_in_authority_sha256`, records `actual_physical_attempt_count` as **`N` only**, and
the chain walker adds the root carry-in **exactly once** (Decision 055 §§7.4–7.5).

## 14. Ruling 061-J — project-scoped executor exclusivity and the writer lease

Before opening private state or beginning live execution, T6 must enforce the owner-ratified
**project-scoped exclusivity** definition. A conflict exists if another process:

1. has its current working directory in the Disclosure Drift repository or below; **or**
2. is an active AI coding session targeting Disclosure Drift or its private state; **or**
3. is actively performing, queued for, or delegated Disclosure Drift live work; **or**
4. has Disclosure Drift or private-state files open in a manner consistent with active execution.

**Idle OpenClaw, Codex, or Claude helper infrastructure outside Disclosure Drift and its private state
is not conflicting merely by existing.** **Unrelated processes are never killed.**

The **SQLite single-writer lease remains separately mandatory** and is never substituted by the
exclusivity check; both are required.

## 15. Ruling 061-K — the bounded operator-runbook correction

The prior stop's **MIN-1** recorded that the operator runbook's printed command forms omit mandatory
frozen-CLI arguments, so an operator following them verbatim receives a usage failure. The owner
authorizes a **strictly bounded** correction, and this record performs exactly it:

**Authorized and performed:**

- adding the **missing mandatory CLI arguments** to the applicable M3.2 `m3 acquire` command forms —
  runbook steps 17, 18, 27, and 27a;
- **replacing command placeholders with the Decision-061 bindings** where the public relative values
  are now fixed (§7);
- **retaining `EV_ROOT` and `WINDOW_LOCAL_CONFIG` as named private variables**, never literal paths;
- marking the **discharged M3-L16 and orphan-adoption precondition** text at step 27a as satisfied;
- stating clearly at step 27a and in Appendix B that **T5 authorization is not T6 execution**;
- **preserving every substantive stop, recovery, ceiling, burn-before-wire, and no-retry rule**
  byte-for-byte in substance.

**Expressly not done:** the runbook is **not redesigned**, and no unrelated section is modified. The
pre-existing `PLANNED — NOT YET IMPLEMENTED (M3.2)` status badges and Appendix B's preamble sentence
are a **separate, pre-existing documentary lag** predating Decision 046's implementation acceptance;
correcting them is outside this authorization and is **left for a later separately authorized
runbook-currency pass**. Nothing in this record depends on them.

## 16. What this authorization does not grant

**Decision 061 authorizes none of the following, and no session may read it as doing so:**

- **execution of the authorized invocation** — that requires the separate later owner execution packet
  named at §20;
- **materialization of the carry-in artifact** or **consumption of the authority** at this stage;
- **more than one** invocation, any **automatic retry**, any **reissue**, any **replacement
  authority**, or any **second clean run**;
- **resume, replay, or retry of the historical run** `m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0`,
  or reuse of its run id;
- **a second orphan adoption** — the real adoption invocation is **1 consumed / 0 remaining**, and
  Decision 057 §12's prohibition stands permanently;
- **M3.2B**, dependent-plan derivation, reconciliation, or **Gate H**;
- **CompanyFacts, Frames, filing-body retrieval, or accession-content retrieval**;
- any **plan, route, host, method, ceiling, spacing, parser, schema, migration, reason-code, or
  receipt-schema change**;
- any **mutation** of the execution evidence bundle, catalog, projection, raw object, lineage, or USB
  archive;
- any **tag**, force push, rebase, amend, or history rewrite.

Migrations remain `0001`–`0013`; the ceiling **801** is never increased, reset, shadowed, or
reinterpreted; SEC consumption remains **1 of 801**; and **live readiness is NOT claimed**. **M3.2 is
NOT COMPLETE.**

## 17. Limitations disposition

```text
M3_L14:  CLOSED — DECISION 056 — UNTOUCHED
M3_L15:  ACTIVE — UNTOUCHED AND BYTE-UNCHANGED; CARRIED AS A T6 EXECUTION-TIME CONDITION
M3_L16:  CLOSED — DECISION 059 — UNTOUCHED
```

**No limitation's state is altered by this record. None is closed, none is reopened, and no new entry
is created.** `Docs/m3/limitations_register.md` is **not edited**: read-only inspection established
that no **current forward-looking** statement in it becomes false on this publication. Its
forward-looking references sit in the **closed** M3-L16 entry and assert that the remaining acts sit
**outside that entry** — which stays true — and that **live readiness remains unclaimed**, which this
non-self-executing authorization does not change. Under Decision 059 §7's documentary-lag rule, a
closed entry's narrative is preserved as historical rather than restated.

**M3-L15 — its condition on the authorized invocation.** M3-L15 records that the second-SIGTERM
`delivered` latch, which suppresses a second signal during live-acquisition cleanup, is implemented
and was directly verified by process-level fault injection but carries **no committed regression
test**. It is a **test-strength gap, not a production defect**; its methodology, reproducibility,
security, and publication impacts are all **none**; and it places **no condition on T5 authorization
and none on T6 authorization**. It nevertheless remains **`ACTIVE` for M3.2 and every later phase that
runs the governed live-acquisition lifecycle**, so **the authorized T6 run proceeds while it is open**,
exactly as the register states. Its **stop condition is narrow and unrelated to this stage**: *any edit
to the scoped SIGTERM handling that is not accompanied by a test covering second-signal suppression*.
**No such edit occurs here** — this record changes no executable byte at all. It is **recorded, not
closed, and not discharged**, and the T6 operator carries it as an execution-time condition: a second
`SIGTERM` during cleanup is not a covered path, so the operator must not send one.

**No other active limitation blocks this authorization.** M3-L01–M3-L10 remain `ACTIVE` live-operation
and platform risk entries that condition acquisition execution and are carried into T6 unchanged.
**D023-O1** remains the sole unresolved owner-ruling condition —
`LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED` — a stop-and-refer condition a
real run may reach; it is not triggered by this record.

## 18. Path and publication boundary

Exactly **four** repository paths are authorized for this recording, with **no fifth**:

1. `Docs/Decisions/decision_061_m3_2a_clean_carry_in_live_invocation_authorization.md` (this record)
2. [`Docs/Decisions/decision_registry.md`](decision_registry.md)
3. [`Milestones/STATUS.md`](../../Milestones/STATUS.md)
4. [`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) — the bounded §15 correction **only**

[`Docs/decision_index.md`](../decision_index.md) is **not** edited, following the convention for
Decisions 050–060. [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) is **not**
edited (§17).

Expressly **not** edited: any accepted decision 001–060, each preserved byte-identical; the accepted
contract; the receipt specification; every template and evidence index; the SEC data dictionary; every
durable review artifact; every production source; every test; every configuration; every migration;
every reason code; the `Makefile`; `pyproject.toml`; and every script. **No private state, no governed
evidence root, no operational catalog, and no USB archive is touched.**

**Publication** is exactly **one** governance commit on `main` over those four paths, under the subject
`Authorize M3.2A clean carry-in live invocation`, followed by exactly **one** ordinary fast-forward
push to `origin/main`. No force, no fetch, no pull, no rebase, no squash, no amend, no cherry-pick, no
branch, no worktree, no stash, and **no history rewrite**. **NO TAG** — M3.2 is not complete. A record
cannot contain the hash of the commit that contains it, so this record's own commit identity is
established by that act.

## 19. Recorded status

```text
DECISION_061_TYPE:                OWNER LIVE-OPERATION AUTHORIZATION — GOVERNANCE PUBLICATION ONLY
RECORD_IS_SELF_EXECUTING:         NO — AUTHORIZES ONE FUTURE T6 INVOCATION; PERFORMS NONE OF IT
T5:                               AUTHORIZED AND PUBLISHED
T6_EXECUTION:                     NOT PERFORMED — REQUIRES ITS OWN SEPARATE OWNER EXECUTION PACKET
AUTHORIZED_INVOCATION_COUNT:      1
COMMAND_CONTRACT:                 FROZEN — SECTION 5, VERIFIED PARSE-ONLY AGAINST THE FROZEN CLI
COMMAND_EXECUTED_BY_THIS_RECORD:  NO
PRIVATE_PARAMETERS:               EV_ROOT, WINDOW_LOCAL_CONFIG — UNIQUELY CONSTRAINED, VALIDATED AT T6
PRIVATE_ABSOLUTE_PATHS_PUBLISHED: NONE
PLAN_REL:                         runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json
PLAN_SHA256:                      19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68
DATA_ROOT_REL:                    .
CATALOG_REL:                      catalogs/m3_2a_operational.sqlite3
RECEIPT_OUT_REL:                  runs/m3_2a_clean_carry_in/execution_receipt.json
CARRY_IN_AUTHORITY_REL:           runs/m3_2a_clean_carry_in/carry_in_authority.json
CARRY_IN_AUTHORITY:               MINTED — UNCONSUMED
CARRY_IN_AUTHORITY_SCHEMA:        m3-carry-in-authority/1.0
CARRY_IN_AUTHORITY_SHA256:        d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d
CARRY_IN_AUTHORITY_BYTE_LENGTH:   571
CARRY_IN_CONSUMPTION_CHECKPOINT:  m3_2_carry_in_authority:d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d — NO SUCH ROW EXISTS
CARRY_IN_USES_TOTAL:              1
CARRY_IN_USES_CONSUMED:           0
CARRY_IN_USES_REMAINING:          1
CARRY_IN_MATERIALIZED:            NO — A BOUNDED T6 OPERATOR STEP, CREATE-ONCE AND DIGEST-VERIFIED
CARRY_IN_REPLACEMENT:             NEW OWNER ACT ONLY — NEVER AUTOMATIC, NEVER SILENT
WINDOW:                           M3.2A
CUMULATIVE_CEILING:               801 — NEVER 802, ADDITIVE, SHADOWED, OR RESET
HISTORICAL_SEED_H:                1 — CARRIED FORWARD EXACTLY; ZERO-BASELINE START NEVER LAWFUL
ROUTE_ALLOCATION:                 sec_bulk_submissions: 1 — COMPARED AS A WHOLE MAPPING
AUTHORIZING_DECISION:             Decision 055
ORPHAN_ADOPTION_DECISION:         Decision 059
ORPHAN_ADOPTION_EVIDENCE_SHA256:  981b5e420dda42e54d2622624db76f95e6072d181f549bf25ae6d05e9d942e5b
AUTHORIZED_NEW_RUN_ID:            m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44 — NOT STARTED, NOT REGISTERED
RUN_ID_SOURCE:                    THE CARRY-IN ARTIFACT — NO --run-id OPTION EXISTS
HISTORICAL_RUN_ID:                m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0
HISTORICAL_RUN_STATE:             stopped — PERMANENTLY NON-RESUMABLE; NEVER REUSED
HISTORICAL_RUN_CLASSIFICATION:    UNDETERMINED — UNCHANGED
TERMINATING_RECEIPT:              NONE — NOT CREATED, NOT RECONSTRUCTED
SEC_REQUEST_CONSUMPTION:          1 / 801 — UNCHANGED BEFORE AND AFTER THIS RECORD
REMAINING_TOTAL_HEADROOM:         800
BULK_ROUTE_HEADROOM:              5 — ACCOUNTING AND REPORTING ONLY
DECISION_050_T5_GRANT:            EXHAUSTED — NON-REUSABLE; NEVER EXTENDED OR REPLAYED
BURN_BEFORE_WIRE:                 PRESERVED EXACTLY — CONSUMED STAYS CONSUMED; NO REISSUE, NO RETRY
NETWORK:                          NOT ENABLED — TRACKED false / false; COMPANYFACTS false
NETWORK_TRANSITION:               FROZEN — WINDOW-LOCAL ONLY, SINGLE COMMAND, WITHDRAWN ON EVERY PATH
CONFIGURATION_BYTES_CHANGED:      NONE
EXECUTABLE_BYTES_CHANGED:         NONE
MIGRATION:                        NONE — 0001-0013 UNCHANGED
SEC_CONTACT:                      NONE OCCURRED — NONE AUTHORIZED BY THIS RECORD
TRANSPORT_CONSTRUCTION:           NOT PERFORMED
PRIVATE_STATE_ACCESS:             NONE — NO CATALOG, DATA ROOT, RAW OBJECT, LINEAGE, PROJECTION, EVIDENCE BUNDLE, OR USB
M3_2B:                            NOT_AUTHORIZED
GATE_H:                           NOT_AUTHORIZED
SECOND_ADOPTION:                  NOT_AUTHORIZED — 1 CONSUMED / 0 REMAINING, PERMANENTLY
HISTORICAL_RUN_RESUME:            PROHIBITED
M3_L14:                           CLOSED — DECISION 056; UNTOUCHED
M3_L15:                           ACTIVE — UNTOUCHED, BYTE-UNCHANGED; CARRIED AS A T6 EXECUTION CONDITION
M3_L16:                           CLOSED — DECISION 059; UNTOUCHED
9475eb3d_MATTER:                  SEPARATE STANDING OWNER MATTER — NONBLOCKING; NOT RESOLVED HERE
LIVE_READINESS:                   NOT_CLAIMED
TAG:                              NONE
M3_2:                             NOT_COMPLETE
```

## 20. Formal outcome and exact next authorized action

```text
FORMAL_OUTCOME: M3_2A_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZED
T5: AUTHORIZED AND PUBLISHED
T6: NOT EXECUTED
CARRY_IN: MINTED / UNCONSUMED
NETWORK_OR_SEC_AUTHORITY: NONE EXERCISED BY THIS RECORD
LIVE_READINESS: NOT_CLAIMED
NEXT_AUTHORIZED_ACTION: OWNER_M3_2_T6_CLEAN_CARRY_IN_CONTROLLED_ACQUISITION_EXECUTION_PACKET
```

**How that next action is derived, and what it is.** The accepted contract §8 fixes the ladder: rung
**T5** is *live-operation authorization (M3.2A) — one bounded acquisition operation*, discharged by
this record; rung **T6** is *controlled acquisition execution (M3.2A window)*, which happens **only
after T5**. The token follows the repository's own convention, in which each accepted record names its
successor and an authorization packet is followed by a separate execution packet — the Decision 050
precedent pair `OWNER_M3_2_T5_INITIAL_LIVE_INVOCATION_AUTHORIZATION_PACKET` →
`…_EXECUTION_PACKET`, and the current `OWNER_`-prefixed form used by Decisions 059 and 060. Its name
mirrors contract §8's own rung title for T6.

**It does not self-execute.** No session may begin it, or any part of it, before the owner issues it.
It is not begun, not drafted as authority, and not implied by this record.

**Authorization is not execution, and no execution exists to authorize beyond the one bounded
invocation frozen here.**

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
