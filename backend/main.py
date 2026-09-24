import sys
import os
import logging

# Ensure project root is always in sys.path regardless of execution context (Render/Local/Docker)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_CURRENT_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.models.database import init_db
from backend.api.routes import market, scanner, portfolio, stocks, audit, settings as settings_router

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("equity_intelligence")

app = FastAPI(
    title="AI-Powered Indian Equity Intelligence Platform",
    description="Deterministic Decision-Support & Quantitative Swing Trading Intelligence System for NSE/BSE Equities",
    version="1.0.0"
)

# Configure CORS for Localhost & Vercel Deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(market.router)
app.include_router(scanner.router)
app.include_router(portfolio.router)
app.include_router(stocks.router)
app.include_router(audit.router)
app.include_router(settings_router.router)

from fastapi import Request
from fastapi.responses import JSONResponse
import httpx

# Global Exception Handlers for Resilient Operation
@app.exception_handler(httpx.HTTPStatusError)
async def httpx_status_error_handler(request: Request, exc: httpx.HTTPStatusError):
    status_code = exc.response.status_code
    logger.warning(f"Upstream Market Data Provider HTTP error {status_code} on {request.url}: {exc}")
    if status_code == 429:
        return JSONResponse(
            status_code=429,
            content={"detail": "Upstream market data rate limit reached. The system is automatically retrying with backoff."}
        )
    elif status_code == 400:
        return JSONResponse(
            status_code=400,
            content={"detail": "Bad request sent to upstream market data provider. Invalid instrument key or parameters."}
        )
    return JSONResponse(
        status_code=502,
        content={"detail": f"Upstream market data error ({status_code})."}
    )

@app.exception_handler(httpx.RequestError)
async def httpx_request_error_handler(request: Request, exc: httpx.RequestError):
    logger.warning(f"Network transport error contacting market data provider on {request.url}: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Market data service is temporarily unreachable. Please retry momentarily."}
    )

@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database schemas...")
    init_db()
    from backend.models.database import SessionLocal
    from backend.services.market_data.universe import seed_instrument_master_if_empty
    from backend.services.market_data.data_service import data_service
    
    db = SessionLocal()
    try:
        seed_instrument_master_if_empty(db)
    finally:
        db.close()
        
    # Background non-blocking sync of full NSE instrument master and AMFI universe
    import asyncio
    asyncio.create_task(data_service.provider.sync_exchange_catalog())
    
    from backend.services.market_data.universe_manager import AMFIUniverseManager
    asyncio.create_task(AMFIUniverseManager.sync_amfi_universe())
    
    # Background live corporate announcements sync
    from backend.services.news.event_tracker import news_engine
    asyncio.create_task(news_engine.fetch_and_sync_live_announcements())
    
    # Background periodic signal audit evaluator
    from backend.services.scheduler.automation import scheduler_service
    async def periodic_audit_runner():
        while True:
            try:
                await asyncio.sleep(300) # Check every 5 minutes
                resolved = await scheduler_service.audit_active_signals()
                if resolved > 0:
                    logger.info(f"Signal Audit Evaluator resolved {resolved} active swing signals.")
            except Exception as e:
                logger.warning(f"Error in background signal audit evaluator: {e}")
                await asyncio.sleep(600)
    
    asyncio.create_task(periodic_audit_runner())
    logger.info("AI Equity Intelligence Platform backend initialized successfully.")

@app.get("/health")
def health_check():
    return {
        "status": "UP",
        "service": "AI Equity Intelligence Backend",
        "upstox_configured": bool(settings.UPSTOX_ACCESS_TOKEN)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
