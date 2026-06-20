"""FastMCP application entry-point for market-data-mcp.

Start with:  fastmcp dev src/stockhub_mcp/server.py
"""

from __future__ import annotations

from fastmcp import FastMCP

from stockhub_mcp.utils.logging import configure_logging

# ---------------------------------------------------------------------------
# One-time setup
# ---------------------------------------------------------------------------
configure_logging()

mcp = FastMCP("market-data-mcp")

# ---------------------------------------------------------------------------
# Lazy-init singletons (created on first use to avoid import-time errors)
# ---------------------------------------------------------------------------
_cache_middleware = None
_cache_store = None


def _get_cache_middleware():
    """Lazily create the CacheMiddleware singleton."""
    global _cache_middleware
    if _cache_middleware is None:
        from stockhub_mcp.tools.cache_middleware import CacheMiddleware
        _cache_middleware = CacheMiddleware()
    return _cache_middleware


def _setup_cache_control():
    """Inject the cache store into cache_control so it shares state."""
    global _cache_store
    if _cache_store is None:
        from stockhub_mcp.services.cache.store import FIFOCacheStore
        from stockhub_mcp.tools import cache_control
        middleware = _get_cache_middleware()
        _cache_store = middleware._store
        cache_control.set_cache_store(_cache_store)


# ---------------------------------------------------------------------------
# 4.1  get_realtime_quote
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_realtime_quote(
    symbol: str,
    market: str | None = None,
    bypass_cache: bool = False,
) -> dict:
    """Query real-time quote for a single instrument.

    Args:
        symbol: User input – code, Chinese name, or English name.
        market: Preferred market (CN/HK/US). Recommended when ambiguous.
        bypass_cache: If True, skip the local cache.
    """
    from stockhub_mcp.tools.quote import get_realtime_quote_impl

    middleware = _get_cache_middleware()
    wrapped = middleware.wrap(get_realtime_quote_impl, "get_realtime_quote")
    result = await wrapped(
        symbol=symbol, market=market, bypass_cache=bypass_cache,
    )
    # Ensure data timestamp is always visible in meta
    if result.get("success") and result.get("data", {}).get("timestamp"):
        result.setdefault("meta", {})["data_timestamp"] = result["data"]["timestamp"]
    return result


# ---------------------------------------------------------------------------
# 4.2  get_price_history
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_price_history(
    symbol: str,
    market: str | None = None,
    period: str = "1mo",
    interval: str = "1d",
    adjust: str | None = None,
) -> dict:
    """Query historical K-line data for an instrument.

    Args:
        symbol: User input.
        market: Preferred market.
        period: 1d / 5d / 1mo / 3mo / 6mo / 1y / 2y / 5y / max.
        interval: 1m / 5m / 15m / 30m / 60m / 1d / 1wk / 1mo.
        adjust: none / qfq / hfq. Default qfq for CN, none for US.
    """
    from stockhub_mcp.tools.history import get_price_history_impl
    result = await get_price_history_impl(
        symbol=symbol, market=market,
        period=period, interval=interval, adjust=adjust,
    )
    # Inject data timestamp from latest K-line date
    if result.get("success"):
        history = result.get("data", {}).get("history", [])
        if history:
            result.setdefault("meta", {})["data_timestamp"] = history[-1]["date"]
    return result


# ---------------------------------------------------------------------------
# 4.3  get_batch_quotes
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_batch_quotes(
    symbols: list[str],
    bypass_cache: bool = False,
) -> dict:
    """Batch query real-time quotes for up to 20 symbols.

    Args:
        symbols: List of user-input symbols (max 20).
        bypass_cache: If True, skip the local cache for all symbols.
    """
    from stockhub_mcp.tools.batch import get_batch_quotes_impl
    return await get_batch_quotes_impl(
        symbols=symbols, bypass_cache=bypass_cache,
    )


# ---------------------------------------------------------------------------
# 4.4  get_technical_indicators
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_technical_indicators(
    symbol: str,
    indicators: list[str],
    market: str | None = None,
    period: str = "3mo",
    interval: str = "1d",
    adjust: str | None = None,
) -> dict:
    """Compute technical indicators for an instrument.

    Args:
        symbol: User input.
        indicators: List of indicator names: MA / EMA / RSI / MACD / BOLL / KDJ.
        market: Preferred market.
        period: Look-back period for K-line data (default 3mo).
        interval: Bar interval (default 1d).
        adjust: Adjustment method (default qfq for CN).
    """
    from stockhub_mcp.tools.indicators import get_technical_indicators_impl
    result = await get_technical_indicators_impl(
        symbol=symbol, indicators=indicators,
        market=market, period=period, interval=interval, adjust=adjust,
    )
    if result.get("success"):
        # V0.4 fix: inject RSI oversold/overbought signal adjustment
        analysis_sig = result.get("data", {}).get("analysis", {}).get("signal", {})
        reasons = analysis_sig.get("reasons", [])
        rsi = result.get("data", {}).get("indicators", {}).get("RSI", {})
        rsi14 = rsi.get("RSI14", 50)
        if rsi14 < 30 and "RSI超卖" not in str(reasons):
            score = analysis_sig.get("signal_score", 0) + 10
            analysis_sig["signal_score"] = score
            reasons.append("RSI超卖(<30)反弹信号")
            analysis_sig["signal"] = "买入" if score >= 45 else ("观望" if score >= 25 else analysis_sig.get("signal", ""))
        if rsi14 > 70 and "RSI超买" not in str(reasons):
            analysis_sig["signal_score"] = max(0, analysis_sig.get("signal_score", 0) - 5)
            reasons.append("RSI超买(>70)")
        # Inject data_timestamp
        meta = result.setdefault("meta", {})
        meta.setdefault("data_timestamp", result.get("data", {}).get("data_timestamp", ""))
    return result


# ---------------------------------------------------------------------------
# 4.5  get_sector_boards
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_sector_boards(
    type: str = "industry",
) -> dict:
    """Query A-share industry / concept sector boards.

    Args:
        type: Board type – 'industry' (default) or 'concept'.
    """
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    from stockhub_mcp.services.eastmoney_source import EastMoneySource
    from stockhub_mcp.config import settings

    builder = ResponseBuilder()

    if type not in ("industry", "concept"):
        return builder.error(
            error={
                "code": "INVALID_BOARD_TYPE",
                "type": "input_error",
                "message": f"Unsupported board type: '{type}'. Use 'industry' or 'concept'.",
                "retryable": False,
                "details": {},
            },
        )

    try:
        # Try efinance first (free SDK, more stable)
        data = None
        used_source = "eastmoney"
        try:
            from stockhub_mcp.services.efinance_source import EfinanceSource
            ef = EfinanceSource()
            if ef.available():
                data = ef.fetch_sector_boards(type)
                used_source = "efinance"
        except Exception:
            pass

        if data is None:
            source = EastMoneySource()
            data = source.fetch_sector_boards(type)
        meta = {
            "market": "CN",
            "symbol": "",
            "source": "eastmoney",
            "currency": "CNY",
            "timezone": "Asia/Shanghai",
            "market_session": "",
            "is_realtime": False,
            "data_delay_seconds": 0,
            "quality_flag": "live",
        }
        return builder.success(data=data.model_dump(), meta=meta)
    except Exception as exc:
        return builder.error(
            error={
                "code": "SECTOR_FETCH_FAILED",
                "type": "source_error",
                "message": f"Failed to fetch sector boards: {exc}",
                "retryable": True,
                "details": {},
            },
        )


# ---------------------------------------------------------------------------
# 4.6  get_capital_flow
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_capital_flow(
    scope: str = "market",
) -> dict:
    """Query A-share capital flow at market or sector level.

    Args:
        scope: 'market' (default) or 'sector'.
    """
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    from stockhub_mcp.services.eastmoney_source import EastMoneySource

    builder = ResponseBuilder()

    try:
        # Try efinance first (free SDK, more stable)
        data = None
        used_source = "eastmoney"
        try:
            from stockhub_mcp.services.efinance_source import EfinanceSource
            ef = EfinanceSource()
            if ef.available():
                data = ef.fetch_capital_flow(scope)
                used_source = "efinance"
        except Exception:
            pass

        if data is None:
            source = EastMoneySource()
            data = source.fetch_capital_flow(scope)

        meta = {
            "market": "CN",
            "symbol": "",
            "source": used_source,
            "currency": "CNY",
            "timezone": "Asia/Shanghai",
            "market_session": "",
            "is_realtime": False,
            "data_delay_seconds": 0,
            "quality_flag": "live",
        }
        return builder.success(data=data.model_dump(), meta=meta)
    except Exception as exc:
        return builder.error(
            error={
                "code": "CAPITAL_FLOW_FAILED",
                "type": "source_error",
                "message": f"Failed to fetch capital flow: {exc}",
                "retryable": True,
                "details": {},
            },
        )


# ---------------------------------------------------------------------------
# 4.7  search_symbol
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_symbol(
    query: str,
    market: str | None = None,
    instrument_type: str | None = None,
    max_results: int = 10,
) -> dict:
    """Fuzzy-search for an instrument symbol.

    Args:
        query: Code, name, or partial name.
        market: Narrow search to this market.
        instrument_type: Filter: stock / etf / index / fund.
        max_results: Maximum hits (default 10).
    """
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    from stockhub_mcp.domain.symbol.resolver import SymbolResolver
    from stockhub_mcp.enums import Market, InstrumentType

    builder = ResponseBuilder()
    resolver = SymbolResolver()

    preferred_market = None
    if market:
        try:
            preferred_market = Market(market.upper())
        except ValueError:
            pass

    inst_type = None
    if instrument_type:
        try:
            inst_type = InstrumentType(instrument_type.lower())
        except ValueError:
            pass

    candidates = resolver.search(
        query, market=preferred_market,
        instrument_type=inst_type, max_results=max_results,
    )

    results = [
        {
            "symbol": c.symbol.to_internal(),
            "name": c.name,
            "display_name": c.display_name,
            "market": c.symbol.market.value,
            "exchange": c.exchange,
            "instrument_type": c.instrument_type.value,
            "currency": c.currency,
        }
        for c in candidates
    ]

    meta = {
        "market": market or "",
        "symbol": query,
        "source": "symbol_db",
        "currency": "",
        "timezone": "",
        "market_session": "",
        "is_realtime": False,
        "data_delay_seconds": 0,
        "quality_flag": "",
    }

    return builder.success(data={"results": results}, meta=meta)


# ---------------------------------------------------------------------------
# 4.8  get_source_status
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_source_status() -> dict:
    """Query the current health status of all data sources."""
    from datetime import datetime, timezone
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    from stockhub_mcp.services.circuit_breaker import CircuitBreaker
    from stockhub_mcp.tools.quote import _CIRCUIT_BREAKER as cb

    builder = ResponseBuilder()
    now = datetime.now(timezone.utc)

    source_info = [
        ("yfinance", ["US", "HK"]),
        ("tx", ["CN", "HK"]),
        ("sina", ["CN"]),
        ("eastmoney", ["CN"]),
        ("akshare", ["CN"]),
    ]

    sources = []
    for name, coverage in source_info:
        status = cb.get_status(name).value
        degraded_since = cb.degraded_since(name)
        sources.append({
            "name": name,
            "status": status,
            "market_coverage": coverage,
            "last_checked": now.isoformat(),
            "failures_in_window": cb.get_failure_count(name),
            "degraded_since": degraded_since.isoformat() if degraded_since else None,
        })

    meta = {
        "market": "",
        "symbol": "",
        "source": "circuit_breaker",
        "currency": "",
        "timezone": "",
        "market_session": "",
        "is_realtime": True,
        "data_delay_seconds": 0,
        "quality_flag": "",
    }

    return builder.success(data={"sources": sources}, meta=meta)


# ---------------------------------------------------------------------------
# 4.9  get_trading_calendar
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_trading_calendar(
    market: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict:
    """Query the trading calendar for a given market.

    Args:
        market: CN / HK / US.
        from_date: Start date (default today).
        to_date: End date (default 30 days from today).
    """
    from datetime import date, datetime, timedelta
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    from stockhub_mcp.domain.market.calendar import TradingCalendar
    from stockhub_mcp.enums import Market

    builder = ResponseBuilder()

    try:
        mkt = Market(market.upper())
    except ValueError:
        return builder.error(
            error={
                "code": "INVALID_MARKET",
                "type": "input_error",
                "message": f"Invalid market: '{market}'. Use CN, HK, or US.",
                "retryable": False,
                "details": {},
            },
        )

    cal = TradingCalendar()

    if from_date:
        try:
            fd = date.fromisoformat(from_date)
        except ValueError:
            return builder.error(
                error={
                    "code": "INVALID_DATE",
                    "type": "input_error",
                    "message": f"Invalid from_date: '{from_date}'. Use YYYY-MM-DD.",
                    "retryable": False,
                    "details": {},
                },
            )
    else:
        fd = date.today()

    if to_date:
        try:
            td = date.fromisoformat(to_date)
        except ValueError:
            return builder.error(
                error={
                    "code": "INVALID_DATE",
                    "type": "input_error",
                    "message": f"Invalid to_date: '{to_date}'. Use YYYY-MM-DD.",
                    "retryable": False,
                    "details": {},
                },
            )
    else:
        td = fd + timedelta(days=30)

    holidays_raw = cal.get_holidays(mkt, fd, td)
    holidays = [
        {"date": h["date"], "name": h.get("name", ""), "type": h.get("type", "public_holiday")}
        for h in holidays_raw
    ]

    total_days = (td - fd).days + 1
    trading_days = total_days - len(holidays)
    # Count weekends in range
    cursor = fd
    while cursor <= td:
        if cursor.weekday() >= 5:
            trading_days -= 1
        cursor += timedelta(days=1)

    next_td = cal.next_trading_day(mkt, td + timedelta(days=1))

    data = {
        "market": mkt.value,
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "total_days": total_days,
        "trading_days": max(0, trading_days),
        "holidays": holidays,
        "next_trading_day": next_td.isoformat(),
    }

    meta = {
        "market": mkt.value,
        "symbol": "",
        "source": "akshare" if mkt == Market.CN else "yfinance",
        "currency": "",
        "timezone": "",
        "market_session": "",
        "is_realtime": False,
        "data_delay_seconds": 0,
        "quality_flag": "",
    }

    return builder.success(data=data, meta=meta)


# ---------------------------------------------------------------------------
# 4.10  clear_quote_cache
# ---------------------------------------------------------------------------


@mcp.tool()
async def clear_quote_cache(
    scope: str,
    market: str | None = None,
    symbol: str | None = None,
    tool: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Clear local price-cache entries.

    Args:
        scope: symbol / market / tool / all (must be explicit).
        market: Filter by market.
        symbol: Filter by symbol.
        tool: Filter by tool name.
        dry_run: If True, report matched count without deleting.
    """
    from stockhub_mcp.tools.cache_control import clear_cache_impl
    return await clear_cache_impl(
        scope=scope, market=market, symbol=symbol,
        tool_name=tool, dry_run=dry_run,
    )


# ============================================================================
# V0.2 中国市场增强工具
# ============================================================================


# -- Northbound / Southbound flow --

@mcp.tool()
async def get_northbound_flow(days: int = 20) -> dict:
    """Fetch northbound (沪深股通) capital flow history.

    Args:
        days: Number of recent trading days (default 20).
    """
    from stockhub_mcp.tools.northbound import get_northbound_flow_impl
    return await get_northbound_flow_impl(days=days)


@mcp.tool()
async def get_southbound_flow(days: int = 20) -> dict:
    """Fetch southbound (港股通) capital flow history.

    Args:
        days: Number of recent trading days (default 20).
    """
    from stockhub_mcp.tools.northbound import get_southbound_flow_impl
    return await get_southbound_flow_impl(days=days)


# -- Dragon Tiger --

@mcp.tool()
async def get_dragon_tiger_list() -> dict:
    """Fetch today's A-share dragon-tiger board list."""
    from stockhub_mcp.tools.china_enhance import get_dragon_tiger_list_impl
    return await get_dragon_tiger_list_impl()


# -- Sector Constituents --

@mcp.tool()
async def get_sector_constituents(sector_code: str) -> dict:
    """Fetch constituent stocks of a sector/industry board.

    Args:
        sector_code: Sector board code, e.g. 'BK0001'.
    """
    from stockhub_mcp.tools.china_enhance import get_sector_constituents_impl
    return await get_sector_constituents_impl(sector_code=sector_code)


# -- Price Limits --

@mcp.tool()
async def get_price_limits(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Compute A-share price limits (涨跌停价格).

    Args:
        symbol: User input.
        market: Preferred market.
    """
    from stockhub_mcp.tools.price_limits import get_price_limits_impl
    return await get_price_limits_impl(symbol=symbol, market=market)


# -- Symbol Status --

@mcp.tool()
async def get_symbol_status(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Query trading status of an instrument.

    Args:
        symbol: User input.
        market: Preferred market.
    """
    from stockhub_mcp.tools.china_enhance import get_symbol_status_impl
    return await get_symbol_status_impl(symbol=symbol, market=market)


# -- Fund tools --

@mcp.tool()
async def get_fund_quote(fund_code: str) -> dict:
    """Fetch real-time fund NAV quote.

    Args:
        fund_code: 6-digit fund code.
    """
    from stockhub_mcp.tools.fund import get_fund_quote_impl
    return await get_fund_quote_impl(fund_code=fund_code)


@mcp.tool()
async def get_fund_nav_history(fund_code: str, period: str = "1mo") -> dict:
    """Fetch fund NAV history.

    Args:
        fund_code: 6-digit fund code.
        period: 1mo / 3mo / 6mo / 1y.
    """
    from stockhub_mcp.tools.fund import get_fund_nav_history_impl
    return await get_fund_nav_history_impl(fund_code=fund_code, period=period)


@mcp.tool()
async def get_fund_rankings(
    fund_type: str = "all",
    sort_by: str = "1y",
    max_results: int = 20,
) -> dict:
    """Fetch fund performance rankings.

    Args:
        fund_type: all / stock / mixed / bond / index.
        sort_by: 1m / 3m / 6m / 1y.
        max_results: Max results (default 20).
    """
    from stockhub_mcp.tools.fund import get_fund_rankings_impl
    return await get_fund_rankings_impl(
        fund_type=fund_type, sort_by=sort_by, max_results=max_results,
    )


@mcp.tool()
async def search_fund(query: str, max_results: int = 10) -> dict:
    """Search for funds by name or code.

    Args:
        query: Fund name or code.
        max_results: Max results.
    """
    from stockhub_mcp.tools.fund import search_fund_impl
    return await search_fund_impl(query=query, max_results=max_results)


# -- ETF tools --

@mcp.tool()
async def get_etf_quote(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch real-time ETF quote.

    Args:
        symbol: ETF code or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.etf import get_etf_quote_impl
    return await get_etf_quote_impl(symbol=symbol, market=market)


@mcp.tool()
async def get_etf_history(
    symbol: str,
    market: str | None = None,
    period: str = "1mo",
    interval: str = "1d",
    adjust: str | None = None,
) -> dict:
    """Fetch ETF historical K-line data.

    Args:
        symbol: ETF code or name.
        market: Preferred market.
        period: 1d / 5d / 1mo / 3mo / 6mo / 1y / 2y / 5y / max.
        interval: 1m / 5m / 15m / 30m / 60m / 1d / 1wk / 1mo.
        adjust: Adjustment method.
    """
    from stockhub_mcp.tools.etf import get_etf_history_impl
    return await get_etf_history_impl(
        symbol=symbol, market=market, period=period,
        interval=interval, adjust=adjust,
    )


@mcp.tool()
async def get_etf_info(symbol: str) -> dict:
    """Fetch ETF metadata (tracking index, fees, size, tags).

    Args:
        symbol: ETF code.
    """
    from stockhub_mcp.tools.etf import get_etf_info_impl
    return await get_etf_info_impl(symbol=symbol)


# -- Futures tools --

@mcp.tool()
async def search_futures_contract(query: str) -> dict:
    """Search futures contracts by name or code.

    Args:
        query: Futures name or code.
    """
    from stockhub_mcp.tools.futures import search_futures_contract_impl
    return await search_futures_contract_impl(query=query)


@mcp.tool()
async def get_futures_contract_info(symbol: str) -> dict:
    """Fetch futures contract details (size, tick, exchange).

    Args:
        symbol: Futures symbol code.
    """
    from stockhub_mcp.tools.futures import get_futures_contract_info_impl
    return await get_futures_contract_info_impl(symbol=symbol)


@mcp.tool()
async def get_futures_position_rank(
    symbol: str,
    date: str = "",
) -> dict:
    """Fetch futures broker position rankings.

    Args:
        symbol: Futures symbol code.
        date: Trading date (default today).
    """
    from stockhub_mcp.tools.futures import get_futures_position_rank_impl
    return await get_futures_position_rank_impl(symbol=symbol, date=date)


@mcp.tool()
async def get_futures_basis_history(symbol: str) -> dict:
    """Fetch futures basis history (spot vs futures spread).

    Args:
        symbol: Futures symbol code.
    """
    from stockhub_mcp.tools.futures import get_futures_basis_history_impl
    return await get_futures_basis_history_impl(symbol=symbol)


# ============================================================================
# V0.3 研究与上下文版
# ============================================================================


# -- Financial Statements --

@mcp.tool()
async def get_financial_statements(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch income statement, balance sheet, and cash flow.

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_financial_statements_impl
    return await get_financial_statements_impl(symbol=symbol, market=market)


# -- Valuation Metrics --

@mcp.tool()
async def get_valuation_metrics(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch valuation metrics (PE, PB, PS, PEG, EV/EBITDA, market cap).

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_valuation_metrics_impl
    return await get_valuation_metrics_impl(symbol=symbol, market=market)


# -- Quality Metrics --

@mcp.tool()
async def get_quality_metrics(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch quality metrics (ROE, ROA, margins, debt/equity, growth).

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_quality_metrics_impl
    return await get_quality_metrics_impl(symbol=symbol, market=market)


# -- Dividends & Splits --

@mcp.tool()
async def get_dividends_splits(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch dividend and stock split history.

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_dividends_splits_impl
    return await get_dividends_splits_impl(symbol=symbol, market=market)


# -- Holders --

@mcp.tool()
async def get_holders(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch major institutional holders.

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_holders_impl
    return await get_holders_impl(symbol=symbol, market=market)


# -- Analyst Forecasts --

@mcp.tool()
async def get_analyst_forecasts(
    symbol: str,
    market: str | None = None,
) -> dict:
    """Fetch analyst revenue and EPS forecasts.

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_analyst_forecasts_impl
    return await get_analyst_forecasts_impl(symbol=symbol, market=market)


# -- Options Chain --

@mcp.tool()
async def get_options_chain(
    symbol: str,
    expiry: str = "",
    market: str | None = None,
) -> dict:
    """Fetch options chain (calls + puts) for a US stock.

    Args:
        symbol: US stock ticker.
        expiry: Expiration date (default nearest).
        market: Preferred market.
    """
    from stockhub_mcp.tools.research import get_options_chain_impl
    return await get_options_chain_impl(symbol=symbol, expiry=expiry, market=market)


# -- Index Quote --

@mcp.tool()
async def get_index_quote(symbol: str) -> dict:
    """Fetch real-time index quote (^GSPC, ^DJI, ^IXIC, ^HSI, etc).

    Args:
        symbol: Index symbol or name (sp500, nasdaq, dow, hsi).
    """
    from stockhub_mcp.tools.research import get_index_quote_impl
    return await get_index_quote_impl(symbol=symbol)


# -- Index History --

@mcp.tool()
async def get_index_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
) -> dict:
    """Fetch index historical K-line data.

    Args:
        symbol: Index symbol.
        period: 1mo / 3mo / 6mo / 1y / 5y / max.
        interval: 1d / 1wk / 1mo.
    """
    from stockhub_mcp.tools.history import get_price_history_impl
    return await get_price_history_impl(symbol=symbol, period=period, interval=interval)


# -- Compare Stocks --

@mcp.tool()
async def compare_stocks(symbols: list[str]) -> dict:
    """Compare multiple stocks on key valuation metrics.

    Args:
        symbols: List of stock tickers (max 10).
    """
    from stockhub_mcp.tools.research import compare_stocks_impl
    return await compare_stocks_impl(symbols=symbols)


# -- Compare Indices --

@mcp.tool()
async def compare_indices(indices: list[str]) -> dict:
    """Compare multiple indices on returns (1m/3m/6m/1y).

    Args:
        indices: List of index symbols (max 5).
    """
    from stockhub_mcp.tools.research import compare_indices_impl
    return await compare_indices_impl(indices=indices)


# -- Quick Analysis (Pipeline) --

@mcp.tool()
async def get_quick_analysis(
    symbol: str,
    market: str | None = None,
) -> dict:
    """One-shot combined analysis: quote + technical indicators + trend.

    Args:
        symbol: Stock ticker or name.
        market: Preferred market.
    """
    from stockhub_mcp.tools.quick_analysis import get_quick_analysis_impl
    return await get_quick_analysis_impl(symbol=symbol, market=market)


# ============================================================================
# V0.4 工具
# ============================================================================


@mcp.tool()
async def get_valuation_percentile(
    symbol: str,
    metric: str = "pe",
    market: str | None = None,
) -> dict:
    """Compute PE/PB historical percentile ranking.

    Args:
        symbol: Stock ticker or name.
        metric: 'pe' or 'pb'.
        market: Preferred market.
    """
    from stockhub_mcp.tools.valuation_percentile import get_valuation_percentile_impl
    return await get_valuation_percentile_impl(symbol=symbol, metric=metric, market=market)
