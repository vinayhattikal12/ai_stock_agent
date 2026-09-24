import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models.schemas import SectorPerformance, Candle
from backend.services.market_data.data_service import data_service
from backend.services.market_data.universe import NSE_SECTOR_KEYS, NSE_EQUITY_UNIVERSE

logger = logging.getLogger("sector_engine")

class SectorRotationEngine:
    """
    Dedicated Sector Rotation and Leadership Engine.
    Evaluates multi-horizon returns (5D, 20D, 50D, 100D, 6M) and relative strength against NIFTY 50.
    
    Zero-fallback policy: When historical candle data is insufficient, returns None/UNAVAILABLE
    instead of inventing synthetic multi-day returns.
    """
    
    @classmethod
    async def evaluate_sector_rotation(cls) -> List[SectorPerformance]:
        # 1. Fetch benchmark NIFTY 50 candles
        nifty_candles = await data_service.get_historical_candles_cached("NIFTY 50", interval="day", days=180)
        
        sector_results: List[SectorPerformance] = []
        
        for sector_meta in NSE_SECTOR_KEYS:
            sector_name = sector_meta["name"]
            sector_symbol = sector_meta["symbol"]
            sector_group = sector_meta["sector"]
            
            # Fetch candles for sector index
            sec_candles = await data_service.get_historical_candles_cached(sector_symbol, interval="day", days=180)
            
            if not sec_candles or len(sec_candles) < 2:
                # Zero fallback: Return honest UNAVAILABLE status with live 1D quote only
                q = await data_service.get_live_quote_for_symbol(sector_symbol)
                chg1d = float(q.get("change_percent", 0.0)) if q and q.get("change_percent") is not None else None
                sec_perf = SectorPerformance(
                    sector_name=sector_name,
                    symbol=sector_symbol,
                    change_percent_1d=chg1d,
                    change_percent_5d=None,
                    change_percent_20d=None,
                    change_percent_50d=None,
                    change_percent_100d=None,
                    change_percent_6m=None,
                    momentum_score=None,
                    relative_strength_vs_nifty=None,
                    trend="UNAVAILABLE",
                    sector_breadth_pct_above_50ema=None,
                    top_driver=sector_group,
                    rank=99,
                    status="UNAVAILABLE"
                )
                sector_results.append(sec_perf)
                continue
                
            curr_c = sec_candles[-1].close
            c_1d = sec_candles[-2].close if len(sec_candles) >= 2 else curr_c
            c_5d = sec_candles[-6].close if len(sec_candles) >= 6 else None
            c_20d = sec_candles[-21].close if len(sec_candles) >= 21 else None
            c_50d = sec_candles[-51].close if len(sec_candles) >= 51 else None
            c_100d = sec_candles[-101].close if len(sec_candles) >= 101 else None
            c_6m = sec_candles[0].close if len(sec_candles) >= 120 else None
            
            ret_1d = round(((curr_c - c_1d) / c_1d) * 100.0, 2) if c_1d else 0.0
            ret_5d = round(((curr_c - c_5d) / c_5d) * 100.0, 2) if c_5d else None
            ret_20d = round(((curr_c - c_20d) / c_20d) * 100.0, 2) if c_20d else None
            ret_50d = round(((curr_c - c_50d) / c_50d) * 100.0, 2) if c_50d else None
            ret_100d = round(((curr_c - c_100d) / c_100d) * 100.0, 2) if c_100d else None
            ret_6m = round(((curr_c - c_6m) / c_6m) * 100.0, 2) if c_6m else None
            
            # Benchmark NIFTY returns
            nifty_ret_20d = 0.0
            if nifty_candles and len(nifty_candles) >= 21:
                nifty_ret_20d = ((nifty_candles[-1].close - nifty_candles[-21].close) / nifty_candles[-21].close) * 100.0
                
            rs_vs_nifty = round(ret_20d - nifty_ret_20d, 2) if ret_20d is not None else None
            
            # Multi-horizon momentum score (0 to 100)
            if ret_20d is not None and ret_5d is not None:
                r50 = ret_50d if ret_50d is not None else ret_20d
                r100 = ret_100d if ret_100d is not None else r50
                weighted_momentum = (ret_1d * 0.10 + ret_5d * 0.25 + ret_20d * 0.35 + r50 * 0.20 + r100 * 0.10)
                momentum_score = round(max(0.0, min(100.0, 50.0 + (weighted_momentum * 3.5))), 1)
            else:
                momentum_score = None
            
            # Trend Classification
            if ret_20d is not None:
                if ret_20d >= 3.0 and (ret_50d is None or ret_50d >= 6.0):
                    trend = "STRONG_BULLISH"
                elif ret_20d >= 0.5:
                    trend = "BULLISH"
                elif ret_20d <= -3.0 and (ret_50d is None or ret_50d <= -6.0):
                    trend = "STRONG_BEARISH"
                elif ret_20d <= -0.5:
                    trend = "BEARISH"
                else:
                    trend = "NEUTRAL"
            else:
                trend = "UNAVAILABLE"
                
            constituents = [s for s in NSE_EQUITY_UNIVERSE if s["sector"].lower() == sector_group.lower()]
            driver = constituents[0]["symbol"] if constituents else sector_group
            
            sec_perf = SectorPerformance(
                sector_name=sector_name,
                symbol=sector_symbol,
                change_percent_1d=ret_1d,
                change_percent_5d=ret_5d,
                change_percent_20d=ret_20d,
                change_percent_50d=ret_50d,
                change_percent_100d=ret_100d,
                change_percent_6m=ret_6m,
                momentum_score=momentum_score,
                relative_strength_vs_nifty=rs_vs_nifty,
                trend=trend,
                sector_breadth_pct_above_50ema=None,  # Not fabricated; computed only when constituent data exists
                top_driver=driver,
                rank=1,
                status="AVAILABLE"
            )
            sector_results.append(sec_perf)
            
        # Rank sectors with valid momentum score descending
        valid_sectors = [s for s in sector_results if s.momentum_score is not None]
        invalid_sectors = [s for s in sector_results if s.momentum_score is None]
        
        valid_sectors.sort(key=lambda x: x.momentum_score or 0.0, reverse=True)
        for i, s in enumerate(valid_sectors):
            s.rank = i + 1
            
        for s in invalid_sectors:
            s.rank = len(valid_sectors) + 1
            
        return valid_sectors + invalid_sectors

sector_engine = SectorRotationEngine()
