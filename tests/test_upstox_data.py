import unittest
from datetime import datetime
from backend.services.market_data.normalizer import DataNormalizer
from backend.services.market_data.upstox_provider import UpstoxProvider

class TestUpstoxDataLayer(unittest.TestCase):
    def test_candle_normalization(self):
        raw_upstox_payload = [
            ["2026-09-23T15:30:00+05:30", 3400.0, 3450.0, 3390.0, 3445.0, 1500000, 450000],
            ["2026-09-22T15:30:00+05:30", 3350.0, 3410.0, 3340.0, 3395.0, 1200000, 420000],
        ]
        candles = DataNormalizer.normalize_upstox_candles(raw_upstox_payload)
        self.assertEqual(len(candles), 2)
        # Should be sorted oldest to newest
        self.assertLess(candles[0].timestamp, candles[1].timestamp)
        self.assertEqual(candles[1].close, 3445.0)

    def test_quote_normalization(self):
        raw_quote = {
            "last_price": 3445.0,
            "volume": 1500000,
            "ohlc": {"open": 3400.0, "high": 3450.0, "low": 3390.0, "close": 3445.0},
            "prev_close": 3395.0
        }
        normalized = DataNormalizer.normalize_upstox_quote("TCS", raw_quote)
        self.assertEqual(normalized["symbol"], "TCS")
        self.assertEqual(normalized["price"], 3445.0)
        self.assertEqual(normalized["change"], 50.0)
        self.assertAlmostEqual(normalized["change_percent"], 1.47, places=2)

    def test_instrument_key_formatting(self):
        provider = UpstoxProvider("dummy_test_token")
        self.assertEqual(provider._format_instrument_key("TCS"), "NSE_EQ|TCS")
        self.assertEqual(provider._format_instrument_key("NIFTY 50"), "NSE_INDEX|Nifty 50")
        self.assertEqual(provider._format_instrument_key("BANKNIFTY"), "NSE_INDEX|Nifty Bank")

if __name__ == "__main__":
    unittest.main()
