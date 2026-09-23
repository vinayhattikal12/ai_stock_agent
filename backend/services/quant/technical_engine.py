import math
from typing import List, Dict, Any, Tuple, Optional
from backend.models.schemas import Candle, TechnicalIndicators

class TechnicalEngine:
    """
    Deterministic quantitative technical analysis engine.
    Zero-fallback policy: returns None when historical observations are insufficient.
    Never returns fake placeholders (e.g. 0.0, 50.0, or 10.0) when calculations fail.
    """

    @staticmethod
    def calculate_sma(closes: List[float], period: int) -> Optional[float]:
        if not closes or len(closes) < period or period <= 0:
            return None
        return round(sum(closes[-period:]) / period, 2)

    @staticmethod
    def calculate_ema(closes: List[float], period: int) -> Optional[float]:
        if not closes or len(closes) < period or period <= 0:
            return None
            
        multiplier = 2.0 / (period + 1.0)
        ema = sum(closes[:period]) / period
        for price in closes[period:]:
            ema = (price - ema) * multiplier + ema
        return round(ema, 2)

    @staticmethod
    def calculate_rsi(closes: List[float], period: int = 14) -> Optional[float]:
        if not closes or len(closes) < period + 1 or period <= 0:
            return None
            
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff > 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(diff))
                
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(rsi, 2)

    @staticmethod
    def calculate_macd(
        closes: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if not closes or len(closes) < slow + signal:
            return None, None, None
            
        fast_mult = 2.0 / (fast + 1.0)
        slow_mult = 2.0 / (slow + 1.0)
        
        fast_ema = sum(closes[:fast]) / fast
        slow_ema = sum(closes[:slow]) / slow
        
        macd_series = []
        for p in closes[fast:slow]:
            fast_ema = (p - fast_ema) * fast_mult + fast_ema
            
        for p in closes[slow:]:
            fast_ema = (p - fast_ema) * fast_mult + fast_ema
            slow_ema = (p - slow_ema) * slow_mult + slow_ema
            macd_series.append(fast_ema - slow_ema)
            
        if not macd_series or len(macd_series) < signal:
            return None, None, None
            
        current_macd = macd_series[-1]
        sig_mult = 2.0 / (signal + 1.0)
        sig_ema = sum(macd_series[:signal]) / signal
        
        for m in macd_series[signal:]:
            sig_ema = (m - sig_ema) * sig_mult + sig_ema
            
        hist = current_macd - sig_ema
        return round(current_macd, 2), round(sig_ema, 2), round(hist, 2)

    @staticmethod
    def calculate_atr(candles: List[Candle], period: int = 14) -> Optional[float]:
        if not candles or len(candles) < period + 1:
            return None
            
        tr_list = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev = candles[i - 1]
            tr = max(
                c.high - c.low,
                abs(c.high - prev.close),
                abs(c.low - prev.close)
            )
            tr_list.append(tr)
            
        if len(tr_list) < period:
            return None
            
        atr = sum(tr_list[:period]) / period
        for tr in tr_list[period:]:
            atr = (atr * (period - 1) + tr) / period
        return round(atr, 2)

    @staticmethod
    def calculate_adx(candles: List[Candle], period: int = 14) -> Optional[float]:
        if not candles or len(candles) < period * 2:
            return None
            
        plus_dm = []
        minus_dm = []
        tr_list = []
        
        for i in range(1, len(candles)):
            curr = candles[i]
            prev = candles[i - 1]
            
            up_move = curr.high - prev.high
            down_move = prev.low - curr.low
            
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)
            
            tr = max(curr.high - curr.low, abs(curr.high - prev.close), abs(curr.low - prev.close))
            tr_list.append(tr)
            
        tr_smooth = sum(tr_list[:period])
        plus_smooth = sum(plus_dm[:period])
        minus_smooth = sum(minus_dm[:period])
        
        dx_list = []
        for i in range(period, len(tr_list)):
            tr_smooth = tr_smooth - (tr_smooth / period) + tr_list[i]
            plus_smooth = plus_smooth - (plus_smooth / period) + plus_dm[i]
            minus_smooth = minus_smooth - (minus_smooth / period) + minus_dm[i]
            
            if tr_smooth > 0:
                plus_di = 100 * (plus_smooth / tr_smooth)
                minus_di = 100 * (minus_smooth / tr_smooth)
                di_sum = plus_di + minus_di
                dx = 100 * (abs(plus_di - minus_di) / di_sum) if di_sum > 0 else 0
                dx_list.append(dx)
                
        if not dx_list or len(dx_list) < period:
            return None
            
        adx = sum(dx_list[:period]) / period
        for d in dx_list[period:]:
            adx = (adx * (period - 1) + d) / period
        return round(adx, 2)

    @staticmethod
    def calculate_bollinger_bands(
        closes: List[float],
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if not closes or len(closes) < period:
            return None, None, None
            
        slice_vals = closes[-period:]
        sma = sum(slice_vals) / period
        variance = sum((x - sma) ** 2 for x in slice_vals) / period
        std_dev = math.sqrt(variance)
        
        upper = sma + (num_std * std_dev)
        lower = sma - (num_std * std_dev)
        return round(upper, 2), round(sma, 2), round(lower, 2)

    @staticmethod
    def calculate_support_resistance(candles: List[Candle], num_levels: int = 3) -> Tuple[List[float], List[float]]:
        """
        Calculates distinct price support and resistance clusters using pivot highs and lows.
        Zero-fallback: returns empty lists if candle history is insufficient.
        """
        if not candles or len(candles) < 20:
            return [], []
            
        current_price = candles[-1].close
        pivot_highs = []
        pivot_lows = []
        
        for i in range(2, len(candles) - 2):
            high = candles[i].high
            low = candles[i].low
            
            if (high > candles[i-1].high and high > candles[i-2].high and 
                high > candles[i+1].high and high > candles[i+2].high):
                pivot_highs.append(high)
                
            if (low < candles[i-1].low and low < candles[i-2].low and 
                low < candles[i+1].low and low < candles[i+2].low):
                pivot_lows.append(low)
                
        resistances = sorted([p for p in pivot_highs if p > current_price * 1.005])[:num_levels]
        supports = sorted([p for p in pivot_lows if p < current_price * 0.995], reverse=True)[:num_levels]
        
        return [round(s, 2) for s in supports], [round(r, 2) for r in resistances]

    @classmethod
    def evaluate_indicators(cls, candles: List[Candle]) -> TechnicalIndicators:
        """
        Evaluates full suite of technical indicators.
        Marks status as AVAILABLE, PARTIAL, or UNAVAILABLE with zero synthetic fallbacks.
        """
        if not candles or len(candles) < 14:
            return TechnicalIndicators(
                sma_20=None, sma_50=None, sma_200=None,
                ema_20=None, ema_50=None, ema_200=None,
                rsi_14=None, macd_line=None, macd_signal=None, macd_hist=None,
                atr_14=None, adx_14=None,
                bb_upper=None, bb_middle=None, bb_lower=None,
                supertrend=None, supertrend_direction="NEUTRAL",
                support_levels=[], resistance_levels=[],
                status="UNAVAILABLE"
            )

        closes = [c.close for c in candles]
        curr_price = closes[-1]
        
        sma_20 = cls.calculate_sma(closes, 20)
        sma_50 = cls.calculate_sma(closes, 50)
        sma_200 = cls.calculate_sma(closes, 200)
        
        ema_20 = cls.calculate_ema(closes, 20)
        ema_50 = cls.calculate_ema(closes, 50)
        ema_200 = cls.calculate_ema(closes, 200)
        
        rsi_14 = cls.calculate_rsi(closes, 14)
        macd_line, macd_signal, macd_hist = cls.calculate_macd(closes)
        atr_14 = cls.calculate_atr(candles, 14)
        adx_14 = cls.calculate_adx(candles, 14)
        bb_upper, bb_mid, bb_lower = cls.calculate_bollinger_bands(closes, 20, 2.0)
        
        supports, resistances = cls.calculate_support_resistance(candles)
        
        supertrend_dir = "NEUTRAL"
        supertrend_val = None
        if ema_20 is not None and atr_14 is not None:
            supertrend_dir = "BULLISH" if curr_price >= ema_20 else "BEARISH"
            supertrend_val = round(curr_price - (atr_14 * 2.0) if supertrend_dir == "BULLISH" else curr_price + (atr_14 * 2.0), 2)
            
        status = "AVAILABLE" if (len(candles) >= 120 and sma_200 is not None) else "PARTIAL"
        
        return TechnicalIndicators(
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            rsi_14=rsi_14,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            atr_14=atr_14,
            adx_14=adx_14,
            bb_upper=bb_upper,
            bb_middle=bb_mid,
            bb_lower=bb_lower,
            supertrend=supertrend_val,
            supertrend_direction=supertrend_dir,
            support_levels=supports,
            resistance_levels=resistances,
            status=status
        )

technical_engine = TechnicalEngine()
