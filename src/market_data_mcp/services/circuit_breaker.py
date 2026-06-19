"""CircuitBreaker: protect against cascading source failures.

After ``N`` consecutive failures within a rolling window, the source
is marked ``degraded``.  After a configurable cooldown, it transitions
back to ``available`` on the next successful probe.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

from market_data_mcp.config import settings
from market_data_mcp.enums import SourceStatus

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Per-source failure tracker with automatic recovery.

    Thread-safe via a re-entrant lock.

    Usage::

        cb = CircuitBreaker()
        cb.record_failure("tx")
        if cb.is_available("tx"):
            ...  # proceed
        cb.record_success("tx")   # reset counter
    """

    def __init__(
        self,
        *,
        failure_threshold: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
        failure_window_seconds: Optional[int] = None,
    ) -> None:
        """Initialise the circuit breaker.

        Args:
            failure_threshold: Consecutive failures to trigger degradation
                               (default from ``config.circuit_breaker_failure_threshold``).
            cooldown_seconds: Seconds to wait before probing recovery
                              (default from ``config.circuit_breaker_cooldown``).
            failure_window_seconds: Rolling window for counting failures
                                    (default from ``config.circuit_breaker_failure_window``).
        """
        self._threshold: int = failure_threshold if failure_threshold is not None else settings.circuit_breaker_failure_threshold
        self._cooldown: int = cooldown_seconds if cooldown_seconds is not None else settings.circuit_breaker_cooldown
        self._window: int = failure_window_seconds if failure_window_seconds is not None else settings.circuit_breaker_failure_window

        # Per-source state: {source_name: {"failures": int, "degraded_since": datetime|None, "timestamps": list[datetime]}}
        self._state: dict[str, dict] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_success(self, source: str) -> None:
        """Reset the failure counter for *source* to zero."""
        with self._lock:
            entry = self._state.get(source)
            if entry:
                entry["failures"] = 0
                entry["degraded_since"] = None
                entry["timestamps"].clear()
                logger.info("CircuitBreaker: source=%s reset to available", source)

    def record_failure(self, source: str) -> None:
        """Record a failure for *source*.  May trigger degradation."""
        now = datetime.now(timezone.utc)

        with self._lock:
            entry = self._state.setdefault(source, {
                "failures": 0,
                "degraded_since": None,
                "timestamps": [],
            })

            # Trim timestamps outside the rolling window
            cutoff = now - timedelta(seconds=self._window)
            entry["timestamps"] = [ts for ts in entry["timestamps"] if ts > cutoff]
            entry["timestamps"].append(now)

            # Count failures within the window
            entry["failures"] = len(entry["timestamps"])

            if entry["failures"] >= self._threshold and entry["degraded_since"] is None:
                entry["degraded_since"] = now
                logger.warning(
                    "CircuitBreaker: source=%s DEGRADED (failures=%d, threshold=%d)",
                    source, entry["failures"], self._threshold,
                )

    def is_available(self, source: str) -> bool:
        """Return True if *source* is currently considered healthy.

        A degraded source may recover after the cooldown period.
        """
        with self._lock:
            entry = self._state.get(source)
            if entry is None:
                return True  # No failures recorded → available

            if entry["degraded_since"] is None:
                return True

            # Check cooldown
            elapsed = (datetime.now(timezone.utc) - entry["degraded_since"]).total_seconds()
            if elapsed >= self._cooldown:
                # Auto-recover: reset on next probe
                logger.info(
                    "CircuitBreaker: source=%s cooldown elapsed, resetting to available",
                    source,
                )
                entry["failures"] = 0
                entry["degraded_since"] = None
                entry["timestamps"].clear()
                return True

            return False

    def get_status(self, source: str) -> SourceStatus:
        """Return the current ``SourceStatus`` for a source."""
        with self._lock:
            entry = self._state.get(source)
            if entry is None or entry["failures"] == 0:
                return SourceStatus.AVAILABLE
            if entry["degraded_since"] is not None:
                elapsed = (datetime.now(timezone.utc) - entry["degraded_since"]).total_seconds()
                if elapsed >= self._cooldown:
                    return SourceStatus.AVAILABLE  # Cooldown passed
                return SourceStatus.DEGRADED
            # Some failures but not yet degraded
            return SourceStatus.AVAILABLE

    def get_failure_count(self, source: str) -> int:
        """Return the number of failures in the rolling window."""
        with self._lock:
            entry = self._state.get(source)
            return entry["failures"] if entry else 0

    def degraded_since(self, source: str) -> Optional[datetime]:
        """Return when *source* was degraded, or None."""
        with self._lock:
            entry = self._state.get(source)
            return entry["degraded_since"] if entry else None

    def reset(self, source: Optional[str] = None) -> None:
        """Reset circuit breaker state.

        Args:
            source: Specific source to reset, or None to reset all.
        """
        with self._lock:
            if source:
                self._state.pop(source, None)
            else:
                self._state.clear()
