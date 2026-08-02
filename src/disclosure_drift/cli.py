"""Command-line interface for Disclosure Drift.

Milestone 1 commands (``validate-config``, ``show-cohorts``) are offline and
read-only. Stage M2.2 enables the bounded ``sec census`` workflow only when the
configuration explicitly enables network access and the SEC contact identity is
valid. The census retrieves approved metadata sources; filing bodies and packages
remain prohibited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from logging import Logger
from pathlib import Path
from typing import Final

from disclosure_drift import __version__
from disclosure_drift.cohorts import (
    COHORT_ORDER,
    FROZEN_BOOTSTRAP_SEED,
    FROZEN_COHORTS,
    FROZEN_MATURITY_GATES,
    FROZEN_SOURCE_RECORDS,
)
from disclosure_drift.config import ConfigError, ProjectConfig, load_config
from disclosure_drift.errors import DisclosureDriftError, GateFailureError, SecUserAgentError
from disclosure_drift.logging_config import configure_logging, get_logger
from disclosure_drift.m3.evidence_paths import EvidenceRootError, require_external_evidence_root
from disclosure_drift.m3.receipt import (
    ExecutionReceipt,
    ReceiptValidationError,
    inspect_receipt,
    write_receipt,
)
from disclosure_drift.m3.recovery import inspect_recovery_state
from disclosure_drift.m3.rehearsal import SCENARIO_IDS, run_rehearsal
from disclosure_drift.m3.request_plan import (
    REQUEST_PLAN_SCHEMA_VERSION,
    build_m3_2a_request_plan,
    canonical_plan_bytes,
)
from disclosure_drift.paths import PathPolicyError
from disclosure_drift.reasons import REASON_CODES, release_blocking_codes
from disclosure_drift.sec.index_plan import (
    INDEX_PLAN_POLICY_VERSION,
    CoverageWindow,
    plan_index_instances,
)
from disclosure_drift.sec.source_registry import M22_SOURCE_REGISTRY_VERSION
from disclosure_drift.storage.catalog import CatalogWriter, read_only_connection

__all__ = ["build_parser", "main", "run"]

PROGRAM: Final = "python -m disclosure_drift"
EXIT_OK: Final = 0
EXIT_CONFIG_ERROR: Final = 1
EXIT_USAGE: Final = 2
EXIT_STAGE_NOT_ENABLED: Final = 3
EXIT_GATE_FAILURE: Final = 4

_STAGE_M2_2: Final = "Stage M2.2 (SEC client and metadata census)"
_STAGE_M2_3: Final = "Stage M2.3 (deterministic pilot selection)"
_STAGE_M2_5: Final = "Stage M2.5 (bounded pilot ingestion)"
_STAGE_M2_6: Final = "Stage M2.6 (inventory validation)"
_STAGE_M2_7: Final = "Stage M2.7 (forecast, backup, and release)"

#: Emitted only by a complete, passing A1-A12 rehearsal (master plan §20). The name is fixed by
#: the master plan; it is a phase completion marker, not a credential.
M3_1A_COMPLETION_TOKEN: Final = "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED"  # noqa: S105


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=(
            "Disclosure Drift research foundation. Offline commands only: no SEC "
            "downloads, no data processing, no network access."
        ),
    )
    parser.add_argument("--version", action="version", version=f"disclosure-drift {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    validate = subparsers.add_parser(
        "validate-config",
        help="Validate configs/project.yaml against the frozen research definitions.",
    )
    _add_config_argument(validate)

    cohorts = subparsers.add_parser(
        "show-cohorts",
        help="Print the frozen temporal cohorts, maturity gates, and bootstrap seed.",
    )
    _add_config_argument(cohorts)

    sec_config = subparsers.add_parser(
        "validate-sec-config",
        help="Validate SEC access policy and contact identity without making a request.",
    )
    _add_config_argument(sec_config)

    sec = subparsers.add_parser(
        "sec",
        help="SEC universe, inventory, and ingestion commands (Milestone 2).",
        description=(
            "Milestone 2 commands. Network commands fail before request construction "
            "when the SEC contact identity is missing or invalid, and are disabled "
            "entirely until their stage is enabled."
        ),
    )
    sec_subparsers = sec.add_subparsers(dest="sec_command", metavar="command")
    for name, help_text in (
        ("census", "Retrieve approved metadata census sources only (Stage M2.2)."),
        ("select-pilot", "Deterministically select the frozen pilot manifest (Stage M2.3)."),
        ("show-pilot", "Display the approved frozen pilot manifest."),
        ("ingest-pilot", "Retrieve approved pilot accessions only (Stage M2.5)."),
        ("validate-inventory", "Run inventory, cohort, and raw-object QA gates (Stage M2.6)."),
        ("forecast-storage", "Produce base, high-storage, and high-failure forecasts."),
        ("build-release", "Export a deterministic Parquet release (Stage M2.7)."),
        ("verify-release", "Rebuild and compare normalized release hashes (Stage M2.7)."),
        ("backup", "Create a consistent backup of raw objects and the catalog."),
        ("restore-test", "Perform an offline restore and verify recovery."),
    ):
        child = sec_subparsers.add_parser(name, help=help_text)
        _add_config_argument(child)
        if name == "census":
            child.add_argument(
                "--dry-run",
                action="store_true",
                help="Validate and print the approved retrieval plan; make no requests.",
            )
            child.add_argument(
                "--calendar-year",
                type=int,
                default=None,
                metavar="YEAR",
                help=(
                    "Year the annual EDGAR calendar instance must cover. Required for a "
                    "complete census: the year is never inferred from today's date."
                ),
            )
            child.add_argument(
                "--coverage-start",
                type=_iso_date,
                default=None,
                metavar="YYYY-MM-DD",
                help="First date of the requested coverage window (for example 2009-01-01).",
            )
            child.add_argument(
                "--coverage-end",
                type=_iso_date,
                default=None,
                metavar="YYYY-MM-DD",
                help="Last date of the requested coverage window.",
            )
            child.add_argument(
                "--as-of",
                type=_iso_date,
                default=None,
                metavar="YYYY-MM-DD",
                help=(
                    "Date the plan is evaluated against. Decides which quarters are "
                    "closed and required. Never defaults to today: a plan must be "
                    "reproducible on any later day."
                ),
            )
            child.add_argument(
                "--include-open-quarter",
                action="store_true",
                help=(
                    "Also retrieve the provisional open quarter containing the as-of "
                    "date. It is still reported as provisional, never finalized."
                ),
            )

    _add_m3_group(subparsers)
    return parser


def _add_m3_group(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the Milestone 3.1 command group.

    Every command that reads or writes evidence requires an absolute ``--evidence-root`` outside the
    repository checkout, and every artifact argument is a path *relative* to that root. The resolved
    root is never printed or serialized, so an evidence packet can be shared without disclosing
    where it lives.
    """
    m3 = subparsers.add_parser(
        "m3",
        help="Milestone 3.1 rehearsal, planning, and inspection commands.",
        description=(
            "Milestone 3.1 commands. Every one of them is offline: M3.1A places no request "
            "at all and M3.1B makes zero live requests. Artifact paths are relative to a "
            "required absolute --evidence-root outside the repository checkout."
        ),
    )
    m3_subparsers = m3.add_subparsers(dest="m3_command", metavar="command")

    rehearse = m3_subparsers.add_parser(
        "rehearse", help="Run offline acquisition rehearsal scenarios A1-A12 (Stage M3.1A)."
    )
    _add_config_argument(rehearse)
    _add_evidence_root_argument(rehearse)
    rehearse.add_argument(
        "--scenarios",
        default="all",
        metavar="{all,<id>[,<id>...]}",
        help="Scenarios to run. The phase token requires 'all'; a subset is for diagnosis.",
    )
    rehearse.add_argument(
        "--evidence-out",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="Where to write the rehearsal evidence report, relative to --evidence-root.",
    )
    rehearse.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="Where to write this command's receipt, relative to --evidence-root.",
    )

    rehearse_report = m3_subparsers.add_parser(
        "rehearse-report", help="Print a stored rehearsal evidence report. Read-only."
    )
    _add_evidence_root_argument(rehearse_report)
    rehearse_report.add_argument(
        "--evidence",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The rehearsal evidence report to read, relative to --evidence-root.",
    )

    plan_requests = m3_subparsers.add_parser(
        "plan-requests",
        help="Derive the zero-request M3.2A request plan and budget (Stage M3.1B).",
    )
    _add_config_argument(plan_requests)
    _add_evidence_root_argument(plan_requests)
    for name, help_text in (
        ("--coverage-start", "First date of the requested coverage window."),
        ("--coverage-end", "Last date of the requested coverage window."),
        ("--as-of", "Date the plan is evaluated against. Never defaults to today."),
    ):
        plan_requests.add_argument(
            name, type=_iso_date, required=True, metavar="YYYY-MM-DD", help=help_text
        )
    plan_requests.add_argument(
        "--calendar-year",
        type=int,
        required=True,
        metavar="YEAR",
        help="Year the annual EDGAR calendar instance must cover. Never inferred.",
    )
    plan_requests.add_argument(
        "--calendar-evidence-manifest",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help=(
            "The approved calendar-evidence manifest, relative to --evidence-root. Its entry "
            "count sets U(sec_edgar_calendar_announcement); an empty manifest lawfully plans zero."
        ),
    )
    plan_requests.add_argument(
        "--catalog",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help=(
            "The operational catalog, read only, to exclude already-satisfied index instances "
            "before planning. Relative to --evidence-root, like every other artifact argument."
        ),
    )
    plan_requests.add_argument(
        "--include-open-quarter",
        action="store_true",
        help="Also plan the provisional open quarter containing the as-of date.",
    )
    plan_requests.add_argument(
        "--plan-out",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="Where to write the request plan, relative to --evidence-root.",
    )
    plan_requests.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="Where to write this command's receipt, relative to --evidence-root.",
    )

    show_budget = m3_subparsers.add_parser(
        "show-budget",
        help="Render a request plan's budget quantities. Read-only; approves nothing.",
    )
    _add_evidence_root_argument(show_budget)
    show_budget.add_argument(
        "--plan",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The request plan to render, relative to --evidence-root.",
    )

    show_receipt = m3_subparsers.add_parser(
        "show-receipt", help="Validate and display an execution receipt. Read-only."
    )
    _add_evidence_root_argument(show_receipt)
    show_receipt.add_argument(
        "--receipt",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The receipt to validate, relative to --evidence-root.",
    )

    recovery_state = m3_subparsers.add_parser(
        "recovery-state",
        help=(
            "Report the safe-resume determination for an interrupted run. Read-only; never repairs."
        ),
    )
    _add_evidence_root_argument(recovery_state)
    for name, help_text in (
        ("--plan", "The request plan the interrupted run was executing."),
        ("--receipt-chain-head", "The most recent receipt of the interrupted run."),
    ):
        recovery_state.add_argument(
            name, type=Path, required=True, metavar="RELATIVE_PATH", help=help_text
        )
    recovery_state.add_argument(
        "--catalog",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The operational catalog to inspect, relative to --data-root.",
    )
    recovery_state.add_argument(
        "--data-root",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The data root whose raw store is inspected, relative to --evidence-root.",
    )


def _add_evidence_root_argument(parser: argparse.ArgumentParser) -> None:
    """Require an absolute evidence root outside the repository checkout."""
    parser.add_argument(
        "--evidence-root",
        type=Path,
        required=True,
        metavar="ABSOLUTE_EXTERNAL_PATH",
        help=(
            "Owner-controlled private evidence root. Must be an absolute path outside the "
            "repository checkout; its resolved value is never printed."
        ),
    )


def _iso_date(text: str) -> date:
    """Parse an explicit ISO date, refusing anything ambiguous.

    Coverage and as-of dates are always supplied. Nothing here reads the clock.
    """
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        message = f"expected an ISO date such as 2009-01-01, received {text!r}"
        raise argparse.ArgumentTypeError(message) from exc


def _coverage_from_args(args: argparse.Namespace) -> CoverageWindow | None:
    """Build the coverage window once, at the command boundary.

    All three of coverage start, coverage end, and as-of date must be supplied together.
    A partial window is refused rather than completed from today's date, and the three
    values are narrowed to concrete :class:`~datetime.date` objects before the window is
    constructed, so nothing downstream has to re-derive or re-validate them.

    Returns:
        The validated window, or ``None`` when no coverage argument was supplied at all.

    Raises:
        argparse.ArgumentTypeError: only some of the three dates were supplied.
    """
    start = getattr(args, "coverage_start", None)
    end = getattr(args, "coverage_end", None)
    as_of = getattr(args, "as_of", None)
    if start is None and end is None and as_of is None:
        return None
    if start is None or end is None or as_of is None:
        message = (
            "--coverage-start, --coverage-end, and --as-of must be supplied together; "
            "a missing value is never filled in from today's date"
        )
        raise argparse.ArgumentTypeError(message)
    # Narrowed above: each value is a concrete date parsed by _iso_date.
    coverage_start: date = start
    coverage_end: date = end
    as_of_date: date = as_of
    return CoverageWindow(
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        as_of_date=as_of_date,
        include_open_quarter=bool(getattr(args, "include_open_quarter", False)),
    )


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help="Configuration file to use (default: nearest configs/project.yaml).",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    if args.command == "sec" and getattr(args, "sec_command", None) is None:
        parser.parse_args(["sec", "--help"])
        return EXIT_USAGE  # pragma: no cover - argparse exits first
    if args.command == "m3" and getattr(args, "m3_command", None) is None:
        parser.parse_args(["m3", "--help"])
        return EXIT_USAGE  # pragma: no cover - argparse exits first

    # The read-only M3 inspection commands take no --config, because they read explicit artifacts
    # rather than project configuration. Their namespace therefore has no `config` attribute, and
    # the default resolution below finds the nearest configs/project.yaml exactly as before.
    try:
        config = load_config(getattr(args, "config", None))
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    configure_logging(config)
    logger = get_logger("cli")

    if args.command == "validate-config":
        return _validate_config_command(config, logger)
    if args.command == "show-cohorts":
        return _show_cohorts_command(config, logger)
    if args.command == "validate-sec-config":
        return _validate_sec_config_command(config, logger)
    if args.command == "sec":
        try:
            coverage = _coverage_from_args(args)
        except (argparse.ArgumentTypeError, ValueError) as exc:
            print(f"invalid coverage plan: {exc}", file=sys.stderr)
            return EXIT_USAGE
        return _sec_command(
            str(args.sec_command),
            config,
            logger,
            dry_run=bool(getattr(args, "dry_run", False)),
            calendar_year=getattr(args, "calendar_year", None),
            coverage=coverage,
        )
    if args.command == "m3":
        return _m3_command(str(args.m3_command), args, config, logger)

    parser.print_help(sys.stderr)  # pragma: no cover - argparse rejects earlier
    return EXIT_USAGE


# --------------------------------------------------------------------------- #
# Milestone 1 commands
# --------------------------------------------------------------------------- #
def _validate_config_command(config: ProjectConfig, logger: Logger) -> int:
    log_file = config.log_file_path()
    user_agent_set = config.sec_user_agent_is_set()
    rows = (
        ("config file", str(config.config_path)),
        ("project", f"{config.project.name} {config.project.version}"),
        ("data root", str(config.paths.data_root)),
        ("log level", config.logging.level),
        ("log file", str(log_file) if log_file else "disabled"),
        ("cohorts validated", f"{len(config.cohorts)} (frozen definitions match)"),
        ("bootstrap seed", str(config.seeds.bootstrap)),
        (
            "SEC user-agent var",
            f"{config.sec.user_agent_env} "
            f"({'set; value not displayed' if user_agent_set else 'not set'})",
        ),
        ("SEC request rate", f"{config.sec.requests_per_second} requests/second (placeholder)"),
    )
    print("Configuration valid.")
    for label, value in rows:
        print(f"  {label:<19}: {value}")

    if not user_agent_set:
        logger.warning(
            "%s is not set. Milestone 1 commands do not need it, but a real contact "
            "address becomes mandatory before Milestone 2 SEC ingestion. Copy "
            ".env.example to .env and set the variable when you reach that milestone.",
            config.sec.user_agent_env,
        )
    logger.info("Configuration validated from %s", config.config_path)
    return EXIT_OK


def _show_cohorts_command(config: ProjectConfig, logger: Logger) -> int:
    print("Frozen temporal cohorts (assigned by official SEC filing date; Decision 010)")
    print(f"  {'cohort':<13} {'window':<28} role")
    for name in COHORT_ORDER:
        window = FROZEN_COHORTS[name]
        print(f"  {name:<13} {window.label:<28} {window.role}")

    print("\nProspective maturity gates (earliest permitted outcome cutoffs)")
    for gate, gate_date in FROZEN_MATURITY_GATES.items():
        print(f"  {gate:<32} {gate_date.isoformat()}")

    print(f"\nBootstrap seed: {FROZEN_BOOTSTRAP_SEED}")
    print("\nThe acceptance date produces a separate audit-only cohort and never")
    print("determines analysis membership. These are frozen research definitions;")
    print("changing one requires an approved decision record and a reviewed code")
    print("change. Governing records:")
    for record in FROZEN_SOURCE_RECORDS:
        print(f"  {record}")

    logger.info("Displayed %d frozen cohorts", len(COHORT_ORDER))
    return EXIT_OK


# --------------------------------------------------------------------------- #
# Milestone 2 commands
# --------------------------------------------------------------------------- #
def _validate_sec_config_command(config: ProjectConfig, logger: Logger) -> int:
    tree = config.data_tree()
    backup = config.backup_root()
    rows = [
        ("config file", str(config.config_path)),
        ("data root", str(tree.data_root)),
        ("catalog path", tree.relative(tree.catalog_database)),
        ("audit directory", tree.relative(tree.audit)),
        ("backup root", backup.detail),
        ("network", "enabled" if config.network.enabled else "disabled (safe default)"),
        (
            "companyfacts",
            "enabled" if config.companyfacts.enabled else "disabled (reconciliation only)",
        ),
        (
            "aggregate rate",
            f"{config.sec.requests_per_second} requests/second, burst {config.sec.burst}",
        ),
        (
            "timeouts",
            f"connect {config.sec.connect_timeout_seconds}s, read "
            f"{config.sec.read_timeout_seconds}s, bulk {config.sec.bulk_read_timeout_seconds}s",
        ),
        (
            "retry policy",
            f"{config.sec.max_retries} transient retries, ceiling "
            f"{config.sec.backoff_ceiling_seconds}s, cooldown {config.sec.cooldown_seconds}s",
        ),
        (
            "reason codes",
            f"{len(REASON_CODES)} registered, {len(release_blocking_codes())} release-blocking",
        ),
        ("SEC user-agent var", config.sec.user_agent_env),
    ]

    try:
        config.require_sec_user_agent()
    except SecUserAgentError as exc:
        for label, value in rows:
            print(f"  {label:<19}: {value}")
        print(f"SEC contact identity invalid: {exc}", file=sys.stderr)
        logger.error("SEC contact identity is invalid; no network command may run")
        return EXIT_CONFIG_ERROR

    rows.append(("SEC contact identity", "valid; value not displayed"))
    print("SEC configuration valid.")
    for label, value in rows:
        print(f"  {label:<19}: {value}")
    logger.info("SEC configuration validated from %s", config.config_path)
    return EXIT_OK


def _validate_inventory_command(config: ProjectConfig, logger: Logger) -> int:
    """Create or migrate the catalog offline, seed reference data, and run the gates."""
    tree = config.data_tree()
    tree.ensure_tree()
    try:
        with CatalogWriter(tree.catalog_database, tree.locks) as writer:
            applied = writer.migrate()
            seeded = writer.seed_reference_data()
            report = writer.integrity()
            sic_row = writer.connection.execute(
                "SELECT COUNT(*) AS rows FROM reference_sic_codes"
            ).fetchone()
            sic_rows: int = int(sic_row["rows"]) if sic_row is not None else 0
            lease_id = writer.lease.lease_id
    except (DisclosureDriftError, sqlite3.Error) as exc:
        print(f"inventory validation error: {exc}", file=sys.stderr)
        logger.error("sec validate-inventory failed")
        return EXIT_GATE_FAILURE

    rows = (
        ("catalog", tree.relative(tree.catalog_database)),
        ("writer lease", f"{lease_id} (single logical writer)"),
        ("migrations applied", ", ".join(applied) if applied else "none pending"),
        ("reference form types", str(seeded["form_types"])),
        ("reference reason codes", str(seeded["reason_codes"])),
        ("reference cohorts", str(seeded["cohorts"])),
        ("reference policies", str(seeded["policies"])),
        ("reference SIC codes", f"{sic_rows} (loaded in Stage M2.2 from an SEC snapshot)"),
        ("quick_check", report.quick_check),
        ("integrity_check", report.integrity_check),
        ("foreign_key_check", f"{report.foreign_key_violations} violation(s)"),
    )
    print("Inventory catalog validated.")
    for label, value in rows:
        print(f"  {label:<22}: {value}")

    if not report.passed:
        print("integrity gate failed; release freezing is blocked", file=sys.stderr)
        return EXIT_GATE_FAILURE

    print("  accessions inventoried  : 0 (no ingestion has run; Stage M2.5 populates these)")
    logger.info("Catalog validated at %s", tree.relative(tree.catalog_database))
    return EXIT_OK


def _stage_refusal(command: str, stage: str, detail: str, logger: Logger) -> int:
    message = f"sec {command} requires {stage}: {detail}"
    print(message, file=sys.stderr)
    logger.warning("refused sec %s: %s not enabled", command, stage)
    return EXIT_STAGE_NOT_ENABLED


def _sec_command(
    command: str,
    config: ProjectConfig,
    logger: Logger,
    *,
    dry_run: bool = False,
    calendar_year: int | None = None,
    coverage: CoverageWindow | None = None,
) -> int:
    network_commands = {"census", "ingest-pilot"}
    if command in network_commands:
        try:
            config.require_sec_user_agent()
        except SecUserAgentError as exc:
            print(f"SEC contact identity invalid: {exc}", file=sys.stderr)
            logger.error("refused sec %s before request construction", command)
            return EXIT_CONFIG_ERROR
        if command == "census" and dry_run:
            return _census_dry_run(config, logger, calendar_year=calendar_year, coverage=coverage)
        if not config.network.enabled:
            return _stage_refusal(
                command,
                _STAGE_M2_2 if command == "census" else _STAGE_M2_5,
                "network access is disabled in configuration",
                logger,
            )

    if command == "validate-inventory":
        return _validate_inventory_command(config, logger)

    if command == "census":
        return _census_command(config, logger, calendar_year=calendar_year, coverage=coverage)

    refusals = {
        "select-pilot": (_STAGE_M2_3, "no metadata census exists yet"),
        "show-pilot": (_STAGE_M2_3, "no frozen pilot manifest exists yet"),
        "ingest-pilot": (_STAGE_M2_5, "no approved pilot manifest exists yet"),
        "forecast-storage": (_STAGE_M2_7, "no measured pilot ingestion exists yet"),
        "build-release": (_STAGE_M2_7, "the release extra and catalog are not available yet"),
        "verify-release": (_STAGE_M2_7, "no frozen release exists yet"),
        "restore-test": (_STAGE_M2_7, "no backup exists yet"),
    }

    if command == "backup":
        try:
            config.backup_root().require()
        except PathPolicyError as exc:
            print(f"backup configuration error: {exc}", file=sys.stderr)
            logger.error("refused sec backup: backup root unusable")
            return EXIT_CONFIG_ERROR
        return _stage_refusal(
            command, _STAGE_M2_7, "there is nothing to back up in Stage M2.1", logger
        )

    if command in refusals:
        stage, detail = refusals[command]
        return _stage_refusal(command, stage, detail, logger)

    print(f"unknown sec command: {command}", file=sys.stderr)  # pragma: no cover
    return EXIT_USAGE  # pragma: no cover


def _census_dry_run(
    config: ProjectConfig,
    logger: Logger,
    *,
    calendar_year: int | None = None,
    coverage: CoverageWindow | None = None,
) -> int:
    """Print the bounded M2.2 plan without constructing a transport.

    Args:
        config: Validated project configuration.
        logger: Command logger.
        calendar_year: Explicit annual-calendar year from the command boundary.
        coverage: The coverage window already parsed and validated at the command
            boundary. It is used as given: this helper never rebuilds it from argparse
            values and never substitutes today's date.
    """
    from disclosure_drift.sec.source_registry import SOURCES  # noqa: PLC0415

    tree = config.data_tree()
    print("SEC metadata census dry run valid.")
    print("  requests made          : 0")
    print("  census completed       : no (planning mode)")
    print(f"  data root              : {tree.data_root}")
    print("  approved initial sources:")
    for source_id in (
        "sec_bulk_submissions",
        "sec_company_tickers_exchange",
        "sec_company_tickers",
        "sec_sic_code_list",
        "sec_edgar_filing_calendar",
    ):
        source = SOURCES[source_id]
        print(f"    {source.source_id}: {source.expected_content}, {source.retrieval_method}")
    if calendar_year is None:
        print("  annual calendar year   : NOT SUPPLIED — the calendar source will be")
        print("                           blocked; pass --calendar-year YEAR. The year is")
        print("                           never inferred from today's date.")
    else:
        print(f"  annual calendar year   : {calendar_year} (explicit plan input)")
    _print_coverage_plan(coverage)
    print("  historical submissions : source-referenced metadata only")
    print("  prohibited             : filing bodies, primary documents, accession indexes,")
    print("                           complete submissions, and XBRL packages")
    logger.info("validated M2.2 census plan; no request was made")
    return EXIT_OK


def _print_coverage_plan(coverage: CoverageWindow | None) -> None:
    """Print the explicit coverage window and the exact quarterly instance plan."""
    if coverage is None:
        print("  coverage window        : NOT SUPPLIED — no quarterly index instance is")
        print("                           planned and no reconciliation coverage is")
        print("                           claimed. Pass --coverage-start, --coverage-end,")
        print("                           and --as-of together.")
        return
    plan = plan_index_instances(coverage)
    open_instance = plan.provisional_open
    print(
        f"  coverage window        : {coverage.coverage_start.isoformat()} to "
        f"{coverage.coverage_end.isoformat()}"
    )
    print(f"  as-of date             : {coverage.as_of_date.isoformat()} (explicit, never today)")
    print(f"  required closed quarters: {len(plan.required_closed)}")
    if open_instance is None:
        print("  provisional open quarter: none in the requested window")
    else:
        state = "included" if open_instance.required else "excluded by default"
        print(f"  provisional open quarter: {open_instance.instance_key} ({state}, provisional)")
    excluded = ", ".join(plan.excluded_future_quarters) or "none"
    print(f"  future quarters excluded: {excluded}")
    print("  satisfied required inst.: 0 (dry run inspects no catalog state)")
    print(f"  remaining required inst.: {len(plan.required_closed)}")
    print(f"  logical retrieval budget: {len(plan.required_keys)} (one per unsatisfied instance)")
    print("  logical retrievals      : 0 (dry run)")
    print("  actual HTTP attempts    : 0 (dry run)")
    print("  retries                 : 0 (dry run)")
    print("  finalized coverage      : none until required closed quarters are satisfied")
    print("  provisional coverage    : none in a dry run")
    print(f"  planned index instances : {len(plan.instances)}")
    for item in plan.instances:
        marker = "required" if item.required else "optional"
        print(f"    {item.instance_key}: {item.kind} ({marker})")
    print(f"  census plan hash       : {plan.plan_hash()}")


def _census_command(
    config: ProjectConfig,
    logger: Logger,
    *,
    calendar_year: int | None = None,
    coverage: CoverageWindow | None = None,
) -> int:
    """Execute the restartable Stage M2.2 census.

    Args:
        config: Validated project configuration.
        logger: Command logger.
        calendar_year: Explicit annual-calendar year from the command boundary.
        coverage: The coverage window already parsed and validated at the command
            boundary, passed straight to the orchestrator. Never reconstructed here, and
            never defaulted to today.
    """
    from disclosure_drift.sec.census_orchestrator import CensusOrchestrator  # noqa: PLC0415

    try:
        report = CensusOrchestrator(
            config,
            calendar_target_year=calendar_year,
            coverage=coverage,
        ).run()
    except (DisclosureDriftError, sqlite3.Error, OSError, ValueError) as exc:
        print(f"SEC census failed: {exc}", file=sys.stderr)
        logger.error("Stage M2.2 census failed: %s", type(exc).__name__)
        return EXIT_GATE_FAILURE
    print("SEC metadata census run finished.")
    print(f"  run id                         : {report.census_run_id}")
    print(f"  census completed               : {'yes' if report.completed else 'no'}")
    print(f"  source observations            : {report.source_observations}")
    print(f"  parsed source records          : {report.parsed_records}")
    print(f"  quarantined parsed records     : {report.quarantined_records}")
    print(f"  historical references retrieved: {report.historical_references_retrieved}")
    print(f"  QA summary                     : {config.data_tree().relative(report.audit_path)}")
    print(f"  accession resolutions          : {report.accession_resolutions}")
    if report.unresolved_accession_fields:
        print(f"  unresolved accession fields    : {len(report.unresolved_accession_fields)}")
        for item in report.unresolved_accession_fields[:5]:
            print(f"    {item}")
    coverage_report = report.index_coverage
    if coverage_report.get("index_planning") == "not_requested":
        print("  index reconciliation           : not requested (no coverage window)")
    else:
        print(
            "  required closed quarters       : "
            f"{coverage_report.get('required_closed_quarters_successful')} of "
            f"{coverage_report.get('required_closed_quarters_planned')} successful"
        )
        print(
            "  finalized coverage             : "
            f"{coverage_report.get('finalized_reconciliation_coverage')}"
        )
        print(
            "  provisional coverage           : "
            f"{coverage_report.get('provisional_reconciliation_coverage')} "
            "(never finalized)"
        )
        print(
            "  future quarters not planned    : "
            f"{coverage_report.get('future_quarters_not_planned')}"
        )
        accounting = report.index_accounting
        if accounting:
            print(f"  index instances planned        : {accounting.get('instances_planned')}")
            print(
                "  already satisfied (reused)     : "
                f"{accounting.get('instances_already_satisfied')}"
            )
            print(f"  logical retrieval budget       : {accounting.get('logical_budget')}")
            print(
                "  logical retrievals initiated   : "
                f"{accounting.get('logical_retrievals_initiated')}"
            )
            print(f"  actual HTTP attempts           : {accounting.get('http_attempts')}")
            print(f"  retries                        : {accounting.get('retries')}")
            print(f"  instances successful           : {accounting.get('instances_successful')}")
            print(f"  instances failed               : {accounting.get('instances_failed')}")
            print(f"  instances remaining            : {accounting.get('instances_remaining')}")
            if accounting.get("stopped_early"):
                print(f"  loop stopped early             : {accounting.get('stop_reason')}")
        print(f"  census plan hash               : {coverage_report.get('plan_sha256')}")
    print(f"  status                         : {report.detail}")
    if report.completion.incomplete_required_sources:
        print("  incomplete required sources:")
        for source in report.completion.incomplete_required_sources:
            reasons = ", ".join(source.unresolved_blocking_reasons) or "terminal state incomplete"
            print(
                f"    {source.source_id} [{source.instance_id}] "
                f"retrieval={source.retrieval_state} parser={source.parser_state} "
                f"catalog={source.catalog_state}: {reasons}"
            )
    return EXIT_OK if report.completed else EXIT_GATE_FAILURE


def run() -> None:
    """Console-script entry point."""
    try:
        raise SystemExit(main())
    except DisclosureDriftError as exc:  # pragma: no cover - defensive
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_GATE_FAILURE) from exc


# --------------------------------------------------------------------------- #
# Milestone 3.1 receipts
# --------------------------------------------------------------------------- #
#: The command version each M3.1 command declares, independent of the package version.
_M3_COMMAND_VERSIONS: Final[Mapping[str, str]] = {
    "m3 rehearse": "m3.1a/1.0",
    "m3 plan-requests": "m3.1b/1.0",
}


def _configuration_fingerprint(config: ProjectConfig) -> str:
    """A digest over effective NON-SECRET configuration.

    The SEC contact identity is never an input here — not even hashed. Receipt spec §5 is explicit
    that encoding does not launder a prohibited value, so the identity simply never reaches this
    function; only settings that are already safe to publish do.
    """
    payload = json.dumps(
        {
            "requests_per_second": config.sec.requests_per_second,
            "burst": config.sec.burst,
            "connect_timeout_seconds": config.sec.connect_timeout_seconds,
            "read_timeout_seconds": config.sec.read_timeout_seconds,
            "bulk_read_timeout_seconds": config.sec.bulk_read_timeout_seconds,
            "max_retries": config.sec.max_retries,
            "cooldown_seconds": config.sec.cooldown_seconds,
            "network_enabled": config.network.enabled,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _migration_chain_head(config: ProjectConfig) -> str:
    """The highest applied migration name, read without taking a writer lease."""
    database = config.data_tree().catalog_database
    if not database.is_file():
        return "none"
    try:
        with read_only_connection(database) as connection:
            row = connection.execute(
                "SELECT name FROM ops_schema_migrations ORDER BY name DESC LIMIT 1"
            ).fetchone()
    except (sqlite3.Error, DisclosureDriftError):
        return "none"
    return "none" if row is None else str(row[0])


def _utc_now() -> datetime:
    """The wall clock, used only for receipt timing fields.

    Timing is operational, never governed: receipt spec §4.3 states every timestamp here is
    excluded from every identity, which is why a real clock is safe to read at this one point.
    """
    return datetime.now(UTC)


def _rfc3339(moment: datetime) -> str:
    """RFC 3339 UTC with a `Z` suffix, as the receipt schema requires."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_m3_receipt(
    receipt: ExecutionReceipt,
    *,
    evidence_root: Path,
    relative: Path | None,
) -> Path:
    """Write a receipt beneath the evidence root, honouring an explicit relative name.

    A receipt is written for every invocation. `--receipt-out` chooses where; omitting it still
    produces one, under the content-derived name in the receipts directory, because "no receipt"
    is not an available outcome for a command that ran.
    """
    if relative is None:
        return write_receipt(
            receipt, evidence_root=evidence_root, repository_root=_repository_root()
        )
    destination = _m3_artifact_path(evidence_root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = receipt.canonical_bytes()
    if destination.exists() and destination.read_bytes() != payload:
        message = (
            f"a different receipt already exists at {relative}; a receipt is immutable and a "
            f"correction is a new receipt, never an edit"
        )
        raise GateFailureError(message)
    destination.write_bytes(payload)
    return destination


# --------------------------------------------------------------------------- #
# Milestone 3.1 commands
# --------------------------------------------------------------------------- #
def _m3_command(
    command: str,
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
) -> int:
    """Dispatch one Milestone 3.1 command.

    Every M3.1 command is offline. The evidence root is resolved and validated before any read or
    write, and a refusal is a configuration error rather than a gate failure: a root inside the
    checkout is a mistake in the invocation, not a finding about the run.
    """
    try:
        evidence_root = require_external_evidence_root(args.evidence_root, _repository_root())
    except EvidenceRootError as exc:
        print(f"evidence root refused: {exc}", file=sys.stderr)
        logger.error("refused m3 %s: the evidence root is not external", command)
        return EXIT_CONFIG_ERROR

    handlers = {
        "rehearse": _m3_rehearse_command,
        "rehearse-report": _m3_rehearse_report_command,
        "plan-requests": _m3_plan_requests_command,
        "show-budget": _m3_show_budget_command,
        "show-receipt": _m3_show_receipt_command,
        "recovery-state": _m3_recovery_state_command,
    }
    handler = handlers.get(command)
    if handler is None:  # pragma: no cover - argparse rejects earlier
        print(f"unknown m3 command {command!r}", file=sys.stderr)
        return EXIT_USAGE

    try:
        return handler(args, config, logger, evidence_root)
    except (DisclosureDriftError, sqlite3.Error) as exc:
        print(f"m3 {command} failed: {exc}", file=sys.stderr)
        logger.error("m3 %s failed", command)
        return EXIT_GATE_FAILURE
    except OSError as exc:
        # An OSError ordinarily carries the offending filename, which may be an absolute personal
        # path. Report the error class and the operator-supplied relative name only.
        print(
            f"m3 {command} failed: {type(exc).__name__} while reading or writing an artifact",
            file=sys.stderr,
        )
        logger.error("m3 %s failed on a filesystem error", command)
        return EXIT_GATE_FAILURE


def _repository_root() -> Path:
    """The repository checkout this package is installed from."""
    return Path(__file__).resolve().parents[2]


def _m3_rehearse_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Run scenarios A1-A12 against scripted transports. Places no request."""
    requested = (
        None
        if args.scenarios.strip() == "all"
        else [item.strip() for item in args.scenarios.split(",") if item.strip()]
    )
    started = _utc_now()
    report = run_rehearsal(requested)
    completed = _utc_now()

    for outcome in report.outcomes:
        status = "PASS" if outcome.passed else "FAIL"
        print(f"  {outcome.scenario_id:<4} {status}  {outcome.title}")
        if not outcome.passed:
            print(f"       {outcome.detail}")

    print("\nRehearsal summary.")
    for label, value in (
        ("scenarios run", str(len(report.outcomes))),
        ("all twelve run", "yes" if report.complete else "no"),
        ("every scenario passed", "yes" if report.passed else "no"),
        ("A_reachable agrees", "yes" if report.a_reachable_agrees else "no"),
        ("routes measured", str(len(report.tested_a_reachable))),
        ("routes unmeasurable", str(len(report.unmeasured_routes))),
        ("simulated logical requests", str(report.simulated_logical_requests)),
        ("simulated physical attempts", str(report.simulated_physical_attempts)),
        ("actual network requests", "0"),
        ("evidence reference", report.evidence_reference),
    ):
        print(f"  {label:<28}: {value}")
    for source_id, reason in sorted(report.unmeasured_routes.items()):
        print(f"  unmeasurable route          : {source_id} ({reason})")

    evidence_written = _m3_artifact_path(evidence_root, args.evidence_out)
    evidence_written.parent.mkdir(parents=True, exist_ok=True)
    evidence_written.write_bytes(report.canonical_bytes())
    print(f"  evidence written            : {args.evidence_out}")

    receipt = ExecutionReceipt(
        command_name="m3 rehearse",
        command_version=_M3_COMMAND_VERSIONS["m3 rehearse"],
        phase="M3.1A",
        invocation_mode="rehearsal",
        configuration_fingerprint=_configuration_fingerprint(config),
        migration_chain_head=_migration_chain_head(config),
        started_at_utc=_rfc3339(started),
        completed_at_utc=_rfc3339(completed),
        elapsed_seconds=round((completed - started).total_seconds(), 3),
        # A rehearsal places no request, so both network counts are zero. The simulated totals
        # live in the evidence report above and never in these fields.
        actual_logical_request_count=0,
        actual_physical_attempt_count=0,
        schema_drift_outcome="none",
        schema_drift_event_count=0,
        completion_status="complete" if report.passed else "failed",
        reason_code=None if report.passed else "SEC_ACQUISITION_INTERRUPTED",
        reason_detail=None if report.passed else "a rehearsal scenario did not pass.",
        rehearsal_evidence_reference=report.evidence_reference,
    )
    written = _write_m3_receipt(receipt, evidence_root=evidence_root, relative=args.receipt_out)
    print(f"  receipt written             : {args.receipt_out or written.name}")
    print(f"  receipt_id                  : {receipt.receipt_id}")

    if not report.passed:
        logger.error("m3 rehearse: a scenario failed; the phase does not pass")
        return EXIT_GATE_FAILURE
    if not report.complete:
        logger.warning("m3 rehearse: a subset ran, so no completion token is emitted")
        return EXIT_OK
    # The token is emitted only after the receipt exists on disk: the phase claims a rehearsal
    # passed, and a passing rehearsal that produced no evidence is an incomplete command.
    # The token is emitted only when BOTH artifacts exist. The receipt's
    # `rehearsal_evidence_reference` names the report, and the simulated totals live only there, so
    # a token backed by a receipt pointing at a missing report claims evidence that does not exist.
    for label, artifact in (("receipt", written), ("evidence report", evidence_written)):
        if not artifact.is_file():  # pragma: no cover - the writes above raise on failure
            message = (
                f"the rehearsal {label} was not written; the phase produces no completion token"
            )
            raise GateFailureError(message)
    print(f"\n{M3_1A_COMPLETION_TOKEN}")
    logger.info("m3 rehearse: all twelve scenarios passed")
    return EXIT_OK


def _m3_rehearse_report_command(
    args: argparse.Namespace,
    config: ProjectConfig,  # noqa: ARG001 - read-only inspection takes no configuration input
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Print a stored rehearsal evidence report. Read-only."""
    document = _read_json_artifact(evidence_root, args.evidence)
    scenarios = document.get("scenarios", [])
    for entry in scenarios if isinstance(scenarios, list) else []:
        if isinstance(entry, dict):
            status = "PASS" if entry.get("passed") else "FAIL"
            print(f"  {str(entry.get('scenario_id')):<4} {status}  {entry.get('title')}")

    # Derived from the scenario list, never from the stored booleans: a report claiming
    # `passed: true` while listing a failed scenario must not exit 0.
    recorded = [
        entry
        for entry in (scenarios if isinstance(scenarios, list) else [])
        if isinstance(entry, dict)
    ]
    recorded_ids = [str(entry.get("scenario_id")) for entry in recorded]
    complete = sorted(recorded_ids) == sorted(SCENARIO_IDS)
    passed = bool(recorded) and all(bool(entry.get("passed")) for entry in recorded)
    agrees = bool(document.get("a_reachable_agrees")) and _bounds_agree(document)

    claimed_complete = bool(document.get("complete"))
    claimed_passed = bool(document.get("passed"))
    if (claimed_complete, claimed_passed) != (complete, passed):
        print(
            "  record inconsistent: its summary disagrees with its own scenario list",
            file=sys.stderr,
        )

    # §9 requires the non-contamination result and the derived/tested route bounds, not just the
    # matrix: those two are what Gate F items 3.7 and 3.10 are read from.
    a12 = next(
        (
            entry
            for entry in (scenarios if isinstance(scenarios, list) else [])
            if isinstance(entry, dict) and entry.get("scenario_id") == "A12"
        ),
        None,
    )
    non_contamination = (
        "not recorded" if a12 is None else ("passed" if a12.get("passed") else "FAILED")
    )

    derived = document.get("derived_a_reachable", {})
    tested = document.get("tested_a_reachable", {})
    unmeasured = document.get("unmeasured_routes", {})
    if isinstance(derived, dict) and isinstance(tested, dict):
        print("\n  route bounds (derived vs independently tested)")
        for source_id in sorted(derived):
            measured = tested.get(source_id, "not measured")
            agreement = "agrees" if tested.get(source_id) == derived[source_id] else "-"
            print(
                f"    {source_id:<34} derived {derived[source_id]!s:>3}  "
                f"tested {measured!s:>12}  {agreement}"
            )
    if isinstance(unmeasured, dict):
        for source_id, reason in sorted(unmeasured.items()):
            print(f"    unmeasurable: {source_id} ({reason})")

    for label, value in (
        ("all twelve recorded", "yes" if complete else "no"),
        ("every scenario passed", "yes" if passed else "no"),
        ("identity non-contamination", non_contamination),
        ("A_reachable agrees", "yes" if agrees else "no"),
    ):
        print(f"  {label:<28}: {value}")

    if not (complete and passed and agrees):
        logger.error("m3 rehearse-report: the record is not a complete passing A1-A12 record")
        return EXIT_GATE_FAILURE
    logger.info("m3 rehearse-report: complete passing record")
    return EXIT_OK


def _m3_plan_requests_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Derive the M3.2A request plan. Constructs no transport and makes zero requests."""
    entry_count = _calendar_manifest_entry_count(evidence_root, args.calendar_evidence_manifest)
    # §9: every artifact argument is a path below the resolved evidence root, so the catalog is
    # located there too rather than at an arbitrary absolute location outside the boundary.
    satisfied = _already_satisfied_index_keys(_m3_artifact_path(evidence_root, args.catalog))

    started = _utc_now()
    plan = build_m3_2a_request_plan(
        coverage_start=args.coverage_start,
        coverage_end=args.coverage_end,
        as_of_date=args.as_of,
        include_open_quarter=bool(args.include_open_quarter),
        calendar_year=int(args.calendar_year),
        calendar_evidence_entry_count=entry_count,
        already_satisfied_index_keys=satisfied,
        requests_per_second=float(config.sec.requests_per_second),
    )

    print("M3.2A request plan (zero requests placed).")
    print(f"  {'source_id':<34} {'planned':>8} {'A_reach':>8} {'max attempts':>13}")
    for route in plan.routes:
        print(
            f"  {route.source_id:<34} {route.planned_unique_logical_requests:>8} "
            f"{route.a_reachable:>8} {route.maximum_physical_attempts:>13}"
        )
    for label, value in (
        ("planned unique logical requests", str(plan.planned_unique_logical_requests)),
        ("maximum physical attempts", str(plan.maximum_physical_attempts)),
        ("maximum new raw objects", str(plan.maximum_new_raw_objects)),
        ("hard request ceiling", str(plan.hard_request_ceiling)),
        ("expected cache hits", str(plan.expected_cache_hits)),
        ("request plan sha256", plan.request_plan_sha256),
    ):
        print(f"  {label:<34}: {value}")

    if args.plan_out is not None:
        destination = _m3_artifact_path(evidence_root, args.plan_out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_plan_bytes(plan))
        print(f"  {'plan written':<34}: {args.plan_out}")

    completed = _utc_now()
    receipt = ExecutionReceipt(
        command_name="m3 plan-requests",
        command_version=_M3_COMMAND_VERSIONS["m3 plan-requests"],
        phase="M3.1B",
        invocation_mode="dry_run",
        configuration_fingerprint=_configuration_fingerprint(config),
        migration_chain_head=_migration_chain_head(config),
        started_at_utc=_rfc3339(started),
        completed_at_utc=_rfc3339(completed),
        elapsed_seconds=round((completed - started).total_seconds(), 3),
        source_registry_version=M22_SOURCE_REGISTRY_VERSION,
        index_plan_policy_version=INDEX_PLAN_POLICY_VERSION,
        request_plan_schema_version=REQUEST_PLAN_SCHEMA_VERSION,
        acquisition_window=plan.acquisition_window,
        request_plan_id=plan.request_plan_id,
        request_plan_sha256=plan.request_plan_sha256,
        # No approved ceiling: a dry run precedes owner approval, so the field is omitted.
        planned_logical_request_count=plan.planned_unique_logical_requests,
        maximum_physical_attempt_count=plan.maximum_physical_attempts,
        planned_per_route={
            route.source_id: route.planned_unique_logical_requests for route in plan.routes
        },
        actual_logical_request_count=0,
        actual_physical_attempt_count=0,
        completion_status="complete",
    )
    written = _write_m3_receipt(receipt, evidence_root=evidence_root, relative=args.receipt_out)
    print(f"  {'receipt written':<34}: {args.receipt_out or written.name}")
    print(f"  {'receipt_id':<34}: {receipt.receipt_id}")

    logger.info("m3 plan-requests: derived the M3.2A plan with zero requests")
    return EXIT_OK


def _m3_show_budget_command(
    args: argparse.Namespace,
    config: ProjectConfig,  # noqa: ARG001 - rendering a stored plan takes no configuration input
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Render a stored plan's budget quantities. Approves neither integer."""
    document = _read_json_artifact(evidence_root, args.plan)
    totals = document.get("totals", {})
    routes = document.get("routes", [])

    print("Request budget (derived; this command approves nothing).")
    for entry in routes if isinstance(routes, list) else []:
        if isinstance(entry, dict):
            print(
                f"  {str(entry.get('source_id')):<34} "
                f"{entry.get('planned_unique_logical_requests')!s:>8} "
                f"{entry.get('a_reachable')!s:>8} "
                f"{entry.get('maximum_physical_attempts')!s:>13}"
            )

    # All eight governed quantities from `request_budget.md` §4, in that order. Three are
    # expectations the plan does not derive; they are shown as unresolved rather than omitted or
    # invented, because a blank in the budget blocks approval and a guess would corrupt it.
    quantities = _eight_budget_quantities(totals if isinstance(totals, dict) else {}, document)
    for label, value in quantities:
        print(f"  {label:<38}: {value}")
    print(
        f"  {'hard request ceiling (derived)':<38}: {_budget_value(totals, 'hard_request_ceiling')}"
    )
    print(f"  {'approval status':<38}: not approved by this command")
    logger.info("m3 show-budget: rendered a stored plan")
    return EXIT_OK


def _m3_show_receipt_command(
    args: argparse.Namespace,
    config: ProjectConfig,  # noqa: ARG001 - receipt validation takes no configuration input
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Validate and display a receipt, including its recovery chain. Exits 4 on any defect."""
    path = _m3_artifact_path(evidence_root, args.receipt)
    try:
        document = inspect_receipt(path)
        chain = _resolve_receipt_chain(path, document)
    except ReceiptValidationError as exc:
        print(f"receipt rejected: {exc}", file=sys.stderr)
        logger.error("m3 show-receipt: the receipt failed validation")
        return EXIT_GATE_FAILURE

    for field_name in sorted(document):
        value = document[field_name]
        if isinstance(value, (dict, list)):
            continue
        print(f"  {field_name:<42}: {value}")
    print(f"  {'recovery_chain_length':<42}: {len(chain)}")
    print(f"  {'validation':<42}: passed")
    logger.info("m3 show-receipt: the receipt validated")
    return EXIT_OK


def _m3_recovery_state_command(
    args: argparse.Namespace,
    config: ProjectConfig,  # noqa: ARG001 - inspection reads only the explicit inputs
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Report the safe-resume determination. Read-only; never repairs. Exit 0 only for SAFE."""
    plan_document = _read_json_artifact(evidence_root, args.plan)
    inputs = plan_document.get("inputs", {})
    if not isinstance(inputs, dict):  # pragma: no cover - a malformed plan fails earlier
        message = "the stored plan carries no inputs section"
        raise GateFailureError(message)

    plan = build_m3_2a_request_plan(
        coverage_start=date.fromisoformat(str(inputs["coverage_start"])),
        coverage_end=date.fromisoformat(str(inputs["coverage_end"])),
        as_of_date=date.fromisoformat(str(inputs["as_of_date"])),
        include_open_quarter=bool(inputs["include_open_quarter"]),
        calendar_year=int(inputs["calendar_year"]),
        calendar_evidence_entry_count=int(inputs["calendar_evidence_entry_count"]),
        already_satisfied_index_keys=frozenset(),
        requests_per_second=float(inputs["requests_per_second"]),
    )

    data_root = _m3_artifact_path(evidence_root, args.data_root)
    state = inspect_recovery_state(
        plan=plan,
        receipt_chain_head=_m3_artifact_path(evidence_root, args.receipt_chain_head),
        catalog_path=data_root / args.catalog,
        data_root=data_root,
    )

    print("Safe-resume determination (read-only; nothing was repaired).")
    for condition in state.conditions:
        print(f"  {condition.number:<5} {condition.status:<8} {condition.condition}")
    for label, value in (
        ("interruption state", str(state.interruption_state)),
        ("receipt chain length", str(len(state.receipt_chain))),
        ("consumed physical attempts", str(state.consumed_physical_attempts)),
        ("committed observations", str(state.committed_observation_count)),
        ("orphan objects", str(state.orphan_object_count)),
        ("rows without object", str(state.rows_without_object_count)),
        ("partial files", str(state.partial_file_count)),
        ("determination", state.determination),
        ("basis", state.basis),
        ("required action", state.required_action),
    ):
        print(f"  {label:<28}: {value}")

    if state.determination != "SAFE":
        logger.error("m3 recovery-state: determination %s", state.determination)
        return EXIT_GATE_FAILURE
    logger.info("m3 recovery-state: SAFE")
    return EXIT_OK


def _resolve_receipt_chain(head_path: Path, head: Mapping[str, object]) -> tuple[str, ...]:
    """Resolve `recovery_predecessor_receipt_id` back to the first attempt.

    Receipt spec §14 requires a present predecessor to resolve to a readable receipt, and §11.4
    makes a broken chain a stop condition. Validating the head alone would let a receipt naming a
    predecessor that was never written pass as intact, which is precisely the case the chain exists
    to detect.
    """
    receipts_dir = head_path.parent
    chain: list[str] = [str(head["receipt_id"])]
    visited = {str(head["receipt_id"])}
    document: Mapping[str, object] = head

    while True:
        predecessor = document.get("recovery_predecessor_receipt_id")
        if predecessor is None:
            return tuple(chain)
        identifier = str(predecessor)
        if identifier in visited:
            message = (
                f"the recovery chain loops back to {identifier[:12]}… and never reaches a first "
                f"attempt"
            )
            raise ReceiptValidationError(message)
        candidate = receipts_dir / f"receipt-{identifier}.json"
        try:
            document = inspect_receipt(candidate)
        except OSError as exc:
            # An OSError carries the absolute filename it failed on, which may never be printed.
            message = (
                f"recovery_predecessor_receipt_id {identifier[:12]}… does not resolve to a "
                f"readable receipt ({type(exc).__name__})"
            )
            raise ReceiptValidationError(message) from exc
        except ReceiptValidationError as exc:
            message = (
                f"recovery_predecessor_receipt_id {identifier[:12]}… resolves to a receipt that "
                f"fails validation: {exc}"
            )
            raise ReceiptValidationError(message) from exc
        visited.add(identifier)
        chain.append(identifier)


def _bounds_agree(document: Mapping[str, object]) -> bool:
    """Recompute derived-versus-tested agreement from the recorded bounds.

    The report carries an `a_reachable_agrees` boolean, but a gate that reads only that boolean
    would accept a record whose own numbers disagree. Master plan §17 item 9 makes a disagreement a
    stop condition, so the numbers are compared here as well.
    """
    derived = document.get("derived_a_reachable")
    tested = document.get("tested_a_reachable")
    if not isinstance(derived, Mapping) or not isinstance(tested, Mapping):
        return False
    return all(derived.get(source_id) == bound for source_id, bound in tested.items())


def _budget_value(totals: object, key: str) -> object:
    """One total from a stored plan, or a marker when the plan does not carry it."""
    if isinstance(totals, Mapping):
        return totals.get(key, "MISSING")
    return "MISSING"


#: The three budget quantities that are operator expectations rather than derived counts. The
#: zero-request planner cannot know how many responses will classify `proceed`, so it must not
#: assert one; `request_budget.md` §4 has the operator supply them before approval.
_UNRESOLVED = "EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN"


def _eight_budget_quantities(
    totals: Mapping[str, object],
    document: Mapping[str, object],
) -> tuple[tuple[str, object], ...]:
    """The eight governed budget quantities, in `request_budget.md` §4 order.

    Every one is shown. Three are expectations the deterministic planner does not derive, and they
    render as unresolved rather than as `0`: a zero would read as an approved expectation of no
    successful responses, which is a different and false claim.
    """
    return (
        (
            "planned unique logical requests",
            totals.get("planned_unique_logical_requests", "MISSING"),
        ),
        ("maximum physical attempts", totals.get("maximum_physical_attempts", "MISSING")),
        ("expected successful responses", _UNRESOLVED),
        ("expected cache hits", document.get("expected_cache_hits", "MISSING")),
        ("expected not-modified responses", _UNRESOLVED),
        ("expected governed non-success responses", _UNRESOLVED),
        ("maximum new raw objects", totals.get("maximum_new_raw_objects", "MISSING")),
        (
            "rate-limiter spacing floor (seconds)",
            totals.get("rate_limiter_spacing_floor_seconds", "MISSING"),
        ),
    )


def _calendar_manifest_entry_count(evidence_root: Path, relative: Path) -> int:
    """Count approved entries in the operator-named calendar-evidence manifest.

    The manifest is named explicitly rather than read from the in-repository constant, so the count
    reflects the evidence the operator actually approved for this window.
    """
    document = _read_json_artifact(evidence_root, relative)
    entries = document.get("entries")
    if not isinstance(entries, list):
        message = (
            f"calendar-evidence manifest {relative} carries no 'entries' list; an empty manifest "
            f"is written as an empty list, never omitted"
        )
        raise GateFailureError(message)
    approved = [
        entry
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("review_status") == "approved"
    ]
    return len(approved)


def _already_satisfied_index_keys(catalog_path: Path) -> frozenset[str]:
    """Index instances already satisfied in the catalog, read without a writer lease.

    These are excluded before the plan is formed and reported as cache hits; Decision 028 §10 is
    explicit that they are never subtracted a second time. A catalog that does not exist yet
    satisfies nothing, which is the ordinary state before the first acquisition.
    """
    if not catalog_path.is_file():
        return frozenset()
    try:
        with read_only_connection(catalog_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT instance_key FROM census_index_instances "
                "WHERE retrieved = 1 AND parse_usable = 1"
            ).fetchall()
    except sqlite3.Error as exc:
        message = f"the catalog could not be read to exclude already-satisfied instances: {exc}"
        raise GateFailureError(message) from exc
    return frozenset(str(row[0]) for row in rows)


def _m3_artifact_path(evidence_root: Path, relative: Path) -> Path:
    """Resolve an artifact path below the evidence root, refusing escape.

    A relative path that climbs out of the root would write evidence somewhere the operator did not
    name, so it is refused rather than normalized away.
    """
    candidate = Path(relative)
    if candidate.is_absolute():
        message = (
            f"artifact path {candidate.name!r} must be relative to --evidence-root, not absolute"
        )
        raise GateFailureError(message)
    resolved = (evidence_root / candidate).resolve()
    if evidence_root not in resolved.parents and resolved != evidence_root:
        message = f"artifact path {candidate.name!r} resolves outside the evidence root"
        raise GateFailureError(message)
    return resolved


def _read_json_artifact(evidence_root: Path, relative: Path) -> dict[str, object]:
    """Read one JSON artifact from below the evidence root."""
    path = _m3_artifact_path(evidence_root, relative)
    try:
        document = json.loads(path.read_bytes().decode("utf-8"))
    except OSError as exc:
        # `str(OSError)` embeds the absolute filename. Master plan §17 stop condition 12 and
        # contract §9 both forbid printing one, and this helper feeds four commands' error paths,
        # so the class of leak is closed here rather than at each call site.
        message = f"artifact {Path(relative).name!r} could not be read ({type(exc).__name__})"
        raise GateFailureError(message) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = f"artifact {Path(relative).name!r} is not readable UTF-8 JSON: {exc}"
        raise GateFailureError(message) from exc
    if not isinstance(document, dict):
        message = f"artifact {path.name!r} is not a JSON object"
        raise GateFailureError(message)
    return document
