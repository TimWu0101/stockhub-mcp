"""V0.2 – Northbound / Southbound flow models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FlowDataPoint(BaseModel):
    """Single daily flow data point."""
    date: str = ""
    net_inflow: float = 0.0


class NorthboundFlowData(BaseModel):
    """Northbound (沪股通+深股通) capital flow response."""
    flow_type: str = Field(default="northbound", description="northbound / southbound")
    data: list[FlowDataPoint] = Field(default_factory=list)
    last_updated: str = ""
