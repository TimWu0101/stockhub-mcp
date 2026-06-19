"""TencentSource: A-share real-time quotes via Tencent's qt.gtimg.cn.

Parses the ``v_<code>="..."`` response format.
Uses ``httpx`` for HTTP requests.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from market_data_mcp.config import settings
from market_data_mcp.domain.symbol.normalizer import SymbolNormalizer
from market_data_mcp.domain.symbol.resolver import StandardSymbol
from market_data_mcp.enums import Market, InstrumentType
from market_data_mcp.models.quote import QuoteData
from market_data_mcp.models.history import HistoryData
from market_data_mcp.services.base import BaseDataSource

logger = logging.getLogger(__name__)

# Tencent API endpoint
_TENCENT_URL = "https://qt.gtimg.cn/q={codes}"

# Regex to extract field values from Tencent's response
_RE_TENCENT_LINE = re.compile(r'v_(\w+)="([^"]*)"')


class TencentSource(BaseDataSource):
    """Tencent market data source for A-share (CN) instruments.

    Fetches real-time quotes from the public ``qt.gtimg.cn`` endpoint.

    Supports:
    - CN stocks / indexes / ETFs
    - HK stocks (limited)
    """

    SUPPORTED_MARKETS: frozenset[Market] = frozenset([Market.CN, Market.HK])

    @property
    def name(self) -> str:
        return "tx"

    # ------------------------------------------------------------------
    # BaseDataSource interface
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """Tencent source is always available (no library dependency)."""
        return True

    def fetch_quote(
        self,
        symbol: str,
        market: Market,
        *,
        bypass_cache: bool = False,
    ) -> QuoteData:
        """Fetch real-time quote from Tencent.

        Args:
            symbol: Source-specific symbol (e.g. ``"sh600519"``) or
                    internal standard (e.g. ``"CN:600519"``).
            market: Market code.
        """
        tencent_code = self._to_tencent_code(symbol, market)
        url = _TENCENT_URL.format(codes=tencent_code)

        logger.debug("Tencent fetch_quote: code=%s url=%s", tencent_code, url)

        try:
            resp = self._sync_get(url)
            fields = self._parse_response(resp, tencent_code)

            if not fields:
                raise RuntimeError(f"Tencent returned empty / unparseable data for {tencent_code}")

            return self._build_quote(fields, symbol, market)

        except httpx.HTTPError as exc:
            logger.error("Tencent HTTP error: %s", exc)
            raise RuntimeError(f"Tencent HTTP request failed for {tencent_code}: {exc}") from exc

    def fetch_history(
        self,
        symbol: str,
        market: Market,
        period: str = "1mo",
        interval: str = "1d",
        *,
        adjust: str = "qfq",
    ) -> HistoryData:
        """Tencent does not provide historical K-line data in V0.1."""
        raise NotImplementedError(
            "Tencent source does not support historical K-line data. "
            "Use yfinance for CN history."
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    @staticmethod
    def _sync_get(url: str, timeout: Optional[int] = None) -> str:
        """Perform a synchronous HTTP GET and return the response text."""
        timeout_val = timeout or settings.request_timeout
        with httpx.Client(timeout=timeout_val) as client:
            resp = client.get(url)
            resp.raise_for_status()
            # Tencent returns gbk-encoded content despite Content-Type claims
            resp.encoding = "gbk"
            return resp.text

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(text: str, code: str) -> list[str]:
        """Parse the Tencent ``v_<code>="..."`` response.

        Returns:
            List of field values split by ``~``, or empty list on failure.
        """
        for m in _RE_TENCENT_LINE.finditer(text):
            if m.group(1) == code:
                return m.group(2).split("~")
        return []

    # ------------------------------------------------------------------
    # Quote builder
    # ------------------------------------------------------------------

    @classmethod
    def _build_quote(
        cls,
        fields: list[str],
        symbol: str,
        market: Market,
    ) -> QuoteData:
        """Build a QuoteData from parsed Tencent fields.

        Tencent field layout (common for stocks)::

            [0]  market (1=sh, 51=sz)
            [1]  name
            [2]  code
            [3]  current price
            [4]  prev close
            [5]  open
            [6]  volume (shares)  ← 注意可能为手(100股)单位
            [7]  bid1 buy
            [8]  bid1 price
            [9]  ask1 sell
            [10] ask1 price
            ...
            [31] high
            [32] low
            [33] price / prev_close ...
            [34] amount (turnover 万元)
            [35] turnover rate %
            [36] change %
            [37] ...
        """
        price = cls._safe_float(_get(fields, 3))
        prev_close = cls._safe_float(_get(fields, 4))
        open_price = cls._safe_float(_get(fields, 5))
        high = cls._safe_float(_get(fields, 33))
        low = cls._safe_float(_get(fields, 34))
        volume_raw = cls._safe_float(_get(fields, 6))
        # Tencent sometimes returns volume in "手" (lots of 100)
        volume = int(volume_raw * 100) if volume_raw < 1000000 else int(volume_raw)
        turnover = cls._safe_float(_get(fields, 37)) * 10000  # 万元 → 元

        change = price - prev_close if prev_close else 0.0
        change_pct = cls._safe_float(_get(fields, 32))  # pre-computed by tencent

        if change_pct == 0 and prev_close:
            change_pct = (change / prev_close) * 100

        name = _get(fields, 1)
        if not name:
            name = symbol

        code_str = _get(fields, 2) or symbol.replace("sh", "").replace("sz", "")

        # Resolve internal symbol
        internal = f"CN:{code_str}" if market == Market.CN else f"HK:{code_str}"

        return QuoteData(
            symbol=internal,
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
            instrument_type=InstrumentType.STOCK.value,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_tencent_code(symbol: str, market: Market) -> str:
        """Convert to Tencent symbol format (``sh600519``)."""
        if symbol.startswith("sh") or symbol.startswith("sz") or symbol.startswith("hk"):
            return symbol
        if ":" in symbol:
            try:
                std = StandardSymbol.from_internal(symbol)
                return SymbolNormalizer.to_tencent(std)
            except Exception:
                pass
        std = StandardSymbol(market=market, code=symbol)
        return SymbolNormalizer.to_tencent(std)


def _get(lst: list[str], idx: int, default: str = "") -> str:
    """Safely get list element by index."""
    try:
        return lst[idx]
    except IndexError:
        return default
