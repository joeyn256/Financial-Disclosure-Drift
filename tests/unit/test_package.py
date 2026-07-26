"""Package import, version single-sourcing, and static networking-import checks."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import disclosure_drift

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "disclosure_drift"

#: Modules the package must never import directly, audited statically over our own sources.
#: A dependency may import ``socket`` transitively without performing any network access,
#: so this audit covers *our* import statements only. Proof that the CLI opens no
#: connection lives in ``tests/integration/test_no_network.py``, which blocks sockets
#: in-process while the commands run.
STATIC_FORBIDDEN_IMPORTS = frozenset(
    {
        "aiohttp",
        "http.client",
        "httpx",
        "requests",
        "socket",
        "urllib.request",
        "urllib3",
    }
)

#: Third-party HTTP clients that must not appear in ``sys.modules`` after import.
#: Standard-library modules are deliberately excluded: ``socket`` and friends can be
#: loaded transitively by a dependency, which is not evidence of network activity.
RUNTIME_FORBIDDEN_MODULES = frozenset(
    {
        "aiohttp",
        "httplib2",
        "httpx",
        "requests",
        "urllib3",
    }
)


def test_package_imports_and_exposes_public_api() -> None:
    assert disclosure_drift.__doc__
    for name in ("load_config", "configure_logging", "get_logger", "cohort_for"):
        assert callable(getattr(disclosure_drift, name))
    for name in ("FROZEN_COHORTS", "FROZEN_MATURITY_GATES", "FROZEN_BOOTSTRAP_SEED"):
        assert hasattr(disclosure_drift, name)


def test_version_is_single_sourced() -> None:
    """The installed distribution version is read from ``__init__.__version__``."""
    assert disclosure_drift.__version__ == "0.1.0"
    assert metadata.version("disclosure-drift") == disclosure_drift.__version__

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in pyproject
    assert 'path = "src/disclosure_drift/__init__.py"' in pyproject
    assert "\nversion = " not in pyproject


def _imported_modules(source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
            # ``from urllib import request`` must be audited as ``urllib.request``.
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
    return modules


def _is_forbidden(module: str) -> bool:
    return any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for forbidden in STATIC_FORBIDDEN_IMPORTS
    )


def test_static_check_no_networking_client_imported() -> None:
    """No package module imports a socket or HTTP client directly."""
    sources = sorted(PACKAGE_DIR.rglob("*.py"))
    assert sources, "expected package sources to scan"

    offenders: dict[str, set[str]] = {}
    for source in sources:
        found = {module for module in _imported_modules(source) if _is_forbidden(module)}
        if found:
            offenders[source.name] = found

    assert offenders == {}, f"networking imports found: {offenders}"


def test_static_audit_detects_a_forbidden_import() -> None:
    """Negative control: the audit flags a direct socket or HTTP-client import."""
    for statement in ("import socket", "from urllib import request", "import requests"):
        tree = ast.parse(statement)
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
                modules.update(f"{node.module}.{alias.name}" for alias in node.names)
        assert any(_is_forbidden(module) for module in modules), statement


def test_importing_package_loads_no_third_party_http_client() -> None:
    """A fresh interpreter importing the package pulls in no third-party HTTP client."""
    program = (
        "import json, sys;"
        "import disclosure_drift;"
        f"forbidden = set({sorted(RUNTIME_FORBIDDEN_MODULES)!r});"
        "print(json.dumps(sorted(forbidden.intersection(sys.modules))))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(completed.stdout.strip()) == []
