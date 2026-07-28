"""Frozen M2.3 pilot policy-version constants (Decision 016 section 1).

These are engineering/provenance policy identifiers, not frozen research
definitions: they version the pilot candidate-snapshot, evidence, selector,
reserve-signature, manifest-hash, and primary-universe-boundary policies that
Stage S3 onward relies on. They do not belong in ``cohorts.py``, which is
reserved for frozen research definitions (cohort windows, maturity gates, the
primary outcome, thresholds, the bootstrap seed) per ``CLAUDE.md`` rule 3.

``PILOT_SELECTION_SEED`` is deliberately not duplicated here: it stays in
``disclosure_drift.sec.pilot`` through Stage S4 (Decision 016 section 1).

Migration ``0009`` seeds ``reference_policy_versions`` with rows that must
match these constants exactly; a test asserts that agreement. Migration
``0010`` adds the ``PILOT_QUOTA_POLICY_VERSION`` row on top, additively (Decision
017): it freezes the governing quota-policy version -- the ``excluded_pool_count``
definition and the boundary-control structural-evidence interpretation -- that S4.2
callers now use as their default rather than inventing an arbitrary value per call.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "PILOT_CANDIDATE_POLICY_VERSION",
    "PILOT_EVIDENCE_POLICY_VERSION",
    "PILOT_MANIFEST_HASH_POLICY_VERSION",
    "PILOT_PRIMARY_UNIVERSE_BOUNDARY_VERSION",
    "PILOT_QUOTA_POLICY_VERSION",
    "PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION",
    "PILOT_SELECTOR_POLICY_VERSION",
    "SIC_FAMILY_MAPPING_VERSION",
]

PILOT_CANDIDATE_POLICY_VERSION: Final = "pilot-candidate/1.0"
PILOT_EVIDENCE_POLICY_VERSION: Final = "pilot-evidence/1.0"
SIC_FAMILY_MAPPING_VERSION: Final = "sic-family-mapping/0.2"
PILOT_SELECTOR_POLICY_VERSION: Final = "deterministic-constrained/1.0"
PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION: Final = "quota-contribution/1.0"
PILOT_MANIFEST_HASH_POLICY_VERSION: Final = "pilot-manifest/1.0"
PILOT_PRIMARY_UNIVERSE_BOUNDARY_VERSION: Final = "sic-6000-6999/1.0"
PILOT_QUOTA_POLICY_VERSION: Final = "m23-pilot-quota-policy-v1"
