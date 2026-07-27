# CLAUDE.md — collaboration rules for Disclosure Drift

This file governs every assistant session in this repository. It encodes the collaboration rules
approved by the project owner (Joey) at Milestone 1.

## Project context

Disclosure Drift is a preregistered temporal-reliability study of Form 10-K disclosures. The research
design is frozen. Engineering work implements that design; it never redefines it.

Authoritative records, in precedence order:

1. `Docs/preregistration.md`
2. `Docs/Decisions/decision_001..016` — see `Docs/Decisions/decision_registry.md` for status, and
   for which record controls when two decisions address the same topic (e.g. Decision 010 controls
   the cohort date-source rule; Decision 003 controls everything else about the temporal split)
3. `Docs/leakage_register.md` and `Docs/research_risk_register.md`
4. `Milestones/milestone_XX_*.md` — the active milestone specification

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
    read-only during engineering milestones.
15. **End every implementation session with a structured completion packet.** See the template below.

## Milestone 1 boundaries

Permitted: packaging, configuration, logging, CLI, tests, CI, repository documentation.

Prohibited: downloading or querying SEC filings, ingestion code, production database design, filing
section parsing, XBRL outcome definitions, research features, the Disclosure Drift Index, rewrite
prompts or LLM provider calls, model training, and any access to 2022-2026 outcomes.

## Engineering conventions

- Python 3.12, `src` layout, type hints in core modules.
- Ruff for lint and format (line length 100); mypy strict over `src`; pytest for tests.
- Minimal runtime dependencies; development dependencies separated in the `dev` extra.
- No network access in package code outside a milestone that explicitly authorizes it.
- Configuration is typed, rejects unknown fields, and produces actionable error messages.
- Only allowlisted `DISCLOSURE_DRIFT_*` environment variables are honoured; secrets are resolved on
  demand and never logged, printed, or stored on a model.
- Tests use temporary paths and fixtures, never a machine-specific directory.

## Completion packet template

End each implementation session with:

1. **Files created** and **files modified**, each with a one-line purpose.
2. **Deviations** from the approved plan, with justification, or an explicit "none".
3. **Command outputs** for install, CLI checks, lint, format check, type check, tests, and any
   repository checks.
4. **Total tests passed.**
5. **Invariants verified** — for example frozen-definition enforcement and absence of network access.
6. **`git status --short`** and **`git diff --stat`**.
7. **Confirmation that `git diff -- Docs Literature Milestones` is empty.**
8. **Confirmation that nothing was staged, committed, or pushed.**
9. **Open questions or risks** carried into the next milestone.
