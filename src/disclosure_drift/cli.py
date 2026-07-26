"""Command-line interface for Disclosure Drift.

Milestone 1 commands (``validate-config``, ``show-cohorts``) are offline and
read-only. The Milestone 2 ``sec`` group is registered here; during Stage M2.1
every command that would need the network or the operational catalog refuses with
a stage exit code instead of acting. Nothing in this module downloads filings,
processes data, or opens a network connection.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
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

    return parser


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
        return _sec_command(str(args.sec_command), config, logger)

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
        ("network", "enabled" if config.network.enabled else "disabled (Stage M2.1)"),
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


def _sec_command(command: str, config: ProjectConfig, logger: Logger) -> int:
    network_commands = {"census", "ingest-pilot"}
    if command in network_commands:
        try:
            config.require_sec_user_agent()
        except SecUserAgentError as exc:
            print(f"SEC contact identity invalid: {exc}", file=sys.stderr)
            logger.error("refused sec %s before request construction", command)
            return EXIT_CONFIG_ERROR
        if not config.network.enabled:
            return _stage_refusal(
                command,
                _STAGE_M2_2 if command == "census" else _STAGE_M2_5,
                "network access is disabled in configuration",
                logger,
            )

    if command == "validate-inventory":
        return _validate_inventory_command(config, logger)

    refusals = {
        "census": (_STAGE_M2_2, "the SEC client is not implemented in Stage M2.1"),
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


def run() -> None:
    """Console-script entry point."""
    try:
        raise SystemExit(main())
    except DisclosureDriftError as exc:  # pragma: no cover - defensive
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_GATE_FAILURE) from exc
