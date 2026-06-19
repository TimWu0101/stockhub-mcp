"""SinaSource: A-share real-time quotes via Sina's hq.sinajs.cn.

Parses the ``var hq_str_<code>="..."`` response format.
Used as a fallback for Tencent when the primary A-share source is
unavailable.
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

# Sina API endpoint
_SINA_URL = "https://hq.sinajs.cn/list={codes}"

# Regex to extract the value from Sina's JS-var response
_RE_SINA_VALUE = re.compile(r'var hq_str_\w+="([^"]*)"')


class SinaSource(BaseDataSource):
    """Sina market data source for A-share (CN) instruments.

    Used as a fallback when Tencent is unavailable or degraded.
    """

    SUPPORTED_MARKETS: frozenset[Market] = frozenset([Market.CN])

    @property
    def name(self) -> str:
        return "sina"

    # ------------------------------------------------------------------
    # BaseDataSource interface
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """Sina source is always available (no library dependency)."""
        return True

    def fetch_quote(
        self,
        symbol: str,
        market: Market,
        *,
        bypass_cache: bool = False,
    ) -> QuoteData:
        """Fetch real-time quote from Sina.

        Args:
            symbol: Source-specific symbol (e.g. ``"sh600519"``) or
                    internal standard.
            market: Market code (must be CN).
        """
        if market != Market.CN:
            raise ValueError(f"Sina source only supports CN market, got {market.value}")

        sina_code = self._to_sina_code(symbol)
        url = _SINA_URL.format(codes=sina_code)

        logger.debug("Sina fetch_quote: code=%s url=%s", sina_code, url)

        try:
            resp = self._sync_get(url)
            fields = self._parse_response(resp)

            if not fields:
                raise RuntimeError(f"Sina returned empty / unparseable data for {sina_code}")

            return self._build_quote(fields, symbol, market)

        except httpx.HTTPError as exc:
            logger.error("Sina HTTP error: %s", exc)
            raise RuntimeError(f"Sina HTTP request failed for {sina_code}: {exc}") from exc

    def fetch_history(
        self,
        symbol: str,
        market: Market,
        period: str = "1mo",
        interval: str = "1d",
        *,
        adjust: str = "qfq",
    ) -> HistoryData:
        """Sina does not provide historical K-line data in V0.1."""
        raise NotImplementedError(
            "Sina source does not support historical K-line data."
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    @staticmethod
    def _sync_get(url: str, timeout: Optional[int] = None) -> str:
        """Perform a synchronous HTTP GET."""
        timeout_val = timeout or settings.request_timeout
        headers = {
            "Referer": "https://finance.sina.com.cn",
        }
        with httpx.Client(timeout=timeout_val, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            resp.encoding = "gb2312"
            return resp.text

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(text: str) -> list[str]:
        """Parse the Sina ``var hq_str_<code>="..."`` response.

        Returns:
            List of comma-separated field values, or empty list.
        """
        m = _RE_SINA_VALUE.search(text)
        if m:
            return m.group(1).split(",")
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
        """Build a QuoteData from parsed Sina fields.

        Sina field layout (A-share stock)::

            [0]  name
            [1]  open
            [2]  prev close
            [3]  current price
            [4]  high
            [5]  low
            [6]  bid/竞买价
            [7]  ask/竞卖价
            [8]  volume (股)
            [9]  turnover (元)
            ...
            [32] change_pct (涨跌幅 %)
        """
        name = _safe_get(fields, 0, symbol)
        open_price = cls._safe_float(_safe_get(fields, 1))
        prev_close = cls._safe_float(_safe_get(fields, 2))
        price = cls._safe_float(_safe_get(fields, 3))
        high = cls._safe_float(_safe_get(fields, 4))
        low = cls._safe_float(_safe_get(fields, 5))
        volume = int(cls._safe_float(_safe_get(fields, 8)))
        turnover = cls._safe_float(_safe_get(fields, 9))
        change_pct = cls._safe_float(_safe_get(fields, 32))

        change = price - prev_close if prev_close else 0.0
        if change_pct == 0 and prev_close:
            change_pct = (change / prev_close) * 100

        # Resolve internal symbol
        code_str = symbol
        if code_str.startswith("sh") or code_str.startswith("sz"):
            code_str = code_str[2:]
        internal = f"CN:{code_str}"

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
    def _to_sina_code(symbol: str) -> str:
        """Convert to Sina symbol format (``sh600519``)."""
        if symbol.startswith("sh") or symbol.startswith("sz"):
            return symbol
        if ":" in symbol:
            try:
                std = StandardSymbol.from_internal(symbol)
                return SymbolNormalizer.to_sina(std)
            except Exception:
                pass
        # Assume CN
        std = StandardSymbol(market=Market.CN, code=symbol)
        return SymbolNormalizer.to_sina(std)


def _safe_get(lst: list[str], idx: int, default: str = "") -> str:
    """Safely get list element."""
    try:
        return lst[idx]
    except IndexError:
        return default
