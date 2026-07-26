"""SEC universe, inventory, and ingestion support (Milestone 2).

Stage M2.1 contains offline logic only: identity parsing, temporal policy,
availability comparison, response classification, rate limiting, source
addressing, schema-drift policy, and the CompanyFacts guard. No module in this
package imports an HTTP client or opens a socket during Stage M2.1.
"""

from __future__ import annotations

__all__: list[str] = []
