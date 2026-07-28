# CLAUDE.md — collaboration rules for Disclosure Drift

This file governs every assistant session in this repository. It encodes the collaboration rules
approved by the project owner (Joey) at Milestone 1, extended with a repository-navigation layer per
project-owner instruction on 2026-07-28. It is the entry point: read it first, then follow "Reading
order" below.

## Project context

Disclosure Drift is a preregistered temporal-reliability study of Form 10-K disclosures. The research
design is frozen. Engineering work implements that design; it never redefines it.

Authoritative records, in precedence order:

1. `Docs/preregistration.md`
2. `Docs/Decisions/decision_NNN_*.md` — see
   [`Docs/Decisions/decision_registry.md`](Docs/Decisions/decision_registry.md) for the complete
   numbered list, current status, and which record controls when two decisions address the same
   topic (e.g. Decision 010 controls the cohort date-source rule; Decision 003 controls everything
   else about the temporal split). The registry is the source of truth for the current highest
   decision number; nothing in this file hardcodes it.
3. `Docs/leakage_register.md` and `Docs/research_risk_register.md`
4. `Milestones/milestone_XX_*.md` — the active milestone specification, and the active stage contract
   under `Milestones/contracts/` where one exists for the current stage.

## Reading order

Before editing anything, read in this order:

1. **This file (`CLAUDE.md`).**
2. **[`Milestones/STATUS.md`](Milestones/STATUS.md)** — the concrete-state ledger: accepted baseline,
   current phase, active blocker, next authorized action. Commit hashes recorded there are historical
   checkpoint references; run `scripts/context_snapshot.sh` (or `make context`) for live state.
3. **The active stage contract** named in `Milestones/STATUS.md` (under `Milestones/contracts/`) —
   states that stage's exact objective, authorized/prohibited paths, and commit boundary. See
   [`Milestones/contracts/README.md`](Milestones/contracts/README.md) for what a contract is and is
   not authorized to do.
4. **[`Docs/decision_index.md`](Docs/decision_index.md)** — find which decisions govern the topic
   you are about to touch.
5. **Only the decisions and modules the active stage contract links to.** Do not read the entire
   `Docs/Decisions/` directory speculatively; the contract states which records apply to this stage.
6. **[`Docs/change_impact_map.md`](Docs/change_impact_map.md)** before choosing which tests to run.

[`Docs/architecture_map.md`](Docs/architecture_map.md) is useful alongside steps 4–5 for locating
which module owns which stage of the data pipeline. It is not itself a required step — consult it to
find code, never as a substitute for the decision records it links to.

## Authority rules

- **Python policy constants control executable frozen values where a decision assigns them
  ownership.** `src/disclosure_drift/cohorts.py` is the canonical location for frozen *research*
  definitions (cohort windows, maturity gates, primary outcome, thresholds, bootstrap seed — rule 3
  below). `src/disclosure_drift/pilot_policy.py` is a separate case: frozen *engineering/provenance*
  policy-version constants that Decision 016 and Decision 017 assign to it. Neither module derives
  authority from the other; each constant is controlled by whichever decision assigns it ownership.
- **Accepted decisions control methodology.** A record with status "Approved by project owner" in
  `Docs/Decisions/decision_registry.md` is binding. A record still marked "Proposed" or "pending" is
  not — confirm its actual current status before treating it as settled.
- **Migrations control the persisted schema contract.** `src/disclosure_drift/storage/migrations/`
  is ground truth for which tables, columns, and constraints actually exist. A decision can approve a
  schema design before it is implemented (e.g. Decision 016 approved the Stage S3 table family
  before migration `0009` existed); until the migration exists, the design is approved but is not yet
  the persisted contract.
- **Milestone status files record workflow state but never override a decision.**
  `Milestones/STATUS.md` and files under `Milestones/contracts/` describe where the project currently
  stands. If either ever appears to contradict a decision record or a migration, the decision or
  migration controls — stop and report the discrepancy rather than trusting the status file.
- **Architecture and decision indexes are navigation aids, not independent authorities.**
  `Docs/architecture_map.md`, `Docs/decision_index.md`, and `Docs/change_impact_map.md` point to
  authoritative sources; they never themselves define, approve, or amend anything. A stale pointer in
  one of them is a bug in the pointer — it is never grounds for treating the pointer's summary as
  authoritative over the source it links to.
- **Old completion reports and chat transcripts are not repository authority.** Only what is
  committed to `Docs/Decisions/`, a migration, or source under `src/` binds a future session. A prior
  session's narrative completion report documents what that session did; it is not a standing
  instruction.

## Approved collaboration rules

1. **Read the active milestone specification before editing.** Also read the frozen research
   documents it references. Scope is set by that specification, not by inference.
2. **Plan before substantial changes.** Present a plan and wait for explicit approval before writing
   files. Report ambiguities rather than resolving them silently.
3. **Never alter frozen research definitions.** Cohort windows, maturity gates, the primary outcome,
   hypotheses, thresholds, and the bootstrap seed change only through an approved decision record in
   `Docs/Decisions/` followed by a reviewed code change. `src/disclosure_drift/cohorts.py` is the
   canonical code location; configuration only mirrors it.
4. **Never use future information in features.** Every predictor must have been publicly available at
   the SEC acceptance timestamp of the target filing. Consult `Docs/leakage_register.md` (L01-L18)
   before adding any transformation.
5. **Never silently change an outcome.** Outcome definitions, caps, industry adjustment, and the
   severe-deterioration rule are preregistered. A change requires a recorded deviation stating whether
   any transition or final-test metric had been viewed.
6. **Never delete raw data.** Raw filings and downloaded artifacts are append-only. Reprocessing
   writes new derived outputs; it never overwrites or removes sources.
7. **Never commit secrets or large datasets.** No API keys, tokens, real contact addresses, `.env`
   files, corpora, or generated data. `.env.example` carries placeholders only.
8. **Test every new transformation.** A parser, feature, join, or metric arrives with unit tests and,
   where behaviour spans components, an integration test.
9. **Preserve lineage.** Carry accession number, CIK, form type, filing date, acceptance timestamp,
   fiscal period end, and source offsets through every derived table. Structural information
   (risk-factor order, headings, offsets) is preserved alongside cleaned text.
10. **Use deterministic seeds.** Seed every stochastic step from the frozen seed and record the seed
    and package versions in the run manifest.
11. **Report row-count changes.** Any stage that adds or drops rows reports before and after counts
    with reasons, and primary analyses carry an exclusion waterfall.
12. **Stop when invariants fail.** On a failed data-quality, leakage, or reconciliation gate, stop and
    report. Do not work around a failing invariant, relax a threshold, or drop failing rows silently.
13. **Do not commit or push unless instructed.** No `git commit`, `git push`, remote configuration,
    branch creation, or history rewriting without an explicit instruction.
14. **Do not edit outside milestone scope without explanation.** If a change beyond scope seems
    necessary, stop and explain why before making it. `Docs/`, `Literature/`, and `Milestones/` are
    read-only during engineering milestones — this includes `Milestones/STATUS.md` and
    `Milestones/contracts/`, which are updated only under the same explicit-instruction discipline as
    any other file in those directories, never as a casual side effect of unrelated work.
15. **End every implementation session with a structured completion packet.** See the templates
    below.

## Milestone 1 boundaries (historical — superseded by later stage contracts)

Retained for the historical record, not as current guidance. Stage M2.2 and later milestones
subsequently authorized SEC retrieval, ingestion code, and filing-inventory work that this list
originally prohibited (see Decisions 007–012 and the M2.2/M2.3 milestone specifications).
**Current scope always comes from the active stage contract (Reading order step 3), never from this
section.**

Permitted at M1: packaging, configuration, logging, CLI, tests, CI, repository documentation.

Prohibited at M1: downloading or querying SEC filings, ingestion code, production database design,
filing section parsing, XBRL outcome definitions, research features, the Disclosure Drift Index,
rewrite prompts or LLM provider calls, model training, and any access to 2022-2026 outcomes.

How that list stands now, stated as authority rather than as a snapshot:

- **Authorized since M1, and implemented:** SEC retrieval, ingestion code, and production database
  design (Decisions 007–012; the M2.2 and M2.3 milestone specifications; migrations `0001`–`0010`).
- **Defined by accepted decisions, but not authorized for implementation in the current stage:** the
  primary outcome definition and the relevant cohort windows
  ([Decision 002](Docs/Decisions/decision_002_primary_outcome.md),
  [Decision 003 v0.2](Docs/Decisions/decision_003_temporal_split.md),
  [Decision 005](Docs/Decisions/decision_005_2025_2026_recency_extension.md),
  [Decision 010](Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md)), and
  the future freeze of the XBRL concept hierarchy (Decision 002, "Deferred implementation detail" —
  frozen from accounting semantics, synthetic fixtures, and development-cohort-only (2010–2021)
  reconciliation evidence). These records define *what* those artifacts are; no stage contract
  currently authorizes writing the code that produces them.
- **Prohibited as an input regardless of stage:** outcome values, pilot membership, and pilot
  stratification must never inform a feature, threshold, vocabulary, transform, or model choice
  (rules 4 and 5 above; `Docs/Decisions/decision_015_pilot_use_prohibition.md`;
  `Docs/leakage_register.md` L15 and L19).
- **Current stage scope:** M2.3 Stage S5 work is SEC *metadata* and deterministic engineering
  selection only. It reads no outcome value, no filing text, and no CompanyFacts value.

Check [`Docs/Decisions/decision_registry.md`](Docs/Decisions/decision_registry.md) and the active
stage contract for the current position; do not treat this summary as the live record.

## Engineering conventions

- Python 3.12, `src` layout, type hints in core modules.
- Ruff for lint and format (line length 100); mypy strict over `src`; pytest for tests.
- Minimal runtime dependencies; development dependencies separated in the `dev` extra.
- No network access in package code outside a milestone that explicitly authorizes it.
- Configuration is typed, rejects unknown fields, and produces actionable error messages.
- Only allowlisted `DISCLOSURE_DRIFT_*` environment variables are honoured; secrets are resolved on
  demand and never logged, printed, or stored on a model.
- Tests use temporary paths and fixtures, never a machine-specific directory.

## Workflow modes

Three `make` targets cover the normal development cycle. Each just invokes the Makefile — see there
for exact commands; they are not duplicated here.

- **Fast development loop — `make fast`.** Changed-file Ruff plus the mypy daemon. Deliberately does
  not run the test suite; pass the specific tests you're working on via
  `make test PYTEST_ARGS="tests/..."`. Not an acceptance gate.
- **Full acceptance validation — `make check`.** Every gate in fixed order: lint, format check, full
  mypy, full test suite, secret scan, hygiene check, config validation, cohort print, SEC help. This
  is the acceptance gate — run it before considering work done.
- **Context snapshot — `make context`.** Runs `scripts/context_snapshot.sh`: a fast, read-only report
  of repository root, branch, HEAD, origin/main comparison, working-tree status, checkpoint tags,
  latest migration, latest decision record, and the current stage/blocker from `Milestones/STATUS.md`.
  No network access, no writes, no pytest, no SQLite access. Run this at the start of a session to
  verify the live baseline before trusting any document's stated baseline — including this one.

## Scope discipline

Before making any change, a session should be able to state:

- the **committed baseline** it started from (commit, tag — verified live via `make context`, not
  assumed from a document);
- the **current stage contract** governing the work (`Milestones/contracts/*.md`);
- the contract's **authorized paths**;
- the contract's **prohibited paths**;
- the **governing decisions** for the specific change (from `Docs/decision_index.md`, narrowed to
  what the active stage contract actually links to);
- the **nearest affected tests** (from `Docs/change_impact_map.md`);
- the **final checkpoint boundary** — the point past which further work needs a new contract or an
  explicit instruction (stated in the active contract's "Commit boundary").

If any of these cannot be stated, stop and read the missing piece before editing — do not infer it
and do not proceed on an assumption.

## Handoff packet

End every session — in addition to the narrative completion packet below — with this compact block,
so a following session (human or agent) can resume without re-deriving context. Plain `KEY: value`
lines; no machine-generated JSON is required.

```
BASELINE_HEAD:
BASELINE_TAG:
CURRENT_STAGE:
MODIFIED_PATHS:
TESTS_RUN:
TESTS_NOT_RUN:
STATIC_GATES:
UNRESOLVED_FINDINGS:
COMMIT_STATUS:
NEXT_AUTHORIZED_ACTION:
```

## Completion packet template

End each implementation session with:

1. **Files created** and **files modified**, each with a one-line purpose.
2. **Deviations** from the approved plan, with justification, or an explicit "none".
3. **Command outputs** for install, CLI checks, lint, format check, type check, tests, and any
   repository checks.
4. **Total tests passed.**
5. **Invariants verified** — for example frozen-definition enforcement and absence of network access.
6. **`git status --short`** and **`git diff --stat`**.
7. **Confirmation that `git diff -- Docs Literature Milestones` is empty.** A non-empty diff is
   acceptable only when the session's own prompt expressly authorized those paths. In that case the
   packet must instead: (a) quote or otherwise identify the exact authorizing instruction, and
   (b) enumerate the exact documentation paths touched. A session may never rely on a prior
   session's authorization, on this file, or on a stage contract as the authorization.
8. **Confirmation that nothing was staged, committed, or pushed.**
9. **Open questions or risks** carried into the next milestone.
