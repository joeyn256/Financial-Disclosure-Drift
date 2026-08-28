"""D151-C21: the four D151-C20 findings, corrected and proved behaviourally.

**C20-MINOR-1 -- the temp root's encoded-byte usability (C2101-C2105).** SQLite composes
``<dir>/etilqs_<hex>`` into a fixed ``mxPathname`` buffer, so a root that passes every directory
test can still make the first spilling statement fail. The ONE shared validator now refuses a raw
value above :data:`~disclosure_drift.m3.external_working_root.SQLITE_TEMP_ROOT_MAX_ENCODED_BYTES`
encoded bytes; a fresh process proves the `486`-byte positive control spills under the governed
root and a root beyond the widest random suffix fails inside SQLite; a multibyte path is measured
as SQLite measures it; a symlink is measured by the spelling SQLite opens.

**C20-MINOR-2 -- environment closure over the finite route taxonomy (C2106-C2108).** Path
expansion, ``pathlib``, ``tempfile``, ``getpass``, ``shutil.which``, ``ctypes``, reflective and
dynamic import, and environment-printing subprocesses are all seen; the accepted reads and the
accepted local names are not false positives; the prose claims exactly the finite property.

**C20-MINOR-3 -- exact per-module capability allowlists (C2109-C2112).** A fixed absolute path is
never sufficient: every audited module is held to its exact program-and-argv launches and its exact
write-open sites, and the destructive API set -- removal programs, shells, network clients,
``asyncio``/``multiprocessing``/``pty`` process routes, truncation, write-mode ``open``,
``Path.write_*``, ``rename``/``replace``, ``chmod`` -- is detected wherever it is not allowlisted.

**C20-MINOR-4 -- full seal versus restart compatibility (C2113-C2119).** All eight binding fields
still move the sealed ``storage_plan_identity`` and an edited attachment field refuses without
resealing; restart compatibility is a distinct in-memory comparison that omits exactly the three
attach-time identifiers; a remount restart continues while a changed stable field refuses; every
child is handed the parent's CURRENT full binding and compares all eight. **C2120-C2122** re-state
the standing multipass invariants on the C21 tree.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c19_corrections as c19  # noqa: E402

from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3.chunk_evidence import write_once_json  # noqa: E402

LIMIT = ewr.SQLITE_TEMP_ROOT_MAX_ENCODED_BYTES
TOO_LONG = "encoded bytes long"
#: One byte beyond the widest random suffix SQLite can append: fails in every fresh process.
CERTAINLY_TOO_LONG = LIMIT + 16
ADMITTED_ON = c19.ADMITTED_ON
ADMITTED_ON_TAIL = c19.ADMITTED_ON_TAIL
RECORDED = "storage plan already recorded"
OTHER_VOLUME = c19.OTHER_VOLUME
AUDITED = c13i.AUDITED_MODULES


@pytest.fixture(autouse=True)
def _pinned(tmp_path: Path) -> Any:
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


def _open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    c13.open_synthetic_multipass(monkeypatch, temp_root=tmp_path / "sqlite-temp")
    monkeypatch.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))


def _audited_source(name: str) -> str:
    path = c13i.module_path(name)
    assert path is not None, name
    return path.read_text(encoding="utf-8")


# ==========================================================================
# C2101-C2105: the encoded-byte usability boundary -- C20-MINOR-1
# ==========================================================================
def _root_of_encoded_bytes(base: Path, total: int, *, filler: str = "a") -> Path:
    """A directory beneath ``base`` whose RAW spelling is exactly ``total`` encoded bytes.

    Components stay under ``NAME_MAX``; only the last one uses ``filler``, so a multibyte filler
    yields a path with fewer characters than bytes.
    """
    remaining = total - len(os.fsencode(str(base)))
    assert remaining >= 2, (base, total)
    unit = len(filler.encode("utf-8"))
    parts: list[str] = []
    while remaining > 201:
        parts.append("a" * 200)
        remaining -= 201
    take = remaining - 1
    parts.append(filler * (take // unit) + "a" * (take % unit))
    path = base.joinpath(*parts)
    path.mkdir(parents=True)
    assert len(os.fsencode(str(path))) == total, (len(os.fsencode(str(path))), total)
    return path


def _verdicts(
    work: Path, archive: Path, provider: Callable[[Path], ewr.VolumeIdentity]
) -> dict[str, str]:
    """Both guards on the CURRENT process environment: ``ADMITTED``, ``too-long``, or the text."""
    verdicts: dict[str, str] = {}
    try:
        ct.require_sqlite_temp_binding(charged_path=work / "world", provider=provider)
        verdicts["multipass"] = "ADMITTED"
    except ct.ChunkTieringError as exc:
        verdicts["multipass"] = "too-long" if TOO_LONG in str(exc) else str(exc)
    try:
        ewr.require_external_sqlite_tmpdir(
            working_root=work,
            archive=archive,
            expected_uuid=c13.SYNTHETIC_MERGE_VOLUME,
            provider=provider,
        )
        verdicts["d137_r8"] = "ADMITTED"
    except ewr.ExternalWorkingRootError as exc:
        verdicts["d137_r8"] = "too-long" if TOO_LONG in str(exc) else str(exc)
    return verdicts


#: The accepted C19 spill probe, reporting a SQLite failure instead of dying on it.
_SPILL_OUTCOME_PROBE = textwrap.dedent(
    """
    import os, sqlite3, sys, fcntl
    governed = os.path.realpath(sys.argv[1])
    try:
        db = sqlite3.connect(sys.argv[2], isolation_level=None)
        db.execute("PRAGMA cache_size = -200")
        db.execute(
            "CREATE TEMP TABLE big AS WITH RECURSIVE s(i) AS (SELECT 1 UNION ALL SELECT i+1 "
            "FROM s WHERE i < 3000) SELECT i, randomblob(1500) AS b FROM s"
        )
        db.execute("SELECT COUNT(*) FROM (SELECT b FROM temp.big ORDER BY b)").fetchone()
    except sqlite3.Error as exc:
        print("ERROR:" + type(exc).__name__ + ":" + str(exc))
        raise SystemExit(0)
    opened = []
    for fd in os.listdir("/dev/fd"):
        try:
            raw = fcntl.fcntl(int(fd), fcntl.F_GETPATH, bytes(1024))
            opened.append(raw.rstrip(b"\\0").decode())
        except OSError:
            pass
    spills = [p for p in opened if "etilqs" in p]
    parents = {os.path.realpath(os.path.dirname(p)) for p in spills}
    print("UNDER_GOVERNED" if spills and parents == {governed} else "ELSEWHERE:" + ";".join(spills))
    """
)


def _spill_outcome(temp_value: str, database: Path) -> str:
    completed = subprocess.run(
        [sys.executable, "-c", _SPILL_OUTCOME_PROBE, temp_value, str(database)],
        env={**os.environ, ewr.SQLITE_TMPDIR_ENV: temp_value},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-1500:]
    return completed.stdout.strip()


@pytest.mark.skipif(sys.platform != "darwin", reason="the fd-path probe is macOS-only")
def test_c2101_the_limit_is_486_encoded_bytes_and_sqlite_really_spills_beneath_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert LIMIT == 486
    assert "SQLITE_TEMP_ROOT_MAX_ENCODED_BYTES" in ewr.__all__
    _volume_, work, _temp, archive = c19._volume(tmp_path)
    provider = c13.synthetic_volume_provider()
    root = _root_of_encoded_bytes(tmp_path / "long", LIMIT)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(root))
    assert _verdicts(work, archive, provider) == {"multipass": "ADMITTED", "d137_r8": "ADMITTED"}
    binding = ct.require_sqlite_temp_binding(charged_path=work / "world", provider=provider)
    assert (binding.temp_root_device, binding.temp_root_inode) == (
        root.stat().st_dev,
        root.stat().st_ino,
    )
    # The positive control: a fresh process, a real spill, the open temporary file's directory
    # is the 486-byte governed root.
    assert _spill_outcome(str(root), tmp_path / "probe.sqlite3") == "UNDER_GOVERNED"


def test_c2102_one_byte_over_refuses_at_both_guards_before_governed_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volume, work, _temp, archive = c19._volume(tmp_path)
    provider = c13.synthetic_volume_provider()
    root = _root_of_encoded_bytes(tmp_path / "long", LIMIT + 1)
    assert root.is_dir() and os.access(root, os.W_OK | os.X_OK)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(root))
    before = sorted(p.name for p in volume.rglob("*"))
    assert _verdicts(work, archive, provider) == {"multipass": "too-long", "d137_r8": "too-long"}
    assert sorted(p.name for p in volume.rglob("*")) == before
    with pytest.raises(ewr.ExternalWorkingRootError, match=TOO_LONG) as refusal:
        ewr.require_usable_sqlite_temp_root(str(root))
    message = str(refusal.value)
    assert f"{LIMIT + 1} encoded bytes" in message and f"{LIMIT}-byte limit" in message
    assert "never characters" in message
    assert str(root) not in message and str(tmp_path) not in message  # path-free
    with pytest.raises(ct.ChunkTieringError, match="A merge world is NOT created"):
        ct.require_sqlite_temp_binding(charged_path=work / "world", provider=provider)
    # Every other C19 condition still holds in the same validator, unchanged.
    for shorter in (LIMIT - 1, LIMIT - 100):
        assert ewr.require_usable_sqlite_temp_root(
            str(_root_of_encoded_bytes(tmp_path / f"ok{shorter}", shorter))
        ).is_dir()
    with pytest.raises(ewr.ExternalWorkingRootError, match="leading or trailing whitespace"):
        ewr.require_usable_sqlite_temp_root(str(root) + " ")


@pytest.mark.skipif(sys.platform != "darwin", reason="the fd-path probe is macOS-only")
def test_c2102_beyond_the_widest_suffix_sqlite_itself_fails_inside_the_statement(
    tmp_path: Path,
) -> None:
    """The mechanism the guard closes, shown in SQLite: a root the guard refuses is a root under
    which the first spilling statement fails mid-transaction. Measured on the governed build,
    `487` bytes failed in `76` of `76` fresh processes; the committed control uses a length
    beyond the widest random ``etilqs_`` suffix, where the failure is certain rather than
    overwhelmingly likely."""
    root = _root_of_encoded_bytes(tmp_path / "long", CERTAINLY_TOO_LONG)
    with pytest.raises(ewr.ExternalWorkingRootError, match=TOO_LONG):
        ewr.require_usable_sqlite_temp_root(str(root))
    outcome = _spill_outcome(str(root), tmp_path / "probe.sqlite3")
    assert outcome.startswith("ERROR:OperationalError"), outcome


@pytest.mark.skipif(sys.platform != "darwin", reason="the fd-path probe is macOS-only")
def test_c2103_a_multibyte_root_is_measured_in_encoded_bytes_never_characters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _volume_, work, _temp, archive = c19._volume(tmp_path)
    provider = c13.synthetic_volume_provider()
    over = _root_of_encoded_bytes(tmp_path / "mb-over", LIMIT + 1, filler="\u00e9")
    assert len(str(over)) < LIMIT < len(os.fsencode(str(over)))  # the character count passes
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(over))
    assert _verdicts(work, archive, provider) == {"multipass": "too-long", "d137_r8": "too-long"}
    with pytest.raises(ewr.ExternalWorkingRootError, match=f"{LIMIT + 1} encoded bytes"):
        ewr.require_usable_sqlite_temp_root(str(over))
    # At the limit, a multibyte root admits and SQLite spills beneath it.
    at = _root_of_encoded_bytes(tmp_path / "mb-at", LIMIT, filler="\u00e9")
    assert len(str(at)) < len(os.fsencode(str(at))) == LIMIT
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(at))
    assert _verdicts(work, archive, provider) == {"multipass": "ADMITTED", "d137_r8": "ADMITTED"}
    assert _spill_outcome(str(at), tmp_path / "probe.sqlite3") == "UNDER_GOVERNED"


@pytest.mark.skipif(sys.platform != "darwin", reason="the fd-path probe is macOS-only")
def test_c2104_a_symlink_is_measured_by_the_spelling_sqlite_opens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _volume_, work, _temp, archive = c19._volume(tmp_path)
    provider = c13.synthetic_volume_provider()
    # (a) a short spelling of a long real directory: SQLite opens the short spelling, the kernel
    # resolves it, and the spill lands under the long real root -- admitted.
    long_real = _root_of_encoded_bytes(tmp_path / "real", CERTAINLY_TOO_LONG)
    short = tmp_path / "s"
    short.symlink_to(long_real)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(short))
    assert _verdicts(work, archive, provider) == {"multipass": "ADMITTED", "d137_r8": "ADMITTED"}
    assert _spill_outcome(str(short), tmp_path / "probe.sqlite3") == "UNDER_GOVERNED"
    # (b) a long spelling of a short real directory: the spelling is what SQLite composes the
    # temporary name from, so it refuses -- a validator measuring the resolved path would not.
    real_short = tmp_path / "short-real"
    real_short.mkdir()
    parent = _root_of_encoded_bytes(tmp_path / "link-parent", LIMIT + 1 - 1 - 20)
    link = parent / ("l" * 20)
    link.symlink_to(real_short)
    assert len(os.fsencode(str(link))) == LIMIT + 1
    assert len(os.fsencode(os.path.realpath(link))) < LIMIT
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(link))
    assert _verdicts(work, archive, provider) == {"multipass": "too-long", "d137_r8": "too-long"}


def test_c2105_one_shared_validator_counts_fsencode_bytes_and_claims_no_universality() -> None:
    source = Path(ewr.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    validator = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "require_usable_sqlite_temp_root"
    )
    fsencode_calls = [
        node
        for node in ast.walk(validator)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "fsencode"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
    ]
    assert len(fsencode_calls) == 1
    compared = [
        node
        for node in ast.walk(validator)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(c, ast.Name) and c.id == "SQLITE_TEMP_ROOT_MAX_ENCODED_BYTES"
            for c in node.comparators
        )
    ]
    assert len(compared) == 1
    # Both guards reach the ONE validator (C19-R2), and no guard carries its own length rule.
    for guard in ("require_external_sqlite_tmpdir", "require_sqlite_temp_binding"):
        module = ewr if guard == "require_external_sqlite_tmpdir" else ct
        body = inspect.getsource(getattr(module, guard))
        assert "require_usable_sqlite_temp_root(" in body
        assert "fsencode" not in body and "SQLITE_TEMP_ROOT_MAX_ENCODED_BYTES" not in body
    # The limit is stated as the current governed VFS's, measured, and not as universal.
    assert "It is not claimed for every SQLite VFS" in source
    assert "Measured on the governed build" in source
    assert c13i.committed_literal(ewr, "SQLITE_TEMP_ROOT_MAX_ENCODED_BYTES") == 486


# ==========================================================================
# C2106-C2108: the finite environment route taxonomy -- C20-MINOR-2
# ==========================================================================
_ENVIRONMENT_ROUTES: dict[str, str] = {
    "os.path.expandvars (C20 survivor)": 'import os\n_P = os.path.expandvars("$SQLITE_TMPDIR")\n',
    "os.path.expanduser": 'import os\n_P = os.path.expanduser("~/x")\n',
    "from os.path import expandvars as e": (
        'from os.path import expandvars as _e\n_P = _e("$SQLITE_TMPDIR")\n'
    ),
    "from os import path; path.expanduser": 'from os import path\n_P = path.expanduser("~")\n',
    "import os as o; o.path.expandvars": 'import os as _o\n_P = _o.path.expandvars("$X")\n',
    "posixpath.expandvars": 'import posixpath\n_P = posixpath.expandvars("$X")\n',
    "Path.home": "from pathlib import Path\n_P = Path.home()\n",
    "pathlib.Path.home": "import pathlib\n_P = pathlib.Path.home()\n",
    "from pathlib import Path as P; P.home": "from pathlib import Path as _Q\n_P = _Q.home()\n",
    "Path(...).expanduser()": 'from pathlib import Path\n_P = Path("~").expanduser()\n',
    "PurePosixPath.home": "from pathlib import PurePosixPath\n_P = PurePosixPath.home()\n",
    "tempfile.gettempdir": "import tempfile\n_P = tempfile.gettempdir()\n",
    "tempfile.gettempdirb": "import tempfile\n_P = tempfile.gettempdirb()\n",
    "from tempfile import mkdtemp": "from tempfile import mkdtemp\n_P = mkdtemp()\n",
    "tempfile.TemporaryDirectory": "import tempfile as _t\n_P = _t.TemporaryDirectory()\n",
    "getpass.getuser": "import getpass\n_P = getpass.getuser()\n",
    "from getpass import getuser as u": "from getpass import getuser as _u\n_P = _u()\n",
    "shutil.which": 'import shutil\n_P = shutil.which("ls")\n',
    "from shutil import which": 'from shutil import which\n_P = which("ls")\n',
    "import ctypes": 'import ctypes\n_P = ctypes.CDLL(None).getenv(b"SQLITE_TMPDIR")\n',
    "from ctypes import CDLL": "from ctypes import CDLL\n_P = CDLL(None)\n",
    "sys.modules subscript": 'import sys\n_P = sys.modules["os"].environ\n',
    "getattr on tempfile": 'import tempfile\n_P = getattr(tempfile, "gettempdir")()\n',
    "vars on os": "import os\n_P = vars(os)\n",
    "importlib.import_module": 'import importlib\n_P = importlib.import_module("os").environ\n',
    "__import__": '_P = __import__("os").environ\n',
    "subprocess env=": (
        'import subprocess\n_P = subprocess.run(["/bin/ls"], env={"A": "b"}, check=False)\n'
    ),
    "subprocess printenv": (
        "import subprocess\n"
        '_P = subprocess.run(["/usr/bin/printenv", "SQLITE_TMPDIR"], check=False)\n'
    ),
    "from subprocess import run; env program": (
        'from subprocess import run as _r\n_P = _r(["/usr/bin/env"], check=False)\n'
    ),
    "posix.environ": "import posix\n_P = posix.environ\n",
    "from os import environ as e; e[...]": 'from os import environ as _e\n_P = _e["X"]\n',
    "os.getenv": 'import os\n_P = os.getenv("X")\n',
}


@pytest.mark.parametrize(("label", "probe"), sorted(_ENVIRONMENT_ROUTES.items()))
def test_c2106_every_route_in_the_taxonomy_is_caught_in_every_audited_module(
    label: str, probe: str
) -> None:
    for name in AUDITED:
        source = _audited_source(name)
        violations = c13i.environment_closure_violations(name, source + "\n" + probe)
        assert violations, (label, name)
        assert all(line > 0 for line, _ in violations), (label, name, violations)


def test_c2107_the_accepted_reads_and_accepted_local_names_are_not_false_positives() -> None:
    tiering = _audited_source("disclosure_drift.m3.chunk_tiering")
    working_root = _audited_source("disclosure_drift.m3.external_working_root")
    multipass = _audited_source("disclosure_drift.m3.chunk_multipass")
    assert [item[1] for item in c13i.environment_accesses(tiering)] == ["os.environ"]
    assert [item[1] for item in c13i.environment_accesses(working_root)] == ["os.environ"]
    assert c13i.environment_accesses(multipass) == []
    assert (
        len(
            c13i.permitted_sqlite_tmpdir_reads(
                working_root, function="require_external_sqlite_tmpdir"
            )
        )
        == 1
    )
    for name in AUDITED:
        assert c13i.environment_closure_violations(name, _audited_source(name)) == [], name
    # Accepted shapes that a spelling-only scan would flag: a parameter named `environ`, a local
    # named `getenv`, a mapping key, a string, `str.replace`, and an attribute that is not a call.
    controls = textwrap.dedent(
        """
        def _accepted(environ, mapping, text):
            getenv = mapping.get("environ")
            home = text.replace("+00:00", "Z")
            expanduser = "os.path.expanduser"
            return environ, getenv, home, expanduser, mapping.home
        """
    )
    assert (
        c13i.environment_closure_violations("disclosure_drift.m3.chunk_tiering", tiering + controls)
        == []
    )
    # A default on the one permitted read is still not the permitted read.
    defaulted = tiering.replace(
        "os.environ.get(SQLITE_TMPDIR_ENV)", 'os.environ.get(SQLITE_TMPDIR_ENV, "/tmp")'
    )
    assert defaulted != tiering
    assert c13i.environment_closure_violations("disclosure_drift.m3.chunk_tiering", defaulted)
    # The taxonomy names every route the owner listed.
    taxonomy = "\n".join(c13i.ENVIRONMENT_ROUTE_TAXONOMY)
    for needle in (
        "os.environ",
        "os.environb",
        "os.getenv",
        "expandvars",
        "expanduser",
        "Path.home",
        "gettempdir",
        "gettempdirb",
        "getuser",
        "which",
        "ctypes",
        "sys.modules",
        "getattr",
        "importlib",
        "__import__",
        "printenv",
        "env=",
    ):
        assert needle in taxonomy, needle
    assert c13i.PERMITTED_SQLITE_TMPDIR_READS == {
        "chunk_tiering": "require_sqlite_temp_binding",
        "external_working_root": "require_external_sqlite_tmpdir",
    }


def test_c2108_the_prose_and_the_test_names_claim_the_finite_property() -> None:
    multipass_doc = cm.__doc__ or ""
    assert "THIS module reads no environment at all" in multipass_doc
    assert "finite" in multipass_doc and "D151-C21 R2" in multipass_doc
    assert "exists anywhere on this path" not in multipass_doc
    assert "finite, enumerated route taxonomy" in multipass_doc
    assert "conceivable side channel" in multipass_doc
    instrument_doc = c13i.__doc__ or ""
    assert "finite route taxonomy" in instrument_doc and "D151-C21 R2" in instrument_doc
    assert hasattr(
        c13i, "test_z02_no_environment_derived_configuration_capability_beyond_the_accepted_reads"
    )
    assert not hasattr(c13i, "test_z02_no_environment_configuration_or_command_line_route")
    closure_doc = inspect.getdoc(c13i.environment_closure_violations) or ""
    assert "finite property is the claim" in closure_doc


# ==========================================================================
# C2109-C2112: exact per-module capability allowlists -- C20-MINOR-3
# ==========================================================================
_UNIVERSAL_ROUTES: dict[str, str] = {
    "/bin/rm fixed argv (C20 survivor)": (
        "import subprocess\n\n\ndef _p(x):\n"
        '    subprocess.run(["/bin/rm", "-rf", str(x)], check=True)\n'
    ),
    "/bin/sh -c fixed argv": (
        'import subprocess\n\n\ndef _p(x):\n    subprocess.run(["/bin/sh", "-c", str(x)])\n'
    ),
    "/bin/zsh fixed argv": 'import subprocess\n\n\ndef _p(x):\n    subprocess.run(["/bin/zsh"])\n',
    "/usr/bin/curl fixed argv": (
        'import subprocess\n\n\ndef _p(x):\n    subprocess.run(["/usr/bin/curl", str(x)])\n'
    ),
    "/usr/bin/env fixed argv": (
        'import subprocess\n\n\ndef _p(x):\n    subprocess.run(["/usr/bin/env"])\n'
    ),
    "/usr/bin/python3 fixed argv": (
        'import subprocess\n\n\ndef _p(x):\n    subprocess.run(["/usr/bin/python3", "-c", "1"])\n'
    ),
    "shell=True": (
        'import subprocess\n\n\ndef _p(x):\n    subprocess.run(["/bin/ls"], shell=True)\n'
    ),
    "from subprocess import Popen as P": (
        'from subprocess import Popen as _P\n\n\ndef _p(x):\n    _P(["/bin/rm", str(x)])\n'
    ),
    "open write mode": '\n\ndef _p(x):\n    with open(x, "w") as h:\n        h.write("x")\n',
    "open append mode kw": '\n\ndef _p(x):\n    return open(x, mode="ab")\n',
    "open exclusive mode": '\n\ndef _p(x):\n    return open(x, "x")\n',
    "open update mode": '\n\ndef _p(x):\n    return open(x, "r+")\n',
    "open non-constant mode": "\n\ndef _p(x, m):\n    return open(x, m)\n",
    "Path.write_text": '\n\ndef _p(x):\n    x.write_text("")\n',
    "Path.write_bytes": '\n\ndef _p(x):\n    x.write_bytes(b"")\n',
    "os.truncate": "import os\n\n\ndef _p(x):\n    os.truncate(x, 0)\n",
    ".truncate()": "\n\ndef _p(x):\n    x.truncate(0)\n",
    "Path.replace": "\n\ndef _p(x, y):\n    x.replace(y)\n",
    "Path.rename": "\n\ndef _p(x, y):\n    x.rename(y)\n",
    "os.rename": "import os\n\n\ndef _p(x, y):\n    os.rename(x, y)\n",
    "os.replace": "import os\n\n\ndef _p(x, y):\n    os.replace(x, y)\n",
    "os.chmod": "import os\n\n\ndef _p(x):\n    os.chmod(x, 0)\n",
    "Path.chmod": "\n\ndef _p(x):\n    x.chmod(0o600)\n",
    "os.chown": "import os\n\n\ndef _p(x):\n    os.chown(x, 0, 0)\n",
    "os.symlink": "import os\n\n\ndef _p(x, y):\n    os.symlink(x, y)\n",
    "asyncio.create_subprocess_exec": (
        "import asyncio\n\n\nasync def _p(x):\n"
        '    await asyncio.create_subprocess_exec("/bin/ls", str(x))\n'
    ),
    "from asyncio import create_subprocess_shell": (
        "from asyncio import create_subprocess_shell\n"
    ),
    "loop.subprocess_exec": "\n\nasync def _p(loop, x):\n    await loop.subprocess_exec(x)\n",
    "import multiprocessing": (
        "import multiprocessing\n\n\ndef _p(x):\n    multiprocessing.Process(target=x).start()\n"
    ),
    "ProcessPoolExecutor": "from concurrent.futures import ProcessPoolExecutor\n",
    "os.posix_spawn": ("import os\n\n\ndef _p(x):\n    os.posix_spawn(x, [x], {})\n"),
    "import pty": "import pty\n",
    "shutil.rmtree": "import shutil\n\n\ndef _p(x):\n    shutil.rmtree(x)\n",
    "caller-controlled argv": "import subprocess\n\n\ndef _p(x):\n    subprocess.run(x)\n",
}


@pytest.mark.parametrize(("label", "probe"), sorted(_UNIVERSAL_ROUTES.items()))
def test_c2109_every_destructive_route_is_detected_in_every_audited_module(
    label: str, probe: str
) -> None:
    for name in AUDITED:
        source = _audited_source(name)
        assert c13i.capability_violations(source + "\n" + probe), (label, name)
        assert c13i.capability_violations(source + "\n" + probe, module=name), (label, name)


_PER_MODULE_ROUTES: dict[str, tuple[str, str]] = {
    "a new os.open write site": (
        "disclosure_drift.m3.chunk_tiering",
        "\n\ndef _p(x):\n    return os.open(x, os.O_WRONLY | os.O_CREAT, 0o600)\n",
    ),
    "a third os.open write site in canary_runtime": (
        "disclosure_drift.m3.canary_runtime",
        "\n\ndef _p(x):\n    return os.open(x, os.O_CREAT | os.O_RDWR, 0o600)\n",
    ),
    "an allowed program with a different argv": (
        "disclosure_drift.m3.external_working_root",
        '\n\ndef _p(x):\n    subprocess.run(["/usr/sbin/diskutil", "eraseVolume", str(x)])\n',
    ),
    "an allowed program with a shorter argv": (
        "disclosure_drift.m3.canary_runtime",
        '\n\ndef _p(x):\n    subprocess.run(["/usr/bin/pmset", "-g"])\n',
    ),
    "any subprocess in chunk_tiering": (
        "disclosure_drift.m3.chunk_tiering",
        '\nimport subprocess\n\n\ndef _p(x):\n    subprocess.run(["/usr/sbin/diskutil", "list"])\n',
    ),
    "subprocess merely imported by chunk_tiering": (
        "disclosure_drift.m3.chunk_tiering",
        "\nimport subprocess\n",
    ),
    "a second child launch shape in chunk_multipass": (
        "disclosure_drift.m3.chunk_multipass",
        '\n\ndef _p(x):\n    subprocess.run([sys.executable, "-m", "disclosure_drift", str(x)])\n',
    ),
}


@pytest.mark.parametrize(("label", "route"), sorted(_PER_MODULE_ROUTES.items()))
def test_c2110_a_fixed_absolute_path_alone_never_establishes_safety(
    label: str, route: tuple[str, str]
) -> None:
    name, probe = route
    source = _audited_source(name)
    assert c13i.capability_violations(source, module=name) == [], name
    assert c13i.capability_violations(source + probe, module=name), (label, name)


def test_c2111_the_committed_child_launch_is_pinned_exactly() -> None:
    source = _audited_source("disclosure_drift.m3.chunk_multipass")
    expected = (
        "<sys.executable>",
        ("-c", c13i.MULTIPASS_CHILD_BOOTSTRAP, "str(request_path)"),
    )
    assert c13i.subprocess_launches(source) == [expected]
    assert c13i.committed_literal(cm, "_CHILD_BOOTSTRAP") == c13i.MULTIPASS_CHILD_BOOTSTRAP
    assert c13i.MULTIPASS_CHILD_BOOTSTRAP == (
        "import sys;from disclosure_drift.m3.chunk_multipass import _child_main;"
        "sys.exit(_child_main(sys.argv[1]))"
    )
    launch = '[sys.executable, "-c", _CHILD_BOOTSTRAP, str(request_path)]'
    assert source.count(launch) == 1
    for mutated_launch in (
        '[sys.executable, "-m", "disclosure_drift.m3.chunk_multipass", str(request_path)]',
        '["/usr/bin/python3", "-c", _CHILD_BOOTSTRAP, str(request_path)]',
        '[sys.executable, "-c", _CHILD_BOOTSTRAP, str(request_path), "--force"]',
        '[sys.executable, "-c", _CHILD_BOOTSTRAP, request_path.as_posix()]',
    ):
        mutated = source.replace(launch, mutated_launch)
        assert c13i.capability_violations(mutated, module="disclosure_drift.m3.chunk_multipass")
    # A changed bootstrap TEXT is a changed launch: the allowlist renders the constant's value.
    changed_bootstrap = source.replace(
        '"sys.exit(_child_main(sys.argv[1]))"', '"import os;sys.exit(_child_main(sys.argv[1]))"'
    )
    assert changed_bootstrap != source
    assert c13i.capability_violations(
        changed_bootstrap, module="disclosure_drift.m3.chunk_multipass"
    )


def test_c2112_the_accepted_allowlists_are_exact_and_the_chain_keeps_its_read_only_argv() -> None:
    assert set(c13i.ACCEPTED_SUBPROCESS_LAUNCHES) == set(AUDITED)
    assert set(c13i.ACCEPTED_WRITE_OPENS) <= set(AUDITED)
    for name in AUDITED:
        source = _audited_source(name)
        assert c13i.capability_violations(source, module=name) == [], name
        assert c13i.capability_violations(source) == [], name
        assert c13i.subprocess_launches(source) == list(c13i.ACCEPTED_SUBPROCESS_LAUNCHES[name])
    assert c13i.ACCEPTED_SUBPROCESS_LAUNCHES["disclosure_drift.m3.chunk_tiering"] == ()
    assert "subprocess" not in c13i.package_imports(
        _audited_source("disclosure_drift.m3.chunk_tiering")
    )
    assert "import subprocess" not in _audited_source("disclosure_drift.m3.chunk_tiering")
    # The chain's accepted programs are unchanged from C19, and every accepted argv is bounded.
    assert c13i.subprocess_programs(
        _audited_source("disclosure_drift.m3.external_working_root")
    ) == {"/usr/sbin/diskutil"}
    assert c13i.subprocess_programs(_audited_source("disclosure_drift.m3.canary_runtime")) == {
        "/bin/ps",
        "/usr/bin/pmset",
        "/usr/sbin/ioreg",
    }
    assert c13i.subprocess_programs(_audited_source("disclosure_drift.m3.dock_transport")) == {
        "/usr/sbin/ioreg"
    }
    for launches in c13i.ACCEPTED_SUBPROCESS_LAUNCHES.values():
        for program, argv in launches:
            assert program == "<sys.executable>" or program.startswith("/")
            assert program.rsplit("/", 1)[-1] not in c13i.FORBIDDEN_PROGRAM_NAMES
            assert all(item == "<sys.executable>" or "<" not in item for item in argv), argv
    # The two accepted write sites are the D140 lock file and pid record, and nothing else.
    assert c13i.ACCEPTED_WRITE_OPENS == {
        "disclosure_drift.m3.canary_runtime": (
            ("O_CREAT", "O_RDWR"),
            ("O_CREAT", "O_TRUNC", "O_WRONLY"),
        )
    }


# ==========================================================================
# C2113-C2119: full seal versus restart compatibility -- C20-MINOR-4
# ==========================================================================
STABLE = ct.SQLITE_TEMP_BINDING_STABLE_FIELDS
ATTACHMENT = ct.SQLITE_TEMP_BINDING_ATTACHMENT_FIELDS


def _reseal(document: dict[str, Any]) -> dict[str, Any]:
    """A document whose identity is recomputed over its (edited) fields."""
    body = {k: v for k, v in document.items() if k != ct.STORAGE_PLAN_IDENTITY_KEY}
    document[ct.STORAGE_PLAN_IDENTITY_KEY] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return document


def _changed(field: str) -> dict[str, Any]:
    """One binding field moved -- both volume UUIDs together, as the constructor requires."""
    if field.endswith("volume_uuid"):
        return {"temp_volume_uuid": OTHER_VOLUME, "charged_volume_uuid": OTHER_VOLUME}
    if field == "temp_root_device":
        return {field: 7}
    if field == "temp_root_inode":
        return {field: 99}
    return {field: "moved"}


def test_c2113_the_eight_fields_partition_into_five_stable_and_three_attachment() -> None:
    assert set(STABLE) | set(ATTACHMENT) == set(ct.SQLITE_TEMP_BINDING_FIELDS)
    assert not set(STABLE) & set(ATTACHMENT)
    assert STABLE == (
        "temp_root_inode",
        "temp_volume_uuid",
        "temp_filesystem_type",
        "charged_volume_uuid",
        "charged_filesystem_type",
    )
    assert ATTACHMENT == ("temp_root_device", "temp_device_identifier", "charged_device_identifier")
    binding = c19._binding()
    assert tuple(binding.stable_record()) == STABLE
    assert tuple(binding.as_record()) == ct.SQLITE_TEMP_BINDING_FIELDS
    plan = c19._plan(binding)
    compatibility = plan.restart_compatibility()
    assert set(compatibility) == set(plan.as_record())
    assert compatibility["sqlite_temp_binding"] == dict(binding.stable_record())
    for field in ATTACHMENT:
        assert field not in compatibility["sqlite_temp_binding"]
    # Not serialized: the document is exactly the record plus its one identity, as in C19.
    document = plan.as_document()
    assert set(document) == set(plan.as_record()) | {ct.STORAGE_PLAN_IDENTITY_KEY}
    assert not [key for key in document if "compat" in key or "restart" in key or "stable" in key]
    assert set(document["sqlite_temp_binding"]) == set(ct.SQLITE_TEMP_BINDING_FIELDS)  # type: ignore[arg-type]


def test_c2114_every_field_moves_the_seal_and_only_stable_fields_move_compatibility() -> None:
    base = c19._plan(c19._binding())
    for field in ct.SQLITE_TEMP_BINDING_FIELDS:
        moved = c19._plan(c19._binding(**_changed(field)))
        assert moved.identity() != base.identity(), field
        if field in STABLE:
            assert moved.restart_compatibility() != base.restart_compatibility(), field
        else:
            assert moved.restart_compatibility() == base.restart_compatibility(), field
    # A non-binding term moves both.
    terms = c19._plan(c19._binding(), level_two_transient_bytes=4097)
    assert terms.identity() != base.identity()
    assert terms.restart_compatibility() != base.restart_compatibility()
    # C2115 (M12): an attachment field edited WITHOUT resealing refuses at the seal; resealed, it
    # reads back, and the rebuilt plan is restart-compatible with the original.
    document = json.loads(json.dumps(dict(base.as_document())))
    for field in ATTACHMENT:
        edited = copy.deepcopy(document)
        edited["sqlite_temp_binding"].update(_changed(field))
        with pytest.raises(ct.ChunkTieringError, match=c19.STALE):
            ct.MultipassStoragePlan.from_document(edited)
        resealed = ct.MultipassStoragePlan.from_document(_reseal(copy.deepcopy(edited)))
        assert resealed.identity() != base.identity()
        assert resealed.restart_compatibility() == base.restart_compatibility()
    for field in STABLE:
        edited = copy.deepcopy(document)
        edited["sqlite_temp_binding"].update(_changed(field))
        with pytest.raises(ct.ChunkTieringError, match=c19.STALE):
            ct.MultipassStoragePlan.from_document(edited)
        resealed = ct.MultipassStoragePlan.from_document(_reseal(copy.deepcopy(edited)))
        assert resealed.restart_compatibility() != base.restart_compatibility()


def test_c2116_the_recorded_plan_is_verified_whole_then_compared_by_compatibility(
    tmp_path: Path,
) -> None:
    base = c19._plan(c19._binding())
    path = tmp_path / cm.STORAGE_PLAN_FILENAME
    cm._record_storage_plan(path, base)
    before = path.read_bytes()
    # (a) the same stable identity under new attach-time identifiers CONTINUES, and the document
    # is not rewritten.
    remounted = c19._plan(
        c19._binding(
            temp_root_device=7,
            temp_device_identifier="disk9s1",
            charged_device_identifier="disk9s1",
        )
    )
    assert remounted.identity() != base.identity()
    cm._record_storage_plan(path, remounted)
    assert path.read_bytes() == before
    # (b) any stable field changed REFUSES, naming the binding, before anything is written.
    for field in STABLE:
        with pytest.raises(cm.ChunkMultipassError, match=RECORDED) as refusal:
            cm._record_storage_plan(path, c19._plan(c19._binding(**_changed(field))))
        assert "restart compatibility" in str(refusal.value) and "sqlite_temp_binding" in str(
            refusal.value
        )
        assert "not what decides" in str(refusal.value)
        assert path.read_bytes() == before
    # (c) a changed term or input refuses too.
    with pytest.raises(cm.ChunkMultipassError, match="'requirements'"):
        cm._record_storage_plan(path, c19._plan(c19._binding(), level_one_transient_bytes=8))
    with pytest.raises(cm.ChunkMultipassError, match="'chunk_bytes_by_id'"):
        cm._record_storage_plan(
            path,
            ct.plan_multipass_storage(
                plan_digest="p",
                merge_schedule_digest="s",
                groups=[
                    ("group-0000", ["chunk-0000", "chunk-0001"]),
                    ("group-0001", ["chunk-0002"]),
                ],
                chunk_bytes_by_id={"chunk-0000": 1001, "chunk-0001": 500, "chunk-0002": 2000},
                seed_catalog_bytes=50,
                requirements=base.requirements,
                sqlite_temp_binding=base.sqlite_temp_binding,
            ),
        )
    assert path.read_bytes() == before
    # (d) the seal is verified FIRST: an attachment field edited without resealing refuses as a
    # stale record even though it would be restart-compatible; resealed, it is accepted.
    document = json.loads(before)
    edited = copy.deepcopy(document)
    edited["sqlite_temp_binding"]["temp_root_device"] = 7
    stale = tmp_path / "stale" / cm.STORAGE_PLAN_FILENAME
    stale.parent.mkdir()
    write_once_json(stale, edited)
    with pytest.raises(ct.ChunkTieringError, match=c19.STALE):
        cm._record_storage_plan(stale, base)
    resealed_path = tmp_path / "resealed" / cm.STORAGE_PLAN_FILENAME
    resealed_path.parent.mkdir()
    write_once_json(resealed_path, _reseal(copy.deepcopy(edited)))
    resealed_before = resealed_path.read_bytes()
    cm._record_storage_plan(resealed_path, base)
    assert resealed_path.read_bytes() == resealed_before
    # (e) a /1 record and an unknown contract still refuse ahead of any comparison (C21-R5).
    for contract, needle in (
        (c19.SUPERSEDED_CONTRACT, c19.SUPERSEDED),
        ("m3.3-chunked-f0-multipass-storage-plan/3", "does not write"),
    ):
        other = tmp_path / contract.rsplit("/", 1)[-1] / cm.STORAGE_PLAN_FILENAME
        other.parent.mkdir()
        relabelled = _reseal({**copy.deepcopy(document), "contract": contract})
        write_once_json(other, relabelled)
        with pytest.raises(ct.ChunkTieringError, match=needle):
            cm._record_storage_plan(other, base)


def _attachment_epoch(document: dict[str, Any]) -> dict[str, Any]:
    """The same plan as recorded by an EARLIER attachment of the same volume: every attach-time
    identifier differs, every stable field and every term is identical, and the seal is valid."""
    earlier = copy.deepcopy(document)
    binding = earlier["sqlite_temp_binding"]
    binding["temp_root_device"] = int(binding["temp_root_device"]) + 1000
    binding["temp_device_identifier"] = "disk9s1"
    binding["charged_device_identifier"] = "disk9s1"
    return _reseal(earlier)


def test_c2117_a_remount_restart_continues_on_the_current_measurement_and_a_moved_volume_refuses(  # noqa: PLR0915
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, tree = c1.build_world(tmp_path, members=9, shards=1, **c19.SHAPE)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    multipass_root = run["base"] / "orch"
    events: list[str] = []
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "run_final_merge", c13i._boom_final)
        with pytest.raises(RuntimeError, match="synthetic final interruption"):
            cm.run_multipass_f0(
                plan=plan,
                internal_root=run["chunk_root"],
                operational_catalog=database,
                multipass_root=multipass_root,
                run_id="c2117",
                observe=events.append,
            )
    groups = cm.derive_merge_schedule(plan).groups
    assert events.count("MERGE_PROCESS_START") == len(groups)
    # The recorded document is rewritten, in test code, as the SAME plan recorded by an earlier
    # attachment of the same volume: new st_dev and disk numbers, identical stable identity,
    # valid full seal.
    storage_path = multipass_root / cm.STORAGE_PLAN_FILENAME
    recorded = json.loads(storage_path.read_text(encoding="utf-8"))
    earlier = _attachment_epoch(recorded)
    storage_path.write_text(json.dumps(earlier, sort_keys=True, indent=2), encoding="utf-8")
    epoch_bytes = storage_path.read_bytes()
    assert (
        ct.MultipassStoragePlan.from_document(earlier).identity()
        == earlier["storage_plan_identity"]
    )
    current = dict(ct.require_sqlite_temp_binding(charged_path=multipass_root).as_record())
    assert current == recorded["sqlite_temp_binding"]
    assert {k for k in current if current[k] != earlier["sqlite_temp_binding"][k]} == set(
        ATTACHMENT
    )
    # The restart CONTINUES: every intermediate reused, exactly one child (the final), and that
    # child was handed the CURRENT measurement -- not the recorded attachment -- and matched it.
    events.clear()
    result = cm.run_multipass_f0(
        plan=plan,
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=multipass_root,
        run_id="c2117",
        observe=events.append,
    )
    assert events == ["MERGE_PROCESS_START", "MERGE_PROCESS_EXIT"]
    assert result.merge_pids == () and result.receipt["status"] == "complete"
    final_request = json.loads((multipass_root / "final-request.json").read_text(encoding="utf-8"))
    assert final_request["expected_sqlite_temp_binding"] == current
    assert final_request["expected_sqlite_temp_binding"] != earlier["sqlite_temp_binding"]
    assert dict(result.storage_plan.sqlite_temp_binding.as_record()) == current
    assert storage_path.read_bytes() == epoch_bytes  # the /2 bytes were not rewritten
    counters = tuple(
        int(result.receipt[name])  # type: ignore[call-overload]
        for name in (
            "first_witness_accessions_corrected",
            "first_witness_rows_staged",
            "evidence_members_corrected",
            "evidence_delta",
        )
    )
    assert counters == (3, 35, 4, 25)

    def restart_refuses(needle: str) -> str:
        events.clear()
        with pytest.raises(cm.ChunkMultipassError, match=RECORDED) as refusal:
            cm.run_multipass_f0(
                plan=plan,
                internal_root=run["chunk_root"],
                operational_catalog=database,
                multipass_root=multipass_root,
                run_id="c2117",
                observe=events.append,
            )
        assert events == []  # refused before any child process
        assert needle in str(refusal.value)
        assert storage_path.read_bytes() == epoch_bytes
        return str(refusal.value)

    # A changed volume UUID (both volumes, as the binding requires) refuses before any child.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(ewr, "macos_volume_identity", c13.synthetic_volume_provider(OTHER_VOLUME))
        restart_refuses("sqlite_temp_binding")
    # A changed filesystem type refuses.
    with pytest.MonkeyPatch.context() as patch:

        def exfat(path: Path) -> ewr.VolumeIdentity:
            return ewr.VolumeIdentity(
                volume_uuid=c13.SYNTHETIC_MERGE_VOLUME,
                mount_point=Path("/"),
                filesystem_type="exfat",
                device_identifier="disk-synthetic",
            )

        patch.setattr(ewr, "macos_volume_identity", exfat)
        restart_refuses("sqlite_temp_binding")
    # A recreated temporary-root directory (same path, new inode) refuses.
    temp_root = tmp_path / "sqlite-temp"
    aside = tmp_path / "sqlite-temp-aside"
    temp_root.rename(aside)
    temp_root.mkdir()
    try:
        assert temp_root.stat().st_ino != aside.stat().st_ino
        restart_refuses("sqlite_temp_binding")
    finally:
        temp_root.rmdir()
        aside.rename(temp_root)
    # A shifted disk number alone -- the one case C20 named -- does NOT refuse: the same volume
    # under a new device identifier is the remount the compatibility representation admits.
    with pytest.MonkeyPatch.context() as patch:

        def shifted(path: Path) -> ewr.VolumeIdentity:
            return ewr.VolumeIdentity(
                volume_uuid=c13.SYNTHETIC_MERGE_VOLUME,
                mount_point=Path("/"),
                filesystem_type="apfs",
                device_identifier="disk7s2",
            )

        patch.setattr(ewr, "macos_volume_identity", shifted)
        shifted_plan = ct.plan_multipass_storage(
            plan_digest=result.storage_plan.plan_digest,
            merge_schedule_digest=result.storage_plan.merge_schedule_digest,
            groups=[(g.group_id, g.chunk_ids) for g in groups],
            chunk_bytes_by_id=dict(result.storage_plan.chunk_bytes_by_id),
            seed_catalog_bytes=result.storage_plan.seed_catalog_bytes,
            requirements=result.storage_plan.requirements,
            sqlite_temp_binding=ct.require_sqlite_temp_binding(charged_path=multipass_root),
        )
        assert shifted_plan.sqlite_temp_binding.temp_device_identifier == "disk7s2"
        assert shifted_plan.identity() != result.storage_plan.identity()
        cm._record_storage_plan(storage_path, shifted_plan)  # admitted
        assert storage_path.read_bytes() == epoch_bytes


def test_c2118_a_child_compares_all_eight_fields_against_the_current_parent_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    measured = ct.require_sqlite_temp_binding(charged_path=tmp_path / "world")
    record = dict(measured.as_record())
    # In the comparison itself: an attachment field alone refuses (M10), a stable field refuses,
    # and only the exact current measurement agrees.
    for field in ct.SQLITE_TEMP_BINDING_FIELDS:
        with pytest.raises(cm.ChunkMultipassError, match=ADMITTED_ON):
            cm._require_expected_binding(measured, {**record, **_changed(field)}, label="x")
    assert cm._require_expected_binding(measured, record, label="x") == measured
    # Through the body and through a REAL child, an attachment-only mismatch refuses before the
    # attempt directory exists; the exact current record is admitted and the child completes.
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    schedule = cm.derive_merge_schedule(run["plan"])
    root = run["base"] / "child"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    group = schedule.groups[0]

    def request(attempt: int, expected: dict[str, object] | None) -> cm.GroupMergeRequest:
        return c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id=group.group_id,
            attempt=attempt,
            attempt_directory=root / "intermediates" / group.group_id / f"attempt-{attempt:03d}",
            database=database,
            expected_binding=expected,
        )

    attachment_only = {**record, "charged_device_identifier": "disk9s1"}
    with pytest.raises(cm.ChunkMultipassError, match=ADMITTED_ON):
        cm.merge_group_body(request(0, attachment_only))
    assert not (root / "intermediates").exists()
    with pytest.raises(cm.ChunkMultipassError, match="NOT complete") as refusal:
        cm.run_group_merge(
            request(1, {**record, "temp_root_device": record["temp_root_device"] + 1})
        )  # type: ignore[operator]
    assert ADMITTED_ON_TAIL in str(refusal.value)
    assert not (root / "intermediates" / group.group_id / "attempt-001").exists()
    receipt = cm.run_group_merge(request(2, None))
    assert receipt.status == "complete" and receipt.attempt == 2
    # The FINAL body compares all eight fields too, before the world exists: an attachment-only
    # mismatch in its request refuses in-process, and no final directory is created.
    partial = c13.merge_in_process(run, database, label="partial", finalize=False)
    final_measured = dict(
        ct.require_sqlite_temp_binding(charged_path=partial["multipass_root"] / "final").as_record()
    )
    with pytest.raises(cm.ChunkMultipassError, match=ADMITTED_ON):
        cm.finalize_multipass_body(
            c13.final_request(
                run,
                schedule_path=partial["schedule_path"],
                intermediates_root=partial["intermediates_root"],
                world_directory=partial["multipass_root"] / "final",
                database=database,
                expected_binding={**final_measured, "temp_device_identifier": "disk9s1"},
            )
        )
    assert not (partial["multipass_root"] / "final").exists()
    # No request field weakens the comparison to stable fields.
    for request_type in (cm.GroupMergeRequest, cm.FinalMergeRequest):
        fields = set(inspect.signature(request_type).parameters)
        assert "expected_sqlite_temp_binding" in fields
        assert not {f for f in fields if "stable" in f or "compat" in f or "attach" in f}


def test_c2119_the_orchestrator_hands_children_its_own_fresh_measurement() -> None:
    source = inspect.getsource(cm.run_multipass_f0)
    tree = ast.parse(textwrap.dedent(source))
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    assignments = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "binding" for t in node.targets)
    ]
    assert len(assignments) == 1
    measured = assignments[0].value
    assert isinstance(measured, ast.Call)
    assert isinstance(measured.func, ast.Name)
    assert measured.func.id == "require_sqlite_temp_binding"
    handed = [
        keyword
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "expected_sqlite_temp_binding"
    ]
    assert len(handed) == 2  # one per request type
    for keyword in handed:
        value = keyword.value
        assert isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
        assert value.func.id == "dict"
        inner = value.args[0]
        assert isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
        assert inner.func.attr == "as_record"
        assert isinstance(inner.func.value, ast.Name) and inner.func.value.id == "binding"
    # Measured before the recorded plan is consulted, compared before any child, and the storage
    # plan handed to the result is the one this run computed.
    assert (
        source.index("require_sqlite_temp_binding(")
        < source.index("_record_storage_plan(")
        < source.index("run_group_merge(")
        < source.index("run_final_merge(")
    )
    # The recorded document is consulted only inside _record_storage_plan; the orchestrator never
    # reads it back itself and never derives a binding from it.
    assert "from_document(" not in source and "restart_compatibility" not in source
    recorder = inspect.getsource(cm._record_storage_plan)
    assert (
        recorder.index("from_document(")
        < recorder.index("restart_compatibility()")
        < recorder.index("_require(")
    )
    assert "write_once_json" in recorder and "rewrite" not in recorder.split('"""')[-1]


# ==========================================================================
# C2120-C2122: the standing boundaries, re-stated on the C21 tree
# ==========================================================================
def test_c2120_the_contract_stays_at_two_and_the_document_shape_is_unchanged() -> None:
    assert ct.MULTIPASS_STORAGE_PLAN_CONTRACT == c19.CURRENT_CONTRACT
    assert ct.SUPERSEDED_STORAGE_PLAN_CONTRACTS == (c19.SUPERSEDED_CONTRACT,)
    for module in (ct, cm):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "multipass-storage-plan/" in node.value
        }
        assert literals <= {c19.CURRENT_CONTRACT, c19.SUPERSEDED_CONTRACT}, (
            module.__name__,
            literals,
        )
    document = c19._plan(c19._binding()).as_document()
    assert list(document) == [
        "contract",
        "plan_digest",
        "merge_schedule_digest",
        "seed_catalog_bytes",
        "chunk_bytes_by_id",
        "retained_chunk_bytes",
        "projected_intermediate_bytes",
        "steps",
        "requirements",
        "sqlite_temp_binding",
        "inputs_retained",
        "reclaimable_bytes",
        "reclaim_authority",
        "transfer_authority",
        "external_tier_qualified",
        ct.STORAGE_PLAN_IDENTITY_KEY,
    ]
    with pytest.raises(ct.ChunkTieringError, match=c19.SUPERSEDED):
        ct.MultipassStoragePlan.from_document(
            {**dict(document), "contract": c19.SUPERSEDED_CONTRACT}
        )


def test_c2121_authority_first_binding_before_admission_and_no_production_value() -> None:
    source = Path(cm.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for name in (
        "run_multipass_f0",
        "run_group_merge",
        "run_final_merge",
        "merge_group_body",
        "finalize_multipass_body",
        "_child_main",
    ):
        function = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
        )
        first = (
            function.body[1]
            if isinstance(function.body[0], ast.Expr)
            and isinstance(function.body[0].value, ast.Constant)
            else function.body[0]
        )
        assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call), name
        assert isinstance(first.value.func, ast.Name), name
        assert first.value.func.id == "require_real_multipass_authority", name
    final = inspect.getsource(cm.finalize_multipass_body)
    assert (
        final.index("require_real_multipass_authority()")
        < final.index("_require_expected_binding(")
        < final.index("_admit_merge_step(")
        < final.index("world_directory.mkdir(")
    )
    group = inspect.getsource(cm.merge_group_body)
    assert (
        group.index("require_real_multipass_authority()")
        < group.index("_require_expected_binding(")
        < group.index("_admit_merge_step(")
        < group.index("attempt_root.mkdir(")
    )
    assert "NOT AUTHORIZED" in c13i.refusal_in_a_fresh_interpreter()
    # Behaviourally, under the COMMITTED literal: the child entry refuses before it reads its
    # request -- a request path that does not exist is never opened.
    assert cm.REAL_MULTIPASS_F0_AUTHORITY is None
    with pytest.raises(cm.ChunkMultipassError, match="NOT AUTHORIZED"):
        cm._child_main("/nonexistent/c21-request.json")
    for module, name in (
        (ce, "REAL_CHUNKED_F0_EXECUTION_AUTHORITY"),
        (cm, "REAL_MULTIPASS_F0_AUTHORITY"),
        (cs, "REAL_CHUNK_TRANSFER_AUTHORITY"),
        (cs, "REAL_INTERNAL_RECLAIM_AUTHORITY"),
        (cp, "PRODUCTION_CHUNK_MEMBERS"),
        (cs, "INTERNAL_RESERVE_BYTES"),
        (cs, "CHUNK_PEAK_REQUIREMENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_ONE_PEAK_RATIO"),
        (ct, "MULTIPASS_LEVEL_TWO_PEAK_RATIO"),
        (ct, "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES"),
        (ct, "PRODUCTION_SPILL_POLICY"),
        (ct, "QUALIFIED_EXTERNAL_TIER"),
    ):
        assert c13i.committed_literal(module, name) is None, name
    assert not hasattr(ct, "MULTIPASS_TRANSIENT_BYTES")
    # 30000 has not become a production constant anywhere in the chunk family.
    for module in (cp, cm, ct, ce, cs):
        module_tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        for node in module_tree.body:
            value = getattr(node, "value", None)
            assert not (isinstance(value, ast.Constant) and value.value == 30000), module.__name__


def test_c2122_the_two_transient_terms_stay_independent_and_none_refuses() -> None:
    requirements = ct.MultipassStorageRequirements(
        internal_reserve_bytes=1,
        level_one_peak_ratio=1.0,
        level_two_peak_ratio=1.0,
        level_one_transient_bytes=3,
        level_two_transient_bytes=5,
    )
    assert (
        requirements.transient_for(ct.MERGE_LEVEL_ONE),
        requirements.transient_for(ct.MERGE_LEVEL_TWO),
    ) == (3, 5)
    with pytest.raises(ct.ChunkTieringError, match="charged at exactly one of"):
        requirements.transient_for("final")
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()
    one = ct.merge_step_requirement(
        step="g",
        level=ct.MERGE_LEVEL_ONE,
        input_bytes=10,
        seed_catalog_bytes=1,
        peak_ratio=1.0,
        requirements=requirements,
    )
    two = ct.merge_step_requirement(
        step="final",
        level=ct.MERGE_LEVEL_TWO,
        input_bytes=10,
        seed_catalog_bytes=1,
        peak_ratio=1.0,
        requirements=requirements,
    )
    assert (one.transient_bytes, two.transient_bytes) == (3, 5)
