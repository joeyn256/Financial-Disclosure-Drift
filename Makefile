PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.DEFAULT_GOAL := help
.PHONY: help venv install lint lint-changed format format-check typecheck typecheck-fast \
	typecheck-stop test test-parallel test-cov validate cohorts \
	secrets hygiene sqlite-check sec-validate sec-help check fast context clean

# Extra arguments for the pytest targets, e.g.
#   make test PYTEST_ARGS="tests/unit/test_cohorts.py -k frozen"
PYTEST_ARGS ?=
# Worker count for the parallel target. `auto` measured fastest on an 8-core machine;
# override for a busier one, e.g. `make test-parallel WORKERS=4`.
WORKERS ?= auto

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

test: ## Run the test suite
	$(BIN)/pytest $(PYTEST_ARGS)

test-parallel: ## Run the test suite across xdist workers (WORKERS=auto)
	$(BIN)/pytest -n $(WORKERS) $(PYTEST_ARGS)

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
	@echo "Run 'make check' before accepting work; it is the acceptance gate."

check: lint format-check typecheck test secrets hygiene validate cohorts sec-help ## Run every gate
	@# Gates run sequentially and in a fixed order so a failure is attributable to one
	@# named gate. Running them concurrently measured 0.46s -> 0.21s, which does not
	@# justify interleaving their output.

context: ## Print a fast, read-only repository/state snapshot (branch, HEAD, stage, blocker)
	./scripts/context_snapshot.sh

clean: ## Remove caches and build artifacts
	-$(BIN)/dmypy stop 2>/dev/null || true
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache .dmypy.json .coverage htmlcov
	find . -type d -name '__pycache__' -not -path './.venv/*' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -not -path './.venv/*' -prune -exec rm -rf {} +
