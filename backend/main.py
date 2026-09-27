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
    
    # Background recurring live corporate announcements sync (every 10 minutes)
    from backend.services.news.event_tracker import news_engine
    async def periodic_news_sync_runner():
        while True:
            try:
                synced = await news_engine.fetch_and_sync_live_announcements()
                if synced > 0:
                    logger.info(f"Corporate News Engine: Synced {synced} new corporate announcements.")
                await asyncio.sleep(600) # Check every 10 minutes
            except Exception as e:
                logger.warning(f"Error in background news announcement sync: {e}")
                await asyncio.sleep(600)

    asyncio.create_task(periodic_news_sync_runner())

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

    # Background automated ML model fitting and walk-forward backtest compilation if missing
    from backend.services.ml.trainer import ml_trainer, MODEL_BUNDLE_PATH
    from backend.services.ml.historical_engine import historical_backtest_engine
    from backend.models.database import DBHistoricalBacktest

    async def init_ml_model_and_backtest():
        try:
            # 1. Fit ML model if bundle missing
            if not os.path.exists(MODEL_BUNDLE_PATH):
                logger.info("Fitted ML model bundle missing. Training calibrated Gradient Boosting model in background...")
                train_res = await ml_trainer.train_and_persist_models(lookback_days=1000)
                logger.info(f"ML Model Training completed with status: {train_res.get('status')}")

            # 2. Run historical walk-forward backtest if table empty
            db = SessionLocal()
            try:
                has_bt = db.query(DBHistoricalBacktest).first() is not None
            finally:
                db.close()

            if not has_bt:
                logger.info("Compiling initial historical walk-forward backtest dataset...")
                samples = await historical_backtest_engine.build_labeled_dataset(lookback_days=1000)
                if samples:
                    bt_res = historical_backtest_engine.run_purged_walk_forward_validation(samples)
                    logger.info(f"Historical Walk-Forward Backtest completed: {bt_res.get('status')}")
        except Exception as ml_init_err:
            logger.warning(f"Note: ML background initialization deferred: {ml_init_err}")

    asyncio.create_task(init_ml_model_and_backtest())

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
