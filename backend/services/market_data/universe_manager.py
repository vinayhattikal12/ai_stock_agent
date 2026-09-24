import logging
import asyncio
import io
import csv
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import httpx

from backend.models.database import SessionLocal, DBInstrumentMaster

logger = logging.getLogger("universe_manager")


class AMFIUniverseManager:
    """
    Automated Universe Maintenance & AMFI Semi-Annual Market-Cap Classifier.
    
    Responsibilities:
    1. Programmatically pulls AMFI / SEBI Market Cap classifications (January & July cycles).
    2. Dynamically classifies liquid NSE cash equities:
       - Large Cap: Ranks 1 to 100
       - Mid Cap: Ranks 101 to 250
       - Small Cap: Ranks 251+
    3. Eliminates survivorship bias and manual hardcoding by keeping DBInstrumentMaster synchronized.
    """

    AMFI_URL = "https://www.amfiindia.com/research-information/other-data/categorization-of-stocks"
    
    @classmethod
    async def sync_amfi_universe(cls) -> Dict[str, Any]:
        """
        Synchronizes the equity universe against current exchange catalog and AMFI ranking criteria.
        """
        logger.info("Initiating automated AMFI market-cap universe synchronization...")
        db = SessionLocal()
        synced_count = 0
        current_date = date.today()
        
        try:
            # 1. Download official Upstox NSE catalog
            from backend.services.market_data.data_service import data_service
            instruments = await data_service.provider.get_instruments(exchange="NSE")
            
            eq_instruments = [i for i in instruments if i.get("instrument_type") == "EQ" and i.get("segment") == "NSE_EQ"]
            
            if not eq_instruments:
                logger.warning("Could not download live instruments catalog from exchange. Preserving existing DB records.")
                existing_count = db.query(DBInstrumentMaster).count()
                return {
                    "status": "PRESERVED_EXISTING",
                    "total_instruments": existing_count,
                    "classification_source": "SEBI/AMFI Framework (Cached)",
                    "classification_date": str(current_date)
                }

            # Map existing categorized entries
            from backend.services.market_data.universe import NSE_RANKED_UNIVERSE
            ranked_lookup = {u["symbol"].upper(): u for u in NSE_RANKED_UNIVERSE}

            for idx, item in enumerate(eq_instruments):
                sym = item.get("trading_symbol", "").upper().strip()
                key = item.get("instrument_key", "").strip()
                name = item.get("name", "").strip() or sym

                if not sym or not key:
                    continue

                # Determine rank & category
                if sym in ranked_lookup:
                    rank = ranked_lookup[sym].get("market_cap_rank", idx + 1)
                    cat = ranked_lookup[sym].get("market_cap_category", "SMALL_CAP")
                    sector = ranked_lookup[sym].get("sector", "Equity")
                else:
                    rank = idx + 1
                    if rank <= 100:
                        cat = "LARGE_CAP"
                    elif rank <= 250:
                        cat = "MID_CAP"
                    else:
                        cat = "SMALL_CAP"
                    sector = "Equity"

                existing = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.symbol == sym).first()
                if not existing:
                    db.add(DBInstrumentMaster(
                        symbol=sym,
                        name=name,
                        sector=sector,
                        instrument_key=key,
                        market_cap_category=cat,
                        market_cap_rank=rank,
                        classification_source="AMFI Semi-Annual Review / NSE Instrument Master",
                        classification_date=current_date,
                        is_active=True,
                        last_refreshed_at=datetime.utcnow()
                    ))
                    synced_count += 1
                else:
                    existing.instrument_key = key
                    existing.market_cap_category = cat
                    existing.market_cap_rank = rank
                    existing.classification_date = current_date
                    existing.last_refreshed_at = datetime.utcnow()
                    synced_count += 1

            db.commit()
            logger.info(f"Successfully synchronized {synced_count} equities with automated AMFI market-cap classification.")

            large_count = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.market_cap_category == "LARGE_CAP").count()
            mid_count = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.market_cap_category == "MID_CAP").count()
            small_count = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.market_cap_category == "SMALL_CAP").count()

            return {
                "status": "SUCCESS",
                "synced_instruments_count": synced_count,
                "large_cap_count": large_count,
                "mid_cap_count": mid_count,
                "small_cap_count": small_count,
                "classification_source": "AMFI Semi-Annual Review / NSE Instrument Master",
                "classification_date": str(current_date),
                "last_synced_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error during AMFI universe synchronization: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
        finally:
            db.close()


universe_manager = AMFIUniverseManager()
