"""V0.3 – Research tools: financials, valuation, dividends, holders, analysts, options, index."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.domain.symbol.resolver import SymbolResolver, StandardSymbol
from stockhub_mcp.enums import Market

_SYMBOL_RESOLVER = SymbolResolver()


def _resolve(symbol: str, market: str | None, builder: ResponseBuilder):
    preferred = Market(market.upper()) if market else None
    result = _SYMBOL_RESOLVER.resolve(symbol, preferred_market=preferred)
    if not result.resolved:
        return None, None, builder.error(error={
            "code": "SYMBOL_NOT_RESOLVED", "type": "input_error",
            "message": f"Cannot resolve: '{symbol}'", "retryable": False, "details": {},
        })
    std = result.symbol
    return std, std.market, None


def _make_meta(market: str, symbol: str, source: str, quality: str = "live") -> dict:
    return {
        "market": market, "symbol": symbol, "source": source,
        "currency": "USD" if market == "US" else ("HKD" if market == "HK" else "CNY"),
        "timezone": "America/New_York" if market == "US" else ("Asia/Hong_Kong" if market == "HK" else "Asia/Shanghai"),
        "market_session": "", "is_realtime": False, "data_delay_seconds": 0,
        "quality_flag": quality,
    }


async def get_financial_statements_impl(
    symbol: str, market: str | None = None,
) -> dict[str, Any]:
    """Fetch income statement, balance sheet, cash flow via yfinance."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        ticker_str = nm.to_yfinance(std)
        t = yf.Ticker(ticker_str)

        inc = t.income_stmt  # annual
        bal = t.balance_sheet
        cf = t.cashflow

        from stockhub_mcp.models.finance import (
            FinancialStatementsData, IncomeStatement, BalanceSheet, CashFlow,
        )
        income_items: list[IncomeStatement] = []
        if inc is not None and not inc.empty:
            for col in inc.columns[:4]:
                income_items.append(IncomeStatement(
                    date=str(col.date()), revenue=_sf(inc.loc["Total Revenue", col] if "Total Revenue" in inc.index else 0),
                    operating_income=_sf(inc.loc["Operating Income", col] if "Operating Income" in inc.index else 0),
                    net_income=_sf(inc.loc["Net Income", col] if "Net Income" in inc.index else 0),
                    eps=_sf(inc.loc["Diluted EPS", col] if "Diluted EPS" in inc.index else (inc.loc["Basic EPS", col] if "Basic EPS" in inc.index else 0)),
                ))

        bal_items: list[BalanceSheet] = []
        if bal is not None and not bal.empty:
            for col in bal.columns[:4]:
                bal_items.append(BalanceSheet(
                    date=str(col.date()),
                    total_assets=_sf(bal.loc["Total Assets", col] if "Total Assets" in bal.index else 0),
                    total_liabilities=_sf(bal.loc["Total Liabilities Net Minority Interest", col] if "Total Liabilities Net Minority Interest" in bal.index else 0),
                    total_equity=_sf(bal.loc["Stockholders Equity", col] if "Stockholders Equity" in bal.index else 0),
                    cash=_sf(bal.loc["Cash And Cash Equivalents", col] if "Cash And Cash Equivalents" in bal.index else 0),
                    debt=_sf(bal.loc["Total Debt", col] if "Total Debt" in bal.index else 0),
                ))

        cf_items: list[CashFlow] = []
        if cf is not None and not cf.empty:
            for col in cf.columns[:4]:
                cf_items.append(CashFlow(
                    date=str(col.date()),
                    operating_cf=_sf(cf.loc["Operating Cash Flow", col] if "Operating Cash Flow" in cf.index else 0),
                    investing_cf=_sf(cf.loc["Investing Cash Flow", col] if "Investing Cash Flow" in cf.index else 0),
                    financing_cf=_sf(cf.loc["Financing Cash Flow", col] if "Financing Cash Flow" in cf.index else 0),
                    free_cash_flow=_sf(cf.loc["Free Cash Flow", col] if "Free Cash Flow" in cf.index else 0),
                ))

        data = FinancialStatementsData(
            symbol=std.to_internal(), name=t.info.get("longName", ""),
            market=mkt.value, currency=t.info.get("currency", ""),
            income=income_items, balance=bal_items, cash_flow=cf_items,
        )
        return builder.success(data=data.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "FINANCIALS_FAILED", "type": "source_error",
            "message": f"Financial statements failed: {exc}", "retryable": True, "details": {},
        })


async def get_valuation_metrics_impl(
    symbol: str, market: str | None = None,
) -> dict[str, Any]:
    """Fetch valuation metrics via yfinance."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        t = yf.Ticker(nm.to_yfinance(std))
        info = t.info

        from stockhub_mcp.models.finance import ValuationMetricsData, QualityMetricsData
        val = ValuationMetricsData(
            symbol=std.to_internal(), name=info.get("longName", ""),
            market=mkt.value,
            pe_ttm=_sf(info.get("trailingPE", 0)),
            pe_forward=_sf(info.get("forwardPE", 0)),
            pb=_sf(info.get("priceToBook", 0)),
            ps_ttm=_sf(info.get("priceToSalesTrailing12Months", 0)),
            peg=_sf(info.get("pegRatio", 0)),
            ev_ebitda=_sf(info.get("enterpriseToEbitda", 0)),
            market_cap=_sf(info.get("marketCap", 0)),
            enterprise_value=_sf(info.get("enterpriseValue", 0)),
            dividend_yield=_sf(info.get("dividendYield", 0)),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return builder.success(data=val.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "VALUATION_FAILED", "type": "source_error",
            "message": f"Valuation failed: {exc}", "retryable": True, "details": {},
        })


async def get_quality_metrics_impl(
    symbol: str, market: str | None = None,
) -> dict[str, Any]:
    """Fetch quality metrics via yfinance."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        t = yf.Ticker(nm.to_yfinance(std))
        info = t.info

        from stockhub_mcp.models.finance import QualityMetricsData
        q = QualityMetricsData(
            symbol=std.to_internal(),
            roe=_sf(info.get("returnOnEquity", 0)) * 100,
            roa=_sf(info.get("returnOnAssets", 0)) * 100,
            gross_margin=_sf(info.get("grossMargins", 0)) * 100,
            net_margin=_sf(info.get("profitMargins", 0)) * 100,
            debt_to_equity=_sf(info.get("debtToEquity", 0)),
            current_ratio=_sf(info.get("currentRatio", 0)),
            revenue_growth=_sf(info.get("revenueGrowth", 0)) * 100,
            earnings_growth=_sf(info.get("earningsGrowth", 0)) * 100,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return builder.success(data=q.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "QUALITY_FAILED", "type": "source_error",
            "message": f"Quality metrics failed: {exc}", "retryable": True, "details": {},
        })


async def get_dividends_splits_impl(
    symbol: str, market: str | None = None,
) -> dict[str, Any]:
    """Fetch dividend/split history via yfinance."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        t = yf.Ticker(nm.to_yfinance(std))

        from stockhub_mcp.models.research import DividendsSplitsData, DividendItem, SplitItem
        divs = t.dividends
        splits = t.splits

        div_items: list[DividendItem] = []
        if divs is not None and not divs.empty:
            for dt, val in divs.tail(20).items():
                div_items.append(DividendItem(date=str(dt.date()), amount=float(val), ex_date=str(dt.date())))

        split_items: list[SplitItem] = []
        if splits is not None and not splits.empty:
            for dt, val in splits.tail(10).items():
                split_items.append(SplitItem(date=str(dt.date()), ratio=float(val)))

        data = DividendsSplitsData(symbol=std.to_internal(), dividends=div_items, splits=split_items)
        return builder.success(data=data.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "DIVIDENDS_FAILED", "type": "source_error",
            "message": f"Dividends failed: {exc}", "retryable": True, "details": {},
        })


async def get_holders_impl(
    symbol: str, market: str | None = None,
) -> dict[str, Any]:
    """Fetch major holders via yfinance."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        t = yf.Ticker(nm.to_yfinance(std))
        info = t.info

        from stockhub_mcp.models.research import HoldersData, HolderItem
        inst_items: list[HolderItem] = []
        inst_holders = t.institutional_holders
        if inst_holders is not None and not inst_holders.empty:
            for _, row in inst_holders.head(10).iterrows():
                inst_items.append(HolderItem(
                    name=str(row.get("Holder", "")),
                    shares=_sf(row.get("Shares", 0)),
                    pct=_sf(row.get("% Out", 0)),
                ))

        data = HoldersData(
            symbol=std.to_internal(),
            institutional=inst_items,
            insider_pct=_sf(info.get("heldPercentInsiders", 0)) * 100,
            institutional_pct=_sf(info.get("heldPercentInstitutions", 0)) * 100,
        )
        return builder.success(data=data.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "HOLDERS_FAILED", "type": "source_error",
            "message": f"Holders failed: {exc}", "retryable": True, "details": {},
        })


async def get_analyst_forecasts_impl(
    symbol: str, market: str | None = None,
) -> dict[str, Any]:
    """Fetch analyst forecasts via yfinance."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        t = yf.Ticker(nm.to_yfinance(std))

        from stockhub_mcp.models.research import AnalystForecastsData, ForecastItem
        forecasts: list[ForecastItem] = []
        try:
            rec = t.recommendations
            if rec is not None and not rec.empty:
                count = len(rec)
            else:
                count = 0
        except Exception:
            count = 0

        info = t.info
        forecasts.append(ForecastItem(
            period="current_quarter",
            revenue_low=_sf(info.get("revenueLow", 0)),
            revenue_avg=_sf(info.get("revenueAvg", 0)),
            revenue_high=_sf(info.get("revenueHigh", 0)),
            eps_low=_sf(info.get("epsLow", 0)),
            eps_avg=_sf(info.get("epsAvg", 0)),
            eps_high=_sf(info.get("epsHigh", 0)),
            analysts=info.get("numberOfAnalystOpinions", count),
        ))

        data = AnalystForecastsData(symbol=std.to_internal(), forecasts=forecasts)
        return builder.success(data=data.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "FORECASTS_FAILED", "type": "source_error",
            "message": f"Analyst forecasts failed: {exc}", "retryable": True, "details": {},
        })


async def get_options_chain_impl(
    symbol: str, expiry: str = "", market: str | None = None,
) -> dict[str, Any]:
    """Fetch options chain via yfinance (US stocks only)."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        std, mkt, err = _resolve(symbol, market, builder)
        if err: return err
        nm = SymbolNormalizer()
        t = yf.Ticker(nm.to_yfinance(std))

        expiries = t.options if t.options else []
        selected = expiry if expiry and expiry in expiries else (expiries[0] if expiries else None)
        if not selected:
            return builder.error(error={
                "code": "NO_OPTIONS", "type": "business_error",
                "message": "No options available for this instrument.",
                "retryable": False, "details": {},
            })

        chain = t.option_chain(selected)
        from stockhub_mcp.models.research import OptionsChainData, OptionItem

        calls: list[OptionItem] = []
        for _, row in chain.calls.head(20).iterrows():
            calls.append(OptionItem(strike=_sf(row.get("strike", 0)), expiry=selected, type="call",
                last=_sf(row.get("lastPrice", 0)), bid=_sf(row.get("bid", 0)), ask=_sf(row.get("ask", 0)),
                volume=int(row.get("volume", 0) or 0), open_interest=int(row.get("openInterest", 0) or 0),
                implied_volatility=_sf(row.get("impliedVolatility", 0)) * 100))

        puts: list[OptionItem] = []
        for _, row in chain.puts.head(20).iterrows():
            puts.append(OptionItem(strike=_sf(row.get("strike", 0)), expiry=selected, type="put",
                last=_sf(row.get("lastPrice", 0)), bid=_sf(row.get("bid", 0)), ask=_sf(row.get("ask", 0)),
                volume=int(row.get("volume", 0) or 0), open_interest=int(row.get("openInterest", 0) or 0),
                implied_volatility=_sf(row.get("impliedVolatility", 0)) * 100))

        data = OptionsChainData(symbol=std.to_internal(), calls=calls, puts=puts)
        return builder.success(data=data.model_dump(), meta=_make_meta(mkt.value, std.to_internal(), "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "OPTIONS_FAILED", "type": "source_error",
            "message": f"Options failed: {exc}", "retryable": True, "details": {},
        })


async def get_index_quote_impl(symbol: str) -> dict[str, Any]:
    """Fetch index quote via yfinance (^GSPC, ^DJI, ^IXIC, ^HSI, etc)."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf

        # Map common names to yfinance symbols
        index_map = {
            "sp500": "^GSPC", "nasdaq": "^IXIC", "dow": "^DJI",
            "hsi": "^HSI", "shanghai": "000001.SS", "shenzhen": "399001.SZ",
        }
        ticker_str = index_map.get(symbol.lower(), symbol)
        t = yf.Ticker(ticker_str)
        info = t.info

        from stockhub_mcp.models.research import IndexQuoteData
        data = IndexQuoteData(
            symbol=ticker_str, name=info.get("shortName", ticker_str),
            price=_sf(info.get("regularMarketPrice", 0)),
            change=_sf(info.get("regularMarketChange", 0)),
            change_pct=_sf(info.get("regularMarketChangePercent", 0)),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return builder.success(data=data.model_dump(),
            meta=_make_meta("US", ticker_str, "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "INDEX_FAILED", "type": "source_error",
            "message": f"Index quote failed: {exc}", "retryable": True, "details": {},
        })


async def compare_stocks_impl(symbols: list[str]) -> dict[str, Any]:
    """Compare multiple stocks on key valuation metrics."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.models.finance import CompareStocksData, CompareItem
        items: list[CompareItem] = []
        for sym in symbols[:10]:
            try:
                t = yf.Ticker(sym)
                info = t.info
                items.append(CompareItem(
                    symbol=sym, name=info.get("longName", sym),
                    pe_ttm=_sf(info.get("trailingPE", 0)),
                    pb=_sf(info.get("priceToBook", 0)),
                    market_cap=_sf(info.get("marketCap", 0)),
                    dividend_yield=_sf(info.get("dividendYield", 0)),
                    revenue_growth=_sf(info.get("revenueGrowth", 0)) * 100,
                    roe=_sf(info.get("returnOnEquity", 0)) * 100,
                ))
            except Exception:
                pass
        data = CompareStocksData(items=items, metric_timestamp=datetime.now(timezone.utc).isoformat())
        return builder.success(data=data.model_dump(),
            meta=_make_meta("US", "", "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "COMPARE_FAILED", "type": "source_error",
            "message": f"Compare failed: {exc}", "retryable": True, "details": {},
        })


async def compare_indices_impl(indices: list[str]) -> dict[str, Any]:
    """Compare multiple indices on returns."""
    builder = ResponseBuilder()
    try:
        import yfinance as yf
        from stockhub_mcp.models.research import CompareIndicesData, IndexCompareItem
        items: list[IndexCompareItem] = []
        for idx in indices[:5]:
            try:
                t = yf.Ticker(idx)
                info = t.info
                items.append(IndexCompareItem(
                    symbol=idx, name=info.get("shortName", idx),
                    price=_sf(info.get("regularMarketPrice", 0)),
                    change_pct=_sf(info.get("regularMarketChangePercent", 0)),
                    return_1m=_sf(info.get("oneMonthReturn", 0)) * 100,
                    return_3m=_sf(info.get("threeMonthReturn", 0)) * 100,
                    return_6m=_sf(info.get("sixMonthReturn", 0)) * 100,
                    return_1y=_sf(info.get("oneYearReturn", 0)) * 100,
                ))
            except Exception:
                pass
        data = CompareIndicesData(items=items)
        return builder.success(data=data.model_dump(),
            meta=_make_meta("US", "", "yfinance"))
    except Exception as exc:
        return builder.error(error={
            "code": "COMPARE_INDICES_FAILED", "type": "source_error",
            "message": f"Compare indices failed: {exc}", "retryable": True, "details": {},
        })


def _sf(val: Any, default: float = 0.0) -> float:
    try:
        v = float(val)
        return 0.0 if v != v else v  # NaN check
    except (TypeError, ValueError):
        return default
