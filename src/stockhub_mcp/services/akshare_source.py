"""AkShareSource: A-share calendar & auxiliary data via the akshare library.

Used for trading calendars, holiday lookups, and supplementary data
that other sources do not provide.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Any, Optional

from stockhub_mcp.config import settings
from stockhub_mcp.enums import Market
from stockhub_mcp.models.quote import QuoteData
from stockhub_mcp.models.history import HistoryData
from stockhub_mcp.services.base import BaseDataSource

logger = logging.getLogger(__name__)


class AkShareSource(BaseDataSource):
    """AkShare data source for A-share calendar and auxiliary data.

    Uses the ``akshare`` Python library for trading-date queries,
    holiday lists, and supplementary market metadata.
    """

    SUPPORTED_MARKETS: frozenset[Market] = frozenset([Market.CN])

    @property
    def name(self) -> str:
        return "akshare"

    # ------------------------------------------------------------------
    # BaseDataSource interface
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """Check that the ``akshare`` library is importable."""
        return self._check_import("akshare")

    def fetch_quote(
        self,
        symbol: str,
        market: Market,
        *,
        bypass_cache: bool = False,
    ) -> QuoteData:
        """AkShare does not provide real-time quotes in V0.1."""
        raise NotImplementedError(
            "AkShare source does not provide real-time quotes."
        )

    def fetch_history(
        self,
        symbol: str,
        market: Market,
        period: str = "1mo",
        interval: str = "1d",
        *,
        adjust: str = "qfq",
    ) -> HistoryData:
        """AkShare history is available but not the primary path in V0.1."""
        raise NotImplementedError(
            "AkShare source does not provide history via this interface."
        )

    # ------------------------------------------------------------------
    # Trading calendar (delegated from TradingCalendar domain layer)
    # ------------------------------------------------------------------

    def is_trading_day(self, market: Market, check_date: date) -> bool:
        """Check if *check_date* is an A-share trading day.

        Args:
            market: Must be ``Market.CN``.
            check_date: Date to check.

        Returns:
            True if it is a trading day; False for weekends/holidays.
            Fails open (assumes trading day) on error.
        """
        if market != Market.CN:
            return True  # Unknown market → assume trading day

        # Weekends are never trading days
        if check_date.weekday() >= 5:
            return False

        try:
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
            if df is None or df.empty:
                logger.warning("akshare returned empty trade-date data; assuming trading day")
                return True

            date_str = check_date.strftime("%Y-%m-%d")
            trade_dates = set(df["trade_date"].astype(str).values)
            return date_str in trade_dates
        except Exception:
            logger.warning(
                "akshare trade-date lookup failed; assuming trading day",
                extra={"date": check_date.isoformat()},
                exc_info=True,
            )
            return True

    def get_holidays(
        self,
        from_date: date,
        to_date: date,
    ) -> list[dict[str, str]]:
        """Return A-share holidays within a date range.

        Args:
            from_date: Start date.
            to_date: End date.

        Returns:
            List of ``{"date": "YYYY-MM-DD", "name": "...", "type": "public_holiday"}``.
        """
        try:
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
            if df is None or df.empty:
                logger.warning("akshare returned empty trade-date data")
                return []

            trade_dates = set(df["trade_date"].astype(str).values)
            holidays: list[dict[str, str]] = []

            cursor = from_date
            while cursor <= to_date:
                if cursor.weekday() < 5:  # Weekday only
                    date_str = cursor.strftime("%Y-%m-%d")
                    if date_str not in trade_dates:
                        holidays.append({
                            "date": date_str,
                            "name": "休市",
                            "type": "public_holiday",
                        })
                cursor += timedelta(days=1)

            return holidays
        except Exception:
            logger.warning(
                "akshare holiday lookup failed; returning empty list",
                exc_info=True,
            )
            return []

    def get_trade_dates(
        self,
        from_date: date,
        to_date: date,
    ) -> list[str]:
        """Return all trading dates within a range.

        Args:
            from_date: Start date.
            to_date: End date.

        Returns:
            List of date strings ``"YYYY-MM-DD"``.
        """
        try:
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
            if df is None or df.empty:
                return []

            trade_dates = sorted(set(df["trade_date"].astype(str).values))
            return [d for d in trade_dates if from_date.strftime("%Y-%m-%d") <= d <= to_date.strftime("%Y-%m-%d")]
        except Exception:
            logger.warning("akshare get_trade_dates failed", exc_info=True)
            return []
