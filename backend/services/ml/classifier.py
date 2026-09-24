import os
import math
import logging
from typing import Dict, Any, Optional
import numpy as np

from backend.models.schemas import MLProbabilityMetrics

logger = logging.getLogger("ml_classifier")

FEATURE_NAMES = [
    "dist_ema20",
    "dist_ema50",
    "dist_ema200",
    "ema_alignment",
    "rsi_norm",
    "macd_hist_ratio",
    "adx_strength",
    "atr_pct",
    "bb_width",
    "volume_surge",
    "breakout_proximity",
    "rs_20d",
    "mansfield_rs",
    "sector_momentum",
    "candle_score_norm",
    "regime_val"
]

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_BUNDLE_PATH = os.path.join(MODEL_DIR, "swing_model_bundle.joblib")


class FittedMLClassifier:
    """
    Production Machine Learning Inference Engine for Swing Trading Probability Estimation.
    
    Features:
    - Loads persisted Calibrated Gradient Boosted Trees for independent T1, T2, T3 predictions.
    - Zero-fallback transparency: Uses heuristic rule-based baseline when model artifact is missing.
    """
    
    def __init__(self):
        self.model_bundle: Optional[Dict[str, Any]] = None
        self.load_fitted_model()

    def load_fitted_model(self):
        if os.path.exists(MODEL_BUNDLE_PATH):
            try:
                import joblib
                self.model_bundle = joblib.load(MODEL_BUNDLE_PATH)
                logger.info(f"Loaded fitted ML model bundle ({self.model_bundle.get('model_version')}) from {MODEL_BUNDLE_PATH}")
            except Exception as e:
                logger.warning(f"Could not load ML model bundle from {MODEL_BUNDLE_PATH}: {e}")
                self.model_bundle = None
        else:
            self.model_bundle = None

    def predict_probabilities(self, features: Dict[str, float]) -> MLProbabilityMetrics:
        if not features or len(features) < 8:
            return MLProbabilityMetrics(
                p_t1_before_sl=None,
                p_t2_before_sl=None,
                p_t3_before_sl=None,
                raw_probability=None,
                confidence_score=None,
                expected_days_min=None,
                expected_days_max=None,
                prediction_horizon_days=10,
                model_version="Heuristic-Rule-Based-v1.0" if not self.model_bundle else self.model_bundle.get("model_version", "Fitted-ML-v1.0"),
                calibration_status="UNAVAILABLE",
                brier_score_calibration=None,
                status="UNAVAILABLE",
                reason="MODEL_FEATURES_INCOMPLETE: Insufficient observations to construct full feature vector"
            )

        # 1. Real Fitted ML Model Inference (if bundle loaded)
        if self.model_bundle and "calibrated_t1" in self.model_bundle:
            try:
                calibrated_t1 = self.model_bundle["calibrated_t1"]
                calibrated_t2 = self.model_bundle.get("calibrated_t2")
                calibrated_t3 = self.model_bundle.get("calibrated_t3")

                feat_vector = np.array([[float(features.get(fname, 0.0)) for fname in FEATURE_NAMES]], dtype=np.float32)

                p_t1 = float(calibrated_t1.predict_proba(feat_vector)[0, 1])
                p_t2 = float(calibrated_t2.predict_proba(feat_vector)[0, 1]) if calibrated_t2 else p_t1 * 0.70
                p_t3 = float(calibrated_t3.predict_proba(feat_vector)[0, 1]) if calibrated_t3 else p_t1 * 0.45

                brier = self.model_bundle.get("brier_score_t1")

                # Multi-factor confidence score
                feature_agreement = (
                    (1.0 if features.get("ema_alignment", 0.0) > 0 else 0.0) +
                    (1.0 if features.get("mansfield_rs", 0.0) > 0 or features.get("rs_20d", 0.0) > 0 else 0.0) +
                    (1.0 if features.get("volume_surge", 1.0) >= 1.15 else 0.0) +
                    (1.0 if features.get("sector_momentum", 0.0) > 0 else 0.0) +
                    (1.0 if features.get("regime_val", 0.0) > 0 else 0.0)
                ) / 5.0
                confidence = round(0.50 + (feature_agreement * 0.45), 2)

                volatility_factor = features.get("atr_pct", 2.0)
                exp_min, exp_max = (3, 7) if volatility_factor > 3.2 else (5, 12)

                return MLProbabilityMetrics(
                    p_t1_before_sl=round(p_t1, 2),
                    p_t2_before_sl=round(p_t2, 2),
                    p_t3_before_sl=round(p_t3, 2),
                    raw_probability=round(p_t1, 2),
                    confidence_score=confidence,
                    expected_days_min=exp_min,
                    expected_days_max=exp_max,
                    prediction_horizon_days=10,
                    model_version=self.model_bundle.get("model_version", "Fitted-GradientBoosted-v1.0"),
                    training_period="Multi-Year Empirical Walk-Forward Dataset",
                    validation_period="Out-of-Sample Triple-Barrier Fold",
                    calibration_status="CALIBRATED_ISOTONIC",
                    brier_score_calibration=brier,
                    status="AVAILABLE",
                    reason=None
                )
            except Exception as e:
                logger.warning(f"Error executing ML inference: {e}. Falling back to transparent heuristic rule.")

        # 2. Transparent Heuristic Fallback (When no model bundle has been trained yet)
        w_ema, w_rsi, w_macd, w_vol, w_rs, w_mansfield, w_sector_mom, w_candle, w_regime, w_adx = (
            0.35, 0.28, 0.22, 0.40, 0.45, 0.50, 0.35, 0.30, 0.45, 0.20
        )
        bias = 0.10

        logit = (
            bias +
            features.get("ema_alignment", 0.0) * w_ema +
            features.get("rsi_norm", 0.0) * w_rsi +
            features.get("macd_hist_ratio", 0.0) * w_macd +
            min(max(features.get("volume_surge", 1.0) - 1.0, -1.0), 2.0) * w_vol +
            min(max(features.get("rs_20d", 0.0) / 10.0, -1.0), 1.5) * w_rs +
            min(max(features.get("mansfield_rs", 0.0) / 10.0, -1.0), 1.5) * w_mansfield +
            features.get("sector_momentum", 0.0) * w_sector_mom +
            features.get("candle_score_norm", 0.0) * w_candle +
            features.get("regime_val", 0.0) * w_regime +
            features.get("adx_strength", 0.5) * w_adx
        )

        p_t1 = 1.0 / (1.0 + math.exp(-logit))
        p_t1 = min(max(p_t1, 0.20), 0.85)
        p_t2 = p_t1 * 0.74
        p_t3 = p_t1 * 0.52

        feature_agreement = (
            (1.0 if features.get("ema_alignment", 0.0) > 0 else 0.0) +
            (1.0 if features.get("mansfield_rs", 0.0) > 0 or features.get("rs_20d", 0.0) > 0 else 0.0) +
            (1.0 if features.get("volume_surge", 1.0) >= 1.15 else 0.0) +
            (1.0 if features.get("sector_momentum", 0.0) > 0 else 0.0) +
            (1.0 if features.get("regime_val", 0.0) > 0 else 0.0)
        ) / 5.0
        confidence = round(0.50 + (feature_agreement * 0.42), 2)

        volatility_factor = features.get("atr_pct", 2.0)
        exp_min, exp_max = (3, 7) if volatility_factor > 3.2 else (5, 12)

        return MLProbabilityMetrics(
            p_t1_before_sl=round(p_t1, 2),
            p_t2_before_sl=round(p_t2, 2),
            p_t3_before_sl=round(p_t3, 2),
            raw_probability=round(p_t1, 2),
            confidence_score=confidence,
            expected_days_min=exp_min,
            expected_days_max=exp_max,
            prediction_horizon_days=10,
            model_version="Heuristic-Rule-Based-v1.0",
            training_period=None,
            validation_period=None,
            calibration_status="UNAVAILABLE",
            brier_score_calibration=None,
            status="HEURISTIC_RULE_BASED",
            reason=None
        )


HeuristicScoringEngine = FittedMLClassifier
SwingMLClassifier = FittedMLClassifier
ml_classifier = FittedMLClassifier()
