"""V0.3 – Dividends, holders, analyst forecasts, options, index models."""

from __future__ import annotations

from pydantic import BaseModel, Field


# -- Dividends & Splits ---------------------------------------------------

class DividendItem(BaseModel):
    date: str = ""
    amount: float = 0.0
    ex_date: str = ""


class SplitItem(BaseModel):
    date: str = ""
    ratio: float = Field(default=1.0, description="e.g. 2=2-for-1 split")


class DividendsSplitsData(BaseModel):
    symbol: str = ""
    dividends: list[DividendItem] = Field(default_factory=list)
    splits: list[SplitItem] = Field(default_factory=list)


# -- Holders --------------------------------------------------------------

class HolderItem(BaseModel):
    name: str = ""
    shares: float = 0.0
    pct: float = 0.0


class HoldersData(BaseModel):
    symbol: str = ""
    institutional: list[HolderItem] = Field(default_factory=list)
    insider_pct: float = 0.0
    institutional_pct: float = 0.0


# -- Analyst Forecasts ----------------------------------------------------

class ForecastItem(BaseModel):
    period: str = ""
    revenue_low: float = 0.0
    revenue_avg: float = 0.0
    revenue_high: float = 0.0
    eps_low: float = 0.0
    eps_avg: float = 0.0
    eps_high: float = 0.0
    analysts: int = 0


class AnalystForecastsData(BaseModel):
    symbol: str = ""
    forecasts: list[ForecastItem] = Field(default_factory=list)


# -- Options Chain --------------------------------------------------------

class OptionItem(BaseModel):
    strike: float = 0.0
    expiry: str = ""
    type: str = Field(default="call", description="call / put")
    last: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    volume: int = 0
    open_interest: int = 0
    implied_volatility: float = 0.0


class OptionsChainData(BaseModel):
    symbol: str = ""
    calls: list[OptionItem] = Field(default_factory=list)
    puts: list[OptionItem] = Field(default_factory=list)


# -- Index ----------------------------------------------------------------

class IndexQuoteData(BaseModel):
    symbol: str = ""
    name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    timestamp: str = ""


class IndexCompareItem(BaseModel):
    symbol: str = ""
    name: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    return_1m: float = 0.0
    return_3m: float = 0.0
    return_6m: float = 0.0
    return_1y: float = 0.0


class CompareIndicesData(BaseModel):
    items: list[IndexCompareItem] = Field(default_factory=list)
