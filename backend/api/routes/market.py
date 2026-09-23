from fastapi import APIRouter
from backend.models.schemas import MarketStatusResponse
from backend.services.quant.market_engine import market_engine

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])

@router.get("/status", response_model=MarketStatusResponse)
async def get_market_status():
    """
    Returns high-level market status, NIFTY/Bank NIFTY/VIX quotes, breadth, and sector leaders.
    """
    return await market_engine.evaluate_market_regime()
