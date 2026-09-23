from fastapi import APIRouter
from typing import Dict, Any

from backend.services.ml.backtest import model_auditor
from backend.services.scheduler.automation import scheduler_service

router = APIRouter(prefix="/api/audit", tags=["Model Evaluation & Audit"])

@router.get("/performance")
async def get_performance_audit():
    """
    Returns walk-forward validation statistics, hit rates, Brier scores, and calibration metrics.
    """
    return model_auditor.get_performance_summary()

@router.get("/alerts")
async def get_recent_alerts():
    """
    Returns automated real-time alert event history.
    """
    return scheduler_service.get_scheduler_status()["alerts"]
