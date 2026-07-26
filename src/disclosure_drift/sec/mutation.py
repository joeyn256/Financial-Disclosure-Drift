"""Classifying a changed official source: ordinary update or genuine anomaly.

Most Stage M2.2 sources are living datasets. The bulk submissions archive, the
ticker files, an entity submissions document, the annual calendar page, and the
current index are all expected to change over time. A changed body is therefore
recorded as a new immutable observation that supersedes the prior one, and it does
**not** block the census.

A blocking mutation reason is reserved for a change that the source's own
semantics cannot explain:

* an identity declared immutable changed (``SOURCE_IMMUTABLE_IDENTITY_MUTATED``);
* a dated artifact changed after its period closed, or its period closure could not
  be established, with no official correction (``SOURCE_DATED_ARTIFACT_CHANGED``);
* the same validator yielded different bytes (``SOURCE_VALIDATOR_CONTRADICTION``);
* transport bytes and stored bytes do not reconcile (``SOURCE_HASH_DISAGREEMENT``);
* a reuse could not be reconciled with its recorded provenance
  (``SOURCE_SNAPSHOT_REUSE_UNRECONCILED``, raised by the snapshot store).

Every path preserves both observations. Nothing here deletes or overwrites.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from disclosure_drift.reasons import reason
from disclosure_drift.sec.source_registry import SourceSpec

__all__ = [
    "ChangeVerdict",
    "PriorContent",
    "classify_content_change",
]

ChangeStatus = Literal["expected_update", "anomalous_mutation"]


@dataclass(frozen=True, slots=True)
class PriorContent:
    """What was previously preserved for one request identity."""

    observation_id: str
    logical_sha256: str
    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True, slots=True)
class ChangeVerdict:
    """How a changed body is classified."""

    status: ChangeStatus
    reason_codes: tuple[str, ...]
    detail: str

    @property
    def blocks_release(self) -> bool:
        """Whether any attached reason blocks a release freeze."""
        return any(reason(code).blocks_release for code in self.reason_codes)

    @property
    def is_expected(self) -> bool:
        """Whether this is an ordinary update of a living source."""
        return self.status == "expected_update"


def classify_content_change(
    spec: SourceSpec,
    prior: PriorContent,
    *,
    logical_sha256: str,
    etag: str | None = None,
    last_modified: str | None = None,
    period_is_closed: bool | None = None,
    correction_observation_id: str | None = None,
) -> ChangeVerdict:
    """Classify a changed body at a stable request identity.

    Args:
        spec: Registered source, whose ``mutability`` sets the expectation.
        prior: The preserved observation this response is compared against.
        logical_sha256: Hash of the new logical content.
        etag: Validator returned with the new response.
        last_modified: Validator returned with the new response.
        period_is_closed: For a ``dated_snapshot`` source, whether the period named
            in the URL has closed. ``None`` means closure was not established, which
            fails closed rather than assuming the period is open.
        correction_observation_id: Observation identifier of official SEC evidence
            explaining a correction to a dated artifact, when one exists.

    Returns:
        A verdict whose reason codes are neutral for an ordinary update and
        release-blocking for an anomaly.
    """
    if prior.logical_sha256 == logical_sha256:
        return ChangeVerdict(
            status="expected_update",
            reason_codes=("SOURCE_CONTENT_UNCHANGED",),
            detail="logical content is identical to the preserved observation",
        )

    contradiction = _validator_contradiction(prior, etag, last_modified)
    if contradiction is not None:
        return ChangeVerdict(
            status="anomalous_mutation",
            reason_codes=("SOURCE_VALIDATOR_CONTRADICTION",),
            detail=contradiction,
        )

    if spec.mutability == "immutable":
        return ChangeVerdict(
            status="anomalous_mutation",
            reason_codes=("SOURCE_IMMUTABLE_IDENTITY_MUTATED",),
            detail=(
                f"source {spec.source_id!r} is registered as immutable, so a changed body "
                f"at the same identity is an anomaly; observation {prior.observation_id} "
                "is preserved for comparison"
            ),
        )

    if spec.mutability == "dated_snapshot":
        return _classify_dated(spec, prior, period_is_closed, correction_observation_id)

    return ChangeVerdict(
        status="expected_update",
        reason_codes=("SOURCE_CONTENT_UPDATED",),
        detail=(
            f"source {spec.source_id!r} is a living official dataset; the changed body is "
            f"a new observation superseding {prior.observation_id}, which is preserved"
        ),
    )


def _classify_dated(
    spec: SourceSpec,
    prior: PriorContent,
    period_is_closed: bool | None,
    correction_observation_id: str | None,
) -> ChangeVerdict:
    if correction_observation_id:
        return ChangeVerdict(
            status="expected_update",
            reason_codes=("SOURCE_CONTENT_UPDATED", "SOURCE_CORRECTION_EXPLAINED"),
            detail=(
                f"dated artifact for {spec.source_id!r} changed and official correction "
                f"evidence {correction_observation_id} explains it"
            ),
        )
    if period_is_closed is False:
        return ChangeVerdict(
            status="expected_update",
            reason_codes=("SOURCE_CONTENT_UPDATED",),
            detail=(
                f"dated artifact for {spec.source_id!r} is still accumulating because its "
                "period is open, so growth is expected"
            ),
        )
    unresolved = (
        "period closure was not established"
        if period_is_closed is None
        else "the period has closed"
    )
    return ChangeVerdict(
        status="anomalous_mutation",
        reason_codes=("SOURCE_DATED_ARTIFACT_CHANGED",),
        detail=(
            f"dated artifact for {spec.source_id!r} changed and {unresolved}; no official "
            f"correction evidence was supplied. Observation {prior.observation_id} is "
            "preserved and the census stops for review."
        ),
    )


def _validator_contradiction(
    prior: PriorContent,
    etag: str | None,
    last_modified: str | None,
) -> str | None:
    """Return a message when an unchanged validator accompanied changed bytes.

    The entity tag is the strong validator and settles the question when both
    observations carry one: an identical ETag with different bytes is a contradiction,
    and a differing ETag is the source stating that the content changed. Last-Modified
    is consulted only when no ETag is available on both sides, because its one-second
    granularity makes a stale value a weak signal rather than a contradiction.
    """
    if etag and prior.etag:
        if etag == prior.etag:
            return (
                f"the response repeated ETag {etag} from observation "
                f"{prior.observation_id} but delivered different bytes"
            )
        return None
    if last_modified and prior.last_modified and last_modified == prior.last_modified:
        return (
            f"the response repeated Last-Modified {last_modified!r} from observation "
            f"{prior.observation_id} with no entity tag on either observation, but "
            "delivered different bytes"
        )
    return None
