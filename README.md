# Financial Disclosure Drift

> **A preregistered financial-NLP and data-engineering project testing whether U.S. 10-K disclosures became more or less informative about subsequent operating performance during the generative-AI era.**

Financial Disclosure Drift is both a research project and a systems-engineering project. The research question is intentionally narrow; the engineering problem is not. Building a defensible answer requires point-in-time SEC data, deterministic cohort assignment, reproducible parsing, large-scale SQLite workflows, crash recovery, provenance tracking, and enough observability to distinguish a slow computation from a broken one.

**What this project demonstrates:** financial data engineering, temporal research design, fault-tolerant pipelines, SQLite at scale, reproducibility, provenance, testing, systems debugging, and disciplined AI-assisted software development.

---

## The research question

Public companies use Form 10-K filings to explain their financial condition, business risks, strategy, and recent performance. Generative AI and AI-assisted writing tools may have changed how those disclosures are prepared.

This project asks:

> **Have companies' 10-K disclosures become more or less aligned with their subsequent operating performance as generative AI and AI-assisted writing tools have become widely available?**

I do **not** assume that every company uses AI, and I do not infer causality from the post-2022 period alone. The project is preregistered around a temporal-reliability design: develop only on earlier filings, lock the methodology, and test it on later cohorts.

---

## What I built

At a high level, the system turns raw SEC filing evidence into a deterministic, auditable research dataset:

```text
SEC source evidence
      |
      v
immutable source observations
      |
      v
point-in-time registrant + filing census
      |
      v
deterministic selection / chunk plan
      |
      v
34 authenticated chunk worlds
      |
      v
5 level-one intermediates
      |
      v
staged level-two construction
      |
      v
durable receipts + provenance checks
      |
      v
locked research cohorts and later modeling
```

The historical-scale execution path is designed to survive interruption without silently changing the research sample or recomputing already accepted work.

---

## Engineering challenges I had to solve

The part of this project I am most proud of is not that the happy path works. It is that the pipeline has been repeatedly forced into difficult failure modes, and each failure produced a more observable and recoverable system.

### 1. Scaling SEC processing on constrained hardware

**Challenge**

The historical run grew far beyond a simple single-process ETL job. The current historical workload contains hundreds of thousands of selected SEC members, tens of millions of derived census rows, and more than 35 GB of authenticated level-one input.

I am running this on an 8 GB Apple-silicon Mac with limited local storage and an external SSD.

**Solution**

I replaced the monolithic workflow with a retention-aware multipass design:

- 34 deterministic source chunks;
- 5 authenticated level-one intermediates;
- a staged level-two build;
- explicit free-space admission before expensive operations;
- bounded RAM/cache settings;
- durable checkpoints between major phases;
- exact input, plan, and schedule identities so a restart cannot silently change the workload.

The goal is not merely to "make it fit." The goal is to make a resource-constrained run reproducible and restartable.

---

### 2. A monolithic SQLite merge produced roughly 38 GB of WAL

**Challenge**

An earlier large merge could run for hours while accumulating an enormous SQLite write-ahead log. One failed historical attempt retained roughly **38 GB of WAL** without producing a committed final result.

That made two weaknesses obvious:

1. a large transaction could consume storage for hours before failure;
2. a final process exit did not tell me *why* progress stopped.

**Solution**

I redesigned level-two construction around durable semantic stages and added statement-level observability:

- WAL-frame monitoring;
- explicit uncommitted-WAL watchdogs;
- per-statement progress journals;
- sampled free-space measurements;
- process peak-RSS measurements;
- stage receipts that are written only after successful commit;
- stage-by-stage checkpoint / truncation behavior rather than one giant all-or-nothing merge.

This converted "SQLite eventually failed" into a measurable systems problem with bounded failure modes.

---

### 3. Distinguishing a slow computation from a stuck computation

**Challenge**

During the first full historical-scale level-two attempt, stage **S3 (`census_parsed_records`)** ran for the entire configured three-hour child limit.

A process listing alone was ambiguous: the worker was often I/O-bound and could appear nearly idle.

**Solution**

The pipeline's statement journal recorded independent progress signals every few seconds:

- SQLite VM-step ticks;
- WAL frame growth;
- WAL byte length;
- free disk space;
- RSS;
- chained event identities.

Immediately before the timeout, both VM work and WAL growth were still increasing. The resulting traceback then proved that Python's configured `10,800` second child timeout—not a semantic error, disk-full condition, or WAL watchdog—terminated the run.

That let me classify the event correctly as a **healthy-progress timeout** instead of rewriting a working algorithm.

**Current recovery approach:** preserve the failed attempt as evidence, reuse durable prior stages where the restart contract permits it, and run the successor under a larger governed time envelope rather than blindly retrying or deleting evidence.

---

### 4. Recovering from failures without losing expensive work

**Challenge**

Long-running data jobs make "just rerun it" expensive and dangerous. A retry can also become scientifically invalid if the inputs, code, ordering, or sample have drifted.

**Solution**

I built restart semantics around durable state rather than process memory:

- committed stages authenticate before reuse;
- the first incomplete stage is identified explicitly;
- incomplete attempts remain preserved as evidence;
- completed stages are not silently recomputed;
- stage identity includes the material inputs needed to detect drift;
- restart boundaries require fresh host/storage/input authentication.

This turns interruption recovery into a deterministic state transition rather than an operator guess.

---

### 5. Reusing expensive intermediates after the codebase evolved

**Challenge**

By the time the historical level-one intermediates were complete, the repository had advanced. Rebuilding all 34 historical chunks simply because HEAD changed would have discarded many hours of verified computation.

But reusing old outputs without proof would have been worse.

**Solution**

I implemented a **producer-to-consumer provenance compatibility bridge**.

The bridge proves that the code paths capable of affecting the level-one products are compatible across the producing and consuming revisions. It binds:

- producer HEAD/tree;
- consumer HEAD/tree;
- the exact certificate;
- the historical plan and schedule;
- authenticated input identities.

I also independently reviewed and corrected the bridge after finding two provenance defects: certificate self-identity handling and a hash/parse time-of-check/time-of-use gap.

The result is a general principle I use throughout the project:

> **Reuse expensive computation only when compatibility is proven—not merely because the files still exist.**

---

### 6. Operating safely with limited storage, power, and I/O

**Challenge**

The development machine has only one reliably usable physical port. In some configurations, external storage and direct power compete for that port. Long runs can also be invalidated by a disconnect, sleep, reboot, insufficient free space, or an unqualified storage path.

**Solution**

I treated the host as part of the execution contract:

- external-SSD transport qualification;
- sustained-I/O tests before critical work;
- host power / lid-state guards;
- `caffeinate`-based sleep prevention during controlled runs;
- disk-space admission with explicit reserve and transient budgets;
- durable phase boundaries before physical reconnection or restart;
- no automatic retries after an unexpected failure.

That is more infrastructure than a typical research notebook requires, but it is what allowed the project to progress safely on real hardware constraints.

---

### 7. Keeping AI-assisted development auditable instead of letting agents "just code"

I use AI heavily in this project, but I deliberately separate **reasoning authority, implementation, and review**.

My working model is:

| Tool | Role |
|---|---|
| **ChatGPT / GPT-5.6 Sol** | architecture, research-method governance, acceptance criteria, failure adjudication |
| **Claude Code / Claude Opus** | implementation, testing, debugging, bounded independent review |
| **OpenClaw** | orchestration layer for model sessions, local-agent workflows, and remote operations |
| **GitHub Actions** | independent repository validation on committed code |
| **Tailscale / local Terminal** | secure remote monitoring and stable long-running execution |

#### Why I used OpenClaw

I experimented with **OpenClaw** as an orchestration and remote-operations layer so I could coordinate long Claude sessions, model routing, and local workflows from a persistent Mac environment.

I added explicit controls around it:

- fixed repository working directories;
- separate read-only audit and write-authorized implementation modes;
- no automatic push/merge authority;
- explicit task packets defining what an agent may change;
- model-role separation and cross-review;
- remote access through Tailscale rather than exposing the local gateway publicly.

OpenClaw itself also became an engineering lesson. Its mobile interface could not reliably accept follow-up prompts while a long run was active. Instead of weakening process controls to work around the tool, I moved critical execution to the Mac's local Terminal and kept remote tooling limited to read-only monitoring.

That decision reflects how I approach engineering tools generally: **use automation where it improves reliability; remove it from the critical path when it becomes the reliability risk.**

---

### 8. Preventing temporal leakage in a financial research problem

**Challenge**

A technically correct pipeline can still answer the wrong research question if later information leaks into model development or cohort construction.

**Solution**

The project freezes cohort boundaries and point-in-time rules in code. Configuration mirrors those values and fails closed if it disagrees.

| Cohort | Filing dates | Role |
|---|---|---|
| Development | 2010-01-01 → 2021-12-31 | feature / estimator development |
| Transition evaluation | 2022-01-01 → 2023-12-31 | locked evaluation |
| Primary test | 2024 | untouched confirmatory test |
| Prospective test | 2025 | predictions frozen before outcomes mature |
| Monitoring | 2026 | outcome-free monitoring |

The project is designed so the engineering layer protects the statistical design instead of relying on analyst memory.

---

## Current scale

As of the current Milestone 3 engineering work:

- **34** historical source chunks completed and authenticated;
- **5** level-one intermediates completed and authenticated;
- **334k+** historical selected members in the full-scale plan;
- **35.5+ GB** of authenticated level-one input to the historical level-two build;
- **45M+** expected derived rows across the historical level-two census tables;
- **6,000+** automated tests in the current engineering suite;
- network access remains explicitly gated rather than enabled by default.

The current frontier is full historical level-two qualification. The most recent S3 run demonstrated healthy progress for the entire three-hour child budget and was stopped by the configured timeout, creating a measured recovery problem rather than an unexplained failure.

---

## Reliability and validation philosophy

The repository is intentionally defensive:

- deterministic plans instead of "whatever is current today";
- immutable source observations;
- explicit provenance and content hashes;
- create-once evidence where ambiguity would be dangerous;
- fail-closed configuration;
- no silent retries after unexpected failures;
- focused tests during development and full validation at acceptance boundaries;
- linting, typing, unit/integration tests, secret scanning, and repository-hygiene checks;
- independent review at consequential milestones.

A failure is useful only if the system preserves enough evidence to explain it.

---

## Tech stack

**Core:** Python 3.12, SQLite, Pydantic, PyYAML, argparse
**Quality:** pytest, pytest-xdist, mypy, Ruff, GitHub Actions
**Data / systems:** SEC EDGAR source data, deterministic JSON/JSONL evidence, SQLite WAL instrumentation, external-SSD execution
**Engineering workflow:** Git, GitHub, Claude Code, ChatGPT, OpenClaw, Tailscale

---

## Project status

**Milestones 0-2:** accepted and closed.

**Milestone 3:** active engineering / historical-scale qualification.

The project has moved well beyond the original offline architecture: chunked multipass historical processing, restartability, storage qualification, stage-level observability, provenance compatibility, and full-scale level-two execution are now part of the working system.

No final predictive-model results are presented yet. That is intentional: the project does not publish model conclusions before the preregistered data and execution gates are satisfied.

For the detailed research record, contracts, decisions, and milestone history, see:

- [`Docs/`](Docs/)
- [`Docs/Decisions/`](Docs/Decisions/)
- [`Milestones/`](Milestones/)
- [`Docs/preregistration.md`](Docs/preregistration.md)

---

## Formal preregistered research question

> Do models developed exclusively on pre-2022 Form 10-K disclosures lose predictive accuracy or calibration when applied to 2024-era filings, and are evidence-grounded models more robust than style-heavy models under observed disclosure drift and controlled factual-preservation rewrites?

The prospective design also includes a 2025 replication cohort and outcome-free 2026 monitoring.

---

## What this project does not claim

- It does not claim to verify AI authorship of any filing.
- It does not claim to detect fraud, deception, or misconduct.
- It does not infer a causal effect of generative AI from post-2022 timing alone.
- It does not provide investment advice or company risk ratings.
- It does not present final model results before the preregistered evaluation gates are reached.

---

## Local setup

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

# SEC-enabled environment only when explicitly required:
python -m pip install -e ".[dev,sec]"
cp .env.example .env
```

The default configuration keeps network access disabled.

Useful checks:

```bash
python -m disclosure_drift --help
python -m disclosure_drift validate-config
python -m disclosure_drift show-cohorts
python -m disclosure_drift validate-sec-config
```

Full repository validation:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/check_no_secrets.py
python scripts/check_repo_hygiene.py
```

---

## Repository map

```text
Docs/                       preregistration, decisions, data dictionaries, technical records
Milestones/                 milestone contracts and completion records
configs/                    tracked project configuration
src/disclosure_drift/       Python package
src/disclosure_drift/sec/   SEC identity, temporal, source, and census logic
tests/                      unit + integration tests
scripts/                    repository / validation utilities
.github/workflows/          CI
data/                       generated data is ignored except documentation
```

Raw and generated SEC corpora, SQLite databases, WAL/SHM files, private evidence, and secrets are intentionally excluded from Git.

---

## Why this project matters to me

The research question sits at the intersection of finance, data science, and AI, but the project has also become a practical exercise in systems engineering.

The recurring pattern has been:

1. scale until a hidden assumption breaks;
2. instrument the failure instead of guessing;
3. preserve evidence;
4. redesign the smallest failing boundary;
5. prove restart / compatibility behavior;
6. continue without weakening the research design.

That is the kind of engineering work I want to keep doing: building analytical systems that remain trustworthy when the data is large, the runtime is long, and the first design does not survive contact with reality.

---

## License

MIT. See [`LICENSE`](LICENSE).
