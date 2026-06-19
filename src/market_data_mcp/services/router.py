"""SourceRouter: route queries to data sources by market priority.

Uses ``config.source_priority`` to determine primary and fallback
source lists per market scope.
"""

from __future__ import annotations

import logging
from typing import Optional

from market_data_mcp.config import settings
from market_data_mcp.enums import Market

logger = logging.getLogger(__name__)


class SourceRouter:
    """Map a market to an ordered list of data source names.

    Usage::

        router = SourceRouter()
        primary = router.get_primary(Market.CN)       # → ["tx"]
        fallback = router.get_fallback(Market.CN)      # → ["sina"]
    """

    def __init__(self, priority_map: Optional[dict[str, list[str]]] = None) -> None:
        """Initialise with an optional priority override.

        Args:
            priority_map: Dict mapping market‑scope to source-name list.
                          Defaults to ``settings.source_priority``.
        """
        self._priority = priority_map or settings.source_priority

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_primary(self, market: Market, scope: str = "") -> str:
        """Return the first (highest-priority) source name for a market.

        Args:
            market: Market code.
            scope: Sub-scope (``""`` for quote, ``"history"``, ``"sector"``).
                   Uses ``"{market}_{scope}"`` or ``"{market}"`` lookup.

        Returns:
            Source name string, or empty string if no source is configured.
        """
        sources = self._lookup(market, scope)
        return sources[0] if sources else ""

    def get_fallback(self, market: Market, scope: str = "") -> list[str]:
        """Return fallback sources (all after the primary).

        Args:
            market: Market code.
            scope: Sub-scope.

        Returns:
            List of source names (may be empty).
        """
        sources = self._lookup(market, scope)
        return sources[1:] if len(sources) > 1 else []

    def get_all(self, market: Market, scope: str = "") -> list[str]:
        """Return the full priority list for a market/scope."""
        return self._lookup(market, scope)

    def get_by_name(self, name: str) -> list[str]:
        """Look up priority list by exact key name (for custom scopes)."""
        return self._priority.get(name, [])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _lookup(self, market: Market, scope: str) -> list[str]:
        """Look up sources: try ``"{market}_{scope}"`` first, then ``"{market}"``."""
        market_val = market.value if hasattr(market, "value") else str(market)

        if scope:
            key = f"{market_val}_{scope}"
            if key in self._priority:
                return self._priority[key]

        return self._priority.get(market_val, [])
