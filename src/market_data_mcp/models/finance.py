"""V0.3 – Financial statements & valuation models."""

from __future__ import annotations

from pydantic import BaseModel, Field


# -- Financial Statements -------------------------------------------------

class IncomeStatement(BaseModel):
    date: str = ""
    revenue: float = 0.0
    operating_income: float = 0.0
    net_income: float = 0.0
    eps: float = 0.0
    diluted_eps: float = 0.0


class BalanceSheet(BaseModel):
    date: str = ""
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    total_equity: float = 0.0
    cash: float = 0.0
    debt: float = 0.0


class CashFlow(BaseModel):
    date: str = ""
    operating_cf: float = 0.0
    investing_cf: float = 0.0
    financing_cf: float = 0.0
    free_cash_flow: float = 0.0


class FinancialStatementsData(BaseModel):
    symbol: str = ""
    name: str = ""
    market: str = ""
    currency: str = ""
    income: list[IncomeStatement] = Field(default_factory=list)
    balance: list[BalanceSheet] = Field(default_factory=list)
    cash_flow: list[CashFlow] = Field(default_factory=list)


# -- Valuation ------------------------------------------------------------

class ValuationMetricsData(BaseModel):
    symbol: str = ""
    name: str = ""
    market: str = ""
    pe_ttm: float = 0.0
    pe_forward: float = 0.0
    pb: float = 0.0
    ps_ttm: float = 0.0
    peg: float = 0.0
    ev_ebitda: float = 0.0
    market_cap: float = 0.0
    enterprise_value: float = 0.0
    dividend_yield: float = 0.0
    timestamp: str = ""


class ValuationPercentileData(BaseModel):
    symbol: str = ""
    metric: str = Field(..., description="pe / pb / ps")
    current: float = 0.0
    p5: float = 0.0
    p25: float = 0.0
    median: float = 0.0
    p75: float = 0.0
    p95: float = 0.0
    percentile: float = Field(default=0.0, description="Current value's position (0-100)")


class QualityMetricsData(BaseModel):
    symbol: str = ""
    roe: float = 0.0
    roa: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    debt_to_equity: float = 0.0
    current_ratio: float = 0.0
    revenue_growth: float = 0.0
    earnings_growth: float = 0.0
    timestamp: str = ""


# -- Comparison -----------------------------------------------------------

class CompareItem(BaseModel):
    symbol: str = ""
    name: str = ""
    pe_ttm: float = 0.0
    pb: float = 0.0
    market_cap: float = 0.0
    dividend_yield: float = 0.0
    revenue_growth: float = 0.0
    roe: float = 0.0


class CompareStocksData(BaseModel):
    items: list[CompareItem] = Field(default_factory=list)
    metric_timestamp: str = ""
