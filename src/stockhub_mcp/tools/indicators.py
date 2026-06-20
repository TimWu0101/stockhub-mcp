"""get_technical_indicators tool implementation.

Fetches historical K-line data, then computes technical indicators
(MA, EMA, RSI, MACD, BOLL, KDJ) locally using pandas.

Result is flagged ``quality=computed``.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from stockhub_mcp.config import settings
from stockhub_mcp.domain.response_builder import ResponseBuilder
from stockhub_mcp.domain.symbol.resolver import SymbolResolver
from stockhub_mcp.enums import Market, QualityFlag
from stockhub_mcp.tools.history import get_price_history_impl

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
        "data_timestamp": history_bars[-1]["date"] if history_bars else "",
    }

    data = {
        "symbol": internal,
        "adjusted": adj,
        "data_timestamp": history_bars[-1].get("date", "") if history_bars else "",
        "indicators": computed,
    }

    # --- Step 5: Qualitative analysis (V0.4) ---
    try:
        trend = _analyze_trend(df, computed)
        volume = _analyze_volume(df)
        signal = _analyze_signal(computed, trend, volume)
        data["analysis"] = {
            "trend": trend,
            "volume": volume,
            "signal": signal,
        }
    except Exception:
        pass

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


# ------------------------------------------------------------------
# V0.4  Qualitative analysis (借鉴 daily_stock_analysis)
# ------------------------------------------------------------------

def _analyze_trend(df: pd.DataFrame, computed: dict) -> dict:
    """7-tier trend state analysis based on MA alignment."""
    close = df["close"]
    mas = {}
    periods = [5, 10, 20, 60]
    for p in periods:
        if len(close) >= p:
            mas[p] = float(close.rolling(window=p).mean().iloc[-1])

    if len(mas) < 3:
        return {"trend": "insufficient_data", "bias_pct": None}

    # MA alignment
    ma5, ma10, ma20 = mas.get(5, 0), mas.get(10, 0), mas.get(20, 0)
    ma60 = mas.get(60, 0)
    last_close = float(close.iloc[-1])

    # Determine trend state
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20 and ma5 > ma20 * 1.03:
            trend = "强势多头"  # strong bull
        elif ma5 > ma10 > ma20:
            trend = "多头排列"  # bullish alignment
        elif ma5 > ma20 and ma10 < ma5:
            trend = "弱势多头"  # weak bull
        elif ma5 < ma10 < ma20:
            trend = "空头排列"  # bearish alignment
        elif ma5 < ma10 < ma20 and ma5 < ma20 * 0.97:
            trend = "强势空头"  # strong bear
        else:
            trend = "盘整"  # consolidation
    else:
        trend = "insufficient_data"

    # Bias rate
    bias_pct = round((last_close - ma5) / ma5 * 100, 2) if ma5 and ma5 > 0 else None

    # Support/Resistance
    support = None
    resistance = None
    for p, ma_val in sorted(mas.items()):
        if ma_val < last_close:
            support = f"MA{p}={ma_val:.2f}"
        if ma_val > last_close and resistance is None:
            resistance = f"MA{p}={ma_val:.2f}"

    return {
        "trend": trend,
        "bias_pct": bias_pct,
        "bias_ma5": bias_pct,
        "support": support,
        "resistance": resistance,
    }


def _analyze_volume(df: pd.DataFrame) -> dict:
    """Volume analysis: ratio, status."""
    if "volume" not in df.columns or len(df) < 6:
        return {"status": "insufficient_data"}

    latest = float(df["volume"].iloc[-1])
    avg5 = float(df["volume"].tail(5).mean()) if len(df) >= 5 else latest
    ratio = round(latest / avg5, 2) if avg5 > 0 else 1.0

    if ratio > 2.0:
        status = "巨量"
    elif ratio > 1.5:
        status = "放量"
    elif ratio < 0.5:
        status = "地量"
    elif ratio < 0.7:
        status = "缩量"
    else:
        status = "正常"

    return {"volume_ratio": ratio, "volume_status": status}


def _analyze_signal(computed: dict, trend: dict, volume: dict) -> dict:
    """Composite signal score (0-100)."""
    score = 0
    reasons: list[str] = []

    t = trend.get("trend", "")
    if t == "强势多头":
        score += 30
        reasons.append("强势多头排列")
    elif t == "多头排列":
        score += 20
        reasons.append("多头排列")
    elif t == "弱势多头":
        score += 10
        reasons.append("弱势多头")

    # Bias: -3% to +3% is ideal for entry
    bias = trend.get("bias_pct")
    if bias is not None:
        if -2 <= bias <= 2:
            score += 15
            reasons.append("乖离率适中")
        elif bias < -5:
            reasons.append(f"超跌(bias={bias}%)")

    # Volume: shrinking means consolidation, good for entry
    vs = volume.get("volume_status", "")
    if vs == "缩量":
        score += 15
        reasons.append("缩量回调(最佳买点)")
    elif vs == "放量":
        score += 5
        reasons.append("放量")
    elif vs == "巨量":
        reasons.append("巨量(注意风险)")

    # MACD
    macd = computed.get("MACD", {})
    dif = macd.get("DIF", 0)
    dea = macd.get("DEA", 0)
    if dif > dea and dif > 0:
        score += 10
        reasons.append("MACD零轴上金叉")
    elif dif > dea:
        score += 8
        reasons.append("MACD金叉")
    elif dif < dea:
        reasons.append("MACD死叉")

    # RSI
    rsi = computed.get("RSI", {})
    rsi14 = rsi.get("RSI14", 50)
    if rsi14 < 30:
        score += 10
        reasons.append("RSI超卖(<30)反弹信号")
    elif 30 <= rsi14 <= 50:
        score += 5
        reasons.append("RSI非超买区")
    elif rsi14 > 70:
        score -= 5
        reasons.append("RSI超买(>70)")

    # Determine signal type
    if score >= 60:
        signal = "强买入"
    elif score >= 45:
        signal = "买入"
    elif score >= 25:
        signal = "观望"
    elif score >= 10:
        signal = "卖出"
    else:
        signal = "强卖出"

    return {
        "signal": signal,
        "signal_score": min(score, 100),
        "reasons": reasons,
    }
