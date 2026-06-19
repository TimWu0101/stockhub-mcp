"""
Test A: Enumerations & Configuration (Round 1).

Tests:
  - Market/InstrumentType/MarketSession/DataSource/QualityFlag enum values
  - Config reads CACHE_MAX_SIZE etc. from env
"""

import os
import sys
import unittest

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestEnums(unittest.TestCase):
    """Test all enumeration definitions."""

    def test_market_values(self):
        """Market enum must have CN, HK, US values."""
        from market_data_mcp.enums import Market
        self.assertEqual(Market.CN.value, "CN")
        self.assertEqual(Market.HK.value, "HK")
        self.assertEqual(Market.US.value, "US")
        self.assertNotEqual(Market.CN, Market.HK)
        self.assertNotEqual(Market.HK, Market.US)

    def test_instrument_type_values(self):
        """InstrumentType must have stock/etf/index/fund/future."""
        from market_data_mcp.enums import InstrumentType
        self.assertEqual(InstrumentType.STOCK.value, "stock")
        self.assertEqual(InstrumentType.ETF.value, "etf")
        self.assertEqual(InstrumentType.INDEX.value, "index")
        self.assertEqual(InstrumentType.FUND.value, "fund")
        self.assertEqual(InstrumentType.FUTURE.value, "future")

    def test_market_session_values(self):
        """MarketSession must have all trading phases."""
        from market_data_mcp.enums import MarketSession
        self.assertEqual(MarketSession.PRE_OPENING.value, "pre_opening")
        self.assertEqual(MarketSession.CONTINUOUS.value, "continuous")
        self.assertEqual(MarketSession.LUNCH_BREAK.value, "lunch_break")
        self.assertEqual(MarketSession.AUCTION.value, "auction")
        self.assertEqual(MarketSession.POST_CLOSE.value, "post_close")
        self.assertEqual(MarketSession.CLOSED.value, "closed")
        self.assertEqual(MarketSession.UNKNOWN.value, "unknown")

    def test_data_source_values(self):
        """DataSource must have yfinance/tx/sina/eastmoney/akshare/tushare/computed."""
        from market_data_mcp.enums import DataSource
        self.assertEqual(DataSource.YFINANCE.value, "yfinance")
        self.assertEqual(DataSource.TX.value, "tx")
        self.assertEqual(DataSource.SINA.value, "sina")
        self.assertEqual(DataSource.EASTMONEY.value, "eastmoney")
        self.assertEqual(DataSource.AKSHARE.value, "akshare")
        self.assertEqual(DataSource.TUSHARE.value, "tushare")
        self.assertEqual(DataSource.COMPUTED.value, "computed")

    def test_quality_flag_values(self):
        """QualityFlag must have live/delayed/stale/fallback/etc."""
        from market_data_mcp.enums import QualityFlag
        self.assertEqual(QualityFlag.LIVE.value, "live")
        self.assertEqual(QualityFlag.DELAYED.value, "delayed")
        self.assertEqual(QualityFlag.STALE.value, "stale")
        self.assertEqual(QualityFlag.FALLBACK.value, "fallback")
        self.assertEqual(QualityFlag.FALLBACK_LOW_CONFIDENCE.value, "fallback_low_confidence")
        self.assertEqual(QualityFlag.ESTIMATED.value, "estimated")
        self.assertEqual(QualityFlag.COMPUTED.value, "computed")

    def test_str_enum_behavior(self):
        """StrEnum instances behave like strings."""
        from market_data_mcp.enums import Market, MarketSession
        self.assertEqual(str(Market.CN), "CN")
        self.assertEqual(str(MarketSession.CONTINUOUS), "continuous")
        # Can be compared to strings
        self.assertEqual(Market.CN, "CN")
        self.assertNotEqual(Market.CN, "HK")

    def test_error_type_values(self):
        """ErrorType must have input/business/source/system_error."""
        from market_data_mcp.enums import ErrorType
        self.assertEqual(ErrorType.INPUT_ERROR.value, "input_error")
        self.assertEqual(ErrorType.BUSINESS_ERROR.value, "business_error")
        self.assertEqual(ErrorType.SOURCE_ERROR.value, "source_error")
        self.assertEqual(ErrorType.SYSTEM_ERROR.value, "system_error")

    def test_source_status_values(self):
        """SourceStatus must have available/degraded/unavailable."""
        from market_data_mcp.enums import SourceStatus
        self.assertEqual(SourceStatus.AVAILABLE.value, "available")
        self.assertEqual(SourceStatus.DEGRADED.value, "degraded")
        self.assertEqual(SourceStatus.UNAVAILABLE.value, "unavailable")

    def test_cache_scope_values(self):
        """CacheScope must have symbol/market/tool/all."""
        from market_data_mcp.enums import CacheScope
        self.assertEqual(CacheScope.SYMBOL.value, "symbol")
        self.assertEqual(CacheScope.MARKET.value, "market")
        self.assertEqual(CacheScope.TOOL.value, "tool")
        self.assertEqual(CacheScope.ALL.value, "all")

    def test_adjust_type_values(self):
        """AdjustType must have none/qfq/hfq."""
        from market_data_mcp.enums import AdjustType
        self.assertEqual(AdjustType.NONE.value, "none")
        self.assertEqual(AdjustType.QFQ.value, "qfq")
        self.assertEqual(AdjustType.HFQ.value, "hfq")


class TestConfig(unittest.TestCase):
    """Test configuration loading with defaults."""

    def setUp(self):
        # Import after clearing any cached env
        import importlib
        import market_data_mcp.config
        importlib.reload(market_data_mcp.config)
        self.settings = market_data_mcp.config.settings

    def test_cache_max_size_default(self):
        """CACHE_MAX_SIZE defaults to 100."""
        self.assertEqual(self.settings.cache_max_size, 100)

    def test_request_timeout_default(self):
        """request_timeout defaults to 15."""
        self.assertEqual(self.settings.request_timeout, 15)

    def test_max_retries_default(self):
        """max_retries defaults to 2."""
        self.assertEqual(self.settings.max_retries, 2)

    def test_circuit_breaker_cooldown_default(self):
        """circuit_breaker_cooldown defaults to 300."""
        self.assertEqual(self.settings.circuit_breaker_cooldown, 300)

    def test_circuit_breaker_failure_window_default(self):
        """circuit_breaker_failure_window defaults to 60."""
        self.assertEqual(self.settings.circuit_breaker_failure_window, 60)

    def test_circuit_breaker_failure_threshold_default(self):
        """circuit_breaker_failure_threshold defaults to 3."""
        self.assertEqual(self.settings.circuit_breaker_failure_threshold, 3)

    def test_log_level_default(self):
        """log_level defaults to INFO."""
        self.assertEqual(self.settings.log_level, "INFO")

    def test_tushare_token_default_none(self):
        """tushare_token defaults to None."""
        self.assertIsNone(self.settings.tushare_token)

    def test_market_timezones_property(self):
        """market_timezones returns correct mapping."""
        tzs = self.settings.market_timezones
        self.assertEqual(tzs["CN"], "Asia/Shanghai")
        self.assertEqual(tzs["HK"], "Asia/Hong_Kong")
        self.assertEqual(tzs["US"], "America/New_York")

    def test_market_currencies_property(self):
        """market_currencies returns correct mapping."""
        cur = self.settings.market_currencies
        self.assertEqual(cur["CN"], "CNY")
        self.assertEqual(cur["HK"], "HKD")
        self.assertEqual(cur["US"], "USD")

    def test_source_priority_property(self):
        """source_priority returns correct priority lists."""
        sp = self.settings.source_priority
        self.assertEqual(sp["CN"], ["tx", "sina"])
        self.assertEqual(sp["US"], ["yfinance"])
        self.assertEqual(sp["HK"], ["yfinance"])
        self.assertIn("CN_history", sp)
        self.assertIn("CN_sector", sp)

    def test_env_override(self):
        """CACHE_MAX_SIZE can be overridden via environment variable."""
        os.environ["CACHE_MAX_SIZE"] = "50"
        import importlib
        import market_data_mcp.config
        importlib.reload(market_data_mcp.config)
        new_settings = market_data_mcp.config.settings
        self.assertEqual(new_settings.cache_max_size, 50)
        # Clean up
        del os.environ["CACHE_MAX_SIZE"]


if __name__ == "__main__":
    unittest.main()
