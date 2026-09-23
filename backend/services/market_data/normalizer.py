from datetime import datetime
from typing import List, Dict, Any
from backend.models.schemas import Candle

class DataNormalizer:
    """
    Standardizes disparate data provider responses into canonical internal domain models.
    """
    
    @staticmethod
    def normalize_upstox_candles(raw_candles: List[List[Any]]) -> List[Candle]:
        """
        Upstox API v2 returns candle records formatted as:
        [timestamp (ISO-8601 string), open (float), high (float), low (float), close (float), volume (int), open_interest (int)]
        Note: Upstox typically returns newest candle first. We sort chronologically (oldest -> newest).
        """
        if not raw_candles:
            return []
        
        candles: List[Candle] = []
        for item in raw_candles:
            try:
                # Parse timestamp
                ts_str = item[0]
                if isinstance(ts_str, str):
                    # Handle formats like 2026-09-23T00:00:00+05:30 or 2026-09-23T09:15:00+05:30
                    if "+" in ts_str or "-" in ts_str[10:]:
                        # strip offset or parse with datetime.fromisoformat
                        ts = datetime.fromisoformat(ts_str)
                    else:
                        ts = datetime.fromisoformat(ts_str)
                elif isinstance(ts_str, datetime):
                    ts = ts_str
                else:
                    continue
                
                open_val = float(item[1])
                high_val = float(item[2])
                low_val = float(item[3])
                close_val = float(item[4])
                volume_val = int(item[5])
                oi_val = int(item[6]) if len(item) > 6 and item[6] is not None else 0
                
                candles.append(Candle(
                    timestamp=ts,
                    open=open_val,
                    high=high_val,
                    low=low_val,
                    close=close_val,
                    volume=volume_val,
                    open_interest=oi_val
                ))
            except Exception:
                continue
        
        # Sort ascending by timestamp (historical order for technical calculations)
        candles.sort(key=lambda c: c.timestamp)
        return candles

    @staticmethod
    def normalize_upstox_quote(symbol: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Upstox v2 quote object to standard dictionary.
        """
        try:
            ohlc = raw_data.get("ohlc", {})
            ltp = float(raw_data.get("last_price", ohlc.get("close", 0.0)))
            close = float(ohlc.get("close", ltp))
            prev_close = float(raw_data.get("prev_close", close))
            open_price = float(ohlc.get("open", ltp))
            high_price = float(ohlc.get("high", ltp))
            low_price = float(ohlc.get("low", ltp))
            volume = int(raw_data.get("volume", 0))
            
            change = ltp - prev_close if prev_close else 0.0
            change_percent = (change / prev_close * 100.0) if prev_close else 0.0
            
            return {
                "symbol": symbol,
                "price": ltp,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "prev_close": prev_close,
                "volume": volume,
                "depth": raw_data.get("depth", {}),
                "timestamp": datetime.utcnow()
            }
        except Exception:
            return {
                "symbol": symbol,
                "price": 0.0,
                "change": 0.0,
                "change_percent": 0.0,
                "open": 0.0,
                "high": 0.0,
                "low": 0.0,
                "prev_close": 0.0,
                "volume": 0,
                "depth": {},
                "timestamp": datetime.utcnow()
            }
