import unittest
from datetime import datetime, timedelta
from backend.models.schemas import Candle
from backend.services.portfolio.thesis_engine import thesis_engine
from backend.services.quant.technical_engine import TechnicalEngine

class TestPortfolioThesis(unittest.TestCase):
    def test_thesis_evaluation_states(self):
        candles = []
        base = 2900.0
        now = datetime.utcnow()
        for i in range(30):
            p = base + i * 8.0
            candles.append(Candle(
                timestamp=now - timedelta(days=(30 - i)),
                open=p - 3.0,
                high=p + 12.0,
                low=p - 5.0,
                close=p + 4.0,
                volume=600000 + i * 8000,
                open_interest=250000
            ))
            
        indicators = TechnicalEngine.evaluate_indicators(candles)
        
        status, points = thesis_engine.evaluate_thesis(
            candles, indicators, buy_price=2850.0, rs_20d=3.0, sector_trend="BULLISH"
        )
        self.assertIn(status, ["STRENGTHENING", "STABLE", "WEAKENING", "BROKEN"])
        self.assertGreater(len(points), 0)

if __name__ == "__main__":
    unittest.main()
