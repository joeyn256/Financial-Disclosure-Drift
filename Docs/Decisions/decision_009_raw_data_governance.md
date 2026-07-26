# Decision 009 — Raw-Data Governance and Storage Architecture

**Date:** 2026-07-25
**Status:** Approved by project owner
**Governs:** Milestone 2 onward
**Related:** Decision 007, Decision 008, Decision 010

## 1. Four storage roles

| Role | Medium | Location |
|---|---|---|
| Immutable raw SEC files | Filesystem | `{data_root}/raw/sec/` |
| Operational catalog | SQLite | `{data_root}/catalog/sec_ingestion.sqlite3` |
| Frozen releases | Parquet | `{data_root}/releases/sec_inventory/` |
| Readable event logs | JSONL | `{data_root}/audit/sec/` |

## 2. Configurable roots

| Variable | Role |
|---|---|
| `DISCLOSURE_DRIFT_DATA_ROOT` | Primary data root; may be an absolute machine-local path |
| `DISCLOSURE_DRIFT_BACKUP_ROOT` | Backup root; may be an absolute machine-local path; may be unset during offline work, and is validated by any command that needs it |

These are the only two runtime roots. The audit directory is always `{data_root}/audit/sec` and is not
separately configurable.

Database rows, manifests, and releases store **only paths relative to their configured root**. No
committed artifact may contain a personal absolute path. Tracked YAML never contains a fabricated
backup destination.

## 3. Directory tree

```text
data/
├── raw/sec/{bulk,indexes,filings,quarantine}/
├── staging/sec/
├── catalog/
├── releases/sec_inventory/
├── audit/sec/
└── locks/
```

Only a small `data/README.md` is tracked in Git. Raw SEC files, SQLite databases, SQLite `-wal` and
`-shm` files, Parquet releases, `.part` files, lock files, and personal contact configuration are
ignored.

## 4. Raw addressing and required fields

Storage is accession-addressed with immutable observation directories. Every raw object records:

```text
raw_object_id            observation_id            logical_role
source_url_canonical     relative_storage_path     media_type
content_encoding_received content_sha256           stored_sha256
content_size_bytes       stored_size_bytes         retrieved_at_utc
retrieval_attempt_id
```

Two hashes with distinct meanings:

| Hash | Over |
|---|---|
| `content_sha256` | The decoded HTTP response entity bytes, before any text transformation. This is the integrity anchor. |
| `stored_sha256` | The bytes actually written locally. Recorded for local verification; never asserted to be portable across machines. |

## 5. Compression

ZIP archives and already-compressed binary payloads are preserved exactly as received.

Text-like raw files use deterministic gzip:

```text
algorithm = gzip
compression_level = 6
mtime = 0
```

Decompression must reproduce the recorded `content_sha256`; that round trip, not byte-identical
compressed output, is the integrity requirement.

Never normalized: line endings, whitespace, encodings, HTML, SGML, or JSON formatting.

## 6. No deletion, no overwrite

- A raw SEC object is never silently overwritten.
- A later differing response becomes a **new observation** with `REMOTE_CONTENT_CHANGED`.
- A damaged local file is quarantined into `raw/sec/quarantine/` and preserved with
  `RAW_FILE_CHECKSUM_MISMATCH`. It is never silently replaced.
- Parser failures never justify deleting raw files; they are recorded in `audit_parser_failures`.
- Crash-orphaned evidence is never deleted automatically.

## 7. Atomic write protocol

1. Create a retrieval-attempt record.
2. Write to a unique `.part` file.
3. Stream the response and compute `content_sha256`.
4. Flush and `fsync` the temporary file.
5. Validate content.
6. Deterministically compress when required.
7. Compute `stored_sha256`.
8. Place the final temporary file on the same filesystem as the destination.
9. Atomically promote with `os.replace`.
10. Best-effort `fsync` of the parent directory.
11. Commit the object and state records in one SQLite transaction.
12. Mark the retrieval attempt complete.

The catalog must never claim an object is committed before the final file exists. On restart,
reconciliation may only adopt a valid final file that is missing a database row, or quarantine a
partial file. A `.part` file is never treated as complete.

## 8. SQLite operational rules

SQLite 3.37 or newer, `STRICT` tables where the type system allows. Every connection sets
`foreign_keys = ON` and `busy_timeout = 10000`; the writer additionally sets `journal_mode = WAL` and
`synchronous = FULL`.

There is **one designated logical writer**. Retrieval and parsing workers produce staging artifacts
and structured completion messages; all database writes are serialized through the catalog-writing
layer. No notebook, cron job, second CLI invocation, or worker process may write independently.

Release freezing requires `integrity_check = ok` and zero rows from `foreign_key_check`, with
`quick_check` run first. Backups use the SQLite backup API or another SQLite-consistent mechanism;
naïve copying of a live WAL-mode database is prohibited. Schema changes use explicit, versioned
migrations.

## 9. Backup and restore

Backups are created after the accepted pilot, after completed ingestion batches, before migrations,
before release freezing, and after a release is frozen. Before broad ingestion is permitted, the
backup root must be on a different physical volume from the data root.

The pilot performs a full offline restore and must achieve 100 percent raw-object checksum recovery,
100 percent pilot-accession recovery, 100 percent relationship recovery, an identical normalized
release hash, and zero network requests.

## 10. Release reproducibility

Releases are frozen and never edited. Incremental updates create new releases plus release diffs.
Reproducibility is asserted on **normalized table content hashes** — stable column order, stable row
order, UTC-normalized timestamps, explicit Eastern filing dates, relative paths only, no personal
contact data — not on Parquet file bytes.

## 11. Revisit triggers

Reopen if SEC response encodings change materially, if deterministic compression proves unstable
across supported platforms, if the single-writer model becomes a throughput blocker at production
scale, or if capacity thresholds cannot be met.
