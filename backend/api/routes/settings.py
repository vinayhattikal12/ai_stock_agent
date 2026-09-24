from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from backend.config import settings
from backend.services.scheduler.automation import scheduler_service

router = APIRouter(prefix="/api/settings", tags=["Settings & Status"])

class TokenUpdate(BaseModel):
    token: str

@router.get("/status")
async def get_system_status():
    """
    Returns API connectivity, Upstox integration status, and scheduler heartbeat.
    """
    has_token = bool(settings.UPSTOX_ACCESS_TOKEN and len(settings.UPSTOX_ACCESS_TOKEN) > 20)
    scheduler_info = scheduler_service.get_scheduler_status()
    
    return {
        "status": "HEALTHY",
        "upstox_connected": has_token,
        "token_masked": f"{settings.UPSTOX_ACCESS_TOKEN[:6]}...{settings.UPSTOX_ACCESS_TOKEN[-6:]}" if has_token else "NOT_CONFIGURED",
        "environment": settings.ENVIRONMENT,
        "database": "SQLite / PostgreSQL Integrated",
        "scheduler": scheduler_info
    }

@router.post("/upstox-token")
async def update_token(payload: TokenUpdate):
    """
    Allows updating Upstox Access Token dynamically without restart.
    """
    settings.UPSTOX_ACCESS_TOKEN = payload.token.strip()
    return {"status": "success", "message": "Upstox Access Token updated successfully."}

@router.post("/universe/sync")
async def sync_amfi_universe():
    """
    Triggers programmatic synchronization and AMFI market-cap classification of the NSE universe.
    """
    from backend.services.market_data.universe_manager import AMFIUniverseManager
    result = await AMFIUniverseManager.sync_amfi_universe()
    return result

@router.get("/universe/status")
async def get_universe_status():
    """
    Returns current active AMFI market-cap universe distribution and refresh metadata.
    """
    from backend.services.market_data.universe_manager import AMFIUniverseManager
    return AMFIUniverseManager.get_active_universe_summary()

