"""V0.4 – Portfolio tools: exposure analysis, correlation matrix (pure local computation)."""

from __future__ import annotations

import asyncio
import numpy as np
import pandas as pd

from stockhub_mcp.domain.response_builder import ResponseBuilder


async def _fetch_history(symbol: str, period: str = "1y") -> dict:
    from stockhub_mcp.tools.history import get_price_history_impl
    return await get_price_history_impl(symbol=symbol, period=period, interval="1d")


async def get_correlation_matrix_impl(
    symbols: list[str],
    period: str = "6mo",
) -> dict:
    """Compute pairwise correlation matrix for a list of stocks.

    Args:
        symbols: List of tickers (3-10 recommended).
        period: Lookback period.
    """
    builder = ResponseBuilder()
    if len(symbols) < 2:
        return builder.error(error={
            "code": "TOO_FEW_SYMBOLS", "type": "input_error",
            "message": "Need at least 2 symbols for correlation.", "retryable": False, "details": {},
        })
    if len(symbols) > 10:
        return builder.error(error={
            "code": "TOO_MANY_SYMBOLS", "type": "input_error",
            "message": "Maximum 10 symbols allowed.", "retryable": False, "details": {},
        })

    try:
        # Fetch all histories in parallel
        tasks = [asyncio.create_task(_fetch_history(sym, period)) for sym in symbols]
        results = await asyncio.gather(*tasks)

        # Build returns DataFrame
        returns_dict: dict[str, pd.Series] = {}
        for sym, resp in zip(symbols, results):
            if not resp.get("success"):
                continue
            bars = resp.get("data", {}).get("history", [])
            if len(bars) < 20:
                continue
            closes = pd.Series([b["close"] for b in bars])
            returns_dict[sym] = closes.pct_change().dropna()

        if len(returns_dict) < 2:
            return builder.error(error={
                "code": "INSUFFICIENT_DATA", "type": "input_error",
                "message": f"Only {len(returns_dict)} valid symbol(s) returned sufficient data.",
                "retryable": False, "details": {},
            })

        # Compute correlation matrix
        returns_df = pd.DataFrame(returns_dict).dropna()
        if len(returns_df) < 10:
            return builder.error(error={
                "code": "INSUFFICIENT_DATA", "type": "input_error",
                "message": "Not enough overlapping trading days.",
                "retryable": False, "details": {},
            })

        corr = returns_df.corr()
        matrix: list[list[float]] = []
        labels = list(corr.columns)
        for row in labels:
            matrix.append([round(float(corr.loc[row, col]), 4) for col in labels])

        return builder.success(data={
            "symbols": labels,
            "period": period,
            "correlation_matrix": matrix,
            "failed_symbols": [s for s in symbols if s not in labels],
        }, meta={
            "market": "", "symbol": "", "source": "computed",
            "currency": "", "timezone": "", "market_session": "",
            "is_realtime": False, "data_delay_seconds": 0, "quality_flag": "computed",
        })
    except Exception as exc:
        return builder.error(error={
            "code": "CORRELATION_FAILED", "type": "source_error",
            "message": str(exc), "retryable": True, "details": {},
        })


async def analyze_portfolio_exposure_impl(
    symbols: list[str],
    period: str = "6mo",
) -> dict:
    """Analyze portfolio concentration and risk exposure.

    Args:
        symbols: Portfolio tickers (2-10).
        period: Lookback period.
    """
    builder = ResponseBuilder()
    if len(symbols) < 2:
        return builder.error(error={
            "code": "TOO_FEW_SYMBOLS", "type": "input_error",
            "message": "Need at least 2 symbols.", "retryable": False, "details": {},
        })

    try:
        # Fetch all histories
        tasks = [asyncio.create_task(_fetch_history(sym, period)) for sym in symbols]
        results = await asyncio.gather(*tasks)

        volatilities: dict[str, float] = {}
        avg_returns: dict[str, float] = {}
        annualized_return: dict[str, float] = {}

        for sym, resp in zip(symbols, results):
            if not resp.get("success"):
                continue
            bars = resp.get("data", {}).get("history", [])
            if len(bars) < 20:
                continue
            returns = pd.Series([b["close"] for b in bars]).pct_change().dropna()
            volatilities[sym] = round(float(np.std(returns) * np.sqrt(252) * 100), 2)
            avg_returns[sym] = round(float(np.mean(returns)) * 252 * 100, 2)

        # Compute correlation for diversification score
        returns_dict = {}
        for sym in volatilities:
            r = results[symbols.index(sym)].get("data", {}).get("history", [])
            s = pd.Series([b["close"] for b in r]).pct_change().dropna()
            returns_dict[sym] = s

        avg_corr = 0.0
        if len(returns_dict) >= 2:
            corr_matrix = pd.DataFrame(returns_dict).corr()
            avg_corr = round(float((corr_matrix.sum().sum() - len(corr_matrix)) / (len(corr_matrix) * (len(corr_matrix) - 1))), 4)

        # Portfolio volatility (equal weight)
        num = len(volatilities)
        weights = [1.0 / num] * num if num > 0 else []
        port_vol = round(float(np.sqrt(sum(w * w * v * v / 10000 for w, v in zip(weights, volatilities.values())) * (1 + avg_corr * (num - 1) / num)) * 100), 2) if num > 1 else 0

        # Concentration: check if any single position dominates
        concentration_warning = "diversified" if num >= 5 else "concentrated" if num <= 3 else "moderate"

        return builder.success(data={
            "symbols": list(volatilities.keys()),
            "count": num,
            "concentration": concentration_warning,
            "portfolio_volatility_pct": port_vol,
            "avg_pairwise_correlation": avg_corr,
            "individual_volatility_pct": volatilities,
            "individual_annualized_return_pct": avg_returns,
        }, meta={
            "market": "", "symbol": "", "source": "computed",
            "currency": "", "timezone": "", "market_session": "",
            "is_realtime": False, "data_delay_seconds": 0, "quality_flag": "computed",
        })
    except Exception as exc:
        return builder.error(error={
            "code": "EXPOSURE_FAILED", "type": "source_error",
            "message": str(exc), "retryable": True, "details": {},
        })
