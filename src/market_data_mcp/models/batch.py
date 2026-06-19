"""BatchQuoteItem / BatchQuoteData: batch quote domain models.

Aligned with v0.1-schema.md §4.3.
Each quote item carries its own cache metadata.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class BatchQuoteItem(BaseModel):
    """A single quote inside a batch response, with per-symbol cache info."""

    symbol: str = Field(..., description="Internal standard symbol.")
    name: str = Field(..., description="Display name.")
    price: float = Field(..., description="Latest price.")
    change: float = Field(..., description="Price change.")
    change_pct: float = Field(..., description="Percentage change (%).")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Session high.")
    low: float = Field(..., description="Session low.")
    prev_close: float = Field(..., description="Previous close.")
    volume: int = Field(..., description="Volume (shares).")
    turnover: float = Field(..., description="Turnover.")
    timestamp: str = Field(..., description="Quote timestamp (ISO 8601).")
    instrument_type: str = Field(..., description="Instrument type.")
    cache: Optional[dict[str, Any]] = Field(
        None, description="Per-symbol cache metadata."
    )


class BatchSummary(BaseModel):
    """Aggregated statistics for a batch request."""

    requested: int = Field(..., description="Total symbols requested.")
    success: int = Field(..., description="Symbols successfully fetched.")
    failed: int = Field(..., description="Symbols that failed.")


class BatchQuoteData(BaseModel):
    """Response data for batch quote requests."""

    quotes: list[BatchQuoteItem] = Field(
        default_factory=list, description="Successful quotes."
    )
    failed_symbols: list[str] = Field(
        default_factory=list, description="Symbols that could not be resolved."
    )
    summary: BatchSummary = Field(..., description="Aggregated counts.")
