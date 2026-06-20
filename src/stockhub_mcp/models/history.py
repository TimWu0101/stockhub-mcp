"""HistoryData / KLineItem: historical K-line domain models.

Aligned with v0.1-schema.md §4.2.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class KLineItem(BaseModel):
    """Single candlestick (K-line) bar."""

    date: str = Field(..., description="Date string, e.g. '2026-06-15'.")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Highest price.")
    low: float = Field(..., description="Lowest price.")
    close: float = Field(..., description="Closing price.")
    volume: int = Field(..., description="Volume (shares).")
    turnover: float = Field(..., description="Turnover (currency units).")
    change_pct: float = Field(..., description="Percentage change vs previous bar.")


class HistoryData(BaseModel):
    """Historical K-line data response.

    Includes adjustment type (复权) and period/interval metadata.
    """

    symbol: str = Field(..., description="Internal standard symbol.")
    market: str = Field(..., description="Market code: CN / HK / US.")
    period: str = Field(..., description="Requested period, e.g. '1mo'.")
    interval: str = Field(..., description="Bar interval, e.g. '1d'.")
    adjust: str = Field(..., description="Adjustment method: none / qfq / hfq.")
    count: int = Field(..., description="Number of bars returned.")
    history: list[KLineItem] = Field(
        default_factory=list, description="K-line data array."
    )
