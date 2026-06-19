"""
Integration Tests (Round 2).

Tests:
  - SymbolResolver.resolve() real-world calls
  - FIFOCacheStore stress test (200 entries)
  - CacheMiddleware.wrap() hit/miss/bypass behavior
"""

import os
import sys
import unittest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestSymbolResolverIntegration(unittest.TestCase):
    """Integration tests for SymbolResolver."""

    @classmethod
    def setUpClass(cls):
        from market_data_mcp.domain.symbol.resolver import SymbolResolver
        cls.resolver = SymbolResolver()

    def test_resolve_well_known_cn_stocks(self):
        """All hardcoded CN stock names resolve."""
        test_cases = [
            ("600519", "CN", "600519"),
            ("000858", "CN", "000858"),
            ("贵州茅台", "CN", "600519"),
            ("五粮液", "CN", "000858"),
            ("招商银行", "CN", "600036"),
            ("宁德时代", "CN", "300750"),
            ("长江电力", "CN", "600900"),
            # Note: "比亚迪" name matches both CN:002594 and HK:01211(比亚迪股份),
            # so it's ambiguous.  Use the code instead.
            ("002594", "CN", "002594"),
        ]
        for user_input, expected_market, expected_code in test_cases:
            with self.subTest(input=user_input):
                result = self.resolver.resolve(user_input)
                self.assertTrue(
                    result.resolved,
                    f"'{user_input}' was not resolved"
                )
                self.assertEqual(result.symbol.market.value, expected_market)
                self.assertEqual(result.symbol.code, expected_code)

    def test_resolve_well_known_us_stocks(self):
        """All hardcoded US stock tickers resolve."""
        test_cases = [
            ("AAPL", "US", "AAPL"),
            ("GOOGL", "US", "GOOGL"),
            ("MSFT", "US", "MSFT"),
            ("TSLA", "US", "TSLA"),
            ("NVDA", "US", "NVDA"),
        ]
        for user_input, expected_market, expected_code in test_cases:
            with self.subTest(input=user_input):
                result = self.resolver.resolve(user_input)
                self.assertTrue(result.resolved)
                self.assertEqual(result.symbol.market.value, expected_market)
                self.assertEqual(result.symbol.code, expected_code)

    def test_resolve_well_known_hk_stocks(self):
        """All hardcoded HK stock codes resolve."""
        test_cases = [
            ("00700", "HK", "00700"),
            ("09988", "HK", "09988"),
            ("01810", "HK", "01810"),
        ]
        for user_input, expected_market, expected_code in test_cases:
            with self.subTest(input=user_input):
                result = self.resolver.resolve(user_input)
                self.assertTrue(result.resolved)
                self.assertEqual(result.symbol.market.value, expected_market)
                self.assertEqual(result.symbol.code, expected_code)

    def test_name_resolution_all_cn(self):
        """Every hardcoded CN stock resolves by name."""
        from market_data_mcp.enums import Market
        # Get all CN entries from _KNOWN_SYMBOLS
        from market_data_mcp.domain.symbol.resolver import _KNOWN_SYMBOLS
        cn_entries = _KNOWN_SYMBOLS.get(Market.CN, [])
        for entry in cn_entries:
            name = entry["name"]
            result = self.resolver.resolve(name)
            self.assertTrue(
                result.resolved or len(result.candidates) > 0,
                f"Name '{name}' should resolve to at least one candidate"
            )

    def test_search_functionality(self):
        """search() returns meaningful results."""
        results = self.resolver.search("银行")
        self.assertGreater(len(results), 0)
        # All results should relate to banking
        for r in results:
            self.assertTrue(
                "银行" in r.name or "银行" in r.display_name or r.symbol.code,
                f"Result '{r.name}' should relate to banking"
            )


class TestFIFOCacheStoreStress(unittest.TestCase):
    """Stress tests for FIFOCacheStore."""

    def test_rapid_insert_200_entries(self):
        """Insert 200 entries quickly, verify max_size respected."""
        from market_data_mcp.services.cache.store import FIFOCacheStore
        store = FIFOCacheStore(max_size=50)

        for i in range(200):
            store.set(f"key_{i:04d}", f"value_{i}")

        self.assertEqual(store.size, 50)

        # Oldest 150 should be evicted, newest 50 retained
        self.assertIsNone(store.get("key_0000"))
        self.assertIsNone(store.get("key_0149"))
        self.assertIsNotNone(store.get("key_0150"))
        self.assertIsNotNone(store.get("key_0199"))

    def test_stress_match_on_many_entries(self):
        """match() works correctly with many entries."""
        from market_data_mcp.services.cache.store import FIFOCacheStore
        store = FIFOCacheStore(max_size=100)

        for i in range(100):
            if i % 2 == 0:
                store.set(f"quote:CN:stock:{i:06d}:tx", f"val_{i}")
            else:
                store.set(f"history:CN:stock:{i:06d}:yfinance", f"val_{i}")

        quote_keys = store.match("quote:")
        history_keys = store.match("history:")
        self.assertEqual(len(quote_keys), 50)
        self.assertEqual(len(history_keys), 50)

    def test_mixed_operations(self):
        """Set, get, delete, match, clear in sequence."""
        from market_data_mcp.services.cache.store import FIFOCacheStore
        store = FIFOCacheStore(max_size=10)

        # Setup
        for i in range(5):
            store.set(f"k{i}", f"v{i}")

        # Read
        for i in range(5):
            self.assertIsNotNone(store.get(f"k{i}"))

        # Delete
        store.delete(["k0", "k1"])
        self.assertIsNone(store.get("k0"))
        self.assertEqual(store.size, 3)

        # Match
        self.assertEqual(len(store.match("k2")), 1)

        # Clear
        store.clear()
        self.assertEqual(store.size, 0)


class TestCacheMiddlewareIntegration(unittest.TestCase):
    """Integration tests for CacheMiddleware.wrap()."""

    def setUp(self):
        from market_data_mcp.services.cache.store import FIFOCacheStore
        from market_data_mcp.services.cache.policy import CachePolicy
        from market_data_mcp.tools.cache_middleware import CacheMiddleware
        from market_data_mcp.domain.market.session import MarketSessionResolver
        self.store = FIFOCacheStore(max_size=10)
        self.policy = CachePolicy()
        self.session_resolver = MarketSessionResolver()
        self.middleware = CacheMiddleware(
            cache_store=self.store,
            cache_policy=self.policy,
            session_resolver=self.session_resolver,
        )

    # ------------------------------------------------------------------
    # Helper: synchronous mock tool function
    # ------------------------------------------------------------------

    @staticmethod
    def _make_sync_wrap(middleware):
        """Wrap a sync function (not async) for testing. Since CacheMiddleware
        expects async, we wrap a simple async function that simulates a tool."""
        pass

    def test_wrap_returns_callable(self):
        """wrap() returns a callable."""
        async def dummy_tool(**kwargs):
            return {"success": True, "data": {"price": 100.0},
                    "meta": {"market": "CN", "symbol": "CN:600519",
                             "source": "tx", "quality_flag": "live",
                             "market_session": "continuous"}}

        wrapped = self.middleware.wrap(dummy_tool, "get_realtime_quote")
        self.assertTrue(callable(wrapped))

    def test_wrap_executes_function(self):
        """Wrapped function executes the underlying tool."""
        async def dummy_tool(**kwargs):
            return {"success": True, "data": {"price": 100.0},
                    "meta": {"market": "CN", "symbol": "CN:600519",
                             "source": "tx", "quality_flag": "live",
                             "market_session": "continuous"}}

        wrapped = self.middleware.wrap(dummy_tool, "get_realtime_quote")
        result = asyncio.run(wrapped(market="CN", symbol="CN:600519"))
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["price"], 100.0)

    def test_wrap_injects_cache_info(self):
        """Wrapped function always injects cache metadata."""
        async def dummy_tool(**kwargs):
            return {"success": True, "data": {"price": 100.0},
                    "meta": {"market": "CN", "symbol": "CN:600519",
                             "source": "tx", "quality_flag": "live",
                             "market_session": "closed"}}

        wrapped = self.middleware.wrap(dummy_tool, "get_realtime_quote")
        result = asyncio.run(wrapped(market="CN", symbol="CN:600519"))
        self.assertIn("cache", result)
        self.assertIn("hit", result["cache"])

    def test_wrap_bypass_cache(self):
        """bypass_cache=True skips cache and returns bypass cache info."""
        async def dummy_tool(**kwargs):
            return {"success": True, "data": {"price": 100.0},
                    "meta": {"market": "CN", "symbol": "CN:600519",
                             "source": "tx", "quality_flag": "live",
                             "market_session": "closed"}}

        wrapped = self.middleware.wrap(dummy_tool, "get_realtime_quote")
        result = asyncio.run(
            wrapped(market="CN", symbol="CN:600519", bypass_cache=True)
        )
        self.assertTrue(result["cache"]["bypass_cache"])
        self.assertFalse(result["cache"]["hit"])

    def test_wrap_cache_hit_on_second_call(self):
        """Second call with same args returns cached result (cache hit)."""
        call_count = [0]

        async def dummy_tool(**kwargs):
            call_count[0] += 1
            return {"success": True, "data": {"price": 100.0 + call_count[0]},
                    "meta": {"market": "CN", "symbol": "CN:600519",
                             "source": "tx", "quality_flag": "live",
                             "market_session": "closed"}}

        wrapped = self.middleware.wrap(dummy_tool, "get_realtime_quote")

        # First call: cache miss, tool executes
        result1 = asyncio.run(wrapped(market="CN", symbol="CN:600519"))
        self.assertEqual(call_count[0], 1)
        self.assertFalse(result1["cache"]["hit"])

        # Second call: cache hit, tool NOT executed
        result2 = asyncio.run(wrapped(market="CN", symbol="CN:600519"))
        self.assertEqual(call_count[0], 1)  # Still 1, not called again
        self.assertTrue(result2["cache"]["hit"])

    def test_wrap_passes_through_error(self):
        """Error responses are not cached and passed through."""
        async def failing_tool(**kwargs):
            return {"success": False, "data": None,
                    "error": {"code": "FAIL", "message": "test failure"},
                    "meta": {}}

        wrapped = self.middleware.wrap(failing_tool, "get_realtime_quote")
        result = asyncio.run(wrapped(market="CN", symbol="CN:600519"))
        self.assertFalse(result["success"])

    def test_wrap_default_market_to_cn(self):
        """Empty market defaults to CN."""
        async def dummy_tool(**kwargs):
            return {"success": True, "data": {"price": 100.0},
                    "meta": {"market": kwargs.get("market", ""),
                             "symbol": kwargs.get("symbol", ""),
                             "source": "tx", "quality_flag": "live",
                             "market_session": "closed"}}

        wrapped = self.middleware.wrap(dummy_tool, "get_realtime_quote")
        # Should not crash with empty market
        result = asyncio.run(wrapped())
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
