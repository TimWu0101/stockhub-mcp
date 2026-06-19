"""SearchResultItem / SearchResponseData: symbol search domain models.

Aligned with v0.1-schema.md §4.7.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Single symbol-search hit."""

    symbol: str = Field(..., description="Internal standard symbol, e.g. 'CN:600519'.")
    name: str = Field(..., description="Instrument name.")
    display_name: str = Field(
        ..., description="Human-readable display name, e.g. '贵州茅台 (600519)'."
    )
    market: str = Field(..., description="Market code: CN / HK / US.")
    exchange: str = Field(default="", description="Exchange, e.g. 'SSE', 'NYSE'.")
    instrument_type: str = Field(
        default="stock", description="Instrument type: stock / etf / index / fund."
    )
    currency: str = Field(default="", description="ISO 4217 currency code.")


class SearchResponseData(BaseModel):
    """Response data for symbol search."""

    results: list[SearchResultItem] = Field(
        default_factory=list, description="Ordered search results."
    )
