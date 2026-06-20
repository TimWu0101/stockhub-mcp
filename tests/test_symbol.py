"""
Test B: Symbol Normalization & Resolution (Round 1).

Tests:
  - SymbolResolver: code-based, name-based, pinyin, ambiguity
  - SymbolNormalizer: to_tencent, to_eastmoney, to_yfinance, to_sina, to_akshare
  - StandardSymbol: to_internal / from_internal
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer


class TestStandardSymbol(unittest.TestCase):
    """Test StandardSymbol dataclass."""

    def test_to_internal_cn(self):
        """CN:600519 → 'CN:600519'."""
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        sym = StandardSymbol(market=Market.CN, code="600519")
        self.assertEqual(sym.to_internal(), "CN:600519")

    def test_to_internal_us(self):
        """US:AAPL → 'US:AAPL'."""
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        sym = StandardSymbol(market=Market.US, code="AAPL")
        self.assertEqual(sym.to_internal(), "US:AAPL")

    def test_to_internal_hk(self):
        """HK:00700 → 'HK:00700'."""
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        sym = StandardSymbol(market=Market.HK, code="00700")
        self.assertEqual(sym.to_internal(), "HK:00700")

    def test_from_internal(self):
        """Parse 'CN:600519' back to StandardSymbol."""
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        sym = StandardSymbol.from_internal("CN:600519")
        self.assertEqual(sym.market, Market.CN)
        self.assertEqual(sym.code, "600519")

    def test_from_internal_us(self):
        """Parse 'US:AAPL' back to StandardSymbol."""
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        sym = StandardSymbol.from_internal("US:AAPL")
        self.assertEqual(sym.market, Market.US)
        self.assertEqual(sym.code, "AAPL")

    def test_immutable(self):
        """StandardSymbol is frozen (immutable)."""
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        sym = StandardSymbol(market=Market.CN, code="600519")
        with self.assertRaises(Exception):
            sym.code = "000001"  # type: ignore[misc]


class TestSymbolResolver(unittest.TestCase):
    """Test SymbolResolver: user input → StandardSymbol."""

    @classmethod
    def setUpClass(cls):
        from stockhub_mcp.domain.symbol.resolver import SymbolResolver
        cls.resolver = SymbolResolver()

    # --- Code-based resolution ---

    def test_resolve_cn_code_600519(self):
        """600519 → CN:600519."""
        result = self.resolver.resolve("600519")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.market.value, "CN")
        self.assertEqual(result.symbol.code, "600519")

    def test_resolve_cn_code_with_sh_prefix(self):
        """sh600519 → CN:600519 (prefix stripped)."""
        result = self.resolver.resolve("sh600519")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.market.value, "CN")
        self.assertEqual(result.symbol.code, "600519")

    def test_resolve_cn_code_with_sz_prefix(self):
        """sz000001 → CN:000001."""
        result = self.resolver.resolve("sz000001")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.market.value, "CN")
        self.assertEqual(result.symbol.code, "000001")

    def test_resolve_us_code_aapl(self):
        """AAPL → US:AAPL."""
        result = self.resolver.resolve("AAPL")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.market.value, "US")
        self.assertEqual(result.symbol.code, "AAPL")

    def test_resolve_hk_code_00700(self):
        """00700 → HK:00700."""
        result = self.resolver.resolve("00700")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.market.value, "HK")
        self.assertEqual(result.symbol.code, "00700")

    # --- Name-based resolution ---

    def test_resolve_name_guizhoumaotai(self):
        """贵州茅台 → CN:600519."""
        result = self.resolver.resolve("贵州茅台")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.market.value, "CN")
        self.assertEqual(result.symbol.code, "600519")

    def test_resolve_name_pingan(self):
        """'银行' should return candidates (ambiguous)."""
        result = self.resolver.resolve("银行")
        self.assertFalse(result.resolved)
        self.assertGreater(len(result.candidates), 0)
        # All candidates should contain '银行' in name
        for c in result.candidates:
            self.assertIn("银行", c.name)

    def test_resolve_pinyin(self):
        """maotai → should find 贵州茅台."""
        result = self.resolver.resolve("maotai")
        self.assertTrue(result.resolved)
        self.assertEqual(result.symbol.code, "600519")

    def test_resolve_empty_input(self):
        """Empty input → not resolved."""
        result = self.resolver.resolve("")
        self.assertFalse(result.resolved)

    def test_resolve_whitespace_input(self):
        """Whitespace-only input → not resolved."""
        result = self.resolver.resolve("   ")
        self.assertFalse(result.resolved)

    # --- Preferred market ---

    def test_resolve_with_preferred_market(self):
        """With preferred_market=Market.HK, '银行' only matches HK."""
        from stockhub_mcp.enums import Market
        result = self.resolver.resolve("银行", preferred_market=Market.HK)
        # HK market only has 招商银行, but "银行" substring also matches some CN ones
        # Actually there may be no HK stocks with "银行" in the hardcoded HK list
        # Let's verify: HK list has 香港交易所, etc. - no bank stocks
        if result.candidates:
            for c in result.candidates:
                self.assertEqual(c.symbol.market, Market.HK)

    # --- search() method ---

    def test_search_returns_results(self):
        """search() returns a list of candidates."""
        results = self.resolver.search("茅台")
        self.assertGreater(len(results), 0)

    def test_search_max_results(self):
        """search() respects max_results."""
        results = self.resolver.search("银行", max_results=3)
        self.assertLessEqual(len(results), 3)


class TestSymbolNormalizer(unittest.TestCase):
    """Test SymbolNormalizer: StandardSymbol → source-specific format."""

    @classmethod
    def setUpClass(cls):
        from stockhub_mcp.domain.symbol.normalizer import SymbolNormalizer
        cls.normalizer = SymbolNormalizer()

    def _make_cn(self, code):
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        return StandardSymbol(market=Market.CN, code=code)

    def _make_hk(self, code):
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        return StandardSymbol(market=Market.HK, code=code)

    def _make_us(self, code):
        from stockhub_mcp.domain.symbol.resolver import StandardSymbol
        from stockhub_mcp.enums import Market
        return StandardSymbol(market=Market.US, code=code)

    # --- Tencent ---

    def test_tencent_cn_600519(self):
        """CN:600519 → sh600519."""
        result = SymbolNormalizer.to_tencent(self._make_cn("600519"))
        self.assertEqual(result, "sh600519")

    def test_tencent_cn_000001(self):
        """CN:000001 → sz000001."""
        result = SymbolNormalizer.to_tencent(self._make_cn("000001"))
        self.assertEqual(result, "sz000001")

    def test_tencent_hk_00700(self):
        """HK:00700 → hk00700."""
        result = SymbolNormalizer.to_tencent(self._make_hk("00700"))
        self.assertEqual(result, "hk00700")

    def test_tencent_us_raises(self):
        """Tencent does not support US market."""
        with self.assertRaises(ValueError):
            SymbolNormalizer.to_tencent(self._make_us("AAPL"))

    # --- EastMoney ---

    def test_eastmoney_cn_600519(self):
        """CN:600519 → 1.600519 (SSE)."""
        result = SymbolNormalizer.to_eastmoney(self._make_cn("600519"))
        self.assertEqual(result, "1.600519")

    def test_eastmoney_cn_000858(self):
        """CN:000858 → 0.000858 (SZSE)."""
        result = SymbolNormalizer.to_eastmoney(self._make_cn("000858"))
        self.assertEqual(result, "0.000858")

    def test_eastmoney_hk_raises(self):
        """EastMoney does not support HK."""
        with self.assertRaises(ValueError):
            SymbolNormalizer.to_eastmoney(self._make_hk("00700"))

    # --- Yahoo Finance ---

    def test_yfinance_cn_600519(self):
        """CN:600519 → 600519.SS."""
        result = SymbolNormalizer.to_yfinance(self._make_cn("600519"))
        self.assertEqual(result, "600519.SS")

    def test_yfinance_cn_000858(self):
        """CN:000858 → 000858.SZ."""
        result = SymbolNormalizer.to_yfinance(self._make_cn("000858"))
        self.assertEqual(result, "000858.SZ")

    def test_yfinance_hk_00700(self):
        """HK:00700 → 700.HK (leading zeros stripped)."""
        result = SymbolNormalizer.to_yfinance(self._make_hk("00700"))
        self.assertEqual(result, "700.HK")

    def test_yfinance_us_aapl(self):
        """US:AAPL → AAPL."""
        result = SymbolNormalizer.to_yfinance(self._make_us("AAPL"))
        self.assertEqual(result, "AAPL")

    # --- Sina ---

    def test_sina_cn_600519(self):
        """CN:600519 → sh600519."""
        result = SymbolNormalizer.to_sina(self._make_cn("600519"))
        self.assertEqual(result, "sh600519")

    def test_sina_us_raises(self):
        """Sina does not support US."""
        with self.assertRaises(ValueError):
            SymbolNormalizer.to_sina(self._make_us("AAPL"))

    # --- akshare ---

    def test_akshare_cn_600519(self):
        """CN:600519 → sh600519."""
        result = SymbolNormalizer.to_akshare(self._make_cn("600519"))
        self.assertEqual(result, "sh600519")

    def test_akshare_hk_00700(self):
        """HK:00700 → 00700 (passthrough)."""
        result = SymbolNormalizer.to_akshare(self._make_hk("00700"))
        self.assertEqual(result, "00700")

    def test_akshare_us_raises(self):
        """akshare does not support US."""
        with self.assertRaises(ValueError):
            SymbolNormalizer.to_akshare(self._make_us("AAPL"))

    # --- normalize() dispatcher ---

    def test_normalize_dispatch_tx(self):
        """normalize(CN:600519, 'tx') → sh600519."""
        result = SymbolNormalizer.normalize(self._make_cn("600519"), "tx")
        self.assertEqual(result, "sh600519")

    def test_normalize_dispatch_eastmoney(self):
        """normalize(CN:600519, 'eastmoney') → 1.600519."""
        result = SymbolNormalizer.normalize(self._make_cn("600519"), "eastmoney")
        self.assertEqual(result, "1.600519")

    def test_normalize_dispatch_yfinance(self):
        """normalize(CN:600519, 'yfinance') → 600519.SS."""
        result = SymbolNormalizer.normalize(self._make_cn("600519"), "yfinance")
        self.assertEqual(result, "600519.SS")

    def test_normalize_unknown_source_raises(self):
        """normalize() with unknown source raises ValueError."""
        with self.assertRaises(ValueError):
            SymbolNormalizer.normalize(self._make_cn("600519"), "unknown_source")

    # --- SSE vs SZSE detection ---

    def test_sse_codes(self):
        """Codes starting with 5,6,9 are SSE."""
        sse_codes = ["600519", "500001", "900001", "688981"]
        for code in sse_codes:
            with self.subTest(code=code):
                result = SymbolNormalizer.to_tencent(self._make_cn(code))
                self.assertTrue(result.startswith("sh"),
                                f"Expected sh prefix for SSE code {code}")

    def test_szse_codes(self):
        """Codes starting with 0,2,3 are SZSE."""
        szse_codes = ["000001", "000858", "002415", "300750"]
        for code in szse_codes:
            with self.subTest(code=code):
                result = SymbolNormalizer.to_tencent(self._make_cn(code))
                self.assertTrue(result.startswith("sz"),
                                f"Expected sz prefix for SZSE code {code}")


if __name__ == "__main__":
    unittest.main()
