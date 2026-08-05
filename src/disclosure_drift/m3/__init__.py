"""Milestone 3 operational surfaces.

Everything in this package is offline in Milestone 3.1: it opens no socket, constructs no
transport, and reads no live SEC data. Network permission for M3.1A is ``NONE`` and for M3.1B is
``ZERO LIVE REQUESTS``.

Milestone 3.2 adds controlled acquisition, and none of it exists yet. Its command surfaces are
recognized by the CLI and refuse; this package contains **no** acquisition module, and network
permission remains ``NONE`` until the separate per-window owner authorization that governs a live
window. Nothing here may be treated as evidence that a later gate has been satisfied.
"""

from __future__ import annotations

__all__: list[str] = []
