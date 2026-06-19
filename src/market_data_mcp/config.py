"""Global configuration via environment variables with sensible defaults."""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables.

    All values have defaults so the server can start with zero configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Cache ---
    cache_max_size: int = 100
    """Maximum number of cache entries (FIFO eviction when full)."""

    # --- Data Source ---
    tushare_token: Optional[str] = None
    """Optional Tushare token for enhanced A-share data."""

    request_timeout: int = 15
    """HTTP request timeout in seconds."""

    max_retries: int = 2
    """Maximum retry attempts per data source."""

    circuit_breaker_cooldown: int = 300
    """Cooldown period in seconds before re-testing a degraded source."""

    circuit_breaker_failure_window: int = 60
    """Rolling window in seconds for counting failures."""

    circuit_breaker_failure_threshold: int = 3
    """Consecutive failures within the window that trigger degradation."""

    # --- Logging ---
    log_level: str = "INFO"
    """Log level (DEBUG, INFO, WARNING, ERROR). Output to stderr only."""

    # --- Market metadata ---
    @property
    def market_timezones(self) -> dict[str, str]:
        """IANA timezone for each market."""
        return {
            "CN": "Asia/Shanghai",
            "HK": "Asia/Hong_Kong",
            "US": "America/New_York",
        }

    @property
    def market_currencies(self) -> dict[str, str]:
        """ISO 4217 currency code for each market."""
        return {
            "CN": "CNY",
            "HK": "HKD",
            "US": "USD",
        }

    @property
    def source_priority(self) -> dict[str, list[str]]:
        """Default data-source priority per market scope.

        Keys are market‑scopes; values are source names in priority order.
        """
        return {
            "CN": ["tx", "sina"],
            "CN_history": ["tencent", "yfinance"],
            "HK": ["yfinance"],
            "US": ["yfinance"],
            "CN_sector": ["eastmoney"],
        }


# Singleton instance – import this everywhere.
settings = Settings()
