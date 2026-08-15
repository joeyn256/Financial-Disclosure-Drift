"""R3 write-freedom and M3.3 gate-isolation tests (contract §14, §23; **R3**, **R8**).

The point of these tests is that a passing rehearsal, a green suite, a commit, or a tag
must never be mistakable for an owner authorization. Each boundary below is asserted as
an absence that a future change would have to remove deliberately.
"""

from __future__ import annotations

import ast
import hashlib
import socket
import sqlite3
import urllib.request
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from disclosure_drift.m3 import candidate_snapshot, offline_parse
from disclosure_drift.paths import DataTree
from disclosure_drift.sec import http_client, httpx_transport
from disclosure_drift.storage.catalog import (
    CatalogWriter,
    read_only_connection,
    strictly_read_only_connection,
)
from disclosure_drift.storage.sqlite import apply_migrations, connect

_REPOSITORY = Path(__file__).resolve().parents[2]
_CLI = _REPOSITORY / "src" / "disclosure_drift" / "cli.py"
_LEASE = "catalog_writer.lease"


def _catalog(tmp_path: Path) -> Path:
    database = tmp_path / "catalog.sqlite3"
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
    return database


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ==========================================================================
# R3: durable-byte equality, no lease, no checkpoint, writes refused
# ==========================================================================


def test_a_strictly_read_only_read_leaves_the_durable_bytes_identical(tmp_path: Path) -> None:
    database = _catalog(tmp_path)
    before = _digest(database)
    with strictly_read_only_connection(database) as connection:
        connection.execute("SELECT name FROM ops_schema_migrations ORDER BY name").fetchall()
    assert _digest(database) == before


def test_a_strictly_read_only_handle_refuses_every_write(tmp_path: Path) -> None:
    database = _catalog(tmp_path)
    with strictly_read_only_connection(database) as connection:
        for statement in (
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES ('x', 'sec_census', 'running', 'M2.2', 'now', '')",
            "DELETE FROM ops_schema_migrations",
            "UPDATE ops_schema_migrations SET name = 'x'",
        ):
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                connection.execute(statement)


def test_a_strictly_read_only_read_acquires_no_writer_lease(tmp_path: Path) -> None:
    database = _catalog(tmp_path)
    locks = tmp_path / "locks"
    with strictly_read_only_connection(database) as connection:
        connection.execute("SELECT 1").fetchone()
    assert not (locks / _LEASE).exists()


def test_the_lease_file_is_written_only_by_an_actual_writer(tmp_path: Path) -> None:
    """The negative above would be vacuous if nothing ever wrote a lease."""
    database = _catalog(tmp_path)
    locks = tmp_path / "locks"
    with CatalogWriter(database, locks):
        assert (locks / _LEASE).exists()


def test_a_convention_only_read_write_handle_is_not_the_r3_standard(tmp_path: Path) -> None:
    """``query_only``-by-convention would let this write; R3 requires the OS refuse it."""
    database = _catalog(tmp_path)
    with read_only_connection(database) as connection:
        connection.execute(
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES ('x', 'sec_census', 'running', 'M2.2', 'now', '')"
        )
        connection.execute("DELETE FROM ops_ingestion_jobs WHERE job_id = 'x'")


def _read_only_helper_calls() -> dict[str, set[str]]:
    """Which read-only opener each ``cli.py`` chain-head helper actually calls."""
    tree = ast.parse(_CLI.read_text(encoding="utf-8"))
    calls: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.endswith("migration_chain_head"):
            calls[node.name] = {
                inner.func.id
                for inner in ast.walk(node)
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
            }
    return calls


def test_every_m3_3_chain_head_helper_opens_strictly_read_only() -> None:
    """**R8**: the two shared helpers M3.3 actually uses are hardened, narrowly."""
    calls = _read_only_helper_calls()
    assert set(calls) == {"_migration_chain_head", "_m3_migration_chain_head"}
    for name, used in calls.items():
        assert "strictly_read_only_connection" in used, f"{name} is not R3-compliant"
        assert "read_only_connection" not in used, f"{name} kept the convention-only opener"


def test_the_hardening_did_not_become_a_repository_wide_cleanup() -> None:
    """R8 authorizes the specific call sites and nothing around them."""
    body = _CLI.read_text(encoding="utf-8")
    assert "read_only_connection(catalog_path) as connection" in body


# ==========================================================================
# IN-4: a process-level network bomb, and the claim it licenses
# ==========================================================================


class NetworkBombError(AssertionError):
    """Raised the instant any offline path reaches for a network capability."""


@pytest.fixture
def network_bomb(monkeypatch: pytest.MonkeyPatch) -> Callable[[], int]:
    """Detonate on socket use, transport construction, or client construction.

    The autouse suite blocker already covers raw sockets. This adds both current
    production transport-construction points -- ``HttpxTransport`` and ``SecClient`` --
    plus ``urlopen``. That pair is an implementation inventory established by source
    inspection; no decision record names it, and none is cited for it here. The
    governed requirement is Decision 071 §6 (**IN-4**), which prohibits network
    construction, network calls, and SEC client or transport creation, requires a
    process-level network bomb, and fixes the claim a rehearsal may make as the
    accurate one: **no network construction or use occurred**, rather than the weaker
    and false "no network capability was imported".
    """
    detonations = 0

    def _boom(*_: object, **__: object) -> None:
        nonlocal detonations
        detonations += 1
        message = "an offline M3.3 path reached for a network capability"
        raise NetworkBombError(message)

    for module, attribute in (
        (socket, "socket"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (urllib.request, "urlopen"),
        (httpx_transport.HttpxTransport, "__init__"),
        (http_client.SecClient, "__init__"),
    ):
        monkeypatch.setattr(module, attribute, _boom)
    return lambda: detonations


def test_the_network_bomb_detonates_when_it_should(
    network_bomb: Callable[[], int],
) -> None:
    """A bomb that never fires would make every quiet run meaningless."""
    with pytest.raises(NetworkBombError):
        socket.create_connection(("example.invalid", 443))
    with pytest.raises(NetworkBombError):
        httpx_transport.HttpxTransport()
    assert network_bomb() == 2


def test_the_offline_driver_never_reaches_a_network_capability(
    tmp_path: Path, network_bomb: Callable[[], int]
) -> None:
    database = _catalog(tmp_path)
    with CatalogWriter(database, tmp_path / "locks") as writer:
        report = offline_parse.run_offline_metadata_parse(
            writer=writer, tree=DataTree.from_root(tmp_path / "data")
        )
    assert report.planned_source_count == 0
    assert network_bomb() == 0


def test_the_builder_never_reaches_a_network_capability(
    tmp_path: Path, network_bomb: Callable[[], int]
) -> None:
    database = _catalog(tmp_path)
    with (
        CatalogWriter(database, tmp_path / "locks") as writer,
        pytest.raises(candidate_snapshot.CandidateSnapshotError),
    ):
        candidate_snapshot.build_and_freeze_candidate_snapshot(
            writer=writer,
            inputs=candidate_snapshot.CandidateSnapshotInputs(
                census_run_id="absent-job",
                coverage_start="2009-01-01",
                coverage_end="2026-06-30",
                as_of_date="2026-06-30",
            ),
        )
    assert network_bomb() == 0


# ==========================================================================
# Gate isolation: I/R is not E0, E0 is not E1, E1 is not E2, E2 is not M3.4
# ==========================================================================


def test_no_cli_subcommand_executes_the_real_offline_parse() -> None:
    """§16 of the authorizing packet: no operator-facing "run E0 now" command."""
    body = _CLI.read_text(encoding="utf-8")
    assert "run_offline_metadata_parse" not in body
    assert "build_and_freeze_candidate_snapshot" not in body


def test_the_offline_driver_grants_no_authorization_token() -> None:
    report = offline_parse.OfflineParseReport(outcomes=(), accession_resolutions=0)
    record = report.as_record()
    assert "authorization" not in " ".join(str(key) for key in record)
    assert record["requests_made"] == 0
    assert record["transports_constructed"] == 0


def test_the_builder_exposes_no_authorization_argument() -> None:
    """A caller cannot pass something that reads as an owner gate."""
    fields = candidate_snapshot.CandidateSnapshotInputs.__dataclass_fields__
    assert set(fields) == {"census_run_id", "coverage_start", "coverage_end", "as_of_date"}


def test_the_tracked_network_switches_remain_disabled() -> None:
    config = yaml.safe_load((_REPOSITORY / "configs" / "project.yaml").read_text())
    assert config["network"]["enabled"] is False
    assert config["network"]["m3_acquire_enabled"] is False


def test_only_the_authorized_r46_migration_was_added() -> None:
    """Accepted Decision 083 §10 authorizes migration ``0014`` and nothing beyond it.

    The M3.3 boundary is not "no migration ever"; it is "no migration this stage was not
    authorized to write". ``0015`` -- the verified-evidence schema -- remains explicitly
    unauthorized (**R63**), so the chain ending anywhere past ``0014`` fails here.
    """
    migrations = sorted(
        path.name
        for path in (_REPOSITORY / "src/disclosure_drift/storage/migrations").glob("*.sql")
    )
    assert migrations[-1] == "0014_m33_multi_registrant_relational_correction.sql"
    assert len(migrations) == 14
    assert not any(name.startswith("0015_") for name in migrations)


def test_the_coverage_policy_version_has_exactly_one_executable_definition() -> None:
    """Decision 070 §4: one canonical constant, and no competing literal."""
    from disclosure_drift import pilot_policy

    assert pilot_policy.PILOT_COVERAGE_POLICY_VERSION == "pilot-coverage/1.0"
    offenders = []
    for path in (_REPOSITORY / "src").rglob("*.py"):
        if path.name == "pilot_policy.py":
            continue
        if "pilot-coverage/1.0" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(_REPOSITORY).as_posix())
    assert offenders == [], f"a second executable definition appeared in {offenders}"
