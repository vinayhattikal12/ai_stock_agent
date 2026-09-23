from typing import List, Tuple
from backend.models.schemas import Candle, CandlestickPattern

class CandlestickEngine:
    """
    Pattern recognition engine for Japanese Candlesticks with trend context validation
    and contextual Candle Confirmation Score (0-100).
    """
    
    @staticmethod
    def identify_patterns(candles: List[Candle]) -> List[CandlestickPattern]:
        if len(candles) < 3:
            return []
            
        patterns: List[CandlestickPattern] = []
        c = candles[-1]       # Current candle
        c_prev = candles[-2]  # Previous candle
        c_prev2 = candles[-3] # Two candles back
        
        # Dimensions
        c_body = abs(c.close - c.open)
        c_range = c.high - c.low
        if c_range == 0:
            c_range = 0.001
            
        c_upper_shadow = c.high - max(c.open, c.close)
        c_lower_shadow = min(c.open, c.close) - c.low
        
        prev_body = abs(c_prev.close - c_prev.open)
        prev_range = c_prev.high - c_prev.low
        if prev_range == 0:
            prev_range = 0.001
            
        is_uptrend = c_prev.close > candles[-5].close if len(candles) >= 5 else True
        is_downtrend = c_prev.close < candles[-5].close if len(candles) >= 5 else False

        # 1. Bullish Hammer (Long lower shadow >= 2x body, tiny upper shadow, occurring at support or after pullback)
        if (c_lower_shadow >= 2.0 * c_body and 
            c_upper_shadow <= 0.25 * c_body and 
            c_body > 0 and 
            (is_downtrend or c.low <= min([x.low for x in candles[-5:]]))):
            patterns.append(CandlestickPattern(
                name="Hammer",
                pattern_type="BULLISH",
                reliability="HIGH",
                description="Strong rejection of lower prices after pullback; buyers regained control."
            ))

        # 2. Shooting Star (Long upper shadow >= 2x body, tiny lower shadow, occurring after uptrend)
        if (c_upper_shadow >= 2.0 * c_body and 
            c_lower_shadow <= 0.25 * c_body and 
            c_body > 0 and 
            is_uptrend):
            patterns.append(CandlestickPattern(
                name="Shooting Star",
                pattern_type="BEARISH",
                reliability="HIGH",
                description="Failed breakout with strong rejection from highs; selling pressure emerging."
            ))

        # 3. Bullish Engulfing
        if (c_prev.close < c_prev.open and # previous was red
            c.close > c.open and           # current is green
            c.open <= c_prev.close and 
            c.close >= c_prev.open and 
            c_body > prev_body):
            patterns.append(CandlestickPattern(
                name="Bullish Engulfing",
                pattern_type="BULLISH",
                reliability="HIGH",
                description="Large green real body completely engulfs prior bearish candle."
            ))

        # 4. Bearish Engulfing
        if (c_prev.close > c_prev.open and # previous was green
            c.close < c.open and           # current is red
            c.open >= c_prev.close and 
            c.close <= c_prev.open and 
            c_body > prev_body):
            patterns.append(CandlestickPattern(
                name="Bearish Engulfing",
                pattern_type="BEARISH",
                reliability="HIGH",
                description="Bearish expansion candle completely engulfs previous candle body."
            ))

        # 5. Morning Star (3-candle bullish reversal)
        if (c_prev2.close < c_prev2.open and # day 1 bear
            prev_body <= prev_range * 0.35 and # day 2 star/indecision
            c.close > c.open and c.close > (c_prev2.open + c_prev2.close) / 2): # day 3 strong bull
            patterns.append(CandlestickPattern(
                name="Morning Star",
                pattern_type="BULLISH",
                reliability="HIGH",
                description="Classic 3-candle bottom reversal confirming transition from selling to buying."
            ))

        # 6. Marubozu (Very strong momentum candle with virtually no shadows)
        if c_body >= c_range * 0.88 and c_range > (sum(abs(x.high - x.low) for x in candles[-10:]) / 10):
            if c.close > c.open:
                patterns.append(CandlestickPattern(
                    name="Bullish Marubozu",
                    pattern_type="BULLISH",
                    reliability="HIGH",
                    description="Decisive directional buying from open to close without significant pushback."
                ))
            else:
                patterns.append(CandlestickPattern(
                    name="Bearish Marubozu",
                    pattern_type="BEARISH",
                    reliability="HIGH",
                    description="Aggressive institutional selling pressure throughout the session."
                ))

        # 7. Pin Bar / Long Shadow Rejection
        if c_lower_shadow >= c_range * 0.60:
            patterns.append(CandlestickPattern(
                name="Bullish Pin Bar",
                pattern_type="BULLISH",
                reliability="MEDIUM",
                description="Deep intraday dip aggressively bought up before session close."
            ))

        # 8. Inside Bar (Volatility contraction)
        if c.high < c_prev.high and c.low > c_prev.low:
            patterns.append(CandlestickPattern(
                name="Inside Bar (Contraction)",
                pattern_type="INDECISION",
                reliability="MEDIUM",
                description="Coiling price action inside previous candle's range, anticipating directional expansion."
            ))

        # 9. Doji (Indecision)
        if c_body <= c_range * 0.10:
            patterns.append(CandlestickPattern(
                name="Doji",
                pattern_type="INDECISION",
                reliability="LOW",
                description="Equilibrium between buyers and sellers, watch for subsequent breakout trigger."
            ))

        return patterns

    @classmethod
    def calculate_candle_confirmation_score(cls, candles: List[Candle]) -> Tuple[float, List[CandlestickPattern]]:
        """
        Computes a 0-100 Candle Confirmation Score reflecting bullish closing strength,
        expansion quality, rejection of lower prices, and detected patterns.
        """
        if len(candles) < 5:
            return 50.0, []

        patterns = cls.identify_patterns(candles)
        c = candles[-1]
        c_range = c.high - c.low
        if c_range == 0:
            c_range = 0.001
        
        # 1. Close Location in Range (0 to 100): Where did price close relative to high/low?
        # High close (near 1.0) = strong buyer domination.
        close_pos = (c.close - c.low) / c_range
        base_score = close_pos * 40.0  # Up to 40 pts

        # 2. Bullish vs Bearish Direction
        is_green = c.close >= c.open
        if is_green:
            body_ratio = (c.close - c.open) / c_range
            base_score += 15.0 + (body_ratio * 15.0) # Up to 30 pts for strong green body
        else:
            body_ratio = (c.open - c.close) / c_range
            base_score -= (body_ratio * 20.0) # Penalty for large red body

        # 3. Lower Shadow Buying Pressure
        c_lower_shadow = min(c.open, c.close) - c.low
        lower_shadow_ratio = c_lower_shadow / c_range
        if lower_shadow_ratio >= 0.35:
            base_score += lower_shadow_ratio * 15.0 # Up to 15 pts for lower shadow dip buying

        # 4. Pattern Boosts / Penalties
        for p in patterns:
            if p.pattern_type == "BULLISH":
                if p.reliability == "HIGH":
                    base_score += 15.0
                else:
                    base_score += 8.0
            elif p.pattern_type == "BEARISH":
                if p.reliability == "HIGH":
                    base_score -= 25.0
                else:
                    base_score -= 12.0

        # Bound score between 0 and 100
        score = max(0.0, min(100.0, base_score))
        return round(score, 1), patterns
