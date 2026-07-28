"""Migration 0008 enforces durable observation supersession and reuse lineage."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.storage.sqlite import (
    apply_migrations,
    available_migrations,
    connect,
    transaction,
)

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_INSERT = """
INSERT INTO census_source_observations (
    observation_id, source_id, request_identity, requested_url, purpose,
    retrieved_at_utc, outcome, validators_sent_json, headers_json,
    observed_content_kind, transport_sha256, stored_sha256, logical_sha256,
    content_sha256, transport_size_bytes, content_size_bytes, stored_size_bytes,
    storage_representation, relative_storage_path,
    parser_version, supersedes_observation_id, reused_observation_id,
    redirects_json, redirect_hops_json, attempts, detail, projected_to_audit,
    recorded_at_utc
) VALUES (
    :observation_id, :source_id, :request_identity, :requested_url, :purpose,
    :retrieved_at_utc, :outcome, '{}', '{}',
    :observed_content_kind, :transport_sha256, :stored_sha256, :logical_sha256,
    :content_sha256, :transport_size_bytes, :content_size_bytes, :stored_size_bytes,
    :storage_representation, :relative_storage_path,
    :parser_version, :supersedes_observation_id, :reused_observation_id,
    '[]', '[]', 1, '', 0, :recorded_at_utc
)
"""


def _values(
    observation_id: str,
    *,
    outcome: str = "stored_new",
    source_id: str = "sec_company_tickers",
    request_identity: str = "sec_company_tickers|https://www.sec.gov/files/company_tickers.json",
    retrieved_at_utc: str = "2026-07-26T00:00:00Z",
    supersedes_observation_id: str | None = None,
    reused_observation_id: str | None = None,
    raw_hash: str = _HASH_A,
    relative_storage_path: str | None = "raw/sec/indexes/object.json.gz",
    storage_representation: str | None = "deterministic_gzip",
    parser_version: str | None = "company-tickers/1.0",
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "source_id": source_id,
        "request_identity": request_identity,
        "requested_url": "https://www.sec.gov/files/company_tickers.json",
        "purpose": "offline lineage fixture",
        "retrieved_at_utc": retrieved_at_utc,
        "outcome": outcome,
        "observed_content_kind": "json" if relative_storage_path is not None else None,
        "transport_sha256": raw_hash if relative_storage_path is not None else None,
        "stored_sha256": raw_hash if relative_storage_path is not None else None,
        "logical_sha256": raw_hash if relative_storage_path is not None else None,
        "content_sha256": raw_hash if relative_storage_path is not None else None,
        "transport_size_bytes": 10 if relative_storage_path is not None else None,
        "content_size_bytes": 10 if relative_storage_path is not None else None,
        "stored_size_bytes": 20 if relative_storage_path is not None else None,
        "storage_representation": storage_representation,
        "relative_storage_path": relative_storage_path,
        "parser_version": parser_version,
        "supersedes_observation_id": supersedes_observation_id,
        "reused_observation_id": reused_observation_id,
        "recorded_at_utc": retrieved_at_utc,
    }


def _insert(connection: sqlite3.Connection, values: Mapping[str, object]) -> None:
    connection.execute(_INSERT, values)


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
    return path


def test_valid_reuse_lineage_preserves_separate_observations(database: Path) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("owner"))
        _insert(
            connection,
            _values(
                "reuse",
                outcome="reused_snapshot",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                reused_observation_id="owner",
            ),
        )
        rows = connection.execute(
            "SELECT observation_id, reused_observation_id "
            "FROM census_source_observations ORDER BY observation_id"
        ).fetchall()
    assert [(row["observation_id"], row["reused_observation_id"]) for row in rows] == [
        ("owner", None),
        ("reuse", "owner"),
    ]


def test_valid_supersession_retains_prior_observation(database: Path) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("prior"))
        _insert(
            connection,
            _values(
                "changed",
                outcome="superseded",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                supersedes_observation_id="prior",
                raw_hash=_HASH_B,
                relative_storage_path="raw/sec/indexes/changed.json.gz",
            ),
        )
        prior = connection.execute(
            "SELECT outcome, stored_sha256 FROM census_source_observations "
            "WHERE observation_id = 'prior'"
        ).fetchone()
    assert tuple(prior) == ("stored_new", _HASH_A)


@pytest.mark.parametrize("target_outcome", ("failed", "quarantined", "stored_new"))
def test_supersession_refuses_unusable_or_payloadless_target(
    database: Path,
    target_outcome: str,
) -> None:
    with connect(database, writer=True) as connection:
        _insert(
            connection,
            _values(
                "prior",
                outcome=target_outcome,
                relative_storage_path=None,
            ),
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="supersession target is not usable preserved evidence",
        ):
            _insert(
                connection,
                _values(
                    "changed",
                    outcome="superseded",
                    retrieved_at_utc="2026-07-27T00:00:00Z",
                    supersedes_observation_id="prior",
                    raw_hash=_HASH_B,
                    relative_storage_path="raw/sec/indexes/changed.json.gz",
                ),
            )


def test_supersession_refuses_incomplete_new_object_metadata(database: Path) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("prior"))
        changed = _values(
            "changed",
            outcome="superseded",
            retrieved_at_utc="2026-07-27T00:00:00Z",
            supersedes_observation_id="prior",
            raw_hash=_HASH_B,
            relative_storage_path="raw/sec/indexes/changed.json.gz",
        )
        changed["transport_sha256"] = None
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            _insert(connection, changed)


@pytest.mark.parametrize(
    ("outcome", "field"),
    (
        ("unchanged_content", "reused_observation_id"),
        ("superseded", "supersedes_observation_id"),
    ),
)
def test_dangling_lineage_is_rejected_at_transaction_commit(
    database: Path,
    outcome: str,
    field: str,
) -> None:
    values = _values("dangling", outcome=outcome)
    values[field] = "missing"
    with (
        connect(database, writer=True) as connection,
        pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"),
        transaction(connection),
    ):
        _insert(connection, values)


def test_deferred_foreign_key_failure_rolls_back_and_connection_recovers(
    database: Path,
) -> None:
    values = _values(
        "dangling",
        outcome="unchanged_content",
        reused_observation_id="missing",
    )
    with connect(database, writer=True) as connection:
        with (
            pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"),
            transaction(connection),
        ):
            _insert(connection, values)
        assert not connection.in_transaction
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM census_source_observations WHERE observation_id = 'dangling'"
            ).fetchone()[0]
            == 0
        )
        with transaction(connection):
            _insert(connection, _values("valid-after-rollback"))


@pytest.mark.parametrize(
    ("outcome", "field"),
    (
        ("unchanged_content", "reused_observation_id"),
        ("superseded", "supersedes_observation_id"),
    ),
)
def test_self_reference_is_rejected(
    database: Path,
    outcome: str,
    field: str,
) -> None:
    values = _values("self", outcome=outcome)
    values[field] = "self"
    with (
        connect(database, writer=True) as connection,
        pytest.raises(sqlite3.IntegrityError, match="lineage cycle|CHECK constraint failed"),
    ):
        _insert(connection, values)


def test_two_node_cycle_is_rejected(database: Path) -> None:
    with (
        connect(database, writer=True) as connection,
        pytest.raises(sqlite3.IntegrityError, match="observation lineage cycle"),
        transaction(connection),
    ):
        _insert(
            connection,
            _values("a", outcome="superseded", supersedes_observation_id="b"),
        )
        _insert(
            connection,
            _values("b", outcome="superseded", supersedes_observation_id="a"),
        )


def test_longer_mixed_lineage_cycle_is_rejected(database: Path) -> None:
    with (
        connect(database, writer=True) as connection,
        pytest.raises(sqlite3.IntegrityError, match="observation lineage cycle"),
        transaction(connection),
    ):
        _insert(
            connection,
            _values("a", outcome="superseded", supersedes_observation_id="b"),
        )
        _insert(
            connection,
            _values("b", outcome="superseded", supersedes_observation_id="c"),
        )
        _insert(
            connection,
            _values("c", outcome="superseded", supersedes_observation_id="a"),
        )


@pytest.mark.parametrize(
    ("override", "message"),
    (
        ({"source_id": "sec_company_tickers_exchange"}, "source or request identity"),
        ({"request_identity": "different-request"}, "source or request identity"),
    ),
)
def test_incompatible_reuse_identity_is_rejected(
    database: Path,
    override: Mapping[str, object],
    message: str,
) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("owner"))
        values = _values(
            "reuse",
            outcome="unchanged_content",
            retrieved_at_utc="2026-07-27T00:00:00Z",
            reused_observation_id="owner",
        )
        values.update(override)
        with pytest.raises(sqlite3.IntegrityError, match=message):
            _insert(connection, values)


def test_incompatible_supersession_request_identity_is_rejected(database: Path) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("owner"))
        with pytest.raises(sqlite3.IntegrityError, match="supersession source or request"):
            _insert(
                connection,
                _values(
                    "changed",
                    outcome="superseded",
                    request_identity="different-request",
                    retrieved_at_utc="2026-07-27T00:00:00Z",
                    supersedes_observation_id="owner",
                    raw_hash=_HASH_B,
                ),
            )


@pytest.mark.parametrize(
    ("target_override", "reuse_override", "message"),
    (
        (
            {"outcome": "quarantined"},
            {},
            "does not own a verified raw object",
        ),
        (
            {"storage_representation": None},
            {},
            "does not own a verified raw object",
        ),
        (
            {"storage_representation": "identical"},
            {},
            "does not own a verified raw object",
        ),
        (
            {},
            {"raw_hash": _HASH_B},
            "raw-object metadata mismatch",
        ),
        (
            {},
            {"parser_version": "company-tickers/2.0"},
            "raw-object metadata mismatch",
        ),
    ),
)
def test_invalid_reuse_owner_or_metadata_is_rejected(
    database: Path,
    target_override: Mapping[str, object],
    reuse_override: Mapping[str, object],
    message: str,
) -> None:
    with connect(database, writer=True) as connection:
        target = _values("owner")
        target.update(target_override)
        _insert(connection, target)
        reuse_parameters: dict[str, object] = {
            "outcome": "unchanged_content",
            "retrieved_at_utc": "2026-07-27T00:00:00Z",
            "reused_observation_id": "owner",
        }
        reuse_parameters.update(reuse_override)
        reuse = _values("reuse", **reuse_parameters)  # type: ignore[arg-type]
        with pytest.raises(sqlite3.IntegrityError, match=message):
            _insert(connection, reuse)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("transport_sha256", None),
        ("transport_size_bytes", None),
        ("observed_content_kind", None),
    ),
)
def test_reuse_refuses_owner_missing_runtime_required_metadata(
    database: Path,
    field: str,
    bad_value: object,
) -> None:
    with connect(database, writer=True) as connection:
        owner = _values("owner")
        owner[field] = bad_value
        _insert(connection, owner)
        with pytest.raises(sqlite3.IntegrityError, match="verified raw object"):
            _insert(
                connection,
                _values(
                    "reuse",
                    outcome="unchanged_content",
                    retrieved_at_utc="2026-07-27T00:00:00Z",
                    reused_observation_id="owner",
                ),
            )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("transport_sha256", _HASH_B),
        ("transport_size_bytes", 11),
        ("observed_content_kind", "html"),
    ),
)
def test_reuse_refuses_runtime_metadata_mismatch(
    database: Path,
    field: str,
    bad_value: object,
) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("owner"))
        reuse = _values(
            "reuse",
            outcome="unchanged_content",
            retrieved_at_utc="2026-07-27T00:00:00Z",
            reused_observation_id="owner",
        )
        reuse[field] = bad_value
        with pytest.raises(sqlite3.IntegrityError, match="metadata mismatch|CHECK constraint"):
            _insert(connection, reuse)


def test_deferred_reuse_refuses_incomplete_owner_runtime_metadata(
    database: Path,
) -> None:
    with (
        connect(database, writer=True) as connection,
        pytest.raises(sqlite3.IntegrityError, match="deferred reuse target"),
        transaction(connection),
    ):
        _insert(
            connection,
            _values(
                "reuse",
                outcome="unchanged_content",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                reused_observation_id="owner",
            ),
        )
        owner = _values("owner")
        owner["observed_content_kind"] = None
        _insert(connection, owner)


def test_deletion_and_mutation_of_referenced_evidence_are_restricted(
    database: Path,
) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("owner"))
        _insert(
            connection,
            _values(
                "reuse",
                outcome="unchanged_content",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                reused_observation_id="owner",
            ),
        )
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            connection.execute(
                "DELETE FROM census_source_observations WHERE observation_id = 'owner'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="raw-object metadata is immutable"):
            connection.execute(
                "UPDATE census_source_observations SET stored_sha256 = ? "
                "WHERE observation_id = 'owner'",
                (_HASH_B,),
            )


def test_supersession_participants_preserve_object_metadata(database: Path) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("prior"))
        _insert(
            connection,
            _values(
                "changed",
                outcome="superseded",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                supersedes_observation_id="prior",
                raw_hash=_HASH_B,
                relative_storage_path="raw/sec/indexes/changed.json.gz",
            ),
        )
        for observation_id in ("prior", "changed"):
            with pytest.raises(sqlite3.IntegrityError, match="raw-object metadata is immutable"):
                connection.execute(
                    "UPDATE census_source_observations SET stored_sha256 = ? "
                    "WHERE observation_id = ?",
                    ("c" * 64, observation_id),
                )


def test_deferred_insertion_order_is_validated_when_target_arrives(database: Path) -> None:
    with connect(database, writer=True) as connection, transaction(connection):
        _insert(
            connection,
            _values(
                "reuse",
                outcome="unchanged_content",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                reused_observation_id="owner",
            ),
        )
        _insert(connection, _values("owner"))
    with connect(database) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_valid_pre_0008_database_migrates_without_row_loss(tmp_path: Path) -> None:
    path = tmp_path / "pre-r3.sqlite3"
    with connect(path, writer=True) as connection:
        assert len(apply_migrations(connection, available_migrations()[:7])) == 7
        _insert(connection, _values("owner"))
        _insert(
            connection,
            _values(
                "reuse",
                outcome="unchanged_content",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                reused_observation_id="owner",
            ),
        )
        connection.execute(
            "INSERT INTO census_parser_runs "
            "(parser_run_id, source_observation_id, parser_id, parser_version, "
            "started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
            "outcome, summary_json) VALUES "
            "('parser-run', 'owner', 'fixture', '1', 'now', 'now', "
            "0, 0, 'completed', '{}')"
        )
        assert [
            migration.version
            for migration in apply_migrations(connection, available_migrations()[:8])
        ] == [8]
        count = connection.execute("SELECT COUNT(*) FROM census_source_observations").fetchone()[0]
        child_count = connection.execute(
            "SELECT COUNT(*) FROM census_parser_runs WHERE parser_run_id = 'parser-run'"
        ).fetchone()[0]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert count == 2
    assert child_count == 1


def test_invalid_preexisting_lineage_refuses_migration_without_data_loss(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pre-r3-invalid.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection, available_migrations()[:7])
        _insert(
            connection,
            _values(
                "dangling",
                outcome="unchanged_content",
                reused_observation_id="missing",
            ),
        )
        with pytest.raises(GateFailureError, match="missing observation"):
            apply_migrations(connection)
        versions = connection.execute(
            "SELECT version FROM ops_schema_migrations ORDER BY version"
        ).fetchall()
        count = connection.execute("SELECT COUNT(*) FROM census_source_observations").fetchone()[0]
    assert [row["version"] for row in versions] == list(range(1, 8))
    assert count == 1


def test_preexisting_foreign_key_violation_refuses_0008_before_rebuild(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pre-r3-invalid-foreign-key.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection, available_migrations()[:7])
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO census_parser_runs "
            "(parser_run_id, source_observation_id, parser_id, parser_version, "
            "started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
            "outcome, summary_json) VALUES "
            "('parser-run', 'missing-observation', 'fixture', '1', 'now', 'now', "
            "0, 0, 'completed', '{}')"
        )
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(GateFailureError, match="before migration 0008"):
            apply_migrations(connection)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM ops_schema_migrations WHERE version = 8"
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM census_parser_runs WHERE parser_run_id = 'parser-run'"
            ).fetchone()[0]
            == 1
        )


def test_0008_schema_and_provenance_bookkeeping_commit_atomically(
    tmp_path: Path,
) -> None:
    path = tmp_path / "atomic-r3.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection, available_migrations()[:7])
        connection.executescript(
            "CREATE TRIGGER reject_migration_8 "
            "BEFORE INSERT ON ops_schema_migrations "
            "WHEN NEW.version = 8 BEGIN "
            "SELECT RAISE(ABORT, 'fault after schema before provenance'); END;"
        )
        with pytest.raises(sqlite3.IntegrityError, match="fault after schema"):
            apply_migrations(connection, available_migrations()[:8])
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert not connection.in_transaction
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM ops_schema_migrations WHERE version = 8"
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type = 'table' AND name = 'census_projection_recovery_events'"
            ).fetchone()
            is None
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM pragma_foreign_key_list('census_source_observations')"
            ).fetchone()[0]
            == 0
        )

        connection.execute("DROP TRIGGER reject_migration_8")
        assert [
            migration.version
            for migration in apply_migrations(connection, available_migrations()[:8])
        ] == [8]
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM pragma_foreign_key_list('census_source_observations')"
            ).fetchone()[0]
            == 2
        )


def test_restart_preserves_lineage_and_foreign_key_integrity(database: Path) -> None:
    with connect(database, writer=True) as connection:
        _insert(connection, _values("owner"))
        _insert(
            connection,
            _values(
                "changed",
                outcome="superseded",
                retrieved_at_utc="2026-07-27T00:00:00Z",
                supersedes_observation_id="owner",
                raw_hash=_HASH_B,
            ),
        )
    with connect(database, writer=True) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert apply_migrations(connection) == ()
