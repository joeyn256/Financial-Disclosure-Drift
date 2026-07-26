# Claude Code Assignment — Milestone 1: Reproducible Project Foundation

You are working in the repository:

`~/Projects/Financial Disclosure Drift`

## Mandatory operating mode

1. Begin in plan mode.
2. Read all current Milestone 0 research files before proposing changes, especially:
   - `Docs/preregistration.md`
   - `Docs/leakage_register.md`
   - `Docs/research_risk_register.md`
   - `Docs/Decisions/decision_001_novelty_boundary.md`
   - `Docs/Decisions/decision_002_primary_outcome.md`
   - `Docs/Decisions/decision_003_temporal_split.md`
   - `Docs/Decisions/decision_004_evaluation_protocol.md`
   - `Docs/Decisions/decision_005_2025_2026_recency_extension.md`
   - `Docs/Decisions/decision_006_final_contribution.md`
   - `Milestones/milestone_00_completion.md`
3. Inspect the repository.
4. Return an implementation plan and ambiguity report.
5. Make no edits until Joey explicitly approves the plan.
6. Do not commit or push unless explicitly instructed.

## Milestone goal

Create a professional, reproducible Python research-engineering foundation. A clean clone must be
able to install the project, validate the environment, run tests, run linting and type checks, and
execute a harmless sample CLI command.

This milestone is infrastructure only.

## Strictly prohibited in Milestone 1

Do not:

- download or query SEC filings;
- implement SEC ingestion;
- design the production database;
- parse filing sections;
- define or calculate XBRL outcomes;
- implement research features;
- implement the Disclosure Drift Index;
- create rewrite prompts or call an LLM provider;
- train predictive models;
- access or construct 2022–2026 outcomes;
- alter frozen research definitions;
- rename or delete existing Milestone 0 files;
- commit large data, secrets, or generated corpora.

## Required repository additions

Preserve the existing capitalized directories `Docs`, `Literature`, and `Milestones`.

Create or configure:

```text
README.md
CLAUDE.md
LICENSE
pyproject.toml
.python-version
.env.example
Makefile
.github/workflows/ci.yml
configs/
    project.yaml
src/
    disclosure_drift/
        __init__.py
        __main__.py
        cli.py
        config.py
        logging_config.py
tests/
    unit/
    integration/
scripts/
```

Add other small foundation files only when justified in the plan.

## Python and dependency requirements

- Target Python 3.12.
- Use a standard `src` package layout.
- Use `pytest`.
- Use Ruff for linting and formatting.
- Use mypy for static type checking.
- Use type hints in core modules.
- Keep runtime dependencies minimal.
- Separate optional development dependencies.
- Avoid premature orchestration frameworks.
- Do not introduce notebooks in this milestone.

## Configuration requirements

Implement a typed configuration loader that:

- loads `configs/project.yaml`;
- supports environment-variable overrides for secrets or machine-specific paths;
- validates required values;
- never hardcodes Joey’s absolute local path;
- provides actionable error messages;
- exposes the current research cohort boundaries without changing them;
- does not contain API keys or a real email address.

The sample config may include:

- project name;
- data-root placeholder;
- log level;
- SEC user-agent environment-variable name;
- conservative request-rate placeholder;
- development, transition, primary-test, prospective, and monitoring dates.

Do not implement network access.

## CLI requirements

Provide harmless commands such as:

```bash
python -m disclosure_drift --help
python -m disclosure_drift validate-config
python -m disclosure_drift show-cohorts
```

The CLI must not perform downloads or data processing.

## Logging requirements

Add structured, readable logging with:

- console output;
- optional file output controlled by configuration;
- timestamps;
- logger names;
- log levels;
- no secret values.

## Testing requirements

At minimum, test:

- package import;
- configuration loading;
- environment overrides;
- invalid configuration errors;
- cohort boundary integrity;
- CLI help;
- `validate-config`;
- `show-cohorts`;
- logging initialization;
- absence of network activity from foundation commands.

Use temporary paths and fixtures. Tests must not depend on Joey’s machine-specific directory.

## CI requirements

GitHub Actions must run on pull requests and pushes to `main` and must:

1. install Python 3.12;
2. install development dependencies;
3. run Ruff;
4. run mypy;
5. run pytest;
6. fail clearly when any check fails.

Do not add deployment or data-download workflows.

## `CLAUDE.md` requirements

Include the approved collaboration rules:

- read the active milestone specification before editing;
- plan before substantial changes;
- never alter frozen research definitions;
- never use future information in features;
- never silently change an outcome;
- never delete raw data;
- never commit secrets or large datasets;
- test every new transformation;
- preserve lineage;
- use deterministic seeds;
- report row-count changes;
- stop when invariants fail;
- do not commit or push unless instructed;
- do not edit outside milestone scope without explanation;
- end every implementation session with a structured completion packet.

## README requirements

The initial README should explain:

- the research question;
- the narrow final contribution;
- the temporal cohorts;
- current status: Milestone 0 complete, Milestone 1 foundation;
- the project’s non-claims about AI authorship, fraud, or investment advice;
- local setup;
- validation commands;
- test/lint/type-check commands;
- repository structure;
- data-governance rule that raw SEC corpora are not committed.

Do not present untested results.

## Acceptance tests

Milestone 1 is complete only when all of these pass from a clean environment:

```bash
python -m pip install -e ".[dev]"
python -m disclosure_drift --help
python -m disclosure_drift validate-config
python -m disclosure_drift show-cohorts
ruff check .
ruff format --check .
mypy src
pytest
```

Also verify:

- no network request occurs;
- no secret exists in tracked files;
- no raw or generated data is tracked;
- existing research documents remain unchanged unless the plan explicitly identifies a necessary
  cross-reference update approved by Joey.

## Plan-mode response required before editing

Return:

1. repository-state summary;
2. exact proposed files to add;
3. exact proposed files to modify;
4. dependency proposal;
5. configuration schema proposal;
6. testing plan;
7. CI plan;
8. risks and ambiguities;
9. commands you expect to run;
10. confirmation that no edits were made.

Stop after the plan.
