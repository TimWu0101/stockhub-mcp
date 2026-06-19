"""V0.2 – Fund models (公募基金)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FundQuoteData(BaseModel):
    """Real-time fund quote."""
    symbol: str = Field(..., description="Internal symbol, e.g. CN:000001")
    name: str = Field(default="", description="Fund display name")
    market: str = Field(default="CN")
    nav: float = Field(default=0.0, description="Latest unit NAV")
    acc_nav: float = Field(default=0.0, description="Accumulated NAV")
    prev_nav: float = Field(default=0.0)
    change: float = Field(default=0.0)
    change_pct: float = Field(default=0.0)
    timestamp: str = Field(default="")
    fund_type: str = Field(default="", description="e.g. 混合型 / 股票型 / 债券型")
    instrument_type: str = Field(default="fund")


class FundNAVItem(BaseModel):
    """Single NAV data point."""
    date: str = ""
    nav: float = 0.0
    acc_nav: float = 0.0
    change_pct: float = 0.0


class FundNAVHistoryData(BaseModel):
    """Historical NAV for a fund."""
    symbol: str = ""
    market: str = "CN"
    period: str = "1mo"
    count: int = 0
    history: list[FundNAVItem] = Field(default_factory=list)


class FundRankingItem(BaseModel):
    """Single ranking entry."""
    rank: int = 0
    symbol: str = ""
    name: str = ""
    nav: float = 0.0
    return_1m: float = 0.0
    return_3m: float = 0.0
    return_6m: float = 0.0
    return_1y: float = 0.0
    fund_type: str = ""


class FundRankingData(BaseModel):
    """Fund ranking response."""
    rankings: list[FundRankingItem] = Field(default_factory=list)
    total: int = 0
