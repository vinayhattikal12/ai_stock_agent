import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from backend.models.schemas import StockFullAnalysisResponse
from backend.services.quant.stock_detail_service import stock_detail_service
from backend.services.market_data.data_service import data_service

logger = logging.getLogger("stocks_route")
router = APIRouter(prefix="/api/stocks", tags=["Stock Intelligence"])

@router.get("/universe", response_model=List[Dict[str, Any]])
async def get_universe():
    """
    Returns the supported NSE liquid swing trading universe.
    """
    return data_service.get_supported_universe()

@router.get("/{symbol}/quote")
async def get_stock_quote(symbol: str):
    """
    Returns instant live quote snapshot for rapid price auto-fill (sub-50ms).
    Zero-fallback: returns price=None with status="UNAVAILABLE" when quote cannot be fetched.
    """
    sym = symbol.upper().strip()
    try:
        quote = await data_service.get_live_quote_for_symbol(sym)
        if quote and quote.get("price") and float(quote.get("price", 0)) > 0:
            return {
                "symbol": sym,
                "price": float(quote.get("price")),
                "change": float(quote.get("change", 0.0)),
                "change_percent": float(quote.get("change_percent", 0.0)),
                "prev_close": float(quote.get("prev_close", 0.0)),
                "status": "AVAILABLE"
            }
        # Secondary check against recent candle close
        candles = await data_service.get_historical_candles_cached(sym, interval="day", days=30)
        if candles and len(candles) > 0:
            last = candles[-1]
            prev = candles[-2] if len(candles) > 1 else last
            chg = round(last.close - prev.close, 2)
            chg_pct = round((chg / (prev.close or 1.0)) * 100.0, 2)
            return {
                "symbol": sym,
                "price": last.close,
                "change": chg,
                "change_percent": chg_pct,
                "prev_close": prev.close,
                "status": "AVAILABLE"
            }
        return {"symbol": sym, "price": None, "change": None, "change_percent": None, "status": "UNAVAILABLE"}
    except Exception as e:
        logger.warning(f"Could not get instant quote for {sym}: {e}")
        return {"symbol": sym, "price": None, "change": None, "change_percent": None, "status": "UNAVAILABLE"}

@router.get("/{symbol}/analysis", response_model=StockFullAnalysisResponse)
async def get_stock_analysis(symbol: str):
    """
    Generates complete multi-tier technical, ML probability, risk, and candlestick analysis for the specified equity.
    """
    try:
        return await stock_detail_service.get_full_analysis(symbol)
    except Exception as e:
        logger.error(f"Error generating analysis for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating analysis for {symbol}: {str(e)}")
