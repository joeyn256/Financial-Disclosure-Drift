"""S5.4 -- pure reserve construction: eligibility, ranking, packages, and signatures.

Pure Python, in-memory only. This module opens no database, issues no SQL, reads
no file, makes no network call, reads no clock, generates no randomness, inspects
no environment variable, mutates no input, holds no mutable global state, and
persists nothing. It carries no manifest, release, or publication behaviour: Stage
S6 is out of scope, and no reserve is a manifest or publication input
(`Decision 020 <../../../Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md>`_
section 2).

Governing records:

* Decision 013 section 6 -- reserves and substitution as amended 2026-07-27: a
  reserve preserves the **complete** quota-contribution signature of the candidate
  it would replace, ranks under the same tie-breaker and ordering rules as initial
  selection, and no discretionary or approximate substitution is ever permitted.
* Decision 016 section 7 -- the reserve package model and the frozen signature
  input list; section 1 content-derived identifiers; section 8 hash boundaries.
* Decision 017 -- the frozen quota-policy version stored on every reserve.
* Decision 018 sections 7-10 -- roles, caps, floors, families and linked-amendment
  coverage; section 19 -- one methodological implementation per rule.
* Decision 020 -- this stage's controlling architecture record: exactly one rank-1
  package per target where a compatible reserve exists (section 7), a durable
  target-specific no-compatible-reserve disposition otherwise (section 7.1),
  reserve packages as subordinate content under the accepted S5 run identity
  (section 9), and exactly one new reason code (section 13).

**This module owns reserve methodology only.** It derives no quota-contribution
membership of its own: the target's contribution set is read from the accepted
Stage S5.1 output, and a candidate replacement's contribution set is produced by
that same single derivation --
:meth:`~disclosure_drift.sec.accession_selector.QuotaContributionMembership.derive`
-- applied to the candidate's own bundle. Roles, penalties, families, tie-break
hashes, and cap evaluation are the accepted S5.1 helpers, called unchanged
(Decision 018 section 19; Decision 020 section 4, alternative B).

**Every target's reserve is computed independently of every other target's.** No
replacement is consumed, reserved, or removed from a shared pool; one replacement
CIK may be the rank-1 reserve for several targets, because packages are
independent contingencies that are never simultaneously applied. There is
therefore no global matching, no assignment optimization, no greedy consumption,
no target-order-dependent allocation, and no pool-exhaustion state (Decision 020
section 7).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.pilot_policy import (
    PILOT_QUOTA_POLICY_VERSION,
    PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION,
)
from disclosure_drift.reasons import reason
from disclosure_drift.release.hashing import hash_table
from disclosure_drift.sec.accession_selector import (
    NOT_APPLICABLE,
    QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES,
    QUOTA_KEY_INLINE_XBRL_ORIGINALS,
    QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS,
    QUOTA_KEY_NAME_CHANGE_ENTITIES,
    QUOTA_KEY_ORIGINAL_2024_ENTITIES,
    QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES,
    QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS,
    QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES,
    AccessionCandidate,
    AccessionCapUsage,
    AccessionRole,
    EntityCandidate,
    JointSelectionResult,
    QuotaContributionMembership,
    accession_caps_satisfied,
    accession_selection_rank,
    assign_accession_role,
    official_filing_year,
)
from disclosure_drift.sec.entity_selector import PILOT_SELECTION_SEED, selection_rank

__all__ = [
    "EVIDENCE_LEVEL_PRECEDENCE",
    "NO_COMPATIBLE_RESERVE_REASON_CODE",
    "RESERVE_RANK",
    "NoCompatibleReserve",
    "ReserveAccession",
    "ReserveConstruction",
    "ReservePackage",
    "build_reserve_packages",
]

#: Decision 020 section 7 and owner ruling 14.1: exactly one package per target,
#: at rank 1. Multiple reserve ranks are not authorized at M2.3.
RESERVE_RANK: Final = 1

#: Decision 020 section 13: the single authorized reserve reason code. Resolved
#: through the registry so an unregistered or renamed code fails at import rather
#: than at write time. ``REVIEW_PILOT_RESERVE_POOL_EXHAUSTED`` does not exist and
#: is not authorized -- each target's reserve is independent, so no pool can be
#: exhausted.
NO_COMPATIBLE_RESERVE_REASON_CODE: Final = reason("REVIEW_PILOT_NO_COMPATIBLE_RESERVE").code

#: Strongest to weakest. Decision 014 section 1 admits only ``provisional`` as an
#: affirmative evidence state; the remaining levels are the ordered vocabulary
#: ``pilot_reserves.evidence_floor`` accepts.
EVIDENCE_LEVEL_PRECEDENCE: Final[tuple[str, ...]] = (
    "provisional",
    "review_required",
    "conflicting",
    "unavailable",
)

#: Decision 014 section 6's amendment-purpose ``unproven`` state is not in the
#: ``pilot_reserves.evidence_floor`` vocabulary. It is rendered as the weakest
#: admissible level so a package can never present a stronger floor than its
#: weakest quota-relevant classification actually supports.
_UNPROVEN: Final = "unproven"
_STRONGEST_EVIDENCE_LEVEL: Final = EVIDENCE_LEVEL_PRECEDENCE[0]

#: Decision 016 section 7 names these contributions individually in the frozen
#: signature input list. Each is rendered as the number of achieved units the
#: package supplies for that quota, which subsumes presence and preserves the
#: coverage the target was selected to provide.
_SIGNATURE_CONTRIBUTION_KEYS: Final[tuple[tuple[str, str], ...]] = (
    ("name_change_contribution", QUOTA_KEY_NAME_CHANGE_ENTITIES),
    ("support_pair_contribution", QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES),
    ("multi_registrant_contribution", QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS),
    ("pre_inline_xbrl_contribution", QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS),
    ("inline_xbrl_contribution", QUOTA_KEY_INLINE_XBRL_ORIGINALS),
    ("original_2024_contribution", QUOTA_KEY_ORIGINAL_2024_ENTITIES),
    ("original_2025_2026_contribution", QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES),
)

_ACCESSION_ROLES: Final[tuple[AccessionRole, ...]] = ("base", "control", "stress", "support")
_OPERATING: Final = "operating"
_CONTROL: Final = "control"
_EVENTFUL: Final = "eventful"


@dataclass(frozen=True, slots=True)
class ReserveAccession:
    """One accession of a replacement package's exact substitution bundle.

    Mirrors ``pilot_reserve_accessions`` (Decision 016 section 7): the same role
    vocabulary as ``pilot_selected_accessions``, plus the explicit hashed
    ``accession_order`` (Decision 016 section 8).
    """

    accession_plain: str
    accession_number_dashed: str
    accession_role: AccessionRole
    accession_order: int
    accession_tie_break_sha256: str


@dataclass(frozen=True, slots=True)
class ReservePackage:
    """One complete deterministic replacement package for one selected entity.

    A reserve is **constructed**, never **applied**: substitution is an M2.5 event
    outside this stage, and constructing a package alters no selected entity or
    accession (Decision 013 section 6; Decision 020 section 7).
    """

    reserve_package_id: str
    target_cik_padded: str
    replacement_cik_padded: str
    reserve_rank: int
    replaces_signature_sha256: str
    reserve_signature_sha256: str
    signature_policy_version: str
    quota_policy_version: str
    reserve_tie_break_sha256: str
    evidence_floor: str
    accessions: tuple[ReserveAccession, ...]
    quota_contributions: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NoCompatibleReserve:
    """One target whose reserve construction produced no compatible package.

    Decision 020 section 7.1: target-specific, review-required, and nonblocking.
    It is not selection infeasibility, not node-limit exhaustion, and never
    permission to substitute an approximate reserve.
    """

    target_cik_padded: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class ReserveConstruction:
    """Every selected entity's reserve disposition, in canonical target order.

    The two families are mutually exclusive and jointly total over the selected
    entities: each target carries exactly one rank-1 package **or** exactly one
    no-compatible-reserve disposition, which is what migration ``0012``'s
    feasible-transition trigger requires before ``running -> feasible``.
    """

    packages: tuple[ReservePackage, ...]
    no_compatible_reserve: tuple[NoCompatibleReserve, ...]

    def disposition_targets(self) -> tuple[str, ...]:
        """Every target carrying a disposition, sorted; duplicates are impossible."""
        return tuple(
            sorted(
                [package.target_cik_padded for package in self.packages]
                + [entry.target_cik_padded for entry in self.no_compatible_reserve]
            )
        )


# --------------------------------------------------------------------------
# Package assembly helpers -- accepted S5.1 rules, called and never restated
# --------------------------------------------------------------------------


def _accession_order_key(
    accession: AccessionCandidate, selection_seed: str
) -> tuple[str, str, str]:
    """Decision 018 section 4's ordering key, expressed through the public rank."""
    anchor = accession.anchor_cik_padded
    return (
        accession_selection_rank(anchor, accession.accession_number_dashed, selection_seed),
        anchor,
        accession.accession_number_dashed,
    )


def _bundle_filing_year(accession: AccessionCandidate) -> int | None:
    """The accepted-core filing year of one candidate accession, or fail closed.

    The single accepted derivation --
    :func:`~disclosure_drift.sec.accession_selector.official_filing_year` -- is the
    only parser consulted; this module holds no regex, no substring slice, and no
    second interpretation of a stored date (Decision 018 section 19).

    An absent ``official_filing_date`` legitimately yields ``None``: the accepted
    core treats a missing date as fail-closed for the filing-year-dependent 2009
    support role, and nothing further is claimed about it. A **stored but
    unusable** date is different in kind -- the snapshot asserts a filing date the
    accepted core cannot read -- so it raises rather than being silently reduced to
    ``None``, silently dropped from the bundle, or given a role. This is the
    fail-closed rule of Decision 020 section 10 and CLAUDE.md rule 12: stop and
    report, never work around a failed gate.
    """
    stored = accession.official_filing_date
    if stored is None:
        return None
    year = official_filing_year(stored)
    if year is None:
        message = (
            f"accession {accession.accession_number_dashed}: stored official_filing_date "
            f"{stored!r} is not an exact YYYY-MM-DD calendar date, so no reserve bundle can "
            "be assembled from it"
        )
        raise GateFailureError(message)
    return year


def _bundle_for(
    entity: EntityCandidate,
    accessions: Sequence[AccessionCandidate],
    selection_seed: str,
) -> tuple[ReserveAccession, ...]:
    """The candidate's exact substitution bundle: all its role-assignable accessions.

    The bundle is not searched and not a chosen subset: it is every accession the
    frozen snapshot anchors to this entity that :func:`assign_accession_role`
    admits under the entity's own category, in the accepted Decision 018 section 4
    order. A searched or hand-trimmed bundle would be a discretionary
    substitution, which Decision 013 section 6 forbids outright.

    Raises:
        GateFailureError: an anchored accession stores an official filing date the
            accepted core cannot read (:func:`_bundle_filing_year`).
    """
    cik = entity.cik_padded
    category = entity.candidate.category
    matched: list[tuple[tuple[str, str, str], AccessionCandidate, AccessionRole]] = []
    for accession in accessions:
        if accession.anchor_cik_padded != cik:
            continue
        role, _reason = assign_accession_role(
            accession, anchor_category=category, filing_year=_bundle_filing_year(accession)
        )
        if role is not None:
            matched.append((_accession_order_key(accession, selection_seed), accession, role))
    matched.sort(key=lambda entry: entry[0])
    return tuple(
        ReserveAccession(
            accession_plain=accession.accession_plain,
            accession_number_dashed=accession.accession_number_dashed,
            accession_role=role,
            accession_order=order,
            accession_tie_break_sha256=key[0],
        )
        for order, (key, accession, role) in enumerate(matched, start=1)
    )


def _bundle_satisfies_floors(entity: EntityCandidate, bundle: Sequence[ReserveAccession]) -> bool:
    """Decision 018 section 9's floors, evaluated for one entity's own bundle.

    An operating entity needs at least one ``base`` accession, a control entity at
    least one ``control`` accession, and every entity must anchor at least one
    accession. Only the replaced entity's row changes under a substitution, so
    every other selected entity's floor is untouched by construction.
    """
    if not bundle:
        return False
    roles = {entry.accession_role for entry in bundle}
    if entity.candidate.category == _OPERATING:
        return "base" in roles
    if entity.candidate.category == _CONTROL:
        return "control" in roles
    return False


def _evidence_floor(
    bundle: Sequence[ReserveAccession], accession_by_plain: Mapping[str, AccessionCandidate]
) -> str:
    """The weakest structurally applicable evidence level across the bundle.

    Decision 016 section 7's "evidence floor (the weakest evidence level across the
    package's quota-relevant classifications)", evaluated over exactly the
    applicability model Decision 018 section 3.4 already freezes -- filing date and
    XBRL always, cohort only where a study cohort applies, amendment purpose and
    linkage only on an amendment -- plus the multi-registrant classification where
    the accession is multi-registrant, because that classification gates a quota.
    A structurally inapplicable dimension is skipped, exactly as it contributes no
    penalty.
    """
    weakest = 0
    for entry in bundle:
        accession = accession_by_plain[entry.accession_plain]
        levels = [accession.filing_date_evidence_level, accession.xbrl_evidence_level]
        if accession.cohort_applicability == "applies":
            levels.append(accession.cohort_evidence_level)
        if accession.is_amendment:
            levels.append(accession.amendment_purpose_evidence_level)
            levels.append(accession.amendment_linkage_evidence_level)
        if accession.multi_registrant:
            levels.append(accession.multi_registrant_evidence_level)
        for level in levels:
            if level == NOT_APPLICABLE:
                continue
            if level == _UNPROVEN:
                weakest = len(EVIDENCE_LEVEL_PRECEDENCE) - 1
                continue
            if level not in EVIDENCE_LEVEL_PRECEDENCE:
                message = (
                    f"unrecognized evidence level {level!r} on {entry.accession_number_dashed}"
                )
                raise ValueError(message)
            weakest = max(weakest, EVIDENCE_LEVEL_PRECEDENCE.index(level))
    return EVIDENCE_LEVEL_PRECEDENCE[weakest] if bundle else _STRONGEST_EVIDENCE_LEVEL


def _role_counts(bundle: Sequence[ReserveAccession]) -> str:
    """Canonical rendering of "the accession counts and roles the package supplies"."""
    counts = dict.fromkeys(_ACCESSION_ROLES, 0)
    for entry in bundle:
        counts[entry.accession_role] += 1
    return "|".join(f"{role}={counts[role]}" for role in _ACCESSION_ROLES)


def _unit_counts_for(membership: QuotaContributionMembership, cik_padded: str) -> Mapping[str, int]:
    """How many achieved units of each quota this entity is a member of."""
    counts: dict[str, int] = {}
    for unit in membership.units:
        if any(member.cik_padded == cik_padded for member in unit.members):
            counts[unit.key] = counts.get(unit.key, 0) + 1
    return counts


def _amendment_purpose_units(
    membership: QuotaContributionMembership, cik_padded: str
) -> tuple[str, ...]:
    """The amendment-purpose categories this entity contributes, sorted.

    The only contribution whose unit identity is a *shared* coverage token rather
    than the entity's or an accession's own identity, so preserving the set of
    categories -- not merely the count -- is what keeps a replacement from
    silently altering a cross-cutting contribution (Decision 013 section 6).
    """
    return tuple(
        sorted(
            {
                unit.unit
                for unit in membership.units
                if unit.key == QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES
                and any(member.cik_padded == cik_padded for member in unit.members)
            }
        )
    )


def _signature(
    entity: EntityCandidate,
    bundle: Sequence[ReserveAccession],
    membership: QuotaContributionMembership,
    *,
    evidence_floor: str,
    signature_policy_version: str,
    quota_policy_version: str,
) -> str:
    """Compute one side of the replacement-compatibility signature.

    Exactly Decision 016 section 7's frozen input list, computed with
    ``release/hashing.py`` (Decision 013 section 7). It is computed from **one
    side's own rows**: called with the target's entity, its selected accessions,
    and the accepted S5.1 membership it produces ``replaces_signature_sha256``;
    called with a replacement's entity, its own bundle, and that bundle's derived
    membership it produces ``reserve_signature_sha256``. Equality of the two is
    therefore an independent recomputation on both sides, never a comparison of
    two stored columns (Decision 016 section 7).

    No timestamp, event identifier, free-text detail, path, SEC identity, outcome
    value, or filing text enters it (Decision 016 section 8).
    """
    candidate = entity.candidate
    counts = _unit_counts_for(membership, candidate.cik_padded)
    fields: dict[str, object] = {
        "signature_policy_version": signature_policy_version,
        "quota_policy_version": quota_policy_version,
        "entity_role": _OPERATING if candidate.category == _OPERATING else _CONTROL,
        "control_kind": candidate.control_kind,
        "size_stratum": candidate.size_stratum,
        "industry_family": candidate.industry_group,
        "industry_quota_eligible": candidate.industry_quota_eligible,
        "history_class": candidate.history_class,
        "eventful_and_currently_inactive": (
            candidate.history_class == _EVENTFUL and candidate.currently_inactive
        ),
        "primary_universe_eligible": candidate.primary_universe_eligible,
        "amendment_purpose_contributions": "|".join(
            _amendment_purpose_units(membership, candidate.cik_padded)
        ),
        "accession_counts_by_role": _role_counts(bundle),
        "evidence_floor": evidence_floor,
    }
    for field_name, quota_key in _SIGNATURE_CONTRIBUTION_KEYS:
        fields[field_name] = counts.get(quota_key, 0)
    return hash_table(
        "pilot_reserve_signature", tuple(sorted(fields)), [fields]
    ).normalized_content_sha256


def _package_id(
    *,
    selection_run_id: str,
    snapshot_id: str,
    target_cik_padded: str,
    replacement_cik_padded: str,
    reserve_rank: int,
    signature: str,
    signature_policy_version: str,
    quota_policy_version: str,
    reserve_tie_break_sha256: str,
    evidence_floor: str,
    bundle: Sequence[ReserveAccession],
    contributions: Sequence[tuple[str, str]],
) -> str:
    """Content-derived 64-hex package identity, subordinate to the S5 run identity.

    Decision 016 section 1 and Decision 020 section 9: derived from the package's
    own normalized content with ``reserve_rank`` as an explicit hashed column, and
    namespaced by the accepted ``selection_run_id`` and ``snapshot_id`` -- the two
    columns the schema scopes reserves by -- so no second S5 run identity is
    created and two runs can never collide on one primary key. No reserve-set root
    digest and no manifest hash is computed here.
    """
    accessions_sha256 = hash_table(
        "pilot_reserve_accessions",
        ("accession_plain", "accession_role", "accession_order", "accession_hash_sha256"),
        [
            {
                "accession_plain": entry.accession_plain,
                "accession_role": entry.accession_role,
                "accession_order": entry.accession_order,
                "accession_hash_sha256": entry.accession_tie_break_sha256,
            }
            for entry in bundle
        ],
    ).normalized_content_sha256
    contributions_sha256 = hash_table(
        "pilot_reserve_quota_contributions",
        ("quota_dimension", "quota_key"),
        [{"quota_dimension": dimension, "quota_key": key} for dimension, key in contributions],
    ).normalized_content_sha256
    fields: dict[str, object] = {
        "selection_run_id": selection_run_id,
        "snapshot_id": snapshot_id,
        "target_cik_padded": target_cik_padded,
        "replacement_cik_padded": replacement_cik_padded,
        "reserve_rank": reserve_rank,
        "replaces_signature_sha256": signature,
        "reserve_signature_sha256": signature,
        "signature_policy_version": signature_policy_version,
        "quota_policy_version": quota_policy_version,
        "reserve_tie_break_sha256": reserve_tie_break_sha256,
        "evidence_floor": evidence_floor,
        "accessions_content_sha256": accessions_sha256,
        "quota_contributions_content_sha256": contributions_sha256,
    }
    return hash_table("pilot_reserves", tuple(sorted(fields)), [fields]).normalized_content_sha256


@dataclass(frozen=True, slots=True)
class _CandidateProfile:
    """One candidate replacement's own package content, computed once.

    Target-independent by construction: a candidate's bundle, contribution set,
    evidence floor, and signature depend only on the frozen snapshot, never on
    which target is being covered. That is what makes cross-target reuse free and
    the result invariant under the order targets are processed.
    """

    entity: EntityCandidate
    bundle: tuple[ReserveAccession, ...]
    contributions: tuple[tuple[str, str], ...]
    evidence_floor: str
    signature: str


def _usage_from(
    roles_by_plain: Mapping[str, tuple[str, AccessionRole]],
) -> AccessionCapUsage:
    """Evaluate the four Decision 018 section 8 caps over an accession assignment."""
    base_by_cik: dict[str, int] = {}
    base_total = 0
    stress_total = 0
    for anchor, role in roles_by_plain.values():
        if role == "base":
            base_total += 1
            base_by_cik[anchor] = base_by_cik.get(anchor, 0) + 1
        elif role == "stress":
            stress_total += 1
    return AccessionCapUsage(
        base_total=base_total,
        stress_total=stress_total,
        accession_total=len(roles_by_plain),
        max_base_per_cik=max(base_by_cik.values(), default=0),
    )


def build_reserve_packages(
    entities: Iterable[EntityCandidate],
    accessions: Iterable[AccessionCandidate],
    result: JointSelectionResult,
    *,
    selection_run_id: str,
    snapshot_id: str,
    selection_seed: str = PILOT_SELECTION_SEED,
    signature_policy_version: str = PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION,
    quota_policy_version: str = PILOT_QUOTA_POLICY_VERSION,
) -> ReserveConstruction:
    """Construct every selected entity's reserve disposition, deterministically.

    **Every selected entity is a target, controls included** (Decision 020 section
    7): compatibility alone decides whether a valid reserve exists, never entity
    role. For each target exactly one rank-1 package is produced where a
    compatible replacement exists, and exactly one no-compatible-reserve
    disposition otherwise. No rank other than 1 and no alternative package is
    produced.

    A candidate replacement is compatible when it is neither the target nor itself
    selected in the run; its own bundle satisfies the Decision 018 section 9 floors
    and, substituted for the target's accessions, breaches none of the section 8
    caps; its quota-contribution set equals the target's **exactly**, with no
    symmetric difference in either direction; and its independently recomputed
    signature equals the target's. Among compatible candidates the rank-1
    replacement is the first under the accepted initial-selection tie-break --
    ``selection_rank`` over the padded CIK under the frozen seed, with the
    canonical CIK identity fallback (Decision 020 section 7). No new quota,
    fallback, ranking term, or eligibility rule is introduced.

    ``selection_run_id`` and ``snapshot_id`` are opaque identity inputs supplied by
    the caller; nothing here derives, replaces, or reissues a run identity.

    A non-feasible result has no selection to cover and yields an empty
    construction, which persists nothing.

    Raises:
        ValueError: an empty run or snapshot identity, a malformed candidate pool,
            a selected identity absent from the pool, or -- as a fail-closed
            self-check -- a constructed package that is not disjoint from the
            selected set or that duplicates a replacement within one target.
        GateFailureError: a candidate replacement anchors an accession whose stored
            official filing date the accepted core cannot read
            (:func:`_bundle_filing_year`).
    """
    if not selection_run_id or not snapshot_id:
        message = "selection_run_id and snapshot_id are required to scope a reserve package"
        raise ValueError(message)

    entity_pool = tuple(entities)
    accession_pool = tuple(accessions)
    if result.status != "feasible":
        return ReserveConstruction(packages=(), no_compatible_reserve=())

    entity_by_cik = {entry.cik_padded: entry for entry in entity_pool}
    accession_by_plain = {a.accession_plain: a for a in accession_pool}
    selected_ciks = {candidate.cik_padded for candidate in result.selected_entities}
    membership = result.quota_contributions

    selected_roles: dict[str, tuple[str, AccessionRole]] = {
        selected.accession_plain: (selected.anchor_cik_padded, selected.accession_role)
        for selected in result.selected_accessions
    }

    profiles = _candidate_profiles(
        entity_pool,
        accession_pool,
        accession_by_plain,
        selected_ciks=selected_ciks,
        selection_seed=selection_seed,
        signature_policy_version=signature_policy_version,
        quota_policy_version=quota_policy_version,
    )

    packages: list[ReservePackage] = []
    uncovered: list[NoCompatibleReserve] = []
    for target in result.selected_entities:
        target_cik = target.cik_padded
        target_entity = entity_by_cik.get(target_cik)
        if target_entity is None:
            message = f"selected entity {target_cik!r} is not in the candidate entity pool"
            raise ValueError(message)
        target_bundle = tuple(
            sorted(
                (
                    ReserveAccession(
                        accession_plain=selected.accession_plain,
                        accession_number_dashed=selected.accession_number_dashed,
                        accession_role=selected.accession_role,
                        accession_order=0,
                        accession_tie_break_sha256=selected.accession_tie_break_sha256,
                    )
                    for selected in result.selected_accessions
                    if selected.anchor_cik_padded == target_cik
                ),
                key=lambda entry: entry.accession_plain,
            )
        )
        target_contributions = membership.contribution_keys_for_entity(target_cik)
        target_floor = _evidence_floor(target_bundle, accession_by_plain)
        target_signature = _signature(
            target_entity,
            target_bundle,
            membership,
            evidence_floor=target_floor,
            signature_policy_version=signature_policy_version,
            quota_policy_version=quota_policy_version,
        )
        chosen = _rank_one_replacement(
            profiles,
            target_cik=target_cik,
            target_contributions=target_contributions,
            target_signature=target_signature,
            target_plains={entry.accession_plain for entry in target_bundle},
            selected_roles=selected_roles,
            selection_seed=selection_seed,
        )
        if chosen is None:
            uncovered.append(
                NoCompatibleReserve(
                    target_cik_padded=target_cik,
                    reason_code=NO_COMPATIBLE_RESERVE_REASON_CODE,
                )
            )
            continue
        if chosen.entity.cik_padded == target_cik or chosen.entity.cik_padded in selected_ciks:
            message = (
                f"reserve replacement {chosen.entity.cik_padded!r} for target {target_cik!r} is "
                "the target itself or already selected in this run"
            )
            raise ValueError(message)
        tie_break = selection_rank(chosen.entity.cik_padded, selection_seed)
        packages.append(
            ReservePackage(
                reserve_package_id=_package_id(
                    selection_run_id=selection_run_id,
                    snapshot_id=snapshot_id,
                    target_cik_padded=target_cik,
                    replacement_cik_padded=chosen.entity.cik_padded,
                    reserve_rank=RESERVE_RANK,
                    signature=target_signature,
                    signature_policy_version=signature_policy_version,
                    quota_policy_version=quota_policy_version,
                    reserve_tie_break_sha256=tie_break,
                    evidence_floor=chosen.evidence_floor,
                    bundle=chosen.bundle,
                    contributions=chosen.contributions,
                ),
                target_cik_padded=target_cik,
                replacement_cik_padded=chosen.entity.cik_padded,
                reserve_rank=RESERVE_RANK,
                replaces_signature_sha256=target_signature,
                reserve_signature_sha256=chosen.signature,
                signature_policy_version=signature_policy_version,
                quota_policy_version=quota_policy_version,
                reserve_tie_break_sha256=tie_break,
                evidence_floor=chosen.evidence_floor,
                accessions=chosen.bundle,
                quota_contributions=chosen.contributions,
            )
        )

    construction = ReserveConstruction(
        packages=tuple(sorted(packages, key=lambda entry: entry.target_cik_padded)),
        no_compatible_reserve=tuple(sorted(uncovered, key=lambda entry: entry.target_cik_padded)),
    )
    _require_one_disposition_per_target(construction, selected_ciks)
    return construction


def _candidate_profiles(
    entity_pool: Sequence[EntityCandidate],
    accession_pool: Sequence[AccessionCandidate],
    accession_by_plain: Mapping[str, AccessionCandidate],
    *,
    selected_ciks: set[str],
    selection_seed: str,
    signature_policy_version: str,
    quota_policy_version: str,
) -> tuple[_CandidateProfile, ...]:
    """Profile every eligible replacement once, in canonical rank order.

    Candidates already selected in the run are excluded here, which is the
    disjointness requirement Decision 020 section 7 makes an S5.4 invariant even
    though migration ``0009`` does not enforce it.
    """
    profiles: list[_CandidateProfile] = []
    for entity in entity_pool:
        cik = entity.cik_padded
        if cik in selected_ciks:
            continue
        bundle = _bundle_for(entity, accession_pool, selection_seed)
        if not _bundle_satisfies_floors(entity, bundle):
            continue
        derived = QuotaContributionMembership.derive(
            entity_pool,
            accession_pool,
            selected_entity_ciks=[cik],
            selected_accession_plains=[entry.accession_plain for entry in bundle],
            selection_seed=selection_seed,
        )
        floor = _evidence_floor(bundle, accession_by_plain)
        profiles.append(
            _CandidateProfile(
                entity=entity,
                bundle=bundle,
                contributions=derived.contribution_keys(),
                evidence_floor=floor,
                signature=_signature(
                    entity,
                    bundle,
                    derived,
                    evidence_floor=floor,
                    signature_policy_version=signature_policy_version,
                    quota_policy_version=quota_policy_version,
                ),
            )
        )
    profiles.sort(
        key=lambda entry: (
            selection_rank(entry.entity.cik_padded, selection_seed),
            entry.entity.cik_padded,
        )
    )
    return tuple(profiles)


def _rank_one_replacement(
    profiles: Sequence[_CandidateProfile],
    *,
    target_cik: str,
    target_contributions: Sequence[tuple[str, str]],
    target_signature: str,
    target_plains: set[str],
    selected_roles: Mapping[str, tuple[str, AccessionRole]],
    selection_seed: str,
) -> _CandidateProfile | None:
    """The first compatible replacement under the accepted initial-selection tie-break.

    ``profiles`` is already in that order, and every compatibility test below is a
    function of the target and the single candidate only -- never of another
    target's outcome, of how many packages have been built, or of the order targets
    are processed. Nothing is consumed: the same profile remains available to every
    other target.
    """
    wanted = tuple(target_contributions)
    for profile in profiles:
        if profile.entity.cik_padded == target_cik:
            continue
        if profile.contributions != wanted:
            continue
        if profile.signature != target_signature:
            continue
        if not _caps_preserved(profile, target_plains=target_plains, selected_roles=selected_roles):
            continue
        _require_unique_within_target(profile)
        return profile
    return None


def _caps_preserved(
    profile: _CandidateProfile,
    *,
    target_plains: set[str],
    selected_roles: Mapping[str, tuple[str, AccessionRole]],
) -> bool:
    """Whether substituting this one package for the target keeps every cap satisfied.

    Evaluated one package at a time, because reserve packages are independent
    contingencies that are never simultaneously applied (Decision 020 section 7).
    The four Decision 018 section 8 caps are evaluated by the accepted
    :func:`accession_caps_satisfied` helper, so a cap can never be read one way
    here and another way in the selection that produced the incumbent.
    """
    substituted = {
        plain: entry for plain, entry in selected_roles.items() if plain not in target_plains
    }
    replacement_cik = profile.entity.cik_padded
    for entry in profile.bundle:
        if entry.accession_plain in substituted:
            return False
        substituted[entry.accession_plain] = (replacement_cik, entry.accession_role)
    return accession_caps_satisfied(_usage_from(substituted))


def _require_unique_within_target(profile: _CandidateProfile) -> None:
    """A replacement CIK appears at most once within one target's package."""
    plains = [entry.accession_plain for entry in profile.bundle]
    if len(plains) != len(set(plains)):
        message = (
            f"replacement {profile.entity.cik_padded!r} would supply a duplicate accession in one "
            "reserve package"
        )
        raise ValueError(message)


def _require_one_disposition_per_target(
    construction: ReserveConstruction, selected_ciks: set[str]
) -> None:
    """Exactly one disposition per selected entity, mutually exclusive.

    The pure counterpart of migration ``0012``'s feasible-transition trigger: a
    construction that could not satisfy that trigger never reaches the store.
    """
    targets = construction.disposition_targets()
    if len(targets) != len(set(targets)):
        message = "a selected entity carries more than one reserve disposition"
        raise ValueError(message)
    if set(targets) != selected_ciks:
        message = "every selected entity must carry exactly one reserve disposition"
        raise ValueError(message)
    if any(package.reserve_rank != RESERVE_RANK for package in construction.packages):
        message = f"every reserve package must be at reserve_rank {RESERVE_RANK}"
        raise ValueError(message)
