"""V0.2 – Futures models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FuturesContractInfo(BaseModel):
    symbol: str = ""
    name: str = ""
    exchange: str = ""
    contract_size: float = 0.0
    tick_size: float = 0.0
    delivery_month: str = ""
    last_trade_date: str = ""


class FuturesInventoryItem(BaseModel):
    date: str = ""
    warehouse: str = ""
    quantity: float = 0.0
    change: float = 0.0


class FuturesInventoryData(BaseModel):
    symbol: str = ""
    name: str = ""
    data: list[FuturesInventoryItem] = Field(default_factory=list)


class FuturesPositionRankItem(BaseModel):
    rank: int = 0
    broker: str = ""
    long: int = 0
    short: int = 0
    net: int = 0
    change: int = 0


class FuturesPositionRankData(BaseModel):
    symbol: str = ""
    date: str = ""
    long_ranks: list[FuturesPositionRankItem] = Field(default_factory=list)
    short_ranks: list[FuturesPositionRankItem] = Field(default_factory=list)


class FuturesBasisItem(BaseModel):
    date: str = ""
    spot: float = 0.0
    futures: float = 0.0
    basis: float = 0.0
    basis_pct: float = 0.0


class FuturesBasisData(BaseModel):
    symbol: str = ""
    data: list[FuturesBasisItem] = Field(default_factory=list)


class FuturesWarehouseReceiptItem(BaseModel):
    date: str = ""
    quantity: float = 0.0
    change: float = 0.0


class FuturesWarehouseReceiptData(BaseModel):
    symbol: str = ""
    data: list[FuturesWarehouseReceiptItem] = Field(default_factory=list)
