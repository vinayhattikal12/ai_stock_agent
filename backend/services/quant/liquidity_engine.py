from typing import List, Dict, Any
from backend.models.schemas import Candle

class LiquidityEngine:
    """
    Verifies institutional tradeability, liquidity parameters, and data quality.
    Enforces minimum ₹5 Crore daily turnover for swing eligibility to prevent slippage and illiquidity traps.
    """
    
    MIN_DAILY_TURNOVER_INR = 50_000_000 # ₹5 Crores
    MIN_20D_AVG_VOLUME = 100_000
    
    @classmethod
    def evaluate_liquidity(cls, candles: List[Candle]) -> Dict[str, Any]:
        if not candles or len(candles) < 20:
            return {
                "is_liquid": False,
                "avg_volume_20d": 0,
                "daily_turnover_cr": 0.0,
                "data_quality_score": 0.0,
                "reason": "Insufficient historical candle bars"
            }
            
        recent_20 = candles[-20:]
        avg_volume_20d = int(sum(c.volume for c in recent_20) / len(recent_20))
        latest_price = candles[-1].close
        avg_turnover_inr = avg_volume_20d * latest_price
        turnover_cr = round(avg_turnover_inr / 10_000_000, 2)
        
        # Data Quality checks: gap anomalies or zero volume days
        zero_vol_days = sum(1 for c in recent_20 if c.volume == 0)
        quality_score = 1.0 - (zero_vol_days / 20.0)
        
        is_liquid = (avg_turnover_inr >= cls.MIN_DAILY_TURNOVER_INR) and (avg_volume_20d >= cls.MIN_20D_AVG_VOLUME)
        
        return {
            "is_liquid": is_liquid,
            "avg_volume_20d": avg_volume_20d,
            "daily_turnover_cr": turnover_cr,
            "data_quality_score": quality_score,
            "volume_surge_ratio": round(candles[-1].volume / (avg_volume_20d or 1), 2),
            "reason": "Meets institutional swing turnover requirement" if is_liquid else "Turnover below minimum threshold"
        }
