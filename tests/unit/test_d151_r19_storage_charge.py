"""D151-C31R2-R19A-C2 §19, §20, §37-§39: membership, provenance, and the storage charge.

* the accepted intermediate receipt's manifest is the SOLE governed-membership authority: the
  production helper takes the parsed receipt, requires the exact contract, re-derives the
  manifest, and returns exactly the six governed entries in canonical order; a seventh, a
  missing, an unknown, a nested or a duplicate entry, the receipt name and any request name are
  refused; no directory listing decides membership;
* the selected group request is bound as provenance only, by deterministic association with the
  selected attempt: it moves the StagePlan identity, never the governed manifest or the governed
  aggregate; a retained request of another attempt is legal and never selected; the two-attempt
  fixture (attempt-000 without a receipt, attempt-001 with the sole valid one) selects attempt 1;
* over five synthetic groups the full/receipt/request/governed counts are 40/5/5/30 and the
  governed byte sum is exactly the sum of the thirty manifest members;
* the storage definition carries the successor charge model beside the accepted method, the six
  persistent relations are world-volume objects, and every production storage value stays None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c17_storage_binding as c17  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    ArtifactManifest,
    build_artifact_manifest,
    file_sha256,
    write_once_json,
)

SIZES = {
    name: 100 + 37 * index for index, name in enumerate(cm.GOVERNED_INTERMEDIATE_MANIFEST_NAMES)
}


def _template(tmp_path: Path) -> dict[str, Any]:
    """A real intermediate receipt record, the template every synthetic receipt derives from."""
    estate = r19.prepare(tmp_path / "template", legacy=False)
    return dict(estate.succ["intermediates"][0].as_record())


def _synthetic_group(
    root: Path,
    template: dict[str, Any],
    group_id: str,
    ordinal: int,
    *,
    attempts: tuple[int, ...] = (0,),
    receipt_in: int | None = 0,
    salt: bytes = b"",
) -> None:
    """One synthetic group: request documents and attempt directories of the accepted shape."""
    for attempt in attempts:
        directory = root / group_id / f"attempt-{attempt:03d}"
        directory.mkdir(parents=True)
        for name in cm.GOVERNED_INTERMEDIATE_MANIFEST_NAMES:
            (directory / name).write_bytes(
                salt + f"{group_id}/{attempt}/{name}".encode() * SIZES[name]
            )
        request = root / group_id / f"{group_id}-{attempt:03d}-request.json"
        request.write_bytes(
            json.dumps({"group_id": group_id, "attempt": attempt, "salt": salt.hex()}).encode()
        )
        if receipt_in == attempt:
            manifest = build_artifact_manifest(
                directory, exclude=(cm.INTERMEDIATE_RECEIPT_FILENAME,)
            )
            record = {
                **template,
                "group_id": group_id,
                "group_ordinal": ordinal,
                "attempt": attempt,
                "manifest": dict(manifest.as_record()),
                "catalog_sha256": next(
                    e.sha256
                    for e in manifest.entries
                    if e.relative_path == "working_catalog.sqlite3"
                ),
            }
            write_once_json(directory / cm.INTERMEDIATE_RECEIPT_FILENAME, record)


def _resolved(root: Path, group_id: str, ordinal: int) -> cm.IntermediateInput:
    found = cm.completed_intermediate_receipt(root, group_id)
    assert found is not None
    receipt, directory = found
    return cm.IntermediateInput(
        group_id=group_id, ordinal=ordinal, region="primary", start=ordinal, end=ordinal + 1,
        directory=directory, receipt=receipt,
    )  # fmt: skip


# ==========================================================================
# The production membership helper
# ==========================================================================
def test_i01_the_helper_returns_exactly_the_six_governed_entries_in_canonical_order(
    tmp_path: Path,
) -> None:
    template = _template(tmp_path)
    root = tmp_path / "groups"
    _synthetic_group(root, template, "group-0000", 0)
    item = _resolved(root, "group-0000", 0)
    entries = cm._governed_intermediate_manifest_entries(item.receipt)
    assert [e.relative_path for e in entries] == list(cm.GOVERNED_INTERMEDIATE_MANIFEST_NAMES)
    assert entries == tuple(sorted(item.receipt.manifest.entries, key=lambda e: e.relative_path))
    # Manifest-entry order never changes the helper's output; the record still re-derives.
    shuffled = dict(item.receipt.as_record())
    manifest = dict(shuffled["manifest"])
    manifest["entries"] = list(reversed(manifest["entries"]))
    manifest["manifest_digest"] = ArtifactManifest.from_record(
        {"entries": manifest["entries"]}
    ).digest
    shuffled["manifest"] = manifest
    reordered = cm.IntermediateReceipt.from_record(shuffled)
    assert cm._governed_intermediate_manifest_entries(reordered) == entries
    # Governed bytes are the sum of the six members, and never the receipt or the request.
    directory = item.directory
    governed = sum(e.byte_length for e in entries)
    assert governed == sum(
        (directory / n).stat().st_size for n in cm.GOVERNED_INTERMEDIATE_MANIFEST_NAMES
    )
    assert governed == item.receipt.manifest.total_bytes


def test_i02_the_helper_refuses_every_broken_membership(tmp_path: Path) -> None:
    template = _template(tmp_path)
    root = tmp_path / "groups"
    _synthetic_group(root, template, "group-0000", 0)
    item = _resolved(root, "group-0000", 0)
    record = dict(item.receipt.as_record())

    def receipt_with(entries: list[dict[str, Any]], **changes: Any) -> cm.IntermediateReceipt:
        manifest = {
            "entries": entries,
            "manifest_digest": ArtifactManifest.from_record({"entries": entries}).digest,
        }
        return cm.IntermediateReceipt.from_record({**record, **changes, "manifest": manifest})

    base = [dict(e.as_record()) for e in item.receipt.manifest.entries]
    extra = {"relative_path": "seventh.txt", "byte_length": 1, "sha256": "0" * 64}
    cases = [
        ("exactly 6", base + [extra]),
        ("exactly 6 governed entries", base[:-1]),
        ("is not one of the governed names", base[:-1] + [extra]),
        (
            "never a governed member",
            base[:-1] + [{**extra, "relative_path": cm.INTERMEDIATE_RECEIPT_FILENAME}],
        ),
        (
            "never a governed member",
            base[:-1] + [{**extra, "relative_path": "group-0000-000-request.json"}],
        ),
        (
            "canonical basename",
            base[:-1] + [{**base[-1], "relative_path": "nested/" + base[-1]["relative_path"]}],
        ),
        (
            "canonical basename",
            base[:-1] + [{**base[-1], "relative_path": "/" + base[-1]["relative_path"]}],
        ),
        (
            "more than once",
            base[:-1] + [dict(base[0])],
        ),
    ]
    for message, entries in cases:
        with pytest.raises(cm.ChunkMultipassError, match=message):
            cm._governed_intermediate_manifest_entries(receipt_with(entries))
    with pytest.raises(cm.ChunkMultipassError, match="complete"):
        cm._governed_intermediate_manifest_entries(receipt_with(base, status="partial"))
    # An ALIEN contract: since Decision 151 made ``/2`` canonical this fixture names ``/3``, a
    # version no writer emits, so the refusal it exercises is still a real contract refusal.
    # Naming it here authorizes no ``/3`` implementation.
    with pytest.raises(cm.ChunkMultipassError, match="complete"):
        cm._governed_intermediate_manifest_entries(
            receipt_with(base, contract="m3.3-chunked-f0-intermediate-receipt/3")
        )
    # A directory listing is not membership: an extra file beside the six refuses the RESOLVER,
    # never widens the helper.
    (item.directory / "stray.txt").write_bytes(b"x")
    with pytest.raises(cm.ChunkMultipassError, match="does not verify"):
        cm.completed_intermediate_receipt(root, "group-0000")


# ==========================================================================
# Five groups, the two-attempt fixture, provenance
# ==========================================================================
def test_i03_five_synthetic_groups_count_40_5_5_30_and_the_governed_sum_is_exact(
    tmp_path: Path,
) -> None:
    template = _template(tmp_path)
    root = tmp_path / "groups"
    for ordinal in range(5):
        _synthetic_group(root, template, f"group-{ordinal:04d}", ordinal, salt=bytes([ordinal]))
    files = [p for p in root.rglob("*") if p.is_file()]
    receipts = [p for p in files if p.name == cm.INTERMEDIATE_RECEIPT_FILENAME]
    requests = [p for p in files if p.name.endswith("-request.json")]
    assert (len(files), len(receipts), len(requests)) == (40, 5, 5)
    descriptors = [_descriptor(root, ordinal) for ordinal in range(5)]
    governed = [e for d in descriptors for e in d["governed_entries"]]
    assert len(governed) == 30
    governed_files = [p for p in files if p.name in cm.GOVERNED_INTERMEDIATE_MANIFEST_NAMES]
    assert sum(d["governed_bytes"] for d in descriptors) == sum(
        p.stat().st_size for p in governed_files
    )
    assert sum(d["governed_bytes"] for d in descriptors) + sum(
        p.stat().st_size for p in receipts + requests
    ) == sum(p.stat().st_size for p in files)
    for descriptor in descriptors:
        names = [e["relative_path"] for e in descriptor["governed_entries"]]
        assert names == list(cm.GOVERNED_INTERMEDIATE_MANIFEST_NAMES)
        provenance = descriptor["group_request_provenance"]
        assert provenance["governed_manifest_member"] is False
        assert provenance["governed_aggregate_member"] is False
        assert provenance["successor_semantic_input"] is False
        assert provenance["provenance_bound"] is True
        assert provenance["relative_filename"] == f"{descriptor['group_id']}-000-request.json"
    # Enumeration order does not change a descriptor.
    assert [_descriptor(root, o) for o in reversed(range(5))][::-1] == descriptors


def _descriptor(root: Path, ordinal: int) -> dict[str, Any]:
    return dict(
        cm._successor_intermediate_descriptor(_resolved(root, f"group-{ordinal:04d}", ordinal))
    )


def test_i04_the_two_attempt_fixture_selects_attempt_001_and_binds_its_request_only(
    tmp_path: Path,
) -> None:
    template = _template(tmp_path)
    root = tmp_path / "groups"
    # attempt-000 has NO receipt (residue only); attempt-001 carries the sole valid terminal.
    _synthetic_group(root, template, "group-0000", 0, attempts=(0, 1), receipt_in=1)
    (root / "group-0000" / "attempt-000" / "partial.txt").write_bytes(b"interrupted")
    found = cm.completed_intermediate_receipt(root, "group-0000")
    assert found is not None and found[0].attempt == 1 and found[1].name == "attempt-001"
    descriptor = _descriptor(root, 0)
    assert descriptor["attempt"] == 1
    assert (
        descriptor["group_request_provenance"]["relative_filename"] == "group-0000-001-request.json"
    )
    selected = root / "group-0000" / "group-0000-001-request.json"
    other = root / "group-0000" / "group-0000-000-request.json"
    assert descriptor["group_request_provenance"]["sha256"] == file_sha256(selected)[0]
    assert descriptor["group_request_provenance"]["sha256"] != file_sha256(other)[0]
    # Changing only the non-selected request changes nothing; changing the selected one moves
    # the provenance -- and nothing else: the governed manifest and aggregate are untouched.
    other.write_bytes(other.read_bytes() + b"\n")
    assert _descriptor(root, 0) == descriptor
    selected.write_bytes(selected.read_bytes() + b"\n")
    moved = _descriptor(root, 0)
    assert moved != descriptor
    assert (
        moved["group_request_provenance"]["sha256"]
        != descriptor["group_request_provenance"]["sha256"]
    )
    assert moved["manifest_digest"] == descriptor["manifest_digest"]
    assert moved["governed_bytes"] == descriptor["governed_bytes"]
    assert moved["governed_entries"] == descriptor["governed_entries"]
    # A missing selected request, or a link standing in for it, refuses.
    selected.unlink()
    with pytest.raises(cm.ChunkMultipassError, match="is absent"):
        _descriptor(root, 0)
    selected.symlink_to(other)
    with pytest.raises(cm.ChunkMultipassError, match="not a regular file"):
        _descriptor(root, 0)


def test_i05_on_a_real_estate_the_selected_request_moves_the_stage_plan_identity_only(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    proof = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )
    before = cm._resolve_successor_context(r19.production_request(estate), proof).stage_plan
    root = Path(estate.succ["intermediates_root"])
    group = estate.schedule.groups[0]
    retained = root / group.group_id / f"{group.group_id}-003-request.json"
    retained.write_bytes(b"{}")
    unchanged = cm._resolve_successor_context(r19.production_request(estate), proof).stage_plan
    assert unchanged.identity == before.identity
    selected = root / group.group_id / f"{group.group_id}-000-request.json"
    selected.write_bytes(selected.read_bytes() + b"\n")
    after = cm._resolve_successor_context(r19.production_request(estate), proof).stage_plan
    assert after.identity != before.identity
    assert after.body["governed_input_bytes"] == before.body["governed_input_bytes"]
    assert [d["manifest_digest"] for d in after.intermediates] == [
        d["manifest_digest"] for d in before.intermediates
    ]


# ==========================================================================
# The storage charge
# ==========================================================================
def test_i06_the_definition_carries_both_regimes_and_the_successor_relations_are_world_objects(
    tmp_path: Path,
) -> None:
    definition, overall, legacy, successor = c17.level_two_definition_slices()
    assert c17.LEGACY_SENTINEL in definition and c17.SUCCESSOR_SENTINEL in definition
    assert definition.index(c17.LEGACY_SENTINEL) < definition.index(c17.SUCCESSOR_SENTINEL)
    for name in cm.L2_PERSISTENT_RELATIONS:
        assert c17._has_token(successor, name) and not c17._has_token(legacy, name), name
    for name in c17.LEGACY_LEVEL_TWO_RELATIONS:
        assert c17._has_token(legacy, name) and not c17._has_token(successor, name), name
    prose = c17._slice_prose(successor)
    assert "WORLD-VOLUME growth" in prose and "SQLITE_TMPDIR volume" in prose
    assert c17.SUCCESSOR_METHOD_BINDING in prose
    for fragment in c17.DANGLING_BACKREFERENCES:
        assert fragment not in c17._slice_prose(definition), fragment
    assert (
        ct.MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES is None and ct.MULTIPASS_LEVEL_TWO_PEAK_RATIO is None
    )
    # Behaviourally: the six relations are pages of the world's main file, on the world volume.
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate))
    connection = r19.readonly(estate.catalog)
    try:
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM main.sqlite_master WHERE type = 'table'"
            )
        }
        databases = [str(row["file"]) for row in connection.execute("PRAGMA database_list")]
    finally:
        connection.close()
    assert set(cm.L2_PERSISTENT_RELATIONS) <= tables
    assert databases == [str(estate.catalog)]
    assert r19.count(estate.catalog, cm.L2_PLAN_WITNESS_TABLE) > 0


def test_i07_no_committed_r19_test_reads_the_live_campaign_estate() -> None:
    here = Path(__file__).parent
    for path in sorted(here.glob("test_d151_r19_*.py")):
        source = path.read_text(encoding="utf-8")
        for needle in ("m3-run" + "-data", "m3-run" + "-logs", "/Users/" + "joeyn256"):
            assert needle not in source, (path.name, needle)
