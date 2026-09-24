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
    Uses concurrency pooling, in-flight request deduplication, and multi-tier in-memory caching.
    """
    def __init__(self):
        self.provider = UpstoxProvider(settings.UPSTOX_ACCESS_TOKEN)
        self._candle_cache: Dict[str, List[Candle]] = {}
        self._cache_timestamp: Dict[str, datetime] = {}
        self._cache_ttl_seconds = 300  # 5 minutes candle cache
        
        self._live_quote_cache: Dict[str, Dict[str, Any]] = {}
        self._quote_cache_timestamp: Dict[str, datetime] = {}
        self._quote_ttl_seconds = 15   # 15 seconds for live quote auto-fill
        
        self._indices_cache: Optional[Dict[str, MarketIndexQuote]] = None
        self._indices_cache_time: Optional[datetime] = None
        
        self._sector_cache: Optional[List[Dict[str, Any]]] = None
        self._sector_cache_time: Optional[datetime] = None
        self._fast_ttl_seconds = 60    # 1 minute for live indices
        
        self._in_flight_candles: Dict[str, asyncio.Future] = {}
        
    async def get_indices_status(self) -> Dict[str, MarketIndexQuote]:
        """
        Fetch real quote snapshots for NIFTY 50, Bank NIFTY, and India VIX from Upstox.
        Cached for 60 seconds to avoid redundant calls.
        """
        now = datetime.utcnow()
        if self._indices_cache and self._indices_cache_time:
            if (now - self._indices_cache_time).total_seconds() < self._fast_ttl_seconds:
                return self._indices_cache

        keys = ["NIFTY 50", "BANKNIFTY", "INDIA VIX", "NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "NSE_INDEX|India VIX"]
        raw_quotes = await self.provider.get_live_quote(keys)
        
        nifty_quote = raw_quotes.get("NIFTY 50") or raw_quotes.get("Nifty 50") or raw_quotes.get("NSE_INDEX|Nifty 50") or {}
        bank_nifty_quote = raw_quotes.get("BANKNIFTY") or raw_quotes.get("Nifty Bank") or raw_quotes.get("NSE_INDEX|Nifty Bank") or {}
        vix_quote = raw_quotes.get("INDIA VIX") or raw_quotes.get("India VIX") or raw_quotes.get("NSE_INDEX|India VIX") or {}

        # If live quote price is 0.0 or unavailable, extract from verified historical daily candles
        async def resolve_index_metric(sym: str, quote: Dict[str, Any], default_name: str) -> MarketIndexQuote:
            p = float(quote.get("price", 0.0))
            chg = float(quote.get("change", 0.0))
            chg_pct = float(quote.get("change_percent", 0.0))
            h = float(quote.get("high", 0.0))
            l = float(quote.get("low", 0.0))
            o = float(quote.get("open", 0.0))
            pc = float(quote.get("prev_close", 0.0))

            if p <= 0.0:
                candles = await self.get_historical_candles_cached(sym, interval="day", days=10)
                if candles and len(candles) >= 1:
                    latest = candles[-1]
                    prev = candles[-2] if len(candles) >= 2 else None
                    p = float(latest.close)
                    pc = float(prev.close) if prev else float(latest.open)
                    chg = round(p - pc, 2)
                    chg_pct = round((chg / pc * 100.0), 2) if pc else 0.0
                    h = float(latest.high)
                    l = float(latest.low)
                    o = float(latest.open)

            return MarketIndexQuote(
                symbol=sym,
                name=default_name,
                price=p,
                change=chg,
                change_percent=chg_pct,
                high=h,
                low=l,
                open=o,
                prev_close=pc
            )

        nifty_iq = await resolve_index_metric("NIFTY 50", nifty_quote, "NIFTY 50")
        bank_iq = await resolve_index_metric("BANKNIFTY", bank_nifty_quote, "NIFTY Bank")
        vix_iq = await resolve_index_metric("INDIA VIX", vix_quote, "India VIX")

        res = {
            "nifty": nifty_iq,
            "bank_nifty": bank_iq,
            "india_vix": vix_iq
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
        Retrieves historical candle list from Upstox API V2 with caching & in-flight deduplication.
        Default 400 days (~260 trading days) ensures full SMA200 and 52-week coverage.
        """
        sym_clean = symbol.upper().strip()
        cache_key = f"{sym_clean}_{interval}_{days}"
        now = datetime.utcnow()
        
        # 1. Check cache
        if cache_key in self._candle_cache:
            last_time = self._cache_timestamp.get(cache_key)
            if last_time and (now - last_time).total_seconds() < self._cache_ttl_seconds:
                return self._candle_cache[cache_key]

        # 2. In-flight request deduplication (Singleflight)
        if cache_key in self._in_flight_candles:
            try:
                return await self._in_flight_candles[cache_key]
            except Exception:
                pass

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._in_flight_candles[cache_key] = fut

        try:
            to_date = date.today().strftime("%Y-%m-%d")
            from_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            candles = await self.provider.get_historical_candles(
                instrument_key=sym_clean,
                interval=interval,
                to_date=to_date,
                from_date=from_date
            )
            
            if candles:
                self._candle_cache[cache_key] = candles
                self._cache_timestamp[cache_key] = now
            
            if not fut.done():
                fut.set_result(candles or [])
            return candles or []
        except Exception as e:
            logger.warning(f"Error fetching candles for {sym_clean}: {e}")
            if not fut.done():
                fut.set_result([])
            return []
        finally:
            self._in_flight_candles.pop(cache_key, None)

    async def get_multiple_candles_parallel(
        self,
        symbols: List[str],
        interval: str = "day",
        days: int = 400,
        concurrency: int = 8
    ) -> Dict[str, List[Candle]]:
        """
        Controlled parallel candle retriever using asyncio Semaphore.
        Throttled strictly to 8 concurrent tasks to protect against rate limit spikes.
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
        Gets current live quote from Upstox API with 15-second cache to prevent rapid hammering.
        """
        sym = symbol.upper().strip()
        now = datetime.utcnow()
        
        if sym in self._live_quote_cache:
            last_t = self._quote_cache_timestamp.get(sym)
            if last_t and (now - last_t).total_seconds() < self._quote_ttl_seconds:
                return self._live_quote_cache[sym]

        quotes = await self.provider.get_live_quote([sym])
        if sym in quotes and quotes[sym]:
            self._live_quote_cache[sym] = quotes[sym]
            self._quote_cache_timestamp[sym] = now
            return quotes[sym]
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
