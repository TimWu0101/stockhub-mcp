"""TradingCalendar: trading-day and holiday queries.

A-share uses akshare; HK/US use yfinance data-availability heuristics.
No early-close special handling in V0.1.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from market_data_mcp.enums import Market

logger = logging.getLogger(__name__)


class TradingCalendar:
    """Query trading days and holidays for a given market.

    Usage::

        cal = TradingCalendar()
        cal.is_trading_day(Market.CN, date.today())
        cal.next_trading_day(Market.US, date.today())
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_trading_day(self, market: Market, check_date: Optional[date] = None) -> bool:
        """Return True if *check_date* is a regular trading day.

        Args:
            market: The market to check.
            check_date: Date to query (default: today in market timezone).

        Returns:
            True if the market is open for trading on this date.
        """
        if check_date is None:
            check_date = self._today(market)

        # Weekends are never trading days for any market.
        if check_date.weekday() >= 5:
            return False

        if market == Market.CN:
            return self._cn_is_trading_day(check_date)
        elif market in (Market.HK, Market.US):
            return self._non_cn_is_trading_day(market, check_date)
        else:
            return False

    def next_trading_day(
        self, market: Market, from_date: Optional[date] = None
    ) -> date:
        """Return the next trading day on or after *from_date*.

        Args:
            market: Market code.
            from_date: Start date (default: today).

        Returns:
            The next date that is a trading day.
        """
        if from_date is None:
            from_date = self._today(market)

        cursor = from_date
        # Safety limit: search up to 30 days forward
        for _ in range(30):
            if self.is_trading_day(market, cursor):
                return cursor
            cursor += timedelta(days=1)

        # Fallback: return a weekday
        logger.warning(
            "next_trading_day exhausted search range",
            extra={"market": market.value, "from_date": from_date.isoformat()},
        )
        while cursor.weekday() >= 5:
            cursor += timedelta(days=1)
        return cursor

    def get_holidays(
        self,
        market: Market,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[dict]:
        """Return holidays within a date range.

        Args:
            market: Market code.
            from_date: Start date (default: today).
            to_date: End date (default: 30 days from today).

        Returns:
            List of ``{"date": "YYYY-MM-DD", "name": "...", "type": "public_holiday"}``
            dicts.
        """
        if from_date is None:
            from_date = self._today(market)
        if to_date is None:
            to_date = from_date + timedelta(days=30)

        if market == Market.CN:
            return self._cn_get_holidays(from_date, to_date)
        elif market in (Market.HK, Market.US):
            return self._non_cn_get_holidays(market, from_date, to_date)
        else:
            return []

    # ------------------------------------------------------------------
    # CN: akshare
    # ------------------------------------------------------------------

    @staticmethod
    def _cn_is_trading_day(check_date: date) -> bool:
        """Use akshare to check if a date is an A-share trading day."""
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
            return True  # Fail open: assume it's a trading day

    @staticmethod
    def _cn_get_holidays(from_date: date, to_date: date) -> list[dict]:
        """Return A-share holidays via akshare."""
        try:
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
            if df is None or df.empty:
                logger.warning("akshare returned empty trade-date data; no holidays found")
                return []

            trade_dates = set(df["trade_date"].astype(str).values)
            holidays: list[dict] = []

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

    # ------------------------------------------------------------------
    # HK / US: yfinance data-availability heuristic
    # ------------------------------------------------------------------

    @staticmethod
    def _non_cn_is_trading_day(market: Market, check_date: date) -> bool:
        """Use yfinance to infer whether a date had trading activity.

        Downloads 1 day of 1m data for a benchmark ticker.  If the
        returned DataFrame is empty we assume it was a non-trading day.
        """
        ticker_map = {
            Market.HK: "0700.HK",
            Market.US: "AAPL",
        }
        ticker = ticker_map.get(market)
        if ticker is None:
            return True

        try:
            import yfinance as yf

            end_date = check_date + timedelta(days=1)
            df = yf.download(
                ticker,
                start=check_date.isoformat(),
                end=end_date.isoformat(),
                interval="1d",
                progress=False,
                auto_adjust=False,
            )
            return not df.empty
        except Exception:
            logger.warning(
                "yfinance trading-day check failed; assuming trading day",
                extra={"market": market.value, "date": check_date.isoformat()},
                exc_info=True,
            )
            return True  # Fail open

    @staticmethod
    def _non_cn_get_holidays(
        market: Market, from_date: date, to_date: date
    ) -> list[dict]:
        """Return holidays by iterating each weekday and checking with yfinance."""
        holidays: list[dict] = []
        cursor = from_date
        while cursor <= to_date:
            if cursor.weekday() < 5:
                if not TradingCalendar._non_cn_is_trading_day(market, cursor):
                    holidays.append({
                        "date": cursor.strftime("%Y-%m-%d"),
                        "name": "休市",
                        "type": "public_holiday",
                    })
            cursor += timedelta(days=1)
        return holidays

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _today(market: Market) -> date:
        """Return today's date in the market's timezone."""
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            return date.today()

        tz_map = {
            Market.CN: "Asia/Shanghai",
            Market.HK: "Asia/Hong_Kong",
            Market.US: "America/New_York",
        }
        tz_name = tz_map.get(market, "UTC")
        return datetime.now(ZoneInfo(tz_name)).date()
