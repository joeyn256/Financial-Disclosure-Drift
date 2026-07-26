"""SEC identity parsing (Decision 007 section 1, Decision 008 section 1).

CIK is the canonical issuer identifier; the accession number is the canonical
filing identifier. The first ten digits of an accession identify the **submitter**
CIK and are never treated automatically as the registrant CIK.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "CIK_MAX",
    "CIK_MIN",
    "CIK_PADDED_WIDTH",
    "Accession",
    "IdentifierError",
    "cik_padded",
    "normalize_cik",
    "parse_accession",
]

_DASHED: Final = re.compile(r"^(\d{10})-(\d{2})-(\d{6})$")
_PLAIN: Final = re.compile(r"^(\d{10})(\d{2})(\d{6})$")
_CIK_DIGITS: Final = re.compile(r"^(?:CIK)?([0-9]+)$")
CIK_MIN: Final = 1
CIK_MAX: Final = 9_999_999_999
CIK_PADDED_WIDTH: Final = 10


class IdentifierError(DisclosureDriftError):
    """Raised when an SEC identifier is malformed."""


@dataclass(frozen=True, slots=True)
class Accession:
    """A parsed accession number.

    Attributes:
        raw: The input string, preserved verbatim.
        dashed: Canonical ``NNNNNNNNNN-NN-NNNNNN`` form.
        plain: Eighteen digits without separators.
        submitter_cik_numeric: Submitter CIK from the prefix. **Not** the registrant.
        year_fragment: The two-digit year fragment as filed.
        sequence: The six-digit sequence number.
    """

    raw: str
    dashed: str
    plain: str
    submitter_cik_numeric: int
    year_fragment: str
    sequence: str

    @property
    def submitter_cik_padded(self) -> str:
        """Ten-character zero-padded submitter CIK."""
        return f"{self.submitter_cik_numeric:010d}"


def parse_accession(value: str) -> Accession:
    """Parse an accession number in dashed or plain form.

    Raises:
        IdentifierError: the value is not a valid accession number.
    """
    candidate = value.strip()
    if not candidate:
        message = "accession number is empty"
        raise IdentifierError(message)

    match = _DASHED.match(candidate) or _PLAIN.match(candidate)
    if match is None:
        message = (
            f"malformed accession number {value!r}\n"
            "Fix: use NNNNNNNNNN-NN-NNNNNN or eighteen digits."
        )
        raise IdentifierError(message)

    prefix, year_fragment, sequence = match.groups()
    return Accession(
        raw=value,
        dashed=f"{prefix}-{year_fragment}-{sequence}",
        plain=f"{prefix}{year_fragment}{sequence}",
        submitter_cik_numeric=int(prefix),
        year_fragment=year_fragment,
        sequence=sequence,
    )


def normalize_cik(value: str | int) -> tuple[int, str]:
    """Return ``(cik_numeric, cik_padded)`` for a canonical CIK.

    A CIK is an unsigned decimal integer from 1 through 9,999,999,999.

    String input must be decimal digits only, optionally preceded by a literal
    ``CIK`` prefix. Signs, surrounding or embedded whitespace, decimal points,
    scientific notation, and digit separators are all rejected rather than
    stripped. Leading zeroes are accepted as representation and normalized away.

    Integer input must not be a boolean and must fall inside the valid range.

    Raises:
        IdentifierError: the value is not a usable CIK.
    """
    if isinstance(value, bool):
        message = (
            f"CIK must not be a boolean, received {value!r}\n"
            "Fix: supply an unsigned decimal integer or a digits-only string."
        )
        raise IdentifierError(message)

    if isinstance(value, int):
        numeric = value
    else:
        match = _CIK_DIGITS.match(value)
        if match is None:
            message = (
                f"malformed CIK {value!r}\n"
                "Fix: supply decimal digits only, optionally zero-padded or prefixed "
                "with CIK. Signs, whitespace, decimal points, exponents, and separators "
                "are not accepted."
            )
            raise IdentifierError(message)
        digits = match.group(1)
        if len(digits.lstrip("0")) > CIK_PADDED_WIDTH:
            message = (
                f"CIK {value!r} has more than {CIK_PADDED_WIDTH} significant digits\n"
                f"Fix: a CIK is at most {CIK_MAX}."
            )
            raise IdentifierError(message)
        numeric = int(digits)

    if not CIK_MIN <= numeric <= CIK_MAX:
        message = (
            f"CIK {value!r} is outside the valid range {CIK_MIN} to {CIK_MAX}\n"
            "Fix: zero is not a CIK, and values above the maximum are not valid."
        )
        raise IdentifierError(message)
    return numeric, f"{numeric:0{CIK_PADDED_WIDTH}d}"


def cik_padded(value: str | int) -> str:
    """Return only the ten-character zero-padded CIK."""
    return normalize_cik(value)[1]
