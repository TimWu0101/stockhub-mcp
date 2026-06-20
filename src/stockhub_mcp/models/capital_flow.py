"""CapitalFlowData: market-level capital flow domain model.

Aligned with v0.1-schema.md §4.6.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CapitalFlowData(BaseModel):
    """Market or sector-level capital flow data.

    Covers main net inflow broken down by order size category.
    """

    scope: str = Field(..., description="Scope: 'market' or 'sector'.")
    timestamp: str = Field(..., description="Data timestamp (ISO 8601).")
    main_net_inflow: float = Field(..., description="Main net inflow (currency units).")
    super_large_net_inflow: float = Field(
        ..., description="Super-large orders net inflow."
    )
    large_net_inflow: float = Field(..., description="Large orders net inflow.")
    medium_net_inflow: float = Field(..., description="Medium orders net inflow.")
    small_net_inflow: float = Field(..., description="Small orders net inflow.")
