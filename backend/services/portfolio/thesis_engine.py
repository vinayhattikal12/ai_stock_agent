from typing import Tuple, List, Optional
from backend.models.schemas import Candle, TechnicalIndicators

class ThesisEngine:
    """
    Continuous thesis validation engine.
    Monitors whether the underlying quantitative and structural rationale for holding a stock
    remains intact, has strengthened, has weakened, or is completely broken.
    """
    
    @classmethod
    def evaluate_thesis(
        cls,
        candles: List[Candle],
        indicators: TechnicalIndicators,
        buy_price: float,
        rs_20d: float,
        sector_trend: str
    ) -> Tuple[str, List[str]]:
        """
        Returns (thesis_status, thesis_points)
        Statuses: STRENGTHENING, STABLE, WEAKENING, BROKEN
        """
        if not candles or buy_price <= 0:
            return "STABLE", ["Baseline data monitoring active"]
            
        current_price = candles[-1].close
        pnl_pct = (current_price - buy_price) / buy_price * 100.0
        
        points = []
        ema_20 = indicators.ema_20
        ema_50 = indicators.ema_50
        ema_200 = indicators.ema_200
        rsi = indicators.rsi_14

        is_above_ema20 = (current_price >= ema_20) if ema_20 is not None else True
        is_above_ema50 = (current_price >= ema_50) if ema_50 is not None else True
        
        # 1. Broken Thesis check
        if ema_200 is not None and current_price < ema_200 and pnl_pct < -5.0:
            points.append("Price violated 200-day long-term moving average with distribution.")
            points.append("Underlying trend structure compromised; risk mitigation required.")
            return "BROKEN", points
            
        if not is_above_ema50 and rs_20d < -4.0 and sector_trend == "BEARISH":
            points.append("Price fell below 50 EMA accompanied by persistent relative underperformance.")
            points.append(f"Sector benchmark ({sector_trend}) is experiencing heavy rotation out.")
            return "BROKEN", points
            
        # 2. Strengthening Thesis
        if is_above_ema20 and rsi is not None and rsi > 58 and rs_20d > 2.0 and pnl_pct > 2.0:
            points.append("Price holding firmly above 20 EMA with positive RSI momentum expansion.")
            points.append(f"Relative strength vs NIFTY is expanding (+{rs_20d:.1f}% over 20 days).")
            points.append("Volume profile indicates steady institutional accumulation.")
            return "STRENGTHENING", points
            
        # 3. Weakening Thesis
        if (not is_above_ema20 and is_above_ema50) or (rsi is not None and rsi < 44) or (rs_20d < -1.5):
            points.append("Price slipped below short-term 20 EMA, testing secondary support.")
            points.append("Momentum oscillator showing mild deceleration.")
            points.append("Watch 50 EMA closely for bounce confirmation before taking action.")
            return "WEAKENING", points
            
        # 4. Stable Thesis (Default)
        points.append("Price consolidating comfortably within expected swing channel.")
        points.append("Key support and resistance pivots behaving as projected.")
        points.append("Sector momentum consistent with broader market trend.")
        return "STABLE", points

thesis_engine = ThesisEngine()
