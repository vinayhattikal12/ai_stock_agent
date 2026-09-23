from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from backend.models.schemas import Candle, MarketIndexQuote

class MarketDataProvider(ABC):
    """
    Abstract interface for market data operations.
    Decouples core analytical and quantitative engines from specific broker API implementations.
    """
    
    @abstractmethod
    async def get_instruments(self, exchange: str = "NSE_EQ") -> List[Dict[str, Any]]:
        """Fetch instrument master catalog for the specified exchange."""
        pass

    @abstractmethod
    async def get_live_quote(self, instrument_keys: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch full quote (LTP, OHLC, volume, depth) for one or multiple instrument keys."""
        pass

    @abstractmethod
    async def get_historical_candles(
        self,
        instrument_key: str,
        interval: str = "day",
        to_date: Optional[str] = None,
        from_date: Optional[str] = None
    ) -> List[Candle]:
        """Fetch historical OHLCV candlestick records."""
        pass

    @abstractmethod
    async def get_intraday_candles(
        self,
        instrument_key: str,
        interval: str = "1minute"
    ) -> List[Candle]:
        """Fetch today's intraday OHLCV candles."""
        pass

    @abstractmethod
    async def get_market_depth(self, instrument_key: str) -> Dict[str, Any]:
        """Fetch Level 2 Market Depth (top 5 bids/asks) where available."""
        pass
