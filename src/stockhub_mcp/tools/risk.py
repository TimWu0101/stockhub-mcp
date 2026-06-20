"""V0.4 – Risk metrics: volatility, drawdown, beta, Sharpe, VaR (pure local computation)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from stockhub_mcp.domain.response_builder import ResponseBuilder


async def get_risk_metrics_impl(
    symbol: str,
    period: str = "1y",
    market: str | None = None,
    benchmark: str | None = None,
) -> dict:
    """Compute risk metrics from historical price data.

    Args:
        symbol: Stock ticker.
        period: Lookback period (3mo/6mo/1y/2y/5y).
        market: Preferred market.
        benchmark: Benchmark ticker for Beta (default: SPY for US, 000300.SS for CN).
    """
    builder = ResponseBuilder()

    try:
        # Fetch history for the stock
        from stockhub_mcp.tools.history import get_price_history_impl
        hist_resp = await get_price_history_impl(
            symbol=symbol, market=market, period=period, interval="1d", adjust="qfq",
        )
        if not hist_resp.get("success"):
            return hist_resp
        bars = hist_resp.get("data", {}).get("history", [])
        if len(bars) < 20:
            return builder.error(error={
                "code": "INSUFFICIENT_DATA", "type": "input_error",
                "message": "Need ≥ 20 trading days for risk metrics.",
                "retryable": False, "details": {},
            })

        closes = pd.Series([b["close"] for b in bars])
        returns = closes.pct_change().dropna()

        # --- Volatility (annualized) ---
        daily_vol = float(np.std(returns))
        ann_vol = round(daily_vol * np.sqrt(252) * 100, 2)

        # --- Max Drawdown ---
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = round(float(np.min(drawdown)) * 100, 2)

        # --- Sharpe Ratio ---
        excess = returns - 0.02 / 252  # assume 2% risk-free rate
        sharpe = round(float(np.mean(excess) / np.std(returns) * np.sqrt(252)), 2) if np.std(returns) > 0 else 0.0

        # --- VaR 95% ---
        var_95 = round(float(np.percentile(returns, 5)) * 100, 2)

        # --- Beta ---
        beta = None
        if benchmark:
            bench_resp = await get_price_history_impl(
                symbol=benchmark, period=period, interval="1d",
            )
            if bench_resp.get("success"):
                bench_bars = bench_resp.get("data", {}).get("history", [])
                if len(bench_bars) >= 20:
                    bench_closes = pd.Series([b["close"] for b in bench_bars])
                    bench_returns = bench_closes.pct_change().dropna()
                    aligned = pd.concat([returns, bench_returns], axis=1).dropna()
                    if len(aligned) > 10:
                        cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
                        beta = round(float(cov[0, 1] / cov[1, 1]), 2)

        data = {
            "symbol": hist_resp.get("data", {}).get("symbol", ""),
            "period": period,
            "trading_days": len(bars),
            "annualized_volatility_pct": ann_vol,
            "max_drawdown_pct": max_dd,
            "sharpe_ratio": sharpe,
            "var_95_pct": var_95,
            "beta": beta,
            "benchmark": benchmark,
        }

        return builder.success(data=data, meta={
            "market": hist_resp.get("meta", {}).get("market", ""),
            "symbol": data["symbol"],
            "source": "computed",
            "currency": "",
            "timezone": "",
            "market_session": "",
            "is_realtime": False,
            "data_delay_seconds": 0,
            "quality_flag": "computed",
        })
    except Exception as exc:
        return builder.error(error={
            "code": "RISK_FAILED", "type": "source_error",
            "message": f"Risk metrics failed: {exc}",
            "retryable": True, "details": {},
        })
