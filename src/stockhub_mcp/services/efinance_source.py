"""EfinanceSource: A-share data via efinance (东方财富 Python SDK).

Zero-config, zero-key, free.  Wraps ``efinance`` to provide sector boards,
sector constituents, dragon-tiger list, and capital flow — replacing the
fragile raw-HTTP eastmoney_source for these capabilities.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from stockhub_mcp.enums import Market
from stockhub_mcp.models.quote import QuoteData
from stockhub_mcp.models.history import HistoryData
from stockhub_mcp.models.capital_flow import CapitalFlowData
from stockhub_mcp.models.sector import SectorBoardsData, SectorItem
from stockhub_mcp.models.enhance import (
    DragonTigerData, DragonTigerItem,
    SectorConstituentsData, ConstituentItem,
)
from stockhub_mcp.models.flow import NorthboundFlowData, FlowDataPoint
from stockhub_mcp.services.base import BaseDataSource

logger = logging.getLogger(__name__)


class EfinanceSource(BaseDataSource):
    """efinance-based data source for CN markets.

    Replaces raw eastmoney HTTP calls with a dedicated Python SDK.
    All methods are synchronous (efinance is sync-only).
    """

    SUPPORTED_MARKETS: frozenset[Market] = frozenset([Market.CN])

    # ------------------------------------------------------------------
    # BaseDataSource interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "efinance"

    def available(self) -> bool:
        return self._check_import("efinance")

    def fetch_quote(self, symbol: str, market: Market, *, bypass_cache: bool = False) -> QuoteData:
        raise NotImplementedError("EfinanceSource does not provide individual quotes – use Tencent/Sina")

    def fetch_history(
        self, symbol: str, market: Market,
        period: str = "1mo", interval: str = "1d", *, adjust: str = "qfq",
    ) -> HistoryData:
        raise NotImplementedError("EfinanceSource does not provide K-line history – use yfinance/Tencent")

    # ------------------------------------------------------------------
    # Sector boards
    # ------------------------------------------------------------------

    def fetch_sector_boards(self, board_type: str = "industry") -> SectorBoardsData:
        """Fetch A-share sector (industry/concept) rankings via efinance.

        Note: efinance does not offer a dedicated sector-ranking endpoint.
        This method raises NotImplementedError so callers fall through to
        the EastMoney HTTP source.
        """
        raise NotImplementedError("efinance does not support sector boards; use eastmoney")

    # ------------------------------------------------------------------
    # Dragon Tiger
    # ------------------------------------------------------------------

    def fetch_dragon_tiger_list(self) -> DragonTigerData:
        """Fetch today's dragon-tiger list via efinance."""
        import efinance as ef

        try:
            df = ef.stock.get_daily_billboard()
        except Exception as exc:
            logger.error("Efinance dragon-tiger failed: %s", exc)
            raise RuntimeError(f"Dragon tiger fetch failed: {exc}") from exc

        items: list[DragonTigerItem] = []
        for _, row in df.iterrows():
            try:
                # efinance columns: 代码, 名称, 收盘价, 涨跌幅, 成交额,
                # 龙虎榜净买额, 龙虎榜买入额, 龙虎榜卖出额, 上榜原因, 日期
                items.append(DragonTigerItem(
                    date=str(row.get("日期", row.get("时间", ""))),
                    symbol="CN:" + str(row.get("代码", row.get("股票代码", ""))),
                    name=str(row.get("名称", row.get("股票名称", ""))),
                    close=self._sf(row.get("收盘价", row.get("最新价", 0))),
                    change_pct=self._sf(row.get("涨跌幅", 0)),
                    turnover=self._sf(row.get("成交额", 0)),
                    buy_amount=self._sf(row.get("龙虎榜买入额", row.get("买入金额", 0))),
                    sell_amount=self._sf(row.get("龙虎榜卖出额", row.get("卖出金额", 0))),
                    net_amount=self._sf(row.get("龙虎榜净买额", row.get("净买额", 0))),
                    reason=str(row.get("上榜原因", row.get("上榜理由", ""))),
                ))
            except Exception:
                continue

        return DragonTigerData(items=items, count=len(items))

    # ------------------------------------------------------------------
    # Sector Constituents
    # ------------------------------------------------------------------

    def fetch_sector_constituents(self, sector_code: str) -> SectorConstituentsData:
        """Not supported by efinance – use eastmoney fallback."""
        raise NotImplementedError("efinance does not support sector constituents; use eastmoney")

    # ------------------------------------------------------------------
    # Capital Flow
    # ------------------------------------------------------------------

    def fetch_capital_flow(self, scope: str = "market") -> CapitalFlowData:
        """Fetch A-share capital flow via efinance."""
        import efinance as ef

        try:
            df = ef.stock.get_history_billboard()
            if df.empty:
                return CapitalFlowData(
                    scope=scope,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    main_net_inflow=0.0, super_large_net_inflow=0.0,
                    large_net_inflow=0.0, medium_net_inflow=0.0,
                    small_net_inflow=0.0,
                )

            latest = df.iloc[-1]
            return CapitalFlowData(
                scope=scope,
                timestamp=datetime.now(timezone.utc).isoformat(),
                main_net_inflow=self._sf(latest.get("主力净流入", latest.get("主力净流入-净额", 0))),
                super_large_net_inflow=self._sf(latest.get("超大单净流入", 0)),
                large_net_inflow=self._sf(latest.get("大单净流入", 0)),
                medium_net_inflow=self._sf(latest.get("中单净流入", 0)),
                small_net_inflow=self._sf(latest.get("小单净流入", 0)),
            )
        except Exception as exc:
            logger.error("Efinance capital-flow failed: %s", exc)
            raise RuntimeError(f"Capital flow failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Northbound / Southbound
    # ------------------------------------------------------------------

    def fetch_northbound_flow(self, days: int = 20) -> NorthboundFlowData:
        """Fetch northbound capital flow history via efinance."""
        import efinance as ef

        try:
            df = ef.stock.get_history_billboard()
        except Exception as exc:
            logger.error("Efinance northbound failed: %s", exc)
            raise RuntimeError(f"Northbound flow failed: {exc}") from exc

        points: list[FlowDataPoint] = []
        for _, row in df.tail(days).iterrows():
            points.append(FlowDataPoint(
                date=str(row.get("日期", "")),
                net_inflow=self._sf(row.get("主力净流入-净额", 0)) / 100000000,  # 元→亿元
            ))

        return NorthboundFlowData(
            flow_type="northbound",
            data=points,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sf(value, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _check_import(module: str) -> bool:
        try:
            __import__(module)
            return True
        except ImportError:
            logger.debug("efinance not installed – efinance source unavailable")
            return False
