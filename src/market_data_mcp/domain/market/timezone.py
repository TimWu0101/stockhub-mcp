"""MarketTimezone: timezone, currency, and local-time helpers per market."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from market_data_mcp.enums import Market


class MarketTimezone:
    """Static lookup for timezone and currency metadata.

    Usage::

        tz = MarketTimezone.get_timezone(Market.CN)       # → "Asia/Shanghai"
        cur = MarketTimezone.get_currency(Market.US)       # → "USD"
        now = MarketTimezone.now_in_market(Market.HK)      # → datetime in HKT
    """

    # ------------------------------------------------------------------
    # Mappings
    # ------------------------------------------------------------------

    _TIMEZONE_MAP: dict[Market, str] = {
        Market.CN: "Asia/Shanghai",
        Market.HK: "Asia/Hong_Kong",
        Market.US: "America/New_York",
    }

    _CURRENCY_MAP: dict[Market, str] = {
        Market.CN: "CNY",
        Market.HK: "HKD",
        Market.US: "USD",
    }

    # ------------------------------------------------------------------
    # Public static methods
    # ------------------------------------------------------------------

    @classmethod
    def get_timezone(cls, market: Market) -> str:
        """Return the IANA timezone string for a market.

        Args:
            market: Market code.

        Returns:
            Timezone string, e.g. ``"Asia/Shanghai"``.  Falls back to ``"UTC"``.
        """
        return cls._TIMEZONE_MAP.get(market, "UTC")

    @classmethod
    def get_currency(cls, market: Market) -> str:
        """Return the ISO 4217 currency code for a market.

        Args:
            market: Market code.

        Returns:
            Currency code, e.g. ``"CNY"``.  Falls back to ``"USD"``.
        """
        return cls._CURRENCY_MAP.get(market, "USD")

    @classmethod
    def now_in_market(cls, market: Market) -> datetime:
        """Get the current datetime in the market's local timezone.

        Args:
            market: Market code.

        Returns:
            Timezone-aware ``datetime`` in the market's local time.
        """
        tz_name = cls.get_timezone(market)
        try:
            from zoneinfo import ZoneInfo
            return datetime.now(ZoneInfo(tz_name))
        except ImportError:
            # Fallback (unlikely given requires-python >= 3.11)
            return datetime.now(timezone.utc)

    @classmethod
    def now_utc(cls) -> datetime:
        """Return the current UTC datetime (timezone-aware)."""
        return datetime.now(timezone.utc)
