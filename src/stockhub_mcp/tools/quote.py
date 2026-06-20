"""get_realtime_quote tool implementation.

Full pipeline:
  symbol resolve → session detect → SourceRouter → CircuitBreaker →
  source.fetch_quote → ResponseBuilder.success
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from stockhub_mcp.config import settings
from stockhub_mcp.domain.market.session import MarketSessionResolver
from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.domain.symbol.resolver import SymbolResolver
from stockhub_mcp.enums import Market, QualityFlag
from stockhub_mcp.services.router import SourceRouter
from stockhub_mcp.services.circuit_breaker import CircuitBreaker
from stockhub_mcp.services.yfinance_source import YFinanceSource
from stockhub_mcp.services.tencent_source import TencentSource
from stockhub_mcp.services.sina_source import SinaSource
from stockhub_mcp.services.eastmoney_source import EastMoneySource

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Source registry (singletons created once at import time)
# ------------------------------------------------------------------

_SOURCES: dict[str, Any] = {}
_SESSION_RESOLVER = MarketSessionResolver()
_SYMBOL_RESOLVER = SymbolResolver()
_ROUTER = SourceRouter()
_CIRCUIT_BREAKER = CircuitBreaker()

# Eagerly populate sources that don't require external libraries
_TENCENT = TencentSource()
_SINA = SinaSource()
_EASTMONEY = EastMoneySource()
_SOURCES["tx"] = _TENCENT
_SOURCES["sina"] = _SINA
_SOURCES["eastmoney"] = _EASTMONEY

# yfinance is optional – create on demand
_yfinance_source: Optional[YFinanceSource] = None


def _get_source(name: str) -> Any:
    """Return a source instance by name, creating it if necessary."""
    if name in _SOURCES:
        return _SOURCES[name]

    if name == "yfinance":
        global _yfinance_source
        if _yfinance_source is None:
            _yfinance_source = YFinanceSource()
        return _yfinance_source

    raise ValueError(f"Unknown source: {name}")


# ------------------------------------------------------------------
# Tool implementation
# ------------------------------------------------------------------


async def get_realtime_quote_impl(
    symbol: str,
    market: str | None = None,
    bypass_cache: bool = False,
) -> dict[str, Any]:
    """Fetch a real-time quote for a single instrument.

    Args:
        symbol: User-input symbol – code, name, or pinyin.
        market: Preferred market code (CN/HK/US).
        bypass_cache: If True, skip cache read + write.
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
                "message": f"Cannot resolve symbol: '{symbol}'. Provide a valid code or unambiguous name.",
                "retryable": False,
                "details": {
                    "candidates": [
                        {"symbol": c.symbol.to_internal(), "name": c.name}
                        for c in resolve_result.candidates
                    ],
                },
            },
            meta={"market": market or "", "symbol": symbol},
        )

    std_symbol = resolve_result.symbol
    assert std_symbol is not None

    internal = std_symbol.to_internal()
    mkt = std_symbol.market
    mkt_val = mkt.value

    # --- Step 2: Determine market session ---
    session = _SESSION_RESOLVER.detect(mkt)

    # --- Step 3: Build base meta ---
    base_meta: dict[str, Any] = {
        "market": mkt_val,
        "symbol": internal,
        "currency": settings.market_currencies.get(mkt_val, ""),
        "timezone": settings.market_timezones.get(mkt_val, ""),
        "market_session": session.value,
        "is_realtime": session.value in ("continuous", "pre_opening", "auction"),
    }

    # --- Step 4: Try primary source, then fallbacks ---
    primary = _ROUTER.get_primary(mkt)
    fallback_list = _ROUTER.get_fallback(mkt)

    sources_to_try = [primary] + fallback_list
    last_error: Optional[Exception] = None
    used_source: str = ""
    fallback_used: bool = False
    quality_flag: str = QualityFlag.LIVE.value

    for idx, source_name in enumerate(sources_to_try):
        if not source_name:
            continue
        if not _CIRCUIT_BREAKER.is_available(source_name):
            logger.debug("source %s is degraded, skipping", source_name)
            continue

        if idx > 0:
            fallback_used = True
            quality_flag = QualityFlag.FALLBACK.value if idx == 1 else QualityFlag.FALLBACK_LOW_CONFIDENCE.value

        try:
            src = _get_source(source_name)
            quote = src.fetch_quote(std_symbol.code, mkt, bypass_cache=bypass_cache)
            _CIRCUIT_BREAKER.record_success(source_name)
            used_source = source_name
            break
        except NotImplementedError:
            continue  # Source doesn't support this market
        except Exception as exc:
            logger.warning(
                "source %s failed for %s: %s", source_name, internal, exc,
            )
            _CIRCUIT_BREAKER.record_failure(source_name)
            last_error = exc
            continue
    else:
        # All sources exhausted
        return builder.error(
            error={
                "code": "ALL_SOURCES_FAILED",
                "type": "source_error",
                "message": f"All data sources failed for '{internal}'.",
                "retryable": True,
                "details": {
                    "tried_sources": sources_to_try,
                    "last_error": str(last_error) if last_error else "unknown",
                },
            },
            meta=base_meta,
        )

    # --- Step 5: Build success response ---
    meta = {
        **base_meta,
        "source": used_source,
        "quality_flag": quality_flag,
        "fallback_used": fallback_used,
        "data_delay_seconds": _estimate_delay(session, quality_flag),
        "data_timestamp": quote.timestamp,
    }

    return builder.success(data=quote.model_dump(), meta=meta)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _estimate_delay(session, quality_flag: str) -> int:
    """Estimate data delay in seconds based on session and quality."""
    from stockhub_mcp.enums import MarketSession

    if quality_flag == QualityFlag.LIVE.value:
        if session in (MarketSession.CONTINUOUS, MarketSession.PRE_OPENING):
            return 3  # ~3 seconds for public APIs during trading
        return 0

    if quality_flag == QualityFlag.DELAYED.value:
        return 900  # 15-minute delay

    if quality_flag == QualityFlag.FALLBACK.value:
        return 5

    if quality_flag == QualityFlag.FALLBACK_LOW_CONFIDENCE.value:
        return 30

    if quality_flag == QualityFlag.STALE.value:
        return 3600

    return 0
