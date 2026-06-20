"""All enumerations used across the stockhub-mcp project.

Shared by models, sources, cache layer, and tools.
"""

from enum import StrEnum


class Market(StrEnum):
    """Financial market identifier."""

    CN = "CN"  # A-share (Shanghai / Shenzhen)
    HK = "HK"  # Hong Kong
    US = "US"  # United States


class InstrumentType(StrEnum):
    """Type of financial instrument."""

    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    FUND = "fund"
    FUTURE = "future"


class MarketSession(StrEnum):
    """Current trading session phase for a given market."""

    PRE_OPENING = "pre_opening"  # Pre-open / call auction
    CONTINUOUS = "continuous"  # Continuous trading
    LUNCH_BREAK = "lunch_break"  # Midday break (CN / HK)
    AUCTION = "auction"  # Closing auction (HK)
    POST_CLOSE = "post_close"  # After market close
    CLOSED = "closed"  # Non-trading day (weekend / holiday)
    UNKNOWN = "unknown"  # Unable to determine – treat conservatively


class DataSource(StrEnum):
    """Data source identifier."""

    YFINANCE = "yfinance"
    TX = "tx"  # Tencent
    SINA = "sina"
    EASTMONEY = "eastmoney"
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    COMPUTED = "computed"  # Locally computed (e.g. technical indicators)


class AdjustType(StrEnum):
    """Price adjustment (复权) method for historical data."""

    NONE = "none"  # No adjustment
    QFQ = "qfq"  # Forward-adjusted (前复权)
    HFQ = "hfq"  # Backward-adjusted (后复权)


class QualityFlag(StrEnum):
    """Data quality / freshness indicator."""

    LIVE = "live"
    DELAYED = "delayed"
    STALE = "stale"
    FALLBACK = "fallback"
    FALLBACK_LOW_CONFIDENCE = "fallback_low_confidence"
    ESTIMATED = "estimated"
    COMPUTED = "computed"


class ErrorType(StrEnum):
    """Top-level error category."""

    INPUT_ERROR = "input_error"
    BUSINESS_ERROR = "business_error"
    SOURCE_ERROR = "source_error"
    SYSTEM_ERROR = "system_error"


class SourceStatus(StrEnum):
    """Health status of a data source."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class CacheScope(StrEnum):
    """Granularity for cache-clear operations."""

    SYMBOL = "symbol"
    MARKET = "market"
    TOOL = "tool"
    ALL = "all"
