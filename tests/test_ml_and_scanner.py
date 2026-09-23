import unittest
from datetime import datetime, timedelta
from backend.models.schemas import Candle
from backend.services.quant.technical_engine import TechnicalEngine
from backend.services.ml.feature_pipeline import FeaturePipeline
from backend.services.ml.classifier import ml_classifier

class TestMLAndScanner(unittest.TestCase):
    def setUp(self):
        self.candles = []
        base = 1600.0
        now = datetime.utcnow()
        for i in range(30):
            p = base + i * 5.0
            self.candles.append(Candle(
                timestamp=now - timedelta(days=(30 - i)),
                open=p - 2.0,
                high=p + 8.0,
                low=p - 4.0,
                close=p + 3.0,
                volume=800000 + i * 5000,
                open_interest=300000
            ))
        self.indicators = TechnicalEngine.evaluate_indicators(self.candles)

    def test_feature_pipeline(self):
        features = FeaturePipeline.extract_features(
            self.candles, self.indicators, rs_20d=2.4, sector_rs_20d=3.1, market_regime="BULL"
        )
        self.assertIn("dist_ema20", features)
        self.assertIn("rsi_norm", features)
        self.assertIn("volume_surge", features)
        self.assertIn("rs_20d", features)

    def test_ml_classifier_probabilities(self):
        features = FeaturePipeline.extract_features(
            self.candles, self.indicators, rs_20d=2.4, sector_rs_20d=3.1, market_regime="BULL"
        )
        prob = ml_classifier.predict_probabilities(features)
        
        self.assertTrue(0.0 <= prob.p_t1_before_sl <= 1.0)
        self.assertTrue(0.0 <= prob.p_t2_before_sl <= 1.0)
        self.assertTrue(0.0 <= prob.p_t3_before_sl <= 1.0)
        self.assertGreater(prob.p_t1_before_sl, prob.p_t2_before_sl)
        self.assertGreater(prob.p_t2_before_sl, prob.p_t3_before_sl)

if __name__ == "__main__":
    unittest.main()
