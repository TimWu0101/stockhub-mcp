"""SymbolNormalizer: internal standard → per-source symbol format.

Converts ``StandardSymbol`` instances to the format expected by each
data source (Tencent, Sina, EastMoney, Yahoo Finance, etc.).
"""

from __future__ import annotations

from stockhub_mcp.domain.symbol.resolver import StandardSymbol
from stockhub_mcp.enums import Market


class SymbolNormalizer:
    """Convert internal standard symbols to data-source-specific formats.

    Usage::

        n = SymbolNormalizer()
        n.to_tencent(StandardSymbol(Market.CN, "600519"))   # → "sh600519"
        n.to_yfinance(StandardSymbol(Market.US, "AAPL"))     # → "AAPL"
    """

    # ------------------------------------------------------------------
    # Public per-source converters
    # ------------------------------------------------------------------

    @staticmethod
    def to_tencent(symbol: StandardSymbol) -> str:
        """Convert to Tencent qt.gtimg.cn format.

        CN: ``600519`` → ``sh600519`` (SSE) / ``sz000001`` (SZSE)
        HK: ``00700`` → ``hk00700``
        US: Not supported by Tencent source.
        """
        market = symbol.market
        code = symbol.code

        if market == Market.CN:
            prefix = _cn_exchange_prefix(code)
            return f"{prefix}{code}"
        elif market == Market.HK:
            return f"hk{code}"
        else:
            raise ValueError(f"Tencent source does not support market {market.value}")

    @staticmethod
    def to_sina(symbol: StandardSymbol) -> str:
        """Convert to Sina hq.sinajs.cn format.

        CN: ``600519`` → ``sh600519``
        HK: ``00700`` → ``hk00700``
        US: Not supported by Sina source.
        """
        market = symbol.market
        code = symbol.code

        if market == Market.CN:
            prefix = _cn_exchange_prefix(code)
            return f"{prefix}{code}"
        elif market == Market.HK:
            return f"hk{code}"
        else:
            raise ValueError(f"Sina source does not support market {market.value}")

    @staticmethod
    def to_eastmoney(symbol: StandardSymbol) -> str:
        """Convert to EastMoney format.

        CN: ``600519`` → ``1.600519`` (SSE) / ``0.000858`` (SZSE)
        HK: Not supported.
        US: Not supported.
        """
        market = symbol.market
        code = symbol.code

        if market == Market.CN:
            secid = _cn_eastmoney_secid(code)
            return secid
        else:
            raise ValueError(f"EastMoney source does not support market {market.value}")

    @staticmethod
    def to_yfinance(symbol: StandardSymbol) -> str:
        """Convert to Yahoo Finance ticker format.

        CN: ``600519`` → ``600519.SS`` (SSE) / ``000858.SZ`` (SZSE)
        HK: ``00700`` → ``0700.HK``
        US: ``AAPL`` → ``AAPL``
        """
        market = symbol.market
        code = symbol.code

        if market == Market.CN:
            suffix = "SS" if _is_shanghai(code) else "SZ"
            return f"{code}.{suffix}"
        elif market == Market.HK:
            # Strip leading zeros and add .HK suffix
            stripped = code.lstrip("0") or "0"
            return f"{stripped}.HK"
        elif market == Market.US:
            return code
        else:
            raise ValueError(f"Unknown market: {market.value}")

    @staticmethod
    def to_akshare(symbol: StandardSymbol) -> str:
        """Convert to akshare-compatible symbol format.

        CN: ``600519`` → ``sh600519``
        HK: ``00700`` → ``00700``
        US: Not supported.
        """
        market = symbol.market
        code = symbol.code

        if market == Market.CN:
            prefix = _cn_exchange_prefix(code)
            return f"{prefix}{code}"
        elif market == Market.HK:
            return code
        else:
            raise ValueError(f"akshare does not support market {market.value}")

    @staticmethod
    def normalize(symbol: StandardSymbol, source: str) -> str:
        """Dispatch to the correct converter by source name.

        Args:
            symbol: Internal standard symbol.
            source: One of ``"tx"``, ``"sina"``, ``"eastmoney"``, ``"yfinance"``, ``"akshare"``.

        Returns:
            Source-specific symbol string.

        Raises:
            ValueError: If *source* is unknown or unsupported for this market.
        """
        converters = {
            "tx": SymbolNormalizer.to_tencent,
            "sina": SymbolNormalizer.to_sina,
            "eastmoney": SymbolNormalizer.to_eastmoney,
            "yfinance": SymbolNormalizer.to_yfinance,
            "akshare": SymbolNormalizer.to_akshare,
        }

        converter = converters.get(source)
        if converter is None:
            raise ValueError(f"Unknown source: {source}")

        return converter(symbol)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# SSE codes start with 5, 6, or 9 (Shanghai Stock Exchange).
# SZSE codes start with 0, 2, 3 (Shenzhen Stock Exchange).
# This is a heuristic; 000xxx and 002xxx are SZSE, 600/601/603/605/688 are SSE.


def _is_shanghai(code: str) -> bool:
    """Return True if the 6-digit CN code belongs to Shanghai Stock Exchange."""
    if len(code) != 6:
        return False
    first = code[0]
    return first in ("5", "6", "9")


def _cn_exchange_prefix(code: str) -> str:
    """Return ``"sh"`` for SSE codes, ``"sz"`` for SZSE codes."""
    return "sh" if _is_shanghai(code) else "sz"


def _cn_eastmoney_secid(code: str) -> str:
    """Return EastMoney secid: ``1.600519`` (SSE) or ``0.000858`` (SZSE)."""
    market_code = "1" if _is_shanghai(code) else "0"
    return f"{market_code}.{code}"
