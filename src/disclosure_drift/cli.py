"""Command-line interface for Disclosure Drift.

Milestone 1 commands (``validate-config``, ``show-cohorts``) are offline and
read-only. Stage M2.2 enables the bounded ``sec census`` workflow only when the
configuration explicitly enables network access and the SEC contact identity is
valid. The census retrieves approved metadata sources; filing bodies and packages
remain prohibited.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from datetime import date
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
from disclosure_drift.errors import DisclosureDriftError, SecUserAgentError
from disclosure_drift.logging_config import configure_logging, get_logger
from disclosure_drift.paths import PathPolicyError
from disclosure_drift.reasons import REASON_CODES, release_blocking_codes
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances
from disclosure_drift.storage.catalog import CatalogWriter

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

    return parser


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

    try:
        config = load_config(args.config)
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
