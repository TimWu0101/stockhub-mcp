"""get_technical_indicators tool implementation.

Fetches historical K-line data, then computes technical indicators
(MA, EMA, RSI, MACD, BOLL, KDJ) locally using pandas.

Result is flagged ``quality=computed``.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from market_data_mcp.config import settings
from market_data_mcp.domain.response_builder import ResponseBuilder
from market_data_mcp.domain.symbol.resolver import SymbolResolver
from market_data_mcp.enums import Market, QualityFlag
from market_data_mcp.tools.history import get_price_history_impl

logger = logging.getLogger(__name__)

# Supported indicators
_SUPPORTED_INDICATORS = {"MA", "EMA", "RSI", "MACD", "BOLL", "KDJ"}


# ------------------------------------------------------------------
# Tool implementation
# ------------------------------------------------------------------


async def get_technical_indicators_impl(
    symbol: str,
    indicators: list[str],
    market: str | None = None,
    period: str = "3mo",
    interval: str = "1d",
    adjust: str | None = None,
) -> dict[str, Any]:
    """Compute technical indicators for an instrument.

    Args:
        symbol: User-input symbol.
        indicators: List of indicator names: ``MA`` / ``EMA`` / ``RSI`` /
                    ``MACD`` / ``BOLL`` / ``KDJ``.
        market: Preferred market code.
        period: Look-back period for K-line data (default ``3mo``).
        interval: Bar interval (default ``1d``).
        adjust: Adjustment method (default ``qfq`` for CN).
    """
    builder = ResponseBuilder()

    # --- Validation ---
    if not indicators:
        return builder.error(
            error={
                "code": "EMPTY_INDICATORS",
                "type": "input_error",
                "message": "Indicators list must not be empty.",
                "retryable": False,
                "details": {},
            },
        )

    invalid = [i for i in indicators if i.upper() not in _SUPPORTED_INDICATORS]
    if invalid:
        return builder.error(
            error={
                "code": "UNSUPPORTED_INDICATOR",
                "type": "input_error",
                "message": f"Unsupported indicator(s): {', '.join(invalid)}. "
                           f"Supported: {', '.join(sorted(_SUPPORTED_INDICATORS))}.",
                "retryable": False,
                "details": {"invalid": invalid, "supported": sorted(_SUPPORTED_INDICATORS)},
            },
        )

    requested = [i.upper() for i in indicators]

    # --- Step 1: Fetch history ---
    history_resp = await get_price_history_impl(
        symbol=symbol, market=market,
        period=period, interval=interval, adjust=adjust,
    )

    if not history_resp.get("success"):
        # Propagate the history error
        return history_resp

    history_data = history_resp.get("data", {})
    history_bars: list[dict[str, Any]] = history_data.get("history", [])

    if not history_bars or len(history_bars) < 2:
        return builder.error(
            error={
                "code": "INSUFFICIENT_DATA",
                "type": "input_error",
                "message": "Not enough K-line data to compute indicators (need ≥ 2 bars).",
                "retryable": False,
                "details": {"bars_count": len(history_bars)},
            },
        )

    # --- Step 2: Build DataFrame ---
    records = []
    for bar in history_bars:
        records.append({
            "date": bar.get("date", ""),
            "close": float(bar.get("close", 0)),
            "high": float(bar.get("high", 0)),
            "low": float(bar.get("low", 0)),
            "volume": float(bar.get("volume", 0)),
        })

    df = pd.DataFrame(records)
    # Drop rows with NaN close (e.g. unfinished trading day)
    df = df.dropna(subset=["close"])
    if df.empty or "close" not in df.columns:
        return builder.error(
            error={
                "code": "INSUFFICIENT_DATA",
                "type": "input_error",
                "message": "Cannot build price series from history data.",
                "retryable": False,
                "details": {},
            },
        )

    # --- Step 3: Compute indicators ---
    computed: dict[str, dict[str, float]] = {}

    for ind in requested:
        try:
            result = _compute_indicator(ind, df)
            if result:
                computed[ind] = result
        except Exception as exc:
            logger.warning("indicator %s computation failed: %s", ind, exc)

    if not computed:
        return builder.error(
            error={
                "code": "COMPUTATION_FAILED",
                "type": "system_error",
                "message": "All indicator computations failed.",
                "retryable": False,
                "details": {},
            },
        )

    # --- Step 4: Build response ---
    internal = history_data.get("symbol", "")
    adj = history_data.get("adjust", "none") or "none"
    mkt_val = history_data.get("market", "") or ""

    meta = {
        "market": mkt_val,
        "symbol": internal,
        "source": "computed",
        "currency": settings.market_currencies.get(mkt_val, ""),
        "timezone": settings.market_timezones.get(mkt_val, ""),
        "market_session": history_resp.get("meta", {}).get("market_session", ""),
        "is_realtime": False,
        "data_delay_seconds": 0,
        "quality_flag": QualityFlag.COMPUTED.value,
        "fallback_used": False,
    }

    data = {
        "symbol": internal,
        "adjusted": adj,
        "indicators": computed,
    }

    return builder.success(data=data, meta=meta)


# ------------------------------------------------------------------
# Indicator computation functions
# ------------------------------------------------------------------


def _compute_indicator(name: str, df: pd.DataFrame) -> dict[str, float]:
    """Dispatch to the appropriate computation function."""
    if name == "MA":
        return _compute_ma(df)
    elif name == "EMA":
        return _compute_ema(df)
    elif name == "RSI":
        return _compute_rsi(df)
    elif name == "MACD":
        return _compute_macd(df)
    elif name == "BOLL":
        return _compute_boll(df)
    elif name == "KDJ":
        return _compute_kdj(df)
    else:
        return {}


def _compute_ma(df: pd.DataFrame) -> dict[str, float]:
    """Compute Simple Moving Averages: MA5, MA10, MA20, MA60."""
    close = df["close"]
    result: dict[str, float] = {}
    periods = [5, 10, 20, 60]
    for p in periods:
        if len(close) >= p:
            result[f"MA{p}"] = round(float(close.rolling(window=p).mean().iloc[-1]), 4)
    return result


def _compute_ema(df: pd.DataFrame) -> dict[str, float]:
    """Compute Exponential Moving Averages: EMA12, EMA26."""
    close = df["close"]
    result: dict[str, float] = {}
    periods = [12, 26]
    for p in periods:
        if len(close) >= p:
            result[f"EMA{p}"] = round(float(close.ewm(span=p, adjust=False).mean().iloc[-1]), 4)
    return result


def _compute_rsi(df: pd.DataFrame) -> dict[str, float]:
    """Compute Relative Strength Index: RSI6, RSI14, RSI24."""
    close = df["close"]
    result: dict[str, float] = {}
    periods = [6, 14, 24]
    for p in periods:
        if len(close) > p:
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0).rolling(window=p).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=p).mean()
            rs = gain / loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
            result[f"RSI{p}"] = round(float(rsi.iloc[-1]), 4)
    return result


def _compute_macd(df: pd.DataFrame) -> dict[str, float]:
    """Compute MACD: DIF, DEA, MACD bar.

    Standard parameters: fast=12, slow=26, signal=9.
    """
    close = df["close"]
    if len(close) < 35:
        return {}

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_bar = 2.0 * (dif - dea)

    return {
        "DIF": round(float(dif.iloc[-1]), 4),
        "DEA": round(float(dea.iloc[-1]), 4),
        "MACD": round(float(macd_bar.iloc[-1]), 4),
    }


def _compute_boll(df: pd.DataFrame) -> dict[str, float]:
    """Compute Bollinger Bands: UPPER, MIDDLE, LOWER (20-period, 2 std)."""
    close = df["close"]
    if len(close) < 20:
        return {}

    middle = close.rolling(window=20).mean()
    std = close.rolling(window=20).std()
    upper = middle + 2.0 * std
    lower = middle - 2.0 * std

    return {
        "UPPER": round(float(upper.iloc[-1]), 4),
        "MIDDLE": round(float(middle.iloc[-1]), 4),
        "LOWER": round(float(lower.iloc[-1]), 4),
    }


def _compute_kdj(df: pd.DataFrame) -> dict[str, float]:
    """Compute KDJ: K, D, J (9-period).

    K = 2/3 * prev_K + 1/3 * RSV
    D = 2/3 * prev_D + 1/3 * K
    J = 3 * K - 2 * D
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    n = 9
    if len(close) < n + 1:
        return {}

    # RSV
    lowest_low = low.rolling(window=n).min()
    highest_high = high.rolling(window=n).max()
    rsv = ((close - lowest_low) / (highest_high - lowest_low + 1e-9)) * 100.0

    # Iterative K/D calculation
    k_vals: list[float] = [50.0]  # Initial K
    d_vals: list[float] = [50.0]  # Initial D

    for i in range(1, len(rsv)):
        rsv_val = rsv.iloc[i]
        if pd.isna(rsv_val):
            k_vals.append(k_vals[-1])
            d_vals.append(d_vals[-1])
            continue
        k = (2.0 / 3.0) * k_vals[-1] + (1.0 / 3.0) * rsv_val
        d = (2.0 / 3.0) * d_vals[-1] + (1.0 / 3.0) * k
        k_vals.append(k)
        d_vals.append(d)

    k = k_vals[-1]
    d = d_vals[-1]
    j = 3.0 * k - 2.0 * d

    return {
        "K": round(k, 4),
        "D": round(d, 4),
        "J": round(j, 4),
    }
