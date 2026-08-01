# Financial Disclosure Drift

<!-- BEGIN FRIENDLY PROJECT OVERVIEW -->

## Did the rise of generative AI change how informative corporate annual reports are?

Public companies use Form 10-K filings to explain their financial condition, business risks,
strategy, and recent performance. Investors rely on these reports to understand not only what has
already happened, but also whether management's discussion reflects the company's underlying
operating condition.

Generative AI and AI-assisted writing tools may have changed how companies prepare these
disclosures. Annual reports may now be clearer and more consistent—or they may become more polished,
standardized, and less revealing about company-specific risks.

**Financial Disclosure Drift** investigates whether the language in corporate 10-K filings became
more or less aligned with companies' subsequent operating performance during the generative-AI era.

> **Central research question:** Have companies' 10-K disclosures become more or less aligned with
> their subsequent operating performance as generative AI and AI-assisted writing tools have become
> widely available?

The project compares filings across carefully separated historical periods, measures changes in
disclosure language, and tests whether those disclosures remain informative about later
operating-margin outcomes.

### What does “disclosure drift” mean?

Disclosure drift is a change in the relationship between what a company says in its annual report
and what happens to the business afterward.

For example, a filing may become more polished, cautious, repetitive, or optimistic without becoming
more informative about the company's underlying financial direction. This project tests whether
those changes make 10-K disclosures better or worse at reflecting subsequent operating performance.

### What this project can—and cannot—claim

This study evaluates changes associated with the generative-AI adoption period. It does not assume
that every company used AI, and it does not treat the timing of generative AI adoption alone as proof
that AI caused a change in disclosure quality.

Instead, the project tests whether measurable changes in 10-K language—and in its relationship with
subsequent operating performance—occurred across preregistered historical periods.

<!-- END FRIENDLY PROJECT OVERVIEW -->


A preregistered temporal-reliability study of U.S. Form 10-K disclosure narratives.

**Status:** **Milestones 0, 1, and 2 are formally accepted and closed** (Decision 026, 2026-07-31),
tagged `m0-complete`, `m1-complete`, and `m2-complete`. Milestone 0 delivered the novelty audit,
preregistration, and definition freeze; Milestone 1 the reproducible engineering foundation; and
**Milestone 2 implementation ends at accepted Stage M2.3 S6** — the M2.2 offline foundation
(approved-source retrieval policy, immutable source observations, defensive bulk-archive handling,
source-native parsers, the transactional registrant census, restart recovery, deterministic QA, and
R3 durability and provenance hardening) plus the M2.3 deterministic pilot architecture (the
candidate/selection/manifest schema, entity selection, joint entity–accession selection, reserve
packages and dispositions, persistence, reconstruction and replay, and pilot-manifest construction
with terminal result identity, lifecycle enforcement, verification, and atomicity).

**What is complete is a deterministic offline architecture** — through manifest construction,
verification, and replay. **No live SEC pilot has been executed.** **Milestone 3 is the next planning
phase**, and Milestone 3 implementation is **not authorized and not begun**. **No SEC data has been
downloaded, no filing body is permitted at this stage, no real pilot sample exists, no manifest root
has been approved or published, and no modeling or outcome code exists.**

## Formal preregistered research question

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
# SEC-enabled acceptance environment only:
python -m pip install -e ".[dev,sec]"
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

The default configuration keeps network access disabled. `sec census --dry-run` validates and
prints the approved metadata plan while making zero requests. An actual `sec census` run requires
the `[sec]` extra, an explicit configuration with `network.enabled: true`, and a valid
`DISCLOSURE_DRIFT_SEC_USER_AGENT`; it still refuses filing bodies, primary documents, accession
indexes, complete submissions, and XBRL packages. Exit codes: 0 success, 1 configuration error,
2 usage, 3 stage not enabled, 4 gate failure.

### Census plan inputs

Every plan input is explicit. Nothing is inferred from today's date, so a plan is
reproducible on any later day:

```bash
python -m disclosure_drift sec census --dry-run \
  --coverage-start 2009-01-01 --coverage-end 2024-12-31 --as-of 2025-01-15 \
  --calendar-year 2024
```

| Argument | Meaning |
|---|---|
| `--coverage-start` | First date of the requested coverage window |
| `--coverage-end` | Last date of the requested coverage window |
| `--as-of` | Date the plan is evaluated against; decides which quarters are closed |
| `--include-open-quarter` | Also retrieve the provisional open quarter; it stays provisional |
| `--calendar-year` | Year the annual EDGAR calendar instance must cover |
| `--dry-run` | Print the plan and make zero requests |

`--coverage-start`, `--coverage-end`, and `--as-of` must be supplied together; a partial
window is refused rather than completed from the clock. Quarters ending on or before the
as-of date are required and block completion when missing; the quarter containing the
as-of date is provisional and optional; quarters starting after it are not planned at all.
See the quarterly index-instance policy in `Docs/sec_data_dictionary.md`.

## Test, lint, and type-check commands

Full acceptance validation — run this before accepting work:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/check_no_secrets.py
python scripts/check_repo_hygiene.py
```

`make check` runs all of the above plus both CLI validation commands, sequentially and in a fixed
order so a failure is attributable to one named gate. CI runs the same sequence on pull requests and
pushes to `main`.

Fast development loop — `make fast` runs the first two:

```bash
./scripts/ruff_changed.sh          # Ruff lint + format on changed Python files only
dmypy run -- src                   # mypy daemon; re-runs are incremental
pytest tests/unit/test_cohorts.py  # just the tests you are working on
```

The daemon and the changed-file script are conveniences, never gates: `mypy src` and the
full-repository Ruff commands above are what acceptance depends on. Stop the daemon with
`make typecheck-stop`.

The suite runs in parallel with [pytest-xdist](https://pytest-xdist.readthedocs.io/) (a `dev`
dependency). It is opted into per invocation rather than through `addopts`, so the default `pytest`
stays serial and debuggable:

```bash
pytest -n auto      # ~8.7s on an 8-core machine; make test-parallel
pytest              # ~19s serial
```

Tests are order-independent and hold no shared writable state, so any worker count is valid. CI runs
the serial suite: at this size the worker start-up cost is not worth the added variability.

## Repository structure

```text
Docs/                    Research record: preregistration, registers, Decisions 001-026, SEC dictionary
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
- SQLite is the authoritative observation catalog. Its JSONL file is a deterministic audit
  projection: appends are file-`fsync`ed before SQLite is marked projected, rebuilds use a
  temporary file plus atomic replacement and parent-directory `fsync`, and startup validates and
  reconstructs any missing, truncated, malformed, reordered, duplicated, or altered projection.
- Every applied migration is checked against the exact packaged name and SQL checksum before
  further writes. Migration 0008 adds enforced reuse and supersession lineage; dangling,
  self-referential, cyclic, or identity-incompatible links fail closed.
- Reused snapshots retain and verify the complete shared-object representation, hashes, sizes,
  encoding, parser version, path, and evidence-owner lineage. A conditional response cannot turn
  incomplete or damaged prior evidence into a usable observation.
- Streamed transports return an explicitly closeable byte stream. Exhaustion, explicit `close()`,
  context-manager exit, and iteration failure release the local spool exactly once; the HTTP
  response is already closed before the caller receives that stream.

## License

MIT. See `LICENSE`.
