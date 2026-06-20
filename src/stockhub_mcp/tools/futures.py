"""V0.2 – Futures tools."""

from __future__ import annotations

from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.models.futures import (
    FuturesContractInfo, FuturesInventoryData, FuturesInventoryItem,
    FuturesPositionRankData, FuturesPositionRankItem,
    FuturesBasisData, FuturesBasisItem,
    FuturesWarehouseReceiptData, FuturesWarehouseReceiptItem,
)


async def search_futures_contract_impl(query: str) -> dict[str, Any]:
    """Search futures contracts."""
    builder = ResponseBuilder()
    try:
        from stockhub_mcp.models.search import SearchResultItem, SearchResponseData
        results: list[SearchResultItem] = []
        # Basic keyword match for known futures contracts
        known: dict[str, str] = {
            "螺纹钢": "RB", "铁矿石": "I", "原油": "SC", "黄金": "AU",
            "铜": "CU", "铝": "AL", "锌": "ZN", "镍": "NI",
            "豆粕": "M", "棕榈油": "P", "白糖": "SR", "棉花": "CF",
            "PTA": "TA", "甲醇": "MA", "玻璃": "FG", "纯碱": "SA",
            "生猪": "LH", "苹果": "AP", "红枣": "CJ", "橡胶": "RU",
        }
        q = query.strip().upper()
        for name, code in known.items():
            if q in name.upper() or q in code.upper():
                results.append(SearchResultItem(
                    symbol=f"CN:{code}",
                    name=name,
                    display_name=f"{name} ({code})",
                    market="CN",
                    instrument_type="future",
                ))
        data = SearchResponseData(results=results)
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "source": "symbol_db", "currency": "CNY",
                  "timezone": "Asia/Shanghai"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "FUTURES_SEARCH_FAILED",
            "type": "source_error",
            "message": f"Futures search failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_futures_contract_info_impl(symbol: str) -> dict[str, Any]:
    """Fetch futures contract info via akshare."""
    builder = ResponseBuilder()
    try:
        import akshare as ak
        df = ak.futures_contract_detail(symbol=symbol.upper())
        if df.empty:
            return builder.error(error={
                "code": "NO_DATA_AVAILABLE", "type": "business_error",
                "message": f"No data for {symbol}", "retryable": False, "details": {},
            })
        row = df.iloc[0]
        data = FuturesContractInfo(
            symbol=f"CN:{symbol}",
            name=str(row.get("variety", "")),
            exchange=str(row.get("exchange", "")),
            contract_size=float(row.get("contract_multiplier", 0) or 0),
            tick_size=float(row.get("tick_size", 0) or 0),
        )
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "source": "akshare", "currency": "CNY",
                  "timezone": "Asia/Shanghai"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "FUTURES_INFO_FAILED",
            "type": "source_error",
            "message": f"Futures info failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_futures_position_rank_impl(symbol: str, date: str = "") -> dict[str, Any]:
    """Fetch futures position rankings via akshare."""
    builder = ResponseBuilder()
    try:
        import akshare as ak
        df = ak.futures_position_rank(symbol=symbol.upper(), date=date or None)
        long_ranks: list[FuturesPositionRankItem] = []
        short_ranks: list[FuturesPositionRankItem] = []
        for _, row in df.iterrows():
            item = FuturesPositionRankItem(
                rank=int(row.get("rank", 0) or 0),
                broker=str(row.get("broker", "")),
                long=int(row.get("long", 0) or 0),
                short=int(row.get("short", 0) or 0),
                net=int(row.get("net", 0) or 0),
                change=int(row.get("change", 0) or 0),
            )
            long_ranks.append(item)
            # Short ranks use same structure
        data = FuturesPositionRankData(
            symbol=f"CN:{symbol}",
            date=date,
            long_ranks=long_ranks[:10],
            short_ranks=short_ranks[:10],
        )
        return builder.success(data=data.model_dump(),
                               meta={"market": "CN", "source": "akshare"})
    except Exception as exc:
        return builder.error(error={
            "code": "FUTURES_POSITION_FAILED",
            "type": "source_error",
            "message": f"Position rank failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_futures_basis_history_impl(symbol: str) -> dict[str, Any]:
    """Fetch futures basis history (spot vs futures spread)."""
    builder = ResponseBuilder()
    try:
        import akshare as ak
        df = ak.futures_spot_price(symbol=symbol.upper())
        items: list[FuturesBasisItem] = []
        for _, row in df.iterrows():
            futures_price = float(row.get("futures_close", 0) or 0)
            spot_price = float(row.get("spot_price", 0) or 0)
            basis = futures_price - spot_price
            items.append(FuturesBasisItem(
                date=str(row.get("date", "")),
                spot=spot_price,
                futures=futures_price,
                basis=basis,
                basis_pct=round(basis / spot_price * 100, 4) if spot_price else 0,
            ))
        data = FuturesBasisData(symbol=f"CN:{symbol}", data=items)
        return builder.success(data=data.model_dump(),
                               meta={"market": "CN", "source": "akshare"})
    except Exception as exc:
        return builder.error(error={
            "code": "FUTURES_BASIS_FAILED",
            "type": "source_error",
            "message": f"Basis history failed: {exc}",
            "retryable": True,
            "details": {},
        })
