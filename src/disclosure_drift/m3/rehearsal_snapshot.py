"""Track B — the explicitly governed feasible rehearsal snapshot, and the R28 bridge.

Accepted Decision 073 §3 (**R27**) splits M3.3 rehearsal into two tracks that may never
be conflated:

* **Track A** runs the real candidate builder over the synthetic base case and is
  *expected* to be infeasible on the amendment-purpose quota. Nothing in this module
  participates in it.
* **Track B** is this module: the same base case, plus **one** explicitly stipulated
  class of synthetic fact — an amendment-purpose category on synthetic amendment
  accessions — so the accepted selector, stores, seal, replay, and manifest machinery
  can be exercised on a *conforming feasible* snapshot.

**These facts are fixture stipulations, never a production inference rule.** They are
not derived from a form suffix, XBRL presence, filing timing, a primary-document name,
an amendment count, linkage state, a company name, or a filing size; IN-2 is not
reversed; and no production path can reach them:

* nothing in ``disclosure_drift.m3.candidate_snapshot`` imports this module, and a
  boundary test asserts that;
* the production builder has **no hook, flag, or fallback** that reaches an overlay —
  it persists only the derivation its own rules produced;
* the overlay is applied to an already-derived
  :class:`~disclosure_drift.m3.candidate_snapshot.CandidateDerivation`, which is the
  same object the production builder produces, so Track B still writes through the
  **single** authoritative persistence routine rather than a second writer.

**A Track-B result never states or implies real feasibility.** Every report it feeds
carries ``FEASIBILITY SOURCE: EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT``
(**R29**), and ``M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN`` (**R30**) stays
open regardless of what it proves.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.m3.candidate_classification import AMENDMENT_PURPOSE_CATEGORIES
from disclosure_drift.m3.candidate_identity import (
    ACCESSION_EVIDENCE_COLUMNS,
    ACCESSION_REASONS_COLUMNS,
    ACCESSION_TABLE_COLUMNS,
    ENTITY_EVIDENCE_COLUMNS,
    ENTITY_REASONS_COLUMNS,
    ENTITY_TABLE_COLUMNS,
    REGISTRANT_TABLE_COLUMNS,
    resolution_contributors,
    resolution_sha256,
)
from disclosure_drift.m3.candidate_snapshot import (
    CandidateDerivation,
    CandidateSnapshotInputs,
    FrozenCandidateSnapshot,
    derive_candidate_snapshot,
    persist_and_freeze_derivation,
)
from disclosure_drift.pilot_policy import PILOT_EVIDENCE_POLICY_VERSION
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import connect

__all__ = [
    "AMENDMENT_PURPOSE_REASON_CODE",
    "BRIDGE_ALLOWED_ACCESSION_COLUMNS",
    "BRIDGE_ALLOWED_REASON_CODES",
    "BRIDGE_ALLOWED_SNAPSHOT_FIELDS",
    "SYNTHETIC_REHEARSAL_ONLY",
    "BridgeDifference",
    "BridgeReport",
    "PairedSnapshots",
    "apply_synthetic_amendment_purpose",
    "build_paired_snapshots",
    "compare_tracks",
]

#: The documentation label **R27** requires the fixture to identify these facts by. It
#: is a label in reports and docstrings only: it is never written to a candidate row,
#: never a persisted evidence-vocabulary value, and never a reason code.
SYNTHETIC_REHEARSAL_ONLY: Final = "SYNTHETIC_REHEARSAL_ONLY"

#: The production reason the builder writes when metadata establishes no category. It
#: is removed on the Track-B side exactly where a category is stipulated, because
#: keeping it would make the row internally contradictory.
AMENDMENT_PURPOSE_REASON_CODE: Final = "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN"

_PURPOSE_DIMENSION: Final = "amendment_purpose"

#: **R28**'s explicit allowlist on ``pilot_candidate_accessions``. A difference in any
#: other column fails the bridge; this tuple is the whole permission.
BRIDGE_ALLOWED_ACCESSION_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "amendment_purpose_category",
        "amendment_purpose_evidence_level",
        "amendment_purpose_resolution_sha256",
        "amendment_purpose_quota_eligible",
    }
)

#: The only reason row that may differ, and only by being absent on the Track-B side.
BRIDGE_ALLOWED_REASON_CODES: Final[frozenset[str]] = frozenset({AMENDMENT_PURPOSE_REASON_CODE})

#: The snapshot-level identities **R28** permits to differ transitively, because the
#: purpose difference propagates into them and into nothing else.
BRIDGE_ALLOWED_SNAPSHOT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "candidate_accession_table_sha256",
        "candidate_accession_reasons_sha256",
        "candidate_snapshot_sha256",
        "snapshot_id",
    }
)


@dataclass(frozen=True, slots=True)
class BridgeDifference:
    """One observed difference between the paired snapshots."""

    scope: str
    key: str
    field: str
    track_a: object
    track_b: object
    allowed: bool

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering for the rehearsal evidence."""
        return {
            "scope": self.scope,
            "key": self.key,
            "field": self.field,
            "track_a": None if self.track_a is None else str(self.track_a),
            "track_b": None if self.track_b is None else str(self.track_b),
            "allowed": self.allowed,
        }


@dataclass(frozen=True, slots=True)
class BridgeReport:
    """The mechanical **R28** verdict over one paired construction."""

    differences: tuple[BridgeDifference, ...]
    compared_scopes: tuple[str, ...]
    compared_rows: int

    @property
    def violations(self) -> tuple[BridgeDifference, ...]:
        """Differences outside the explicit allowlist. Any one of these fails R28."""
        return tuple(item for item in self.differences if not item.allowed)

    @property
    def passed(self) -> bool:
        """Whether every observed difference is inside the allowlist."""
        return not self.violations

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering of the whole verdict."""
        return {
            "passed": self.passed,
            "compared_scopes": list(self.compared_scopes),
            "compared_rows": self.compared_rows,
            "difference_count": len(self.differences),
            "violation_count": len(self.violations),
            "differences": [item.as_record() for item in self.differences],
        }


@dataclass(frozen=True, slots=True)
class PairedSnapshots:
    """Track A and Track B, built from one base case and mechanically bridged."""

    track_a_database: Path
    track_b_database: Path
    track_a: FrozenCandidateSnapshot
    track_b: FrozenCandidateSnapshot
    bridge: BridgeReport
    stipulated_categories: Mapping[str, str]


# --------------------------------------------------------------------------
# The overlay
# --------------------------------------------------------------------------


def apply_synthetic_amendment_purpose(
    derivation: CandidateDerivation,
    *,
    categories: Sequence[str] = AMENDMENT_PURPOSE_CATEGORIES,
) -> tuple[CandidateDerivation, Mapping[str, str]]:
    """Stipulate synthetic amendment-purpose facts on an already-derived snapshot.

    Applied **only** to accessions the production derivation already marked
    ``is_amendment`` with an ``unproven`` purpose level, so the overlay can never
    contradict the builder or reach a non-amendment row. Categories are assigned by
    position in the deterministic accession order, cycling through the three frozen
    Decision 014 §6 categories, so every category has a witness and two runs assign
    identically.

    The resolution digest is computed by the **production** identity functions over the
    **production** purpose evidence rows -- this fixture stipulates a classification,
    never a second hashing or contributor-membership rule.

    Returns the new derivation and the ``{accession_plain: category}`` map it stipulated.

    Raises:
        GateFailureError: a category outside the three frozen ones was requested, or the
            derivation carries no amendment to stipulate against.
    """
    unknown = sorted(set(categories) - set(AMENDMENT_PURPOSE_CATEGORIES))
    if unknown or not categories:
        message = (
            "the Track-B overlay may stipulate only Decision 014 §6's three frozen "
            f"amendment-purpose categories; received {list(categories)}"
        )
        raise GateFailureError(message)

    stipulated: dict[str, str] = {}
    accessions = []
    position = 0
    for draft in derivation.accessions:
        columns = dict(draft.columns)
        if not columns.get("is_amendment") or columns.get("amendment_purpose_category") is not None:
            accessions.append(draft)
            continue
        category = categories[position % len(categories)]
        position += 1
        plain = str(columns["accession_plain"])
        purpose_rows = [
            item.content() for item in draft.evidence if item.dimension == _PURPOSE_DIMENSION
        ]
        if not purpose_rows:
            message = (
                f"accession {plain!r} carries no amendment-purpose evidence row, so the "
                "rehearsal overlay has nothing to bind a stipulated category to"
            )
            raise GateFailureError(message)
        columns["amendment_purpose_category"] = category
        columns["amendment_purpose_evidence_level"] = "provisional"
        columns["amendment_purpose_quota_eligible"] = 1
        columns["amendment_purpose_resolution_sha256"] = resolution_sha256(
            dimension=_PURPOSE_DIMENSION,
            contributors=resolution_contributors(purpose_rows),
            evidence_policy_version=PILOT_EVIDENCE_POLICY_VERSION,
            classification={"amendment_purpose_category": category},
        )
        reasons = [entry for entry in draft.reasons if entry[1] != AMENDMENT_PURPOSE_REASON_CODE]
        accessions.append(replace(draft, columns=columns, reasons=reasons))
        stipulated[plain] = category
    if not stipulated:
        message = (
            "the Track-B overlay found no unproven amendment accession to stipulate a "
            "category on; the base case cannot exercise the amendment-purpose quota"
        )
        raise GateFailureError(message)
    return replace(derivation, accessions=accessions), dict(sorted(stipulated.items()))


# --------------------------------------------------------------------------
# Paired construction
# --------------------------------------------------------------------------


def build_paired_snapshots(
    *,
    source_database: Path,
    track_a_database: Path,
    track_b_database: Path,
    lock_root: Path,
    inputs: CandidateSnapshotInputs,
) -> PairedSnapshots:
    """Build both tracks from one census layer and bridge them before any selection.

    ``source_database`` is the disposable catalog the synthetic base case derived. It is
    copied twice so the two tracks are byte-independent siblings -- and so the two
    snapshots, which share a ``snapshot_id`` by construction (**OR-1** binds the
    coverage window, observation set, and policy versions, not the row content), never
    collide inside one catalog.
    """
    _copy_catalog(source_database, track_a_database)
    _copy_catalog(source_database, track_b_database)

    with CatalogWriter(track_a_database, lock_root / "a") as writer:
        derivation = derive_candidate_snapshot(writer.connection, inputs)
        track_a = persist_and_freeze_derivation(writer=writer, inputs=inputs, derivation=derivation)
    with CatalogWriter(track_b_database, lock_root / "b") as writer:
        base = derive_candidate_snapshot(writer.connection, inputs)
        overlaid, stipulated = apply_synthetic_amendment_purpose(base)
        track_b = persist_and_freeze_derivation(writer=writer, inputs=inputs, derivation=overlaid)

    bridge = compare_tracks(
        track_a_database,
        track_b_database,
        snapshot_a=track_a.snapshot_id,
        snapshot_b=track_b.snapshot_id,
    )
    return PairedSnapshots(
        track_a_database=track_a_database,
        track_b_database=track_b_database,
        track_a=track_a,
        track_b=track_b,
        bridge=bridge,
        stipulated_categories=stipulated,
    )


def _copy_catalog(source: Path, target: Path) -> None:
    """Copy one disposable catalog, through SQLite rather than through the filesystem.

    ``sqlite3``'s own backup API is used so a live write-ahead log cannot leave the copy
    inconsistent, which a byte copy of the main file alone could.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(source, writer=False) as origin, sqlite3.connect(target) as destination:
        origin.backup(destination)


# --------------------------------------------------------------------------
# The R28 bridge
# --------------------------------------------------------------------------

#: The five candidate row families compared row by row, with the key each is keyed on
#: and the frozen column tuple each is compared over. Using the **identity** column
#: tuples is deliberate: they are exactly the fields that reach a governed digest, so a
#: substantive divergence cannot hide in a column the bridge forgot to name.
_ROW_SCOPES: Final[tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...]] = (
    ("pilot_candidate_entities", "cik_numeric", ("cik_numeric",), ENTITY_TABLE_COLUMNS),
    (
        "pilot_candidate_accessions",
        "accession_plain",
        ("accession_plain",),
        ACCESSION_TABLE_COLUMNS,
    ),
    (
        "pilot_candidate_accession_registrants",
        "accession_plain|registrant_cik_numeric",
        ("accession_plain", "registrant_cik_numeric"),
        REGISTRANT_TABLE_COLUMNS,
    ),
    (
        "pilot_candidate_entity_evidence",
        "cik_numeric|classification_dimension|source_field|evidence_sha256",
        ("cik_numeric", "classification_dimension", "source_field", "evidence_sha256"),
        ENTITY_EVIDENCE_COLUMNS,
    ),
    (
        "pilot_candidate_accession_evidence",
        "accession_plain|classification_dimension|source_field|evidence_sha256",
        ("accession_plain", "classification_dimension", "source_field", "evidence_sha256"),
        ACCESSION_EVIDENCE_COLUMNS,
    ),
)

#: The snapshot-level fields compared directly. Everything not listed as permitted in
#: :data:`BRIDGE_ALLOWED_SNAPSHOT_FIELDS` must agree exactly.
_SNAPSHOT_FIELDS: Final[tuple[str, ...]] = (
    "accession_count",
    "candidate_accession_evidence_sha256",
    "candidate_accession_reasons_sha256",
    "candidate_accession_table_sha256",
    "candidate_entity_evidence_sha256",
    "candidate_entity_reasons_sha256",
    "candidate_entity_table_sha256",
    "candidate_policy_version",
    "candidate_registrant_table_sha256",
    "candidate_snapshot_sha256",
    "coverage_end",
    "coverage_policy_version",
    "coverage_start",
    "coverage_window_sha256",
    "entity_count",
    "evidence_policy_version",
    "include_open_quarter",
    "input_observation_set_sha256",
    "sic_family_mapping_version",
    "snapshot_id",
    "snapshot_state",
)


def compare_tracks(
    track_a_database: Path,
    track_b_database: Path,
    *,
    snapshot_a: str,
    snapshot_b: str,
) -> BridgeReport:
    """Mechanically compare the paired snapshots against **R28**'s explicit allowlist.

    Every substantive candidate fact not dependent on amendment-purpose evidence must be
    equivalent; the permitted differences are exactly the amendment-purpose
    classification, its evidence level, its quota eligibility, its resolution digest,
    its reason row, and the digests those propagate into. **Any other difference fails**,
    including a row present on one side and absent on the other.

    The comparison is run **before** any selection, which is what proves Track B did not
    quietly substitute an easier candidate universe.
    """
    differences: list[BridgeDifference] = []
    compared = 0
    with (
        connect(track_a_database, writer=False) as left,
        connect(track_b_database, writer=False) as right,
    ):
        for table, key_label, key_columns, columns in _ROW_SCOPES:
            rows_a = _rows(left, table, snapshot_a, key_columns, columns)
            rows_b = _rows(right, table, snapshot_b, key_columns, columns)
            compared += len(rows_a) + len(rows_b)
            for key in sorted(set(rows_a) | set(rows_b)):
                record_a = rows_a.get(key)
                record_b = rows_b.get(key)
                if record_a is None or record_b is None:
                    differences.append(
                        BridgeDifference(
                            scope=table,
                            key=f"{key_label}={key}",
                            field="<row presence>",
                            track_a="present" if record_a is not None else "absent",
                            track_b="present" if record_b is not None else "absent",
                            allowed=False,
                        )
                    )
                    continue
                for column in columns:
                    if record_a[column] == record_b[column]:
                        continue
                    allowed = (
                        table == "pilot_candidate_accessions"
                        and column in BRIDGE_ALLOWED_ACCESSION_COLUMNS
                    )
                    differences.append(
                        BridgeDifference(
                            scope=table,
                            key=f"{key_label}={key}",
                            field=column,
                            track_a=record_a[column],
                            track_b=record_b[column],
                            allowed=allowed,
                        )
                    )
        differences.extend(_reason_differences(left, right, snapshot_a, snapshot_b))
        differences.extend(_snapshot_differences(left, right, snapshot_a, snapshot_b))
    return BridgeReport(
        differences=tuple(differences),
        compared_scopes=(*(item[0] for item in _ROW_SCOPES), "reasons", "snapshot"),
        compared_rows=compared,
    )


def _rows(
    connection: sqlite3.Connection,
    table: str,
    snapshot_id: str,
    key_columns: Sequence[str],
    columns: Sequence[str],
) -> Mapping[str, Mapping[str, object]]:
    """Read one candidate family, keyed by its natural identity."""
    selected = ", ".join(sorted({*key_columns, *columns}))
    rows = connection.execute(
        f"SELECT {selected} FROM {table} WHERE snapshot_id = ?",  # noqa: S608 -- fixed allowlist
        (snapshot_id,),
    ).fetchall()
    return {"|".join(str(row[column]) for column in key_columns): dict(row) for row in rows}


def _reason_differences(
    left: sqlite3.Connection,
    right: sqlite3.Connection,
    snapshot_a: str,
    snapshot_b: str,
) -> list[BridgeDifference]:
    """Compare both reason families as sets, since a reason row is its own content."""
    differences: list[BridgeDifference] = []
    for table, owner in (
        ("pilot_candidate_entity_reasons", "cik_numeric"),
        ("pilot_candidate_accession_reasons", "accession_plain"),
    ):
        columns = (
            ENTITY_REASONS_COLUMNS
            if table == "pilot_candidate_entity_reasons"
            else ACCESSION_REASONS_COLUMNS
        )
        set_a = _reason_set(left, table, snapshot_a, columns)
        set_b = _reason_set(right, table, snapshot_b, columns)
        for entry in sorted(set_a ^ set_b):
            code = entry[-1]
            only_in_a = entry in set_a
            differences.append(
                BridgeDifference(
                    scope=table,
                    key=f"{owner}={entry[0]}",
                    field=f"{entry[1]}/{code}",
                    track_a="present" if only_in_a else "absent",
                    track_b="absent" if only_in_a else "present",
                    # R28 permits only the purpose reason, and only by being absent on
                    # the Track-B side: the stipulated category makes it untrue there.
                    allowed=code in BRIDGE_ALLOWED_REASON_CODES and only_in_a,
                )
            )
    return differences


def _reason_set(
    connection: sqlite3.Connection,
    table: str,
    snapshot_id: str,
    columns: Sequence[str],
) -> set[tuple[str, ...]]:
    selected = ", ".join(columns)
    return {
        tuple(str(row[column]) for column in columns)
        for row in connection.execute(
            f"SELECT {selected} FROM {table} WHERE snapshot_id = ?",  # noqa: S608
            (snapshot_id,),
        ).fetchall()
    }


def _snapshot_differences(
    left: sqlite3.Connection,
    right: sqlite3.Connection,
    snapshot_a: str,
    snapshot_b: str,
) -> list[BridgeDifference]:
    """Compare the two snapshot rows field by field."""
    selected = ", ".join(_SNAPSHOT_FIELDS)
    row_a = left.execute(
        f"SELECT {selected} FROM pilot_candidate_snapshots WHERE snapshot_id = ?",  # noqa: S608
        (snapshot_a,),
    ).fetchone()
    row_b = right.execute(
        f"SELECT {selected} FROM pilot_candidate_snapshots WHERE snapshot_id = ?",  # noqa: S608
        (snapshot_b,),
    ).fetchone()
    if row_a is None or row_b is None:
        message = "the R28 bridge requires both paired snapshots to exist"
        raise GateFailureError(message)
    return [
        BridgeDifference(
            scope="pilot_candidate_snapshots",
            key="snapshot",
            field=column,
            track_a=row_a[column],
            track_b=row_b[column],
            allowed=column in BRIDGE_ALLOWED_SNAPSHOT_FIELDS,
        )
        for column in _SNAPSHOT_FIELDS
        if row_a[column] != row_b[column]
    ]
