"""V0.2 – Capital flow tools (northbound, southbound)."""

from __future__ import annotations

import logging
from typing import Any

from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.services.eastmoney_source import EastMoneySource

logger = logging.getLogger(__name__)


def _get_efinance():
    try:
        from stockhub_mcp.services.efinance_source import EfinanceSource
        src = EfinanceSource()
        if src.available():
            return src
    except Exception:
        pass
    return None


async def get_northbound_flow_impl(days: int = 20) -> dict[str, Any]:
    """Fetch northbound (沪深股通) flow."""
    builder = ResponseBuilder()

    efinance = _get_efinance()
    if efinance:
        try:
            data = efinance.fetch_northbound_flow(days=days)
            return builder.success(data=data.model_dump(), meta={
                "market": "CN", "source": "efinance", "currency": "CNY",
                "timezone": "Asia/Shanghai", "market_session": "", "is_realtime": False,
                "data_delay_seconds": 0, "quality_flag": "live",
            })
        except Exception as exc:
            logger.warning("Efinance northbound failed: %s", exc)

    try:
        src = EastMoneySource()
        data = src.fetch_northbound_flow(days=days)
        return builder.success(data=data.model_dump(), meta={
            "market": "CN", "source": "eastmoney", "currency": "CNY",
            "timezone": "Asia/Shanghai", "market_session": "", "is_realtime": False,
            "data_delay_seconds": 0, "quality_flag": "live",
        })
    except Exception as exc:
        return builder.error(error={
            "code": "NORTHBOUND_FAILED", "type": "source_error",
            "message": f"Northbound flow failed: {exc}", "retryable": True, "details": {},
        })


async def get_southbound_flow_impl(days: int = 20) -> dict[str, Any]:
    """Fetch southbound (港股通) flow."""
    builder = ResponseBuilder()
    try:
        src = EastMoneySource()
        data = src.fetch_southbound_flow(days=days)
        return builder.success(
            data=data.model_dump(),
            meta={"market": "HK", "source": "eastmoney", "currency": "CNY",
                  "timezone": "Asia/Hong_Kong", "market_session": "", "is_realtime": False,
                  "data_delay_seconds": 0, "quality_flag": "live"},
        )
    except Exception as exc:
        return builder.error(error={
            "code": "SOUTHBOUND_FAILED", "type": "source_error",
            "message": f"Southbound flow failed: {exc}", "retryable": True, "details": {},
        })
