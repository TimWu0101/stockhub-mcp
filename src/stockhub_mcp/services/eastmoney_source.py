"""EastMoneySource: sector boards & capital-flow data via EastMoney API.

Uses EastMoney's public HTTP JSON endpoints for A-share industry/concept
sector data and capital-flow statistics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from stockhub_mcp.config import settings
from stockhub_mcp.enums import Market
from stockhub_mcp.models.quote import QuoteData
from stockhub_mcp.models.history import HistoryData
from stockhub_mcp.models.sector import SectorItem, SectorBoardsData
from stockhub_mcp.models.capital_flow import CapitalFlowData
from stockhub_mcp.services.base import BaseDataSource

logger = logging.getLogger(__name__)

# EastMoney API endpoints
_EM_SECTOR_URL = (
    "https://push2.eastmoney.com/api/qt/clist/get"
    "?pn=1&pz=50&po=1&np=1&fltt=2&invt=2"
    "&fid=f3&fs=m:90+t:{board_type}"
    "&fields=f2,f3,f4,f12,f14,f128,f140"
)

_EM_CAPITAL_FLOW_URL = (
    "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get"
    "?lmt=1&secid={secid}"
    "&fields=f1,f2,f3,f4,f5,f6,f7"
)

# Board type mapping
_BOARD_TYPES: dict[str, str] = {
    "industry": "2",   # 行业板块
    "concept": "3",    # 概念板块
}

# Capital flow secid for market-level (上证 1.000001, 深证 0.399001)
_CAPITAL_FLOW_MARKET_SECID = "1.000001"


class EastMoneySource(BaseDataSource):
    """EastMoney data source for A-share sectors and capital flow.

    Does NOT provide individual stock quotes or history.
    """

    SUPPORTED_MARKETS: frozenset[Market] = frozenset([Market.CN])

    @property
    def name(self) -> str:
        return "eastmoney"

    # ------------------------------------------------------------------
    # BaseDataSource interface
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """EastMoney API is always available (no library dependency)."""
        return True

    def fetch_quote(
        self,
        symbol: str,
        market: Market,
        *,
        bypass_cache: bool = False,
    ) -> QuoteData:
        """EastMoney does not provide individual stock quotes."""
        raise NotImplementedError(
            "EastMoney source does not provide individual stock quotes. "
            "Use Tencent or Sina for CN quotes."
        )

    def fetch_history(
        self,
        symbol: str,
        market: Market,
        period: str = "1mo",
        interval: str = "1d",
        *,
        adjust: str = "qfq",
    ) -> HistoryData:
        """EastMoney does not provide historical K-line data."""
        raise NotImplementedError(
            "EastMoney source does not provide historical K-line data."
        )

    # ------------------------------------------------------------------
    # Sector boards
    # ------------------------------------------------------------------

    def fetch_sector_boards(self, board_type: str = "industry") -> SectorBoardsData:
        """Fetch A-share industry or concept sector/board list.

        Args:
            board_type: ``"industry"`` or ``"concept"``.

        Returns:
            ``SectorBoardsData`` with up to 50 entries.
        """
        board_code = _BOARD_TYPES.get(board_type, "2")
        url = _EM_SECTOR_URL.format(board_type=board_code)

        logger.debug("EastMoney fetch_sector_boards: type=%s", board_type)

        try:
            data = self._sync_get_json(url)
            sectors: list[SectorItem] = []

            items = data.get("data", {}).get("diff", [])
            if not items:
                logger.warning("EastMoney returned empty sector list")

            for item in items:
                sectors.append(SectorItem(
                    code=str(item.get("f12", "")),
                    name=str(item.get("f14", "")),
                    type=board_type,
                    change_pct=self._safe_float(item.get("f3", 0)),
                    leading_stock="CN:" + str(item.get("f128", "")),
                    leading_stock_name=str(item.get("f140", "")),
                    leading_stock_change_pct=self._safe_float(item.get("f4", 0)) / 100,
                    stock_count=int(self._safe_float(item.get("f2", 0))),
                ))

            return SectorBoardsData(sectors=sectors)

        except httpx.HTTPError as exc:
            logger.error("EastMoney sector fetch error: %s", exc)
            raise RuntimeError(f"EastMoney sector fetch failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Capital flow
    # ------------------------------------------------------------------

    def fetch_capital_flow(self, scope: str = "market") -> CapitalFlowData:
        """Fetch A-share capital flow data.

        Args:
            scope: ``"market"`` (market-level) or ``"sector"``.

        Returns:
            ``CapitalFlowData`` instance.
        """
        secid = _CAPITAL_FLOW_MARKET_SECID
        url = _EM_CAPITAL_FLOW_URL.format(secid=secid)

        logger.debug("EastMoney fetch_capital_flow: scope=%s", scope)

        try:
            data = self._sync_get_json(url)
            klines = (data.get("data") or {}).get("klines", [])

            if not klines:
                logger.warning("EastMoney returned empty capital flow data")
                return CapitalFlowData(
                    scope=scope,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    main_net_inflow=0.0,
                    super_large_net_inflow=0.0,
                    large_net_inflow=0.0,
                    medium_net_inflow=0.0,
                    small_net_inflow=0.0,
                )

            # Kline format: "date,main_net,super_large,large,medium,small"
            latest = klines[-1] if isinstance(klines[-1], str) else ""
            parts = latest.split(",") if latest else []

            return CapitalFlowData(
                scope=scope,
                timestamp=datetime.now(timezone.utc).isoformat(),
                main_net_inflow=self._safe_float(_get(parts, 1)),
                super_large_net_inflow=self._safe_float(_get(parts, 4)),
                large_net_inflow=self._safe_float(_get(parts, 3)),
                medium_net_inflow=self._safe_float(_get(parts, 2)),
                small_net_inflow=self._safe_float(_get(parts, 5)),
            )

        except httpx.HTTPError as exc:
            logger.error("EastMoney capital-flow fetch error: %s", exc)
            raise RuntimeError(f"EastMoney capital-flow fetch failed: {exc}") from exc

    # ------------------------------------------------------------------
    # V0.2  Northbound / Southbound flow
    # ------------------------------------------------------------------

    def fetch_northbound_flow(self, days: int = 20) -> "NorthboundFlowData":
        """Fetch northbound capital flow history."""
        from stockhub_mcp.models.flow import NorthboundFlowData, FlowDataPoint

        url = (
            "https://push2his.eastmoney.com/api/qt/kamt.kline/get"
            "?fields1=f1,f2,f3,f4&fields2=f51,f52"
            "&klt=101&lmt={days}&ut=b2884a393a59ad64002192a3e90d46a5"
        ).format(days=days)

        data = self._sync_get_json(url)
        klines = (data.get("data") or {}).get("klines", [])
        points: list[FlowDataPoint] = []
        for line in klines:
            parts = line.split(",") if isinstance(line, str) else []
            if len(parts) >= 2:
                points.append(FlowDataPoint(
                    date=parts[0],
                    net_inflow=self._safe_float(parts[1]) / 10000,  # 万元→亿元
                ))
        return NorthboundFlowData(
            flow_type="northbound",
            data=points,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    def fetch_southbound_flow(self, days: int = 20) -> "NorthboundFlowData":
        """Fetch southbound (港股通) capital flow history."""
        from stockhub_mcp.models.flow import NorthboundFlowData, FlowDataPoint

        url = (
            "https://push2his.eastmoney.com/api/qt/kamt.kline/get"
            "?fields1=f1,f2,f3,f4&fields2=f51,f52"
            "&klt=103&lmt={days}&ut=b2884a393a59ad64002192a3e90d46a5"
        ).format(days=days)

        data = self._sync_get_json(url)
        klines = (data.get("data") or {}).get("klines", [])
        points: list[FlowDataPoint] = []
        for line in klines:
            parts = line.split(",") if isinstance(line, str) else []
            if len(parts) >= 2:
                points.append(FlowDataPoint(
                    date=parts[0],
                    net_inflow=self._safe_float(parts[1]) / 10000,
                ))
        return NorthboundFlowData(
            flow_type="southbound",
            data=points,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # V0.2  Dragon Tiger
    # ------------------------------------------------------------------

    def fetch_dragon_tiger_list(self) -> "DragonTigerData":
        """Fetch today's dragon-tiger list."""
        from stockhub_mcp.models.enhance import DragonTigerData, DragonTigerItem

        url = (
            "https://push2.eastmoney.com/api/qt/clist/get"
            "?fid=f62&po=1&pz=50&pn=1&np=1&fltt=2&invt=2"
            "&fs=m:90+t:3&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205"
        )
        data = self._sync_get_json(url)
        items_raw = (data.get("data") or {}).get("diff", [])
        items: list[DragonTigerItem] = []
        for it in items_raw:
            items.append(DragonTigerItem(
                date=str(it.get("f204", "")),
                symbol="CN:" + str(it.get("f12", "")),
                name=str(it.get("f14", "")),
                close=self._safe_float(it.get("f2", 0)),
                change_pct=self._safe_float(it.get("f3", 0)),
                turnover=self._safe_float(it.get("f62", 0)),
                buy_amount=self._safe_float(it.get("f66", 0)) / 10000,
                sell_amount=self._safe_float(it.get("f72", 0)) / 10000,
                net_amount=self._safe_float(it.get("f184", 0)) / 10000,
                reason=str(it.get("f205", "")),
            ))
        return DragonTigerData(items=items, count=len(items))

    # ------------------------------------------------------------------
    # V0.2  Sector Constituents
    # ------------------------------------------------------------------

    def fetch_sector_constituents(self, sector_code: str) -> "SectorConstituentsData":
        """Fetch stocks in a sector/industry board."""
        from stockhub_mcp.models.enhance import SectorConstituentsData, ConstituentItem

        url = (
            "https://push2.eastmoney.com/api/qt/clist/get"
            f"?fid=f3&po=1&pz=200&pn=1&np=1&fltt=2&invt=2"
            f"&fs=b:{sector_code}&fields=f12,f14,f3,f20"
        )
        data = self._sync_get_json(url)
        items_raw = (data.get("data") or {}).get("diff", [])
        items: list[ConstituentItem] = []
        for it in items_raw:
            items.append(ConstituentItem(
                symbol="CN:" + str(it.get("f12", "")),
                name=str(it.get("f14", "")),
                weight=self._safe_float(it.get("f20", 0)) / 100,
            ))
        return SectorConstituentsData(
            sector_name="",
            sector_code=sector_code,
            constituents=items,
            count=len(items),
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    @staticmethod
    def _sync_get_json(url: str, timeout: Optional[int] = None) -> dict[str, Any]:
        """Perform a synchronous HTTP GET and parse JSON."""
        timeout_val = timeout or settings.request_timeout
        headers = {
            "Referer": "https://quote.eastmoney.com/",
        }
        with httpx.Client(timeout=timeout_val, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


def _get(lst: list[str], idx: int, default: str = "0") -> str:
    try:
        return lst[idx]
    except IndexError:
        return default
