"""
Test C: Market Session Detection (Round 1).

Tests:
  - CN: 10:30 → CONTINUOUS, 12:00 → LUNCH_BREAK, is_trading logic
  - US: 10:30 ET → CONTINUOUS
  - HK: 12:30 → LUNCH_BREAK
"""

import os
import sys
import unittest
from datetime import datetime, time, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestMarketSessionResolver(unittest.TestCase):
    """Test MarketSessionResolver.detect() and is_trading()."""

    @classmethod
    def setUpClass(cls):
        from market_data_mcp.domain.market.session import MarketSessionResolver
        cls.resolver = MarketSessionResolver()
        from market_data_mcp.enums import Market, MarketSession
        cls.Market = Market
        cls.MarketSession = MarketSession

    # ------------------------------------------------------------------
    # CN (A-share) session detection
    # ------------------------------------------------------------------

    def _cn_dt(self, hour, minute, second=0):
        """Build a CN-local datetime for testing."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        today = datetime.now(tz).date()
        return datetime(today.year, today.month, today.day,
                        hour, minute, second, tzinfo=tz)

    def test_cn_pre_opening(self):
        """CN 9:15 → PRE_OPENING."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(9, 15))
        self.assertEqual(session, self.MarketSession.PRE_OPENING)

    def test_cn_continuous_morning(self):
        """CN 10:30 → CONTINUOUS."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(10, 30))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_cn_lunch_break(self):
        """CN 12:00 → LUNCH_BREAK."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(12, 0))
        self.assertEqual(session, self.MarketSession.LUNCH_BREAK)

    def test_cn_continuous_afternoon(self):
        """CN 14:00 → CONTINUOUS."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(14, 0))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_cn_post_close(self):
        """CN 15:10 → POST_CLOSE."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(15, 10))
        self.assertEqual(session, self.MarketSession.POST_CLOSE)

    def test_cn_closed(self):
        """CN 16:00 → CLOSED."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(16, 0))
        self.assertEqual(session, self.MarketSession.CLOSED)

    def test_cn_is_trading_continuous(self):
        """CN CONTINUOUS → is_trading=True."""
        self.assertTrue(
            self.resolver.is_trading(self.Market.CN, self._cn_dt(10, 30))
        )

    def test_cn_is_trading_pre_opening(self):
        """CN PRE_OPENING → is_trading=True."""
        self.assertTrue(
            self.resolver.is_trading(self.Market.CN, self._cn_dt(9, 15))
        )

    def test_cn_is_trading_lunch_break(self):
        """CN LUNCH_BREAK → is_trading=False."""
        self.assertFalse(
            self.resolver.is_trading(self.Market.CN, self._cn_dt(12, 0))
        )

    def test_cn_is_trading_post_close(self):
        """CN POST_CLOSE → is_trading=False."""
        self.assertFalse(
            self.resolver.is_trading(self.Market.CN, self._cn_dt(15, 10))
        )

    def test_cn_is_trading_closed(self):
        """CN CLOSED → is_trading=False."""
        self.assertFalse(
            self.resolver.is_trading(self.Market.CN, self._cn_dt(16, 0))
        )

    # ------------------------------------------------------------------
    # US session detection
    # ------------------------------------------------------------------

    def _us_dt(self, hour, minute, second=0):
        """Build a US-local datetime for testing."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/New_York")
        today = datetime.now(tz).date()
        return datetime(today.year, today.month, today.day,
                        hour, minute, second, tzinfo=tz)

    def test_us_pre_market(self):
        """US 8:00 ET → PRE_OPENING."""
        session = self.resolver.detect(self.Market.US, self._us_dt(8, 0))
        self.assertEqual(session, self.MarketSession.PRE_OPENING)

    def test_us_continuous(self):
        """US 10:30 ET → CONTINUOUS."""
        session = self.resolver.detect(self.Market.US, self._us_dt(10, 30))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_us_post_market(self):
        """US 17:00 ET → POST_CLOSE."""
        session = self.resolver.detect(self.Market.US, self._us_dt(17, 0))
        self.assertEqual(session, self.MarketSession.POST_CLOSE)

    def test_us_closed(self):
        """US 22:00 ET → CLOSED."""
        session = self.resolver.detect(self.Market.US, self._us_dt(22, 0))
        self.assertEqual(session, self.MarketSession.CLOSED)

    def test_us_is_trading_continuous(self):
        """US CONTINUOUS → is_trading=True."""
        self.assertTrue(
            self.resolver.is_trading(self.Market.US, self._us_dt(10, 30))
        )

    def test_us_is_trading_post_close(self):
        """US POST_CLOSE → is_trading=False."""
        self.assertFalse(
            self.resolver.is_trading(self.Market.US, self._us_dt(17, 0))
        )

    # ------------------------------------------------------------------
    # HK session detection
    # ------------------------------------------------------------------

    def _hk_dt(self, hour, minute, second=0):
        """Build a HK-local datetime for testing."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Hong_Kong")
        today = datetime.now(tz).date()
        return datetime(today.year, today.month, today.day,
                        hour, minute, second, tzinfo=tz)

    def test_hk_lunch_break(self):
        """HK 12:30 → LUNCH_BREAK."""
        session = self.resolver.detect(self.Market.HK, self._hk_dt(12, 30))
        self.assertEqual(session, self.MarketSession.LUNCH_BREAK)

    def test_hk_morning_continuous(self):
        """HK 10:30 → CONTINUOUS."""
        session = self.resolver.detect(self.Market.HK, self._hk_dt(10, 30))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_hk_afternoon_continuous(self):
        """HK 14:30 → CONTINUOUS."""
        session = self.resolver.detect(self.Market.HK, self._hk_dt(14, 30))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_hk_auction(self):
        """HK 16:05 → AUCTION."""
        session = self.resolver.detect(self.Market.HK, self._hk_dt(16, 5))
        self.assertEqual(session, self.MarketSession.AUCTION)

    def test_hk_post_close(self):
        """HK 16:15 → POST_CLOSE."""
        session = self.resolver.detect(self.Market.HK, self._hk_dt(16, 15))
        self.assertEqual(session, self.MarketSession.POST_CLOSE)

    def test_hk_is_trading_auction(self):
        """HK AUCTION → is_trading=True."""
        self.assertTrue(
            self.resolver.is_trading(self.Market.HK, self._hk_dt(16, 5))
        )

    def test_hk_is_trading_lunch_break(self):
        """HK LUNCH_BREAK → is_trading=False."""
        self.assertFalse(
            self.resolver.is_trading(self.Market.HK, self._hk_dt(12, 30))
        )

    # ------------------------------------------------------------------
    # Weekend detection (all markets closed)
    # ------------------------------------------------------------------

    def test_cn_weekend_closed(self):
        """CN on Saturday → CLOSED."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        # Find next Saturday
        from datetime import date
        today = date.today()
        days_ahead = 5 - today.weekday()  # Saturday = 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = today + timedelta(days=days_ahead)
        dt = datetime(saturday.year, saturday.month, saturday.day,
                      10, 0, tzinfo=tz)
        session = self.resolver.detect(self.Market.CN, dt)
        self.assertEqual(session, self.MarketSession.CLOSED)

    # ------------------------------------------------------------------
    # Boundary conditions
    # ------------------------------------------------------------------

    def test_cn_exact_lunch_start(self):
        """CN 11:30 exactly → LUNCH_BREAK."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(11, 30))
        self.assertEqual(session, self.MarketSession.LUNCH_BREAK)

    def test_cn_exact_afternoon_start(self):
        """CN 13:00 exactly → CONTINUOUS."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(13, 0))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_cn_exact_close(self):
        """CN 15:00 exactly → POST_CLOSE."""
        session = self.resolver.detect(self.Market.CN, self._cn_dt(15, 0))
        self.assertEqual(session, self.MarketSession.POST_CLOSE)

    def test_us_exact_regular_start(self):
        """US 9:30 ET exactly → CONTINUOUS."""
        session = self.resolver.detect(self.Market.US, self._us_dt(9, 30))
        self.assertEqual(session, self.MarketSession.CONTINUOUS)

    def test_us_exact_regular_end(self):
        """US 16:00 ET exactly → POST_CLOSE."""
        session = self.resolver.detect(self.Market.US, self._us_dt(16, 0))
        self.assertEqual(session, self.MarketSession.POST_CLOSE)


if __name__ == "__main__":
    unittest.main()
