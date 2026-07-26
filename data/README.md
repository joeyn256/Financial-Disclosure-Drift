# Data directory

This is the only tracked file under `data/`. Everything else here is generated,
git-ignored, and governed by `Docs/Decisions/decision_009_raw_data_governance.md`.

## Layout

```text
data/
├── raw/sec/
│   ├── bulk/        immutable bulk archive downloads
│   ├── indexes/     immutable EDGAR master-index downloads
│   ├── filings/     accession-addressed filing objects
│   └── quarantine/  preserved damaged or unparseable payloads
├── staging/sec/     short-lived staging artifacts
├── catalog/         operational SQLite catalog (sec_ingestion.sqlite3)
├── releases/        frozen Parquet releases under sec_inventory/
├── audit/sec/       readable JSONL event logs
└── locks/           writer leases and rate-limiter coordination
```

Create the tree with `python -m disclosure_drift validate-sec-config`, which reports
the resolved locations, or let an ingestion command create it on demand.

## Rules

- **Nothing here is committed.** Raw SEC files, SQLite databases and their `-wal`
  and `-shm` companions, Parquet releases, `.part` files, and lock files are all
  ignored.
- **Raw objects are immutable and append-only.** A later differing response becomes
  a new observation; a damaged file is quarantined and preserved, never replaced;
  parser failures never delete raw evidence.
- **Only relative paths are persisted.** Catalog rows, manifests, and releases store
  paths relative to `DISCLOSURE_DRIFT_DATA_ROOT` or `DISCLOSURE_DRIFT_BACKUP_ROOT`,
  so no personal absolute path can reach an exported artifact.

## Relocating the roots

```bash
export DISCLOSURE_DRIFT_DATA_ROOT=/Volumes/research/disclosure-drift/data
export DISCLOSURE_DRIFT_BACKUP_ROOT=/Volumes/backup/disclosure-drift
```

Both may be absolute machine-local paths. The backup root may stay unset during
offline work; commands that back up or restore validate it, and broad ingestion
requires it to sit on a different physical volume from the data root.
