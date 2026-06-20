"""V0.2 – Fund data tools."""

from __future__ import annotations

from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.models.fund import (
    FundQuoteData, FundNAVItem, FundNAVHistoryData, FundRankingData, FundRankingItem,
)


async def get_fund_quote_impl(fund_code: str) -> dict[str, Any]:
    """Fetch real-time fund NAV quote via eastmoney public API."""
    builder = ResponseBuilder()

    try:
        import httpx
        url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        raw = resp.text
        # jsonpgz({"fundcode":"000001","name":"...","jzrq":"...","dwjz":"...","gsz":"...","gszzl":"...","gztime":"..."})
        import json
        start = raw.find("{")
        end = raw.rfind("}") + 1
        obj = json.loads(raw[start:end])

        data = FundQuoteData(
            symbol=f"CN:{fund_code}",
            name=obj.get("name", ""),
            nav=float(obj.get("dwjz", 0) or 0),
            acc_nav=0.0,
            prev_nav=float(obj.get("dwjz", 0) or 0),
            change=0.0,
            change_pct=float(obj.get("gszzl", 0) or 0),
            timestamp=obj.get("gztime", "") or obj.get("jzrq", ""),
        )
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "symbol": f"CN:{fund_code}", "source": "eastmoney",
                  "currency": "CNY", "timezone": "Asia/Shanghai", "market_session": "",
                  "is_realtime": False, "data_delay_seconds": 0, "quality_flag": "live"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "FUND_FETCH_FAILED",
            "type": "source_error",
            "message": f"Fund quote fetch failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_fund_nav_history_impl(
    fund_code: str,
    period: str = "1mo",
) -> dict[str, Any]:
    """Fetch fund NAV history via eastmoney API."""
    builder = ResponseBuilder()

    import datetime
    today = datetime.date.today()
    if period == "1mo":
        start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    elif period == "3mo":
        start_date = (today - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    elif period == "6mo":
        start_date = (today - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    elif period == "1y":
        start_date = (today - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    else:
        start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    end_date = today.strftime("%Y-%m-%d")

    try:
        import httpx
        url = (
            f"https://api.fund.eastmoney.com/f10/lsjz"
            f"?fundCode={fund_code}&pageIndex=1&pageSize=200"
            f"&startDate={start_date}&endDate={end_date}"
        )
        resp = httpx.get(url, headers={"Referer": "https://fund.eastmoney.com/"}, timeout=10)
        resp.raise_for_status()
        obj = resp.json()
        items = obj.get("Data", {}).get("LSJZList", [])

        history: list[FundNAVItem] = []
        for it in items:
            history.append(FundNAVItem(
                date=it.get("FSRQ", ""),
                nav=float(it.get("DWJZ", 0) or 0),
                acc_nav=float(it.get("LJJZ", 0) or 0),
                change_pct=float(it.get("JZZZL", 0) or 0),
            ))

        data = FundNAVHistoryData(
            symbol=f"CN:{fund_code}",
            period=period,
            count=len(history),
            history=history,
        )
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "symbol": f"CN:{fund_code}", "source": "eastmoney",
                  "currency": "CNY", "timezone": "Asia/Shanghai"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "FUND_HISTORY_FAILED",
            "type": "source_error",
            "message": f"Fund NAV history failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def get_fund_rankings_impl(
    fund_type: str = "all",
    sort_by: str = "1y",
    max_results: int = 20,
) -> dict[str, Any]:
    """Fetch fund rankings from eastmoney."""
    builder = ResponseBuilder()

    type_map = {"all": "all", "stock": "gp", "mixed": "hh", "bond": "zq", "index": "zs"}
    sort_map = {"1m": "1m", "3m": "3m", "6m": "6m", "1y": "1y"}

    try:
        import httpx
        url = (
            "https://fund.eastmoney.com/data/rankhandler.aspx"
            f"?op=ph&dt=kf&ft={type_map.get(fund_type, 'all')}"
            f"&rs=&gs=0&sc=1nzf&st=desc"
            f"&pi=1&pn={max_results}&v=0.1"
        )
        resp = httpx.get(url, headers={"Referer": "https://fund.eastmoney.com/"}, timeout=10)
        resp.raise_for_status()
        raw = resp.text
        import re, json
        match = re.search(r"\[.*\]", raw)
        items: list[FundRankingItem] = []
        if match:
            arr = json.loads(match.group())
            for idx, entry in enumerate(arr):
                parts = entry.split(",")
                if len(parts) >= 12:
                    items.append(FundRankingItem(
                        rank=idx + 1,
                        symbol=f"CN:{parts[1]}",
                        name=parts[2],
                        nav=float(parts[4] or 0),
                        return_1m=float(parts[6] or 0),
                        return_3m=float(parts[8] or 0),
                        return_6m=float(parts[10] or 0),
                        return_1y=float(parts[7] or 0),
                    ))

        data = FundRankingData(rankings=items, total=len(items))
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "source": "eastmoney", "currency": "CNY",
                  "timezone": "Asia/Shanghai"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "FUND_RANKING_FAILED",
            "type": "source_error",
            "message": f"Fund ranking failed: {exc}",
            "retryable": True,
            "details": {},
        })


async def search_fund_impl(query: str, max_results: int = 10) -> dict[str, Any]:
    """Search for funds by name/code."""
    builder = ResponseBuilder()
    try:
        import httpx
        url = f"https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key={query}"
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        obj = resp.json()
        datas = obj.get("Datas", [])

        from stockhub_mcp.models.search import SearchResultItem, SearchResponseData
        results: list[SearchResultItem] = []
        for it in datas[:max_results]:
            results.append(SearchResultItem(
                symbol=f"CN:{it.get('CODE', '')}",
                name=it.get("NAME", ""),
                display_name=f"{it.get('NAME', '')} ({it.get('CODE', '')})",
                market="CN",
                instrument_type="fund",
            ))

        data = SearchResponseData(results=results)
        return builder.success(
            data=data.model_dump(),
            meta={"market": "CN", "source": "eastmoney", "currency": "CNY",
                  "timezone": "Asia/Shanghai"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "FUND_SEARCH_FAILED",
            "type": "source_error",
            "message": f"Fund search failed: {exc}",
            "retryable": True,
            "details": {},
        })
