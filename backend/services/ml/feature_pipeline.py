from typing import List, Dict, Any, Optional
from backend.models.schemas import Candle, TechnicalIndicators

class FeaturePipeline:
    """
    Transforms raw OHLCV series, technical indicators, relative strength,
    volume profile, and market context into calibrated feature vectors for ML models.
    Returns empty dict if required features cannot be computed.
    """
    
    @classmethod
    def extract_features(
        cls,
        candles: List[Candle],
        indicators: TechnicalIndicators,
        rs_20d: Optional[float] = None,
        mansfield_rs: Optional[float] = None,
        sector_momentum: Optional[float] = None,
        candle_score: Optional[float] = None,
        rvol: Optional[float] = None,
        market_regime: str = "BULL"
    ) -> Dict[str, float]:
        if not candles or len(candles) < 20:
            return {}

        current = candles[-1].close
        if current <= 0:
            return {}

        # 1. Trend & Moving Average Features
        ema20 = indicators.ema_20 or current
        ema50 = indicators.ema_50 or current
        ema200 = indicators.ema_200 or current

        dist_ema20 = (current - ema20) / ema20 * 100.0
        dist_ema50 = (current - ema50) / ema50 * 100.0
        dist_ema200 = (current - ema200) / ema200 * 100.0
        
        ema_alignment = 0.0
        if indicators.ema_20 is not None and indicators.ema_50 is not None:
            if indicators.ema_200 is not None:
                if indicators.ema_20 > indicators.ema_50 > indicators.ema_200:
                    ema_alignment = 1.0
                elif indicators.ema_20 < indicators.ema_50 < indicators.ema_200:
                    ema_alignment = -1.0
            else:
                ema_alignment = 0.5 if indicators.ema_20 > indicators.ema_50 else -0.5

        # 2. Momentum & Oscillator Features
        rsi_val = indicators.rsi_14 if indicators.rsi_14 is not None else 50.0
        rsi_norm = (rsi_val - 50.0) / 50.0
        
        macd_hist = indicators.macd_hist or 0.0
        macd_hist_ratio = macd_hist / (current * 0.01) if current > 0 else 0.0
        adx_val = indicators.adx_14 or 20.0
        adx_strength = min(adx_val / 50.0, 1.0)
        
        # 3. Volatility Features
        atr_val = indicators.atr_14 or (current * 0.02)
        atr_pct = (atr_val / current) * 100.0
        
        bb_upper = indicators.bb_upper or (current * 1.05)
        bb_lower = indicators.bb_lower or (current * 0.95)
        bb_mid = indicators.bb_middle or current
        bb_width = ((bb_upper - bb_lower) / bb_mid) * 100.0 if bb_mid > 0 else 5.0
        
        # 4. Breakout Proximity
        highest_20 = max([c.high for c in candles[-min(20, len(candles)):]])
        breakout_proximity = (current - highest_20) / highest_20 * 100.0 if highest_20 > 0 else 0.0
        
        # 5. Market Regime Encoding
        regime_weights = {
            "STRONG_BULL": 1.0,
            "BULL": 0.8,
            "RECOVERY": 0.5,
            "NEUTRAL": 0.1,
            "BEAR": -0.7,
            "STRESS": -1.0
        }
        regime_val = regime_weights.get(market_regime.upper(), 0.0)
        
        return {
            "dist_ema20": round(dist_ema20, 3),
            "dist_ema50": round(dist_ema50, 3),
            "dist_ema200": round(dist_ema200, 3),
            "ema_alignment": ema_alignment,
            "rsi_norm": round(rsi_norm, 3),
            "macd_hist_ratio": round(macd_hist_ratio, 3),
            "adx_strength": round(adx_strength, 3),
            "atr_pct": round(atr_pct, 3),
            "bb_width": round(bb_width, 3),
            "volume_surge": round(rvol if rvol is not None else 1.0, 3),
            "breakout_proximity": round(breakout_proximity, 3),
            "rs_20d": round(rs_20d if rs_20d is not None else 0.0, 3),
            "mansfield_rs": round(mansfield_rs if mansfield_rs is not None else 0.0, 3),
            "sector_momentum": round(((sector_momentum or 50.0) - 50.0) / 50.0, 3),
            "candle_score_norm": round(((candle_score or 50.0) - 50.0) / 50.0, 3),
            "regime_val": regime_val
        }
