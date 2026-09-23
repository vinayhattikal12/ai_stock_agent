import logging
import urllib.parse
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

class UpstoxProvider(MarketDataProvider):
    """
    Real Market Data Provider communicating directly with Upstox API V2.
    Translates standard NSE equity symbols to Upstox ISIN instrument keys.
    Uses persistent HTTP connection pooling for sub-50ms query throughput.
    """
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or settings.UPSTOX_ACCESS_TOKEN
        self.base_url = settings.UPSTOX_BASE_URL.rstrip("/")
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Api-Version": "2.0"
        }
        self.timeout = httpx.Timeout(10.0, connect=3.0)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(max_connections=100, max_keepalive_connections=50, keepalive_expiry=30.0)
            self._client = httpx.AsyncClient(timeout=self.timeout, limits=limits)
        return self._client

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
        """
        if not instrument_keys:
            return {}
            
        formatted_keys = [self._format_instrument_key(k) for k in instrument_keys]
        keys_param = ",".join(formatted_keys)
        url = f"{self.base_url}/v2/market-quote/quotes"
        params = {"instrument_key": keys_param}
        
        try:
            client = self._get_client()
            resp = await client.get(url, headers=self.headers, params=params)
            if resp.status_code == 200:
                payload = resp.json()
                data = payload.get("data", {})
                results = {}
                for key, raw_quote in data.items():
                    # Map Upstox key back to human symbol
                    sym = key.split(":")[-1] if ":" in key else key
                    
                    # Reverse lookup symbol if it is an ISIN
                    found_sym = sym
                    for s, ik in SYMBOL_TO_UPSTOX_KEY.items():
                        if ik.endswith(sym) or sym in ik:
                            found_sym = s
                            break
                            
                    results[found_sym] = DataNormalizer.normalize_upstox_quote(found_sym, raw_quote)
                return results
            else:
                logger.warning(f"Upstox quote API error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error fetching live quote from Upstox: {e}")
            
        return {}

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
        """
        formatted_raw_key = self._format_instrument_key(instrument_key)
        encoded_key = urllib.parse.quote(formatted_raw_key, safe='')
        
        # Default date range: past 180 days
        if not to_date:
            to_date = date.today().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (date.today() - timedelta(days=200)).strftime("%Y-%m-%d")
            
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
        
        try:
            client = self._get_client()
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                payload = resp.json()
                raw_candles = payload.get("data", {}).get("candles", [])
                return DataNormalizer.normalize_upstox_candles(raw_candles)
            else:
                logger.warning(f"Upstox candle API returned {resp.status_code} for {formatted_raw_key}: {resp.text}")
                # Try calling without from_date (Upstox supports /v2/historical-candle/{key}/{interval}/{to_date})
                alt_url = f"{self.base_url}/v2/historical-candle/{encoded_key}/{upstox_interval}/{to_date}"
                alt_resp = await client.get(alt_url, headers=self.headers)
                if alt_resp.status_code == 200:
                    raw_candles = alt_resp.json().get("data", {}).get("candles", [])
                    return DataNormalizer.normalize_upstox_candles(raw_candles)
        except Exception as e:
            logger.error(f"Exception fetching historical candles for {instrument_key}: {e}")
            
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
        formatted_raw_key = self._format_instrument_key(instrument_key)
        encoded_key = urllib.parse.quote(formatted_raw_key, safe='')
        url = f"{self.base_url}/v2/historical-candle/intraday/{encoded_key}/{interval}"
        
        try:
            client = self._get_client()
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                payload = resp.json()
                raw_candles = payload.get("data", {}).get("candles", [])
                return DataNormalizer.normalize_upstox_candles(raw_candles)
        except Exception as e:
            logger.error(f"Error fetching intraday candles for {instrument_key}: {e}")
            
        return []

    async def get_market_depth(self, instrument_key: str) -> Dict[str, Any]:
        quotes = await self.get_live_quote([instrument_key])
        sym = instrument_key.split("|")[-1] if "|" in instrument_key else instrument_key
        quote = quotes.get(sym, {})
        return quote.get("depth", {})
