from typing import List
from backend.models.schemas import Candle, VolumeProfileMetrics

class VolumeEngine:
    """
    Analyzes volume behavior, Relative Volume (RVOL), institutional accumulation/distribution,
    pocket pivot signatures, delivery volume estimations, and volume climax/exhaustion conditions.
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
                is_volume_confirmed=False,
                is_volume_climax=False,
                institutional_accumulation_score=50.0,
                delivery_est_ratio=0.45,
                exhaustion_risk="LOW"
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
        up_days = 0
        down_days = 0
        
        for i in range(-n_10, 0):
            c = candles[i]
            if c.close >= c.open:
                up_volume += float(c.volume)
                up_days += 1
            else:
                down_volume += float(c.volume)
                down_days += 1
                
        # Institutional Accumulation Score (0 to 100)
        # Factors: Up/Down Volume ratio, closing location in daily range, volume surge on up-bars
        vol_ratio = (up_volume / (down_volume or 1.0))
        daily_range = current_candle.high - current_candle.low
        close_location = (current_candle.close - current_candle.low) / daily_range if daily_range > 0 else 0.5
        
        raw_acc_score = 50.0 + (min(vol_ratio, 3.0) - 1.0) * 20.0 + (close_location - 0.5) * 30.0
        if rvol_20d >= 1.5 and current_candle.close >= current_candle.open:
            raw_acc_score += 15.0
        inst_acc_score = round(min(max(raw_acc_score, 10.0), 98.0), 1)

        # Estimated Delivery Participation (higher close near high + higher turnover correlates with institutional delivery)
        delivery_est = round(min(max(0.35 + (close_location * 0.25) + (0.10 if rvol_20d > 1.2 else 0.0), 0.20), 0.85), 2)

        # Classify volume trend
        if rvol_20d < 0.65 and vol_5d_vs_20d < 0.85:
            volume_trend = "CONTRACTION"
        elif up_volume > (down_volume * 1.35) and current_candle.close >= current_candle.open:
            volume_trend = "ACCUMULATION"
        elif down_volume > (up_volume * 1.35) and current_candle.close < current_candle.open:
            volume_trend = "DISTRIBUTION"
        else:
            volume_trend = "NEUTRAL"

        # Volume Climax / Exhaustion Risk:
        # Extreme volume spike (> 2.8x RVOL) with either long upper shadow (selling into strength) or extreme gap-up
        upper_shadow = current_candle.high - max(current_candle.open, current_candle.close)
        body_size = abs(current_candle.close - current_candle.open)
        
        is_climax = False
        exhaustion_risk = "LOW"
        
        if rvol_20d >= 2.8:
            if upper_shadow > body_size * 1.2:
                is_climax = True
                exhaustion_risk = "EXTREME"
            elif rvol_20d >= 3.5:
                is_climax = True
                exhaustion_risk = "HIGH"
            else:
                exhaustion_risk = "MODERATE"
        elif rvol_20d >= 2.0 and down_volume > (up_volume * 1.5):
            exhaustion_risk = "MODERATE"

        # Breakout volume surge
        breakout_surge = rvol_20d if current_candle.close >= current_candle.open else round(rvol_20d * 0.5, 2)
        
        # Volume confirmed trigger
        is_confirmed = (rvol_20d >= 1.30 and current_candle.close >= current_candle.open and not is_climax) or (
            volume_trend == "ACCUMULATION" and rvol_20d >= 1.0
        )
        
        return VolumeProfileMetrics(
            rvol_20d=rvol_20d,
            volume_5d_vs_20d_ratio=vol_5d_vs_20d,
            breakout_volume_surge=breakout_surge,
            volume_trend=volume_trend,
            avg_turnover_cr_20d=avg_turnover_cr,
            is_volume_confirmed=is_confirmed,
            is_volume_climax=is_climax,
            institutional_accumulation_score=inst_acc_score,
            delivery_est_ratio=delivery_est,
            exhaustion_risk=exhaustion_risk
        )

volume_engine = VolumeEngine()
