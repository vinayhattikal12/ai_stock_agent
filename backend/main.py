import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

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
        
    # Background non-blocking sync of full NSE instrument master
    import asyncio
    asyncio.create_task(data_service.provider.sync_exchange_catalog())
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
