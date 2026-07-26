"""SEC contact-identity validation at the network boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from disclosure_drift.config import (
    BACKUP_ROOT_ENV,
    RECOGNIZED_ENV_VARS,
    RUNTIME_ROOT_ENV_VARS,
    SEC_USER_AGENT_ENV,
    load_config,
    validate_sec_user_agent,
)
from disclosure_drift.errors import NetworkDisabledError, SecUserAgentError
from disclosure_drift.sec.calendar import FROZEN_FILING_CUTOFF_ET

VALID = "Financial Disclosure Drift research@your-institution.edu"


def test_valid_identity_is_returned_normalized() -> None:
    assert validate_sec_user_agent("  Financial   Disclosure Drift  contact@your-org.edu ") == (
        "Financial Disclosure Drift contact@your-org.edu"
    )


@pytest.mark.parametrize("value", [None, "", "   ", "\t\n"])
def test_absent_or_blank_is_rejected(value: str | None) -> None:
    with pytest.raises(SecUserAgentError, match="not set or is blank"):
        validate_sec_user_agent(value)


@pytest.mark.parametrize(
    "value",
    [
        "Example Researcher researcher@example.com",
        "Financial Disclosure Drift real-contact-email@example.com",
        "Project x@example.org",
        "Project x@host.invalid",
        "Project x@service.test",
    ],
)
def test_placeholder_domains_are_rejected(value: str) -> None:
    with pytest.raises(SecUserAgentError, match="placeholder domain"):
        validate_sec_user_agent(value)


@pytest.mark.parametrize("value", ["Financial Disclosure Drift", "no-contact-here", "12345"])
def test_missing_contact_address_is_rejected(value: str) -> None:
    with pytest.raises(SecUserAgentError, match="no email-like administrative contact"):
        validate_sec_user_agent(value)


@pytest.mark.parametrize("value", ["research@your-institution.edu", "  contact@your-org.co  "])
def test_missing_project_identity_is_rejected(value: str) -> None:
    with pytest.raises(SecUserAgentError, match="no project or organization identity"):
        validate_sec_user_agent(value)


def test_error_message_names_the_variable() -> None:
    with pytest.raises(SecUserAgentError, match=SEC_USER_AGENT_ENV):
        validate_sec_user_agent(None, variable=SEC_USER_AGENT_ENV)


def test_config_requires_the_identity_and_never_stores_it(config_file: Path) -> None:
    config = load_config(config_file, env={})
    with pytest.raises(SecUserAgentError):
        config.require_sec_user_agent(env={})

    resolved = config.require_sec_user_agent(env={SEC_USER_AGENT_ENV: VALID})
    assert resolved == VALID
    assert VALID not in repr(config)
    assert VALID not in config.model_dump_json()


def test_network_is_disabled_by_default(config_file: Path) -> None:
    config = load_config(config_file, env={})
    assert config.network.enabled is False
    with pytest.raises(NetworkDisabledError, match="disabled in configuration"):
        config.require_network()


def test_companyfacts_is_disabled_by_default(config_file: Path) -> None:
    config = load_config(config_file, env={})
    assert config.companyfacts.enabled is False
    assert config.companyfacts.documented_need is None


def test_backup_root_is_recognized_but_is_not_a_config_override(
    config_file: Path,
    tmp_path: Path,
) -> None:
    assert BACKUP_ROOT_ENV in RUNTIME_ROOT_ENV_VARS
    assert BACKUP_ROOT_ENV in RECOGNIZED_ENV_VARS

    env = {BACKUP_ROOT_ENV: str(tmp_path)}
    config = load_config(config_file, env=env)
    baseline = load_config(config_file, env={})

    assert config.paths == baseline.paths
    assert config.backup_root(env).require() == tmp_path
    assert not baseline.backup_root({}).configured


FILING_CUTOFF_KEYS = ("filing_cutoff", "filing_cutoff_et", "after_hours_cutoff", "cutoff_et")
OUTCOME_MATURITY_KEYS = ("prospective_outcome_cutoff", "monitoring_outcome_cutoff")


def test_filing_cutoff_is_not_configurable(config_file: Path, repo_root: Path) -> None:
    """The frozen 17:30 ET filing cutoff is code-only.

    The configuration legitimately contains the frozen outcome-maturity cutoffs, so
    the invariant is about a *filing* cutoff field, not the substring "cutoff".
    """
    config = load_config(config_file, env={})
    tracked_yaml = yaml.safe_load(
        (repo_root / "configs" / "project.yaml").read_text(encoding="utf-8")
    )
    sec_section = set(config.sec.model_dump())
    yaml_keys = {key.lower() for key in _all_keys(tracked_yaml)}

    assert FROZEN_FILING_CUTOFF_ET.isoformat() == "17:30:00"
    assert not [name for name in sec_section if "cutoff" in name.lower()]
    assert not [key for key in FILING_CUTOFF_KEYS if key in yaml_keys]
    assert not [name for name in RECOGNIZED_ENV_VARS if "CUTOFF" in name.upper()]


def test_outcome_maturity_cutoffs_remain_configured(config_file: Path) -> None:
    """The frozen maturity gates are separate fields and must not be removed."""
    config = load_config(config_file, env={})
    gates = config.gates.model_dump()
    assert set(gates) == set(OUTCOME_MATURITY_KEYS)
    assert gates["prospective_outcome_cutoff"].isoformat() == "2027-03-31"
    assert gates["monitoring_outcome_cutoff"].isoformat() == "2028-03-31"


def _all_keys(node: object) -> list[str]:
    """Return every mapping key in a nested YAML document."""
    keys: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            keys.append(str(key))
            keys.extend(_all_keys(value))
    elif isinstance(node, list):
        for item in node:
            keys.extend(_all_keys(item))
    return keys


def test_audit_root_is_derived_not_configured(config_file: Path) -> None:
    config = load_config(config_file, env={})
    tree = config.data_tree()
    assert tree.audit == tree.data_root / "audit" / "sec"
    assert "DISCLOSURE_DRIFT_AUDIT_ROOT" not in RECOGNIZED_ENV_VARS
