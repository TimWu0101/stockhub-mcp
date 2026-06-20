"""V0.2 – Dragon tiger list + sector constituents + symbol status tools."""

from __future__ import annotations

import logging
from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.domain.symbol.resolver import SymbolResolver
from stockhub_mcp.enums import Market
from stockhub_mcp.services.eastmoney_source import EastMoneySource

logger = logging.getLogger(__name__)
_SYMBOL_RESOLVER = SymbolResolver()


def _get_efinance():
    """Lazy-load EfinanceSource if installed."""
    try:
        from stockhub_mcp.services.efinance_source import EfinanceSource
        src = EfinanceSource()
        if src.available():
            return src
    except Exception:
        pass
    return None


def _make_meta(source: str, market: str = "CN") -> dict:
    return {
        "market": market, "source": source, "currency": "CNY",
        "timezone": "Asia/Shanghai", "market_session": "", "is_realtime": False,
        "data_delay_seconds": 0, "quality_flag": "live",
    }


async def get_dragon_tiger_list_impl() -> dict[str, Any]:
    """Fetch today's dragon-tiger board list."""
    builder = ResponseBuilder()

    # Try efinance first (free, SDK-based, more stable)
    efinance = _get_efinance()
    if efinance:
        try:
            data = efinance.fetch_dragon_tiger_list()
            return builder.success(data=data.model_dump(), meta=_make_meta("efinance"))
        except Exception as exc:
            logger.warning("Efinance dragon-tiger failed, falling back: %s", exc)

    # Fallback: eastmoney HTTP
    try:
        src = EastMoneySource()
        data = src.fetch_dragon_tiger_list()
        return builder.success(data=data.model_dump(), meta=_make_meta("eastmoney"))
    except Exception as exc:
        return builder.error(error={
            "code": "DRAGON_TIGER_FAILED",
            "type": "source_error",
            "message": f"Dragon tiger fetch failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_sector_constituents_impl(sector_code: str) -> dict[str, Any]:
    """Fetch constituents of a sector/industry board."""
    builder = ResponseBuilder()

    efinance = _get_efinance()
    if efinance:
        try:
            data = efinance.fetch_sector_constituents(sector_code)
            return builder.success(data=data.model_dump(), meta=_make_meta("efinance"))
        except Exception as exc:
            logger.warning("Efinance sector constituents failed, falling back: %s", exc)

    try:
        src = EastMoneySource()
        data = src.fetch_sector_constituents(sector_code)
        return builder.success(data=data.model_dump(), meta=_make_meta("eastmoney"))
    except Exception as exc:
        return builder.error(error={
            "code": "SECTOR_CONSTITUENTS_FAILED",
            "type": "source_error",
            "message": f"Sector constituents failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_symbol_status_impl(
    symbol: str,
    market: str | None = None,
) -> dict[str, Any]:
    """Query trading status of a symbol (normal/halted/delisted)."""
    builder = ResponseBuilder()

    preferred = Market(market.upper()) if market else None
    result = _SYMBOL_RESOLVER.resolve(symbol, preferred_market=preferred)
    if not result.resolved:
        return builder.error(error={
            "code": "SYMBOL_NOT_RESOLVED",
            "type": "input_error",
            "message": f"Cannot resolve: '{symbol}'",
            "retryable": False,
            "details": {},
        })

    std = result.symbol
    assert std is not None

    # Try getting a quote – if it fails with TRADING_HALTED or is empty, mark accordingly
    from stockhub_mcp.tools.quote import get_realtime_quote_impl
    quote_resp = await get_realtime_quote_impl(
        symbol=symbol, market=std.market.value,
    )

    from stockhub_mcp.models.enhance import SymbolStatusData

    if quote_resp.get("success"):
        data = SymbolStatusData(
            symbol=std.to_internal(),
            name=quote_resp.get("data", {}).get("name", ""),
            status="normal",
            reason="",
            since="",
        )
        return builder.success(
            data=data.model_dump(),
            meta={"market": std.market.value, "symbol": std.to_internal(),
                  "source": "tx", "is_realtime": False, "data_delay_seconds": 0,
                  "quality_flag": "live"},
        )

    error_code = quote_resp.get("error", {}).get("code", "")
    if error_code == "TRADING_HALTED":
        data = SymbolStatusData(symbol=std.to_internal(), name="", status="halted")
    elif error_code == "DELISTED_SYMBOL":
        data = SymbolStatusData(symbol=std.to_internal(), name="", status="delisted")
    elif error_code == "MARKET_NOT_SUPPORTED":
        data = SymbolStatusData(symbol=std.to_internal(), name="", status="unknown")
    else:
        # Quote failed for another reason – treat as unavailable
        data = SymbolStatusData(symbol=std.to_internal(), name="", status="unavailable")

    return builder.success(
        data=data.model_dump(),
        meta={"market": std.market.value, "symbol": std.to_internal(),
              "source": "tx", "is_realtime": False, "data_delay_seconds": 0,
              "quality_flag": "computed"},
    )
