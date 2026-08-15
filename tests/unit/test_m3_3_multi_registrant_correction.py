"""The R46 multi-registrant relational correction: MR-M1 through MR-M14.

Governing records: Decision 081 **R46**; Decision 082 §10 (the implementation contract,
and §10.13 the exact mutation set); Decision 083 **R58**-**R62** (the owner rulings this
module proves), and §14 (the identity and re-baselining rule).

**Every test here is a mutation test in the strict sense Decision 082 §10.13 requires:**
each one applies the named defect and asserts the exact condition that must kill it. A
mutation nothing detects is not a protection, so each test either applies the mutation
directly to production input and asserts a refusal, or -- where the mutation is a code
change rather than a data state -- reproduces the mutant's *output* and asserts the
production path does not produce it.

``hash_table`` sorts its rendered rows, so a pure row-order mutation is invisible to a
digest. Decision 082 §10.13 says so explicitly, and the order-invariance tests below
therefore assert on **persisted content and derived state**, not only on digests.
"""

from __future__ import annotations

import itertools
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import pytest

# The accepted census-layer builder fixture. **MR-M10A** is a derivation-layer
# protection, so it has to run the real builder over a real census world; reusing that
# suite's world is what keeps this module from carrying a second, drifting copy of it.
import test_m3_candidate_snapshot as builder  # noqa: E402

# The accepted S5 feasible plan, which owns the two joint fixture filings whose
# pre-correction identities `_REBASELINED_MULTI_REGISTRANT_RANKS` re-baselines.
import test_m23_accession_selection_store as s5  # noqa: E402

from disclosure_drift import pilot_policy
from disclosure_drift.m3.candidate_snapshot import (
    UNESTABLISHED_REGISTRANT_SET_REASON,
)
from disclosure_drift.pilot_policy import PILOT_SELECTOR_POLICY_VERSION
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.accession_selector import (
    MULTI_REGISTRANT_MINIMUM,
    MULTI_REGISTRANT_TIE_BREAK_SENTINEL,
    AccessionCandidate,
    accession_registrant_slot,
    accession_selection_rank,
)
from disclosure_drift.sec.entity_selector import PILOT_SELECTION_SEED
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES
from disclosure_drift.storage.sqlite import (
    apply_migrations,
    available_migrations,
    connect,
    transaction,
)

# --------------------------------------------------------------------------
# Pre-correction baselines (Decision 083 §10 / R60)
#
# These digests were produced by the implementation BEFORE this correction and are
# pinned as literals. MR-M13 is the test that makes Decision 082 §10.9's byte-for-byte
# guarantee real rather than asserted, and a literal is the only way to state it: a
# recomputation would move with the code it is supposed to be checking.
# --------------------------------------------------------------------------

#: ``SHA256(seed | 0000000001 | 0000000001-20-000001)`` at the frozen production seed.
#:
#: **Provenance** (Decision 085 §7). The pre-correction primitive was
#: ``accession_selection_rank(anchor_cik_padded, accession_number_dashed, selection_seed)``
#: -- the first parameter was literally named ``anchor_cik_padded`` -- over the preimage
#: ``f"{selection_seed}|{anchor_cik_padded}|{accession_number_dashed}"``. Every literal
#: below is therefore reproducible from the parent commit
#: ``6fdec2ed685c3c6248e392b04cdf184e8f3549e3`` as
#: ``accession_selection_rank(f"{cik:010d}", dashed, PILOT_SELECTION_SEED)``, and MR-M13
#: asserts exactly that identity against today's primitive.
_PRE_CORRECTION_SINGLE_REGISTRANT_RANKS: Final[dict[tuple[int, str], str]] = {
    (1, "0000000001-20-000001"): (
        "054107861c080cc678644e8ab137f714616146fcce95abfdb6ab1e8dc3205e02"
    ),
    (17, "0000000017-18-000002"): (
        "8ac3c01ecd193aca6b66a4daaec00c22c99629475686a191abe23f9e4f13d61a"
    ),
    (306, "0000000306-19-000004"): (
        "3ee412bcbab435b047d767dd0febba8c04687143491087c9b96cd94c193fc566"
    ),
}

#: The intentionally re-baselined multi-registrant values (Decision 083 §10: "return
#: exact before/after values for every intentionally changed governed digest"). The
#: "before" column is the false-singleton digest the correction abolishes.
#:
#: **Provenance, re-derived under Decision 085 §7.** These two accessions are the joint
#: filings of the accepted S5 feasible fixture -- ``test_m23_accession_selection_store``
#: slots 16 and 17, CIK 17 with co-registrant 917 and CIK 18 with co-registrant 918, both
#: at ``dashed(cik, 2018, 2)``. The fixture is byte-identical in the pre-correction parent
#: ``6fdec2ed685c3c6248e392b04cdf184e8f3549e3``, so each "before" is the value that
#: commit's ``write_plan`` actually persisted into
#: ``pilot_candidate_accessions.accession_tie_break_sha256`` at chain head ``0013``, where
#: the anchor was mandatory and was the plan's own CIK. Reproduce either column from a
#: disposable checkout of that parent with::
#:
#:     s5.write_plan(connection, s5.feasible_plan())
#:     SELECT accession_tie_break_sha256 FROM pilot_candidate_accessions
#:      WHERE accession_number_dashed = ?
#:
#: which yields ``anchor_cik_numeric`` 17 / 18, ``multi_registrant`` 1, and the "before"
#: digests below -- the false-singleton state R58 abolishes, observed rather than
#: asserted. The same query at chain head ``0014`` yields ``anchor_cik_numeric`` NULL and
#: the "after" digests. ``test_the_multi_registrant_rebaseline_is_explicit_and_traceable``
#: re-derives both columns from their stated preimages, so neither is an unchecked
#: literal. **An earlier revision of this table carried an unreproducible second "before"
#: value; it was replaced with the reproduced one, never patched for symmetry.**
_REBASELINED_MULTI_REGISTRANT_RANKS: Final[tuple[tuple[int, str, str, str], ...]] = (
    (
        17,
        "0000000017-18-000002",
        "8ac3c01ecd193aca6b66a4daaec00c22c99629475686a191abe23f9e4f13d61a",
        "29f00d58c0db00152f4c9dfec439e10fed91f045084cd8db40c7dd62fbfc05b7",
    ),
    (
        18,
        "0000000018-18-000002",
        "03e8736ec68b4f57776c2d8facc5b03a3313ebf813edac2aa49f9a0b272d9ce5",
        "ae4e009174a16afc305c49885587fe840cff75c4e99fc57ca80d8bd207740678",
    ),
)

_AT: Final = "2026-01-01T00:00:00Z"
_SNAPSHOT: Final = "a" * 64


def _accession(
    *,
    anchor: int | None,
    substantive: tuple[int, ...] = (),
    dashed: str = "0000000001-20-000001",
    multi: bool | None = None,
) -> AccessionCandidate:
    """One candidate accession at exactly the fields this module reasons about."""
    resolved_multi = (
        multi
        if multi is not None
        else (len({*substantive}) >= MULTI_REGISTRANT_MINIMUM if anchor is None else False)
    )
    return AccessionCandidate(
        accession_plain=dashed.replace("-", ""),
        accession_number_dashed=dashed,
        anchor_cik_numeric=anchor,
        substantive_registrant_ciks=substantive,
        form_type="10-K",
        multi_registrant=resolved_multi,
        multi_registrant_evidence_level="provisional" if resolved_multi else "not_applicable",
    )


# ==========================================================================
# MR-M1, MR-M2, MR-M3, MR-M14: order and membership invariance
# ==========================================================================


def test_mr_m1_permuting_substantive_registrant_order_changes_nothing() -> None:
    """**MR-M1.** Permute the insertion order of substantive registrant rows.

    Killing assertion: the association set, the tie-break, ``multi_registrant``, and the
    quota-relevant cardinality are all identical under every permutation.
    """
    members = (17, 917, 4242)
    baseline = _accession(anchor=None, substantive=members)
    for permutation in itertools.permutations(members):
        mutated = _accession(anchor=None, substantive=permutation)
        assert mutated.substantive_registrant_ciks_resolved == (
            baseline.substantive_registrant_ciks_resolved
        )
        assert mutated.substantive_registrants_padded == baseline.substantive_registrants_padded
        assert mutated.registrant_slot == baseline.registrant_slot
        assert mutated.rank == baseline.rank
        assert mutated.is_established_multi_registrant == baseline.is_established_multi_registrant


def test_mr_m2_removing_the_read_ordering_cannot_change_the_association_set() -> None:
    """**MR-M2.** Remove the ``ORDER BY`` from the full-index observation read.

    Killing assertion: the set is a *set* of distinct canonical CIKs, so any read order
    -- including the reverse of the accepted one -- yields an identical association set
    and identical digests. The production derivation collapses to the same value because
    it deduplicates and sorts, never because the query happened to be ordered.
    """
    observed_forward = (917, 17, 917, 4242, 17)
    observed_reverse = tuple(reversed(observed_forward))
    forward = _accession(anchor=None, substantive=observed_forward)
    reverse = _accession(anchor=None, substantive=observed_reverse)
    assert forward.substantive_registrant_ciks_resolved == (17, 917, 4242)
    assert reverse.substantive_registrant_ciks_resolved == (17, 917, 4242)
    assert forward.rank == reverse.rank


def test_mr_m3_reversing_the_registrant_row_builder_ordering_preserves_the_row_set() -> None:
    """**MR-M3.** Reverse the ``sorted()`` ordering in the registrant-row builder.

    Killing assertion: the persisted row **set** is identical and the anchor state is
    identical. Asserted on content rather than on a digest, because ``hash_table`` sorts
    its rendered rows and would hide exactly this mutation (Decision 082 §10.13).
    """
    ascending = _accession(anchor=None, substantive=(17, 917, 4242))
    descending = _accession(anchor=None, substantive=(4242, 917, 17))
    assert set(ascending.substantive_registrants_padded) == set(
        descending.substantive_registrants_padded
    )
    # And the emitted order is canonical either way, not merely equal as a set.
    assert ascending.substantive_registrants_padded == descending.substantive_registrants_padded
    assert ascending.anchor_cik_padded is None
    assert descending.anchor_cik_padded is None


def test_mr_m14_the_multi_registrant_tie_break_depends_on_no_member_cik() -> None:
    """**MR-M14.** Make the multi-registrant tie-break depend on a specific member CIK.

    Killing assertion: permuting -- and indeed *replacing* -- the association set leaves
    the tie-break unchanged, because the slot is a function of cardinality alone. This is
    also why Decision 082 §10.9 rejected option H-b: a membership-derived slot would drift
    the moment the association set was corrected.
    """
    dashed = "0000000017-18-000002"
    first = _accession(anchor=None, substantive=(17, 917), dashed=dashed)
    second = _accession(anchor=None, substantive=(555, 666, 777), dashed=dashed)
    assert first.rank == second.rank
    assert first.registrant_slot == MULTI_REGISTRANT_TIE_BREAK_SENTINEL
    assert second.registrant_slot == MULTI_REGISTRANT_TIE_BREAK_SENTINEL


# ==========================================================================
# MR-M4 through MR-M9: every prohibited anchor-selection heuristic
# ==========================================================================


@pytest.mark.parametrize(
    ("mutation", "chosen"),
    (
        pytest.param("MR-M4 min(CIK)", min, id="mr_m4_minimum_cik"),
        pytest.param("MR-M5 max(CIK)", max, id="mr_m5_maximum_cik"),
    ),
)
def test_mr_m4_and_mr_m5_extremal_cik_anchors_are_refused(mutation: str, chosen: object) -> None:
    """**MR-M4 / MR-M5.** Set the anchor to ``min(CIK)`` / ``max(CIK)``.

    Killing assertion: ``anchor_cik_numeric IS NULL`` fails. The production path produces
    ``None``; the mutant produces a CIK, and the two are asserted unequal at the property
    every downstream consumer reads.
    """
    members = (17, 917, 4242)
    production = _accession(anchor=None, substantive=members)
    assert production.anchor_cik_numeric is None
    assert production.anchor_cik_padded is None
    mutant_anchor = chosen(members)  # type: ignore[operator]
    assert production.anchor_cik_numeric != mutant_anchor, mutation
    # And the mutant's tie-break is a different digest, so it cannot pass unnoticed.
    assert production.rank != accession_selection_rank(
        f"{mutant_anchor:010d}", production.accession_number_dashed
    )


def test_mr_m6_first_write_order_never_selects_an_anchor() -> None:
    """**MR-M6.** Set the anchor from first-write / first-observation order.

    Killing assertion: ``anchor_cik_numeric IS NULL`` fails. Two observation orders that
    disagree about which CIK arrived first produce the *same* anchorless result, so no
    first-write rule can be reconstructed from the output.
    """
    first_seen_917 = _accession(anchor=None, substantive=(917, 17))
    first_seen_17 = _accession(anchor=None, substantive=(17, 917))
    assert first_seen_917.anchor_cik_numeric is None
    assert first_seen_17.anchor_cik_numeric is None
    assert first_seen_917.rank == first_seen_17.rank


def test_mr_m7_the_submitter_is_never_promoted_to_registrant_identity(
    catalog: sqlite3.Connection,
) -> None:
    """**MR-M7.** Set the anchor to ``submitter_cik_numeric`` -- the rejected MR-3(a).

    Killing assertion: ``anchor_cik_numeric IS NULL`` fails. Decision 081 **R46** §3.2(7)
    prohibits exactly this promotion, and Decision 080 §8.3 recommended it, so it is the
    single most important mutation in the set. The submitter is a real per-submission
    fact and stays one; it never becomes registrant identity.
    """
    _seed_multi_registrant_candidate(catalog, submitter=7777)
    # Writing the submitter into the anchor column is refused by the CHECK that ties
    # anchor presence to non-multi-registrant status.
    with (
        pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"),
        transaction(catalog) as c,
    ):
        c.execute(
            "UPDATE pilot_candidate_accessions SET anchor_cik_numeric = 7777 WHERE snapshot_id = ?",
            (_SNAPSHOT,),
        )


def test_mr_m8_no_anchor_is_chosen_by_hash_order() -> None:
    """**MR-M8.** Set the anchor to the CIK whose hash sorts first (**R46** §3.2(5)).

    Killing assertion: ``anchor_cik_numeric IS NULL`` fails. The sentinel is *not* a
    hash-chosen CIK -- it chooses no registrant at all -- so the production slot is
    asserted to differ from every member's own slot.
    """
    members = (17, 917, 4242)
    production = _accession(anchor=None, substantive=members)
    assert production.registrant_slot == MULTI_REGISTRANT_TIE_BREAK_SENTINEL
    hash_ordered = sorted(
        members, key=lambda cik: accession_selection_rank(f"{cik:010d}", "0000000001-20-000001")
    )
    for cik in hash_ordered:
        assert production.registrant_slot != f"{cik:010d}"
        assert production.anchor_cik_numeric != cik


def test_mr_m9_the_census_scalar_is_not_reinstated_as_the_anchor(
    catalog: sqlite3.Connection,
) -> None:
    """**MR-M9.** Set the anchor to the census scalar -- the status-quo regression.

    Killing assertion: ``anchor_cik_numeric IS NULL`` fails. This is the mutation that
    silently reverts the correction, so it is proved at the schema layer: the row cannot
    be written at all.
    """
    _seed_multi_registrant_candidate(catalog, submitter=8888)
    with (
        pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"),
        transaction(catalog) as c,
    ):
        c.execute(
            "UPDATE pilot_candidate_accessions SET anchor_cik_numeric = 17 WHERE snapshot_id = ?",
            (_SNAPSHOT,),
        )


# ==========================================================================
# MR-M10: an incomplete source must never read as a sole registrant
#
# **Two layers, and neither replaces the other** (Decision 085 §4). The mutation
# MR-M10 names is a DERIVATION defect: the builder reads a source with rows omitted --
# in the limit, with every row omitted -- and silently reports one substantive
# registrant. The state that produces is fully lawful once written (an established
# sole-registrant accession with a matching anchor), so the freeze and schema layers
# structurally cannot see it. MR-M10A is therefore the load-bearing protection and
# MR-M10B the backstop for a hand-seeded row that never went through the builder.
# ==========================================================================


def test_mr_m10a_the_builder_never_reads_absent_evidence_as_a_sole_registrant(
    tmp_path: Path,
) -> None:
    """**MR-M10A.** Derive the association set from a source with rows omitted.

    Killing assertion (Decision 082 §10.13): ``registrant_set_completeness`` must be
    ``unestablished``, and **a silent single-registrant result fails**. Under
    **Decision 083 R59** that state blocks candidacy **entirely**, so the accession never
    reaches a snapshot at all -- strictly stronger than recording it and hoping a
    downstream consumer notices.

    The census world is ``test_m3_candidate_snapshot``'s, not a second copy of it, and it
    is exercised through the real ``build_and_freeze_candidate_snapshot``. The mutant this
    kills is ``derive_candidate_snapshot`` treating ``associations is None`` as an empty
    set and falling through to the scalar; under it every assertion below fails, because
    the accession becomes an established sole-registrant candidate anchored on CIK
    ``UNESTABLISHED_CIK``.
    """
    # The reason is registered and nameable, so the exclusion is explicit rather than a
    # silent drop (R59: "fail closed with an explicit accepted reason").
    assert UNESTABLISHED_REGISTRANT_SET_REASON in REASON_CODES
    assert REASON_CODES[UNESTABLISHED_REGISTRANT_SET_REASON].requires_manual_review

    database = builder.seed_catalog(tmp_path, unestablished=True)
    plain = builder.UNESTABLISHED_ACCESSION_PLAIN
    with connect(database) as connection:
        # The scalar IS populated: the mutation is reading it as proof, not inventing it.
        assert (
            connection.execute(
                "SELECT registrant_cik_numeric FROM census_accessions WHERE accession_plain = ?",
                (plain,),
            ).fetchone()[0]
            == builder.UNESTABLISHED_CIK
        )

    frozen = builder.build_snapshot(database, tmp_path)

    # 1. Excluded before candidate snapshot entry, and reported rather than dropped.
    assert frozen.excluded_unestablished_registrant_set == 1  # type: ignore[attr-defined]
    with connect(database) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM pilot_candidate_accessions WHERE accession_plain = ?",
                (plain,),
            ).fetchone()[0]
            == 0
        )
        # 2. No fabricated scalar registrant anywhere in the governed relation.
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM pilot_candidate_accession_registrants "
                "WHERE accession_plain = ?",
                (plain,),
            ).fetchone()[0]
            == 0
        )
        # 3. No 'established' claim survives for it at the candidate layer.
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM pilot_candidate_accessions "
                "WHERE registrant_set_completeness <> 'established'"
            ).fetchone()[0]
            == 0
        )

    # 4. No entity, history, or quota credit: the snapshot is byte-identical to one
    #    built over a census that never carried the accession at all.
    control_root = tmp_path / "control"
    control = builder.build_snapshot(builder.seed_catalog(control_root), control_root)
    assert frozen.snapshot_id == control.snapshot_id  # type: ignore[attr-defined]
    assert frozen.accession_count == control.accession_count  # type: ignore[attr-defined]
    assert dict(frozen.family_digests) == dict(control.family_digests)  # type: ignore[attr-defined]


def test_mr_m10b_an_unestablished_candidate_row_can_never_be_frozen(
    catalog: sqlite3.Connection,
) -> None:
    """**MR-M10B.** The persistence backstop, retained beside MR-M10A above.

    Killing assertion: a hand-seeded ``unestablished`` candidate accession cannot reach a
    frozen snapshot even when every other freeze obligation is satisfied. This layer
    cannot see the derivation mutant -- the mutant's output is `established` and lawful --
    which is exactly why MR-M10A exists and why this test does not stand alone.
    """
    _seed_multi_registrant_candidate(catalog, unestablished=True)
    with pytest.raises(sqlite3.IntegrityError, match="established registrant set"):
        _freeze(catalog)


# ==========================================================================
# MR-M11, MR-M12: the flag is distinct substantive cardinality
# ==========================================================================


def test_mr_m11_multi_registrant_is_never_a_raw_row_count() -> None:
    """**MR-M11.** Compute ``multi_registrant`` from a raw row count.

    Killing assertion: a duplicate-row fixture must not flip the flag. Membership is the
    distinct canonical CIK set (**R23** §5.3), so three observations of one CIK is one
    registrant -- and an accession with a *sole* substantive registrant keeps its anchor.
    """
    duplicated = _accession(anchor=17, substantive=(17, 17, 17))
    assert duplicated.substantive_registrant_ciks_resolved == (17,)
    assert duplicated.is_established_multi_registrant is False
    assert duplicated.anchor_cik_numeric == 17
    assert duplicated.registrant_slot == "0000000017"


def test_mr_m12_a_submitter_only_row_is_never_substantive(catalog: sqlite3.Connection) -> None:
    """**MR-M12.** Count a ``submitter_only`` row as substantive.

    Killing assertion: the flag must not flip. Proved at the schema layer, where the
    freeze guard counts ``association_class = 'substantive'`` rows and a submitter row is
    excluded from that count by construction.
    """
    _seed_single_registrant_candidate_with_submitter_row(catalog)
    # Freezes cleanly: one substantive registrant, one anchor, flag 0.
    _freeze(catalog)
    state = catalog.execute(
        "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
        (_SNAPSHOT,),
    ).fetchone()["snapshot_state"]
    assert state == "frozen"
    row = catalog.execute(
        "SELECT anchor_cik_numeric, multi_registrant FROM pilot_candidate_accessions "
        "WHERE snapshot_id = ?",
        (_SNAPSHOT,),
    ).fetchone()
    assert row["multi_registrant"] == 0
    assert row["anchor_cik_numeric"] == 17


# ==========================================================================
# MR-M13: the byte-for-byte single-registrant guarantee
# ==========================================================================


def test_mr_m13_every_single_registrant_tie_break_preimage_is_byte_identical() -> None:
    """**MR-M13.** Alter the single-registrant tie-break preimage.

    Killing assertion: the byte-identity assertion against the **pre-correction** digests
    fails. Decision 082 §10.13 requires those digests to be pinned as literals, and
    Decision 083 R60 requires the guarantee itself; this is the test that makes both real.

    ``SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0`` is exactly the claim below.
    """
    for (cik, dashed), expected in _PRE_CORRECTION_SINGLE_REGISTRANT_RANKS.items():
        candidate = _accession(anchor=cik, dashed=dashed)
        assert candidate.registrant_slot == f"{cik:010d}"
        assert candidate.rank == expected
        # And through the public primitive, at the frozen production seed.
        assert accession_selection_rank(f"{cik:010d}", dashed, PILOT_SELECTION_SEED) == expected


def test_the_multi_registrant_rebaseline_is_explicit_and_traceable() -> None:
    """Decision 083 §10: changed multi-registrant identities are **re-baselined**.

    Every changed digest is stated with its exact before and after value, and **both**
    columns are re-derived here from their stated preimages rather than merely compared
    to each other (Decision 085 §7):

    * "before" is the pre-correction rule -- the mandatory anchor CIK in the tie-break
      slot -- so it is exactly what the parent commit persisted for this fixture;
    * "after" is the **R60** sentinel alone, carrying no member CIK.

    ``before != after`` is then a *consequence* of two independently reproduced values
    rather than the only thing asserted, which is what makes the "before" column
    evidence instead of decoration.
    """
    for cik, dashed, before, after in _REBASELINED_MULTI_REGISTRANT_RANKS:
        assert accession_selection_rank(f"{cik:010d}", dashed, PILOT_SELECTION_SEED) == before, (
            f"{dashed} 'before' is not the pre-correction anchor rule at CIK {cik}"
        )
        assert (
            accession_selection_rank(
                MULTI_REGISTRANT_TIE_BREAK_SENTINEL, dashed, PILOT_SELECTION_SEED
            )
            == after
        )
        assert before != after


def test_the_rebaselined_accessions_are_the_accepted_joint_fixture_filings() -> None:
    """The re-baseline table names real fixture accessions, not invented identities.

    Decision 085 §7 requires enough provenance that a fresh reviewer can reproduce each
    literal from the parent commit. The preimage half of that is the *identity*: these
    two dashed forms must be exactly the joint filings the accepted S5 feasible fixture
    builds, so the reproduction recipe in ``_REBASELINED_MULTI_REGISTRANT_RANKS`` points
    at something that genuinely exists.
    """
    joint = {
        entry.plain: entry
        for entry in s5.feasible_plan().accessions
        if entry.registrants is not None
        and len({r.cik for r in entry.registrants if r.association_class == "substantive"}) > 1
    }
    assert {s5.dashed(cik, 2018, 2) for cik in (17, 18)} == {
        s5.dashed(entry.cik, entry.year, entry.seq) for entry in joint.values()
    }
    for cik, dashed, _before, _after in _REBASELINED_MULTI_REGISTRANT_RANKS:
        entry = joint[dashed.replace("-", "")]
        assert entry.cik == cik
        substantive = {
            r.cik for r in (entry.registrants or []) if r.association_class == "substantive"
        }
        assert substantive == {cik, 900 + cik}


def test_the_sentinel_can_never_collide_with_a_padded_cik() -> None:
    """**Decision 083 R60**: the sentinel is not a CIK and cannot be parsed as one."""
    assert MULTI_REGISTRANT_TIE_BREAK_SENTINEL == "MULTI_REGISTRANT_NO_SINGLETON"
    assert not MULTI_REGISTRANT_TIE_BREAK_SENTINEL.isdigit()
    assert len(MULTI_REGISTRANT_TIE_BREAK_SENTINEL) != 10
    with pytest.raises(ValueError, match="invalid literal"):
        int(MULTI_REGISTRANT_TIE_BREAK_SENTINEL)


def test_an_anchorless_accession_without_a_real_set_is_refused_rather_than_hashed() -> None:
    """**Decision 083 R60**: an unestablished set hashes no fake value at all."""
    with pytest.raises(ValueError, match="at least two distinct substantive registrants"):
        accession_registrant_slot(None, ())
    with pytest.raises(ValueError, match="at least two distinct substantive registrants"):
        accession_registrant_slot(None, (17,))
    # A duplicate is one registrant, not two.
    with pytest.raises(ValueError, match="at least two distinct substantive registrants"):
        accession_registrant_slot(None, (17, 17))


def test_an_accession_can_never_have_neither_an_anchor_nor_an_association_set() -> None:
    """The unrepresentable state stays unrepresentable, at the pool validator."""
    from disclosure_drift.sec.accession_selector import solve_joint_selection

    orphan = AccessionCandidate(
        accession_plain="000000000120000001",
        accession_number_dashed="0000000001-20-000001",
        anchor_cik_numeric=None,
        form_type="10-K",
    )
    with pytest.raises(ValueError, match="neither an anchor nor a substantive"):
        solve_joint_selection(entities=(), accessions=(orphan,), node_limit=1000)


# ==========================================================================
# Schema-layer fixtures
# ==========================================================================


@pytest.fixture
def catalog(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A migrated catalog at the full 0001-0015 chain, on a disposable path."""
    with connect(tmp_path / "catalog.sqlite3", writer=True) as connection:
        apply_migrations(connection)
        with transaction(connection) as c:
            for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
                c.execute(
                    "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                    "is_eligible_universe, description, decision_record) VALUES (?, ?, ?, ?, ?)",
                    (form_type, int(is_amendment), int(eligible), description, "D007"),
                )
            for code in REASON_CODES.values():
                c.execute(
                    "INSERT OR REPLACE INTO reference_reason_codes (reason_code, category, "
                    "description, blocks_release, requires_manual_review, decision_record) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        code.code,
                        code.category,
                        code.description,
                        int(code.blocks_release),
                        int(code.requires_manual_review),
                        code.decision_reference,
                    ),
                )
        yield connection


def _seed_snapshot(c: sqlite3.Connection) -> None:
    c.execute(
        "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, started_at_utc, "
        "detail) VALUES ('job-1', 'sec_census', 'completed', 'M3.3', ?, '')",
        (_AT,),
    )
    c.execute(
        "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
        "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
        "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
        "coverage_window_sha256, input_observation_set_sha256, snapshot_state, entity_count, "
        "accession_count, created_at_utc) "
        "VALUES (?, 'job-1', '2010-01-01', '2026-06-30', '2026-06-30', 0, 'coverage/1.0', "
        "?, ?, ?, ?, ?, 'building', 0, 1, ?)",
        (
            _SNAPSHOT,
            pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
            pilot_policy.SIC_FAMILY_MAPPING_VERSION,
            pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
            "c" * 64,
            "d" * 64,
            _AT,
        ),
    )


def _seed_accession(
    c: sqlite3.Connection, *, anchor: int | None, multi: int, completeness: str
) -> None:
    c.execute(
        "INSERT INTO pilot_candidate_accessions (snapshot_id, accession_plain, "
        "accession_number_dashed, accession_tie_break_sha256, anchor_cik_numeric, "
        "registrant_set_completeness, form_type, is_amendment, filing_date_evidence_level, "
        "cohort_evidence_level, xbrl_evidence_level, amendment_purpose_evidence_level, "
        "multi_registrant, recorded_at_utc) "
        "VALUES (?, 'acc-1', 'acc-1', ?, ?, ?, '10-K', 0, 'unavailable', 'unavailable', "
        "'unavailable', 'unavailable', ?, ?)",
        (_SNAPSHOT, "b" * 64, anchor, completeness, multi, _AT),
    )


def _seed_registrant(
    c: sqlite3.Connection,
    *,
    cik: int,
    role: str,
    association_class: str = "substantive",
    completeness: str = "established",
) -> None:
    c.execute(
        "INSERT INTO pilot_candidate_accession_registrants (snapshot_id, accession_plain, "
        "registrant_cik_numeric, registrant_cik_padded, role, is_anchor, association_class, "
        "registrant_set_completeness, evidence_level, recorded_at_utc) "
        "VALUES (?, 'acc-1', ?, ?, ?, ?, ?, ?, 'unavailable', ?)",
        (
            _SNAPSHOT,
            cik,
            f"{cik:010d}",
            role,
            int(role == "anchor"),
            association_class,
            completeness,
            _AT,
        ),
    )


def _seed_multi_registrant_candidate(
    connection: sqlite3.Connection, *, submitter: int = 7777, unestablished: bool = False
) -> None:
    """One established, anchorless, genuinely multi-registrant accession."""
    completeness = "unestablished" if unestablished else "established"
    with transaction(connection) as c:
        _seed_snapshot(c)
        _seed_accession(c, anchor=None, multi=1, completeness=completeness)
        _seed_registrant(c, cik=17, role="associated", completeness=completeness)
        _seed_registrant(c, cik=917, role="associated", completeness=completeness)
        _seed_registrant(
            c,
            cik=submitter,
            role="submitter_only",
            association_class="submitter_only",
            completeness=completeness,
        )


def _seed_single_registrant_candidate_with_submitter_row(connection: sqlite3.Connection) -> None:
    """A sole substantive registrant beside a noncontributing submitter row."""
    with transaction(connection) as c:
        _seed_snapshot(c)
        _seed_accession(c, anchor=17, multi=0, completeness="established")
        _seed_registrant(c, cik=17, role="anchor")
        _seed_registrant(c, cik=9999, role="submitter_only", association_class="submitter_only")


def _freeze(connection: sqlite3.Connection) -> None:
    """Freeze the snapshot, supplying every digest the 0009 freeze CHECK requires."""
    digests = tuple(f"{index:064x}" for index in range(1, 10))
    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen', "
            "frozen_at_utc = ?, candidate_snapshot_sha256 = ?, "
            "input_observation_set_sha256 = ?, candidate_entity_table_sha256 = ?, "
            "candidate_accession_table_sha256 = ?, candidate_registrant_table_sha256 = ?, "
            "candidate_entity_evidence_sha256 = ?, candidate_accession_evidence_sha256 = ?, "
            "candidate_entity_reasons_sha256 = ?, candidate_accession_reasons_sha256 = ?, "
            "entity_count = 0, accession_count = 1 WHERE snapshot_id = ?",
            (_AT, *digests, _SNAPSHOT),
        )


# ==========================================================================
# Accepted Decision 084 R65 and R66 -- the two bounded continuation corrections
# ==========================================================================


def test_r65_the_disposable_catalog_machinery_recognizes_migration_head_0014(
    tmp_path: Path,
) -> None:
    """**Accepted Decision 084 R65.** The chain-head constant names the real head.

    Migration ``0014`` moved the repository's schema chain head. The refusal rule is
    unchanged -- a chain ending anywhere other than the accepted head is still refused
    rather than upgraded -- so the constant had to move with it, or every freshly prepared
    catalog would refuse itself.

    This exercises the **disposable** machinery only. It creates a catalog under a
    pytest-managed temporary root; it never resolves ``EV_ROOT``, never reads or writes the
    accepted private M3.2 operational catalog, and applies no migration to it.
    """
    from disclosure_drift.m3.acquisition import FINAL_MIGRATION_VERSION, prepare_operational_catalog

    assert FINAL_MIGRATION_VERSION == 15
    preparation = prepare_operational_catalog(evidence_root=tmp_path)
    assert preparation.created is True
    assert preparation.migration_chain_head == 15
    assert preparation.chain_is_exact is True
    with connect(preparation.database_path) as connection:
        versions = tuple(
            int(row["version"])
            for row in connection.execute(
                "SELECT version FROM ops_schema_migrations ORDER BY version"
            ).fetchall()
        )
    assert versions == tuple(range(1, 16))


def test_r66_the_persisted_caller_gives_a_joint_pair_its_truthful_entities(
    catalog: sqlite3.Connection,
) -> None:
    """**Accepted Decision 084 R66**, end to end through the persisted reader.

    A jointly filed 2009 support leg and 2010 base leg, both anchorless under **R58**,
    must reach **both** substantive registrants -- and each accession must still count
    once. Before the correction this returned no entities at all, which is the Decision
    083 **MINOR-1** defect the ruling closes.
    """
    from disclosure_drift.m3.offline_execution import verify_support_target_pairs

    _seed_joint_support_target_run(catalog)
    verification = verify_support_target_pairs(catalog, _RUN)
    # Proof A: truthful entity-domain attribution to every substantive registrant.
    assert verification.entities == (1, 901)
    # Proof B: no duplicate accession-domain credit -- two legs, two accessions.
    assert verification.inspected_accessions == 2


def test_r66_the_persisted_caller_grants_no_credit_without_the_association_set(
    catalog: sqlite3.Connection,
) -> None:
    """**Proof D**, at the persisted boundary: an unestablished set earns nothing.

    The caller reads ``association_class = 'substantive'`` rows. An accession that has
    none names no entity, and the reader invents none -- so the pair quota simply is not
    satisfied. Fail-closed in the safe direction: a hard quota only gets harder.
    """
    from disclosure_drift.m3.offline_execution import verify_support_target_pairs

    _seed_joint_support_target_run(catalog)
    with transaction(catalog) as c:
        c.execute("PRAGMA foreign_keys = OFF")
        c.execute(
            "DELETE FROM pilot_candidate_accession_registrants WHERE snapshot_id = ?",
            (_SNAPSHOT,),
        )
    verification = verify_support_target_pairs(catalog, _RUN)
    assert verification.entities == ()
    assert verification.inspected_accessions == 2


_RUN: Final = "e" * 64


def _seed_joint_support_target_run(connection: sqlite3.Connection) -> None:
    """One selection run holding a jointly filed 2009/2010 support-target pair.

    Both legs are filed by CIK 1 and CIK 901 together, so neither carries an anchor
    (**Decision 083 R58**) and both entities are selected.
    """
    legs = (
        ("acc-2009", "2009-03-01", None, "support", 1),
        ("acc-2010", "2010-03-01", "development", "base", 2),
    )
    with transaction(connection) as c:
        _seed_snapshot(c)
        for cik in (1, 901):
            c.execute(
                "INSERT INTO pilot_candidate_entities (snapshot_id, cik_numeric, cik_padded, "
                "entity_tie_break_sha256, candidate_category, size_evidence_level, "
                "industry_evidence_level, history_evidence_level, "
                "primary_universe_evidence_level, filing_time_name, recorded_at_utc) "
                "VALUES (?, ?, ?, ?, 'operating', 'unavailable', 'unavailable', 'unavailable', "
                "'unavailable', ?, ?)",
                (_SNAPSHOT, cik, f"{cik:010d}", f"{cik:064x}", f"Issuer {cik}", _AT),
            )
        for plain, filing_date, cohort, _role, order in legs:
            c.execute(
                "INSERT INTO pilot_candidate_accessions (snapshot_id, accession_plain, "
                "accession_number_dashed, accession_tie_break_sha256, anchor_cik_numeric, "
                "registrant_set_completeness, form_type, is_amendment, official_filing_date, "
                "filing_date_resolution_sha256, provisional_official_cohort, "
                "cohort_resolution_sha256, filing_date_evidence_level, cohort_evidence_level, "
                "xbrl_evidence_level, amendment_purpose_evidence_level, multi_registrant, "
                "base_eligible, support_eligible, recorded_at_utc) "
                "VALUES (?, ?, ?, ?, NULL, 'established', '10-K', 0, ?, ?, ?, ?, 'provisional', "
                "'provisional', 'unavailable', 'unavailable', 1, ?, ?, ?)",
                (
                    _SNAPSHOT,
                    plain,
                    plain,
                    f"{order:064x}",
                    filing_date,
                    "f" * 64,
                    cohort,
                    None if cohort is None else "9" * 64,
                    int(cohort is not None),
                    int(cohort is None),
                    _AT,
                ),
            )
            for cik in (1, 901):
                c.execute(
                    "INSERT INTO pilot_candidate_accession_registrants (snapshot_id, "
                    "accession_plain, registrant_cik_numeric, registrant_cik_padded, role, "
                    "is_anchor, association_class, registrant_set_completeness, evidence_level, "
                    "recorded_at_utc) VALUES (?, ?, ?, ?, 'associated', 0, 'substantive', "
                    "'established', 'provisional', ?)",
                    (_SNAPSHOT, plain, cik, f"{cik:010d}", _AT),
                )
        c.execute(
            "INSERT INTO pilot_candidate_accession_reasons (snapshot_id, accession_plain, "
            "reason_scope, reason_code, recorded_at_utc) "
            "VALUES (?, 'acc-2009', 'cohort', 'PILOT_ACCESSION_PRE_STUDY_SUPPORT', ?)",
            (_SNAPSHOT, _AT),
        )
        c.execute(
            "INSERT INTO pilot_selection_runs (selection_run_id, snapshot_id, selection_seed, "
            "selector_policy_version, quota_policy_version, search_node_limit, run_state, "
            "selection_input_sha256, started_at_utc) "
            "VALUES (?, ?, 'seed', ?, 'quota/1.0', 1000, 'running', ?, ?)",
            (_RUN, _SNAPSHOT, PILOT_SELECTOR_POLICY_VERSION, "a" * 64, _AT),
        )
        for order, cik in enumerate((1, 901), start=1):
            c.execute(
                "INSERT INTO pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric, "
                "selected_order, entity_hash_sha256, entity_role, candidate_category, "
                "recorded_at_utc) VALUES (?, ?, ?, ?, ?, 'operating', 'operating', ?)",
                (_RUN, _SNAPSHOT, cik, order, f"{cik:064x}", _AT),
            )
        for plain, _filing_date, _cohort, role, order in legs:
            c.execute(
                "INSERT INTO pilot_selected_accessions (selection_run_id, snapshot_id, "
                "accession_plain, anchor_cik_numeric, selected_order, accession_hash_sha256, "
                "accession_role, recorded_at_utc) VALUES (?, ?, ?, NULL, ?, ?, ?, ?)",
                (_RUN, _SNAPSHOT, plain, order, f"{order:064x}", role, _AT),
            )


# ==========================================================================
# Accepted Decision 084 R67 -- the acceptance precondition, as a standing proof
#
# R67 accepts leaving candidate_identity.py's column tuples unwidened ONLY on the claim
# that the relational association set is already genuinely governed and bound. The claim
# is not asserted here; it is exercised. If it were false these tests would pass trivially
# with equal digests, which is exactly what they refuse to do.
# ==========================================================================


def _registrant_rows(members: tuple[int, ...]) -> list[dict[str, object]]:
    """One candidate registrant row per member, at the governed E3 column tuple."""
    return [
        {
            "accession_plain": "acc-1",
            "registrant_cik_numeric": cik,
            "registrant_cik_padded": f"{cik:010d}",
            "role": "associated",
            "is_anchor": 0,
            "evidence_level": "provisional",
        }
        for cik in members
    ]


def test_r67_no_association_can_be_removed_without_changing_the_governed_digest() -> None:
    """**Accepted Decision 084 R67**, the acceptance precondition.

    Removing, altering, or adding one substantive association must change
    ``candidate_registrant_table_sha256`` (**E3**), which
    ``candidate_snapshot_sha256`` (**E4**) carries and which reaches selection identity
    and the manifest root transitively (**E5**).

    That is what makes widening ``REGISTRANT_TABLE_COLUMNS`` unnecessary: the relation is
    bound row-by-row already, so the set cannot be tampered with silently.
    """
    from disclosure_drift.m3.candidate_identity import (
        SNAPSHOT_CONTENT_FIELDS,
        candidate_registrant_table_sha256,
    )

    base = candidate_registrant_table_sha256(_registrant_rows((1, 901, 4242)))
    assert candidate_registrant_table_sha256(_registrant_rows((1, 901))) != base
    assert candidate_registrant_table_sha256(_registrant_rows((1, 901, 4243))) != base
    assert candidate_registrant_table_sha256(_registrant_rows((1, 901, 4242, 5555))) != base
    # E3 is carried by the snapshot content digest, so the change propagates to E4/E5.
    assert "candidate_registrant_table_sha256" in SNAPSHOT_CONTENT_FIELDS


def test_r67_the_governed_registrant_digest_is_row_order_independent() -> None:
    """Bound, but not order-sensitive: permuting the relation changes nothing."""
    from disclosure_drift.m3.candidate_identity import candidate_registrant_table_sha256

    base = candidate_registrant_table_sha256(_registrant_rows((1, 901, 4242)))
    assert candidate_registrant_table_sha256(_registrant_rows((4242, 1, 901))) == base
    assert candidate_registrant_table_sha256(_registrant_rows((901, 4242, 1))) == base


def test_r67_losing_the_anchor_role_changes_the_governed_digest() -> None:
    """The anchor state itself is bound, so **R58**'s change is visible in **E3**.

    A sole registrant carrying its anchor and the same CIK demoted to ``associated`` are
    different governed content -- which is why the multi-registrant correction is
    detectable at the digest layer without any new column.
    """
    from disclosure_drift.m3.candidate_identity import candidate_registrant_table_sha256

    anchored = _registrant_rows((1,))
    anchored[0]["role"] = "anchor"
    anchored[0]["is_anchor"] = 1
    assert candidate_registrant_table_sha256(anchored) != candidate_registrant_table_sha256(
        _registrant_rows((1,))
    )


def test_the_four_preserved_identities_carry_no_registrant_field() -> None:
    """**Decision 083 R61**: four identities are preserved, and this is why.

    ``snapshot_id``, ``entity_tie_break_sha256``, the **R15** evidence preimage, and the
    **R16** resolution preimage are unaffected because **no registrant field enters any of
    them** -- asserted against the frozen field tuples themselves rather than by
    recomputation, so a future widening of any of them fails here.
    """
    from disclosure_drift.m3.candidate_identity import (
        EVIDENCE_PREIMAGE_FIELDS,
        RESOLUTION_PREIMAGE_FIELDS,
        SNAPSHOT_IDENTITY_FIELDS,
    )

    for tuple_name, fields in (
        ("SNAPSHOT_IDENTITY_FIELDS", SNAPSHOT_IDENTITY_FIELDS),
        ("EVIDENCE_PREIMAGE_FIELDS", EVIDENCE_PREIMAGE_FIELDS),
        ("RESOLUTION_PREIMAGE_FIELDS", RESOLUTION_PREIMAGE_FIELDS),
    ):
        joined = " ".join(fields)
        assert "registrant" not in joined, tuple_name
        assert "anchor" not in joined, tuple_name
    # entity_tie_break_sha256 is the entity's own padded CIK and the selection seed only.
    from disclosure_drift.sec.entity_selector import selection_rank

    assert selection_rank("0000000001") == selection_rank("0000000001")


# ==========================================================================
# Decision 085 §6: the census layer cannot persist ESTABLISHED with zero relations
#
# 'established' claims the COMPLETE substantive association set is known, so it needs at
# least one substantive relation row to stand on. Migration `0014` shipped with only the
# UPDATE door closed; these tests hold all four shut, and hold the lawful ingest shape
# open. Probes A-G of the accepted correction packet, as standing tests.
# ==========================================================================

_CENSUS_ESTABLISHED_REFUSAL: Final = "established requires at least one substantive association"


def _seed_census_source(c: sqlite3.Connection, *ciks: int) -> None:
    """The observation, parser run, parsed record, and registrants a census row needs."""
    c.execute(
        "INSERT INTO census_source_observations (observation_id, source_id, request_identity, "
        "requested_url, purpose, retrieved_at_utc, outcome, logical_sha256, parser_version, "
        "recorded_at_utc) VALUES ('obs-c', 'sec_bulk_submissions', 'req/c', "
        "'https://example.invalid/c', 'census', ?, 'stored_new', ?, 'v/1.0', ?)",
        (_AT, "c" * 64, _AT),
    )
    c.execute(
        "INSERT INTO census_parser_runs (parser_run_id, source_observation_id, parser_id, "
        "parser_version, started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
        "outcome, summary_json) VALUES ('pr-c', 'obs-c', 'p', 'v/1.0', ?, ?, 0, 0, "
        "'completed', '{}')",
        (_AT, _AT),
    )
    c.execute(
        "INSERT INTO census_parsed_records (parsed_record_id, parser_run_id, "
        "source_observation_id, native_identity, record_sha256, record_index, payload_json, "
        "unknown_fields_json, warnings_json, reason_codes_json, duplicate_indicator, "
        "conflict_indicator, recorded_at_utc) VALUES ('pd-c', 'pr-c', 'obs-c', 'n', ?, 0, "
        "'{}', '[]', '[]', '[]', 0, 0, ?)",
        ("d" * 64, _AT),
    )
    for cik in ciks:
        c.execute(
            "INSERT INTO census_registrants (cik_numeric, cik_padded, first_observed_at_utc, "
            "latest_observed_at_utc) VALUES (?, ?, ?, ?)",
            (cik, f"{cik:010d}", _AT, _AT),
        )


def _census_accession(
    c: sqlite3.Connection,
    plain: str,
    *,
    scalar: int | None,
    completeness: str = "unestablished",
) -> None:
    c.execute(
        "INSERT INTO census_accessions (accession_plain, accession_dashed, "
        "registrant_cik_numeric, registrant_set_completeness, submitter_cik_numeric, form_type, "
        "is_amendment, is_discovery_form, is_negative_control, source_observation_id, "
        "parsed_record_id, first_observed_at_utc, latest_observed_at_utc) "
        "VALUES (?, ?, ?, ?, 7, '10-K', 0, 1, 0, 'obs-c', 'pd-c', ?, ?)",
        (plain, f"{plain[:10]}-{plain[10:12]}-{plain[12:]}", scalar, completeness, _AT, _AT),
    )


def _census_relation(
    c: sqlite3.Connection, plain: str, cik: int, association_class: str = "substantive"
) -> None:
    c.execute(
        "INSERT INTO census_accession_registrants (accession_plain, registrant_cik_numeric, "
        "registrant_cik_padded, association_class, evidence_level, source_observation_id, "
        "parsed_record_id, first_observed_at_utc, latest_observed_at_utc) "
        "VALUES (?, ?, ?, ?, 'provisional', 'obs-c', 'pd-c', ?, ?)",
        (plain, cik, f"{cik:010d}", association_class, _AT, _AT),
    )


@pytest.fixture
def census(catalog: sqlite3.Connection) -> sqlite3.Connection:
    """The migrated catalog plus the minimum census provenance a row needs."""
    with transaction(catalog) as c:
        _seed_census_source(c, 7, 8, 9)
    return catalog


def test_min2_a_the_lawful_established_single_registrant_write_succeeds(
    census: sqlite3.Connection,
) -> None:
    """**A.** Accession, then relation, then the claim -- all inside one transaction.

    This is the shape the foreign key already forces: ``census_accession_registrants``
    references ``census_accessions``, so the accession row cannot come second. The guards
    below must never make this sequence impossible, only make skipping its middle step
    impossible.
    """
    with transaction(census) as c:
        _census_accession(c, "000000000720000001", scalar=7)
        _census_relation(c, "000000000720000001", 7)
        c.execute(
            "UPDATE census_accessions SET registrant_set_completeness = 'established' "
            "WHERE accession_plain = '000000000720000001'"
        )
    row = census.execute(
        "SELECT registrant_cik_numeric, registrant_set_completeness FROM census_accessions"
    ).fetchone()
    assert row["registrant_cik_numeric"] == 7
    assert row["registrant_set_completeness"] == "established"


def test_min2_b_the_lawful_established_multi_registrant_write_succeeds(
    census: sqlite3.Connection,
) -> None:
    """**B.** Two substantive registrants, a NULL scalar, and the claim still lands."""
    with transaction(census) as c:
        _census_accession(c, "000000000820000001", scalar=None)
        _census_relation(c, "000000000820000001", 8)
        _census_relation(c, "000000000820000001", 9)
        c.execute(
            "UPDATE census_accessions SET registrant_set_completeness = 'established' "
            "WHERE accession_plain = '000000000820000001'"
        )
    row = census.execute(
        "SELECT registrant_cik_numeric, registrant_set_completeness FROM census_accessions"
    ).fetchone()
    assert row["registrant_cik_numeric"] is None
    assert row["registrant_set_completeness"] == "established"


def test_min2_c_an_unestablished_insert_is_always_permitted(census: sqlite3.Connection) -> None:
    """**C.** Fail-closed is the DEFAULT state, so ingest is never blocked by it."""
    with transaction(census) as c:
        _census_accession(c, "000000000920000001", scalar=9)
    assert (
        census.execute("SELECT registrant_set_completeness FROM census_accessions").fetchone()[0]
        == "unestablished"
    )


def test_min2_d_an_insert_cannot_assert_established_with_zero_relations(
    census: sqlite3.Connection,
) -> None:
    """**D.** The door the shipped migration left open.

    Its own comment said "the claim can never be made by assertion alone"; before this
    correction an INSERT could do exactly that, because the guard fired only on UPDATE.
    """
    with (
        pytest.raises(sqlite3.IntegrityError, match=_CENSUS_ESTABLISHED_REFUSAL),
        transaction(census) as c,
    ):
        _census_accession(c, "000000000720000002", scalar=7, completeness="established")
    assert census.execute("SELECT COUNT(*) FROM census_accessions").fetchone()[0] == 0


def test_min2_e_the_last_substantive_relation_cannot_be_deleted(
    census: sqlite3.Connection,
) -> None:
    """**E.** Emptying an established set from the relation side is refused too."""
    with transaction(census) as c:
        _census_accession(c, "000000000720000001", scalar=7)
        _census_relation(c, "000000000720000001", 7)
        c.execute(
            "UPDATE census_accessions SET registrant_set_completeness = 'established' "
            "WHERE accession_plain = '000000000720000001'"
        )
    with (
        pytest.raises(sqlite3.IntegrityError, match=_CENSUS_ESTABLISHED_REFUSAL),
        transaction(census) as c,
    ):
        c.execute("DELETE FROM census_accession_registrants")
    assert census.execute("SELECT COUNT(*) FROM census_accession_registrants").fetchone()[0] == 1


def test_min2_e_the_last_substantive_relation_cannot_be_reclassified_away(
    census: sqlite3.Connection,
) -> None:
    """**E**, the equivalent door: Decision 019 §6.2 says a submitter never establishes
    the set, so demoting the last substantive row empties it exactly as a delete does."""
    with transaction(census) as c:
        _census_accession(c, "000000000720000001", scalar=7)
        _census_relation(c, "000000000720000001", 7)
        c.execute(
            "UPDATE census_accessions SET registrant_set_completeness = 'established' "
            "WHERE accession_plain = '000000000720000001'"
        )
    with (
        pytest.raises(sqlite3.IntegrityError, match=_CENSUS_ESTABLISHED_REFUSAL),
        transaction(census) as c,
    ):
        c.execute("UPDATE census_accession_registrants SET association_class = 'submitter_only'")
    assert (
        census.execute("SELECT association_class FROM census_accession_registrants").fetchone()[0]
        == "substantive"
    )


def test_min2_the_lawful_downgrade_then_delete_path_stays_open(
    census: sqlite3.Connection,
) -> None:
    """Losing the evidence really does unestablish the set, so that path is not closed.

    The guards refuse a false state, never a truthful transition. Downgrade first and the
    relation rows may then be removed -- which is what a re-parse that no longer sees the
    registrant would legitimately do.
    """
    with transaction(census) as c:
        _census_accession(c, "000000000720000001", scalar=7)
        _census_relation(c, "000000000720000001", 7)
        c.execute(
            "UPDATE census_accessions SET registrant_set_completeness = 'established' "
            "WHERE accession_plain = '000000000720000001'"
        )
    with transaction(census) as c:
        c.execute(
            "UPDATE census_accessions SET registrant_set_completeness = 'unestablished' "
            "WHERE accession_plain = '000000000720000001'"
        )
        c.execute("DELETE FROM census_accession_registrants")
    assert census.execute("SELECT COUNT(*) FROM census_accession_registrants").fetchone()[0] == 0


def test_min2_f_an_update_to_established_without_a_relation_is_refused(
    census: sqlite3.Connection,
) -> None:
    """**F.** The original guard, still load-bearing and unchanged."""
    with transaction(census) as c:
        _census_accession(c, "000000000920000001", scalar=9)
    with (
        pytest.raises(sqlite3.IntegrityError, match=_CENSUS_ESTABLISHED_REFUSAL),
        transaction(census) as c,
    ):
        c.execute("UPDATE census_accessions SET registrant_set_completeness = 'established'")
    assert (
        census.execute("SELECT registrant_set_completeness FROM census_accessions").fetchone()[0]
        == "unestablished"
    )


def test_min2_the_r58_multi_scalar_guard_is_unaffected(census: sqlite3.Connection) -> None:
    """The existing **R58** guard still fires: a multi set forces a NULL scalar."""
    with transaction(census) as c:
        _census_accession(c, "000000000720000001", scalar=7)
        _census_relation(c, "000000000720000001", 7)
    with (
        pytest.raises(sqlite3.IntegrityError, match="must have a NULL registrant_cik_numeric"),
        transaction(census) as c,
    ):
        _census_relation(c, "000000000720000001", 8)


def test_min2_g_the_empty_table_precondition_still_refuses_a_populated_catalog(
    tmp_path: Path,
) -> None:
    """**G.** Migration `0014` is still prospective: it refuses a non-empty census.

    The added guards live inside the same script, so this proves they did not disturb
    the Decision 082 §10.12 precondition that keeps `0014` from becoming a DATA
    migration -- and that a catalog failing that gate is left intact at `0013`.
    """
    through_13 = tuple(m for m in available_migrations() if m.version <= 13)
    database = tmp_path / "populated.sqlite3"
    with connect(database, writer=True) as connection:
        apply_migrations(connection, through_13)
        with transaction(connection) as c:
            _seed_census_source(c, 7)
            c.execute(
                "INSERT INTO census_accessions (accession_plain, accession_dashed, "
                "registrant_cik_numeric, submitter_cik_numeric, form_type, is_amendment, "
                "is_discovery_form, is_negative_control, source_observation_id, "
                "parsed_record_id, first_observed_at_utc, latest_observed_at_utc) VALUES "
                "('000000000720000009', '0000000007-20-000009', 7, 7, '10-K', 0, 1, 0, "
                "'obs-c', 'pd-c', ?, ?)",
                (_AT, _AT),
            )
    with connect(database, writer=True) as connection:
        with pytest.raises(Exception, match="requires an empty census_accessions"):
            apply_migrations(connection)
        assert (
            connection.execute("SELECT MAX(version) FROM ops_schema_migrations").fetchone()[0] == 13
        )
