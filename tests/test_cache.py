"""
Test D+E: FIFO Cache Store & CachePolicy (Round 1).

Tests:
  - FIFOCacheStore: set/get, capacity eviction, clear, match
  - CachePolicy: should_cache during trading/lunch/low_quality/bypass
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestFIFOCacheStore(unittest.TestCase):
    """Test FIFOCacheStore in-memory FIFO cache."""

    def setUp(self):
        from stockhub_mcp.services.cache.store import FIFOCacheStore
        self.store = FIFOCacheStore(max_size=3)

    # --- Basic read/write ---

    def test_set_and_get(self):
        """set() then get() returns the stored entry."""
        self.store.set("key1", {"price": 100.0})
        entry = self.store.get("key1")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["value"]["price"], 100.0)

    def test_get_missing_key(self):
        """get() on missing key returns None."""
        entry = self.store.get("nonexistent")
        self.assertIsNone(entry)

    def test_set_overwrites_existing(self):
        """set() on existing key overwrites value."""
        self.store.set("key1", {"price": 100.0})
        self.store.set("key1", {"price": 200.0})
        entry = self.store.get("key1")
        self.assertEqual(entry["value"]["price"], 200.0)

    # --- Expiry ---

    def test_expires_at_stored(self):
        """expires_at is stored with the entry."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        self.store.set("key1", "value", expires_at=future)
        entry = self.store.get("key1")
        self.assertEqual(entry["expires_at"], future)

    def test_cached_at_is_utc(self):
        """cached_at is always a UTC datetime."""
        self.store.set("key1", "value")
        entry = self.store.get("key1")
        self.assertIsInstance(entry["cached_at"], datetime)
        self.assertEqual(entry["cached_at"].tzinfo, timezone.utc)

    # --- FIFO eviction ---

    def test_fifo_eviction_when_full(self):
        """When max_size=3, inserting 4th entry evicts the oldest."""
        self.store.set("key1", "val1")
        self.store.set("key2", "val2")
        self.store.set("key3", "val3")
        self.store.set("key4", "val4")

        self.assertEqual(self.store.size, 3)
        # Oldest (key1) should be evicted
        self.assertIsNone(self.store.get("key1"))
        # Newer entries retained
        self.assertIsNotNone(self.store.get("key2"))
        self.assertIsNotNone(self.store.get("key3"))
        self.assertIsNotNone(self.store.get("key4"))

    def test_no_eviction_when_updating_existing(self):
        """Updating an existing key does NOT evict."""
        self.store.set("key1", "val1")
        self.store.set("key2", "val2")
        self.store.set("key3", "val3")
        self.store.set("key1", "val1_updated")  # Overwrite, not new key

        self.assertEqual(self.store.size, 3)
        self.assertIsNotNone(self.store.get("key1"))
        self.assertIsNotNone(self.store.get("key2"))
        self.assertIsNotNone(self.store.get("key3"))

    def test_fifo_order_maintained_after_update(self):
        """After updating key1, key2 is still the oldest for eviction."""
        self.store.set("key1", "val1")
        self.store.set("key2", "val2")
        self.store.set("key3", "val3")
        self.store.set("key1", "val1_updated")  # Moves key1 to end
        self.store.set("key4", "val4")  # Should evict key2

        self.assertEqual(self.store.size, 3)
        self.assertIsNone(self.store.get("key2"))  # key2 was oldest
        self.assertIsNotNone(self.store.get("key1"))
        self.assertIsNotNone(self.store.get("key3"))
        self.assertIsNotNone(self.store.get("key4"))

    # --- clear() ---

    def test_clear_removes_all(self):
        """clear() removes all entries and returns count."""
        self.store.set("a", 1)
        self.store.set("b", 2)
        self.store.set("c", 3)

        count = self.store.clear()
        self.assertEqual(count, 3)
        self.assertEqual(self.store.size, 0)
        self.assertIsNone(self.store.get("a"))
        self.assertIsNone(self.store.get("b"))
        self.assertIsNone(self.store.get("c"))

    def test_clear_empty_store(self):
        """clear() on empty store returns 0."""
        count = self.store.clear()
        self.assertEqual(count, 0)
        self.assertEqual(self.store.size, 0)

    # --- match() ---

    def test_match_substring(self):
        """match() returns keys containing the pattern."""
        # Use larger store so all 4 keys fit (default setUp has max_size=3)
        from stockhub_mcp.services.cache.store import FIFOCacheStore
        store = FIFOCacheStore(max_size=10)
        store.set("quote:CN:600519", 1)
        store.set("quote:CN:000001", 2)
        store.set("history:CN:600519", 3)
        store.set("quote:US:AAPL", 4)

        results = store.match("600519")
        self.assertEqual(len(results), 2)
        self.assertIn("quote:CN:600519", results)
        self.assertIn("history:CN:600519", results)

    def test_match_no_results(self):
        """match() returns empty list when no keys match."""
        self.store.set("quote:CN:600519", 1)
        results = self.store.match("NONEXISTENT")
        self.assertEqual(len(results), 0)

    def test_match_case_sensitive(self):
        """match() is case-sensitive substring matching."""
        self.store.set("quote:US:AAPL", 1)
        results = self.store.match("aapl")
        self.assertEqual(len(results), 0)
        results2 = self.store.match("AAPL")
        self.assertEqual(len(results2), 1)

    def test_match_on_empty_store(self):
        """match() on empty store returns empty list."""
        results = self.store.match("anything")
        self.assertEqual(results, [])

    # --- delete() ---

    def test_delete_existing_keys(self):
        """delete() removes specified keys."""
        self.store.set("key1", "val1")
        self.store.set("key2", "val2")
        self.store.set("key3", "val3")

        deleted = self.store.delete(["key1", "key3"])
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.store.get("key1"))
        self.assertIsNotNone(self.store.get("key2"))
        self.assertIsNone(self.store.get("key3"))

    def test_delete_nonexistent_keys(self):
        """delete() on nonexistent keys returns 0."""
        deleted = self.store.delete(["no_such_key"])
        self.assertEqual(deleted, 0)

    # --- Introspection ---

    def test_size_property(self):
        """size property reflects current entries."""
        self.assertEqual(self.store.size, 0)
        self.store.set("a", 1)
        self.assertEqual(self.store.size, 1)
        self.store.set("b", 2)
        self.assertEqual(self.store.size, 2)

    def test_max_size_property(self):
        """max_size property reflects configured max."""
        self.assertEqual(self.store.max_size, 3)

    def test_keys_method(self):
        """keys() returns all cache keys."""
        self.store.set("a", 1)
        self.store.set("b", 2)
        keys = self.store.keys()
        self.assertEqual(set(keys), {"a", "b"})

    def test_expired_keys(self):
        """expired_keys() returns keys with past expires_at."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        self.store.set("expired_key", "val", expires_at=past)
        self.store.set("valid_key", "val", expires_at=future)
        self.store.set("no_expiry_key", "val")

        expired = self.store.expired_keys()
        self.assertIn("expired_key", expired)
        self.assertNotIn("valid_key", expired)
        self.assertNotIn("no_expiry_key", expired)

    def test_default_max_size_from_config(self):
        """When max_size not specified, uses config.cache_max_size."""
        from stockhub_mcp.services.cache.store import FIFOCacheStore
        from stockhub_mcp.config import settings
        store = FIFOCacheStore()
        self.assertEqual(store.max_size, settings.cache_max_size)


# ---------------------------------------------------------------------------
# CachePolicy Tests
# ---------------------------------------------------------------------------


class TestCachePolicy(unittest.TestCase):
    """Test CachePolicy: should_cache() logic."""

    @classmethod
    def setUpClass(cls):
        from stockhub_mcp.services.cache.policy import CachePolicy
        cls.policy = CachePolicy()
        from stockhub_mcp.enums import Market, MarketSession, QualityFlag
        cls.Market = Market
        cls.MarketSession = MarketSession
        cls.QualityFlag = QualityFlag

    # --- is_trading scenarios (no cache) ---

    def test_cn_continuous_no_cache(self):
        """CN CONTINUOUS → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.CONTINUOUS, "live"
            )
        )

    def test_cn_pre_opening_no_cache(self):
        """CN PRE_OPENING → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.PRE_OPENING, "live"
            )
        )

    def test_us_continuous_no_cache(self):
        """US CONTINUOUS → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.US, self.MarketSession.CONTINUOUS, "live"
            )
        )

    # --- lunch_break → should_cache=True ---

    def test_cn_lunch_break_cache_allowed(self):
        """CN LUNCH_BREAK → should_cache=True."""
        self.assertTrue(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.LUNCH_BREAK, "live"
            )
        )

    def test_hk_lunch_break_cache_allowed(self):
        """HK LUNCH_BREAK → should_cache=True."""
        self.assertTrue(
            self.policy.should_cache(
                self.Market.HK, self.MarketSession.LUNCH_BREAK, "live"
            )
        )

    # --- Low quality flag → no cache ---

    def test_stale_no_cache(self):
        """STALE quality → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.LUNCH_BREAK, "stale"
            )
        )

    def test_delayed_no_cache(self):
        """DELAYED quality → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.LUNCH_BREAK, "delayed"
            )
        )

    def test_fallback_low_confidence_no_cache(self):
        """FALLBACK_LOW_CONFIDENCE → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.LUNCH_BREAK,
                "fallback_low_confidence"
            )
        )

    def test_fallback_quality_can_cache(self):
        """FALLBACK (not low confidence) → should_cache=True."""
        self.assertTrue(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.LUNCH_BREAK, "fallback"
            )
        )

    # --- bypass_cache → no cache ---

    def test_bypass_cache_skips_cache(self):
        """bypass_cache=True → should_cache=False."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.LUNCH_BREAK, "live",
                bypass_cache=True,
            )
        )

    # --- UNKNOWN session → no cache ---

    def test_unknown_session_no_cache(self):
        """UNKNOWN session → should_cache=False (conservative)."""
        self.assertFalse(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.UNKNOWN, "live"
            )
        )

    # --- POST_CLOSE → should_cache=True ---

    def test_cn_post_close_cache_allowed(self):
        """CN POST_CLOSE → should_cache=True."""
        self.assertTrue(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.POST_CLOSE, "live"
            )
        )

    def test_us_post_close_cache_allowed(self):
        """US POST_CLOSE → should_cache=True."""
        self.assertTrue(
            self.policy.should_cache(
                self.Market.US, self.MarketSession.POST_CLOSE, "live"
            )
        )

    # --- CLOSED → should_cache=True ---

    def test_cn_closed_cache_allowed(self):
        """CN CLOSED → should_cache=True."""
        self.assertTrue(
            self.policy.should_cache(
                self.Market.CN, self.MarketSession.CLOSED, "live"
            )
        )

    # --- get_policy_name ---

    def test_get_policy_name_cn_continuous(self):
        """CN CONTINUOUS → cn_live_no_cache."""
        name = self.policy.get_policy_name(
            self.Market.CN, self.MarketSession.CONTINUOUS
        )
        self.assertEqual(name, "cn_live_no_cache")

    def test_get_policy_name_cn_lunch(self):
        """CN LUNCH_BREAK → cn_lunch_until_1300."""
        name = self.policy.get_policy_name(
            self.Market.CN, self.MarketSession.LUNCH_BREAK
        )
        self.assertEqual(name, "cn_lunch_until_1300")

    def test_get_policy_name_cn_post_close(self):
        """CN POST_CLOSE → cn_post_close_until_next_trading_day_0900."""
        name = self.policy.get_policy_name(
            self.Market.CN, self.MarketSession.POST_CLOSE
        )
        self.assertEqual(name, "cn_post_close_until_next_trading_day_0900")

    def test_get_policy_name_us_closed(self):
        """US CLOSED → us_deep_offhours_300s."""
        name = self.policy.get_policy_name(
            self.Market.US, self.MarketSession.CLOSED
        )
        self.assertEqual(name, "us_deep_offhours_300s")

    def test_get_policy_name_weekend_cn(self):
        """CN CLOSED (weekend) → weekend_until_next_trading_day_0900."""
        name = self.policy.get_policy_name(
            self.Market.CN, self.MarketSession.CLOSED
        )
        self.assertEqual(name, "weekend_until_next_trading_day_0900")

    # --- get_expiry ---

    def test_get_expiry_cn_lunch(self):
        """CN LUNCH_BREAK → expiry at next 13:00 local time."""
        expiry = self.policy.get_expiry(
            self.Market.CN, self.MarketSession.LUNCH_BREAK
        )
        self.assertIsNotNone(expiry)
        self.assertIsInstance(expiry, datetime)

    def test_get_expiry_us_post_close(self):
        """US POST_CLOSE → 10-second TTL."""
        now = datetime.now(timezone.utc)
        expiry = self.policy.get_expiry(
            self.Market.US, self.MarketSession.POST_CLOSE, now=now
        )
        self.assertIsNotNone(expiry)
        delta = (expiry - now).total_seconds()
        self.assertAlmostEqual(delta, 10, delta=1)  # within 1 sec

    def test_get_expiry_cn_continuous(self):
        """CN CONTINUOUS → None (no caching during trading)."""
        expiry = self.policy.get_expiry(
            self.Market.CN, self.MarketSession.CONTINUOUS
        )
        self.assertIsNone(expiry)

    # --- build_key ---

    def test_build_key_format(self):
        """build_key produces expected format."""
        from stockhub_mcp.services.cache.policy import CachePolicy
        key = CachePolicy.build_key(
            "get_realtime_quote", self.Market.CN,
            "stock", "CN:600519", "tx", "continuous"
        )
        self.assertIn("get_realtime_quote", key)
        self.assertIn("CN", key)
        self.assertIn("600519", key)
        self.assertIn("tx", key)

    @staticmethod
    def test_build_key_no_session():
        """build_key works without session_state."""
        from stockhub_mcp.services.cache.policy import CachePolicy
        from stockhub_mcp.enums import Market
        key = CachePolicy.build_key(
            "get_realtime_quote", Market.CN,
            "stock", "CN:600519", "tx"
        )
        assert isinstance(key, str)
        assert key.endswith(":")


if __name__ == "__main__":
    unittest.main()
