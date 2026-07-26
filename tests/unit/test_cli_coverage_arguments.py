"""Acceptance regression: the CLI coverage arguments reach the census helpers intact.

The command boundary parses and validates ``--coverage-start``, ``--coverage-end``, and
``--as-of`` exactly once, narrows them to concrete dates, and passes the resulting
:class:`CoverageWindow` object through. No helper reconstructs it, and no helper ever
substitutes today's date. Dry-run stays entirely offline.
"""

from __future__ import annotations

import argparse
from datetime import date
from typing import Any

import pytest

from disclosure_drift import cli
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances

APPROVED_WINDOW = ("--coverage-start", "2009-01-01", "--coverage-end", "2024-12-31")
APPROVED_AS_OF = ("--as-of", "2025-01-15")


def parse(argv: list[str]) -> argparse.Namespace:
    """Parse a census command line through the real parser."""
    return cli.build_parser().parse_args(argv)


def census_argv(*extra: str) -> list[str]:
    """A census dry-run command line with ``extra`` arguments appended."""
    return ["sec", "census", "--dry-run", *extra]


# --------------------------------------------------------------------------- #
# All three dates accepted; partial input rejected
# --------------------------------------------------------------------------- #
def test_all_three_coverage_dates_are_accepted_and_narrowed() -> None:
    args = parse(census_argv(*APPROVED_WINDOW, *APPROVED_AS_OF))
    window = cli._coverage_from_args(args)  # noqa: SLF001 - boundary under test
    assert isinstance(window, CoverageWindow)
    assert window.coverage_start == date(2009, 1, 1)
    assert window.coverage_end == date(2024, 12, 31)
    assert window.as_of_date == date(2025, 1, 15)
    assert window.include_open_quarter is False
    # Narrowed to concrete dates, not left as strings or None.
    for value in (window.coverage_start, window.coverage_end, window.as_of_date):
        assert isinstance(value, date)


def test_no_coverage_argument_yields_no_window() -> None:
    assert cli._coverage_from_args(parse(census_argv())) is None  # noqa: SLF001


@pytest.mark.parametrize(
    "partial",
    [
        ("--coverage-start", "2009-01-01"),
        ("--coverage-end", "2024-12-31"),
        ("--as-of", "2025-01-15"),
        ("--coverage-start", "2009-01-01", "--coverage-end", "2024-12-31"),
        ("--coverage-start", "2009-01-01", "--as-of", "2025-01-15"),
        ("--coverage-end", "2024-12-31", "--as-of", "2025-01-15"),
    ],
)
def test_a_partial_date_set_is_rejected_with_the_documented_message(
    partial: tuple[str, ...],
) -> None:
    args = parse(census_argv(*partial))
    with pytest.raises(argparse.ArgumentTypeError, match="must be supplied together"):
        cli._coverage_from_args(args)  # noqa: SLF001


def test_the_rejection_message_rules_out_inferring_today() -> None:
    args = parse(census_argv("--coverage-start", "2009-01-01"))
    with pytest.raises(argparse.ArgumentTypeError, match="never filled in from today"):
        cli._coverage_from_args(args)  # noqa: SLF001


def test_a_malformed_date_is_refused_by_the_argument_type() -> None:
    with pytest.raises(SystemExit):
        parse(census_argv("--as-of", "15-01-2025"))


def test_the_open_quarter_flag_is_carried_onto_the_window() -> None:
    args = parse(census_argv(*APPROVED_WINDOW, *APPROVED_AS_OF, "--include-open-quarter"))
    window = cli._coverage_from_args(args)  # noqa: SLF001
    assert window is not None
    assert window.include_open_quarter is True


# --------------------------------------------------------------------------- #
# The helpers accept and use the exact object
# --------------------------------------------------------------------------- #
def test_both_census_helpers_accept_the_coverage_keyword() -> None:
    """The reported defect: callers passed ``coverage=`` to helpers lacking the parameter."""
    import inspect

    for helper in (cli._census_dry_run, cli._census_command):  # noqa: SLF001
        parameters = inspect.signature(helper).parameters
        assert "coverage" in parameters, helper.__name__
        assert parameters["coverage"].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters["coverage"].default is None


def test_dry_run_receives_the_exact_coverage_object(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}
    window = CoverageWindow(date(2009, 1, 1), date(2024, 12, 31), date(2025, 1, 15))

    def capture(config: Any, logger: Any, **kwargs: Any) -> int:
        seen.update(kwargs)
        return cli.EXIT_OK

    monkeypatch.setattr(cli, "_census_dry_run", capture)
    exit_code = cli._sec_command(  # noqa: SLF001
        "census",
        _config_stub(),
        _logger_stub(),
        dry_run=True,
        calendar_year=2024,
        coverage=window,
    )
    assert exit_code == cli.EXIT_OK
    # The identical object, not a reconstruction.
    assert seen["coverage"] is window
    assert seen["calendar_year"] == 2024


def test_the_live_helper_receives_the_exact_coverage_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}
    window = CoverageWindow(date(2009, 1, 1), date(2024, 12, 31), date(2025, 1, 15))

    def capture(config: Any, logger: Any, **kwargs: Any) -> int:
        seen.update(kwargs)
        return cli.EXIT_OK

    monkeypatch.setattr(cli, "_census_command", capture)
    exit_code = cli._sec_command(  # noqa: SLF001
        "census",
        _config_stub(network_enabled=True),
        _logger_stub(),
        dry_run=False,
        calendar_year=2024,
        coverage=window,
    )
    assert exit_code == cli.EXIT_OK
    assert seen["coverage"] is window


# --------------------------------------------------------------------------- #
# The plan the approved window produces
# --------------------------------------------------------------------------- #
def test_the_approved_window_plans_sixty_four_required_closed_quarters() -> None:
    args = parse(census_argv(*APPROVED_WINDOW, *APPROVED_AS_OF))
    window = cli._coverage_from_args(args)  # noqa: SLF001
    assert window is not None
    plan = plan_index_instances(window)
    assert len(plan.required_closed) == 64
    assert plan.provisional_open is None
    assert plan.excluded_future_quarters == ()


def test_repeated_dry_runs_produce_the_same_plan_hash() -> None:
    argv = census_argv(*APPROVED_WINDOW, *APPROVED_AS_OF)
    first = cli._coverage_from_args(parse(argv))  # noqa: SLF001
    second = cli._coverage_from_args(parse(argv))  # noqa: SLF001
    assert first is not None
    assert second is not None
    assert plan_index_instances(first).plan_hash() == plan_index_instances(second).plan_hash()


def test_a_different_as_of_date_changes_the_plan_hash() -> None:
    baseline = cli._coverage_from_args(  # noqa: SLF001
        parse(census_argv(*APPROVED_WINDOW, *APPROVED_AS_OF))
    )
    shifted = cli._coverage_from_args(  # noqa: SLF001
        parse(census_argv(*APPROVED_WINDOW, "--as-of", "2025-04-01"))
    )
    assert baseline is not None
    assert shifted is not None
    assert plan_index_instances(baseline).plan_hash() != plan_index_instances(shifted).plan_hash()


# --------------------------------------------------------------------------- #
# Offline
# --------------------------------------------------------------------------- #
def test_building_the_plan_needs_no_network() -> None:
    """The autouse conftest fixture makes any socket use raise.

    Reaching a plan hash therefore proves the coverage path is entirely offline.
    """
    window = cli._coverage_from_args(  # noqa: SLF001
        parse(census_argv(*APPROVED_WINDOW, *APPROVED_AS_OF))
    )
    assert window is not None
    assert len(plan_index_instances(window).plan_hash()) == 64


# --------------------------------------------------------------------------- #
# Stubs
# --------------------------------------------------------------------------- #
class _NetworkStub:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled


class _ConfigStub:
    """The minimum surface ``_sec_command`` touches before delegating."""

    def __init__(self, network_enabled: bool) -> None:
        self.network = _NetworkStub(network_enabled)

    def require_sec_user_agent(self) -> str:
        return "Financial Disclosure Drift research@your-institution.edu"


class _LoggerStub:
    def error(self, *args: Any, **kwargs: Any) -> None:
        return None

    def info(self, *args: Any, **kwargs: Any) -> None:
        return None

    def warning(self, *args: Any, **kwargs: Any) -> None:
        return None


def _config_stub(*, network_enabled: bool = False) -> Any:
    return _ConfigStub(network_enabled)


def _logger_stub() -> Any:
    return _LoggerStub()
