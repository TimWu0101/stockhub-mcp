"""CachePolicy: determines whether to cache, and builds cache keys.

Driven by ``MarketSessionResolver`` (T02) and the cache-strategy.md rules.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from stockhub_mcp.domain.market.session import MarketSessionResolver
from stockhub_mcp.enums import Market, MarketSession, QualityFlag

logger = logging.getLogger(__name__)

# Policy name constants (from cache-strategy.md §12)
POLICY_CN_LIVE_NO_CACHE = "cn_live_no_cache"
POLICY_CN_LUNCH_UNTIL_1300 = "cn_lunch_until_1300"
POLICY_CN_POST_CLOSE_UNTIL_NEXT_0900 = "cn_post_close_until_next_trading_day_0900"
POLICY_HK_LUNCH_UNTIL_1300 = "hk_lunch_until_1300"
POLICY_HK_POST_CLOSE_UNTIL_NEXT_0900 = "hk_post_close_until_next_trading_day_0900"
POLICY_US_PRE_MARKET_10S = "us_pre_market_10s"
POLICY_US_AFTER_HOURS_10S = "us_after_hours_10s"
POLICY_US_DEEP_OFFHOURS_300S = "us_deep_offhours_300s"
POLICY_WEEKEND_UNTIL_NEXT_0900 = "weekend_until_next_trading_day_0900"
POLICY_NO_CACHE = "no_cache"

# Quality flags that forbid caching
_LOW_QUALITY_FLAGS: set[str] = {
    QualityFlag.STALE.value,
    QualityFlag.DELAYED.value,
    QualityFlag.FALLBACK_LOW_CONFIDENCE.value,
}

# Market sessions where caching is NEVER allowed (trading is active)
_NO_CACHE_SESSIONS: set[MarketSession] = {
    MarketSession.PRE_OPENING,
    MarketSession.CONTINUOUS,
    MarketSession.AUCTION,
}


class CachePolicy:
    """Determine caching behaviour per market / session / quality.

    Usage::

        policy = CachePolicy()
        can_cache = policy.should_cache(Market.CN, session, QualityFlag.LIVE)
        if can_cache:
            expires = policy.get_expiry(Market.CN, session)
    """

    def __init__(self, session_resolver: Optional[MarketSessionResolver] = None) -> None:
        self._session = session_resolver or MarketSessionResolver()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def should_cache(
        self,
        market: Market,
        session: MarketSession,
        quality_flag: str,
        *,
        bypass_cache: bool = False,
    ) -> bool:
        """Return True if data may be written to the cache.

        Args:
            market: Market code.
            session: Current market session from ``MarketSessionResolver.detect()``.
            quality_flag: Quality flag value (``live``, ``delayed``, etc.).
            bypass_cache: True if the caller explicitly skipped the cache.

        Returns:
            True if caching is allowed.
        """
        # Explicit bypass
        if bypass_cache:
            logger.debug("Cache skipped: bypass_cache=True")
            return False

        # Unknown session – conservative: no cache
        if session == MarketSession.UNKNOWN:
            logger.debug("Cache skipped: unknown session")
            return False

        # Low-quality data
        if quality_flag in _LOW_QUALITY_FLAGS:
            logger.debug("Cache skipped: quality_flag=%s", quality_flag)
            return False

        # During active trading – no cache
        if session in _NO_CACHE_SESSIONS:
            return False

        return True

    def get_policy_name(
        self,
        market: Market,
        session: MarketSession,
    ) -> str:
        """Return the human-readable policy name for the current state.

        Used to populate the ``cache.policy`` field in responses.
        """
        if session in _NO_CACHE_SESSIONS:
            if market == Market.CN:
                return POLICY_CN_LIVE_NO_CACHE
            elif market == Market.HK:
                return POLICY_CN_LIVE_NO_CACHE  # reuse naming
            elif market == Market.US:
                return POLICY_CN_LIVE_NO_CACHE

        if session == MarketSession.LUNCH_BREAK:
            if market == Market.CN:
                return POLICY_CN_LUNCH_UNTIL_1300
            elif market == Market.HK:
                return POLICY_HK_LUNCH_UNTIL_1300

        if session == MarketSession.POST_CLOSE:
            if market in (Market.CN, Market.HK):
                if market == Market.CN:
                    return POLICY_CN_POST_CLOSE_UNTIL_NEXT_0900
                else:
                    return POLICY_HK_POST_CLOSE_UNTIL_NEXT_0900
            elif market == Market.US:
                return POLICY_US_AFTER_HOURS_10S

        if session == MarketSession.CLOSED:
            if market == Market.US:
                return POLICY_US_DEEP_OFFHOURS_300S
            # CN/HK closed days (weekend/holiday) → long cache
            return POLICY_WEEKEND_UNTIL_NEXT_0900

        if session == MarketSession.PRE_OPENING and market == Market.US:
            return POLICY_US_PRE_MARKET_10S

        return POLICY_NO_CACHE

    def get_expiry(
        self,
        market: Market,
        session: MarketSession,
        *,
        now: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """Return the absolute expiry datetime for a cache entry.

        Returns None when caching is not allowed for this session.

        Args:
            market: Market code.
            session: Current market session.
            now: Reference datetime (default: now UTC).
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # --- CN ---
        if market == Market.CN:
            if session == MarketSession.LUNCH_BREAK:
                # Cache until 13:00 local → 05:00 UTC
                return self._next_local_time(market, 13, 0)
            elif session in (MarketSession.POST_CLOSE, MarketSession.CLOSED):
                return self._next_trading_day_0900(market)
            else:
                return None

        # --- HK ---
        if market == Market.HK:
            if session == MarketSession.LUNCH_BREAK:
                return self._next_local_time(market, 13, 0)
            elif session in (MarketSession.POST_CLOSE, MarketSession.CLOSED):
                return self._next_trading_day_0900(market)
            else:
                return None

        # --- US ---
        if market == Market.US:
            if session == MarketSession.PRE_OPENING or session == MarketSession.POST_CLOSE:
                # 10-second TTL
                return now + timedelta(seconds=10)
            elif session == MarketSession.CLOSED:
                # 300-second TTL
                return now + timedelta(seconds=300)
            else:
                return None

        return None

    # ------------------------------------------------------------------
    # Cache key builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_key(
        tool: str,
        market: Market,
        instrument_type: str,
        symbol: str,
        source: str,
        session_state: str = "",
    ) -> str:
        """Build a canonical cache key.

        Format: ``quote:{tool}:{market}:{instrument_type}:{symbol}:{source}:{session}``

        Args:
            tool: Tool name, e.g. ``"get_realtime_quote"``.
            market: Market code value (``"CN"``, ``"HK"``, ``"US"``).
            instrument_type: ``"stock"``, ``"index"``, ``"etf"``.
            symbol: Internal standard symbol, e.g. ``"CN:600519"``.
            source: Data source name, e.g. ``"tx"``.
            session_state: Market session value (optional).

        Returns:
            Cache key string.
        """
        return f"quote:{tool}:{market.value if hasattr(market, 'value') else market}:{instrument_type}:{symbol}:{source}:{session_state}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _next_local_time(market: Market, hour: int, minute: int) -> datetime:
        """Return the next occurrence of *hour*:*minute* in market local time,
        expressed as a UTC datetime."""
        from zoneinfo import ZoneInfo

        tz_map = {
            Market.CN: "Asia/Shanghai",
            Market.HK: "Asia/Hong_Kong",
            Market.US: "America/New_York",
        }
        tz_name = tz_map.get(market, "UTC")
        tz = ZoneInfo(tz_name)

        now_local = datetime.now(tz)
        target = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target <= now_local:
            target += timedelta(days=1)

        return target.astimezone(timezone.utc)

    @staticmethod
    def _next_trading_day_0900(market: Market) -> datetime:
        """Return the next trading day at 09:00 local time, expressed as UTC.

        Uses a simple weekday-skip heuristic.  The caller can refine with
        ``TradingCalendar`` for holiday awareness.
        """
        from zoneinfo import ZoneInfo

        tz_map = {
            Market.CN: "Asia/Shanghai",
            Market.HK: "Asia/Hong_Kong",
            Market.US: "America/New_York",
        }
        tz_name = tz_map.get(market, "UTC")
        tz = ZoneInfo(tz_name)

        now_local = datetime.now(tz)
        target_date = now_local.date()

        # If it's already past 09:00 today, move to tomorrow
        if now_local.hour >= 9:
            target_date = now_local.date() + timedelta(days=1)

        # Skip weekends
        while target_date.weekday() >= 5:
            target_date += timedelta(days=1)

        target = datetime(target_date.year, target_date.month, target_date.day,
                          hour=9, minute=0, second=0, microsecond=0, tzinfo=tz)

        return target.astimezone(timezone.utc)
