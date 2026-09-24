from fastapi import APIRouter
from typing import Dict, Any, Optional

from backend.services.ml.backtest import model_auditor
from backend.services.ml.historical_engine import historical_backtest_engine
from backend.services.ml.trainer import ml_trainer
from backend.services.scheduler.automation import scheduler_service

router = APIRouter(prefix="/api/audit", tags=["Model Evaluation & Audit"])

@router.get("/performance")
async def get_performance_audit():
    """
    Returns walk-forward validation statistics, hit rates, Brier scores, and calibration metrics.
    """
    return model_auditor.get_performance_summary()

@router.post("/backtest/run")
async def run_historical_backtest_endpoint():
    """
    Executes a multi-year historical backtest replay with Triple-Barrier labeling
    and Purged & Embargoed Walk-Forward Cross-Validation across liquid NSE equities.
    """
    samples = await historical_backtest_engine.build_labeled_dataset(lookback_days=1000)
    result = historical_backtest_engine.run_purged_walk_forward_validation(samples)
    return result

@router.post("/model/train")
async def train_ml_model_endpoint():
    """
    Fits and persists calibrated Gradient Boosting models on the historical Triple-Barrier dataset.
    """
    return await ml_trainer.train_and_persist_models(lookback_days=1000)

@router.get("/alerts")
async def get_recent_alerts():
    """
    Returns automated real-time alert event history.
    """
    return scheduler_service.get_scheduler_status()["alerts"]
