"""
Test G+H: ResponseBuilder & Price Models (Round 1).

Tests:
  - ResponseBuilder: success() / partial_success() / error()
  - QuoteData / HistoryData / KLineItem / BatchQuoteItem / TechnicalIndicatorsData
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestResponseBuilder(unittest.TestCase):
    """Test ResponseBuilder factory methods."""

    def test_success_has_correct_structure(self):
        """success() returns dict with success=True, data, meta."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.success(data={"price": 100.0})
        self.assertTrue(response["success"])
        self.assertEqual(response["data"], {"price": 100.0})
        self.assertIn("meta", response)
        self.assertIn("request_id", response["meta"])
        self.assertIn("responded_at", response["meta"])

    def test_success_has_request_id(self):
        """success() auto-injects request_id in meta."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.success(data={})
        self.assertIsNotNone(response["meta"]["request_id"])
        self.assertEqual(len(response["meta"]["request_id"]), 12)

    def test_success_accepts_custom_request_id(self):
        """success() accepts explicit request_id."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.success(data={}, request_id="my-req-id")
        self.assertEqual(response["meta"]["request_id"], "my-req-id")

    def test_success_accepts_cache_info(self):
        """success() injects cache dict when provided."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        cache_info = {"hit": True, "expires_at": None}
        response = ResponseBuilder.success(data={}, cache=cache_info)
        self.assertIn("cache", response)
        self.assertEqual(response["cache"]["hit"], True)

    def test_success_accepts_warnings(self):
        """success() injects warnings list when provided."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        warnings = [{"code": "TEST", "message": "test warning"}]
        response = ResponseBuilder.success(data={}, warnings=warnings)
        self.assertIn("warnings", response)
        self.assertEqual(len(response["warnings"]), 1)

    def test_success_merges_meta(self):
        """success() merges caller-provided meta with defaults."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.success(
            data={},
            meta={"market": "CN", "symbol": "CN:600519"}
        )
        self.assertEqual(response["meta"]["market"], "CN")
        self.assertEqual(response["meta"]["symbol"], "CN:600519")
        # Auto-filled fields should still exist
        self.assertIn("request_id", response["meta"])

    # --- partial_success ---

    def test_partial_success_structure(self):
        """partial_success() has partial_success=True."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.partial_success(
            data={"quotes": [], "failed": ["AAPL"]},
            warnings=[{"code": "PARTIAL", "message": "Some failed"}]
        )
        self.assertTrue(response["success"])
        self.assertTrue(response["partial_success"])
        self.assertIn("warnings", response)

    def test_partial_success_without_warnings(self):
        """partial_success() works without warnings."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.partial_success(data={})
        self.assertTrue(response["partial_success"])
        self.assertNotIn("warnings", response)

    # --- error ---

    def test_error_structure(self):
        """error() returns success=False with error dict."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.error(
            error={
                "code": "SYMBOL_NOT_FOUND",
                "type": "input_error",
                "message": "Symbol 'XYZ' not found.",
                "retryable": False,
                "details": {"input": "XYZ"},
            }
        )
        self.assertFalse(response["success"])
        self.assertIsNone(response["data"])
        self.assertEqual(response["error"]["code"], "SYMBOL_NOT_FOUND")
        self.assertEqual(response["error"]["type"], "input_error")
        self.assertEqual(response["error"]["message"],
                         "Symbol 'XYZ' not found.")
        self.assertFalse(response["error"]["retryable"])
        self.assertEqual(response["error"]["details"], {"input": "XYZ"})

    def test_error_defaults(self):
        """error() fills defaults for missing fields."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.error(error={})
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(response["error"]["type"], "system_error")
        self.assertEqual(response["error"]["message"],
                         "An unexpected error occurred.")
        self.assertFalse(response["error"]["retryable"])
        self.assertEqual(response["error"]["details"], {})

    def test_error_has_request_id(self):
        """error() also injects request_id."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.error(error={})
        self.assertIn("request_id", response["meta"])

    def test_not_implemented(self):
        """not_implemented() returns standard error."""
        from market_data_mcp.domain.response_builder import ResponseBuilder
        response = ResponseBuilder.not_implemented("my_tool")
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["code"], "NOT_IMPLEMENTED")
        self.assertIn("my_tool", response["error"]["message"])


# ---------------------------------------------------------------------------
# Price Model Instantiation Tests
# ---------------------------------------------------------------------------


class TestQuoteDataModel(unittest.TestCase):
    """Test QuoteData Pydantic model."""

    def test_minimal_construction(self):
        """QuoteData can be constructed with all required fields."""
        from market_data_mcp.models.quote import QuoteData
        quote = QuoteData(
            symbol="CN:600519",
            name="贵州茅台",
            market="CN",
            price=1680.50,
            change=10.50,
            change_pct=0.63,
            open=1670.00,
            high=1690.00,
            low=1665.00,
            prev_close=1670.00,
            volume=5000000,
            turnover=8400000000.0,
            timestamp="2026-06-15T10:30:00+08:00",
            instrument_type="stock",
        )
        self.assertEqual(quote.symbol, "CN:600519")
        self.assertEqual(quote.price, 1680.50)
        self.assertEqual(quote.instrument_type, "stock")

    def test_missing_required_field_raises(self):
        """QuoteData raises ValidationError if required field missing."""
        from market_data_mcp.models.quote import QuoteData
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            QuoteData(name="Test")  # Missing symbol, price, etc.

    def test_field_types_enforced(self):
        """QuoteData enforces correct field types."""
        from market_data_mcp.models.quote import QuoteData
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            QuoteData(
                symbol="CN:600519",
                name="Test",
                market="CN",
                price="not_a_number",  # type: ignore[arg-type]
                change=0.0,
                change_pct=0.0,
                open=0.0,
                high=0.0,
                low=0.0,
                prev_close=0.0,
                volume=0,
                turnover=0.0,
                timestamp="now",
                instrument_type="stock",
            )

    def test_model_dump(self):
        """QuoteData.model_dump() produces a dict."""
        from market_data_mcp.models.quote import QuoteData
        quote = QuoteData(
            symbol="CN:600519", name="茅台", market="CN",
            price=1680.50, change=10.50, change_pct=0.63,
            open=1670.00, high=1690.00, low=1665.00,
            prev_close=1670.00, volume=5000000,
            turnover=8400000000.0, timestamp="2026-06-15T10:30:00+08:00",
            instrument_type="stock",
        )
        d = quote.model_dump()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["symbol"], "CN:600519")


class TestHistoryDataModel(unittest.TestCase):
    """Test HistoryData + KLineItem Pydantic models."""

    def test_kline_item_construction(self):
        """KLineItem can be constructed with all fields."""
        from market_data_mcp.models.history import KLineItem
        bar = KLineItem(
            date="2026-06-15",
            open=1670.0,
            high=1690.0,
            low=1665.0,
            close=1680.5,
            volume=5000000,
            turnover=8400000000.0,
            change_pct=0.63,
        )
        self.assertEqual(bar.date, "2026-06-15")
        self.assertEqual(bar.close, 1680.5)

    def test_history_data_construction(self):
        """HistoryData can be constructed with KLineItem list."""
        from market_data_mcp.models.history import HistoryData, KLineItem
        bars = [
            KLineItem(
                date="2026-06-15", open=1670.0, high=1690.0,
                low=1665.0, close=1680.5, volume=5000000,
                turnover=8400000000.0, change_pct=0.63,
            ),
            KLineItem(
                date="2026-06-16", open=1680.5, high=1695.0,
                low=1678.0, close=1690.0, volume=4500000,
                turnover=7600000000.0, change_pct=0.56,
            ),
        ]
        history = HistoryData(
            symbol="CN:600519",
            market="CN",
            period="1mo",
            interval="1d",
            adjust="none",
            count=2,
            history=bars,
        )
        self.assertEqual(history.count, 2)
        self.assertEqual(len(history.history), 2)
        self.assertEqual(history.history[0].date, "2026-06-15")

    def test_history_data_empty_default(self):
        """HistoryData history defaults to empty list."""
        from market_data_mcp.models.history import HistoryData
        history = HistoryData(
            symbol="CN:600519", market="CN",
            period="1mo", interval="1d", adjust="none", count=0,
        )
        self.assertEqual(history.history, [])
        self.assertEqual(history.count, 0)


class TestBatchQuoteModel(unittest.TestCase):
    """Test BatchQuoteItem + BatchQuoteData models."""

    def test_batch_quote_item_with_cache(self):
        """BatchQuoteItem can carry per-symbol cache info."""
        from market_data_mcp.models.batch import BatchQuoteItem
        item = BatchQuoteItem(
            symbol="CN:600519", name="茅台", price=1680.50,
            change=10.50, change_pct=0.63, open=1670.0,
            high=1690.0, low=1665.0, prev_close=1670.0,
            volume=5000000, turnover=8400000000.0,
            timestamp="2026-06-15T10:30:00+08:00",
            instrument_type="stock",
            cache={"hit": True, "expires_at": None},
        )
        self.assertIsNotNone(item.cache)
        self.assertTrue(item.cache["hit"])

    def test_batch_quote_item_without_cache(self):
        """BatchQuoteItem cache is None by default."""
        from market_data_mcp.models.batch import BatchQuoteItem
        item = BatchQuoteItem(
            symbol="CN:600519", name="茅台", price=1680.50,
            change=10.50, change_pct=0.63, open=1670.0,
            high=1690.0, low=1665.0, prev_close=1670.0,
            volume=5000000, turnover=8400000000.0,
            timestamp="2026-06-15T10:30:00+08:00",
            instrument_type="stock",
        )
        self.assertIsNone(item.cache)

    def test_batch_quote_data_construction(self):
        """BatchQuoteData with summary and quotes."""
        from market_data_mcp.models.batch import (
            BatchQuoteData, BatchQuoteItem, BatchSummary
        )
        data = BatchQuoteData(
            quotes=[],
            failed_symbols=["BAD:SYMBOL"],
            summary=BatchSummary(requested=3, success=2, failed=1),
        )
        self.assertEqual(data.summary.requested, 3)
        self.assertEqual(data.summary.failed, 1)
        self.assertEqual(data.failed_symbols, ["BAD:SYMBOL"])


class TestTechnicalIndicatorsModel(unittest.TestCase):
    """Test TechnicalIndicatorsData model."""

    def test_indicators_construction(self):
        """TechnicalIndicatorsData with full indicators dict."""
        from market_data_mcp.models.indicators import TechnicalIndicatorsData
        data = TechnicalIndicatorsData(
            symbol="CN:600519",
            adjusted="qfq",
            indicators={
                "MA": {"MA5": 1690.2, "MA10": 1685.0, "MA20": 1670.5, "MA60": 1620.0},
                "EMA": {"EMA12": 1688.0, "EMA26": 1670.0},
                "RSI": {"RSI6": 58.2, "RSI14": 52.3, "RSI24": 48.1},
                "MACD": {"DIF": 12.5, "DEA": 10.2, "MACD": 2.3},
                "BOLL": {"UPPER": 1720.0, "MIDDLE": 1685.0, "LOWER": 1650.0},
                "KDJ": {"K": 55.0, "D": 50.0, "J": 65.0},
            },
        )
        self.assertEqual(data.symbol, "CN:600519")
        self.assertEqual(data.adjusted, "qfq")
        self.assertEqual(data.indicators["MA"]["MA5"], 1690.2)
        self.assertEqual(data.indicators["RSI"]["RSI6"], 58.2)

    def test_indicators_empty_default(self):
        """TechnicalIndicatorsData indicators defaults to empty dict."""
        from market_data_mcp.models.indicators import TechnicalIndicatorsData
        data = TechnicalIndicatorsData(
            symbol="CN:600519",
            adjusted="none",
        )
        self.assertEqual(data.indicators, {})


if __name__ == "__main__":
    unittest.main()
