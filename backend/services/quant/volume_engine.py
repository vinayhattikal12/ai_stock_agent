from typing import List
from backend.models.schemas import Candle, VolumeProfileMetrics

class VolumeEngine:
    """
    Analyzes volume behavior, Relative Volume (RVOL), institutional accumulation/distribution,
    and volume dry-up during consolidations.
    """
    
    @staticmethod
    def calculate_volume_metrics(candles: List[Candle]) -> VolumeProfileMetrics:
        if not candles or len(candles) < 5:
            return VolumeProfileMetrics(
                rvol_20d=1.0,
                volume_5d_vs_20d_ratio=1.0,
                breakout_volume_surge=1.0,
                volume_trend="NEUTRAL",
                avg_turnover_cr_20d=10.0,
                is_volume_confirmed=False
            )
            
        n_20 = min(len(candles), 20)
        n_5 = min(len(candles), 5)
        
        current_candle = candles[-1]
        current_vol = float(current_candle.volume)
        current_price = current_candle.close
        
        # 20-day SMA volume
        vols_20 = [float(c.volume) for c in candles[-n_20:]]
        avg_vol_20 = sum(vols_20) / len(vols_20) if sum(vols_20) > 0 else 1.0
        
        # 5-day SMA volume
        vols_5 = [float(c.volume) for c in candles[-n_5:]]
        avg_vol_5 = sum(vols_5) / len(vols_5) if sum(vols_5) > 0 else 1.0
        
        # RVOL (Relative Volume vs 20-day average)
        rvol_20d = round(current_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
        
        # 5D vs 20D volume ratio
        vol_5d_vs_20d = round(avg_vol_5 / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
        
        # Turnover in INR Crores (Volume * Close / 10,000,000)
        avg_turnover_cr = round((avg_vol_20 * current_price) / 10_000_000.0, 2)
        
        # Accumulation vs Distribution analysis over last 10 sessions
        n_10 = min(len(candles), 10)
        up_volume = 0.0
        down_volume = 0.0
        for i in range(-n_10, 0):
            c = candles[i]
            if c.close >= c.open:
                up_volume += float(c.volume)
            else:
                down_volume += float(c.volume)
                
        # Classify volume trend
        if rvol_20d < 0.65 and vol_5d_vs_20d < 0.85:
            volume_trend = "CONTRACTION"
        elif up_volume > (down_volume * 1.35) and current_candle.close >= current_candle.open:
            volume_trend = "ACCUMULATION"
        elif down_volume > (up_volume * 1.35) and current_candle.close < current_candle.open:
            volume_trend = "DISTRIBUTION"
        else:
            volume_trend = "NEUTRAL"
            
        # Breakout volume surge
        breakout_surge = rvol_20d if current_candle.close >= current_candle.open else round(rvol_20d * 0.5, 2)
        
        # Volume confirmed trigger
        is_confirmed = (rvol_20d >= 1.30 and current_candle.close >= current_candle.open) or (
            volume_trend == "ACCUMULATION" and rvol_20d >= 1.0
        )
        
        return VolumeProfileMetrics(
            rvol_20d=rvol_20d,
            volume_5d_vs_20d_ratio=vol_5d_vs_20d,
            breakout_volume_surge=breakout_surge,
            volume_trend=volume_trend,
            avg_turnover_cr_20d=avg_turnover_cr,
            is_volume_confirmed=is_confirmed
        )

volume_engine = VolumeEngine()
