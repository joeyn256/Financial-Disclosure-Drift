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
import signal
import sqlite3
import sys
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, date, datetime
from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING, Final

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
from disclosure_drift.m3.acquisition import (
    ACQUISITION_WINDOWS,
    RECOVERY_ACTIONS,
    ContinuationProposal,
    LiveAcquisitionResult,
    LiveOperationAuthorization,
    LiveOperatorGate,
    RequestReconciliation,
    StorageBinding,
    WindowOutcome,
    apply_recovery_action,
    derive_dependent_plan,
    drift_for_run,
    execute_live_acquisition,
    load_carry_in_authority,
    prepare_operational_catalog,
    prepare_storage,
    propose_continuation,
    rebuild_projection_eligibility,
    reconcile_requests,
    reconstruct_catalog_state,
    require_m3_2a_consumed_baseline,
    validate_acquisition_run,
    verify_carry_in_authority,
    verify_plan_transition,
    verify_window_bindings,
)
from disclosure_drift.m3.evidence_paths import EvidenceRootError, require_external_evidence_root
from disclosure_drift.m3.execution_rehearsal import run_execution_rehearsal
from disclosure_drift.m3.offline_execution import (
    OFFLINE_EXECUTION_MODE,
    cohort_definition_digest,
    offline_execution_policy_versions,
)
from disclosure_drift.m3.receipt import (
    ExecutionReceipt,
    ReceiptChainResolutionError,
    ReceiptValidationError,
    inspect_receipt,
    resolve_predecessor_receipt,
    write_receipt,
)
from disclosure_drift.m3.recovery import (
    PlanTransitionAuthority,
    inspect_receiptless_first_invocation,
    inspect_recovery_state,
    walk_receipt_chain,
)
from disclosure_drift.m3.rehearsal import SCENARIO_IDS, RehearsalReport, run_rehearsal
from disclosure_drift.m3.request_plan import (
    RequestPlan,
    build_m3_2a_request_plan,
    canonical_plan_bytes,
    derive_a_reachable,
    request_plan_from_document,
)
from disclosure_drift.paths import PathPolicyError
from disclosure_drift.reasons import REASON_CODES, release_blocking_codes
from disclosure_drift.sec.http_client import RetrievalPolicy
from disclosure_drift.sec.index_plan import (
    INDEX_PLAN_POLICY_VERSION,
    CoverageWindow,
    plan_index_instances,
)
from disclosure_drift.sec.source_registry import (
    M22_SOURCE_REGISTRY_VERSION,
    SOURCES,
    require_registered,
)
from disclosure_drift.storage.catalog import (
    CatalogWriter,
    read_only_connection,
    strictly_read_only_connection,
)

if TYPE_CHECKING:  # pragma: no cover - typing only; `m3/e0.py` stays a call-time import
    from disclosure_drift.m3.e0 import OperatorResult

__all__ = ["build_parser", "main", "run"]

PROGRAM: Final = "python -m disclosure_drift"
EXIT_OK: Final = 0
EXIT_CONFIG_ERROR: Final = 1
EXIT_USAGE: Final = 2
EXIT_STAGE_NOT_ENABLED: Final = 3
EXIT_GATE_FAILURE: Final = 4

#: The accepted contract and stage authority a live acquisition names when it asserts the operator
#: conjunction. It records *which* authority the invocation runs under; naming it is necessary and
#: never sufficient, and it grants nothing on its own (Decision 045 §6 item 7).
_M3_2_STAGE_AUTHORITY: Final = "Milestones/contracts/m3_2.md; Decision 045 T2.5-T2.6"

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
        help="Milestone 3 rehearsal, planning, inspection, and acquisition commands.",
        description=(
            "Milestone 3 commands. Every implemented one is offline: M3.1A places no request "
            "at all and M3.1B makes zero live requests. Artifact paths are relative to a "
            "required absolute --evidence-root outside the repository checkout. The Milestone "
            "3.2 acquisition surfaces are recognized but not implemented: at stage T2.1 each "
            "refuses, and none can construct a transport."
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

    rehearse_execution = m3_subparsers.add_parser(
        "rehearse-execution",
        help="Run the offline M3.3A execution rehearsal, scenarios E1-E8. Fixtures only.",
        description=(
            "Runs the M3.3A execution rehearsal against disposable synthetic catalogs the "
            "command creates under --evidence-root. It never reads the accepted real private "
            "catalog, constructs no transport, and places no request. A passing run is not an "
            "authorization for M3.3-E0, M3.3-E1, M3.3-E2, or M3.4."
        ),
    )
    _add_config_argument(rehearse_execution)
    _add_evidence_root_argument(rehearse_execution)
    rehearse_execution.add_argument(
        "--scenarios",
        default="all",
        metavar="{all,<id>[,<id>...]}",
        help="Scenarios to run. A complete report requires 'all'; a subset is for diagnosis.",
    )
    rehearse_execution.add_argument(
        "--evidence-out",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="Where to write the execution-rehearsal evidence report, relative to --evidence-root.",
    )
    rehearse_execution.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="Where to write this command's receipt, relative to --evidence-root.",
    )

    # Decision 094 §7.1. Both take exactly --config and --mode: there is no --evidence-root,
    # --catalog, --data-root, --run-namespace, migration list, force, resume, overwrite,
    # repair, network, or output option, because none of those is an operator choice. The
    # private root comes from the fixed unlogged environment variable and nowhere else.
    for name, summary, detail in _M3_3_PRE_E0_COMMANDS:
        pre_e0 = m3_subparsers.add_parser(name, help=summary, description=detail)
        _add_config_argument(pre_e0)
        pre_e0.add_argument(
            "--mode",
            required=True,
            choices=("preflight", "execute", "verify"),
            help=(
                "preflight validates every predicate and creates nothing; execute is the only "
                "write mode and is not enabled; verify validates a durable namespace read-only."
            ),
        )

    # Decision 103 R6. Same shape and the same absent options as the two surfaces above: no
    # --force, --pid, --lease-id, --host, --catalog, --lease-file, --evidence-root,
    # --ignore-lock, --skip-check, --run-namespace, or --network. Every eligibility predicate is
    # measured from the world, so there is nothing left for an operator to assert.
    recover_lease = m3_subparsers.add_parser(
        _M3_3_RECOVERY_COMMAND,
        help="Reconcile one stale catalog writer lease left by an interrupted run (D103 R3).",
        description=(
            "Reconciles a persisted writer lease that still records 'held' for a process that "
            "no longer exists. It is never automatic and never a step another command performs: "
            "the ordinary PRE-E0 surfaces continue to refuse a held lease. Eligibility is "
            "conjunctive and fail-closed — same host, dead writer, no other active writer, a "
            "free exclusive advisory lock, an expired lease, a clean catalog whose identity "
            "matches the accepted recovery baseline, network disabled, and no prior "
            "reconciliation. preflight is strictly read-only; execute reconciles exactly once "
            "and writes a durable recovery record. No catalog page, WAL frame, migration, "
            "observation, parser state, or E0 evidence is written on any path, and no transport "
            "is constructed."
        ),
    )
    _add_config_argument(recover_lease)
    recover_lease.add_argument(
        "--mode",
        required=True,
        choices=_M3_3_RECOVERY_MODES,
        help=(
            "preflight evaluates every eligibility predicate and writes nothing; execute "
            "repeats them, reasserts under the exclusive lock, and reconciles exactly once."
        ),
    )

    # Accepted Decision 116 §5. A canary-only surface, deliberately unlike the two PRE-E0
    # commands above: it holds no authority constant, creates no run namespace under the
    # private root, applies no migration, and writes every byte it produces into a disposable
    # world beneath an operator-supplied work root outside both the checkout and the private
    # evidence root. Its one selector is the plan's own source_instance_id — there is no path
    # option, no source-directory option, no all-sources mode, and no continuation.
    canary = m3_subparsers.add_parser(
        _M3_3_CANARY_COMMAND,
        help="Run exactly one governed planned source into a disposable compact world.",
        description=(
            "Materializes exactly one planned source, named by its own census_plan_sources "
            "source_instance_id, into a run-local Decision 111 working catalog under the "
            "supplied --work-root, bound explicitly to the accepted e0-compact-evidence/2 "
            "contract and emitting its Decision 112 §8 sidecar. The accepted operational "
            "catalog is opened strictly read-only on every path and no writer lease is taken "
            "on it; nothing is promoted, no migration is applied, and no E0 authority or run "
            "namespace is involved. One invocation runs one source and stops: there is no "
            "continuation to a second. preflight validates every predicate and creates "
            "nothing. profile-prefix is a diagnostic-only third mode: it runs the same path "
            "over the first --member-limit governed members and stops before any source-level "
            "finalization, so it never reports a parsed source, a complete-source identity, or "
            "a canary success. A completed run is not an authorization for M3.3-E0 or "
            "anything else."
        ),
    )
    _add_config_argument(canary)
    canary.add_argument(
        "--mode",
        required=True,
        choices=_M3_3_CANARY_MODES,
        help=(
            "preflight validates the plan selection, the world, and the boundaries read-only "
            "and creates nothing; run builds the disposable world and parses that one source; "
            "profile-prefix is diagnostic only -- it runs the same path over the first "
            "--member-limit governed members, finalizes nothing, and can never report success."
        ),
    )
    canary.add_argument(
        "--source-instance-id",
        required=True,
        metavar="SOURCE_INSTANCE_ID",
        help=(
            "The one planned source's own census_plan_sources key. An identifier the accepted "
            "plan does not carry, or carries more than once, is refused."
        ),
    )
    canary.add_argument(
        "--run-id",
        required=True,
        metavar="RUN_ID",
        help="This disposable world's identity. Create-once: an existing world is refused.",
    )
    canary.add_argument(
        "--work-root",
        required=True,
        metavar="ABSOLUTE_PATH",
        help=(
            "Absolute directory the disposable world is built under. Refused if it is inside "
            "the repository checkout, or is, contains, or lies inside the private evidence root."
        ),
    )
    canary.add_argument(
        "--require-volume-uuid",
        default=None,
        metavar="VOLUME_UUID",
        help=(
            "Assert that the work root is on the external volume with exactly this Volume UUID. "
            "It does NOT switch the protection on: a work root on any external volume is "
            "ALWAYS held to the full Decision 137 envelope -- exact volume identity, isolation "
            "from the immutable D130 archive, the bounded archive precheck, the 185 GiB launch "
            "floor, and an explicit external SQLITE_TMPDIR -- whether or not this is supplied. "
            "Omitting it cannot disable a single guard. Supplied, it must be the one qualified "
            "volume and it forces the envelope onto a root that would classify as internal. A "
            "wrong UUID, an absent volume, and a lookup that fails are all refusals; there is "
            "no fallback to internal storage. Supplying it is not an authorization to launch a "
            "corrected complete-source canary."
        ),
    )
    canary.add_argument(
        "--member-limit",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Diagnostic prefix bound: how many governed members profile-prefix traverses "
            "before it stops. Required and positive for --mode profile-prefix; refused for "
            "every other mode, because run is complete-source-only."
        ),
    )

    for name, gate, summary in _M3_3_GATED_COMMANDS:
        gated = m3_subparsers.add_parser(
            name,
            help=f"{summary} Recognized; refuses without a separate owner {gate} authorization.",
            description=(
                f"{summary} This surface is recognized so the contract's command set is "
                f"complete, and it refuses: {gate} is a separate Sol/GPT owner gate that no "
                "contract acceptance, passing rehearsal, green suite, commit, or tag supplies. "
                "It constructs no transport on any code path."
            ),
        )
        _add_config_argument(gated)
        _add_evidence_root_argument(gated)

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
    recovery_state.add_argument(
        "--plan",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The request plan the interrupted run was executing.",
    )
    # Exactly one mode, chosen explicitly. A missing or mistyped receipt path is an error in
    # ordinary mode and never silently selects receiptless inspection (Decision 051 §7.4, §8).
    mode = recovery_state.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--receipt-chain-head",
        type=Path,
        metavar="RELATIVE_PATH",
        help="The most recent receipt of the interrupted run (ordinary receipt-chain mode).",
    )
    mode.add_argument(
        "--receiptless-first-invocation",
        action="store_true",
        help=(
            "Forensic, read-only inspection of an interrupted first invocation that emitted no "
            "receipt. Never resume-eligible and never SAFE; requires --run."
        ),
    )
    recovery_state.add_argument(
        "--run",
        type=str,
        metavar="CENSUS_RUN_ID",
        help=(
            "The exact interrupted census run id. Required with --receiptless-first-invocation; "
            "rejected in ordinary receipt-chain mode so the mode is never inferred or mixed."
        ),
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
    _add_plan_transition_argument(recovery_state)

    _add_m3_2_parsers(m3_subparsers)


def _add_plan_transition_argument(parser: argparse.ArgumentParser) -> None:
    """Declare the explicit, bounded predecessor-plan argument (Decision 062 §7).

    Opt-in and never inferred. Without it, the plan hash must be unchanged exactly as before. With
    it, the named predecessor and the supplied successor go through the full seventeen-condition
    verification, which refuses every pair but the one an accepted owner decision names — so the
    flag exposes one authorized substitution rather than a general "resume against another plan".
    """
    parser.add_argument(
        "--plan-transition-predecessor",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help=(
            "The predecessor request plan a supplied successor plan continues, under an accepted "
            "owner plan-transition decision. Refused unless the two plans are exactly the pair "
            "that decision names, differing in exactly its named substitution."
        ),
    )


def _add_m3_2_parsers(m3_subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Wire the six Milestone 3.2 operator surfaces (Decision 045 §4).

    Five of them are offline in every mode. Only ``m3 acquire --live`` has a live path at all, and
    it is the only command whose handler can reach a transport-construction site.

    ``acquire``'s mode-specific arguments are declared optional at the argparse level and required
    per mode in the handler. That is deliberate: ``--show-scope`` and ``--live`` need different
    argument sets, and argparse cannot express "required only in this mode" without two subcommands
    the accepted interface does not have. The handler returns exit ``2`` for a missing or
    contradictory argument, which is what the accepted exit-code boundary reserves for a usage
    failure.
    """
    acquire = m3_subparsers.add_parser(
        "acquire",
        help="Controlled metadata-only acquisition, or its zero-request scope report.",
        description=(
            "Controlled metadata-only acquisition of the approved request plan. --show-scope "
            "reports the acquisition authority and places zero requests; it constructs no "
            "transport. --live is the only mode that may reach the network, and it additionally "
            "requires both tracked network switches, a valid SEC contact identity, the exact "
            "approved plan hash, the exact window, and the exact approved ceiling."
        ),
    )
    _add_config_argument(acquire)
    _add_evidence_root_argument(acquire)
    acquire.add_argument(
        "--live",
        action="store_true",
        help=(
            "Explicitly request live operation. No default: no configuration key, gate token, or "
            "contract acceptance stands in for this flag."
        ),
    )
    acquire.add_argument(
        "--show-scope",
        action="store_true",
        help=(
            "Report the acquisition authority for the requested window. Zero network, zero "
            "transport, no catalog, no receipt, no artifact."
        ),
    )
    acquire.add_argument(
        "--plan",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="The owner-approved request plan document, relative to --evidence-root.",
    )
    acquire.add_argument(
        "--window",
        default=None,
        metavar="M3.2A|M3.2B",
        help="The acquisition window this invocation addresses. Never inferred from the plan.",
    )
    acquire.add_argument(
        "--ceiling",
        type=int,
        default=None,
        metavar="INTEGER",
        help=(
            "The exact owner-approved physical-attempt ceiling. Must equal the plan's own derived "
            "ceiling exactly; it is never rounded, defaulted, or raised."
        ),
    )
    acquire.add_argument(
        "--catalog",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="The operational catalog, relative to --data-root.",
    )
    acquire.add_argument(
        "--data-root",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="The isolated Milestone 3.2 data root, relative to --evidence-root.",
    )
    acquire.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help="Where to write this invocation's execution receipt, relative to --evidence-root.",
    )
    acquire.add_argument(
        "--resume-from",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help=(
            "The exact predecessor receipt this invocation continues. Never inferred from ambient "
            "state; a resume registers its own new run identity."
        ),
    )
    acquire.add_argument(
        "--receipt-chain-head",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help=(
            "For --show-scope: the receipt chain whose consumed-count baseline is reconstructed. "
            "Omitting it reports a fresh chain baseline of zero."
        ),
    )
    acquire.add_argument(
        "--carry-in-authority",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help=(
            "The one-use owner authority carrying an approved consumed baseline into a clean new "
            "run, relative to --evidence-root. This is never a resume: it may not be combined with "
            "--resume-from, it is consumed exactly once, and it is never reissued automatically."
        ),
    )
    _add_plan_transition_argument(acquire)

    dependent = m3_subparsers.add_parser(
        "derive-dependent-plan",
        help="Derive the M3.2B dependent request plan from frozen M3.2A objects. Zero network.",
        description=(
            "Deterministic, zero-network derivation of the M3.2B dependent plan from frozen "
            "M3.2A objects and one explicit reviewed reconciliation set. It verifies object "
            "identity, hash, and provenance, refuses disagreement in either direction, derives "
            "only the two authorized dependent routes, and writes exactly one dry_run receipt on "
            "success. Successful derivation approves neither the resulting count nor a ceiling."
        ),
    )
    _add_config_argument(dependent)
    _add_evidence_root_argument(dependent)
    dependent.add_argument(
        "--from-window",
        required=True,
        metavar="M3.2A",
        help="The frozen source window. Must be exactly M3.2A for this dependent derivation.",
    )
    for name, help_text in (
        ("--catalog", "The frozen operational catalog, relative to --data-root."),
        ("--data-root", "The data root holding the frozen objects, relative to --evidence-root."),
        ("--reconciliation-set", "The explicit reviewed reconciliation set."),
        ("--plan-out", "Where to write the derived M3.2B plan."),
        ("--receipt-out", "Where to write the mandatory dry_run receipt."),
    ):
        dependent.add_argument(
            name, type=Path, required=True, metavar="RELATIVE_PATH", help=help_text
        )

    reconcile = m3_subparsers.add_parser(
        "reconcile-requests",
        help="Reconcile an approved plan against durable catalog and object state. Read-only.",
        description=(
            "Deterministic plan-to-catalog reconciliation. Exits 0 only when no blocking defect "
            "exists, the required-absence enumeration is empty, and any remaining divergence is "
            "plan-explained and nonblocking; otherwise exits 4 after completing the evaluation. "
            "It emits no receipt and writes one private, deterministic report."
        ),
    )
    _add_config_argument(reconcile)
    _add_evidence_root_argument(reconcile)
    for name, help_text in (
        ("--plan", "The approved request plan to reconcile."),
        ("--catalog", "The operational catalog, relative to --data-root."),
        ("--data-root", "The data root whose object store is reconciled."),
        ("--report-out", "Where to write the private deterministic reconciliation report."),
    ):
        reconcile.add_argument(
            name, type=Path, required=True, metavar="RELATIVE_PATH", help=help_text
        )
    _add_plan_transition_argument(reconcile)
    reconcile.add_argument(
        "--plan-transition-predecessor-receipt",
        type=Path,
        default=None,
        metavar="RELATIVE_PATH",
        help=(
            "The receipt of the run that executed the predecessor plan. Required with, and only "
            "with, --plan-transition-predecessor: the transition's registry-version condition asks "
            "what the predecessor run actually recorded, and only that run's receipt records it."
        ),
    )

    drift = m3_subparsers.add_parser(
        "show-drift",
        help="List the schema-drift events of exactly one M3.2 acquisition run. Read-only.",
        description=(
            "Lists and evaluates only the drift attributable through durable observation lineage "
            "to the supplied M3.2 acquisition run. There is no global-drift fallback: an unknown, "
            "non-M3.2, unattributable, or ambiguous run identity fails closed with exit 4, as "
            "does any blocking drift. It emits no receipt."
        ),
    )
    _add_config_argument(drift)
    _add_evidence_root_argument(drift)
    drift.add_argument(
        "--catalog",
        type=Path,
        required=True,
        metavar="RELATIVE_PATH",
        help="The operational catalog to inspect, relative to --evidence-root.",
    )
    drift.add_argument(
        "--run",
        required=True,
        metavar="CENSUS_RUN_ID",
        help=(
            "An existing ops_ingestion_jobs.job_id registered as an M3.2 acquisition run. Never "
            "created, fabricated, or inferred by this command."
        ),
    )

    recover = m3_subparsers.add_parser(
        "recover",
        help="Apply exactly one explicitly requested deterministic recovery action.",
        description=(
            "Exposes the accepted recovery applier unchanged. The run identity is mandatory and "
            "must already be a registered M3.2 acquisition run: this command never fabricates, "
            "substitutes, creates, or infers one. It emits no receipt; its durable evidence is "
            "the accepted recovery-state and recovery-event catalog family."
        ),
    )
    _add_config_argument(recover)
    _add_evidence_root_argument(recover)
    for name, help_text in (
        ("--plan", "The request plan the interrupted run was executing."),
        ("--receipt-chain-head", "The most recent receipt of the interrupted run."),
        ("--catalog", "The operational catalog, relative to --data-root."),
        ("--data-root", "The data root whose raw store is repaired, relative to --evidence-root."),
    ):
        recover.add_argument(
            name, type=Path, required=True, metavar="RELATIVE_PATH", help=help_text
        )
    recover.add_argument(
        "--run",
        required=True,
        metavar="CENSUS_RUN_ID",
        help=(
            "The already-registered M3.2 acquisition run this mutation is recorded under. "
            "Mandatory, verified to exist, and never fabricated by this command."
        ),
    )
    recover.add_argument(
        "--action",
        required=True,
        choices=sorted(RECOVERY_ACTIONS),
        help="The one deterministic recovery action class to apply.",
    )
    recover.add_argument(
        "--event",
        required=True,
        metavar="TARGET",
        help=(
            "The exact target the action addresses, as the deterministic recovery recommendation "
            "names it: a data-root-relative path, or the audit projection filename."
        ),
    )
    recover.add_argument(
        "--check-only",
        action="store_true",
        help=(
            "Report whether the requested action is eligible and stop. Mutates nothing, opens no "
            "writer, and consumes no repair authority, so eligibility can be proved before a "
            "one-use authority is spent. Exits 4 when the action would be refused."
        ),
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
    "m3 acquire": "m3.2/1.0",
    "m3 derive-dependent-plan": "m3.2b-plan/1.0",
    "m3 rehearse-execution": "m3.3a/1.0",
}

#: Label column for the ``m3 rehearse-execution`` summary. Wide enough for the longest
#: label — the amendment-purpose real-path gate — so every gate keeps its own aligned,
#: independently greppable line rather than being abbreviated or merged.
_M3_3A_SUMMARY_LABEL_WIDTH: Final = 39

#: Decision 094 §7's two PRE-E0 operator surfaces. Unlike the gated commands below, these are
#: **implemented**: `preflight` and `verify` do real read-only work and can pass, while
#: `execute` is reachable exactly while its own source-bound activation constant holds a
#: governed token, and returns exit 3 whenever that constant is `None`. That distinction is the
#: point of the redesign -- the old unconditional refusal made the transition and E0
#: unexecutable even after an owner authorized them.
_M3_3_PRE_E0_COMMANDS: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "prepare-e0-catalog",
        "Run the exact accepted-catalog 0013 -> 0014 -> 0015 transition (Decision 094 §5).",
        "Validates, and when separately authorized performs, the only lawful pre-E0 catalog "
        "transition. The private root is read from the fixed unlogged environment variable, "
        "the catalog and run namespace are internal constants, and preflight and verify are "
        "strictly read-only. execute returns exit 3 until a later exact owner instrument "
        "replaces PRE_E0_CATALOG_TRANSITION_AUTHORITY. Constructs no transport on any path.",
    ),
    (
        "offline-parse",
        "Derive the census parse layer from accepted stored objects, offline (M3.3-E0).",
        "Validates, and when separately authorized performs, the real M3.3-E0 offline "
        "metadata parse into the Decision 094 §6.1 sixteen-table footprint plus the "
        "category-A parser_state transition. execute is enabled only while an exact owner "
        "instrument holds M3_3_E0_EXECUTION_AUTHORITY, and returns exit 3 otherwise. A "
        "passing preflight is not authorization, and a complete run is not M3.3-E1 "
        "authority. No transport is constructed on any path.",
    ),
)

#: Accepted Decision 103 R6's recovery surface. It sits beside the two PRE-E0 commands rather
#: than among them because it is not a stage: it reconciles one stale writer lease left by an
#: interrupted run, and it has no `verify` mode because its entire result is one lease document
#: and one create-once record, both of which `preflight` already reads.
_M3_3_RECOVERY_COMMAND: Final = "reconcile-writer-lease"
_M3_3_RECOVERY_MODES: Final[tuple[str, ...]] = ("preflight", "execute")

#: Accepted Decision 116 §5's disposable single-source canary surface. It sits apart from the
#: PRE-E0 commands and from the recovery surface because it is neither a stage nor a
#: reconciliation: it runs one governed source into a disposable world and returns. Its second
#: mode is `run` rather than `execute` on purpose — `execute` is E0's governed, authority-gated
#: verb, and this path has no authority to gate.
#: Its third mode is diagnostic and is deliberately named as such: `profile-prefix` measures
#: the accepted materialization path over a bounded number of members and finalizes nothing
#: (accepted Decision 119 §6). `run` stays complete-source-only and refuses a bound.
_M3_3_CANARY_COMMAND: Final = "canary-source"
_M3_3_CANARY_MODES: Final[tuple[str, ...]] = ("preflight", "run", "profile-prefix")

#: The M3.3 real-execution surfaces the accepted contract §19 names. Each is recognized so
#: the command set is complete and each **refuses**: the owner gate it names has not been
#: issued, and no acceptance, rehearsal, suite, commit, or tag issues one.
_M3_3_GATED_COMMANDS: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "build-candidate-snapshot",
        "M3.3-E1",
        "Construct and freeze the authoritative candidate snapshot.",
    ),
    (
        "execute-selection",
        "M3.3-E1",
        "Execute, persist, reconstruct, and replay the accepted joint selection.",
    ),
    (
        "manifest-output",
        "M3.3-E2",
        "Construct the pilot manifest and render the deferred CLI output.",
    ),
)


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
    """The highest applied migration name, read without touching a durable byte.

    Opened ``SQLITE_OPEN_READONLY`` rather than by convention: M3.3 reaches this for
    receipt provenance, and ruling **R3** requires every governed M3.3 read-only path to
    be strictly read-only at the operating system. A read-write handle to a WAL-mode
    database checkpoints on close, which would rewrite the main file's bytes even though
    no statement wrote anything.
    """
    database = config.data_tree().catalog_database
    if not database.is_file():
        return "none"
    try:
        with strictly_read_only_connection(database) as connection:
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


def _write_m3_artifact_once(
    payload: bytes,
    *,
    evidence_root: Path,
    relative: Path,
    description: str,
) -> Path:
    """Write one evidence artifact below the root, never overwriting a different one.

    Contract §11 states that re-running never overwrites an existing artifact, and §15 keeps
    retained rehearsal evidence from being silently rewritten. Rewriting *byte-identical* content
    is a collision by identity rather than an edit, so an idempotent replay from the same explicit
    inputs still succeeds; anything else is refused, because a correction is a new artifact.

    Only the operator-supplied relative name appears in the refusal — the resolved absolute path
    is never rendered (§9).
    """
    destination = _m3_artifact_path(evidence_root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() != payload:
        message = (
            f"a different {description} already exists at {relative}; re-running never overwrites "
            f"an existing artifact, and a correction is a new artifact, never an edit"
        )
        raise GateFailureError(message)
    destination.write_bytes(payload)
    return destination


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
    return _write_m3_artifact_once(
        receipt.canonical_bytes(),
        evidence_root=evidence_root,
        relative=relative,
        description="receipt",
    )


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

    Every M3.1 command is offline, and five of the six Milestone 3.2 surfaces are offline in every
    mode. The evidence root is resolved and validated before any read or write, and a refusal is a
    configuration error rather than a gate failure: a root inside the checkout is a mistake in the
    invocation, not a finding about the run.
    """
    # Decision 094 §7.1: the two PRE-E0 surfaces take no --evidence-root, so they are routed
    # before the shared resolution below. They read the fixed unlogged environment variable
    # through the accepted external-root boundary instead, and the value never reaches this
    # module -- which is why nothing here can print, log, or persist it.
    if command in {name for name, _, _ in _M3_3_PRE_E0_COMMANDS}:
        return _m3_pre_e0_command(command, args, config, logger)
    if command == _M3_3_RECOVERY_COMMAND:
        return _m3_reconcile_writer_lease_command(args, config, logger)
    if command == _M3_3_CANARY_COMMAND:
        return _m3_canary_source_command(args, logger)

    try:
        evidence_root = require_external_evidence_root(args.evidence_root, _repository_root())
    except EvidenceRootError as exc:
        print(f"evidence root refused: {exc}", file=sys.stderr)
        logger.error("refused m3 %s: the evidence root is not external", command)
        return EXIT_CONFIG_ERROR

    handlers = {
        "rehearse": _m3_rehearse_command,
        "rehearse-execution": _m3_rehearse_execution_command,
        "rehearse-report": _m3_rehearse_report_command,
        **{name: _m3_gated_command for name, _, _ in _M3_3_GATED_COMMANDS},
        "plan-requests": _m3_plan_requests_command,
        "show-budget": _m3_show_budget_command,
        "show-receipt": _m3_show_receipt_command,
        "recovery-state": _m3_recovery_state_command,
        "acquire": _m3_acquire_command,
        "derive-dependent-plan": _m3_derive_dependent_plan_command,
        "reconcile-requests": _m3_reconcile_requests_command,
        "show-drift": _m3_show_drift_command,
        "recover": _m3_recover_command,
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


def _m3_pre_e0_command(
    command: str,
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
) -> int:
    """Dispatch one Decision 094 §7 PRE-E0 surface.

    This function does no work of its own beyond routing and rendering. Every predicate,
    write boundary, identity, and refusal lives in :mod:`disclosure_drift.m3.e0`, so the
    operator surface cannot become a second place where authority is decided.

    Nothing printed here can carry the private root: the module returns rendered lines built
    from counts, digests, enum tokens, and root-relative names, and the environment value is
    never returned to this layer at all.
    """
    from disclosure_drift.m3.e0 import run_offline_parse_command, run_prepare_e0_catalog_command

    mode = str(args.mode)
    runner = (
        run_prepare_e0_catalog_command
        if command == "prepare-e0-catalog"
        else run_offline_parse_command
    )
    result = runner(mode=mode, config=config, repository_root=_repository_root())
    return _report_pre_e0_result(result, command=command, mode=mode, logger=logger)


def _m3_reconcile_writer_lease_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
) -> int:
    """Dispatch the Decision 103 R6 stale-writer-lease recovery surface.

    Routing and rendering only, exactly like :func:`_m3_pre_e0_command`. Every eligibility
    predicate, the lock, the mutation, and the durable record live in
    :mod:`disclosure_drift.m3.e0`, so this layer cannot become a second place where a lease is
    judged reconcilable. It never sees the private root's value either — the module returns
    counts, digests, enum tokens, and fixed root-relative names.
    """
    from disclosure_drift.m3.e0 import run_reconcile_writer_lease_command

    mode = str(args.mode)
    result = run_reconcile_writer_lease_command(
        mode=mode, config=config, repository_root=_repository_root()
    )
    return _report_pre_e0_result(result, command=_M3_3_RECOVERY_COMMAND, mode=mode, logger=logger)


def _m3_canary_source_command(args: argparse.Namespace, logger: Logger) -> int:
    """Dispatch the accepted Decision 116 §5 disposable single-source canary surface.

    Routing and rendering only, exactly like the two surfaces above. Every predicate, every
    boundary, the disposable world, and every durable byte live in
    :mod:`disclosure_drift.m3.single_source_canary`, so this layer cannot become a second place
    where a canary is judged runnable.

    It takes no ``config`` argument beyond the one ``main`` already loaded and validated: this
    path reads no configuration value, and the private root comes from the fixed unlogged
    environment variable through the module's own boundary. Nothing printed here can carry the
    private root or the work root — the module returns counts, digests, enum tokens, and names
    relative to the disposable world.
    """
    from disclosure_drift.m3.single_source_canary import run_canary_source_command

    mode = str(args.mode)
    try:
        result = run_canary_source_command(
            mode=mode,
            run_id=str(args.run_id),
            source_instance_id=str(args.source_instance_id),
            work_root=str(args.work_root),
            repository_root=_repository_root(),
            member_limit=None if args.member_limit is None else int(args.member_limit),
            require_volume_uuid=(
                None if args.require_volume_uuid is None else str(args.require_volume_uuid)
            ),
        )
    except (DisclosureDriftError, sqlite3.Error) as exc:
        print(f"m3 {_M3_3_CANARY_COMMAND} failed: {exc}", file=sys.stderr)
        logger.error("m3 %s --mode %s did not pass", _M3_3_CANARY_COMMAND, mode)
        return EXIT_GATE_FAILURE
    except OSError as exc:
        # An OSError ordinarily carries the offending filename, which may be an absolute
        # personal path. Report the error class alone.
        print(
            f"m3 {_M3_3_CANARY_COMMAND} failed: {type(exc).__name__} while reading or writing "
            "a canary artifact",
            file=sys.stderr,
        )
        logger.error("m3 %s failed on a filesystem error", _M3_3_CANARY_COMMAND)
        return EXIT_GATE_FAILURE
    stream = sys.stdout if result.exit_code == EXIT_OK else sys.stderr
    for line in result.lines:
        print(line, file=stream)
    if result.exit_code != EXIT_OK:
        logger.error("m3 %s --mode %s did not pass", _M3_3_CANARY_COMMAND, mode)
    return result.exit_code


def _report_pre_e0_result(
    result: OperatorResult, *, command: str, mode: str, logger: Logger
) -> int:
    """Render one operator result to the right stream and log the right severity.

    Shared by every Decision 094 §7 / Decision 103 R6 surface so the exit-code-to-stream and
    exit-code-to-log-line mapping is stated once. Exit ``3`` is a governance fact and is logged
    as such; every other nonzero exit is a gate that ran and did not pass.
    """
    stream = sys.stdout if result.exit_code == EXIT_OK else sys.stderr
    for line in result.lines:
        print(line, file=stream)
    if result.exit_code == EXIT_STAGE_NOT_ENABLED:
        logger.error("m3 %s --mode %s is not enabled by the current boundary", command, mode)
    elif result.exit_code != EXIT_OK:
        logger.error("m3 %s --mode %s did not pass", command, mode)
    return result.exit_code


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
    # §11 places the synthetic data tree and synthetic catalog below the external evidence root,
    # alongside the evidence and the receipt. The root is already resolved and validated here.
    report = run_rehearsal(requested, workspace_root=evidence_root)
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
        ("A_reachable fully tested", "yes" if report.a_reachable_fully_tested else "no"),
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

    evidence_written = _write_m3_artifact_once(
        report.canonical_bytes(),
        evidence_root=evidence_root,
        relative=args.evidence_out,
        description="rehearsal evidence report",
    )
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
        # Decision 029 §5: a rehearsal that does not reach the state the specification names is an
        # integrity failure of the *evidence*, so it carries its own code.
        # `SEC_ACQUISITION_INTERRUPTED` stays reserved for a genuine acquisition interruption and
        # never stands in for a defective witness — a rehearsal interrupts no acquisition, because
        # it places no request.
        completion_status="complete" if _rehearsal_sound(report) else "failed",
        reason_code=(None if _rehearsal_sound(report) else "OFFLINE_REHEARSAL_SCENARIO_MISMATCH"),
        reason_detail=(None if _rehearsal_sound(report) else _rehearsal_receipt_detail(report)),
        rehearsal_evidence_reference=report.evidence_reference,
    )
    written = _write_m3_receipt(receipt, evidence_root=evidence_root, relative=args.receipt_out)
    print(f"  receipt written             : {args.receipt_out or written.name}")
    print(f"  receipt_id                  : {receipt.receipt_id}")

    if not report.passed:
        logger.error("m3 rehearse: a scenario failed; the phase does not pass")
        return EXIT_GATE_FAILURE
    # Master plan §17 stop condition 9 and Decision 029 §6: the token requires four conjuncts, and
    # two of them are about `A_reachable`. `a_reachable_agrees` quantifies only over the routes that
    # *were* measured, so a route excluded into `unmeasured_routes` would be silently skipped rather
    # than failing the gate — which is exactly how an unproven worst-path bound could claim M3.1A
    # passed. `a_reachable_fully_tested` closes that, and the key-set equality below closes the case
    # where a report is measured but omits a derived route.
    if not _rehearsal_sound(report):
        detail = _rehearsal_mismatch_detail(report)
        logger.error("m3 rehearse: %s", detail)
        print(f"  A_reachable evidence gap    : {detail}", file=sys.stderr)
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


def _m3_rehearse_execution_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Run the M3.3A execution rehearsal E1-E8 against disposable synthetic catalogs.

    Offline in every mode: it opens no socket, constructs no transport, resolves no host,
    and never reads the accepted real private catalog. Its disposable data trees and
    catalogs are created beneath the validated external evidence root, alongside the
    evidence report and the receipt.

    **A passing run authorizes nothing.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 each remain
    a separate owner gate, and both real-path feasibility gates stay open regardless of
    what this command reports.
    """
    requested = (
        None
        if args.scenarios.strip() == "all"
        else [item.strip() for item in args.scenarios.split(",") if item.strip()]
    )
    started = _utc_now()
    report = run_execution_rehearsal(requested, workspace_root=evidence_root)
    completed = _utc_now()

    for outcome in report.outcomes:
        status = "PASS" if outcome.passed else "FAIL"
        print(f"  {outcome.scenario_id:<4} {status}  {outcome.track:<8} {outcome.title}")
        if not outcome.passed:
            print(f"       {outcome.detail}")

    # Both real-path gates are printed separately and by name, read from the generated
    # payload so the printed summary and the evidence report can never disagree. They are
    # never merged into one line, and neither replaces the builder-feasibility claim
    # (Decision 073 **R30**, Decision 074 **R32**, Decision 075 §3.3).
    payload = report.as_payload()
    print("\nExecution rehearsal summary.")
    for label, value in (
        ("scenarios run", str(len(report.outcomes))),
        ("all eight run", "yes" if report.complete else "no"),
        ("every scenario passed", "yes" if report.passed else "no"),
        ("R28 bridge violations", str(report.bridge.get("violation_count", "unknown"))),
        ("builder-derived disposition", report.builder_derived_disposition),
        (
            "selector feasible on rehearsal",
            "yes" if report.accepted_selector_feasible_on_rehearsal_snapshot else "no",
        ),
        ("real builder feasibility proved", "no"),
        (
            "real amendment-purpose feasibility gate",
            str(payload["real_amendment_purpose_feasibility_gate"]),
        ),
        (
            "real linked-amendment feasibility gate",
            str(payload["real_linked_amendment_feasibility_gate"]),
        ),
        ("actual network requests", "0"),
        ("evidence reference", report.evidence_reference),
    ):
        print(f"  {label:<{_M3_3A_SUMMARY_LABEL_WIDTH}}: {value}")

    evidence_written = _write_m3_artifact_once(
        report.canonical_bytes(),
        evidence_root=evidence_root,
        relative=args.evidence_out,
        description="execution-rehearsal evidence report",
    )
    print(f"  {'evidence written':<{_M3_3A_SUMMARY_LABEL_WIDTH}}: {args.evidence_out}")

    receipt = ExecutionReceipt(
        command_name="m3 rehearse-execution",
        command_version=_M3_COMMAND_VERSIONS["m3 rehearse-execution"],
        phase="M3.3A",
        invocation_mode=OFFLINE_EXECUTION_MODE,
        configuration_fingerprint=_configuration_fingerprint(config),
        migration_chain_head=_migration_chain_head(config),
        cohort_definition_digest=cohort_definition_digest(),
        parser_versions={
            source_id: source.parser_version for source_id, source in sorted(SOURCES.items())
        },
        quota_policy_version=_offline_policy("quota_policy_version"),
        joint_selector_policy_version=_offline_policy("joint_selector_policy_version"),
        replacement_signature_policy_version=_offline_policy(
            "replacement_signature_policy_version"
        ),
        manifest_hash_policy_version=_offline_policy("manifest_hash_policy_version"),
        selection_input_schema_version=_offline_policy("selection_input_schema_version"),
        started_at_utc=_rfc3339(started),
        completed_at_utc=_rfc3339(completed),
        elapsed_seconds=round((completed - started).total_seconds(), 3),
        # Contract §6 item 5: an offline execution places no request, so both network
        # counts are zero. Nothing simulated is ever recorded in these fields.
        actual_logical_request_count=0,
        actual_physical_attempt_count=0,
        # Schema-drift fields belong to the live and rehearsal modes only; the receipt
        # spec forbids them here, so they are omitted rather than reported as "none".
        completion_status="complete" if report.passed else "failed",
        reason_code=(None if report.passed else "OFFLINE_REHEARSAL_SCENARIO_MISMATCH"),
        reason_detail=(None if report.passed else _execution_rehearsal_detail(report)),
        # `rehearsal_evidence_reference` is a rehearsal-mode field the spec forbids here.
        # The evidence report is named by the operator-supplied relative path printed
        # above and by its own content-derived reference, so nothing is lost.
    )
    written = _write_m3_receipt(receipt, evidence_root=evidence_root, relative=args.receipt_out)
    name = args.receipt_out or written.name
    print(f"  {'receipt written':<{_M3_3A_SUMMARY_LABEL_WIDTH}}: {name}")
    print(f"  {'receipt_id':<{_M3_3A_SUMMARY_LABEL_WIDTH}}: {receipt.receipt_id}")

    if not report.passed:
        logger.error("m3 rehearse-execution: a scenario failed; the phase does not pass")
        return EXIT_GATE_FAILURE
    if not report.complete:
        logger.warning("m3 rehearse-execution: a subset ran, so no completion statement is made")
        return EXIT_OK
    for label, artifact in (("receipt", written), ("evidence report", evidence_written)):
        if not artifact.is_file():  # pragma: no cover - the writes above raise on failure
            message = f"the execution-rehearsal {label} was not written"
            raise GateFailureError(message)
    print("\nM3_3A_EXECUTION_REHEARSAL_PASSED_NO_REAL_EXECUTION_AUTHORIZED")
    logger.info("m3 rehearse-execution: all eight scenarios passed")
    return EXIT_OK


def _offline_policy(name: str) -> str:
    """One accepted ``offline_execution`` policy version, read from its owning constant."""
    return offline_execution_policy_versions()[name]


def _execution_rehearsal_detail(report: object) -> str:
    """The first failing scenario, rendered without a path or an SEC identity."""
    outcomes = getattr(report, "outcomes", ())
    failed = [item.scenario_id for item in outcomes if not item.passed]
    return f"scenario(s) {','.join(failed)} did not reach the specified outcome"


def _m3_gated_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Refuse an M3.3 real-execution surface that has no owner authorization.

    The command exists so the accepted contract §19 surface set is complete and visible.
    It refuses, and the refusal is the point: **M3.3-E0, M3.3-E1, and M3.3-E2 are separate
    Sol/GPT owner gates**, and neither contract acceptance, a passing rehearsal, a green
    suite, a commit, a tag, nor the presence of a private catalog supplies one. Two
    real-path feasibility gates are additionally open. No transport is constructed on any
    path here.
    """
    del config, evidence_root
    command = str(args.m3_command)
    gate = next(item[1] for item in _M3_3_GATED_COMMANDS if item[0] == command)
    print(
        f"m3 {command} refused: {gate} is not authorized.\n"
        "  A separate Sol/GPT owner authorization is required, and no contract acceptance, "
        "rehearsal,\n  green suite, commit, tag, or private catalog supplies one.",
        file=sys.stderr,
    )
    logger.error("m3 %s refused: %s is not authorized", command, gate)
    return EXIT_STAGE_NOT_ENABLED


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
    # Recomputed, never trusted (Decision 029 §6): the stored booleans are claims about the record,
    # and `_bounds_agree` re-derives the authoritative key set, exact key equality, the emptiness of
    # `unmeasured_routes`, and numeric agreement from the record's own numbers. A forged
    # `a_reachable_fully_tested: true` beside a non-empty `unmeasured_routes` fails here.
    agrees = (
        bool(document.get("a_reachable_agrees"))
        and bool(document.get("a_reachable_fully_tested"))
        and _bounds_agree(document)
    )

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
        (
            "A_reachable fully tested",
            "yes" if _bounds_agree(document) else "no",
        ),
    ):
        print(f"  {label:<28}: {value}")

    if not (complete and passed and agrees):
        logger.error(
            "m3 rehearse-report: the record is not a complete passing A1-A12 record with an "
            "independently tested A_reachable for every derived route"
        )
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
        # Contract §9 lists the exact argument set for this command and it contains no
        # open-quarter switch. The provisional open quarter changes the planned quarter set and
        # therefore the budget integers the owner signs, so it is fixed closed here rather than
        # left switchable: Decision 013 §1 plans closed quarters only.
        include_open_quarter=False,
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
        _write_m3_artifact_once(
            canonical_plan_bytes(plan),
            evidence_root=evidence_root,
            relative=args.plan_out,
            description="request plan",
        )
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
        request_plan_schema_version=plan.request_plan_schema_version,
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
        chain = _resolve_receipt_chain(path, document, evidence_root=evidence_root)
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
    # The stored plan document is the authority on the plan, not a set of inputs to replan from.
    # Rebuilding from its `inputs` section cannot restore the already-satisfied instances that were
    # excluded before the plan was formed — that set is not an input the schema carries — so a
    # rebuild plans every cache hit again, derives a larger ceiling, and hashes differently.
    # Condition 8.10 would then read NOT MET for the very plan being executed, and 8.8 would measure
    # headroom against a ceiling nobody approved: a gate refusing the lawful case. Reading the
    # document instead keeps the governed hash and the signed ceiling exactly as written.
    plan = request_plan_from_document(_read_artifact_bytes(evidence_root, args.plan))

    data_root = _m3_artifact_path(evidence_root, args.data_root)
    # §9 makes every artifact argument a relative path contained by the resolved evidence root.
    # `--catalog` is named relative to `--data-root`, so the two are composed first and the result
    # goes through the same containment check every other artifact argument uses. Joining them
    # directly would let an absolute or `..`-climbing value open a database anywhere on the
    # machine; here it is refused by its bare name, never by an absolute path.
    catalog_path = _m3_artifact_path(evidence_root, Path(args.data_root) / args.catalog)

    if args.receiptless_first_invocation:
        # Receiptless mode is explicit and bound to the exact interrupted run identity. `--run` is
        # mandatory here; the argparse mutually-exclusive group already guarantees no
        # `--receipt-chain-head` was given (Decision 051 §7.4, §8).
        if args.run is None:
            return _usage_failure(
                "--receiptless-first-invocation requires --run CENSUS_RUN_ID",
                logger,
                "recovery-state",
            )
        # A transition binds to what a predecessor *receipt* recorded, and receiptless mode is
        # defined by there being none. Refused rather than ignored: silently dropping it would
        # report a determination the operator believes was reached under an authority.
        if args.plan_transition_predecessor is not None:
            return _usage_failure(
                "--plan-transition-predecessor is not valid with "
                "--receiptless-first-invocation; a plan transition binds to the registry version "
                "a predecessor receipt recorded, and a receiptless invocation recorded none",
                logger,
                "recovery-state",
            )
        state = inspect_receiptless_first_invocation(
            plan=plan,
            census_run_id=args.run,
            catalog_path=catalog_path,
            data_root=data_root,
        )
    else:
        # Ordinary receipt-chain mode. `--run` belongs only to receiptless mode, so accepting it
        # here would let the mode be inferred or mixed; it is refused instead.
        if args.run is not None:
            return _usage_failure(
                "--run is only valid with --receiptless-first-invocation, not in ordinary "
                "receipt-chain mode",
                logger,
                "recovery-state",
            )
        head_path = _m3_artifact_path(evidence_root, args.receipt_chain_head)
        state = inspect_recovery_state(
            plan=plan,
            receipt_chain_head=head_path,
            catalog_path=catalog_path,
            data_root=data_root,
            plan_transition=_resolved_plan_transition(evidence_root, args, plan, head_path),
            evidence_root=evidence_root,
        )

    print("Recovery determination (read-only; nothing was repaired).")
    for condition in state.conditions:
        print(f"  {condition.number:<5} {condition.status:<8} {condition.condition}")
    for label, value in (
        ("interruption state", str(state.interruption_state)),
        ("head completion status", str(state.head_completion_status)),
        ("receipt chain length", str(len(state.receipt_chain))),
        ("consumed physical attempts", str(state.consumed_physical_attempts)),
        ("committed observations", str(state.committed_observation_count)),
        ("orphan objects", str(state.orphan_object_count)),
        ("rows without object", str(state.rows_without_object_count)),
        ("partial files", str(state.partial_file_count)),
        ("determination", state.determination),
        # Reported beside the determination, and separately from it, because they answer a
        # different question. The determination is about evidence certainty; these are about
        # permission and outstanding work, and a completed window is `SAFE` with continuation
        # refused (Decision 064 §4). Both remainders come from the identity-level reconciliation
        # continuation enforcement uses, so this display and that enforcement cannot disagree.
        ("continuation permitted", "yes" if state.continuation_permitted else "no"),
        ("continuation remaining", str(state.remaining_logical_requests)),
        ("worst-case remaining attempts", str(state.worst_case_remaining_attempts)),
        ("basis", state.basis),
        ("required action", state.required_action),
    ):
        print(f"  {label:<28}: {value}")

    if state.determination != "SAFE":
        logger.error("m3 recovery-state: determination %s", state.determination)
        return EXIT_GATE_FAILURE
    logger.info("m3 recovery-state: SAFE")
    return EXIT_OK


def _resolved_plan_transition(
    evidence_root: Path,
    args: argparse.Namespace,
    successor_plan: RequestPlan,
    receipt_chain_head: Path,
) -> PlanTransitionAuthority | None:
    """Verify an explicitly requested plan transition, or return `None` when none was requested.

    The predecessor's recorded source-registry version is read from the **predecessor receipt**,
    not from the operator and not from the predecessor plan document: condition 14 asks what the
    run actually recorded, and the pre-transition plan schema recorded no registry version at all.

    ``receipt_chain_head`` is therefore the receipt of the run that executed the *predecessor* plan,
    and each caller names it explicitly. For a resume and for a recovery inspection that is the
    chain head, because the run being continued is the predecessor. For a reconciliation performed
    *after* the successor run completed it is not — the head is the successor's own receipt, which
    records the successor registry — so that surface takes the predecessor receipt as its own
    argument rather than assuming the two coincide.

    Raises:
        GateFailureError: the transition was requested but no receipt is available to bind it to.
        PlanTransitionRefusedError: the two plans are not the authorized pair.
    """
    relative = getattr(args, "plan_transition_predecessor", None)
    if relative is None:
        return None
    try:
        head = inspect_receipt(receipt_chain_head)
    except (OSError, ReceiptValidationError) as exc:
        message = (
            f"a plan transition binds to what the predecessor receipt recorded, and that receipt "
            f"could not be read: {exc}"
        )
        raise GateFailureError(message) from exc
    recorded = head.get("source_registry_version")
    predecessor = request_plan_from_document(_read_artifact_bytes(evidence_root, relative))
    return verify_plan_transition(
        predecessor_plan=predecessor,
        successor_plan=successor_plan,
        predecessor_source_registry_version=None if recorded is None else str(recorded),
    )


def _resolve_receipt_chain(
    head_path: Path, head: Mapping[str, object], *, evidence_root: Path | None = None
) -> tuple[str, ...]:
    """Resolve `recovery_predecessor_receipt_id` back to the first attempt.

    Receipt spec §14 requires a present predecessor to resolve to a readable receipt, and §11.4
    makes a broken chain a stop condition. Validating the head alone would let a receipt naming a
    predecessor that was never written pass as intact, which is precisely the case the chain exists
    to detect.

    Location is delegated to :func:`resolve_predecessor_receipt`, which searches the accepted
    receipt locations beneath ``evidence_root`` rather than only beside the head — a receipt written
    through `--receipt-out` into its own run namespace is otherwise unreachable from a head in a
    different one. Validation is unchanged: every candidate is loaded, schema-checked, and required
    to carry exactly the recorded identity.
    """
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
        try:
            _, document = resolve_predecessor_receipt(
                identifier,
                head_directory=head_path.parent,
                evidence_root=evidence_root,
            )
        except OSError as exc:
            # An OSError carries the absolute filename it failed on, which may never be printed.
            message = (
                f"recovery_predecessor_receipt_id {identifier[:12]}… does not resolve to a "
                f"readable receipt ({type(exc).__name__})"
            )
            raise ReceiptValidationError(message) from exc
        except ReceiptChainResolutionError as exc:
            # Already phrased against `recovery_predecessor_receipt_id`, and already free of any
            # absolute path. Re-wrapping would only bury the specific refusal.
            raise ReceiptValidationError(str(exc)) from exc
        except ReceiptValidationError as exc:
            message = (
                f"recovery_predecessor_receipt_id {identifier[:12]}… resolves to a receipt that "
                f"fails validation: {exc}"
            )
            raise ReceiptValidationError(message) from exc
        visited.add(identifier)
        chain.append(identifier)


def _rehearsal_sound(report: RehearsalReport) -> bool:
    """Whether the rehearsal's `A_reachable` evidence is complete as well as consistent.

    Decision 029 §6. Three separate things can be wrong, and only the first was ever checked:
    a measured bound can disagree with its derivation; a route can be excluded from measurement
    altogether; and a measured set can silently omit a route the derivation counts. A gate reading
    only `a_reachable_agrees` passes the last two, because that property quantifies over the tested
    keys rather than the derived ones.
    """
    return (
        report.passed
        and report.a_reachable_agrees
        and report.a_reachable_fully_tested
        and set(report.tested_a_reachable) == set(report.derived_a_reachable)
    )


def _rehearsal_mismatch_detail(report: RehearsalReport) -> str:
    """Say exactly which routes are missing, unmeasured, or disagreeing."""
    problems: list[str] = []
    if not report.passed:
        failed = sorted(outcome.scenario_id for outcome in report.outcomes if not outcome.passed)
        problems.append(f"scenario(s) failed: {', '.join(failed)}")
    disagreements = sorted(
        source_id
        for source_id, tested in report.tested_a_reachable.items()
        if report.derived_a_reachable.get(source_id) != tested
    )
    if disagreements:
        problems.append(
            "derived and independently tested A_reachable disagree for " + ", ".join(disagreements)
        )
    if report.unmeasured_routes:
        problems.append("no full-path witness for " + ", ".join(sorted(report.unmeasured_routes)))
    missing = sorted(set(report.derived_a_reachable) - set(report.tested_a_reachable))
    if missing:
        problems.append("derived route(s) absent from the tested set: " + ", ".join(missing))
    extra = sorted(set(report.tested_a_reachable) - set(report.derived_a_reachable))
    if extra:
        problems.append("tested route(s) absent from the derived set: " + ", ".join(extra))
    if not problems:  # pragma: no cover - only reached when the report is sound
        return "no defect recorded"
    return "; ".join(problems)


def _rehearsal_receipt_detail(report: RehearsalReport) -> str:
    """The same finding, compressed to the one short single-line sentence §4.8 permits.

    The stderr diagnostic names every affected route so an operator can act on it; a receipt field
    is bounded at 200 characters, so it counts rather than enumerates. The evidence report the
    receipt references carries the full picture, which is where a reader is sent for it.
    """
    failed = sum(1 for outcome in report.outcomes if not outcome.passed)
    disagreeing = sum(
        1
        for source_id, tested in report.tested_a_reachable.items()
        if report.derived_a_reachable.get(source_id) != tested
    )
    unwitnessed = len(report.unmeasured_routes)
    missing = len(set(report.derived_a_reachable) - set(report.tested_a_reachable))
    return (
        f"the rehearsal did not reach its specified state: {failed} failing scenario(s), "
        f"{disagreeing} disagreeing bound(s), {unwitnessed} unwitnessed route(s), "
        f"{missing} untested derived route(s)."
    )


def _bounds_agree(document: Mapping[str, object]) -> bool:
    """Recompute the authoritative derived bounds and check the stored record against them.

    The report carries `a_reachable_agrees` and `a_reachable_fully_tested` booleans, but a gate that
    reads either would accept a record whose own numbers contradict it. Master plan §17 item 9 and
    Decision 029 §6 make all three of disagreement, an unmeasured route, and an omitted route stop
    conditions.

    **A record does not get to define its own route set.** Comparing the two stored mappings to each
    other is not enough: a document naming one route in both mappings, with equal values and an
    empty `unmeasured_routes`, satisfies every stored-versus-stored comparison while withholding
    eight routes. So the derivation is recomputed here from the source registry — the same
    :func:`derive_a_reachable` over the same `SOURCES` the rehearsal itself derives from — and the
    record must reproduce it exactly, key for key and value for value, before its tested mapping is
    consulted at all. Equal-but-wrong bounds fail against the recomputation even though they agree
    with each other.
    """
    authoritative = {source_id: derive_a_reachable(spec) for source_id, spec in SOURCES.items()}
    derived = document.get("derived_a_reachable")
    tested = document.get("tested_a_reachable")
    unmeasured = document.get("unmeasured_routes", {})
    if not isinstance(derived, Mapping) or not isinstance(tested, Mapping):
        return False
    if not isinstance(unmeasured, Mapping) or unmeasured:
        return False
    if set(derived) != set(authoritative) or set(tested) != set(authoritative):
        return False
    return all(
        derived.get(source_id) == bound and tested.get(source_id) == bound
        for source_id, bound in authoritative.items()
    )


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


def _read_artifact_bytes(evidence_root: Path, relative: Path) -> bytes:
    """Read one artifact's exact bytes from below the evidence root.

    A stored artifact whose identity is a hash over its bytes has to be read *as bytes*: parsing to
    JSON and re-serializing would compare a reconstruction against a recomputation rather than
    against what is actually on disk.
    """
    path = _m3_artifact_path(evidence_root, relative)
    try:
        return path.read_bytes()
    except OSError as exc:
        # `str(OSError)` embeds the absolute filename, which §9 forbids printing.
        message = f"artifact {Path(relative).name!r} could not be read ({type(exc).__name__})"
        raise GateFailureError(message) from exc


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


# --------------------------------------------------------------------------- #
# Milestone 3.2 operator surfaces (Decision 045 §4)
# --------------------------------------------------------------------------- #
def _m3_catalog_path(evidence_root: Path, data_root: Path, catalog: Path) -> Path:
    """Resolve the operational catalog, which is named relative to the data root.

    Composed first and then contained, exactly as ``m3 recovery-state`` does: joining an operator
    string straight onto a resolved root would let an absolute or ``..``-climbing value open a
    database anywhere on the machine. Here it is refused by its bare name, never by an absolute
    path.
    """
    return _m3_artifact_path(evidence_root, Path(data_root) / catalog)


def _m3_migration_chain_head(catalog_path: Path) -> str:
    """The operational catalog's applied chain head, for the receipt's provenance field.

    Deliberately not :func:`_migration_chain_head`, which reads the *repository* data root: an
    M3.2 receipt reports the chain of the catalog the window actually ran against.

    Strictly read-only at the operating system, for the same **R3** reason: M3.3 reaches
    this path too, and a governed read-only action may not checkpoint or otherwise alter
    the main database.
    """
    if not catalog_path.is_file():
        return "none"
    try:
        with strictly_read_only_connection(catalog_path) as connection:
            row = connection.execute(
                "SELECT name FROM ops_schema_migrations ORDER BY name DESC LIMIT 1"
            ).fetchone()
    except (sqlite3.Error, DisclosureDriftError):
        return "none"
    return "none" if row is None else str(row[0])


def _usage_failure(message: str, logger: Logger, command: str) -> int:
    """Report one operator usage failure. Exit 2, never 3 or 4."""
    print(f"m3 {command}: {message}", file=sys.stderr)
    logger.error("m3 %s: usage failure", command)
    return EXIT_USAGE


def _gate_unavailable(message: str, logger: Logger, command: str) -> int:
    """Report one unavailable or disabled live operator gate. Exit 3, never 4."""
    print(f"m3 {command}: {message}", file=sys.stderr)
    logger.error("m3 %s: the live operator gate is unavailable", command)
    return EXIT_STAGE_NOT_ENABLED


def _m3_acquire_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Dispatch ``m3 acquire`` to exactly one of its two modes.

    The modes are mutually exclusive by construction. ``--show-scope`` is structurally incapable
    of reaching a transport: it never calls into the live path at all, so its zero-transport
    property is a fact about the call graph rather than about a flag being checked.
    """
    live = bool(getattr(args, "live", False))
    show_scope = bool(getattr(args, "show_scope", False))
    if live and show_scope:
        return _usage_failure(
            "--live and --show-scope are mutually exclusive; a scope report never acquires",
            logger,
            "acquire",
        )
    # Decision 055 §6: the carry-in interface is *never* resume. The two are refused together here,
    # at the very top of the dispatch, so the contradiction is rejected before a configuration is
    # consulted, a plan is read, an artifact is opened, or any durable state is touched - and long
    # before a transport could be constructed.
    if getattr(args, "carry_in_authority", None) is not None and args.resume_from is not None:
        return _usage_failure(
            "--carry-in-authority and --resume-from are mutually exclusive; a carry-in root begins "
            "a clean run from an approved baseline and is never a resume",
            logger,
            "acquire",
        )
    # A plan transition says which predecessor plan the supplied successor continues, so it is
    # meaningless — and therefore refused — without the resume that continues one. Refused here,
    # beside the other argument-decidable contradictions, before any durable state is touched.
    if getattr(args, "plan_transition_predecessor", None) is not None and args.resume_from is None:
        return _usage_failure(
            "--plan-transition-predecessor requires --resume-from; a plan transition names the "
            "predecessor a continuation continues, and there is nothing to continue without one",
            logger,
            "acquire",
        )
    if show_scope:
        return _m3_acquire_show_scope(args, config, logger, evidence_root)
    if not live:
        return _usage_failure(
            "one of --show-scope or --live is required; live acquisition has no default and is "
            "never implied by configuration",
            logger,
            "acquire",
        )
    return _m3_acquire_live(args, config, logger, evidence_root)


def _m3_acquire_show_scope(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Report the acquisition authority for one window. Zero network, zero transport, no artifact.

    It reads the approved plan document and, when one is supplied, reconstructs the consumed-count
    baseline from the receipt chain. It creates no catalog, writes no artifact, emits no receipt,
    constructs no client, and never enters :func:`_m3_acquire_live` - the only function in this
    module from which a transport-construction site is reachable.
    """
    missing = [name for name in ("plan", "window") if getattr(args, name, None) is None]
    if missing:
        return _usage_failure(
            f"--show-scope requires {', '.join('--' + name.replace('_', '-') for name in missing)}",
            logger,
            "acquire",
        )
    window = str(args.window)
    if window not in ACQUISITION_WINDOWS:
        print(
            f"window {window!r} is not one of the accepted acquisition windows "
            f"{list(ACQUISITION_WINDOWS)}",
            file=sys.stderr,
        )
        logger.error("m3 acquire --show-scope: unaccepted window")
        return EXIT_GATE_FAILURE

    plan = request_plan_from_document(_read_artifact_bytes(evidence_root, args.plan))
    if plan.acquisition_window != window:
        print(
            f"the approved plan is for window {plan.acquisition_window!r}, not {window!r}; a plan "
            "is never executed against another window",
            file=sys.stderr,
        )
        logger.error("m3 acquire --show-scope: plan window mismatch")
        return EXIT_GATE_FAILURE

    consumed = 0
    chain_length = 0
    carried_in = 0
    if args.receipt_chain_head is not None:
        head_path = _m3_artifact_path(evidence_root, args.receipt_chain_head)
        inspect_receipt(head_path)  # refuse an invalid head before any chain arithmetic
        # Decision 055 §7.5 requires `--show-scope` to agree with the receipt-chain walker, so it
        # calls the walker rather than restating the arithmetic. Reading the head alone would be
        # correct only while every receipt's carried-forward count happens to equal the sum of its
        # predecessors; the walker sums `actual_physical_attempt_count` across the whole chain and
        # adds the single no-predecessor root's carry-in exactly once, which is the definition.
        chain = walk_receipt_chain(head_path, evidence_root=evidence_root)
        if not chain.resolved:
            message = (
                f"the receipt chain does not resolve to a first attempt, so the consumed-count "
                f"baseline cannot be established: {chain.detail}"
            )
            raise GateFailureError(message)
        chain_length = len(chain.receipt_ids)
        consumed = chain.consumed_physical_attempts
        carried_in = chain.root_carried_forward

    hosts = sorted({route.host for route in plan.routes})
    allowed = sorted(route.source_id for route in plan.routes)
    prohibited = sorted(set(SOURCES) - set(allowed))
    print(f"m3 acquire scope — window {window} (zero requests placed).")
    print(f"  {'allowed hosts':<34}: {', '.join(hosts)}")
    print(f"  {'method':<34}: GET")
    print(f"  {'route allowlist':<34}: {', '.join(allowed)}")
    print(f"  {'prohibited route/family set':<34}: {', '.join(prohibited)}")
    print(f"  {'filing bodies and packages':<34}: prohibited in every window")
    print(f"  {'approved plan sha256':<34}: {plan.request_plan_sha256}")
    print(f"  {'approved request ceiling':<34}: {plan.hard_request_ceiling}")
    print(f"  {'consumed-count baseline':<34}: {consumed}")
    print(f"  {'of which carried in at root':<34}: {carried_in}")
    print(f"  {'receipt chain length':<34}: {chain_length}")
    print(f"  {'transport':<34}: not constructed by this command")
    print(f"  {'receipt':<34}: not emitted by this command")
    logger.info("m3 acquire --show-scope: reported %s authority with zero requests", window)
    return EXIT_OK


def _receipt_count(document: Mapping[str, object], field_name: str) -> int:
    """Read one non-negative integer count from a validated receipt, or refuse.

    An absent field is ``0``, which is what an omitted conditional count means. A present value
    that is not a non-negative integer is refused rather than coerced: the consumed-count baseline
    this feeds is what a later resume charges against the approved ceiling.
    """
    value = document.get(field_name)
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = f"receipt field {field_name} is not a non-negative integer count"
        raise GateFailureError(message)
    return value


@contextmanager
def _scoped_sigterm_interruption() -> Iterator[None]:
    """Route the first SIGTERM through the same interruption path a SIGINT takes.

    A live acquisition owns durable state — an open writer lease, an in-flight retrieval, a
    registered run row, a write-ahead attempt reservation — and the accepted lifecycle only
    reconciles that state when it observes the catchable ``KeyboardInterrupt`` a SIGINT delivers.
    SIGTERM otherwise terminates the process outright, so a graceful ``kill`` would skip the
    truthful run closure entirely. Installed **only** around the governed live-acquisition
    lifecycle, only on the main thread (``signal.signal`` refuses any other), and always restored in
    ``finally``, this raises ``KeyboardInterrupt`` on the first SIGTERM so the existing SIGINT
    handling reconciles the run through one code path (Decision 051 §7.3).

    The handler performs no SQLite, file, receipt, or catalog write — it only re-raises, exactly as
    the default SIGINT handler does; durable protection when a receipt cannot be emitted is the
    pre-send attempt reservation, not anything done here. A second SIGTERM during cleanup is ignored
    rather than raising again, so cleanup and any single terminating-receipt attempt are never
    duplicated. SIGINT is left untouched, so its existing behaviour is preserved. Nothing here
    claims to survive SIGKILL, a power loss, an OOM kill, or a kernel termination — none of those
    deliver a catchable signal.
    """
    if threading.current_thread() is not threading.main_thread():
        # Only the main thread may install a signal handler; a non-main caller keeps the default
        # SIGTERM disposition rather than pretending to have scoped it.
        yield
        return

    delivered = False

    def _handle_sigterm(_signum: int, _frame: object) -> None:
        nonlocal delivered
        if delivered:
            return  # the first SIGTERM already began the accepted interruption; never double it
        delivered = True
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def _m3_acquire_live(  # noqa: PLR0911, PLR0912 - one explicit operator gate ladder
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Execute one live acquisition invocation, or refuse before anything is constructed.

    The gate ladder runs in the accepted order and each rung reports its own exit class: a missing
    argument is a usage failure (``2``), a disabled or unavailable live gate is ``3``, and every
    governed integrity, plan, window, ceiling, run, or accounting refusal is ``4``.

    Nothing below constructs a transport. The single construction site lives in
    :func:`~disclosure_drift.m3.acquisition.execute_live_acquisition`, which reaches it only after
    the complete conjunction, the window bindings, the catalog and storage prerequisites, any
    resume proposal, and the durable run registration and its fresh-connection verification have
    all passed.

    **Nothing durable is created before a refusal that does not need it.** Every condition
    decidable from the operator's arguments, the configuration, and the approved plan alone - the
    explicit ``--live`` flag, both network switches, the canonical identity validator, the accepted
    window vocabulary, the exact plan hash, the exact window, the exact ceiling equality, route
    registration and window membership, and the filing-body prohibition - is proved *before*
    :func:`prepare_operational_catalog` runs. A refused invocation therefore leaves no operational
    catalog, no data root, and no lock file behind, rather than an empty database an operator has
    to recognize as debris. Only the genuinely catalog-dependent step, the resume's continuation
    proposal, stays after catalog preparation, because it reads durable state to decide at all.
    """
    required = ("plan", "window", "ceiling", "catalog", "data_root", "receipt_out")
    missing = [name for name in required if getattr(args, name, None) is None]
    if missing:
        return _usage_failure(
            "--live requires " + ", ".join("--" + name.replace("_", "-") for name in missing),
            logger,
            "acquire",
        )

    if not config.network.enabled:
        return _gate_unavailable(
            "network.enabled is false; live acquisition requires the accepted network "
            "prerequisite state and no flag overrides it",
            logger,
            "acquire",
        )
    if not config.network.m3_acquire_enabled:
        return _gate_unavailable(
            "network.m3_acquire_enabled is false; the global network switch never enables "
            "acquisition on its own",
            logger,
            "acquire",
        )
    try:
        user_agent = config.require_sec_user_agent()
    except SecUserAgentError as exc:
        return _gate_unavailable(
            f"the SEC contact identity is not accepted by the canonical validator: {exc}",
            logger,
            "acquire",
        )

    window = str(args.window)
    plan = request_plan_from_document(_read_artifact_bytes(evidence_root, args.plan))
    ceiling = int(args.ceiling)
    authorization = LiveOperationAuthorization(
        window=window,
        plan_sha256=plan.request_plan_sha256,
        approved_ceiling=ceiling,
        authorization_reference=_M3_2_STAGE_AUTHORITY,
    )
    gate = LiveOperatorGate(
        explicit_live=True,
        network_enabled=config.network.enabled,
        m3_acquire_enabled=config.network.m3_acquire_enabled,
        sec_identity_validated=bool(user_agent),
        stage_authority_reference=_M3_2_STAGE_AUTHORITY,
    )
    # Every binding decidable without durable state, proved before any of it is created. This is
    # the same one implementation `execute_live_acquisition` re-asserts adjacent to the
    # construction site; running it here as well is what keeps a wrong window, a mismatched plan
    # hash, or an unequal ceiling from leaving an empty operational catalog behind.
    verify_window_bindings(
        plan=plan,
        window=window,
        approved_ceiling=ceiling,
        authorization=authorization,
    )

    # The carry-in authority is parsed, canonicalized, hashed, and fully bound here - before the
    # operational catalog exists, before storage is prepared, and long before the transport factory
    # is reachable (Decision 055 §6.2). A refused authority therefore burns nothing and leaves no
    # durable state behind, and `execute_live_acquisition` re-proves the same bindings adjacent to
    # the construction site.
    carry_in = None
    if args.carry_in_authority is not None:
        carry_in = load_carry_in_authority(
            _read_artifact_bytes(evidence_root, args.carry_in_authority)
        )
        verify_carry_in_authority(
            carry_in,
            window=window,
            plan_sha256=plan.request_plan_sha256,
            approved_ceiling=ceiling,
            resuming=args.resume_from is not None,
        )

    # M3-L16: an M3.2A run states the consumed baseline it begins from. Decided from the operator's
    # arguments alone, so it lands here with the other argument-decidable refusals - before the
    # operational catalog is created, before storage is prepared, and before any durable state
    # exists to leave behind. `execute_live_acquisition` re-asserts it adjacent to the construction
    # site.
    require_m3_2a_consumed_baseline(
        window,
        carry_in=args.carry_in_authority is not None,
        resuming=args.resume_from is not None,
    )

    catalog_path = _m3_catalog_path(evidence_root, args.data_root, args.catalog)
    catalog = prepare_operational_catalog(
        evidence_root=evidence_root,
        relative_path=Path(args.data_root) / args.catalog,
        repository_root=_repository_root(),
    )
    storage = prepare_storage(
        evidence_root=evidence_root,
        data_root_relative=args.data_root,
        repository_root=_repository_root(),
    )

    continuation = None
    if args.resume_from is not None:
        resume_head = _m3_artifact_path(evidence_root, args.resume_from)
        continuation = propose_continuation(
            plan=plan,
            receipt_chain_head=resume_head,
            catalog_path=catalog_path,
            storage=storage,
            window=window,
            approved_ceiling=ceiling,
            plan_transition=_resolved_plan_transition(evidence_root, args, plan, resume_head),
            evidence_root=evidence_root,
        )

    # SIGTERM is scoped here, after every live gate has passed, so a graceful `kill` of a running
    # acquisition is reconciled through the same interruption lifecycle a SIGINT uses rather than
    # terminating the process before the run row is truthfully closed (Decision 051 §7.3). The
    # prior handler is always restored on exit.
    try:
        with _scoped_sigterm_interruption():
            result = execute_live_acquisition(
                plan=plan,
                window=window,
                approved_ceiling=ceiling,
                authorization=authorization,
                gate=gate,
                catalog=catalog,
                storage=storage,
                user_agent=user_agent,
                requests_per_second=float(config.sec.requests_per_second),
                burst=int(config.sec.burst),
                policy=RetrievalPolicy(
                    connect_timeout_seconds=float(config.sec.connect_timeout_seconds),
                    read_timeout_seconds=float(config.sec.read_timeout_seconds),
                    bulk_read_timeout_seconds=float(config.sec.bulk_read_timeout_seconds),
                    max_transient_retries=int(config.sec.max_retries),
                    cooldown_seconds=float(config.sec.cooldown_seconds),
                ),
                continuation=continuation,
                carry_in=carry_in,
            )
    except KeyboardInterrupt:
        # The invocation was interrupted (SIGINT, or a SIGTERM routed through the same path) and its
        # interruption point could not be established exactly, so the driver refused to produce a
        # window at all. No receipt is written: a receipt without an established interruption state
        # would fail the accepted recovery inspection's condition 8.2 anyway, and writing one would
        # advertise a resume that cannot safely start. What the interruption left on disk is
        # preserved untouched for the read-only recovery inspection to rule on.
        print(
            "m3 acquire: the invocation was interrupted and its exact interruption state could "
            "not be established, so no receipt was written; run m3 recovery-state before any "
            "further acquisition",
            file=sys.stderr,
        )
        logger.error("m3 acquire: interrupted without an establishable interruption state")
        return EXIT_GATE_FAILURE

    receipt = _live_acquisition_receipt(
        result,
        plan=plan,
        window=window,
        approved_ceiling=ceiling,
        continuation=continuation,
        config=config,
        catalog_path=catalog_path,
    )
    written = _write_m3_receipt(receipt, evidence_root=evidence_root, relative=args.receipt_out)

    outcome = result.outcome
    print(f"m3 acquire — window {window}.")
    print(f"  {'census run id':<34}: {result.census_run_id}")
    print(f"  {'completion status':<34}: {outcome.completion_status}")
    if outcome.interruption_state is not None:
        print(f"  {'interruption state':<34}: {outcome.interruption_state}")
    print(f"  {'planned logical requests':<34}: {outcome.planned_logical_requests}")
    print(f"  {'satisfied':<34}: {len(outcome.satisfied)}")
    print(f"  {'consumed physical attempts':<34}: {outcome.consumed_physical_attempts}")
    if result.carried_forward_consumed:
        print(f"  {'of which carried forward':<34}: {result.carried_forward_consumed}")
    if result.carry_in_authority_sha256 is not None:
        print(f"  {'carry-in authority':<34}: {result.carry_in_authority_sha256}")
    print(f"  {'approved request ceiling':<34}: {outcome.approved_ceiling}")
    print(f"  {'receipt written':<34}: {args.receipt_out or written.name}")
    print(f"  {'receipt_id':<34}: {receipt.receipt_id}")
    for failure in outcome.progress_failures:
        print(f"  {'progress sink':<34}: {failure}")

    if not outcome.completed_successfully:
        logger.error("m3 acquire: window %s did not complete successfully", window)
        return EXIT_GATE_FAILURE
    logger.info("m3 acquire: window %s completed successfully", window)
    return EXIT_OK


#: How an engine completion status maps onto the frozen receipt's closed status vocabulary. The
#: engine's ``incomplete`` - every request terminated, but a required object is absent - has no
#: frozen counterpart of its own, and deliberately does not get one: the receipt schema has no
#: ``completed_with_absences`` value and a run that left a required object absent is not a
#: successful window (accepted contract §14), so it is reported as ``failed``.
#:
#: ``interrupted`` maps to itself and to nothing else. It is the frozen vocabulary's own value for
#: a genuine external interruption of a lawful invocation, and it is what the accepted recovery
#: inspection's condition 8.2 reads to establish that the interruption point was recorded rather
#: than guessed. Folding it into ``failed`` - or letting ``failed`` stand in for it - would make a
#: real interrupted run unresumable through the accepted path, which is exactly the defect this
#: correction repairs.
_RECEIPT_COMPLETION_STATUS: Final[Mapping[str, str]] = {
    "complete": "complete",
    "incomplete": "failed",
    "interrupted": "interrupted",
    "stopped_at_ceiling": "stopped_at_ceiling",
    "stopped_by_gate": "stopped_by_gate",
    "failed": "failed",
}

#: The registered fallback reason a non-complete window reports when no narrower registered code
#: is present on any of its outcomes. It is an existing registry entry whose description is
#: exactly this case; no new reason code is introduced by this stage.
_ACQUISITION_FALLBACK_REASON: Final = "SEC_ACQUISITION_INTERRUPTED"


def _live_acquisition_receipt(  # noqa: PLR0913 - the frozen receipt binds many explicit facts
    result: LiveAcquisitionResult,
    *,
    plan: RequestPlan,
    window: str,
    approved_ceiling: int,
    continuation: ContinuationProposal | None,
    config: ProjectConfig,
    catalog_path: Path,
) -> ExecutionReceipt:
    """Assemble the one terminal receipt a lawful live invocation owes.

    Every count is bound from the producer side, and the two response-event maps come from the
    exhaustive accounting rather than from the request-disposition totals - Decision 045 §8 is
    explicit that request dispositions and response-policy events are different universes, and
    §9's equality invariant is checked here before anything is written.

    The two instants are the **run's own**, taken from the one governed clock the engine stamps
    its observations with, rather than sampled again here. That matters beyond tidiness: the
    accepted continuation math segments committed observations around ``completed_at_utc`` to
    decide which attempts a receipt already accounts for. A separately sampled, second-truncated
    instant can fall *before* observations the run itself covered, which charges them a second
    time against the approved ceiling on every resume. Reading both from the run removes the
    possibility rather than narrowing it: ``completed_at_utc`` is stamped after the last
    observation, by the same clock, at the same precision.

    ``cache_hit_count`` is the count of requests **already satisfied and therefore never placed**,
    which is the plan's own excluded set for a fresh window and the continuation proposal's
    excluded set for a resume. The legacy ``WindowOutcome.cache_hits`` alias is deliberately not
    used: it counts lawful ``304`` reuses, which belong in ``not_modified_count``.

    Raises:
        GateFailureError: the accounting cannot be proven exact. Decision 045 §9.5 requires
            exactness or a stop, so an inexact receipt is refused rather than written.
    """
    outcome = result.outcome
    accounting = result.accounting
    started_at = result.started_at_utc
    completed_at = result.completed_at_utc

    carried = result.carried_forward_consumed
    actual_physical = outcome.consumed_physical_attempts - (carried or 0)
    attempted = tuple(item for item in outcome.outcomes if item.attempts > 0)
    if sum(item.attempts for item in attempted) != actual_physical:
        message = (
            "the per-request attempt totals disagree with the window's consumed physical "
            "attempts, so the receipt's execution accounting cannot be proven exact"
        )
        raise GateFailureError(message)
    if not accounting.is_exact:
        message = (
            "the response-event accounting is not exact"
            + (f": {accounting.undetermined_basis}" if accounting.undetermined_basis else "")
            + "; an inexact receipt is refused rather than written"
        )
        raise GateFailureError(message)
    if accounting.status_event_count != actual_physical:
        message = (
            f"{accounting.status_event_count} response event(s) were accounted against "
            f"{actual_physical} physical attempt(s); every physical attempt produces exactly one "
            "response event"
        )
        raise GateFailureError(message)

    classification_totals, status_totals = accounting.as_receipt_totals()
    completion = _RECEIPT_COMPLETION_STATUS[outcome.completion_status]
    per_route: dict[str, dict[str, int]] = {}
    for item in attempted:
        entry = per_route.setdefault(
            item.request.source_id, {"logical_request_count": 0, "physical_attempt_count": 0}
        )
        entry["logical_request_count"] += 1
        entry["physical_attempt_count"] += item.attempts
    if not per_route:
        message = (
            "the window placed no physical attempt, so no live execution accounting exists to "
            "record; a receipt is refused rather than written with empty totals"
        )
        raise GateFailureError(message)

    drift_outcome, drift_events = _window_schema_drift(outcome)
    reason_code = None if completion == "complete" else _window_reason_code(outcome)
    remaining = len(outcome.unattempted) if completion == "stopped_at_ceiling" else None

    return ExecutionReceipt(
        command_name="m3 acquire",
        command_version=_M3_COMMAND_VERSIONS["m3 acquire"],
        phase=window,
        invocation_mode="live",
        configuration_fingerprint=_configuration_fingerprint(config),
        migration_chain_head=_m3_migration_chain_head(catalog_path),
        started_at_utc=started_at,
        completed_at_utc=completed_at,
        elapsed_seconds=_elapsed_seconds(started_at, completed_at),
        source_registry_version=M22_SOURCE_REGISTRY_VERSION,
        index_plan_policy_version=INDEX_PLAN_POLICY_VERSION,
        request_plan_schema_version=plan.request_plan_schema_version,
        parser_versions=_route_parser_versions(plan),
        acquisition_window=plan.acquisition_window,
        request_plan_id=plan.request_plan_id,
        request_plan_sha256=plan.request_plan_sha256,
        approved_request_ceiling=approved_ceiling,
        planned_logical_request_count=plan.planned_unique_logical_requests,
        maximum_physical_attempt_count=plan.maximum_physical_attempts,
        planned_per_route={
            route.source_id: route.planned_unique_logical_requests for route in plan.routes
        },
        actual_logical_request_count=len(attempted),
        actual_physical_attempt_count=actual_physical,
        actual_per_route=per_route,
        response_classification_totals=classification_totals,
        status_code_totals=status_totals,
        raw_object_count=outcome.new_raw_objects,
        duplicate_object_count=outcome.byte_identical_duplicates,
        cache_hit_count=_excluded_cache_hits(plan, continuation),
        not_modified_count=outcome.not_modified_reuses,
        quarantined_object_count=outcome.classification_totals["quarantined"],
        redirect_hop_count=accounting.redirect_hop_count,
        cooldown_count=accounting.cooldown_count,
        remaining_planned_logical_request_count=remaining,
        schema_drift_outcome=drift_outcome,
        schema_drift_event_count=drift_events,
        completion_status=completion,
        reason_code=reason_code,
        reason_detail=None if reason_code is None else _window_reason_detail(outcome),
        interruption_state=outcome.interruption_state,
        recovery_predecessor_receipt_id=result.predecessor_receipt_id,
        consumed_request_count_carried_forward=carried,
        carry_in_authority_sha256=result.carry_in_authority_sha256,
    )


def _elapsed_seconds(started_at_utc: str, completed_at_utc: str) -> float:
    """How long the invocation ran, from its own two recorded instants.

    Derived from the same two strings the receipt records rather than from a separate clock
    reading, so the elapsed figure and the timestamps beside it can never describe different
    intervals. An unparseable instant is ``0.0``: the receipt schema has already validated both
    against its timestamp pattern before this is reached, so this branch is unreachable in
    practice and exists so a timing field can never raise.
    """
    started = _parse_instant(started_at_utc)
    completed = _parse_instant(completed_at_utc)
    if started is None or completed is None:  # pragma: no cover - both are schema-validated
        return 0.0
    return round((completed - started).total_seconds(), 3)


def _parse_instant(value: str) -> datetime | None:
    """Parse one RFC 3339 ``Z`` instant, or ``None`` when it is not one."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:  # pragma: no cover - schema-validated before it reaches here
        return None


def _excluded_cache_hits(plan: RequestPlan, continuation: ContinuationProposal | None) -> int:
    """Requests already satisfied and therefore never placed (Decision 040 §6 ``cache_hit_count``).

    A resume reports the continuation proposal's excluded set, which is a snapshot over the whole
    durable history; a fresh window reports the plan's own ``expected_cache_hits``, the instances
    excluded before the plan was formed. Neither is the lawful-``304`` count, which the receipt
    keeps separately as ``not_modified_count``.
    """
    if continuation is not None:
        return continuation.already_satisfied_excluded_count
    return plan.expected_cache_hits


def _route_parser_versions(plan: RequestPlan) -> Mapping[str, str]:
    """The registered parser version of every route the window planned.

    Milestone 3.2 acquires and parses nothing, so this records the parser-version *provenance* of
    the objects it stored rather than claiming a parse happened. It is read from the source
    registry, which derives each version from the parser implementation rather than storing a copy.
    """
    return {
        require_registered(route.source_id).parser_id: require_registered(
            route.source_id
        ).parser_version
        for route in plan.routes
    }


def _window_schema_drift(outcome: WindowOutcome) -> tuple[str, int]:
    """The window's frozen ``schema_drift_outcome`` and event count.

    ``blocked`` when any observed drift reason blocks release, ``unknown_fields_retained`` when
    drift was observed and retained without blocking, and ``none`` otherwise. The three values are
    the frozen vocabulary; no fourth is invented for a window that parsed nothing.
    """
    drift_codes = [
        code
        for item in outcome.outcomes
        for code in item.reason_codes
        if code in _DRIFT_RECEIPT_CODES
    ]
    if not drift_codes:
        return "none", 0
    blocking = any(REASON_CODES[code].blocks_release for code in drift_codes)
    return ("blocked" if blocking else "unknown_fields_retained"), len(drift_codes)


#: Registered reason codes whose presence on a committed observation is a schema-drift event for
#: the receipt's drift fields. It is the same registered family the accepted T2.4 drift listing
#: reads, restated here because the driver keeps its copy private.
_DRIFT_RECEIPT_CODES: Final[frozenset[str]] = frozenset(
    {
        "PARSER_SCHEMA_DRIFT_OBSERVED",
        "RAW_ARCHIVE_INVALID",
        "RAW_ARCHIVE_MEMBER_REFUSED",
        "SEC_RESPONSE_MALFORMED",
        "SOURCE_CONTENT_UPDATED",
        "SOURCE_DATED_ARTIFACT_CHANGED",
        "SOURCE_IMMUTABLE_IDENTITY_MUTATED",
        "SOURCE_VALIDATOR_CONTRADICTION",
    }
)


def _window_reason_code(outcome: WindowOutcome) -> str:
    """One registered reason code for a non-complete window, chosen deterministically.

    The window's own stop reason first, then the lowest-sorting registered blocking code any
    outcome carries, then the registered fallback whose description is exactly "acquisition was
    interrupted and no narrower registered reason applies". No code is invented: an unregistered
    code would be refused by the receipt validator, and this stage introduces none.
    """
    for code in outcome.reason_codes:
        if code in REASON_CODES:
            return code
    blocking = sorted(
        {
            code
            for item in outcome.outcomes
            for code in item.reason_codes
            if code in REASON_CODES and REASON_CODES[code].blocks_release
        }
    )
    return blocking[0] if blocking else _ACQUISITION_FALLBACK_REASON


def _window_reason_detail(outcome: WindowOutcome) -> str:
    """One short single-line non-secret sentence for the receipt's ``reason_detail``.

    Built from counts and the frozen completion status only. The window's own ``detail`` string is
    deliberately not copied: it is bounded here rather than at its many producers, and a receipt
    field constrained to one short line must not depend on a caller having kept it short.
    """
    return (
        f"window {outcome.window} ended {outcome.completion_status} with "
        f"{len(outcome.satisfied)} of {outcome.planned_logical_requests} planned logical "
        f"request(s) satisfied"
    )


def _m3_derive_dependent_plan_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Derive the M3.2B dependent plan from frozen M3.2A objects. Zero network, always.

    Refuses before reading anything when the invoking configuration is transport-capable, writes
    the deterministic plan document, and then writes **exactly one** ``dry_run`` receipt. Every
    refusal path returns before either write, so a refused derivation leaves no plan and no
    success receipt behind.
    """
    started = _utc_now()
    catalog_path = _m3_catalog_path(evidence_root, args.data_root, args.catalog)
    storage = prepare_storage(
        evidence_root=evidence_root,
        data_root_relative=args.data_root,
        repository_root=_repository_root(),
    )
    derivation = derive_dependent_plan(
        from_window=str(args.from_window),
        catalog_path=catalog_path,
        storage=storage,
        reconciliation_set=_read_json_artifact(evidence_root, args.reconciliation_set),
        requests_per_second=float(config.sec.requests_per_second),
        transport_capable_configuration=(
            config.network.enabled or config.network.m3_acquire_enabled
        ),
    )
    plan = derivation.plan

    _write_m3_artifact_once(
        derivation.plan_bytes,
        evidence_root=evidence_root,
        relative=args.plan_out,
        description="dependent request plan",
    )

    completed = _utc_now()
    receipt = ExecutionReceipt(
        command_name="m3 derive-dependent-plan",
        command_version=_M3_COMMAND_VERSIONS["m3 derive-dependent-plan"],
        phase="M3.2B",
        invocation_mode="dry_run",
        configuration_fingerprint=_configuration_fingerprint(config),
        migration_chain_head=_m3_migration_chain_head(catalog_path),
        started_at_utc=_rfc3339(started),
        completed_at_utc=_rfc3339(completed),
        elapsed_seconds=round((completed - started).total_seconds(), 3),
        source_registry_version=M22_SOURCE_REGISTRY_VERSION,
        index_plan_policy_version=INDEX_PLAN_POLICY_VERSION,
        request_plan_schema_version=plan.request_plan_schema_version,
        acquisition_window=plan.acquisition_window,
        request_plan_id=plan.request_plan_id,
        request_plan_sha256=plan.request_plan_sha256,
        planned_logical_request_count=plan.planned_unique_logical_requests,
        maximum_physical_attempt_count=plan.maximum_physical_attempts,
        planned_per_route={
            route.source_id: route.planned_unique_logical_requests for route in plan.routes
        },
        # A derivation places nothing. `dry_run` is a zero-network mode, and the receipt refuses
        # any other value here rather than treating it as a reporting convention.
        actual_logical_request_count=0,
        actual_physical_attempt_count=0,
        completion_status="complete",
    )
    written = _write_m3_receipt(receipt, evidence_root=evidence_root, relative=args.receipt_out)

    print("M3.2B dependent plan derived (zero requests placed).")
    print(f"  {'frozen objects verified':<38}: {derivation.verified_object_count}")
    print(f"  {'entity instances':<38}: {derivation.entity_instance_count}")
    print(f"  {'historical instances':<38}: {derivation.historical_instance_count}")
    print(f"  {'dependent logical requests':<38}: {derivation.dependent_instance_count}")
    print(f"  {'derived hard request ceiling':<38}: {plan.hard_request_ceiling}")
    print(f"  {'request plan sha256':<38}: {plan.request_plan_sha256}")
    print(f"  {'plan written':<38}: {args.plan_out}")
    print(f"  {'receipt written':<38}: {args.receipt_out or written.name}")
    print(f"  {'receipt_id':<38}: {receipt.receipt_id}")
    print(f"  {'approval status':<38}: this command approves no count and no ceiling")
    logger.info("m3 derive-dependent-plan: derived the M3.2B plan with zero requests")
    return EXIT_OK


def _m3_reconcile_requests_command(
    args: argparse.Namespace,
    config: ProjectConfig,  # noqa: ARG001 - reconciliation reads only the explicit inputs
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Reconcile an approved plan against durable state, and write one private report.

    Exit ``0`` only when no blocking reconciliation defect exists, the required-absence
    enumeration is empty, and every remaining divergence is plan-explained and nonblocking.
    Otherwise exit ``4`` **after** the evaluation completed - a malformed input or an IO failure
    raises instead and is reported by the ordinary failure class, so an ordinary failure can never
    masquerade as a clean reconciliation.

    The report is written on both exits, because the evidence that explains a ``4`` is as
    load-bearing as the evidence that explains a ``0``. It emits no receipt.

    ``--plan-transition-predecessor`` makes this surface transition-aware (Decision 064 §7). It is
    opt-in and never inferred: without it, a successor plan reconciled against a catalog holding the
    predecessor's retired identity reports that identity as a blocking out-of-plan observation, and
    reconciliation can never come clean for a window an owner has already ruled on. With it, the
    *same* seventeen-condition verifier every other surface uses proves the pair, and the one
    superseded identity moves to ``superseded_out_of_plan`` — still stored, still visible, still
    failed historical evidence, still satisfying nothing. Every other out-of-plan observation stays
    blocking, and an unauthorized pair refuses rather than reconciling.
    """
    if (args.plan_transition_predecessor is None) != (
        args.plan_transition_predecessor_receipt is None
    ):
        return _usage_failure(
            "--plan-transition-predecessor and --plan-transition-predecessor-receipt are supplied "
            "together or not at all; the transition names a plan pair and binds to what the "
            "predecessor run recorded, and neither half establishes it alone",
            logger,
            "reconcile-requests",
        )

    plan = request_plan_from_document(_read_artifact_bytes(evidence_root, args.plan))
    catalog_path = _m3_catalog_path(evidence_root, args.data_root, args.catalog)
    storage = prepare_storage(
        evidence_root=evidence_root,
        data_root_relative=args.data_root,
        repository_root=_repository_root(),
    )
    transition = (
        None
        if args.plan_transition_predecessor is None
        else _resolved_plan_transition(
            evidence_root,
            args,
            plan,
            _m3_artifact_path(evidence_root, args.plan_transition_predecessor_receipt),
        )
    )
    reconciliation = reconcile_requests(
        plan=plan,
        reconstruction=reconstruct_catalog_state(catalog_path=catalog_path, storage=storage),
        storage=storage,
        plan_transition=transition,
    )

    clean = _reconciliation_is_clean(reconciliation)
    _write_m3_artifact_once(
        _canonical_json_bytes(
            _reconciliation_report(reconciliation, clean=clean, transition=transition)
        ),
        evidence_root=evidence_root,
        relative=args.report_out,
        description="reconciliation report",
    )

    print(f"Request reconciliation — window {reconciliation.window} (read-only).")
    for state, count in reconciliation.totals.items():
        print(f"  {state:<38}: {count}")
    for label, value in (
        ("required absences", str(len(reconciliation.absences))),
        (
            "absences without terminal reason",
            str(len(reconciliation.absences_without_terminal_reason)),
        ),
        ("out-of-plan observations", str(len(reconciliation.out_of_plan))),
        (
            "superseded out-of-plan observations",
            str(len(reconciliation.superseded_out_of_plan)),
        ),
        (
            "plan transition applied",
            "none" if transition is None else transition.decision_reference,
        ),
        ("store findings", str(len(reconciliation.store_findings))),
        ("blocking drift events", str(len(reconciliation.blocking_drift))),
        ("nonblocking drift events", str(len(reconciliation.nonblocking_drift))),
        ("blocked recovery states", str(reconciliation.blocked_recovery_states)),
        ("report written", str(args.report_out)),
    ):
        print(f"  {label:<38}: {value}")

    if not clean:
        logger.error("m3 reconcile-requests: a blocking defect or a required absence remains")
        return EXIT_GATE_FAILURE
    logger.info("m3 reconcile-requests: no blocking defect and no required absence")
    return EXIT_OK


def _reconciliation_is_clean(reconciliation: RequestReconciliation) -> bool:
    """Whether the evaluated reconciliation permits exit ``0`` (Decision 045 §4.4).

    Three conjuncts, stated exactly as the interface rules them: no blocking reconciliation
    defect, an empty required-absence enumeration, and no remaining divergence that is not
    plan-explained and nonblocking. Nonblocking drift is explicitly *not* a defect; an out-of-plan
    observation and a store finding are, because neither is explained by the plan.
    """
    return (
        not reconciliation.absences
        and not reconciliation.blocking_drift
        and not reconciliation.out_of_plan
        and not reconciliation.store_findings
        and reconciliation.blocked_recovery_states == 0
    )


def _reconciliation_report(
    reconciliation: RequestReconciliation,
    *,
    clean: bool,
    transition: PlanTransitionAuthority | None = None,
) -> Mapping[str, object]:
    """The private, deterministic reconciliation report document.

    Identical inputs serialize byte-identically: every list is already in the accepted
    reconciliation's own deterministic order, and the canonical writer sorts keys at every level.

    It records the evaluated result, the absence enumeration, and the blocking and nonblocking
    drift that explain the exit. It carries **no** raw progress-sink exception text: no field here
    is derived from one, and the reconciliation it renders is built from durable catalog state
    rather than from any in-memory run observable.

    Schema ``1.1`` adds exactly one field, ``plan_transition``, and changes nothing else. It is not
    decoration: a reconciliation that moves an observation out of the blocking set has to record
    *under what authority*, or the report states a clean result while silently omitting the reason a
    stranded identity stopped counting. ``null`` is the ordinary case and means no transition was
    supplied — which is also the only case a ``1.0`` reader ever saw.
    """
    return {
        "reconciliation_report_schema_version": "m3-2-reconciliation-report/1.1",
        "window": reconciliation.window,
        "plan_sha256": reconciliation.plan_sha256,
        "exit_is_clean": clean,
        "plan_transition": (
            None
            if transition is None
            else {
                "decision_reference": transition.decision_reference,
                "predecessor_plan_sha256": transition.predecessor_plan_sha256,
                "successor_plan_sha256": transition.successor_plan_sha256,
                "substituted_source_id": transition.substituted_source_id,
            }
        ),
        "absence_enumeration": [item.as_record() for item in reconciliation.absences],
        "absences_without_terminal_reason": [
            item.identity_label for item in reconciliation.absences_without_terminal_reason
        ],
        "blocking_drift": [entry.as_record() for entry in reconciliation.blocking_drift],
        "nonblocking_drift": [entry.as_record() for entry in reconciliation.nonblocking_drift],
        "reconciliation": reconciliation.as_record(),
    }


def _canonical_json_bytes(document: Mapping[str, object]) -> bytes:
    """Serialize one private artifact in the project's canonical JSON form.

    The same discipline the plan and the receipt use - UTF-8, LF only, keys sorted at every level,
    compact separators, non-finite numbers refused, one trailing newline - so a report is
    byte-comparable across machines and across reruns.
    """
    rendered = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return f"{rendered}\n".encode()


def _m3_show_drift_command(
    args: argparse.Namespace,
    config: ProjectConfig,  # noqa: ARG001 - drift inspection reads only the explicit inputs
    logger: Logger,
    evidence_root: Path,
) -> int:
    """List the drift of exactly one M3.2 acquisition run. Read-only; emits no receipt.

    There is no global-drift fallback and no unscoped listing: an unknown, non-M3.2,
    unattributable, or ambiguous run identity raises out of :func:`drift_for_run` and is reported
    as exit ``4``, exactly as blocking drift is.
    """
    scoped = drift_for_run(
        catalog_path=_m3_artifact_path(evidence_root, args.catalog),
        census_run_id=str(args.run),
    )

    print(f"Schema drift for census run {scoped.census_run_id} (stage {scoped.stage}).")
    print(f"  {'attributed observations':<38}: {scoped.attributed_observation_count}")
    print(f"  {'drift events':<38}: {len(scoped.entries)}")
    print(f"  {'blocking drift events':<38}: {len(scoped.blocking)}")
    print(f"  {'nonblocking drift events':<38}: {len(scoped.nonblocking)}")
    for entry in scoped.entries:
        marker = "BLOCKING" if entry.blocking else "retained"
        print(f"  {marker:<8} {entry.source_id:<32} {', '.join(entry.reason_codes)}")

    if scoped.has_blocking:
        logger.error("m3 show-drift: blocking drift is attributed to run %s", scoped.census_run_id)
        return EXIT_GATE_FAILURE
    logger.info("m3 show-drift: no blocking drift for run %s", scoped.census_run_id)
    return EXIT_OK


def _m3_recover_command(
    args: argparse.Namespace,
    config: ProjectConfig,
    logger: Logger,
    evidence_root: Path,
) -> int:
    """Apply exactly one explicitly requested recovery action under an existing run identity.

    The run identity is validated **before** the applier is invoked, and validation is a read of
    the durable ``ops_ingestion_jobs`` row: it must exist, be an M3.2 acquisition run, and carry
    an accepted acquisition window. This command never creates, fabricates, substitutes, or infers
    a run identity, and the accepted applier - which is passed the identity unchanged and likewise
    never mints one - is exposed without broadening its semantics. It emits no receipt.

    ``--event`` is the operator name for the exact target the action addresses, which is what the
    accepted applier calls its ``target``.

    The configured network switches are read for exactly one purpose: the projection rebuild's
    action-specific eligibility requires the network to be disabled (Decision 064 §5, condition 10).
    They authorize nothing here and are never consulted to permit anything.
    """
    catalog_path = _m3_catalog_path(evidence_root, args.data_root, args.catalog)
    validate_acquisition_run(catalog_path, str(args.run))

    plan = request_plan_from_document(_read_artifact_bytes(evidence_root, args.plan))
    storage = prepare_storage(
        evidence_root=evidence_root,
        data_root_relative=args.data_root,
        repository_root=_repository_root(),
    )
    network_disabled = not (config.network.enabled or config.network.m3_acquire_enabled)
    receipt_chain_head = _m3_artifact_path(evidence_root, args.receipt_chain_head)

    if args.check_only:
        return _m3_recover_check_only(
            args,
            logger,
            plan=plan,
            receipt_chain_head=receipt_chain_head,
            catalog_path=catalog_path,
            storage=storage,
            network_disabled=network_disabled,
            evidence_root=evidence_root,
        )

    result = apply_recovery_action(
        action=str(args.action),
        target=str(args.event),
        plan=plan,
        receipt_chain_head=receipt_chain_head,
        catalog_path=catalog_path,
        storage=storage,
        census_run_id=str(args.run),
        evidence_root=evidence_root,
        network_disabled=network_disabled,
    )

    print("Recovery action applied (exactly one; a fresh inspection is required next).")
    for label, value in (
        ("census run id", result.census_run_id),
        ("action", result.action),
        ("target", result.target),
        ("recovery state id", result.recovery_state_id),
        ("action taken", result.action_taken),
        ("event recorded", str(result.event_recorded)),
        ("state resolved", str(result.state_resolved)),
        ("post state undetermined", str(result.post_state_undetermined)),
        ("continuation", "prohibited until a fresh inspection returns SAFE"),
        ("detail", result.detail),
    ):
        print(f"  {label:<28}: {value}")

    if result.post_state_undetermined:
        logger.error("m3 recover: the post-action state is UNDETERMINED")
        return EXIT_GATE_FAILURE
    logger.info("m3 recover: applied %s and resolved its write-ahead state", result.action)
    return EXIT_OK


def _m3_recover_check_only(
    args: argparse.Namespace,
    logger: Logger,
    *,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    storage: StorageBinding,
    network_disabled: bool,
    evidence_root: Path,
) -> int:
    """Report the requested action's eligibility without applying it. Mutates nothing.

    Only ``rebuild-projection`` has an action-specific eligibility gate to report; the other three
    keep the blanket determination rule, and for those this prints the determination that decides
    them rather than inventing a per-condition table they do not have.
    """
    action = str(args.action)
    if action != "rebuild-projection":
        state = inspect_recovery_state(
            plan=plan,
            receipt_chain_head=receipt_chain_head,
            catalog_path=catalog_path,
            data_root=storage.data_root,
            evidence_root=evidence_root,
        )
        permitted = state.determination != "UNDETERMINED"
        print(f"Recovery action eligibility — {action} (read-only; nothing was applied).")
        print(f"  {'determination':<52}: {state.determination}")
        print(f"  {'eligible':<52}: {'yes' if permitted else 'no'}")
        print(f"  {'basis':<52}: {state.basis}")
    else:
        eligibility = rebuild_projection_eligibility(
            action=action,
            plan=plan,
            receipt_chain_head=receipt_chain_head,
            catalog_path=catalog_path,
            storage=storage,
            network_disabled=network_disabled,
            evidence_root=evidence_root,
        )
        permitted = eligibility.permitted
        print(f"Recovery action eligibility — {action} (read-only; nothing was applied).")
        for name, held, detail in eligibility.conditions:
            print(f"  {'HELD' if held else 'NOT HELD':<9}{name}")
            if not held:
                print(f"            {detail}")
        print(f"  {'eligible':<52}: {'yes' if permitted else 'no'}")

    if not permitted:
        logger.error("m3 recover --check-only: %s is not eligible", action)
        return EXIT_GATE_FAILURE
    logger.info("m3 recover --check-only: %s is eligible", action)
    return EXIT_OK
