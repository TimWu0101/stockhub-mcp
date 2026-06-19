"""MarketSessionResolver: determine current trading session for a market.

Key use: ``is_trading`` boolean drives the "clear-all-cache-during-trading"
logic in the cache layer.
"""

from __future__ import annotations

from datetime import datetime, time, timezone, timedelta
from typing import Optional

from market_data_mcp.enums import Market, MarketSession


# ---------------------------------------------------------------------------
# Trading schedule definitions (all times in market-local time)
# ---------------------------------------------------------------------------

# A-share: 9:15–11:30, 13:00–15:00 (with lunch break)
_CN_PRE_OPENING_START = time(9, 15)
_CN_PRE_OPENING_END = time(9, 25)
_CN_MORNING_START = time(9, 30)
_CN_MORNING_END = time(11, 30)
_CN_AFTERNOON_START = time(13, 0)
_CN_AFTERNOON_END = time(15, 0)
_CN_POST_CLOSE_END = time(15, 30)

# HK: 9:00–12:00, 13:00–16:00; closing auction 16:00–16:10
_HK_PRE_OPENING_START = time(9, 0)
_HK_PRE_OPENING_END = time(9, 30)
_HK_MORNING_START = time(9, 30)
_HK_MORNING_END = time(12, 0)
_HK_AFTERNOON_START = time(13, 0)
_HK_AFTERNOON_END = time(16, 0)
_HK_AUCTION_END = time(16, 10)

# US: pre-market 4:00–9:30, regular 9:30–16:00, post-market 16:00–20:00 ET
_US_PRE_MARKET_START = time(4, 0)
_US_PRE_MARKET_END = time(9, 30)
_US_REGULAR_START = time(9, 30)
_US_REGULAR_END = time(16, 0)
_US_POST_MARKET_END = time(20, 0)

# Session labels returned when market is closed.
_CLOSED_SESSION_MAP: dict[Market, MarketSession] = {
    Market.CN: MarketSession.CLOSED,
    Market.HK: MarketSession.CLOSED,
    Market.US: MarketSession.CLOSED,
}


class MarketSessionResolver:
    """Detect the current trading session for any supported market.

    Also exposes ``is_trading`` – a boolean used by the cache layer to decide
    whether to clear all cache entries during active trading hours.

    Usage::

        resolver = MarketSessionResolver()
        session = resolver.detect(Market.CN)
        if resolver.is_trading(Market.CN):
            ...  # clear cache, don't write
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, market: Market, dt: Optional[datetime] = None) -> MarketSession:
        """Determine the current market session.

        Args:
            market: The market to check.
            dt: A timezone-aware datetime to evaluate (default: now in market timezone).

        Returns:
            The ``MarketSession`` enum value.
        """
        if dt is None:
            dt = self._now_in_market(market)

        t = dt.time()
        weekday = dt.weekday()  # Monday=0 .. Sunday=6

        # Weekends are always closed.
        if market in (Market.CN, Market.HK):
            if weekday >= 5:  # Saturday / Sunday
                return MarketSession.CLOSED
        elif market == Market.US:
            if weekday >= 5:  # Saturday / Sunday
                return MarketSession.CLOSED

        if market == Market.CN:
            return self._detect_cn(t)
        elif market == Market.HK:
            return self._detect_hk(t)
        elif market == Market.US:
            return self._detect_us(t)
        else:
            return MarketSession.UNKNOWN

    def is_trading(self, market: Market, dt: Optional[datetime] = None) -> bool:
        """Return True if the market is currently in a trading phase where
        cache should be cleared and not written.

        "Trading" phases include: pre_opening, continuous, auction.
        Cache is disabled (cleared, not written) during these phases.
        """
        session = self.detect(market, dt)
        return session in (
            MarketSession.PRE_OPENING,
            MarketSession.CONTINUOUS,
            MarketSession.AUCTION,
        )

    # ------------------------------------------------------------------
    # Market-specific detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_cn(t: time) -> MarketSession:
        """Detect session for A-share (CN)."""
        if _CN_PRE_OPENING_START <= t < _CN_PRE_OPENING_END:
            return MarketSession.PRE_OPENING
        elif _CN_PRE_OPENING_END <= t < _CN_MORNING_START:
            # Brief gap between pre-opening end and continuous start
            return MarketSession.PRE_OPENING
        elif _CN_MORNING_START <= t < _CN_MORNING_END:
            return MarketSession.CONTINUOUS
        elif _CN_MORNING_END <= t < _CN_AFTERNOON_START:
            return MarketSession.LUNCH_BREAK
        elif _CN_AFTERNOON_START <= t < _CN_AFTERNOON_END:
            return MarketSession.CONTINUOUS
        elif _CN_AFTERNOON_END <= t < _CN_POST_CLOSE_END:
            return MarketSession.POST_CLOSE
        else:
            return MarketSession.CLOSED

    @staticmethod
    def _detect_hk(t: time) -> MarketSession:
        """Detect session for Hong Kong (HK)."""
        if _HK_PRE_OPENING_START <= t < _HK_PRE_OPENING_END:
            return MarketSession.PRE_OPENING
        elif _HK_MORNING_START <= t < _HK_MORNING_END:
            return MarketSession.CONTINUOUS
        elif _HK_MORNING_END <= t < _HK_AFTERNOON_START:
            return MarketSession.LUNCH_BREAK
        elif _HK_AFTERNOON_START <= t < _HK_AFTERNOON_END:
            return MarketSession.CONTINUOUS
        elif _HK_AFTERNOON_END <= t < _HK_AUCTION_END:
            return MarketSession.AUCTION
        elif _HK_AUCTION_END <= t:
            return MarketSession.POST_CLOSE
        else:
            return MarketSession.CLOSED

    @staticmethod
    def _detect_us(t: time) -> MarketSession:
        """Detect session for US (NYSE/NASDAQ)."""
        if _US_PRE_MARKET_START <= t < _US_PRE_MARKET_END:
            return MarketSession.PRE_OPENING
        elif _US_REGULAR_START <= t < _US_REGULAR_END:
            return MarketSession.CONTINUOUS
        elif _US_REGULAR_END <= t < _US_POST_MARKET_END:
            return MarketSession.POST_CLOSE
        else:
            return MarketSession.CLOSED

    # ------------------------------------------------------------------
    # Timezone helpers
    # ------------------------------------------------------------------

    _TIMEZONE_MAP: dict[Market, str] = {
        Market.CN: "Asia/Shanghai",
        Market.HK: "Asia/Hong_Kong",
        Market.US: "America/New_York",
    }

    @classmethod
    def _now_in_market(cls, market: Market) -> datetime:
        """Get the current datetime in the market's local timezone."""
        tz_name = cls._TIMEZONE_MAP.get(market, "UTC")
        try:
            from zoneinfo import ZoneInfo  # Python 3.9+
            tz = ZoneInfo(tz_name)
        except ImportError:
            # Fallback for older Python – unlikely given requires-python >= 3.11
            offset_map = {
                "Asia/Shanghai": 8,
                "Asia/Hong_Kong": 8,
                "America/New_York": -5,
            }
            offset_hours = offset_map.get(tz_name, 0)
            tz = timezone(timedelta(hours=offset_hours))
        return datetime.now(tz)
