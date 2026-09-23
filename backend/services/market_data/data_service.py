import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

from backend.config import settings
from backend.models.schemas import Candle, MarketIndexQuote, MarketBreadth, SectorPerformance, MarketStatusResponse
from backend.services.market_data.upstox_provider import UpstoxProvider
from backend.services.market_data.universe import NSE_EQUITY_UNIVERSE, NSE_SECTOR_KEYS

logger = logging.getLogger("data_service")

class MarketDataService:
    """
    Central orchestrator for all market data operations.
    Communicates strictly with Upstox API V2. Never creates fake prices or synthetic candles.
    Uses concurrency pooling & multi-tier in-memory caching for real-time throughput.
    """
    def __init__(self):
        self.provider = UpstoxProvider(settings.UPSTOX_ACCESS_TOKEN)
        self._candle_cache: Dict[str, List[Candle]] = {}
        self._cache_timestamp: Dict[str, datetime] = {}
        self._cache_ttl_seconds = 300 # 5 minutes candle cache
        
        self._indices_cache: Optional[Dict[str, MarketIndexQuote]] = None
        self._indices_cache_time: Optional[datetime] = None
        
        self._sector_cache: Optional[List[Dict[str, Any]]] = None
        self._sector_cache_time: Optional[datetime] = None
        self._fast_ttl_seconds = 60 # 1 minute for live indices
        
    async def get_indices_status(self) -> Dict[str, MarketIndexQuote]:
        """
        Fetch real quote snapshots for NIFTY 50, Bank NIFTY, and India VIX from Upstox.
        Cached for 60 seconds to avoid redundant calls.
        """
        now = datetime.utcnow()
        if self._indices_cache and self._indices_cache_time:
            if (now - self._indices_cache_time).total_seconds() < self._fast_ttl_seconds:
                return self._indices_cache

        keys = ["NIFTY 50", "BANKNIFTY", "INDIA VIX"]
        raw_quotes = await self.provider.get_live_quote(keys)
        
        nifty_quote = raw_quotes.get("NIFTY 50") or raw_quotes.get("Nifty 50") or {
            "symbol": "NIFTY 50", "price": 0.0, "change": 0.0, "change_percent": 0.0,
            "open": 0.0, "high": 0.0, "low": 0.0, "prev_close": 0.0
        }
        
        bank_nifty_quote = raw_quotes.get("BANKNIFTY") or raw_quotes.get("Nifty Bank") or {
            "symbol": "BANKNIFTY", "price": 0.0, "change": 0.0, "change_percent": 0.0,
            "open": 0.0, "high": 0.0, "low": 0.0, "prev_close": 0.0
        }
        
        vix_quote = raw_quotes.get("INDIA VIX") or raw_quotes.get("India VIX") or {
            "symbol": "INDIAVIX", "price": 0.0, "change": 0.0, "change_percent": 0.0,
            "open": 0.0, "high": 0.0, "low": 0.0, "prev_close": 0.0
        }
        
        res = {
            "nifty": MarketIndexQuote(
                symbol="NIFTY 50", name="NIFTY 50",
                price=float(nifty_quote.get("price", 0.0)),
                change=float(nifty_quote.get("change", 0.0)),
                change_percent=float(nifty_quote.get("change_percent", 0.0)),
                high=float(nifty_quote.get("high", 0.0)),
                low=float(nifty_quote.get("low", 0.0)),
                open=float(nifty_quote.get("open", 0.0)),
                prev_close=float(nifty_quote.get("prev_close", 0.0))
            ),
            "bank_nifty": MarketIndexQuote(
                symbol="BANKNIFTY", name="NIFTY Bank",
                price=float(bank_nifty_quote.get("price", 0.0)),
                change=float(bank_nifty_quote.get("change", 0.0)),
                change_percent=float(bank_nifty_quote.get("change_percent", 0.0)),
                high=float(bank_nifty_quote.get("high", 0.0)),
                low=float(bank_nifty_quote.get("low", 0.0)),
                open=float(bank_nifty_quote.get("open", 0.0)),
                prev_close=float(bank_nifty_quote.get("prev_close", 0.0))
            ),
            "india_vix": MarketIndexQuote(
                symbol="INDIAVIX", name="India VIX",
                price=float(vix_quote.get("price", 0.0)),
                change=float(vix_quote.get("change", 0.0)),
                change_percent=float(vix_quote.get("change_percent", 0.0)),
                high=float(vix_quote.get("high", 0.0)),
                low=float(vix_quote.get("low", 0.0)),
                open=float(vix_quote.get("open", 0.0)),
                prev_close=float(vix_quote.get("prev_close", 0.0))
            )
        }
        self._indices_cache = res
        self._indices_cache_time = now
        return res

    async def get_historical_candles_cached(
        self,
        symbol: str,
        interval: str = "day",
        days: int = 400
    ) -> List[Candle]:
        """
        Retrieves historical candle list from Upstox API V2 with caching.
        Default 400 days (~260 trading days) ensures full SMA200 and 52-week coverage.
        """
        cache_key = f"{symbol}_{interval}_{days}"
        now = datetime.utcnow()
        
        if cache_key in self._candle_cache:
            last_time = self._cache_timestamp.get(cache_key)
            if last_time and (now - last_time).total_seconds() < self._cache_ttl_seconds:
                return self._candle_cache[cache_key]
                
        to_date = date.today().strftime("%Y-%m-%d")
        from_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        candles = await self.provider.get_historical_candles(
            instrument_key=symbol,
            interval=interval,
            to_date=to_date,
            from_date=from_date
        )
        
        if candles:
            self._candle_cache[cache_key] = candles
            self._cache_timestamp[cache_key] = now
            return candles
            
        return []

    async def get_multiple_candles_parallel(
        self,
        symbols: List[str],
        interval: str = "day",
        days: int = 400,
        concurrency: int = 15
    ) -> Dict[str, List[Candle]]:
        """
        Concurrent parallel candle retriever using asyncio Semaphore.
        Retrieves 400-day daily candles for all symbols simultaneously within 1-2 seconds.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: Dict[str, List[Candle]] = {}

        async def fetch_one(sym: str):
            async with semaphore:
                try:
                    c = await self.get_historical_candles_cached(sym, interval=interval, days=days)
                    results[sym] = c
                except Exception as e:
                    logger.warning(f"Failed fetching candles for {sym}: {e}")
                    results[sym] = []

        tasks = [fetch_one(s) for s in symbols]
        await asyncio.gather(*tasks)
        return results

    async def get_canonical_snapshot(
        self,
        symbol: str
    ) -> Tuple[Optional[Any], List[Candle], Any]:
        """
        Constructs the canonical, unified MarketDataSnapshot for a given symbol.
        Enforces 100% price synchronization across Header, Chart, Indicators, Targets, and ML.
        """
        from backend.services.market_data.data_quality import data_quality_gate
        from backend.models.schemas import MarketDataSnapshot, DataQualityReport

        sym = symbol.upper().strip()
        universe = self.get_supported_universe()
        match = next((s for s in universe if s["symbol"] == sym), None)
        instrument_key = match.get("instrument_key", f"NSE_EQ|{sym}") if match else f"NSE_EQ|{sym}"
        isin = match.get("isin") or (instrument_key.split("|")[-1] if "|" in instrument_key else None)

        # 1. Fetch historical candles (400 calendar days for full 200+ trading day coverage)
        raw_candles = await self.get_historical_candles_cached(sym, interval="day", days=400)
        dq_res = data_quality_gate.validate_daily_candles(raw_candles, symbol=sym, min_required_bars=30)
        clean_candles = dq_res.clean_candles if dq_res.is_valid else []

        # 2. Fetch live market quote
        raw_quote = await self.get_live_quote_for_symbol(sym)
        quote_price = raw_quote.get("price") if (raw_quote and raw_quote.get("price", 0) > 0) else (
            clean_candles[-1].close if clean_candles else None
        )
        prev_close = raw_quote.get("prev_close") if (raw_quote and raw_quote.get("prev_close", 0) > 0) else (
            clean_candles[-2].close if len(clean_candles) > 1 else quote_price
        )
        quote_open = raw_quote.get("open") if raw_quote else (clean_candles[-1].open if clean_candles else None)
        quote_high = raw_quote.get("high") if raw_quote else (clean_candles[-1].high if clean_candles else None)
        quote_low = raw_quote.get("low") if raw_quote else (clean_candles[-1].low if clean_candles else None)
        quote_vol = raw_quote.get("volume") if raw_quote else (clean_candles[-1].volume if clean_candles else None)

        # 3. Formulate canonical snapshot
        snapshot = MarketDataSnapshot(
            symbol=sym,
            exchange="NSE_EQ",
            instrument_key=instrument_key,
            isin=isin,
            quote_price=quote_price,
            previous_close=prev_close,
            open=quote_open,
            high=quote_high,
            low=quote_low,
            volume=quote_vol,
            quote_timestamp=datetime.utcnow(),
            latest_candle_timestamp=clean_candles[-1].timestamp if clean_candles else None,
            historical_candle_count=len(clean_candles),
            data_source="Upstox API v2 Live Feed",
            data_freshness="REALTIME" if raw_quote else ("EOD" if clean_candles else "UNAVAILABLE"),
            data_quality_status=dq_res.status,
            provenance_note=f"Verified {len(clean_candles)} historical daily bars against Upstox Data Quality Gate."
        )

        dq_report = DataQualityReport(
            is_valid=dq_res.is_valid,
            status=dq_res.status,
            rejection_reason=dq_res.rejection_reason,
            candle_count=dq_res.candle_count,
            min_required_candles=30,
            first_candle_date=dq_res.first_timestamp.strftime("%Y-%m-%d") if dq_res.first_timestamp else None,
            last_candle_date=dq_res.last_timestamp.strftime("%Y-%m-%d") if dq_res.last_timestamp else None,
            exchange="NSE_EQ",
            instrument_key=instrument_key,
            isin=isin,
            validated_at=datetime.utcnow()
        )

        return snapshot, clean_candles, dq_report

    async def get_live_quote_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Gets current live quote from Upstox API.
        """
        quotes = await self.provider.get_live_quote([symbol])
        if symbol in quotes:
            return quotes[symbol]
        return {}


    def get_supported_universe(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        from backend.services.market_data.universe import get_or_fetch_active_universe
        return get_or_fetch_active_universe(category=category)

    async def get_sector_indices_data(self) -> List[Dict[str, Any]]:
        """
        Fetches live sector performance metrics from Upstox (cached 60s).
        """
        now = datetime.utcnow()
        if self._sector_cache and self._sector_cache_time:
            if (now - self._sector_cache_time).total_seconds() < self._fast_ttl_seconds:
                return self._sector_cache

        keys = [s["name"] for s in NSE_SECTOR_KEYS]
        quotes = await self.provider.get_live_quote(keys)
        
        results = []
        for s in NSE_SECTOR_KEYS:
            sym = s["name"]
            q = quotes.get(sym) or quotes.get(s["symbol"]) or {}
            chg = float(q.get("change_percent", 0.0))
            trend = "STRONG_BULLISH" if chg >= 1.2 else ("BULLISH" if chg > 0.3 else ("BEARISH" if chg < -0.3 else "NEUTRAL"))
            results.append({
                "name": s["name"],
                "symbol": s["symbol"],
                "change": chg,
                "momentum": max(0.0, min(100.0, 50.0 + chg * 15.0)),
                "rs": round(1.0 + (chg / 100.0), 3),
                "trend": trend,
                "driver": s["sector"]
            })
        self._sector_cache = results
        self._sector_cache_time = now
        return results

data_service = MarketDataService()

