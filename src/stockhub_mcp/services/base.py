"""BaseDataSource: abstract base class for all market-data sources.

Every data source (Tencent, Sina, Yahoo Finance, EastMoney, AkShare)
must implement this interface.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from stockhub_mcp.enums import Market
from stockhub_mcp.models.quote import QuoteData
from stockhub_mcp.models.history import HistoryData

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# V0.3 Standard column names (adopted from daily_stock_analysis)
# ------------------------------------------------------------------

STANDARD_COLUMNS = [
    "date", "open", "high", "low", "close", "volume", "amount", "pct_chg",
]


class BaseDataSource(ABC):
    """Abstract data source with unified fetch contract.

    Subclasses implement ``fetch_quote`` and ``fetch_history`` for
    the markets they support, and report availability via ``available()``.
    """

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique source name matching ``enums.DataSource`` values.

        E.g. ``"tx"``, ``"yfinance"``, ``"sina"``, ``"eastmoney"``.
        """
        ...

    @abstractmethod
    def available(self) -> bool:
        """Return True if the source is currently usable.

        Base implementation only checks that the required library is
        importable.  Subclasses may add their own health checks.
        """
        ...

    @abstractmethod
    def fetch_quote(
        self,
        symbol: str,
        market: Market,
        *,
        bypass_cache: bool = False,
    ) -> QuoteData:
        """Fetch real-time quote for a single instrument.

        Args:
            symbol: Source-specific symbol string (already normalised).
            market: Market code.
            bypass_cache: If True the caller wants a fresh fetch.

        Returns:
            Populated ``QuoteData`` instance.

        Raises:
            ValueError: The symbol or market is unsupported by this source.
            RuntimeError: The underlying HTTP / library call failed.
        """
        ...

    @abstractmethod
    def fetch_history(
        self,
        symbol: str,
        market: Market,
        period: str = "1mo",
        interval: str = "1d",
        *,
        adjust: str = "qfq",
    ) -> HistoryData:
        """Fetch historical K-line data.

        Args:
            symbol: Source-specific symbol string.
            market: Market code.
            period: Data period (``1d``, ``5d``, ``1mo``, ``3mo``, ``6mo``,
                    ``1y``, ``2y``, ``5y``, ``max``).
            interval: Bar interval (``1m``, ``5m``, ``15m``, ``30m``,
                      ``60m``, ``1d``, ``1wk``, ``1mo``).
            adjust: Adjustment method (``none`` / ``qfq`` / ``hfq``).

        Returns:
            Populated ``HistoryData`` instance.

        Raises:
            ValueError / RuntimeError: See ``fetch_quote``.
        """
        ...

    # ------------------------------------------------------------------
    # Helpers for subclasses
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        """Convert *value* to float, returning *default* on failure."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(value, default: int = 0) -> int:
        """Convert *value* to int, returning *default* on failure."""
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _check_import(package: str) -> bool:
        """Return True if *package* can be imported."""
        try:
            __import__(package)
            return True
        except ImportError:
            return False
