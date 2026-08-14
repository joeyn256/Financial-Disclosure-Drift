PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.DEFAULT_GOAL := help
.PHONY: help venv install lint lint-changed format format-check typecheck typecheck-fast \
	typecheck-stop test test-parallel test-cov validate cohorts \
	secrets hygiene links decision-refs sqlite-check sec-validate sec-help \
	check check-fast fast context stage-gate clean

# Extra arguments for the pytest targets, e.g.
#   make test PYTEST_ARGS="tests/unit/test_cohorts.py -k frozen"
PYTEST_ARGS ?=
# Worker count for the parallel targets (Decision 076 R35, "Seven-Worker Full-Suite Development
# Standard"). Seven is the measured local optimum on the project owner's 8-core machine, not a
# universal constant: it is a plain `?=` default precisely so a busier machine or a CI runner with
# different core topology can choose its own, e.g. `make test-parallel WORKERS=4`.
WORKERS ?= 7
# xdist scheduling mode. `worksteal` seeds every worker up front and then re-balances whenever one
# runs dry, so a worker that draws the long subprocess tests does not become the critical path.
# Measured at WORKERS=7 on this repository: worksteal 60.75s, load 72.68s, both 3949 passed /
# 1 skipped. `loadfile` is deliberately not used -- grouping by file pins the two large modules
# (test_m3_acquisition.py, test_m3_cli.py) to single workers and makes them the bottleneck.
# Override with `make test-parallel DIST=load`.
DIST ?= worksteal

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

venv: ## Create the local virtual environment
	$(PYTHON) -m venv $(VENV)

install: ## Install the project with development dependencies
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev]"

lint: ## Run Ruff lint checks
	$(BIN)/ruff check .

lint-changed: ## Run Ruff lint and format checks on changed Python files only
	./scripts/ruff_changed.sh

format: ## Apply Ruff formatting
	$(BIN)/ruff format .

format-check: ## Verify formatting without writing changes
	$(BIN)/ruff format --check .

typecheck: ## Run mypy over the package
	$(BIN)/mypy src

typecheck-fast: ## Type-check via the mypy daemon (development loop only)
	@# `dmypy run` starts the daemon if needed and checks; subsequent calls are
	@# incremental. This is never the acceptance gate: `make check` runs `mypy src`.
	$(BIN)/dmypy run -- src

typecheck-stop: ## Stop the mypy daemon
	-$(BIN)/dmypy stop

test: ## Run the test suite serially (the reference path)
	@# The serial reference execution. Nothing may remove it: xdist is an optimization, and a
	@# suite that is only ever observed under a scheduler is a suite whose isolation is assumed
	@# rather than checked. Debugging, `--pdb`, and any parallel/serial disagreement start here.
	$(BIN)/pytest $(PYTEST_ARGS)

test-parallel: ## Run the test suite across xdist workers (WORKERS=7, DIST=worksteal)
	$(BIN)/pytest -n $(WORKERS) --dist $(DIST) $(PYTEST_ARGS)

test-cov: ## Run the test suite with coverage
	$(BIN)/pytest --cov --cov-report=term-missing $(PYTEST_ARGS)

validate: ## Validate configuration against the frozen definitions
	$(BIN)/python -m disclosure_drift validate-config

cohorts: ## Print the frozen temporal cohorts
	$(BIN)/python -m disclosure_drift show-cohorts

secrets: ## Scan tracked project files for secrets
	$(BIN)/python scripts/check_no_secrets.py

hygiene: ## Verify no raw data, database, release, or personal path is tracked
	$(BIN)/python scripts/check_repo_hygiene.py

links: ## Verify every relative Markdown link resolves to a tracked path
	$(BIN)/python scripts/check_markdown_links.py

decision-refs: ## Verify every decision section citation names a section that exists
	$(BIN)/python scripts/check_decision_section_refs.py

sqlite-check: ## Report the SQLite runtime version (floor 3.37 for STRICT tables)
	$(BIN)/python -c "import sqlite3, sys; print(sys.version.split()[0], sqlite3.sqlite_version)"

sec-help: ## Show the Milestone 2 SEC command group
	$(BIN)/python -m disclosure_drift sec --help

sec-validate: ## Validate SEC access policy and contact identity without any request
	$(BIN)/python -m disclosure_drift validate-sec-config

fast: lint-changed typecheck-fast ## Fast development validation (changed-file Ruff + mypy daemon)
	@# Deliberately does not run the suite: pass the tests you are working on, e.g.
	@#   make test PYTEST_ARGS="tests/unit/test_sec_parsers_and_census.py"
	@echo "fast validation passed: changed-file Ruff, mypy daemon."
	@echo "Run 'make check-fast' before accepting work; it is the acceptance gate."

check: lint format-check typecheck test secrets hygiene links decision-refs validate cohorts sec-help ## Run every gate serially
	@# Gates run sequentially and in a fixed order so a failure is attributable to one
	@# named gate. Running them concurrently measured 0.46s -> 0.21s, which does not
	@# justify interleaving their output.
	@#
	@# The conservative reference gate: identical gate set to `check-fast`, serial pytest.
	@# Reach for it when a parallel and a serial run disagree, when a test-isolation symptom
	@# appears, or when a reviewer wants the unscheduled execution order.

check-fast: lint format-check typecheck test-parallel secrets hygiene links decision-refs validate cohorts sec-help ## Run every gate, parallel pytest (recommended)
	@# Same substantive gate set as `check`, in the same order, differing in exactly one
	@# respect: pytest runs across $(WORKERS) xdist workers instead of serially. No gate is
	@# dropped, relaxed, or reordered, so a green `check-fast` covers what a green `check`
	@# covers. Decision 076 R35 makes this the routine full-validation command; `check`
	@# remains available unchanged as the serial reference.

context: ## Print a fast, read-only repository/state snapshot (branch, HEAD, stage, blocker)
	./scripts/context_snapshot.sh

stage-gate: ## Stage-boundary validation, in order: check, then sqlite-check, then context
	@# Convenience only. The accepted contract and decision records remain the authority
	@# on what a stage boundary requires; if this target ever diverges from them, they
	@# control. It weakens nothing: each gate is the existing target, unmodified.
	@#
	@# Recursive sub-makes rather than prerequisites. Prerequisites may be satisfied
	@# concurrently under `make -j`, which would destroy the required order; recipe lines
	@# run one at a time, in the order written, and a failing line stops the recipe before
	@# the next gate starts. `make -n stage-gate` shows that sequence.
	$(MAKE) check
	$(MAKE) sqlite-check
	$(MAKE) context

clean: ## Remove caches and build artifacts
	-$(BIN)/dmypy stop 2>/dev/null || true
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache .dmypy.json .coverage htmlcov
	find . -type d -name '__pycache__' -not -path './.venv/*' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -not -path './.venv/*' -prune -exec rm -rf {} +
