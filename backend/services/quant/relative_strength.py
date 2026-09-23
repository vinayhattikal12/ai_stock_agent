from typing import List, Dict, Tuple, Optional, Any
from backend.models.schemas import Candle, RelativeStrengthMetrics

class RelativeStrengthEngine:
    """
    Computes Mansfield Relative Strength and Alpha metrics against benchmarks (NIFTY 50 and Sector).
    Zero-fallback policy: returns None when stock or benchmark data is insufficient.
    """
    
    @staticmethod
    def calculate_excess_return(
        stock_candles: List[Candle],
        benchmark_candles: List[Candle],
        period: int = 20
    ) -> Optional[float]:
        """
        Calculates outperformance percentage of stock relative to benchmark over N bars.
        Formula: ((Stock_t / Stock_{t-n}) - 1) - ((Bench_t / Bench_{t-n}) - 1) * 100
        """
        if not stock_candles or not benchmark_candles:
            return None
        if len(stock_candles) < period or len(benchmark_candles) < period:
            return None
            
        stock_prev = stock_candles[-period].close
        stock_curr = stock_candles[-1].close
        bench_prev = benchmark_candles[-period].close
        bench_curr = benchmark_candles[-1].close

        if stock_prev <= 0 or bench_prev <= 0:
            return None

        stock_ret = (stock_curr - stock_prev) / stock_prev
        bench_ret = (bench_curr - bench_prev) / bench_prev
        
        rel_strength = (stock_ret - bench_ret) * 100.0
        return round(rel_strength, 2)

    # Alias for backward compatibility
    calculate_relative_performance = calculate_excess_return

    @staticmethod
    def calculate_mansfield_rs(
        stock_candles: List[Candle],
        benchmark_candles: List[Candle],
        period: int = 50
    ) -> Dict[str, Any]:
        """
        Calculates true Mansfield Relative Strength:
        Ratio_t = Stock_t / Benchmark_t
        SMA_Ratio = SMA(Ratio, period)
        Mansfield RS = ((Ratio_t / SMA_Ratio) - 1) * 100
        """
        if not stock_candles or not benchmark_candles:
            return {"mansfield_rs": None, "rs_trend": None, "is_above_zero": False, "status": "UNAVAILABLE"}

        min_len = min(len(stock_candles), len(benchmark_candles))
        if min_len < period + 5:
            return {"mansfield_rs": None, "rs_trend": None, "is_above_zero": False, "status": "UNAVAILABLE"}
        
        ratios = []
        for i in range(min_len):
            s_idx = len(stock_candles) - min_len + i
            b_idx = len(benchmark_candles) - min_len + i
            b_close = benchmark_candles[b_idx].close
            s_close = stock_candles[s_idx].close
            if b_close > 0 and s_close > 0:
                ratios.append(s_close / b_close)
            else:
                ratios.append(1.0)
                
        current_ratio = ratios[-1]
        sma_ratio = sum(ratios[-period:]) / period
        
        if sma_ratio == 0:
            return {"mansfield_rs": None, "rs_trend": None, "is_above_zero": False, "status": "UNAVAILABLE"}
            
        m_rs = ((current_ratio / sma_ratio) - 1.0) * 100.0
        
        prior_ratio = ratios[-5]
        prior_sma_ratio = sum(ratios[-period-5:-5]) / period
        prior_m_rs = ((prior_ratio / prior_sma_ratio) - 1.0) * 100.0 if prior_sma_ratio > 0 else 0.0
        
        rs_trend = round(m_rs - prior_m_rs, 2)
        
        return {
            "mansfield_rs": round(m_rs, 2),
            "rs_trend": rs_trend,
            "is_above_zero": m_rs > 0,
            "status": "AVAILABLE"
        }

    @classmethod
    def evaluate_multi_timeframe_rs(
        cls,
        stock_candles: List[Candle],
        nifty_candles: List[Candle],
        sector_momentum: Optional[float] = None
    ) -> RelativeStrengthMetrics:
        """
        Calculates RS excess returns over 5D, 20D, 50D, 100D periods plus Mansfield RS.
        """
        if not stock_candles or not nifty_candles or len(stock_candles) < 10:
            return RelativeStrengthMetrics(
                excess_return_5d=None,
                excess_return_20d=None,
                excess_return_50d=None,
                excess_return_100d=None,
                mansfield_rs_20d=None,
                mansfield_rs_50d=None,
                mansfield_rs_100d=None,
                sector_relative_strength_20d=None,
                market_relative_strength_20d=None,
                rs_trend="FLAT",
                status="UNAVAILABLE"
            )

        rs_5 = cls.calculate_excess_return(stock_candles, nifty_candles, 5)
        rs_20 = cls.calculate_excess_return(stock_candles, nifty_candles, 20)
        rs_50 = cls.calculate_excess_return(stock_candles, nifty_candles, 50)
        rs_100 = cls.calculate_excess_return(stock_candles, nifty_candles, 100)
        mansfield_50_data = cls.calculate_mansfield_rs(stock_candles, nifty_candles, period=50)
        m_rs_50 = mansfield_50_data.get("mansfield_rs")
        m_rs_trend_val = mansfield_50_data.get("rs_trend")

        rs_trend_str = "FLAT"
        if m_rs_trend_val is not None:
            if m_rs_trend_val > 0.5:
                rs_trend_str = "EXPANDING"
            elif m_rs_trend_val < -0.5:
                rs_trend_str = "DETERIORATING"

        sector_rs = None
        if rs_20 is not None and sector_momentum is not None:
            sector_rs = round(rs_20 - (sector_momentum - 50.0) / 10.0, 2)

        return RelativeStrengthMetrics(
            excess_return_5d=rs_5,
            excess_return_20d=rs_20,
            excess_return_50d=rs_50,
            excess_return_100d=rs_100,
            mansfield_rs_20d=rs_20,
            mansfield_rs_50d=m_rs_50,
            mansfield_rs_100d=rs_100,
            sector_relative_strength_20d=sector_rs,
            market_relative_strength_20d=rs_20,
            rs_trend=rs_trend_str,
            status="AVAILABLE" if m_rs_50 is not None else "PARTIAL"
        )

relative_strength_engine = RelativeStrengthEngine()
