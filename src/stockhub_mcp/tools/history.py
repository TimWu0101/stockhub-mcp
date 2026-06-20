"""get_price_history tool implementation.

Full pipeline:
  symbol resolve → source.fetch_history → adjust tag injection →
  ResponseBuilder.success
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from stockhub_mcp.config import settings
from stockhub_mcp.domain.market.session import MarketSessionResolver
from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.domain.symbol.resolver import SymbolResolver
from stockhub_mcp.enums import Market, QualityFlag
from stockhub_mcp.services.router import SourceRouter
from stockhub_mcp.services.circuit_breaker import CircuitBreaker
from stockhub_mcp.services.yfinance_source import YFinanceSource

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Shared singletons (imported from quote.py scope; re-created for
# independence at module level)
# ------------------------------------------------------------------

_SESSION_RESOLVER = MarketSessionResolver()
_SYMBOL_RESOLVER = SymbolResolver()
_ROUTER = SourceRouter()
_CIRCUIT_BREAKER = CircuitBreaker()

_yfinance_source: Optional[YFinanceSource] = None


def _get_yfinance() -> YFinanceSource:
    global _yfinance_source
    if _yfinance_source is None:
        _yfinance_source = YFinanceSource()
    return _yfinance_source


# ------------------------------------------------------------------
# Tool implementation
# ------------------------------------------------------------------


async def get_price_history_impl(
    symbol: str,
    market: str | None = None,
    period: str = "1mo",
    interval: str = "1d",
    adjust: str | None = None,
) -> dict[str, Any]:
    """Fetch historical K-line data for an instrument.

    Args:
        symbol: User-input symbol – code, name, or pinyin.
        market: Preferred market code.
        period: ``1d`` / ``5d`` / ``1mo`` / ``3mo`` / ``6mo`` /
                ``1y`` / ``2y`` / ``5y`` / ``max``.
        interval: ``1m`` / ``5m`` / ``15m`` / ``30m`` / ``60m`` /
                  ``1d`` / ``1wk`` / ``1mo``.
        adjust: ``none`` / ``qfq`` / ``hfq``. Default: ``qfq`` for CN,
                ``none`` for US/HK.
    """
    builder = ResponseBuilder()

    # --- Step 1: Resolve symbol ---
    preferred_market: Optional[Market] = None
    if market:
        try:
            preferred_market = Market(market.upper())
        except ValueError:
            pass

    resolve_result = _SYMBOL_RESOLVER.resolve(symbol, preferred_market=preferred_market)

    if not resolve_result.resolved:
        return builder.error(
            error={
                "code": "SYMBOL_NOT_RESOLVED",
                "type": "input_error",
                "message": f"Cannot resolve symbol: '{symbol}'.",
                "retryable": False,
                "details": {},
            },
            meta={"market": market or "", "symbol": symbol},
        )

    std_symbol = resolve_result.symbol
    assert std_symbol is not None

    internal = std_symbol.to_internal()
    mkt = std_symbol.market
    mkt_val = mkt.value

    # --- Step 2: Determine adjustment default ---
    if adjust is None:
        adjust = "qfq" if mkt == Market.CN else "none"

    # --- Step 3: Determine session ---
    session = _SESSION_RESOLVER.detect(mkt)

    # --- Step 4: Build base meta ---
    base_meta: dict[str, Any] = {
        "market": mkt_val,
        "symbol": internal,
        "currency": settings.market_currencies.get(mkt_val, ""),
        "timezone": settings.market_timezones.get(mkt_val, ""),
        "market_session": session.value,
        "is_realtime": False,
    }

    # --- Step 5: History sources ---
    history_scope = f"{mkt_val}_history"
    sources = _ROUTER.get_all(mkt, "history")
    if not sources:
        # Fall back to default market sources
        sources = _ROUTER.get_all(mkt)

    last_error: Optional[Exception] = None
    used_source: str = ""
    quality_flag: str = QualityFlag.LIVE.value

    for source_name in sources:
        if not source_name:
            continue
        if not _CIRCUIT_BREAKER.is_available(source_name):
            continue

        try:
            # For now, history only comes from yfinance
            if source_name == "yfinance":
                src = _get_yfinance()
                history = src.fetch_history(
                    std_symbol.code, mkt,
                    period=period, interval=interval, adjust=adjust,
                )
            elif source_name == "tencent":
                # Tencent doesn't support history in V0.1
                continue
            else:
                continue

            _CIRCUIT_BREAKER.record_success(source_name)
            used_source = source_name
            break
        except NotImplementedError:
            continue
        except Exception as exc:
            logger.warning(
                "history source %s failed for %s: %s",
                source_name, internal, exc,
            )
            _CIRCUIT_BREAKER.record_failure(source_name)
            last_error = exc
            continue
    else:
        return builder.error(
            error={
                "code": "HISTORY_SOURCES_FAILED",
                "type": "source_error",
                "message": f"All history sources failed for '{internal}'.",
                "retryable": True,
                "details": {
                    "tried_sources": sources,
                    "last_error": str(last_error) if last_error else "unknown",
                },
            },
            meta=base_meta,
        )

    # --- Step 6: Build success response ---
    history.symbol = internal
    meta = {
        **base_meta,
        "source": used_source,
        "quality_flag": quality_flag,
    }

    return builder.success(data=history.model_dump(), meta=meta)
