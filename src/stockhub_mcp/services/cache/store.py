"""FIFOCacheStore: in-memory FIFO cache backed by OrderedDict.

Capacity is read from ``config.cache_max_size`` (default 100).
When full, the oldest entry is evicted first (FIFO).

Every entry is a dict::

    {
        "value": <any>,
        "expires_at": <datetime or None>,
        "cached_at": <datetime>,
    }
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Optional

from stockhub_mcp.config import settings

logger = logging.getLogger(__name__)


class FIFOCacheStore:
    """Thread-safe in-memory FIFO cache.

    Usage::

        store = FIFOCacheStore()
        store.set("quote:CN:stock:600519:tx", quote_data, expires_at=future_dt)
        entry = store.get("quote:CN:stock:600519:tx")
    """

    def __init__(self, max_size: Optional[int] = None) -> None:
        """Initialise the cache.

        Args:
            max_size: Maximum entries (default from ``config.cache_max_size``).
        """
        self._max_size: int = max_size if max_size is not None else settings.cache_max_size
        self._store: OrderedDict[str, dict[str, Any]] = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Return the cache entry for *key*, or None if missing / expired.

        Does NOT evict expired entries at read time (expiry is checked
        by the caller / policy layer).  Returns the raw entry dict.
        """
        return self._store.get(key)

    def set(
        self,
        key: str,
        value: Any,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Store *value* under *key* with an optional absolute expiry.

        If the store is at capacity the oldest entry is evicted (FIFO).
        """
        # Evict if at capacity and inserting a new key
        if key not in self._store and len(self._store) >= self._max_size:
            evicted_key, _ = self._store.popitem(last=False)
            logger.debug("FIFO eviction: key=%s", evicted_key)

        now = datetime.now(timezone.utc)
        self._store[key] = {
            "value": value,
            "expires_at": expires_at,
            "cached_at": now,
        }
        # Move to end to maintain insertion order correctly
        self._store.move_to_end(key, last=True)

    def delete(self, keys: list[str]) -> int:
        """Delete entries whose key is in *keys*.  Return count deleted."""
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count

    def match(self, pattern: str) -> list[str]:
        """Return keys that contain *pattern* as a substring.

        Args:
            pattern: Substring to match against cache keys.

        Returns:
            List of matching keys (may be empty).
        """
        return [k for k in self._store if pattern in k]

    def clear(self) -> int:
        """Remove all entries.  Return count of entries removed."""
        count = len(self._store)
        self._store.clear()
        logger.debug("Cache cleared: removed %d entries", count)
        return count

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Current number of entries."""
        return len(self._store)

    @property
    def max_size(self) -> int:
        """Configured maximum capacity."""
        return self._max_size

    def keys(self) -> list[str]:
        """Return all cache keys (for debugging)."""
        return list(self._store.keys())

    def expired_keys(self) -> list[str]:
        """Return keys whose ``expires_at`` is in the past."""
        now = datetime.now(timezone.utc)
        expired: list[str] = []
        for key, entry in self._store.items():
            expires = entry.get("expires_at")
            if expires is not None and expires <= now:
                expired.append(key)
        return expired
