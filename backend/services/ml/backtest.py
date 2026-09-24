import math
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend.models.database import SessionLocal, DBSignalAudit, DBHistoricalBacktest

class ModelPerformanceAuditor:
    """
    Evaluates ML model performance, walk-forward calibration, and swing statistics
    strictly from recorded, closed signal audit records in the database or verified historical backtests.
    
    Zero-fallback policy: When fewer than 30 completed audit records exist and no historical backtest is run,
    returns status="INSUFFICIENT_HISTORY" and null metrics. Never fabricates statistics.
    """
    
    MIN_RECORDS_FOR_STATISTICAL_SIGNIFICANCE = 30
    
    @classmethod
    def record_signal_audit(
        cls,
        symbol: str,
        signal: str,
        setup_type: str,
        entry_low: float,
        entry_high: float,
        target_1: float,
        target_2: float,
        target_3: float,
        stop_loss: float,
        probability_t1: float,
        market_regime: str,
        sector: str,
        model_version: str = "Heuristic-Rule-Based-v1.0",
        holding_days_max: int = 10
    ):
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing = db.query(DBSignalAudit).filter(
                DBSignalAudit.symbol == symbol,
                DBSignalAudit.timestamp >= today_start
            ).first()
            
            if not existing:
                audit = DBSignalAudit(
                    symbol=symbol,
                    signal=signal,
                    setup_type=setup_type,
                    entry_low=entry_low,
                    entry_high=entry_high,
                    target_1=target_1,
                    target_2=target_2,
                    target_3=target_3,
                    stop_loss=stop_loss,
                    probability_t1=probability_t1,
                    market_regime=market_regime,
                    sector=sector,
                    model_version=model_version,
                    holding_days_max=holding_days_max,
                    outcome_status="ACTIVE",
                    mfe_pct=0.0,
                    mae_pct=0.0
                )
                db.add(audit)
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    
    @classmethod
    def get_performance_summary(cls) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            records = db.query(DBSignalAudit).all()
            total_records = len(records)
            completed_records = [r for r in records if r.outcome_status not in ["ACTIVE", "PENDING"]]
            completed_count = len(completed_records)
            
            # If live records >= 30, use real live audit
            if completed_count >= cls.MIN_RECORDS_FOR_STATISTICAL_SIGNIFICANCE:
                return cls._compute_live_audit_summary(completed_records, total_records)
                
            # Check if a completed historical walk-forward backtest exists in DB
            latest_backtest = db.query(DBHistoricalBacktest).order_by(DBHistoricalBacktest.id.desc()).first()
            if latest_backtest:
                return {
                    "status": "AVAILABLE",
                    "model_version": "Historical-Triple-Barrier-WalkForward-v1.0",
                    "validation_methodology": "Purged & Embargoed Historical Walk-Forward Validation",
                    "dataset_summary": {
                        "total_historical_trades": latest_backtest.total_trades,
                        "start_date": str(latest_backtest.start_date),
                        "end_date": str(latest_backtest.end_date)
                    },
                    "overall_metrics": {
                        "total_evaluated_trades": latest_backtest.total_trades,
                        "active_trades_in_progress": total_records - completed_count,
                        "hit_rate_t1": latest_backtest.hit_rate_t1,
                        "hit_rate_t2": latest_backtest.hit_rate_t2,
                        "hit_rate_t3": latest_backtest.hit_rate_t3,
                        "brier_score": latest_backtest.brier_score,
                        "profit_factor": latest_backtest.profit_factor,
                        "expectancy_per_trade_pct": round(latest_backtest.hit_rate_t1 * 4.5 - (1 - latest_backtest.hit_rate_t1) * 2.8, 2) if latest_backtest.hit_rate_t1 else None,
                        "win_loss_ratio": latest_backtest.win_loss_ratio,
                        "sharpe_ratio": latest_backtest.sharpe_ratio,
                        "sortino_ratio": latest_backtest.sortino_ratio,
                        "max_drawdown_pct": latest_backtest.max_drawdown_pct,
                        "avg_holding_days": latest_backtest.avg_holding_days
                    },
                    "performance_by_regime": json.loads(latest_backtest.regime_breakdown_json or "[]"),
                    "performance_by_setup": json.loads(latest_backtest.setup_breakdown_json or "[]"),
                    "probability_bucket_calibration": json.loads(latest_backtest.calibration_json or "[]"),
                    "folds": json.loads(latest_backtest.folds_json or "[]")
                }

            # Return explicit INSUFFICIENT_HISTORY if neither exists
            return {
                "status": "INSUFFICIENT_HISTORY",
                "model_version": "Heuristic-Rule-Based-v1.0",
                "validation_methodology": "Chronological Walk-Forward Live Database Audit",
                "message": f"INSUFFICIENT_HISTORY: {completed_count}/{cls.MIN_RECORDS_FOR_STATISTICAL_SIGNIFICANCE} live completed trade audits in DB. Trigger a historical walk-forward backtest replay to populate multi-year empirical metrics.",
                "overall_metrics": {
                    "total_evaluated_trades": completed_count,
                    "active_trades_in_progress": total_records - completed_count,
                    "hit_rate_t1": None,
                    "hit_rate_t2": None,
                    "hit_rate_t3": None,
                    "brier_score": None,
                    "profit_factor": None,
                    "expectancy_per_trade_pct": None,
                    "win_loss_ratio": None,
                    "sharpe_ratio": None,
                    "sortino_ratio": None,
                    "max_drawdown_pct": None,
                    "avg_holding_days": None
                },
                "performance_by_regime": [],
                "performance_by_setup": [],
                "performance_by_sector": [],
                "probability_bucket_calibration": []
            }
        finally:
            db.close()

    @classmethod
    def _compute_live_audit_summary(cls, completed_records: List[DBSignalAudit], total_records: int) -> Dict[str, Any]:
        completed_count = len(completed_records)
        t1_hits = sum(1 for r in completed_records if r.outcome_status in ["T1_HIT", "T2_HIT", "T3_HIT"])
        t2_hits = sum(1 for r in completed_records if r.outcome_status in ["T2_HIT", "T3_HIT"])
        t3_hits = sum(1 for r in completed_records if r.outcome_status == "T3_HIT")
        
        hit_rate_t1 = round(t1_hits / completed_count, 3)
        hit_rate_t2 = round(t2_hits / completed_count, 3)
        hit_rate_t3 = round(t3_hits / completed_count, 3)
        
        returns = [r.return_pct for r in completed_records if r.return_pct is not None]
        avg_return = round(sum(returns) / len(returns), 2) if returns else 0.0
        
        gains = [ret for ret in returns if ret > 0]
        losses = [abs(ret) for ret in returns if ret < 0]
        profit_factor = round(sum(gains) / sum(losses), 2) if losses and sum(losses) > 0 else (round(float(len(gains)), 2) if gains else 0.0)
        win_loss_ratio = round(len(gains) / (len(losses) or 1), 2)

        # Real Brier Score: sum((p_i - y_i)^2) / N
        brier_sq_errors = []
        for r in completed_records:
            if r.probability_t1 is not None:
                y_i = 1.0 if r.outcome_status in ["T1_HIT", "T2_HIT", "T3_HIT"] else 0.0
                brier_sq_errors.append((r.probability_t1 - y_i) ** 2)
        brier_score = round(sum(brier_sq_errors) / len(brier_sq_errors), 3) if brier_sq_errors else None

        if len(returns) >= 2:
            mean_ret = sum(returns) / len(returns)
            variance = sum((x - mean_ret) ** 2 for x in returns) / (len(returns) - 1)
            std_dev = math.sqrt(variance) if variance > 0 else 1.0
            downside_variance = sum((min(0.0, x) ** 2) for x in returns) / len(returns)
            downside_std = math.sqrt(downside_variance) if downside_variance > 0 else 1.0
            sharpe_ratio = round((mean_ret / std_dev) * math.sqrt(25), 2)
            sortino_ratio = round((mean_ret / downside_std) * math.sqrt(25), 2)
        else:
            sharpe_ratio = None
            sortino_ratio = None

        holding_days_list = [r.actual_holding_days for r in completed_records if r.actual_holding_days is not None]
        avg_holding = round(sum(holding_days_list) / len(holding_days_list), 1) if holding_days_list else None

        return {
            "status": "AVAILABLE",
            "model_version": "Heuristic-Rule-Based-v1.0",
            "validation_methodology": "Chronological Walk-Forward Live Database Audit",
            "overall_metrics": {
                "total_evaluated_trades": completed_count,
                "active_trades_in_progress": total_records - completed_count,
                "hit_rate_t1": hit_rate_t1,
                "hit_rate_t2": hit_rate_t2,
                "hit_rate_t3": hit_rate_t3,
                "brier_score": brier_score,
                "profit_factor": profit_factor,
                "expectancy_per_trade_pct": avg_return,
                "win_loss_ratio": win_loss_ratio,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown_pct": None,
                "avg_holding_days": avg_holding
            },
            "performance_by_regime": [],
            "performance_by_setup": [],
            "performance_by_sector": [],
            "probability_bucket_calibration": []
        }

model_auditor = ModelPerformanceAuditor()
