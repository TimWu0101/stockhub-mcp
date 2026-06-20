"""V0.2 – ETF tools."""

from __future__ import annotations

from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.domain.symbol.resolver import SymbolResolver
from stockhub_mcp.enums import Market
from stockhub_mcp.models.etf import ETFQuoteData, ETFInfoData

_SYMBOL_RESOLVER = SymbolResolver()


async def get_etf_quote_impl(symbol: str, market: str | None = None) -> dict[str, Any]:
    """Fetch real-time ETF quote (reuses stock quote pipeline)."""
    from stockhub_mcp.tools.quote import get_realtime_quote_impl
    return await get_realtime_quote_impl(symbol=symbol, market=market or "CN")


async def get_etf_history_impl(
    symbol: str, market: str | None = None,
    period: str = "1mo", interval: str = "1d", adjust: str | None = None,
) -> dict[str, Any]:
    """Fetch ETF historical K-line (reuses stock history pipeline)."""
    from stockhub_mcp.tools.history import get_price_history_impl
    return await get_price_history_impl(
        symbol=symbol, market=market or "CN",
        period=period, interval=interval, adjust=adjust,
    )


async def get_etf_info_impl(symbol: str) -> dict[str, Any]:
    """Fetch ETF metadata from eastmoney."""
    builder = ResponseBuilder()
    try:
        import httpx, json

        # Search for the ETF code
        code = symbol
        if ":" in code:
            code = code.split(":")[-1]

        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=1.{code}&fields=f12,f14,f112,f128,f148"
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        obj = resp.json()
        d = obj.get("data", {}) or {}

        # ETF name and tracking index from push2 API
        etf_name = str(d.get("f14", ""))
        track_code = str(d.get("f128", "")) if d.get("f128") else ""
        track_name = str(d.get("f148", "")) if d.get("f148") else ""
        inception = str(d.get("f112", "")) if d.get("f112") else ""

        data = ETFInfoData(
            symbol=f"CN:{code}",
            name=etf_name,
            tracking_index=track_name,
            tracking_index_code=track_code,
            management_fee=0.0,
            inception_date=inception,
            fund_size=0.0,
            industry_tags=[track_name] if track_name else [],
        )
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "source": "eastmoney", "currency": "CNY",
                  "timezone": "Asia/Shanghai", "market_session": "",
                  "is_realtime": False, "data_delay_seconds": 0, "quality_flag": "live"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "ETF_INFO_FAILED",
            "type": "source_error",
            "message": f"ETF info fetch failed: {exc}",
            "retryable": True,
            "details": {},
        })
