import logging
import urllib.parse
import asyncio
import time
import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
import httpx

from backend.config import settings
from backend.models.schemas import Candle
from backend.services.market_data.provider import MarketDataProvider
from backend.services.market_data.normalizer import DataNormalizer
from backend.services.market_data.universe import NSE_EQUITY_UNIVERSE

logger = logging.getLogger("upstox_provider")

# Map standard NSE symbol to Upstox Instrument Key
SYMBOL_TO_UPSTOX_KEY: Dict[str, str] = {
    u["symbol"]: u["instrument_key"] for u in NSE_EQUITY_UNIVERSE
}

# Add Index Mappings
SYMBOL_TO_UPSTOX_KEY.update({
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "NIFTY BANK": "NSE_INDEX|Nifty Bank",
    "INDIA VIX": "NSE_INDEX|India VIX",
    "INDIAVIX": "NSE_INDEX|India VIX",
    "VIX": "NSE_INDEX|India VIX",
    "NIFTY IT": "NSE_INDEX|Nifty IT",
    "NIFTY AUTO": "NSE_INDEX|Nifty Auto",
    "NIFTY PHARMA": "NSE_INDEX|Nifty Pharma",
    "NIFTY FMCG": "NSE_INDEX|Nifty FMCG",
    "NIFTY METAL": "NSE_INDEX|Nifty Metal",
    "NIFTY ENERGY": "NSE_INDEX|Nifty Energy",
    "NIFTY INFRA": "NSE_INDEX|Nifty Infra",
    "NIFTY REALTY": "NSE_INDEX|Nifty Realty",
    "NIFTY FIN SERVICE": "NSE_INDEX|Nifty Fin Service",
})


class AsyncRateLimiter:
    """
    Token-bucket asynchronous rate limiter.
    Ensures outbound requests stay safely under Upstox API limits (default 8 req/sec).
    """
    def __init__(self, max_rate: float = 8.0, time_period: float = 1.0):
        self.max_rate = max_rate
        self.time_period = time_period
        self._tokens = max_rate
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last_update
                self._last_update = now
                self._tokens = min(self.max_rate, self._tokens + elapsed * (self.max_rate / self.time_period))
                
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                
                needed = (1.0 - self._tokens) * (self.time_period / self.max_rate)
                await asyncio.sleep(max(0.02, needed))


class UpstoxProvider(MarketDataProvider):
    """
    Real Market Data Provider communicating directly with Upstox API V2.
    Translates standard NSE equity symbols to Upstox ISIN instrument keys.
    Features:
    - Asynchronous rate limiting to eliminate 429 Too Many Requests.
    - Automatic exponential backoff + jitter for transient failures.
    - Safe batch chunking (max 25 symbols) to prevent 400 Bad Request.
    - Sub-50ms connection pooling with persistent HTTP keep-alive.
    """
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or settings.UPSTOX_ACCESS_TOKEN
        self.base_url = settings.UPSTOX_BASE_URL.rstrip("/")
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Api-Version": "2.0"
        }
        self.timeout = httpx.Timeout(12.0, connect=4.0)
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = AsyncRateLimiter(max_rate=8.0, time_period=1.0)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(max_connections=50, max_keepalive_connections=30, keepalive_expiry=60.0)
            self._client = httpx.AsyncClient(timeout=self.timeout, limits=limits)
        return self._client

    async def _execute_with_retry(self, request_fn, description: str = "API request", max_retries: int = 3):
        """
        Executes HTTP call with rate limiting and exponential backoff on 429 / 5xx / timeouts.
        """
        for attempt in range(1, max_retries + 1):
            await self._rate_limiter.acquire()
            try:
                resp = await request_fn()
                if resp.status_code == 429:
                    wait_time = 0.6 * (2 ** (attempt - 1)) + random.uniform(0.1, 0.3)
                    logger.warning(f"Upstox 429 Too Many Requests on {description}. Backing off for {wait_time:.2f}s (attempt {attempt}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                    continue
                elif resp.status_code in [500, 502, 503, 504]:
                    wait_time = 0.5 * attempt + random.uniform(0.1, 0.2)
                    logger.warning(f"Upstox {resp.status_code} on {description}. Retrying in {wait_time:.2f}s (attempt {attempt}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                    continue
                return resp
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
                wait_time = 0.5 * attempt
                logger.warning(f"Network transient issue on {description}: {e}. Retrying in {wait_time:.2f}s (attempt {attempt}/{max_retries})...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error executing {description}: {e}")
                break
        return None

    def _format_instrument_key(self, symbol: str, exchange: str = "NSE_EQ") -> str:
        """
        Translates symbol (e.g. TCS, RELIANCE, MAZDOCK, COCHINSHIP, NIFTY 50) to official Upstox Instrument Key.
        Uses in-memory cache, DBInstrumentMaster, and ranked universe dynamically.
        """
        if not symbol:
            return ""
            
        sym_upper = symbol.upper().strip()
        if sym_upper in SYMBOL_TO_UPSTOX_KEY:
            return SYMBOL_TO_UPSTOX_KEY[sym_upper]

        # 1. Dynamic check in ranked universe
        try:
            from backend.services.market_data.universe import NSE_RANKED_UNIVERSE
            match = next((u for u in NSE_RANKED_UNIVERSE if u["symbol"].upper() == sym_upper), None)
            if match and "instrument_key" in match:
                SYMBOL_TO_UPSTOX_KEY[sym_upper] = match["instrument_key"]
                return match["instrument_key"]
        except Exception:
            pass

        # 2. Dynamic check in SQLite DBInstrumentMaster (case-insensitive)
        try:
            from backend.models.database import SessionLocal, DBInstrumentMaster
            db = SessionLocal()
            try:
                db_record = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.symbol.ilike(sym_upper)).first()
                if db_record and db_record.instrument_key:
                    SYMBOL_TO_UPSTOX_KEY[sym_upper] = db_record.instrument_key
                    return db_record.instrument_key
            finally:
                db.close()
        except Exception:
            pass

        if "|" in symbol:
            return symbol
            
        return f"{exchange}|{sym_upper}"

    async def get_instruments(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        """
        Fetches official instrument catalog from Upstox (e.g. exchange='NSE').
        Decompresses json.gz and returns instrument records.
        """
        url = f"https://assets.upstox.com/market-quote/instruments/exchange/{exchange}.json.gz"
        try:
            client = self._get_client()
            resp = await client.get(url)
            if resp.status_code == 200:
                import gzip
                import json
                try:
                    content = gzip.decompress(resp.content).decode("utf-8")
                    return json.loads(content)
                except Exception:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Could not download instrument catalog from Upstox: {e}")
        return []

    async def sync_exchange_catalog(self) -> int:
        """
        Downloads the full NSE instrument master from Upstox and synchronizes DBInstrumentMaster.
        Registers all NSE cash equities (EQ) into SYMBOL_TO_UPSTOX_KEY cache.
        """
        logger.info("Downloading latest NSE equity catalog from Upstox CDN...")
        instruments = await self.get_instruments(exchange="NSE")
        if not instruments:
            logger.warning("Empty instrument catalog received.")
            return 0
            
        eq_instruments = [i for i in instruments if i.get("instrument_type") == "EQ" and i.get("segment") == "NSE_EQ"]
        logger.info(f"Parsed {len(eq_instruments)} NSE cash equity instruments.")
        
        from backend.models.database import SessionLocal, DBInstrumentMaster
        db = SessionLocal()
        synced_count = 0
        try:
            for item in eq_instruments:
                sym = item.get("trading_symbol", "").upper().strip()
                key = item.get("instrument_key", "").strip()
                name = item.get("name", "").strip()
                if sym and key:
                    SYMBOL_TO_UPSTOX_KEY[sym] = key
                    existing = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.symbol == sym).first()
                    if not existing:
                        db.add(DBInstrumentMaster(
                            symbol=sym,
                            name=name or sym,
                            sector="Equity",
                            instrument_key=key,
                            market_cap_category="EQUITY",
                            classification_source="Upstox Master Catalog",
                            is_active=True
                        ))
                        synced_count += 1
                    else:
                        if existing.instrument_key != key:
                            existing.instrument_key = key
                            if name:
                                existing.name = name
                            synced_count += 1
            db.commit()
            logger.info(f"Successfully synced {synced_count} new/updated instruments to DBInstrumentMaster.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing instrument catalog to database: {e}")
        finally:
            db.close()
            
        return len(eq_instruments)

    async def get_live_quote(self, instrument_keys: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch quotes for one or multiple instrument keys from Upstox /v2/market-quote/quotes.
        Automatically chunks requests into safe batches of max 25 keys to eliminate 400 Bad Request.
        """
        if not instrument_keys:
            return {}
            
        # Sanitize keys
        formatted_keys = []
        for k in instrument_keys:
            if not k:
                continue
            fmt = self._format_instrument_key(k)
            if fmt and fmt not in formatted_keys:
                formatted_keys.append(fmt)

        if not formatted_keys:
            return {}

        results = {}
        client = self._get_client()
        BATCH_SIZE = 25
        batches = [formatted_keys[i:i + BATCH_SIZE] for i in range(0, len(formatted_keys), BATCH_SIZE)]

        for batch in batches:
            keys_param = ",".join(batch)
            url = f"{self.base_url}/v2/market-quote/quotes"
            params = {"instrument_key": keys_param}
            
            async def do_req():
                return await client.get(url, headers=self.headers, params=params)

            resp = await self._execute_with_retry(do_req, description=f"live quotes for {len(batch)} symbols")
            
            if resp and resp.status_code == 200:
                try:
                    payload = resp.json()
                    data = payload.get("data", {})
                    for key, raw_quote in data.items():
                        norm_key = key.replace(":", "|")
                        sym = key.split(":")[-1] if ":" in key else key
                        found_sym = sym
                        for s, ik in SYMBOL_TO_UPSTOX_KEY.items():
                            if ik == norm_key or ik == key or ik.endswith(sym) or sym.upper() == s.upper():
                                found_sym = s
                                break
                        normalized = DataNormalizer.normalize_upstox_quote(found_sym, raw_quote)
                        results[found_sym] = normalized
                        results[sym] = normalized
                        results[norm_key] = normalized
                        results[key] = normalized
                except Exception as e:
                    logger.warning(f"Error parsing live quote response: {e}")
            elif resp and resp.status_code == 400:
                logger.warning(f"Upstox 400 Bad Request on batch quote ({keys_param[:60]}...). Falling back to single queries...")
                # Query keys individually to bypass single-symbol corruption
                for single_key in batch:
                    try:
                        await self._rate_limiter.acquire()
                        s_resp = await client.get(url, headers=self.headers, params={"instrument_key": single_key})
                        if s_resp.status_code == 200:
                            s_data = s_resp.json().get("data", {})
                            for k_res, raw_q in s_data.items():
                                norm_k = k_res.replace(":", "|")
                                s_sym = k_res.split(":")[-1] if ":" in k_res else k_res
                                found_s = s_sym
                                for s, ik in SYMBOL_TO_UPSTOX_KEY.items():
                                    if ik == norm_k or ik == k_res or ik.endswith(s_sym) or s_sym.upper() == s.upper():
                                        found_s = s
                                        break
                                norm_res = DataNormalizer.normalize_upstox_quote(found_s, raw_q)
                                results[found_s] = norm_res
                                results[s_sym] = norm_res
                                results[norm_k] = norm_res
                    except Exception:
                        pass
                        
        return results

    async def get_historical_candles(
        self,
        instrument_key: str,
        interval: str = "day",
        to_date: Optional[str] = None,
        from_date: Optional[str] = None
    ) -> List[Candle]:
        """
        Fetches historical candles from Upstox API v2.
        Endpoint: /v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
        Guarded against invalid date order, special char escaping, and 429/400 errors.
        """
        if not instrument_key:
            return []
            
        formatted_raw_key = self._format_instrument_key(instrument_key)
        if not formatted_raw_key:
            return []
        encoded_key = urllib.parse.quote(formatted_raw_key, safe='')
        
        today_dt = date.today()
        if not to_date:
            to_date = today_dt.strftime("%Y-%m-%d")
        if not from_date:
            from_date = (today_dt - timedelta(days=200)).strftime("%Y-%m-%d")
            
        # Ensure chronological sanity
        try:
            f_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            t_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            if f_dt >= t_dt:
                from_date = (t_dt - timedelta(days=180)).strftime("%Y-%m-%d")
        except Exception:
            pass
            
        upstox_interval = interval
        if interval in ["1d", "D", "day", "daily"]:
            upstox_interval = "day"
        elif interval in ["1w", "W", "week", "weekly"]:
            upstox_interval = "week"
        elif interval in ["1m", "M", "month", "monthly"]:
            upstox_interval = "month"
        elif interval in ["1min", "1minute", "1"]:
            upstox_interval = "1minute"
        elif interval in ["30min", "30minute", "30"]:
            upstox_interval = "30minute"

        url = f"{self.base_url}/v2/historical-candle/{encoded_key}/{upstox_interval}/{to_date}/{from_date}"
        client = self._get_client()

        async def do_req():
            return await client.get(url, headers=self.headers)

        resp = await self._execute_with_retry(do_req, description=f"candles for {instrument_key}")

        if resp and resp.status_code == 200:
            try:
                payload = resp.json()
                raw_candles = payload.get("data", {}).get("candles", [])
                return DataNormalizer.normalize_upstox_candles(raw_candles)
            except Exception as e:
                logger.warning(f"Error parsing candles for {instrument_key}: {e}")
                return []
        elif resp and resp.status_code in [400, 404]:
            # Fallback to single to_date endpoint: /v2/historical-candle/{key}/{interval}/{to_date}
            alt_url = f"{self.base_url}/v2/historical-candle/{encoded_key}/{upstox_interval}/{to_date}"
            try:
                await self._rate_limiter.acquire()
                alt_resp = await client.get(alt_url, headers=self.headers)
                if alt_resp.status_code == 200:
                    raw_candles = alt_resp.json().get("data", {}).get("candles", [])
                    return DataNormalizer.normalize_upstox_candles(raw_candles)
            except Exception:
                pass
                
        return []

    async def get_intraday_candles(
        self,
        instrument_key: str,
        interval: str = "1minute"
    ) -> List[Candle]:
        """
        Fetches intraday candles for current trading day.
        Endpoint: /v2/historical-candle/intraday/{instrument_key}/{interval}
        """
        if not instrument_key:
            return []
            
        formatted_raw_key = self._format_instrument_key(instrument_key)
        if not formatted_raw_key:
            return []
        encoded_key = urllib.parse.quote(formatted_raw_key, safe='')
        url = f"{self.base_url}/v2/historical-candle/intraday/{encoded_key}/{interval}"
        client = self._get_client()
        
        async def do_req():
            return await client.get(url, headers=self.headers)
            
        resp = await self._execute_with_retry(do_req, description=f"intraday candles for {instrument_key}")
        if resp and resp.status_code == 200:
            try:
                payload = resp.json()
                raw_candles = payload.get("data", {}).get("candles", [])
                return DataNormalizer.normalize_upstox_candles(raw_candles)
            except Exception as e:
                logger.warning(f"Error parsing intraday candles for {instrument_key}: {e}")
                
        return []

    async def get_market_depth(self, instrument_key: str) -> Dict[str, Any]:
        quotes = await self.get_live_quote([instrument_key])
        sym = instrument_key.split("|")[-1] if "|" in instrument_key else instrument_key
        quote = quotes.get(sym, {})
        return quote.get("depth", {})
