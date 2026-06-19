"""V0.2 – ETF models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ETFQuoteData(BaseModel):
    """Real-time ETF quote (trading perspective)."""
    symbol: str = Field(..., description="Internal symbol")
    name: str = ""
    market: str = "CN"
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    prev_close: float = 0.0
    volume: int = 0
    turnover: float = 0.0
    timestamp: str = ""
    instrument_type: str = "etf"


class ETFInfoData(BaseModel):
    """ETF metadata."""
    symbol: str = ""
    name: str = ""
    tracking_index: str = Field(default="", description="Underlying index")
    tracking_index_code: str = Field(default="")
    management_fee: float = 0.0
    inception_date: str = ""
    fund_size: float = Field(default=0.0, description="Fund size in CNY")
    industry_tags: list[str] = Field(default_factory=list)
    is_margin: bool = False
