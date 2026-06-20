"""V0.2 – Dragon Tiger, price limits, symbol status, sector constituents."""

from __future__ import annotations

from pydantic import BaseModel, Field


# -- Dragon Tiger ----------------------------------------------------------

class DragonTigerItem(BaseModel):
    date: str = ""
    symbol: str = ""
    name: str = ""
    close: float = 0.0
    change_pct: float = 0.0
    turnover: float = 0.0
    buy_amount: float = 0.0
    sell_amount: float = 0.0
    net_amount: float = 0.0
    reason: str = Field(default="", description="上榜原因")


class DragonTigerData(BaseModel):
    items: list[DragonTigerItem] = Field(default_factory=list)
    count: int = 0


# -- Price Limits ---------------------------------------------------------

class PriceLimitsData(BaseModel):
    symbol: str = ""
    prev_close: float = 0.0
    limit_up: float = 0.0
    limit_down: float = 0.0
    board_type: str = Field(default="main", description="main / gem / star")


# -- Symbol Status ---------------------------------------------------------

class SymbolStatusData(BaseModel):
    symbol: str = ""
    name: str = ""
    status: str = Field(default="normal", description="normal / halted / delisted / suspended")
    reason: str = Field(default="")
    since: str = Field(default="")


# -- Sector Constituents ----------------------------------------------------

class ConstituentItem(BaseModel):
    symbol: str = ""
    name: str = ""
    weight: float = Field(default=0.0, description="Weight in sector index")


class SectorConstituentsData(BaseModel):
    sector_name: str = ""
    sector_code: str = ""
    constituents: list[ConstituentItem] = Field(default_factory=list)
    count: int = 0
