"""SEC universe, inventory, and ingestion support (Milestone 2).

Stage M2.2 adds the approved-source registry, isolated optional HTTP adapter,
immutable source observations, defensive archive handling, source-native parsers,
transactional registrant census, restart recovery, and deterministic QA. Ordinary
package imports remain network-free; only an explicit enabled census command can
construct the isolated transport.
"""

from __future__ import annotations

__all__: list[str] = []
