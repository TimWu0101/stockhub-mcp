"""Unified logging configuration for market-data-mcp.

All log output goes to stderr; no file logging in V0.1.
"""

from __future__ import annotations

import logging
import sys

from market_data_mcp.config import settings


def configure_logging() -> None:
    """Set up the root logger with the configured level and stderr handler.

    Called once at server startup.
    """
    level = _parse_level(settings.log_level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on re-import / hot-reload
    root.handlers.clear()
    root.addHandler(handler)

    # Keep third-party loggers quieter
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("akshare").setLevel(logging.WARNING)


def _parse_level(name: str) -> int:
    """Convert a level name string to a logging constant, defaulting to INFO."""
    try:
        return getattr(logging, name.upper())
    except AttributeError:
        return logging.INFO
