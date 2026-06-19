"""get_batch_quotes tool implementation.

Fetches up to 20 symbols concurrently.  Each symbol is independently
resolved and fetched; partial failures are reported via
``failed_symbols`` and warnings.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from market_data_mcp.config import settings
from market_data_mcp.domain.response_builder import ResponseBuilder
from market_data_mcp.domain.symbol.resolver import SymbolResolver, ResolveResult, StandardSymbol
from market_data_mcp.enums import Market, QualityFlag
from market_data_mcp.tools.quote import get_realtime_quote_impl

logger = logging.getLogger(__name__)

# Maximum batch size
_MAX_BATCH_SIZE = 20


# ------------------------------------------------------------------
# Tool implementation
# ------------------------------------------------------------------


async def get_batch_quotes_impl(
    symbols: list[str],
    bypass_cache: bool = False,
) -> dict[str, Any]:
    """Batch query real-time quotes for multiple symbols.

    Args:
        symbols: List of user-input symbols (codes or names, max 20).
        bypass_cache: If True, skip cache for all symbols.

    Returns:
        Partial-success structure with ``quotes`` and ``failed_symbols``.
    """
    builder = ResponseBuilder()

    # --- Validation ---
    if not symbols:
        return builder.error(
            error={
                "code": "EMPTY_SYMBOLS",
                "type": "input_error",
                "message": "Symbols list must not be empty.",
                "retryable": False,
                "details": {},
            },
        )

    if len(symbols) > _MAX_BATCH_SIZE:
        return builder.error(
            error={
                "code": "TOO_MANY_SYMBOLS",
                "type": "input_error",
                "message": f"Maximum {_MAX_BATCH_SIZE} symbols per batch, got {len(symbols)}.",
                "retryable": False,
                "details": {"max": _MAX_BATCH_SIZE, "got": len(symbols)},
            },
        )

    # --- Step 1: Resolve all symbols first (synchronous, fast) ---
    resolver = SymbolResolver()
    resolved: list[tuple[str, StandardSymbol]] = []  # (original_input, std_symbol)
    failed_inputs: list[str] = []

    for raw in symbols:
        raw = raw.strip()
        if not raw:
            failed_inputs.append(raw)
            continue

        result = resolver.resolve(raw)
        if result.resolved and result.symbol:
            resolved.append((raw, result.symbol))
        else:
            failed_inputs.append(raw)

    # --- Step 2: Concurrent fetch ---
    async def _fetch_one(original: str, std: StandardSymbol) -> dict[str, Any]:
        """Fetch a single quote, always returning a dict."""
        try:
            return await get_realtime_quote_impl(
                symbol=original,
                market=std.market.value,
                bypass_cache=bypass_cache,
            )
        except Exception as exc:
            logger.warning("batch fetch failed for %s: %s", original, exc)
            return {
                "_batch_failed": True,
                "_symbol": std.to_internal(),
                "_error": str(exc),
            }

    tasks = [_fetch_one(orig, std) for orig, std in resolved]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # --- Step 3: Collect successes, failures, warnings ---
    quote_items: list[dict[str, Any]] = []
    batch_failed_symbols: list[str] = list(failed_inputs)
    warnings: list[dict[str, Any]] = []

    for (original, std), result in zip(resolved, results):
        if isinstance(result, Exception):
            batch_failed_symbols.append(std.to_internal())
            warnings.append({
                "code": "BATCH_ITEM_ERROR",
                "message": f"Error fetching '{original}': {result}",
                "details": {"symbol": std.to_internal()},
            })
            continue

        if isinstance(result, dict) and result.get("_batch_failed"):
            batch_failed_symbols.append(result.get("_symbol", original))
            continue

        if isinstance(result, dict) and result.get("success"):
            data = result.get("data", {})
            if data:
                # Wrap as BatchQuoteItem
                meta = result.get("meta", {})
                cache_info = result.get("cache")
                item: dict[str, Any] = {
                    "symbol": data.get("symbol", std.to_internal()),
                    "name": data.get("name", ""),
                    "price": data.get("price", 0.0),
                    "change": data.get("change", 0.0),
                    "change_pct": data.get("change_pct", 0.0),
                    "open": data.get("open", 0.0),
                    "high": data.get("high", 0.0),
                    "low": data.get("low", 0.0),
                    "prev_close": data.get("prev_close", 0.0),
                    "volume": data.get("volume", 0),
                    "turnover": data.get("turnover", 0.0),
                    "timestamp": data.get("timestamp", ""),
                    "instrument_type": data.get("instrument_type", ""),
                }
                if cache_info:
                    item["cache"] = cache_info
                quote_items.append(item)
        else:
            batch_failed_symbols.append(std.to_internal())

    # --- Step 4: Build response ---
    validated_count = validated_total = sum(
        1 for r in resolved
        if isinstance(r, tuple)
    )

    data = {
        "quotes": quote_items,
        "failed_symbols": batch_failed_symbols,
        "summary": {
            "requested": len(symbols),
            "success": len(quote_items),
            "failed": len(batch_failed_symbols),
        },
    }

    # Determine primary market from first successful result
    first_market = ""
    if quote_items:
        first_market = quote_items[0].get("symbol", "").split(":")[0] if ":" in quote_items[0].get("symbol", "") else ""

    meta = {
        "market": first_market,
        "symbol": "",
        "source": "batch",
        "currency": settings.market_currencies.get(first_market, ""),
        "timezone": settings.market_timezones.get(first_market, ""),
        "market_session": "",
        "is_realtime": len(batch_failed_symbols) == 0,
        "data_delay_seconds": 0,
        "quality_flag": QualityFlag.LIVE.value if not batch_failed_symbols else QualityFlag.FALLBACK.value,
        "fallback_used": False,
    }

    if batch_failed_symbols:
        return builder.partial_success(
            data=data,
            meta=meta,
            warnings=warnings,
        )

    return builder.success(data=data, meta=meta)
