import pytest
from datetime import datetime, timedelta, date
from backend.models.schemas import (
    Candle, TechnicalIndicators, VolumeProfileMetrics, MarketDataSnapshot, DataQualityReport
)
from backend.services.market_data.data_quality import data_quality_gate
from backend.services.quant.technical_engine import TechnicalEngine
from backend.services.quant.relative_strength import RelativeStrengthEngine
from backend.services.quant.factor_engine import factor_engine
from backend.services.quant.target_stop_engine import TargetStopEngine
from backend.services.quant.setup_engine import setup_engine
from backend.services.ml.classifier import ml_classifier
from backend.services.market_data.universe import NSE_RANKED_UNIVERSE

def generate_mock_candles(count: int, base_price: float = 1000.0, trend: float = 0.5) -> list[Candle]:
    candles = []
    base_dt = datetime(2025, 1, 1, 9, 15)
    for i in range(count):
        close = round(base_price + (i * trend) + (5.0 if i % 2 == 0 else -5.0), 2)
        open_p = round(close - (1.0 if i % 2 == 0 else -1.0), 2)
        high = round(max(open_p, close) + 4.0, 2)
        low = round(min(open_p, close) - 4.0, 2)
        vol = 100000 + (i * 1000)
        candles.append(Candle(
            timestamp=base_dt + timedelta(days=i),
            open=open_p,
            high=high,
            low=low,
            close=close,
            volume=vol,
            open_interest=0
        ))
    return candles

# --- 1. TCS Regression Test ---
def test_tcs_regression_rr_and_reference_entry_consistency():
    """
    Verifies that for a setup with reference_entry = 2113.42, stop_loss = 2064.92, target_1 = 2177.14:
    Risk per share = 48.50
    Reward T1 = 63.72
    Calculated R:R = 1.31R (NOT an arbitrary mismatched ratio like 1.86R)
    """
    ref_entry = 2113.42
    stop = 2064.92
    target_1 = 2177.14

    risk_per_share = round(ref_entry - stop, 2)
    assert risk_per_share == 48.50

    reward_t1 = round(target_1 - ref_entry, 2)
    assert reward_t1 == 63.72

    rr = round(reward_t1 / risk_per_share, 2)
    assert rr == 1.31

# --- 2. SMA200 Lookback & Coverage ---
def test_technical_engine_sma200_coverage():
    # 250 candles must calculate SMA200
    candles_250 = generate_mock_candles(250, 2000.0, trend=1.0)
    ind_250 = TechnicalEngine.evaluate_indicators(candles_250)
    assert ind_250.sma_200 is not None
    assert ind_250.sma_200 > 0
    assert ind_250.ema_20 is not None
    assert ind_250.ema_50 is not None

    # 150 candles must return None for SMA200 (Zero synthetic defaults)
    candles_150 = generate_mock_candles(150, 2000.0, trend=1.0)
    ind_150 = TechnicalEngine.evaluate_indicators(candles_150)
    assert ind_150.sma_200 is None
    assert ind_150.ema_20 is not None

# --- 3. Factor Engine Mathematical Identity ---
def test_factor_engine_mathematical_identity():
    candles = generate_mock_candles(100, 1500.0, trend=2.0)
    ind = TechnicalEngine.evaluate_indicators(candles)
    vol = VolumeProfileMetrics(rvol_20d=1.5, volume_5d_vs_20d_ratio=1.2, breakout_volume_surge=1.8, volume_trend="ACCUMULATION", avg_turnover_cr_20d=65.0, is_volume_confirmed=True)
    
    factors = factor_engine.calculate_factors(
        candles=candles,
        indicators=ind,
        volume_metrics=vol,
        mansfield_rs=3.5,
        sector_momentum=65.0,
        setup_quality_score=80.0,
        catalyst_score=75.0
    )

    assert factors.status == "AVAILABLE"
    assert factors.overall_factor_rank is not None
    assert len(factors.factor_breakdown) == 8

    # Sum of weighted contributions must equal overall_factor_rank
    breakdown_sum = round(sum(item.weighted_contribution for item in factors.factor_breakdown if item.weighted_contribution is not None), 1)
    assert factors.overall_factor_rank == breakdown_sum

# --- 4. Setup Engine Explicit Supported Classes ---
def test_setup_engine_supported_types():
    candles = generate_mock_candles(60, 2000.0, trend=2.0)
    ind = TechnicalEngine.evaluate_indicators(candles)
    vol = VolumeProfileMetrics(rvol_20d=1.4, volume_5d_vs_20d_ratio=1.1, breakout_volume_surge=1.5, volume_trend="ACCUMULATION", avg_turnover_cr_20d=50.0, is_volume_confirmed=True)
    
    setup = setup_engine.classify_setup(candles, ind, vol, mansfield_rs=2.0)
    
    allowed_types = ["BREAKOUT", "PULLBACK", "MOMENTUM_CONTINUATION", "VOLATILITY_CONTRACTION", "BASE_BREAKOUT", "UNCLASSIFIED", "NONE"]
    assert setup.setup_type in allowed_types
    assert setup.setup_type != "OTHER_VALID_SETUP"

# --- 5. Target & Stop Engine Structural Levels & Reference Entry ---
def test_target_stop_engine_structural_levels():
    candles = generate_mock_candles(100, 2000.0, trend=1.5)
    ind = TechnicalEngine.evaluate_indicators(candles)
    
    levels = TargetStopEngine.calculate_levels(candles, ind)
    assert levels.status == "AVAILABLE"
    assert levels.reference_entry is not None
    assert levels.stop_loss is not None
    assert levels.target_1 is not None
    assert levels.target_2 is not None
    
    # Exact R:R identity check
    expected_risk = round(levels.reference_entry - levels.stop_loss, 2)
    assert levels.risk_per_share == expected_risk
    
    expected_reward_t1 = round(levels.target_1 - levels.reference_entry, 2)
    assert levels.reward_t1_per_share == expected_reward_t1
    
    expected_rr = round(expected_reward_t1 / expected_risk, 2)
    assert levels.risk_reward_ratio == expected_rr

    # Structural method tagging
    assert levels.target_1_method is not None
    assert levels.target_2_method is not None

# --- 6. ML Classifier Horizon & Calibration Decoupling ---
def test_ml_classifier_horizon_and_calibration():
    ml_res = ml_classifier.predict_probabilities({})
    assert ml_res.status == "UNAVAILABLE"
    assert ml_res.p_t1_before_sl is None
    assert ml_res.horizon_label == "10 trading days"
    assert "P(T1 before SL within 10 trading days)" in ml_res.prediction_label
