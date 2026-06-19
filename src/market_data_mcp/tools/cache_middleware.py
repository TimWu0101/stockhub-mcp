"""CacheMiddleware: decorator-style wrapper for price-class tools.

Implements the "clear-all-cache-during-trading" strategy (§12):

1. On every request: if ``is_trading`` → ``cache_store.clear()``
2. Build a lookup key → check ``FIFOCacheStore``
3. Hit + not expired → return cached response with cache meta injected
4. Miss → execute the tool function → evaluate ``CachePolicy.should_cache()``
5. If cacheable → write to store → inject cache meta into response
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional

from market_data_mcp.config import settings
from market_data_mcp.domain.market.session import MarketSessionResolver
from market_data_mcp.enums import Market, MarketSession, QualityFlag
from market_data_mcp.services.cache.store import FIFOCacheStore
from market_data_mcp.services.cache.policy import CachePolicy

logger = logging.getLogger(__name__)


class CacheMiddleware:
    """Transparent cache layer for price-class MCP tools.

    Usage::

        middleware = CacheMiddleware()
        wrapped = middleware.wrap(quote_impl, "get_realtime_quote")
        result = await wrapped(symbol="600519", market="CN", bypass_cache=False)
    """

    def __init__(
        self,
        *,
        cache_store: Optional[FIFOCacheStore] = None,
        cache_policy: Optional[CachePolicy] = None,
        session_resolver: Optional[MarketSessionResolver] = None,
    ) -> None:
        self._store = cache_store or FIFOCacheStore()
        self._policy = cache_policy or CachePolicy()
        self._session = session_resolver or MarketSessionResolver()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def wrap(
        self,
        tool_func: Callable[..., Any],
        tool_name: str,
    ) -> Callable[..., Any]:
        """Return an async function that wraps *tool_func* with caching.

        Args:
            tool_func: The async implementation function.  Must accept
                       keyword arguments including at least ``market``,
                       ``symbol``, and ``bypass_cache``.
            tool_name: Canonical tool name for cache-key construction.

        Returns:
            An async callable with the same signature as *tool_func*.
        """

        @wraps(tool_func)
        async def wrapped(**kwargs: Any) -> dict[str, Any]:
            bypass_cache: bool = kwargs.get("bypass_cache", False)
            market_raw: str = kwargs.get("market", "")
            symbol_raw: str = kwargs.get("symbol", "")

            # Resolve market for session check
            market = self._resolve_market(market_raw)

            # ------------------------------------------------------------------
            # Step 1: Clear cache during active trading (§12 盘中全清)
            # ------------------------------------------------------------------
            if self._session.is_trading(market):
                cleared = self._store.clear()
                if cleared:
                    logger.info(
                        "cache cleared during trading: market=%s count=%d",
                        market.value, cleared,
                    )

            # ------------------------------------------------------------------
            # Step 2: Build lookup key + probe cache
            # ------------------------------------------------------------------
            if not bypass_cache:
                lookup_key = self._build_lookup_key(tool_name, kwargs)
                entry = self._store.get(lookup_key)

                if entry and not self._is_expired(entry):
                    # Cache hit – return stored response with cache-hit meta
                    logger.debug("cache hit: key=%s", lookup_key)
                    result: dict[str, Any] = entry["value"]
                    result["cache"] = self._build_cache_info(
                        entry, hit=True, policy=None,
                    )
                    return result

            # ------------------------------------------------------------------
            # Step 3: Cache miss – execute the tool function
            # ------------------------------------------------------------------
            result = await tool_func(**kwargs)

            # Do not cache errors or partial results
            if not result.get("success"):
                return result

            if bypass_cache:
                result["cache"] = {
                    "hit": False,
                    "expires_at": None,
                    "ttl_remaining": None,
                    "cached_at": None,
                    "policy": None,
                    "bypass_cache": True,
                }
                return result

            # ------------------------------------------------------------------
            # Step 4: Decide whether to cache the fresh result
            # ------------------------------------------------------------------
            meta = result.get("meta", {})
            session = self._resolve_session(meta.get("market_session", ""))
            quality_flag: str = meta.get("quality_flag", "")
            source: str = meta.get("source", "")
            symbol: str = meta.get("symbol", "")
            inst_type: str = self._extract_instrument_type(result)

            can_cache = self._policy.should_cache(market, session, quality_flag)

            if can_cache:
                # Use the same lookup key for writing
                lookup_key = self._build_lookup_key(tool_name, kwargs)
                expiry = self._policy.get_expiry(market, session)
                self._store.set(lookup_key, result, expires_at=expiry)

                # Build cache-info dict
                entry = self._store.get(lookup_key) or {}
                result["cache"] = self._build_cache_info(
                    entry, hit=False,
                    policy=self._policy.get_policy_name(market, session),
                )

                logger.debug(
                    "cache write: key=%s policy=%s market=%s session=%s",
                    lookup_key,
                    self._policy.get_policy_name(market, session),
                    market.value, session.value,
                )
            else:
                result["cache"] = {
                    "hit": False,
                    "expires_at": None,
                    "ttl_remaining": None,
                    "cached_at": None,
                    "policy": None,
                    "bypass_cache": False,
                }

            return result

        return wrapped

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_market(raw: str) -> Market:
        """Parse a market string into a ``Market`` enum."""
        if not raw:
            return Market.CN
        try:
            return Market(raw.upper())
        except ValueError:
            return Market.CN

    @staticmethod
    def _resolve_session(raw: str) -> MarketSession:
        """Parse a session string into a ``MarketSession`` enum."""
        if not raw:
            return MarketSession.UNKNOWN
        try:
            return MarketSession(raw.lower())
        except ValueError:
            return MarketSession.UNKNOWN

    @staticmethod
    def _extract_instrument_type(result: dict[str, Any]) -> str:
        """Extract instrument_type from a tool response's data payload."""
        data = result.get("data", {})
        if isinstance(data, dict):
            return data.get("instrument_type", "")
        return ""

    @staticmethod
    def _build_lookup_key(tool_name: str, kwargs: dict[str, Any]) -> str:
        """Build a deterministic cache-lookup key from the tool's arguments.

        Format: ``{tool}:{market}:{symbol}:{extra_params_hash}``
        """
        market = kwargs.get("market", "") or ""
        symbol = kwargs.get("symbol", "") or ""

        # Collect extra params that differentiate requests
        extra_parts: list[str] = []
        for k in sorted(kwargs.keys()):
            if k in ("market", "symbol", "bypass_cache"):
                continue
            v = kwargs[k]
            if v is not None and v != "":
                if isinstance(v, list):
                    extra_parts.append(f"{k}={','.join(sorted(str(x) for x in v))}")
                else:
                    extra_parts.append(f"{k}={v}")

        extra = ":".join(extra_parts) if extra_parts else "default"
        return f"{tool_name}:{market}:{symbol}:{extra}"

    @staticmethod
    def _is_expired(entry: dict[str, Any]) -> bool:
        """Return True if the cache entry has an ``expires_at`` in the past."""
        expires = entry.get("expires_at")
        if expires is None:
            return False
        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires)
            except (ValueError, TypeError):
                return False
        if isinstance(expires, datetime):
            return expires <= datetime.now(timezone.utc)
        return False

    @staticmethod
    def _build_cache_info(
        entry: dict[str, Any],
        *,
        hit: bool,
        policy: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build the ``cache`` dict injected into tool responses."""
        expires_at: Optional[str] = None
        ttl_remaining: Optional[int] = None
        cached_at: Optional[str] = None

        if entry:
            exp: Any = entry.get("expires_at")
            if isinstance(exp, datetime):
                expires_at = exp.isoformat()
                remaining = (exp - datetime.now(timezone.utc)).total_seconds()
                ttl_remaining = max(0, int(remaining))
            elif isinstance(exp, str):
                expires_at = exp
                try:
                    exp_dt = datetime.fromisoformat(exp)
                    remaining = (exp_dt - datetime.now(timezone.utc)).total_seconds()
                    ttl_remaining = max(0, int(remaining))
                except (ValueError, TypeError):
                    pass

            cat: Any = entry.get("cached_at")
            if isinstance(cat, datetime):
                cached_at = cat.isoformat()
            elif isinstance(cat, str):
                cached_at = cat

        return {
            "hit": hit,
            "expires_at": expires_at,
            "ttl_remaining": ttl_remaining,
            "cached_at": cached_at,
            "policy": policy,
            "bypass_cache": False,
        }
