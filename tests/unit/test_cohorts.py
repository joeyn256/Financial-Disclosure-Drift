"""Frozen cohort integrity and mirror enforcement."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.cohorts import (
    COHORT_ORDER,
    FROZEN_BOOTSTRAP_SEED,
    FROZEN_COHORTS,
    FROZEN_MATURITY_GATES,
    FROZEN_SOURCE_RECORDS,
    STUDY_END,
    STUDY_START,
    CohortWindow,
    cohort_for,
)
from disclosure_drift.config import (
    ENV_OVERRIDES,
    RECOGNIZED_ENV_VARS,
    FrozenDefinitionMismatchError,
    load_config,
)


def test_five_cohorts_in_frozen_order() -> None:
    assert COHORT_ORDER == (
        "development",
        "transition",
        "primary_test",
        "prospective",
        "monitoring",
    )
    assert set(FROZEN_COHORTS) == set(COHORT_ORDER)


def test_frozen_boundaries_match_decision_003() -> None:
    expected = {
        "development": (date(2010, 1, 1), date(2021, 12, 31)),
        "transition": (date(2022, 1, 1), date(2023, 12, 31)),
        "primary_test": (date(2024, 1, 1), date(2024, 12, 31)),
        "prospective": (date(2025, 1, 1), date(2025, 12, 31)),
        "monitoring": (date(2026, 1, 1), date(2026, 12, 31)),
    }
    actual = {name: (window.start, window.end) for name, window in FROZEN_COHORTS.items()}
    assert actual == expected


def test_cohorts_are_contiguous_and_cover_the_study_period() -> None:
    windows = [FROZEN_COHORTS[name] for name in COHORT_ORDER]
    assert windows[0].start == STUDY_START
    assert windows[-1].end == STUDY_END
    for earlier, later in zip(windows[:-1], windows[1:], strict=True):
        assert later.start == earlier.end + timedelta(days=1)


def test_maturity_gates_and_seed_match_decision_005_and_preregistration() -> None:
    assert FROZEN_MATURITY_GATES["prospective_outcome_cutoff"] == date(2027, 3, 31)
    assert FROZEN_MATURITY_GATES["monitoring_outcome_cutoff"] == date(2028, 3, 31)
    assert FROZEN_BOOTSTRAP_SEED == 20260725
    assert FROZEN_SOURCE_RECORDS


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (date(2010, 1, 1), "development"),
        (date(2021, 12, 31), "development"),
        (date(2022, 1, 1), "transition"),
        (date(2024, 6, 30), "primary_test"),
        (date(2025, 12, 31), "prospective"),
        (date(2026, 12, 31), "monitoring"),
    ],
)
def test_cohort_lookup(moment: date, expected: str) -> None:
    window = cohort_for(moment)
    assert window is not None
    assert window.name == expected
    assert window.contains(moment)


@pytest.mark.parametrize("moment", [date(2009, 12, 31), date(2027, 1, 1)])
def test_dates_outside_the_design_have_no_cohort(moment: date) -> None:
    assert cohort_for(moment) is None


def test_cohort_window_is_immutable() -> None:
    window = FROZEN_COHORTS["primary_test"]
    with pytest.raises((AttributeError, TypeError)):
        window.start = date(2023, 1, 1)  # type: ignore[misc]
    assert isinstance(window, CohortWindow)


def test_no_environment_variable_can_reach_a_frozen_value() -> None:
    frozen_tokens = {"COHORT", "GATE", "CUTOFF", "SEED", "BOOTSTRAP"}
    for variable in RECOGNIZED_ENV_VARS:
        assert not any(token in variable.upper() for token in frozen_tokens)
    assert all(section in {"paths", "logging"} for section, _ in ENV_OVERRIDES.values())


def _mutations() -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = []
    for name in COHORT_ORDER:
        for bound in ("start", "end"):

            def _mutate(mapping: dict[str, Any], name: str = name, bound: str = bound) -> None:
                current = mapping["cohorts"][name][bound]
                mapping["cohorts"][name][bound] = current + timedelta(days=1)

            cases.append((f"cohorts.{name}.{bound}", _mutate))

    for gate in FROZEN_MATURITY_GATES:

        def _mutate_gate(mapping: dict[str, Any], gate: str = gate) -> None:
            mapping["gates"][gate] = mapping["gates"][gate] + timedelta(days=1)

        cases.append((f"gates.{gate}", _mutate_gate))

    def _mutate_seed(mapping: dict[str, Any]) -> None:
        mapping["seeds"]["bootstrap"] = FROZEN_BOOTSTRAP_SEED + 1

    cases.append(("seeds.bootstrap", _mutate_seed))
    return cases


@pytest.mark.parametrize(("field", "mutate"), _mutations(), ids=[case[0] for case in _mutations()])
def test_mirror_mismatch_hard_fails(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
    field: str,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    mapping = {
        **frozen_mapping,
        "cohorts": {name: dict(window) for name, window in frozen_mapping["cohorts"].items()},
        "gates": dict(frozen_mapping["gates"]),
        "seeds": dict(frozen_mapping["seeds"]),
    }
    mutate(mapping)
    path = write_config(mapping)

    with pytest.raises(FrozenDefinitionMismatchError) as excinfo:
        load_config(path, env={})

    message = str(excinfo.value)
    assert field in message
    assert "code constants are canonical" in message
    assert "approved decision record" in message


def test_missing_cohort_hard_fails(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    cohorts = {
        name: dict(window)
        for name, window in frozen_mapping["cohorts"].items()
        if name != "monitoring"
    }
    path = write_config({**frozen_mapping, "cohorts": cohorts})
    with pytest.raises(FrozenDefinitionMismatchError, match="missing monitoring"):
        load_config(path, env={})


def test_extra_cohort_hard_fails(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    cohorts = {name: dict(window) for name, window in frozen_mapping["cohorts"].items()}
    cohorts["future"] = {"start": date(2027, 1, 1), "end": date(2027, 12, 31)}
    path = write_config({**frozen_mapping, "cohorts": cohorts})
    with pytest.raises(FrozenDefinitionMismatchError, match="unexpected future"):
        load_config(path, env={})
