"""YFinanceSource: US & HK market data via Yahoo Finance.

Wraps the synchronous ``yfinance`` library.  Provides real-time
quotes and historical K-line data for US and HK instruments.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from market_data_mcp.config import settings
from market_data_mcp.domain.symbol.normalizer import SymbolNormalizer
from market_data_mcp.domain.symbol.resolver import StandardSymbol
from market_data_mcp.enums import Market, InstrumentType
from market_data_mcp.models.quote import QuoteData
from market_data_mcp.models.history import HistoryData, KLineItem
from market_data_mcp.services.base import BaseDataSource

logger = logging.getLogger(__name__)

# yfinance period mapping
_YF_PERIOD_MAP: dict[str, str] = {
    "1d": "1d",
    "5d": "5d",
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    "max": "max",
}

# yfinance interval mapping
_YF_INTERVAL_MAP: dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "1h": "1h",
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo",
}

# Benchmark tickers for each market (used to detect market health)
_BENCHMARK_TICKER: dict[Market, str] = {
    Market.HK: "0700.HK",
    Market.US: "AAPL",
}


class YFinanceSource(BaseDataSource):
    """Yahoo Finance data source for US and HK markets.

    Uses the synchronous ``yfinance`` library.  CN stocks are supported
    via the yfinance ticker format (e.g. ``600519.SS``) but are not the
    primary path for A-share data.
    """

    SUPPORTED_MARKETS: frozenset[Market] = frozenset([Market.HK, Market.US])

    @property
    def name(self) -> str:
        return "yfinance"

    # ------------------------------------------------------------------
    # BaseDataSource interface
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """Check that yfinance is importable."""
        return self._check_import("yfinance")

    def fetch_quote(
        self,
        symbol: str,
        market: Market,
        *,
        bypass_cache: bool = False,
    ) -> QuoteData:
        """Fetch real-time / latest quote via yfinance.

        Uses ``Ticker.fast_info`` for speed; falls back to
        ``Ticker.history(period="1d")``.
        """
        import yfinance as yf

        ticker_str = self._to_yfinance_symbol(symbol, market)
        logger.debug("yfinance fetch_quote: ticker=%s", ticker_str)

        try:
            tk = yf.Ticker(ticker_str)

            # Try fast_info first (most performant)
            fast = tk.fast_info
            price = self._safe_float(getattr(fast, "last_price", None) or getattr(fast, "regular_market_previous_close", 0))
            prev_close = self._safe_float(getattr(fast, "previous_close", None) or getattr(fast, "regular_market_previous_close", 0))
            open_price = self._safe_float(getattr(fast, "open", None) or getattr(fast, "regular_market_open", 0))
            high = self._safe_float(getattr(fast, "day_high", None) or getattr(fast, "regular_market_day_high", 0))
            low = self._safe_float(getattr(fast, "day_low", None) or getattr(fast, "regular_market_day_low", 0))

            # If fast_info didn't give us a usable price, fall back to history
            if price == 0:
                hist = tk.history(period="1d")
                if not hist.empty:
                    row = hist.iloc[-1]
                    price = self._safe_float(row.get("Close", 0))
                    prev_close = self._safe_float(row.get("Close", price))  # best effort
                    open_price = self._safe_float(row.get("Open", 0))
                    high = self._safe_float(row.get("High", 0))
                    low = self._safe_float(row.get("Low", 0))

            # Volume & turnover
            volume = 0
            turnover = 0.0
            try:
                # fast_info day_volume may be available
                volume = int(getattr(fast, "last_volume", 0) or 0)
            except Exception:
                pass

            name = self._get_instrument_name(tk, symbol)
            inst_type = self._infer_instrument_type(ticker_str, market)

            change = price - prev_close if prev_close else 0.0
            change_pct = (change / prev_close * 100) if prev_close else 0.0

            return QuoteData(
                symbol=f"{market.value}:{symbol}",
                name=name,
                market=market.value,
                price=round(price, 4),
                change=round(change, 4),
                change_pct=round(change_pct, 4),
                open=round(open_price, 4),
                high=round(high, 4),
                low=round(low, 4),
                prev_close=round(prev_close, 4),
                volume=volume,
                turnover=turnover,
                timestamp=datetime.now(timezone.utc).isoformat(),
                instrument_type=inst_type,
            )
        except Exception as exc:
            logger.error("yfinance fetch_quote failed: ticker=%s error=%s", ticker_str, exc)
            raise RuntimeError(f"yfinance quote fetch failed for {ticker_str}: {exc}") from exc

    def fetch_history(
        self,
        symbol: str,
        market: Market,
        period: str = "1mo",
        interval: str = "1d",
        *,
        adjust: str = "qfq",
    ) -> HistoryData:
        """Fetch historical K-line data via yfinance.

        Note: yfinance does not support ``qfq``/``hfq`` adjustment;
        the *adjust* parameter is accepted but only ``none`` (raw) is
        truly effective.  Adjusted close is always included.
        """
        import yfinance as yf

        ticker_str = self._to_yfinance_symbol(symbol, market)
        yf_period = _YF_PERIOD_MAP.get(period, "1mo")
        yf_interval = _YF_INTERVAL_MAP.get(interval, "1d")

        # yfinance auto_adjust=False returns the raw OHLC + Adj Close column
        auto_adjust = False

        logger.debug(
            "yfinance fetch_history: ticker=%s period=%s interval=%s",
            ticker_str, yf_period, yf_interval,
        )

        try:
            df = yf.download(
                ticker_str,
                period=yf_period,
                interval=yf_interval,
                progress=False,
                auto_adjust=auto_adjust,
            )

            # Flatten MultiIndex columns from yfinance download
            # e.g. ('Open', 'AAPL') → 'Open'
            if hasattr(df, 'columns') and hasattr(df.columns, 'levels') and len(df.columns.levels) > 1:
                df.columns = df.columns.get_level_values(0)

            if df is None or df.empty:
                logger.warning("yfinance returned empty history for %s", ticker_str)
                return HistoryData(
                    symbol=f"{market.value}:{symbol}",
                    market=market.value,
                    period=period,
                    interval=interval,
                    adjust=adjust,
                    count=0,
                    history=[],
                )

            bars: list[KLineItem] = []
            for idx, row in df.iterrows():
                date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)[:10]
                close_val = self._safe_float(row.get("Close", 0))
                prev_close = bars[-1].close if bars else close_val
                chg_pct = ((close_val - prev_close) / prev_close * 100) if prev_close else 0.0

                bars.append(KLineItem(
                    date=date_str,
                    open=self._safe_float(row.get("Open", 0)),
                    high=self._safe_float(row.get("High", 0)),
                    low=self._safe_float(row.get("Low", 0)),
                    close=close_val,
                    volume=self._safe_int(row.get("Volume", 0)),
                    turnover=0.0,  # yfinance doesn't provide turnover
                    change_pct=round(chg_pct, 4),
                ))

            return HistoryData(
                symbol=f"{market.value}:{symbol}",
                market=market.value,
                period=period,
                interval=interval,
                adjust=adjust,
                count=len(bars),
                history=bars,
            )

        except Exception as exc:
            logger.error(
                "yfinance fetch_history failed: ticker=%s error=%s",
                ticker_str, exc,
            )
            raise RuntimeError(
                f"yfinance history fetch failed for {ticker_str}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_yfinance_symbol(symbol: str, market: Market) -> str:
        """Convert a raw code or internal symbol to a yfinance ticker.

        If *symbol* already looks like a yfinance ticker (contains a dot),
        use it directly.  Otherwise normalise via SymbolNormalizer.
        """
        if "." in symbol:
            return symbol

        # Try to parse as internal standard
        from market_data_mcp.domain.symbol.resolver import StandardSymbol
        try:
            if ":" in symbol:
                std = StandardSymbol.from_internal(symbol)
            else:
                std = StandardSymbol(market=market, code=symbol)
        except Exception:
            std = StandardSymbol(market=market, code=symbol)

        return SymbolNormalizer.to_yfinance(std)

    @staticmethod
    def _get_instrument_name(tk, fallback: str) -> str:
        """Extract the instrument name from a yfinance Ticker object."""
        try:
            info = tk.info
            if info:
                return info.get("longName") or info.get("shortName") or info.get("symbol", fallback)
        except Exception:
            pass
        return fallback

    @staticmethod
    def _infer_instrument_type(ticker: str, market: Market) -> str:
        """Heuristic to classify a ticker as stock / etf / index."""
        ticker_upper = ticker.upper()
        # Indices
        if ticker.startswith("^"):
            return InstrumentType.INDEX.value
        # Common ETF tickers
        if ticker_upper in ("SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "GLD", "SLV",
                            "2800.HK", "2828.HK", "2822.HK", "2823.HK",
                            "510050.SS", "510300.SS", "159915.SZ"):
            return InstrumentType.ETF.value
        return InstrumentType.STOCK.value
