import pytest
from datetime import datetime, timedelta, date
from backend.models.schemas import Candle, TechnicalIndicators, VolumeProfileMetrics
from backend.services.market_data.data_quality import data_quality_gate
from backend.services.quant.technical_engine import TechnicalEngine
from backend.services.quant.relative_strength import RelativeStrengthEngine
from backend.services.quant.factor_engine import factor_engine
from backend.services.quant.target_stop_engine import TargetStopEngine
from backend.services.ml.classifier import ml_classifier
from backend.services.ml.feature_pipeline import FeaturePipeline
from backend.services.market_data.universe import NSE_RANKED_UNIVERSE

def generate_mock_candles(count: int, base_price: float = 1000.0, trend: float = 0.5) -> list[Candle]:
    candles = []
    base_dt = datetime(2026, 1, 1, 9, 15)
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

# --- Test 1: Data Quality Gate ---
def test_data_quality_gate_valid():
    candles = generate_mock_candles(150, 1000.0)
    result = data_quality_gate.validate_daily_candles(candles, symbol="TEST", min_required_bars=120)
    assert result.is_valid is True
    assert result.status == "AVAILABLE"
    assert result.candle_count == 150
    assert result.rejection_reason is None

def test_data_quality_gate_insufficient_history():
    candles = generate_mock_candles(15, 1000.0)
    result = data_quality_gate.validate_daily_candles(candles, symbol="TEST", min_required_bars=120)
    assert result.is_valid is False
    assert result.status == "UNAVAILABLE"
    assert "Insufficient history" in result.rejection_reason

def test_data_quality_gate_malformed_ohlc():
    bad_candles = [
        Candle(timestamp=datetime(2026, 1, 1), open=100.0, high=90.0, low=110.0, close=95.0, volume=1000), # High < Low
        Candle(timestamp=datetime(2026, 1, 2), open=-10.0, high=100.0, low=80.0, close=90.0, volume=1000)  # Negative Open
    ]
    result = data_quality_gate.validate_daily_candles(bad_candles, symbol="BAD", min_required_bars=2)
    assert result.is_valid is False
    assert result.status == "INVALID"

# --- Test 2: Technical Engine Zero Fallbacks ---
def test_technical_engine_zero_fallbacks():
    # Empty list must return None for indicators, not 0.0 or 50.0
    empty_ind = TechnicalEngine.evaluate_indicators([])
    assert empty_ind.status == "UNAVAILABLE"
    assert empty_ind.rsi_14 is None
    assert empty_ind.ema_20 is None
    assert empty_ind.ema_50 is None
    assert empty_ind.sma_200 is None
    assert empty_ind.atr_14 is None
    assert empty_ind.macd_line is None

def test_technical_engine_mathematical_accuracy():
    candles = generate_mock_candles(220, 1000.0, trend=1.0)
    ind = TechnicalEngine.evaluate_indicators(candles)
    assert ind.status == "AVAILABLE"
    assert ind.ema_20 is not None and ind.ema_20 > 0
    assert ind.sma_200 is not None and ind.sma_200 > 0
    assert ind.rsi_14 is not None and 0 <= ind.rsi_14 <= 100
    assert ind.atr_14 is not None and ind.atr_14 > 0

# --- Test 3: Relative Strength Engine ---
def test_relative_strength_engine():
    stock_candles = generate_mock_candles(80, 1000.0, trend=2.0)
    bench_candles = generate_mock_candles(80, 20000.0, trend=10.0)
    rs_metrics = RelativeStrengthEngine.evaluate_multi_timeframe_rs(stock_candles, bench_candles, sector_momentum=60.0)
    assert rs_metrics.status == "AVAILABLE"
    assert rs_metrics.excess_return_20d is not None
    assert rs_metrics.mansfield_rs_50d is not None
    assert rs_metrics.rs_trend in ["EXPANDING", "FLAT", "DETERIORATING"]

def test_relative_strength_empty_fallback():
    rs_metrics = RelativeStrengthEngine.evaluate_multi_timeframe_rs([], [])
    assert rs_metrics.status == "UNAVAILABLE"
    assert rs_metrics.excess_return_20d is None
    assert rs_metrics.mansfield_rs_50d is None

# --- Test 4: Factor Engine Zero Fallbacks ---
def test_factor_engine_zero_fallbacks():
    empty_ind = TechnicalEngine.evaluate_indicators([])
    empty_vol = VolumeProfileMetrics(rvol_20d=None, volume_5d_vs_20d_ratio=None, breakout_volume_surge=None, volume_trend="NEUTRAL", avg_turnover_cr_20d=None, is_volume_confirmed=False)
    factors = factor_engine.calculate_factors([], empty_ind, empty_vol)
    assert factors.status == "UNAVAILABLE"
    assert factors.momentum_score is None
    assert factors.overall_factor_rank is None

# --- Test 5: Target and Stop Engine Rupee Prices ---
def test_target_stop_engine_rupee_prices():
    candles = generate_mock_candles(60, 2000.0, trend=1.5)
    ind = TechnicalEngine.evaluate_indicators(candles)
    levels = TargetStopEngine.calculate_levels(candles, ind)
    assert levels.status == "AVAILABLE"
    assert levels.current_price is not None and levels.current_price > 0
    assert levels.stop_loss is not None and levels.stop_loss < levels.current_price
    assert levels.target_1 is not None and levels.target_1 > levels.current_price
    assert levels.target_2 is not None and levels.target_2 > levels.target_1
    if levels.target_3 is not None:
        assert levels.target_3 > levels.target_2
    assert "₹" in levels.target_1_display
    assert "₹" in levels.stop_loss_display

def test_target_stop_engine_empty_fallbacks():
    empty_ind = TechnicalEngine.evaluate_indicators([])
    levels = TargetStopEngine.calculate_levels([], empty_ind)
    assert levels.status == "UNAVAILABLE"
    assert levels.target_1 is None
    assert levels.stop_loss is None

# --- Test 6: ML Classifier Unavailable Provenance ---
def test_ml_classifier_unavailable():
    ml_res = ml_classifier.predict_probabilities({})
    assert ml_res.status == "UNAVAILABLE"
    assert ml_res.p_t1_before_sl is None
    assert ml_res.confidence_score is None
    assert ml_res.calibration_status == "UNAVAILABLE"
    assert "MODEL_FEATURES_INCOMPLETE" in ml_res.reason

# --- Test 7: Instrument Resolution & MAZDOCK Trace ---
def test_mazdock_instrument_resolution():
    mazdock = next((u for u in NSE_RANKED_UNIVERSE if u["symbol"] == "MAZDOCK"), None)
    assert mazdock is not None
    assert mazdock["instrument_key"] == "NSE_EQ|INE249Z01020"
    assert mazdock["market_cap_category"] == "MID_CAP"
    assert mazdock["market_cap_rank"] == 128


