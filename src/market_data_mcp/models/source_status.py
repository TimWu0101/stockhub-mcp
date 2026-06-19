"""SourceHealthItem / SourceStatusData: data-source health domain models.

Aligned with v0.1-schema.md §4.8.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SourceHealthItem(BaseModel):
    """Health status of a single data source."""

    name: str = Field(..., description="Source name: tx / sina / yfinance / eastmoney.")
    status: str = Field(
        ..., description="Status: available / degraded / unavailable."
    )
    market_coverage: list[str] = Field(
        default_factory=list, description="Markets covered by this source."
    )
    last_checked: str = Field(
        ..., description="Last health-check time (ISO 8601)."
    )
    failures_in_window: int = Field(
        0, description="Failure count in the current rolling window."
    )
    degraded_since: Optional[str] = Field(
        None, description="When the source became degraded (ISO 8601), or null."
    )


class SourceStatusData(BaseModel):
    """Response data for source status queries."""

    sources: list[SourceHealthItem] = Field(
        default_factory=list, description="Per-source health entries."
    )
