"""Common Pydantic models shared across all response types.

These models appear inside every tool response (meta, cache, error, warnings).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class MetaInfo(BaseModel):
    """Mandatory metadata included in every tool response."""

    request_id: str = Field(..., description="Unique request identifier (UUID).")
    market: str = Field(..., description="Market code: CN / HK / US.")
    symbol: str = Field(
        ..., description="Internal standard symbol, e.g. 'CN:600519'."
    )
    source: str = Field(..., description="Data source that served this response.")
    currency: str = Field(..., description="ISO 4217 currency code.")
    timezone: str = Field(..., description="IANA timezone, e.g. 'Asia/Shanghai'.")
    market_session: str = Field(
        ..., description="Current market session, e.g. 'continuous'."
    )
    is_realtime: bool = Field(..., description="Whether data is real-time.")
    data_delay_seconds: int = Field(0, description="Estimated data delay in seconds.")
    quality_flag: str = Field(..., description="Data quality flag, e.g. 'live'.")
    fallback_used: bool = Field(
        False, description="Whether a fallback source was used."
    )
    responded_at: str = Field(..., description="Response time in ISO 8601.")


class CacheInfo(BaseModel):
    """Cache metadata attached to price‑class tool responses."""

    hit: bool = Field(..., description="Whether the cache was hit.")
    expires_at: Optional[str] = Field(
        None, description="Cache expiration time (ISO 8601)."
    )
    ttl_remaining: Optional[int] = Field(
        None, description="Remaining TTL in seconds."
    )
    cached_at: Optional[str] = Field(
        None, description="Time when this entry was cached (ISO 8601)."
    )
    policy: Optional[str] = Field(
        None, description="Cache policy name, e.g. 'cn_post_close_until_next_trading_day_0900'."
    )
    bypass_cache: bool = Field(
        False, description="Whether the request explicitly skipped the cache."
    )


class ErrorInfo(BaseModel):
    """Structured error returned on failure."""

    code: str = Field(..., description="Machine-readable error code.")
    type: str = Field(..., description="Error category: input_error / source_error / ...")
    message: str = Field(..., description="Human-readable error message.")
    retryable: bool = Field(..., description="Whether retrying may succeed.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error context."
    )


class WarningInfo(BaseModel):
    """Structured warning for partial-success or advisory scenarios."""

    code: str = Field(..., description="Machine-readable warning code.")
    message: str = Field(..., description="Human-readable warning message.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional warning context."
    )
