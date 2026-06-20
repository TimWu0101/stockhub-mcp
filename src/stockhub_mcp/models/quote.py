"""QuoteData: single-instrument real-time quote domain model.

Aligned with v0.1-schema.md §4.1.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuoteData(BaseModel):
    """Single-instrument real-time quote.

    All price/volume fields follow the unified V0.1 schema.
    """

    symbol: str = Field(
        ..., description="Internal standard symbol, e.g. 'CN:600519'."
    )
    name: str = Field(..., description="Display name of the instrument.")
    market: str = Field(..., description="Market code: CN / HK / US.")
    price: float = Field(..., description="Latest price.")
    change: float = Field(..., description="Price change from previous close.")
    change_pct: float = Field(..., description="Percentage change (%).")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Session high.")
    low: float = Field(..., description="Session low.")
    prev_close: float = Field(..., description="Previous close price.")
    volume: int = Field(..., description="Trading volume (shares).")
    turnover: float = Field(..., description="Trading turnover (currency units).")
    timestamp: str = Field(..., description="Quote timestamp (ISO 8601).")
    instrument_type: str = Field(
        ..., description="Instrument type: stock / index / etf."
    )
