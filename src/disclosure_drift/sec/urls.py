"""URL normalization and redirect-boundary enforcement for official SEC retrieval.

Two jobs live here, both required before any payload is trusted:

* **Normalized request identity.** A snapshot may only be reused for the same
  logical request. Casing of scheme and host, a default port, a redundant ``/./``
  segment, query-parameter order, and a fragment must not make two identical
  requests look different, and must not make two different requests look the same.

* **Redirect boundary.** Every hop and the final URL are validated, not only the
  URL the caller asked for. A hop may not leave the official SEC origins, may not
  downgrade the scheme, may not carry user-info or an unexpected port, may not
  enter a filing-body or accession-document path, and may not leave the registered
  source's permitted URL family. Loops and excessive depth are refused.

Because redirects are followed by the policy layer rather than by the HTTP library,
no redirect can bypass :func:`filing_body_url_is_prohibited` or the source registry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, NoReturn
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.sec.source_registry import (
    SEC_ORIGINS,
    SOURCES,
    SourceSpec,
    filing_body_url_is_prohibited,
)

__all__ = [
    "MAX_REDIRECT_DEPTH",
    "REDIRECT_STATUSES",
    "RedirectBoundaryError",
    "RedirectHop",
    "normalize_url",
    "request_identity",
    "resolve_redirect",
    "validate_chain",
    "validate_url",
]

MAX_REDIRECT_DEPTH: Final = 5
"""How many hops a registered source may traverse before the retrieval is abandoned."""

REDIRECT_STATUSES: Final[frozenset[int]] = frozenset({301, 302, 303, 307, 308})
"""Statuses the policy layer follows itself, one validated hop at a time."""

_ALLOWED_HOSTS: Final[frozenset[str]] = frozenset(
    urlsplit(origin).hostname or "" for origin in SEC_ORIGINS
)
_DEFAULT_PORTS: Final[frozenset[int]] = frozenset({443})
_IDENTITY_BOUND_REDIRECT_SOURCES: Final[frozenset[str]] = frozenset(
    {"sec_submissions_entity", "sec_submissions_historical"}
)
_AMBIGUOUS_PATH_CHARACTERS: Final = frozenset({"%", "\\", "\x00"})


@dataclass(frozen=True, slots=True)
class _UrlFamilyPolicy:
    hosts: frozenset[str]
    exact_paths: tuple[str, ...] = ()
    path_pattern: re.Pattern[str] | None = None
    manifest_exact: bool = False
    permitted_query_keys: frozenset[str] = frozenset()
    allow_duplicate_query_keys: bool = False


_WWW: Final = frozenset({"www.sec.gov"})
_DATA: Final = frozenset({"data.sec.gov"})
_SOURCE_URL_POLICIES: Final[dict[str, _UrlFamilyPolicy]] = {
    "sec_bulk_submissions": _UrlFamilyPolicy(
        _WWW,
        exact_paths=("/Archives/edgar/daily-index/bulkdata/submissions.zip",),
    ),
    "sec_company_tickers_exchange": _UrlFamilyPolicy(
        _WWW,
        exact_paths=("/files/company_tickers_exchange.json",),
    ),
    "sec_company_tickers": _UrlFamilyPolicy(
        _WWW,
        exact_paths=("/files/company_tickers.json",),
    ),
    "sec_submissions_entity": _UrlFamilyPolicy(
        _DATA,
        path_pattern=re.compile(r"^/submissions/CIK[0-9]{10}\.json$"),
    ),
    "sec_submissions_historical": _UrlFamilyPolicy(
        _DATA,
        path_pattern=re.compile(r"^/submissions/CIK[0-9]{10}-submissions-[0-9]{3}\.json$"),
    ),
    # Decision 062 replaced the retired /corpfin/... path with the successor SEC published.
    # Exactly one exact path, as before: the family admits no second in-family URL, so the route
    # still reaches zero redirect hops and its derived A_reachable is unchanged at 6. Carrying
    # both paths would raise it to 7 and would leave a retired identity live-authorized.
    "sec_sic_code_list": _UrlFamilyPolicy(
        _WWW,
        exact_paths=("/search-filings/standard-industrial-classification-sic-code-list",),
    ),
    "sec_edgar_filing_calendar": _UrlFamilyPolicy(
        _WWW,
        exact_paths=(
            "/submit-filings/filer-support-resources/edgar-calendar",
            "/edgar/filer-information/calendar",
        ),
    ),
    "sec_edgar_calendar_announcement": _UrlFamilyPolicy(
        frozenset(_ALLOWED_HOSTS),
        manifest_exact=True,
    ),
    "sec_full_index_company": _UrlFamilyPolicy(
        _WWW,
        path_pattern=re.compile(
            r"^/Archives/edgar/full-index/(?:19[6-9][0-9]|20[0-9]{2})/"
            r"QTR[1-4]/company\.idx$"
        ),
    ),
}
if set(_SOURCE_URL_POLICIES) != set(SOURCES):
    missing = sorted(set(SOURCES) - set(_SOURCE_URL_POLICIES))
    extra = sorted(set(_SOURCE_URL_POLICIES) - set(SOURCES))
    message = f"structured URL policy coverage mismatch: missing={missing}, extra={extra}"
    raise AssertionError(message)


class RedirectBoundaryError(DisclosureDriftError):
    """Raised when a URL or redirect hop leaves the approved source boundary."""

    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class RedirectHop:
    """One validated redirect hop, recorded on the observation."""

    status: int
    from_url: str
    to_url: str

    def as_record(self) -> dict[str, object]:
        """Deterministic mapping for the catalog and audit projection."""
        return {"status": self.status, "from_url": self.from_url, "to_url": self.to_url}


def normalize_url(url: str) -> str:
    """Return the canonical form of ``url`` used for request identity.

    Scheme and host are lowercased, a default port is dropped, an empty path
    becomes ``/``, ``/./`` and empty segments are collapsed, query parameters are
    sorted, and the fragment is discarded. ``..`` segments are **not** resolved:
    a URL containing one is refused by :func:`validate_url` instead of being
    silently rewritten.
    """
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host if port is None or port in _DEFAULT_PORTS else f"{host}:{port}"
    segments = [segment for segment in parts.path.split("/") if segment not in {"", "."}]
    path = "/" + "/".join(segments)
    if parts.path.endswith("/") and len(path) > 1:
        path += "/"
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((parts.scheme.lower(), netloc, path, query, ""))


def request_identity(
    source_id: str,
    url: str,
    parameters: dict[str, str] | None = None,
) -> str:
    """Return the normalized identity of one logical request.

    Two retrievals share an identity only when the source, the normalized URL, and
    the rendered template parameters all agree. Snapshot reuse is permitted only
    within a single identity.
    """
    values = parameters or {}
    rendered = "&".join(f"{key}={values[key]}" for key in sorted(values))
    return f"{source_id}|{normalize_url(url)}|{rendered}"


def validate_url(
    url: str,
    spec: SourceSpec,
    *,
    role: str = "request",
    identity_url: str | None = None,
) -> str:
    """Validate one URL against the approved boundary and return its normalized form.

    Args:
        url: Absolute URL to validate.
        spec: Registered source the retrieval belongs to.
        role: What is being validated, used in the message: ``"request"``,
            ``"redirect hop"``, or ``"final URL"``.

    Raises:
        RedirectBoundaryError: the URL is outside the approved boundary.
    """
    stripped = url.strip()
    try:
        parts = urlsplit(stripped)
        port = parts.port
    except ValueError as exc:
        _refuse(
            f"{role} {url!r} has an invalid authority or port: {exc}",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if parts.scheme != "https":
        _refuse(
            f"{role} {url!r} does not use https; a scheme downgrade is never followed",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        _refuse(
            f"{role} {url!r} carries a user-info component",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    policy = _SOURCE_URL_POLICIES[spec.source_id]
    host = (parts.hostname or "").lower()
    if host not in policy.hosts:
        permitted = ", ".join(sorted(policy.hosts))
        _refuse(
            f"{role} {url!r} is outside this source's SEC host family (permitted: {permitted})",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if port is not None and port not in _DEFAULT_PORTS:
        _refuse(
            f"{role} {url!r} uses unexpected port {port}",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if parts.fragment:
        _refuse(
            f"{role} {url!r} carries a fragment, which is not part of an SEC request identity",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if any(character in parts.path for character in _AMBIGUOUS_PATH_CHARACTERS):
        _refuse(
            f"{role} {url!r} contains an encoded or ambiguous path character",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if ".." in parts.path.split("/"):
        _refuse(
            f"{role} {url!r} contains a relative path segment",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if any(segment in {"", "."} for segment in parts.path.split("/")[1:]):
        _refuse(
            f"{role} {url!r} contains an empty or dot path segment",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if filing_body_url_is_prohibited(url):
        _refuse(
            f"{role} {url!r} points at a filing body or accession document, which Stage "
            "M2.2 never retrieves",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )

    if policy.manifest_exact:
        if identity_url is None:
            _refuse(
                f"{role} for manifest-resolved source {spec.source_id!r} lacks its "
                "reviewed exact identity URL",
                "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
            )
        if normalize_url(stripped) != normalize_url(identity_url):
            _refuse(
                f"{role} {url!r} differs from the exact reviewed manifest URL",
                "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
            )
    elif parts.path not in policy.exact_paths and (
        policy.path_pattern is None or policy.path_pattern.fullmatch(parts.path) is None
    ):
        _refuse(
            f"{role} {url!r} escaped the structured path policy for {spec.source_id!r}",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )

    # An absent query string is not a malformed one. ``parse_qsl`` only gained a guard
    # for an empty ``qs`` in Python 3.12; on 3.10 and 3.11 ``strict_parsing=True``
    # raises "bad query field: ''" for every URL without a query, which would refuse
    # every registered SEC source. The emptiness check is done here so the boundary
    # behaves identically on every interpreter.
    query_pairs: list[tuple[str, str]] = []
    if parts.query:
        try:
            query_pairs = parse_qsl(parts.query, keep_blank_values=True, strict_parsing=True)
        except ValueError as exc:
            _refuse(
                f"{role} {url!r} carries a malformed query string: {exc}",
                "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
            )
    keys = [key for key, _ in query_pairs]
    unexpected = sorted(set(keys) - policy.permitted_query_keys)
    if unexpected:
        _refuse(
            f"{role} {url!r} carries unexpected query key(s) {unexpected}",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if not policy.allow_duplicate_query_keys and len(keys) != len(set(keys)):
        _refuse(
            f"{role} {url!r} carries duplicate query keys",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    return normalize_url(stripped)


def resolve_redirect(
    location: str,
    current_url: str,
    spec: SourceSpec,
    *,
    seen: tuple[str, ...],
    identity_url: str | None = None,
) -> str:
    """Validate one ``Location`` header and return the absolute next URL.

    Args:
        location: Raw ``Location`` header value, absolute or origin-relative.
        current_url: URL that produced the redirect.
        spec: Registered source.
        seen: Normalized URLs already visited on this chain.

    Raises:
        RedirectBoundaryError: the hop is outside the boundary, loops, or exceeds depth.
    """
    if not location.strip():
        _refuse(
            f"redirect from {current_url!r} carried no Location header",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    candidate = urljoin(current_url, location.strip())

    normalized = validate_url(
        candidate,
        spec,
        role="redirect hop",
        identity_url=identity_url,
    )
    if (spec.manifest_resolved or spec.source_id in _IDENTITY_BOUND_REDIRECT_SOURCES) and urlsplit(
        normalized
    ).path != urlsplit(normalize_url(current_url)).path:
        _refuse(
            f"redirect target {candidate!r} changed the identity-bound source path",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if normalized in seen:
        _refuse(
            f"redirect chain for {spec.source_id!r} loops back to {candidate!r}",
            "SEC_REDIRECT_DEPTH_EXCEEDED",
        )
    if len(seen) > MAX_REDIRECT_DEPTH:
        _refuse(
            f"redirect chain for {spec.source_id!r} exceeded {MAX_REDIRECT_DEPTH} hops",
            "SEC_REDIRECT_DEPTH_EXCEEDED",
        )
    return candidate


def validate_chain(
    initial_url: str,
    hops: tuple[RedirectHop, ...],
    final_url: str,
    spec: SourceSpec,
) -> tuple[str, ...]:
    """Validate an entire chain and return the normalized URLs in order.

    Used as a defence in depth: even when a transport followed redirects itself,
    every hop and the final URL are validated before the payload is trusted.

    Raises:
        RedirectBoundaryError: any hop or the final URL is outside the boundary.
    """
    if len(hops) > MAX_REDIRECT_DEPTH:
        _refuse(
            f"redirect chain for {spec.source_id!r} recorded {len(hops)} hops, above the "
            f"limit of {MAX_REDIRECT_DEPTH}",
            "SEC_REDIRECT_DEPTH_EXCEEDED",
        )
    chain = [
        validate_url(
            initial_url,
            spec,
            role="request",
            identity_url=initial_url,
        )
    ]
    initial_path = urlsplit(chain[0]).path
    for hop in hops:
        normalized = validate_url(
            hop.to_url,
            spec,
            role="redirect hop",
            identity_url=initial_url,
        )
        if (
            spec.manifest_resolved or spec.source_id in _IDENTITY_BOUND_REDIRECT_SOURCES
        ) and urlsplit(normalized).path != initial_path:
            _refuse(
                f"redirect hop {hop.to_url!r} changed the identity-bound source path",
                "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
            )
        if normalized in chain:
            _refuse(
                f"redirect chain for {spec.source_id!r} revisits {hop.to_url!r}",
                "SEC_REDIRECT_DEPTH_EXCEEDED",
            )
        chain.append(normalized)
    final = validate_url(
        final_url,
        spec,
        role="final URL",
        identity_url=initial_url,
    )
    if (spec.manifest_resolved or spec.source_id in _IDENTITY_BOUND_REDIRECT_SOURCES) and urlsplit(
        final
    ).path != initial_path:
        _refuse(
            f"final URL {final_url!r} changed the identity-bound source path",
            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        )
    if final != chain[-1]:
        chain.append(final)
    return tuple(chain)


def _refuse(message: str, reason_code: str) -> NoReturn:
    raise RedirectBoundaryError(message, reason_code)
