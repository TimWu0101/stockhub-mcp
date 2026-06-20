"""Pydantic response models for all V0.1 tools.

Each model corresponds to the ``data`` field of a tool's response as defined in
`docs/v0.1-schema.md`.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 4.1  get_realtime_quote
# ---------------------------------------------------------------------------


class QuoteResponse(BaseModel):
    """Single-instrument real-time quote."""

    symbol: str = Field(..., description="Internal standard symbol, e.g. 'CN:600519'.")
    name: str = Field(..., description="Display name of the instrument.")
    market: str = Field(..., description="Market code: CN / HK / US.")
    price: float = Field(..., description="Latest price.")
    change: float = Field(..., description="Price change from previous close.")
    change_pct: float = Field(..., description="Percentage change.")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Session high.")
    low: float = Field(..., description="Session low.")
    prev_close: float = Field(..., description="Previous close price.")
    volume: int = Field(..., description="Trading volume (shares).")
    turnover: float = Field(..., description="Trading turnover (currency units).")
    timestamp: str = Field(..., description="Quote timestamp (ISO 8601).")
    instrument_type: str = Field(..., description="Instrument type: stock / index / etf.")


# ---------------------------------------------------------------------------
# 4.2  get_price_history
# ---------------------------------------------------------------------------


class KLineItem(BaseModel):
    """Single candlestick bar."""

    date: str = Field(..., description="Date string, e.g. '2026-06-15'.")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Highest price.")
    low: float = Field(..., description="Lowest price.")
    close: float = Field(..., description="Closing price.")
    volume: int = Field(..., description="Volume (shares).")
    turnover: float = Field(..., description="Turnover (currency units).")
    change_pct: float = Field(..., description="Percentage change vs previous bar.")


class HistoryResponse(BaseModel):
    """Historical K-line data response."""

    symbol: str = Field(..., description="Internal standard symbol.")
    market: str = Field(..., description="Market code.")
    period: str = Field(..., description="Requested period, e.g. '1mo'.")
    interval: str = Field(..., description="Bar interval, e.g. '1d'.")
    adjust: str = Field(..., description="Adjustment method: none / qfq / hfq.")
    count: int = Field(..., description="Number of bars returned.")
    history: list[KLineItem] = Field(default_factory=list, description="K-line data.")


# ---------------------------------------------------------------------------
# 4.3  get_batch_quotes
# ---------------------------------------------------------------------------


class BatchQuoteItem(BaseModel):
    """A single quote inside a batch response, with its own cache info."""

    symbol: str = Field(..., description="Internal standard symbol.")
    name: str = Field(..., description="Display name.")
    price: float = Field(..., description="Latest price.")
    change: float = Field(..., description="Price change.")
    change_pct: float = Field(..., description="Percentage change.")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Session high.")
    low: float = Field(..., description="Session low.")
    prev_close: float = Field(..., description="Previous close.")
    volume: int = Field(..., description="Volume.")
    turnover: float = Field(..., description="Turnover.")
    timestamp: str = Field(..., description="Quote timestamp (ISO 8601).")
    instrument_type: str = Field(..., description="Instrument type.")
    cache: Optional[dict[str, Any]] = Field(
        None, description="Per-symbol cache metadata."
    )


class BatchSummary(BaseModel):
    """Aggregated statistics for a batch request."""

    requested: int = Field(..., description="Total symbols requested.")
    success: int = Field(..., description="Symbols successfully fetched.")
    failed: int = Field(..., description="Symbols that failed.")


class BatchQuoteResponse(BaseModel):
    """Response for get_batch_quotes."""

    quotes: list[BatchQuoteItem] = Field(default_factory=list, description="Successful quotes.")
    failed_symbols: list[str] = Field(
        default_factory=list, description="Symbols that could not be resolved."
    )
    summary: BatchSummary = Field(..., description="Aggregated counts.")


# ---------------------------------------------------------------------------
# 4.4  get_technical_indicators
# ---------------------------------------------------------------------------


class TechnicalIndicatorsResponse(BaseModel):
    """Response for get_technical_indicators."""

    symbol: str = Field(..., description="Internal standard symbol.")
    adjusted: str = Field(..., description="Adjustment method used.")
    indicators: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Computed indicators, e.g. {'MA': {'MA5': 1690.2, ...}, ...}.",
    )


# ---------------------------------------------------------------------------
# 4.5  get_sector_boards
# ---------------------------------------------------------------------------


class SectorItem(BaseModel):
    """Single sector / concept board entry."""

    code: str = Field(..., description="Sector code, e.g. 'BK0001'.")
    name: str = Field(..., description="Sector display name.")
    type: str = Field(..., description="Board type: industry / concept.")
    change_pct: float = Field(..., description="Sector average change %.")
    leading_stock: str = Field(
        ..., description="Internal symbol of the leading stock."
    )
    leading_stock_name: str = Field(..., description="Name of the leading stock.")
    leading_stock_change_pct: float = Field(
        ..., description="Leading stock change %."
    )
    stock_count: int = Field(..., description="Number of constituent stocks.")


class SectorBoardsResponse(BaseModel):
    """Response for get_sector_boards."""

    sectors: list[SectorItem] = Field(default_factory=list, description="Sector list.")


# ---------------------------------------------------------------------------
# 4.6  get_capital_flow
# ---------------------------------------------------------------------------


class CapitalFlowResponse(BaseModel):
    """Response for get_capital_flow (market-level)."""

    scope: str = Field(..., description="Scope: market or sector.")
    timestamp: str = Field(..., description="Data timestamp (ISO 8601).")
    main_net_inflow: float = Field(..., description="Main net inflow.")
    super_large_net_inflow: float = Field(..., description="Super-large orders net inflow.")
    large_net_inflow: float = Field(..., description="Large orders net inflow.")
    medium_net_inflow: float = Field(..., description="Medium orders net inflow.")
    small_net_inflow: float = Field(..., description="Small orders net inflow.")


# ---------------------------------------------------------------------------
# 4.7  search_symbol
# ---------------------------------------------------------------------------


class SearchResultItem(BaseModel):
    """Single symbol-search hit."""

    symbol: str = Field(..., description="Internal standard symbol.")
    name: str = Field(..., description="Instrument name.")
    display_name: str = Field(..., description="Human-readable display name.")
    market: str = Field(..., description="Market code.")
    exchange: str = Field(..., description="Exchange, e.g. 'SSE', 'NYSE'.")
    instrument_type: str = Field(..., description="Instrument type.")
    currency: str = Field(..., description="ISO 4217 currency.")


class SearchResponse(BaseModel):
    """Response for search_symbol."""

    results: list[SearchResultItem] = Field(
        default_factory=list, description="Search results."
    )


# ---------------------------------------------------------------------------
# 4.8  get_source_status
# ---------------------------------------------------------------------------


class SourceHealthItem(BaseModel):
    """Health status of a single data source."""

    name: str = Field(..., description="Source name.")
    status: str = Field(
        ..., description="One of: available / degraded / unavailable."
    )
    market_coverage: list[str] = Field(
        default_factory=list, description="Markets covered by this source."
    )
    last_checked: str = Field(..., description="Last health-check time (ISO 8601).")
    failures_in_window: int = Field(
        0, description="Failure count in the current rolling window."
    )
    degraded_since: Optional[str] = Field(
        None, description="When the source became degraded (ISO 8601)."
    )


class SourceStatusResponse(BaseModel):
    """Response for get_source_status."""

    sources: list[SourceHealthItem] = Field(
        default_factory=list, description="Per-source health entries."
    )


# ---------------------------------------------------------------------------
# 4.9  get_trading_calendar
# ---------------------------------------------------------------------------


class HolidayItem(BaseModel):
    """A non-trading day entry."""

    date: str = Field(..., description="Date string, e.g. '2026-06-20'.")
    name: str = Field(..., description="Holiday name, e.g. '端午节'.")
    type: str = Field(..., description="Holiday type, e.g. 'public_holiday'.")


class TradingCalendarResponse(BaseModel):
    """Response for get_trading_calendar."""

    market: str = Field(..., description="Market code.")
    from_date: str = Field(..., description="Start date of the query range.")
    to_date: str = Field(..., description="End date of the query range.")
    total_days: int = Field(..., description="Total calendar days in range.")
    trading_days: int = Field(..., description="Number of trading days in range.")
    holidays: list[HolidayItem] = Field(
        default_factory=list, description="Holidays within the range."
    )
    next_trading_day: str = Field(
        ..., description="Next trading day (ISO 8601 date)."
    )


# ---------------------------------------------------------------------------
# 4.10 clear_quote_cache
# ---------------------------------------------------------------------------


class ClearCacheResponse(BaseModel):
    """Response for clear_quote_cache."""

    scope: str = Field(..., description="Cleared scope: symbol / market / tool / all.")
    matched_count: int = Field(..., description="Number of cache keys matched.")
    deleted_count: int = Field(
        ..., description="Number of cache keys actually deleted (0 in dry_run)."
    )
    dry_run: bool = Field(
        False, description="Whether this was a dry-run (no actual deletion)."
    )
    filters: dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Filters used for this clear operation.",
    )
