import unittest
from datetime import datetime, timedelta
from backend.models.schemas import Candle
from backend.services.quant.technical_engine import TechnicalEngine
from backend.services.quant.candle_engine import CandlestickEngine
from backend.services.quant.relative_strength import RelativeStrengthEngine
from backend.services.quant.liquidity_engine import LiquidityEngine
from backend.services.quant.target_stop_engine import TargetStopEngine

class TestQuantEngines(unittest.TestCase):
    def setUp(self):
        # Create explicit test fixture candles (30 bars)
        self.candles = []
        base = 3000.0
        now = datetime.utcnow()
        for i in range(30):
            p = base + i * 10.0
            self.candles.append(Candle(
                timestamp=now - timedelta(days=(30 - i)),
                open=p - 5.0,
                high=p + 15.0,
                low=p - 8.0,
                close=p + 5.0,
                volume=500000 + i * 10000,
                open_interest=200000
            ))
            
        self.nifty_candles = []
        nifty_base = 25000.0
        for i in range(30):
            p = nifty_base + i * 25.0
            self.nifty_candles.append(Candle(
                timestamp=now - timedelta(days=(30 - i)),
                open=p - 10.0,
                high=p + 30.0,
                low=p - 15.0,
                close=p + 10.0,
                volume=10000000,
                open_interest=5000000
            ))

    def test_technical_engine_indicators(self):
        indicators = TechnicalEngine.evaluate_indicators(self.candles)
        self.assertGreater(indicators.sma_20, 0)
        self.assertGreater(indicators.ema_20, 0)
        self.assertGreater(indicators.ema_50, 0)
        self.assertTrue(0 <= indicators.rsi_14 <= 100)
        self.assertGreater(indicators.atr_14, 0)

    def test_candlestick_engine(self):
        patterns = CandlestickEngine.identify_patterns(self.candles)
        self.assertIsInstance(patterns, list)

    def test_relative_strength(self):
        rs_20 = RelativeStrengthEngine.calculate_excess_return(self.candles, self.nifty_candles, 20)
        self.assertIsInstance(rs_20, float)


    def test_liquidity_engine(self):
        liq = LiquidityEngine.evaluate_liquidity(self.candles)
        self.assertTrue(liq["is_liquid"])
        self.assertGreater(liq["daily_turnover_cr"], 0)

    def test_target_stop_engine(self):
        indicators = TechnicalEngine.evaluate_indicators(self.candles)
        levels = TargetStopEngine.calculate_levels(self.candles, indicators)
        current = self.candles[-1].close
        
        self.assertLess(levels.stop_loss, current)
        self.assertGreater(levels.target_1, current)
        self.assertGreater(levels.target_2, levels.target_1)
        self.assertGreater(levels.target_3, levels.target_2)
        self.assertGreaterEqual(levels.risk_reward_ratio, 1.0)
        self.assertTrue(len(levels.levels_reasoning) >= 3)

    def test_fundamental_disqualification_gate(self):
        from backend.services.market_data.fundamental_service import fundamental_service
        # Loss-making stock must be disqualified
        is_disq, reason = fundamental_service.evaluate_fundamental_disqualifier("PAYTM")
        self.assertTrue(is_disq)
        self.assertIn("net loss", reason.lower())

        # High growth profitable stock must NOT be disqualified
        is_disq_rel, _ = fundamental_service.evaluate_fundamental_disqualifier("RELIANCE")
        self.assertFalse(is_disq_rel)

    def test_street_analyst_target_cross_check(self):
        from backend.services.market_data.fundamental_service import fundamental_service
        # Target higher than street high target (e.g. Reliance street high is 3350)
        check = fundamental_service.check_street_analyst_consensus("RELIANCE", 3600.0)
        self.assertTrue(check["exceeds_street_high"])
        self.assertIsNotNone(check["warning_message"])

        # Realistic target within Street consensus
        check_valid = fundamental_service.check_street_analyst_consensus("RELIANCE", 3200.0)
        self.assertFalse(check_valid["exceeds_street_high"])

if __name__ == "__main__":
    unittest.main()
