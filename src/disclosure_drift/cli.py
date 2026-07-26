"""Command-line interface for the Disclosure Drift foundation.

Every command is read-only and offline. Nothing here downloads filings,
processes data, or opens a network connection.
"""

from __future__ import annotations

import argparse
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
from disclosure_drift.logging_config import configure_logging, get_logger

__all__ = ["build_parser", "main", "run"]

PROGRAM: Final = "python -m disclosure_drift"
EXIT_OK: Final = 0
EXIT_CONFIG_ERROR: Final = 1
EXIT_USAGE: Final = 2


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the foundation CLI."""
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

    parser.print_help(sys.stderr)  # pragma: no cover - argparse rejects earlier
    return EXIT_USAGE


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
    print("Frozen temporal cohorts (SEC acceptance dates)")
    print(f"  {'cohort':<13} {'window':<28} role")
    for name in COHORT_ORDER:
        window = FROZEN_COHORTS[name]
        print(f"  {name:<13} {window.label:<28} {window.role}")

    print("\nProspective maturity gates (earliest permitted outcome cutoffs)")
    for gate, gate_date in FROZEN_MATURITY_GATES.items():
        print(f"  {gate:<32} {gate_date.isoformat()}")

    print(f"\nBootstrap seed: {FROZEN_BOOTSTRAP_SEED}")
    print("\nThese are frozen research definitions. Changing one requires an approved")
    print("decision record and a reviewed code change. Governing records:")
    for record in FROZEN_SOURCE_RECORDS:
        print(f"  {record}")

    logger.info("Displayed %d frozen cohorts", len(COHORT_ORDER))
    return EXIT_OK


def run() -> None:
    """Console-script entry point."""
    raise SystemExit(main())
