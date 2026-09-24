from fastapi import APIRouter
from backend.models.schemas import MarketStatusResponse, TodaysMoversResponse
from backend.services.quant.market_engine import market_engine
from backend.services.quant.movers_engine import todays_movers_engine

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])

@router.get("/status", response_model=MarketStatusResponse)
async def get_market_status():
    """
    Returns high-level market status, NIFTY/Bank NIFTY/VIX quotes, breadth, and sector leaders.
    """
    return await market_engine.evaluate_market_regime()

@router.get("/movers", response_model=TodaysMoversResponse)
async def get_todays_movers():
    """
    Returns real-time intraday movers (Top Gainers, Losers, Unusual Volume, Opening Gaps)
    with 'Why It Moved' catalyst attachment and Sector-vs-Stock decoupling.
    """
    return await todays_movers_engine.get_todays_movers()
