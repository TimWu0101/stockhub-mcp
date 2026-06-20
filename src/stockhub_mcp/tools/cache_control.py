"""Cache-control tool: scoped cache clearing and stats."""

from __future__ import annotations

import logging
from typing import Any, Optional

from stockhub_mcp.services.cache.store import FIFOCacheStore

logger = logging.getLogger(__name__)

# Shared singleton cache store (injected by server.py at startup).
_cache_store: Optional[FIFOCacheStore] = None


def set_cache_store(store: FIFOCacheStore) -> None:
    """Set the global cache-store singleton for cache-control tools."""
    global _cache_store
    _cache_store = store


def _get_store() -> FIFOCacheStore:
    """Return the active cache store, creating a default one if needed."""
    global _cache_store
    if _cache_store is None:
        _cache_store = FIFOCacheStore()
    return _cache_store


# ------------------------------------------------------------------
# Tool implementations
# ------------------------------------------------------------------


def clear_cache_impl(
    scope: str,
    *,
    market: Optional[str] = None,
    symbol: Optional[str] = None,
    tool: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Clear cache entries by scope.

    Args:
        scope: ``symbol`` / ``market`` / ``tool`` / ``all``.
        market: Filter by market code (e.g. ``"CN"``).
        symbol: Filter by internal symbol (substring match).
        tool: Filter by tool name (substring match).
        dry_run: If True, only report matched count without deleting.

    Returns:
        Dict suitable for ``ClearCacheResponse``.
    """
    store = _get_store()

    # Build match patterns
    patterns: list[str] = []

    if scope == "symbol":
        if not symbol:
            raise ValueError("scope=symbol requires a 'symbol' filter")
        patterns.append(symbol)
    elif scope == "market":
        if not market:
            raise ValueError("scope=market requires a 'market' filter")
        patterns.append(market.upper())
    elif scope == "tool":
        if not tool:
            raise ValueError("scope=tool requires a 'tool' filter")
        patterns.append(tool)
    elif scope == "all":
        # Match everything
        patterns.append("")
    else:
        raise ValueError(
            f"Unknown scope '{scope}'. Must be one of: symbol, market, tool, all."
        )

    # Find all matching keys (union of pattern matches)
    matched_keys: set[str] = set()
    for pat in patterns:
        if pat:
            matched_keys.update(store.match(pat))
        else:
            matched_keys.update(store.keys())

    matched_count = len(matched_keys)
    deleted_count = 0

    if not dry_run:
        deleted_count = store.delete(list(matched_keys))
        logger.info(
            "cache clear: scope=%s matched=%d deleted=%d",
            scope, matched_count, deleted_count,
        )

    return {
        "scope": scope,
        "matched_count": matched_count,
        "deleted_count": deleted_count if not dry_run else 0,
        "dry_run": dry_run,
        "filters": {
            "market": market,
            "symbol": symbol,
            "tool": tool,
        },
    }


def get_cache_stats_impl() -> dict[str, Any]:
    """Return current cache statistics.

    Returns:
        Dict with ``size``, ``max_size``, and ``expired_count``.
    """
    store = _get_store()
    return {
        "size": store.size,
        "max_size": store.max_size,
        "expired_count": len(store.expired_keys()),
    }
