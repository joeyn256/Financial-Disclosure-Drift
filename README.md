# Disclosure Drift

A preregistered temporal-reliability study of U.S. Form 10-K disclosure narratives.

**Status:** Milestone 0 (novelty audit, preregistration, definition freeze) and Milestone 1
(reproducible engineering foundation) are complete. Milestone 2 is in progress at **Stage M2.1**,
which is documentation and offline foundation only: SEC policy modules, temporal and availability
policy, reason codes, path policy, and CLI skeletons. **No SEC data has been downloaded, no HTTP
client is installed, and no research code exists.**

## Research question

Do models developed exclusively on pre-2022 Form 10-K disclosures lose predictive accuracy or
calibration when applied to 2024-era filings, and are evidence-grounded models more robust than
style-heavy models under observed disclosure drift and controlled factual-preservation rewrites?

## Narrow final contribution

Quoted from `Docs/Decisions/decision_006_final_contribution.md`, which is frozen:

> Disclosure Drift is a preregistered temporal-reliability study testing whether models developed
> exclusively on pre-2022 Form 10-K disclosures lose predictive accuracy or calibration when
> forecasting one-year-ahead, industry-adjusted operating-margin deterioration in the untouched 2024
> filing cohort; whether any reliability loss is concentrated in style-dependent representations and
> associated with a frozen Disclosure Drift Index; and whether evidence-grounded models are more
> stable than style-heavy models under both observed disclosure change and paired, fact-preserving
> rewrites. The design includes a prospective 2025 replication and outcome-free 2026 monitoring with
> timestamped frozen predictions.

## Temporal cohorts

Cohorts are assigned by the official SEC filing date of the original Form 10-K (Decision 010).

| Cohort | Cohort-assignment dates | Role |
|---|---|---|
| Development | 2010-01-01 to 2021-12-31 | Feature development, estimator and hyperparameter selection, rolling-origin selection |
| Transition evaluation | 2022-01-01 to 2023-12-31 | Locked evaluation; no predictive-model tuning |
| Final primary test | 2024-01-01 to 2024-12-31 | One untouched confirmatory evaluation |
| Prospective secondary test | 2025-01-01 to 2025-12-31 | Predictions frozen before outcome linkage; evaluated after the 2027-03-31 maturity gate |
| Current monitoring cohort | 2026-01-01 to 2026-12-31 | Outcome-free language and data-quality monitoring; earliest outcome gate 2028-03-31 |

These windows, both maturity gates, and the bootstrap seed `20260725` are **frozen research
definitions**. They live in `src/disclosure_drift/cohorts.py`, which is the canonical source of
truth. `configs/project.yaml` mirrors them and configuration loading hard-fails on any disagreement.
No environment variable can override them. Changing one requires an approved decision record in
`Docs/Decisions/` plus a reviewed code change.

**Cohort assignment uses the official SEC filing date** per
`Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md`, recorded as Deviation
D001 in `Docs/preregistration.md` section 25.1. The SEC acceptance date produces a separate
audit-only cohort that never determines analysis membership, and the point-in-time cutoff uses the
approved public-availability boundary with a tri-state comparison
(`eligible` / `ineligible` / `indeterminate`).

## What this project does not claim

- It does not claim to verify AI authorship of any filing. AI-likeness measures are noisy proxies.
- It does not claim to detect fraud, deception, or misconduct.
- It does not claim causal effects of generative AI from post-2022 timing alone.
- It does not provide investment advice, and its outputs are not company risk ratings.
- It does not claim to be the first study of temporal drift, 10-K prediction, narrative
  transformation, or evidence-grounded financial NLP. See
  `Docs/Decisions/decision_006_final_contribution.md` for the full list of prohibited claims.

No model results exist yet, and none will be presented here until they are produced under the
preregistered protocol.

## Local setup

Requires Python 3.12 (see `.python-version`).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env    # optional offline; required before any SEC request
```

`make install` performs the same install into `.venv`.

### Environment variables

These are the only recognized variables. Any other `DISCLOSURE_DRIFT_*` variable raises an error, so
a typo never passes silently.

| Variable | Purpose |
|---|---|
| `DISCLOSURE_DRIFT_SEC_USER_AGENT` | Recognized secret. Resolved on demand, never logged or printed. Optional for offline commands; mandatory at the network boundary, which validates it before any request. |
| `DISCLOSURE_DRIFT_DATA_ROOT` | Override the data root. May be an absolute path. |
| `DISCLOSURE_DRIFT_LOG_DIR` | Override the log directory. May be an absolute path. |
| `DISCLOSURE_DRIFT_LOG_LEVEL` | Override the log level. |
| `DISCLOSURE_DRIFT_LOG_TO_FILE` | Enable or disable file logging. |
| `DISCLOSURE_DRIFT_BACKUP_ROOT` | Backup root for Milestone 2 backup and restore. May be absolute. Optional offline; validated by any command that needs it. |
| `DISCLOSURE_DRIFT_CONFIG` | Use an alternate configuration file. |

The audit directory is always `{data_root}/audit/sec` and is not separately configurable.

The tracked configuration contains no absolute or machine-specific path; loading rejects one if it
ever appears there.

## Validation commands

```bash
python -m disclosure_drift --help
python -m disclosure_drift validate-config
python -m disclosure_drift show-cohorts
python -m disclosure_drift validate-sec-config
python -m disclosure_drift sec --help
```

Every command is offline and read-only. None downloads filings or processes data. Milestone 2
commands that would need the network refuse before request construction when
`DISCLOSURE_DRIFT_SEC_USER_AGENT` is missing or invalid, and exit 3 while their stage is not enabled.
Exit codes: 0 success, 1 configuration error, 2 usage, 3 stage not enabled, 4 gate failure.

## Test, lint, and type-check commands

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/check_no_secrets.py
python scripts/check_repo_hygiene.py
```

`make check` runs all of the above plus both CLI validation commands. CI runs the same sequence on
pull requests and pushes to `main`.

## Repository structure

```text
Docs/                    Research record: preregistration, registers, Decisions 001-010, SEC dictionary
Literature/              Literature matrix, search log, bibliography, competitor audit
Milestones/              Milestone specifications and completion records
configs/project.yaml     Project configuration; mirrors the frozen definitions
data/                    Generated, git-ignored except data/README.md (Decision 009)
src/disclosure_drift/    Package: cohorts, config, logging, paths, reasons, errors, CLI
src/disclosure_drift/sec/  SEC identity, temporal, availability, response, and source policy
tests/unit/              Configuration, cohort-integrity, and logging tests
tests/integration/       CLI and offline-behaviour tests
scripts/                 Repository maintenance checks
.github/workflows/ci.yml Lint, type-check, test, CLI smoke, and secret-scan pipeline
```

`Docs/`, `Literature/`, and `Milestones/` are the research record. Engineering milestones do not
modify them, with two explicitly authorized Milestone 2 exceptions: the new Milestone 2 documents,
and the append-only Deviation D001 entry in `Docs/preregistration.md` section 25.1. Existing protocol
wording and Decisions 001-006 are unchanged; version-suffixed files are retained history.

## Data governance

- Raw and generated SEC corpora are **never** committed. Everything under `data/` is git-ignored
  except `data/README.md`, and `*.sqlite3`, `*-wal`, `*-shm`, `*.parquet`, `*.part`, and `logs/`
  are ignored everywhere. `scripts/check_repo_hygiene.py` enforces this.
- Secrets are never committed. `.env` is ignored; placeholder values live only in `.env.example`,
  which uses reserved `example.com` addresses.
- The point-in-time source of truth is the SEC filing and its SEC metadata. External corpora may be
  used only for validation, per `Docs/preregistration.md` section 5.
- Raw data is never deleted or silently reprocessed; lineage and row-count changes are reported.

## License

MIT. See `LICENSE`.
