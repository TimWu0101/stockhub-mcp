"""V0.4 – Composite analysis tool: chains quote + indicators via Pipeline."""

from __future__ import annotations

from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.core.pipeline import Pipeline


async def get_quick_analysis_impl(
    symbol: str,
    market: str | None = None,
) -> dict[str, Any]:
    """One-shot: quote + indicators + analysis in a single call.

    Uses the V0.4 Pipeline to chain stages.
    """
    builder = ResponseBuilder()

    async def stage_fetch_quote(ctx: dict | None) -> dict:
        from stockhub_mcp.tools.quote import get_realtime_quote_impl
        result = await get_realtime_quote_impl(symbol=symbol, market=market)
        if not result.get("success"):
            raise RuntimeError(f"Quote failed: {result.get('error', {}).get('message', '')}")
        return {"quote": result}

    async def stage_fetch_indicators(ctx: dict | None) -> dict:
        from stockhub_mcp.tools.indicators import get_technical_indicators_impl
        result = await get_technical_indicators_impl(
            symbol=symbol, indicators=["MA", "MACD", "RSI"],
            market=market, period="3mo",
        )
        if result.get("success"):
            ctx["indicators"] = result
        else:
            ctx["indicators"] = {"error": result.get("error", {}).get("message")}
        return ctx

    pipeline = Pipeline() \
        .stage(stage_fetch_quote) \
        .stage(stage_fetch_indicators)

    try:
        result = await pipeline.run({})
        final = result.get("final", {})

        # Check for stage failures
        if "quote" not in final or not final["quote"].get("success"):
            return builder.error(error={
                "code": "QUOTE_FAILED",
                "type": "source_error",
                "message": final.get("quote", {}).get("error", {}).get("message", "Quote stage failed"),
                "retryable": True,
                "details": {},
            })

        quote = final.get("quote", {}).get("data", {})
        ind = final.get("indicators", {}).get("data", {})

        data = {
            "symbol": quote.get("symbol", ""),
            "name": quote.get("name", ""),
            "price": quote.get("price", 0),
            "change_pct": quote.get("change_pct", 0),
            "trend": ind.get("analysis", {}).get("trend", {}),
            "signal": ind.get("analysis", {}).get("signal", {}),
            "indicators": ind.get("indicators", {}),
            "data_timestamp": quote.get("timestamp", ""),
        }

        return builder.success(data=data, meta={
            "market": quote.get("market", ""),
            "symbol": quote.get("symbol", ""),
            "source": "composite",
            "currency": "CNY",
            "timezone": "Asia/Shanghai",
            "market_session": "",
            "is_realtime": False,
            "data_delay_seconds": 0,
            "quality_flag": "live",
        })
    except Exception as exc:
        return builder.error(error={
            "code": "QUICK_ANALYSIS_FAILED",
            "type": "source_error",
            "message": f"Quick analysis failed: {exc}",
            "retryable": True,
            "details": {},
        })
