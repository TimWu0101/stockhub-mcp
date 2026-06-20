"""TechnicalIndicatorsData: computed technical indicators domain model.

Aligned with v0.1-schema.md §4.4.

Supported indicators: MA, EMA, RSI, MACD, BOLL, KDJ.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TechnicalIndicatorsData(BaseModel):
    """Computed technical indicators for a single instrument.

    ``indicators`` is a nested dict keyed by indicator name:

    .. code-block:: json

        {
            "MA":  {"MA5": 1690.2, "MA10": 1685.0, "MA20": 1670.5, "MA60": 1620.0},
            "EMA": {"EMA12": 1688.0, "EMA26": 1670.0},
            "RSI": {"RSI6": 58.2, "RSI14": 52.3, "RSI24": 48.1},
            "MACD": {"DIF": 12.5, "DEA": 10.2, "MACD": 2.3},
            "BOLL": {"UPPER": 1720.0, "MIDDLE": 1685.0, "LOWER": 1650.0},
            "KDJ": {"K": 55.0, "D": 50.0, "J": 65.0}
        }
    """

    symbol: str = Field(..., description="Internal standard symbol, e.g. 'CN:600519'.")
    adjusted: str = Field(..., description="Adjustment method used: none / qfq / hfq.")
    indicators: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description=(
            "Computed indicators keyed by name (MA / EMA / RSI / MACD / BOLL / KDJ). "
            "Each sub-dict maps indicator-specific keys to float values."
        ),
    )
