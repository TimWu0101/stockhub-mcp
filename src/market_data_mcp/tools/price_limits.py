"""V0.2 – get_price_limits tool (A股涨跌停价格)."""

from __future__ import annotations

from typing import Any

from market_data_mcp.domain.response_builder import ResponseBuilder
from market_data_mcp.domain.symbol.resolver import SymbolResolver
from market_data_mcp.enums import Market

_SYMBOL_RESOLVER = SymbolResolver()


async def get_price_limits_impl(
    symbol: str,
    market: str | None = None,
) -> dict[str, Any]:
    """Compute A-share price limits based on previous close.

    Args:
        symbol: User input.
        market: Preferred market.
    """
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

    if std.market != Market.CN:
        return builder.error(error={
            "code": "MARKET_NOT_SUPPORTED",
            "type": "business_error",
            "message": "Price limits only available for A-shares.",
            "retryable": False,
            "details": {},
        })

    # Fetch quote to get prev_close
    from market_data_mcp.tools.quote import get_realtime_quote_impl
    quote_resp = await get_realtime_quote_impl(symbol=symbol, market="CN")
    if not quote_resp.get("success"):
        return quote_resp

    prev_close = float(quote_resp.get("data", {}).get("prev_close", 0))
    if prev_close <= 0:
        return builder.error(error={
            "code": "NO_DATA_AVAILABLE",
            "type": "business_error",
            "message": "Cannot determine previous close.",
            "retryable": False,
            "details": {},
        })

    # Detect board: 300xxx/301xxx/68xxxx → gem/star (20%), others → main (10%)
    code = std.code
    is_gem_star = code.startswith(("300", "301", "688"))
    rate = 0.20 if is_gem_star else 0.10

    limit_up = round(prev_close * (1 + rate), 2)
    limit_down = round(prev_close * (1 - rate), 2)
    board_type = "gem_star" if is_gem_star else "main"

    from market_data_mcp.models.enhance import PriceLimitsData
    data = PriceLimitsData(
        symbol=std.to_internal(),
        prev_close=prev_close,
        limit_up=limit_up,
        limit_down=limit_down,
        board_type=board_type,
    )

    meta = {
        "market": "CN",
        "symbol": std.to_internal(),
        "source": "computed",
        "currency": "CNY",
        "timezone": "Asia/Shanghai",
        "market_session": "",
        "is_realtime": False,
        "data_delay_seconds": 0,
        "quality_flag": "computed",
    }
    return builder.success(data=data.model_dump(), meta=meta)
