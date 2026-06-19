"""SectorItem / SectorBoardsData: sector/industry board domain models.

Aligned with v0.1-schema.md §4.5.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SectorItem(BaseModel):
    """Single sector / concept board entry."""

    code: str = Field(..., description="Sector code, e.g. 'BK0001'.")
    name: str = Field(..., description="Sector display name.")
    type: str = Field(..., description="Board type: industry / concept.")
    change_pct: float = Field(..., description="Sector average change (%).")
    leading_stock: str = Field(
        ..., description="Internal standard symbol of the leading stock."
    )
    leading_stock_name: str = Field(..., description="Display name of the leading stock.")
    leading_stock_change_pct: float = Field(
        ..., description="Leading stock change (%)."
    )
    stock_count: int = Field(..., description="Number of constituent stocks.")


class SectorBoardsData(BaseModel):
    """Response data for sector/board queries."""

    sectors: list[SectorItem] = Field(
        default_factory=list, description="Ordered list of sector entries."
    )
