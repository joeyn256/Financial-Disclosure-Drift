"""D151-C31R2-R19A-C2 §41 (C28-MINOR-4): the successor charges Level Two at the Level-Two ratio.

With DISTINCT synthetic Level-One and Level-Two peak ratios and transient allowances, the
successor's pre-world admission record carries exactly the Level-Two arithmetic, every legacy
level-1 intermediate carries exactly the Level-One arithmetic, swapping the two terms moves the
admission identity and the StagePlan's storage-requirement identity, and no production ratio is
frozen anywhere. A Level-Two-to-Level-One substitution is therefore observable, which is what
the C28 MINOR-4 gap was about.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402

#: Two ratios that cannot be mistaken for each other, beside the two distinct transients.
DISTINCT = ct.MultipassStorageRequirements(
    internal_reserve_bytes=0,
    level_one_peak_ratio=1.0,
    level_two_peak_ratio=3.0,
    level_one_transient_bytes=c13.LEVEL_ONE_TRANSIENT_SENTINEL,
    level_two_transient_bytes=c13.LEVEL_TWO_TRANSIENT_SENTINEL,
)
SWAPPED = ct.MultipassStorageRequirements(
    internal_reserve_bytes=0,
    level_one_peak_ratio=3.0,
    level_two_peak_ratio=1.0,
    level_one_transient_bytes=c13.LEVEL_TWO_TRANSIENT_SENTINEL,
    level_two_transient_bytes=c13.LEVEL_ONE_TRANSIENT_SENTINEL,
)


def _admission(estate: r19.SuccessorWorld) -> dict[str, object]:
    path = estate.receipt_root / "admission-attempt-000.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["contract"] == cm.L2_STAGE_ADMISSION_CONTRACT
    return record  # type: ignore[no-any-return]


def test_c28m4_the_successor_admission_is_level_two_arithmetic_and_level_one_stays_level_one(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False, requirements=DISTINCT)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    record = _admission(estate)
    admission = record["admission"]
    assert isinstance(admission, dict)
    input_bytes = int(record["input_bytes"])  # type: ignore[call-overload]
    seed = int(record["seed_catalog_bytes"])  # type: ignore[call-overload]
    assert admission["level"] == ct.MERGE_LEVEL_TWO
    assert admission["peak_bytes"] == -(-input_bytes * 3.0 // 1) + seed
    assert admission["transient_bytes"] == c13.LEVEL_TWO_TRANSIENT_SENTINEL
    assert (
        admission["required_free_bytes"]
        == admission["peak_bytes"] + 0 + c13.LEVEL_TWO_TRANSIENT_SENTINEL
    )
    # The governed input is the manifest total of every intermediate: the governed aggregate.
    assert input_bytes == sum(r.manifest.total_bytes for r in estate.succ["intermediates"])
    # Every legacy level-1 intermediate was admitted at level one with the level-one terms.
    for receipt in estate.succ["intermediates"]:
        level_one = receipt.storage_admission
        assert level_one["level"] == ct.MERGE_LEVEL_ONE
        assert level_one["transient_bytes"] == c13.LEVEL_ONE_TRANSIENT_SENTINEL
    # The S0 unit binds the same admission, and the StagePlan seals the level-two requirement.
    unit = cm.AppliedUnit.from_row(r19.applied_units(estate.catalog)[0])
    assert unit.outcome_witness["admission"] == admission
    assert unit.outcome_witness["admission_identity"] == record["admission_identity"]
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    assert plan.body["storage_requirements"] == dict(DISTINCT.as_record())


def test_c28m4_swapping_the_two_terms_moves_the_admission_and_the_stage_plan_identity(
    tmp_path: Path,
) -> None:
    distinct = r19.prepare(tmp_path / "distinct", legacy=False, requirements=DISTINCT)
    swapped = r19.prepare(tmp_path / "swapped", legacy=False, requirements=SWAPPED)
    cm.run_successor_multipass_final(r19.production_request(distinct, stop_after="S0"))
    cm.run_successor_multipass_final(r19.production_request(swapped, stop_after="S0"))
    one, two = _admission(distinct), _admission(swapped)
    assert one["admission"]["peak_bytes"] > two["admission"]["peak_bytes"]  # type: ignore[index]
    assert one["admission"]["transient_bytes"] != two["admission"]["transient_bytes"]  # type: ignore[index]
    assert one["admission_identity"] != two["admission_identity"]
    first = cm._read_stored_stage_plan(r19.readonly(distinct.catalog))
    second = cm._read_stored_stage_plan(r19.readonly(swapped.catalog))
    assert first.body["storage_requirement_identity"] != second.body["storage_requirement_identity"]
    assert first.identity != second.identity
    # A run continued under the other requirement is a different StagePlan: refused, no mutation.
    with pytest.raises(cm.ChunkMultipassError, match="minimal StagePlan identity"):
        cm.run_successor_multipass_final(
            r19.production_request(
                distinct, stop_after="S1", storage_requirements=dict(SWAPPED.as_record())
            )
        )
    assert r19.stage_ids(distinct.catalog) == ["S0"]


def test_c28m4_no_production_ratio_or_transient_is_frozen() -> None:
    for name in (
        "MULTIPASS_LEVEL_ONE_PEAK_RATIO",
        "MULTIPASS_LEVEL_TWO_PEAK_RATIO",
        "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES",
        "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES",
    ):
        assert getattr(ct, name) is None, name
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()
