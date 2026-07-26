PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.DEFAULT_GOAL := help
.PHONY: help venv install lint format format-check typecheck test test-cov validate cohorts \
	secrets hygiene sqlite-check sec-validate sec-help check clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

venv: ## Create the local virtual environment
	$(PYTHON) -m venv $(VENV)

install: ## Install the project with development dependencies
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev]"

lint: ## Run Ruff lint checks
	$(BIN)/ruff check .

format: ## Apply Ruff formatting
	$(BIN)/ruff format .

format-check: ## Verify formatting without writing changes
	$(BIN)/ruff format --check .

typecheck: ## Run mypy over the package
	$(BIN)/mypy src

test: ## Run the test suite
	$(BIN)/pytest

test-cov: ## Run the test suite with coverage
	$(BIN)/pytest --cov --cov-report=term-missing

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

check: lint format-check typecheck test secrets hygiene validate cohorts sec-help ## Run every gate

clean: ## Remove caches and build artifacts
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find . -type d -name '__pycache__' -not -path './.venv/*' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -not -path './.venv/*' -prune -exec rm -rf {} +
