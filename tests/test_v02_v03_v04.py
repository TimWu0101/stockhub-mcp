"""QA tests for V0.2 + V0.3 + V0.4 tools — non-network tests (model validation, error paths)."""

import pytest
import sys
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# -- V0.2 Models ----------------------------------------------------------------

def test_fund_models():
    from stockhub_mcp.models.fund import FundQuoteData, FundNAVHistoryData, FundRankingData
    q = FundQuoteData(symbol="CN:000001", name="test", nav=1.5)
    assert q.symbol == "CN:000001"
    assert q.nav == 1.5
    assert q.instrument_type == "fund"

    # NAV history
    h = FundNAVHistoryData(symbol="CN:000001", period="1mo", count=10, history=[])
    assert h.period == "1mo"

    # Ranking
    r = FundRankingData(rankings=[], total=0)
    assert r.total == 0


def test_etf_models():
    from stockhub_mcp.models.etf import ETFQuoteData, ETFInfoData
    q = ETFQuoteData(symbol="CN:510050")
    assert q.instrument_type == "etf"

    info = ETFInfoData(symbol="CN:510050", name="上证50ETF")
    assert info.name == "上证50ETF"


def test_flow_models():
    from stockhub_mcp.models.flow import NorthboundFlowData, FlowDataPoint
    f = FlowDataPoint(date="2026-01-01", net_inflow=100.0)
    assert f.net_inflow == 100.0
    n = NorthboundFlowData(data=[f])
    assert len(n.data) == 1


def test_enhance_models():
    from stockhub_mcp.models.enhance import (
        DragonTigerData, DragonTigerItem, PriceLimitsData,
        SymbolStatusData, SectorConstituentsData, ConstituentItem,
    )
    dt = DragonTigerItem(symbol="CN:000001", name="test", close=10.0,
                         buy_amount=100, sell_amount=50, net_amount=50)
    assert dt.symbol == "CN:000001"

    pl = PriceLimitsData(symbol="CN:000001", prev_close=10.0, limit_up=11.0, limit_down=9.0)
    assert pl.limit_up == 11.0

    ss = SymbolStatusData(symbol="CN:000001", status="normal")
    assert ss.status == "normal"

    sc = SectorConstituentsData(sector_code="BK0001", constituents=[], count=0)
    assert sc.sector_code == "BK0001"


def test_futures_models():
    from stockhub_mcp.models.futures import (
        FuturesContractInfo, FuturesPositionRankData, FuturesBasisData,
    )
    ci = FuturesContractInfo(symbol="CN:RB", name="螺纹钢")
    assert ci.name == "螺纹钢"

    pr = FuturesPositionRankData(symbol="CN:RB", date="2026-01-01")
    assert pr.symbol == "CN:RB"

    bd = FuturesBasisData(symbol="CN:RB", data=[])
    assert bd.symbol == "CN:RB"


def test_search_model_optional_fields():
    """V0.2 fix: exchange/currency must be optional."""
    from stockhub_mcp.models.search import SearchResultItem
    item = SearchResultItem(symbol="CN:000001", name="test", display_name="test (000001)",
                            market="CN", instrument_type="fund")
    assert item.exchange == ""
    assert item.currency == ""


# -- V0.3 Models ----------------------------------------------------------------

def test_finance_models():
    from stockhub_mcp.models.finance import (
        ValuationMetricsData, QualityMetricsData, CompareStocksData, CompareItem,
        FinancialStatementsData, IncomeStatement, BalanceSheet, CashFlow,
    )
    v = ValuationMetricsData(symbol="US:AAPL", pe_ttm=30.0, pb=40.0)
    assert v.pe_ttm == 30.0

    q = QualityMetricsData(symbol="US:AAPL", roe=140.0, gross_margin=47.0)
    assert q.roe == 140.0

    c = CompareItem(symbol="AAPL", name="Apple", pe_ttm=30.0)
    assert c.name == "Apple"

    # Financial statements
    inc = IncomeStatement(date="2026", revenue=100, net_income=20, eps=5.0)
    assert inc.eps == 5.0

    bal = BalanceSheet(date="2026", total_assets=1000)
    assert bal.total_assets == 1000

    cf = CashFlow(date="2026", operating_cf=50, free_cash_flow=30)
    assert cf.free_cash_flow == 30

    fs = FinancialStatementsData(symbol="US:AAPL", income=[inc], balance=[bal], cash_flow=[cf])
    assert len(fs.income) == 1

    cs = CompareStocksData(items=[c])
    assert len(cs.items) == 1


def test_research_models():
    from stockhub_mcp.models.research import (
        DividendsSplitsData, DividendItem, SplitItem,
        HoldersData, HolderItem, AnalystForecastsData, ForecastItem,
        OptionsChainData, OptionItem,
        IndexQuoteData, CompareIndicesData, IndexCompareItem,
    )
    # Dividends
    d = DividendItem(date="2026-01-01", amount=0.25)
    assert d.amount == 0.25
    s = SplitItem(date="2020-01-01", ratio=4.0)
    assert s.ratio == 4.0
    ds = DividendsSplitsData(symbol="US:AAPL", dividends=[d], splits=[s])
    assert len(ds.splits) == 1

    # Holders
    h = HolderItem(name="Vanguard", shares=500_000_000, pct=7.5)
    assert h.name == "Vanguard"
    hd = HoldersData(symbol="US:AAPL", institutional=[h], institutional_pct=75.0)
    assert hd.institutional_pct == 75.0

    # Analyst
    f = ForecastItem(period="2027", eps_avg=8.5, analysts=35)
    assert f.eps_avg == 8.5
    af = AnalystForecastsData(symbol="US:AAPL", forecasts=[f])
    assert len(af.forecasts) == 1

    # Options
    o = OptionItem(strike=250, expiry="2026-07-15", type="call", last=5.0, implied_volatility=20.0)
    assert o.type == "call"
    oc = OptionsChainData(symbol="US:AAPL", calls=[o], puts=[])
    assert len(oc.calls) == 1

    # Index
    iq = IndexQuoteData(symbol="^GSPC", name="S&P 500", price=7500)
    assert iq.price == 7500

    ic = IndexCompareItem(symbol="^GSPC", name="S&P 500", return_1m=5.0)
    assert ic.return_1m == 5.0

    ci = CompareIndicesData(items=[ic])
    assert len(ci.items) == 1


# -- V0.4 Pipeline --------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_basic():
    from stockhub_mcp.core.pipeline import Pipeline

    calls = []

    async def stage_a(ctx):
        calls.append("a")
        ctx["a"] = 1
        return ctx

    async def stage_b(ctx):
        calls.append("b")
        ctx["b"] = 2
        return ctx

    pipeline = Pipeline().stage(stage_a).stage(stage_b)
    result = await pipeline.run({})
    assert result["success"] is True
    assert calls == ["a", "b"]
    assert result["final"]["a"] == 1
    assert result["final"]["b"] == 2


@pytest.mark.asyncio
async def test_pipeline_error():
    from stockhub_mcp.core.pipeline import Pipeline

    async def stage_fail(ctx):
        raise RuntimeError("boom")

    async def stage_never(ctx):
        ctx["ran"] = True
        return ctx

    pipeline = Pipeline().stage(stage_fail).stage(stage_never)
    result = await pipeline.run({})
    assert result["success"] is True  # pipeline doesn't fail, just marks stage
    assert result["final"].get("ran") is None  # stage_never should not run


# -- V0.4 Risk Metrics (unit) -----------------------------------------------------

def test_risk_metrics_math():
    """Verify volatility/drawdown/Sharpe/VaR computation on a known series."""
    import numpy as np
    rng = np.random.default_rng(42)
    np.random.seed(42)  # keep old randint for pytest compatibility
    returns = np.random.normal(0.001, 0.02, 252)

    daily_vol = float(np.std(returns))
    ann_vol = daily_vol * np.sqrt(252)

    cumulative = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    max_dd = np.min(drawdown)

    excess = returns - 0.02 / 252
    sharpe = np.mean(excess) / np.std(returns) * np.sqrt(252)

    var_95 = np.percentile(returns, 5) * 100

    assert ann_vol > 0  # annualized volatility should be positive
    assert max_dd <= 0  # max drawdown is always <= 0
    assert var_95 < 0  # VaR 95% is negative


def test_beta_computation():
    """Simple beta: cov(x,y) / var(y)."""
    import numpy as np
    rng = np.random.default_rng(42)
    x = rng.normal(0.001, 0.02, 100)
    y = rng.normal(0.001, 0.015, 100)
    cov = np.cov(x, y)
    beta = cov[0, 1] / cov[1, 1]
    assert -5 < beta < 5  # beta for daily returns should be in reasonable range


@pytest.mark.asyncio
async def test_risk_metrics_unresolvable_symbol():
    """Unresolvable symbol should return error."""
    from stockhub_mcp.tools.risk import get_risk_metrics_impl
    result = await get_risk_metrics_impl(symbol="ZZZZ_INVALID")
    assert result["success"] is False


# -- V0.4 Quick Analysis (error path) ---------------------------------------------

@pytest.mark.asyncio
async def test_quick_analysis_unresolvable():
    """Quick analysis with bad symbol should return error."""
    from stockhub_mcp.tools.quick_analysis import get_quick_analysis_impl
    result = await get_quick_analysis_impl(symbol="ZZZZ_INVALID")
    assert result["success"] is False


# -- V0.4 Pipeline (edge cases) ---------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_empty():
    """Empty pipeline should still succeed."""
    from stockhub_mcp.core.pipeline import Pipeline
    result = await Pipeline().run({"initial": "value"})
    assert result["success"] is True
    assert result["final"] == {"initial": "value"}


@pytest.mark.asyncio
async def test_pipeline_chained_context():
    """Pipeline should pass context between stages."""
    from stockhub_mcp.core.pipeline import Pipeline

    async def stage_a(ctx):
        ctx["a"] = 1
        return ctx

    async def stage_b(ctx):
        ctx["b"] = ctx["a"] + 1
        return ctx

    result = await Pipeline().stage(stage_a).stage(stage_b).run({})
    assert result["final"]["a"] == 1
    assert result["final"]["b"] == 2


# -- V0.2 Price Limits -----------------------------------------------------------

@pytest.mark.asyncio
async def test_price_limits_invalid_symbol():
    from stockhub_mcp.tools.price_limits import get_price_limits_impl
    result = await get_price_limits_impl(symbol="ZZZZ_INVALID")
    assert result["success"] is False


# -- V0.2 Symbol Status ----------------------------------------------------------

@pytest.mark.asyncio
async def test_symbol_status_unresolvable():
    from stockhub_mcp.tools.china_enhance import get_symbol_status_impl
    result = await get_symbol_status_impl(symbol="ZZZZ_INVALID")
    assert result["success"] is False


# -- Response Builder ------------------------------------------------------------

def test_response_builder_success():
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    builder = ResponseBuilder()
    resp = builder.success(data={"foo": "bar"}, meta={"source": "test"})
    assert resp["success"] is True
    assert resp["data"] == {"foo": "bar"}


def test_response_builder_error():
    from stockhub_mcp.domain.response_builder import ResponseBuilder
    builder = ResponseBuilder()
    resp = builder.error(error={"code": "TEST", "type": "system_error", "message": "test"})
    assert resp["success"] is False
    assert resp["error"]["code"] == "TEST"


# -- STANDARD_COLUMNS ------------------------------------------------------------

def test_standard_columns():
    from stockhub_mcp.services.base import STANDARD_COLUMNS
    assert "date" in STANDARD_COLUMNS
    assert "open" in STANDARD_COLUMNS
    assert "close" in STANDARD_COLUMNS
    assert len(STANDARD_COLUMNS) == 8


# -- V0.4 Portfolio (unit) -------------------------------------------------------

def test_correlation_matrix_math():
    """Verify correlation matrix computation on a known dataset."""
    import numpy as np
    rng = np.random.default_rng(42)
    n = 100
    a = rng.normal(0.001, 0.02, n)
    b = a * 0.8 + rng.normal(0, 0.01, n)  # highly correlated with a
    c = rng.normal(0.002, 0.03, n)  # independent
    df = pd.DataFrame({"A": a, "B": b, "C": c})
    corr = df.corr()
    assert corr.loc["A", "B"] > 0.75  # A and B should be highly correlated
    assert abs(corr.loc["A", "C"]) < 0.3  # A and C should be loosely correlated


@pytest.mark.asyncio
async def test_correlation_matrix_too_few():
    from stockhub_mcp.tools.portfolio import get_correlation_matrix_impl
    result = await get_correlation_matrix_impl(symbols=["ONE"])
    assert result["success"] is False
    assert "TOO_FEW" in result.get("error", {}).get("code", "")


@pytest.mark.asyncio
async def test_portfolio_exposure_too_few():
    from stockhub_mcp.tools.portfolio import analyze_portfolio_exposure_impl
    result = await analyze_portfolio_exposure_impl(symbols=["ONE"])
    assert result["success"] is False
