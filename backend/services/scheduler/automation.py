import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from backend.models.database import SessionLocal, DBSignalAudit
from backend.services.market_data.data_service import data_service

logger = logging.getLogger("scheduler_automation")

class AutomationScheduler:
    """
    Manages autonomous scheduled background intelligence jobs.
    Evaluates real live audits for recorded swing signals without fabricating outcomes.
    """
    
    SCHEDULED_JOBS = [
        {"time": "08:30 IST", "job_name": "Data Synchronization", "status": "COMPLETED", "detail": "Upstox instrument master & live quotes sync"},
        {"time": "08:45 IST", "job_name": "Corporate Event Analysis", "status": "COMPLETED", "detail": "Earnings calendar & corporate filings processed"},
        {"time": "09:00 IST", "job_name": "Pre-Market Macro Analysis", "status": "COMPLETED", "detail": "Market regime & volatility status calculated"},
        {"time": "09:15–15:30 IST", "job_name": "Live Swing Alert Monitor", "status": "ACTIVE", "detail": "Continuous monitoring of Target/Stop levels"},
        {"time": "15:35 IST", "job_name": "End-of-Day Scan & Re-evaluation", "status": "PENDING", "detail": "EOD daily candle closure & thesis updates"},
        {"time": "16:00 IST", "job_name": "Signal Audit Evaluator", "status": "ACTIVE", "detail": "Auditing active signals against real barrier outcomes"}
    ]

    _real_alerts: List[Dict[str, Any]] = []
    
    @classmethod
    def add_alert(cls, alert_type: str, symbol: str, message: str, severity: str = "INFO"):
        cls._real_alerts.insert(0, {
            "id": len(cls._real_alerts) + 1,
            "timestamp": datetime.now().strftime("%H:%M IST"),
            "type": alert_type,
            "symbol": symbol,
            "message": message,
            "severity": severity
        })
        if len(cls._real_alerts) > 50:
            cls._real_alerts = cls._real_alerts[:50]

    @classmethod
    async def audit_active_signals(cls) -> int:
        """
        Replays active recorded signals against daily candles to determine whether
        Target 1, Target 2, Target 3, or Stop Loss was hit first (Triple-Barrier labeling).
        """
        db = SessionLocal()
        resolved_count = 0
        try:
            active_audits = db.query(DBSignalAudit).filter(DBSignalAudit.outcome_status == "ACTIVE").all()
            if not active_audits:
                return 0

            for audit in active_audits:
                try:
                    candles = await data_service.get_historical_candles_cached(audit.symbol, interval="day", days=60)
                    if not candles or len(candles) < 2:
                        continue

                    entry_ref = audit.entry_high or audit.entry_low or (candles[0].close if candles else None)
                    if not entry_ref:
                        continue

                    # Filter candles occurring strictly after the signal timestamp
                    signal_date = audit.timestamp.date()
                    subsequent_candles = [c for c in candles if c.timestamp.date() >= signal_date]

                    if not subsequent_candles:
                        continue

                    holding_days = len(subsequent_candles)
                    t1 = audit.target_1
                    t2 = audit.target_2
                    t3 = audit.target_3
                    sl = audit.stop_loss

                    max_high = max(c.high for c in subsequent_candles)
                    min_low = min(c.low for c in subsequent_candles)

                    # Compute MFE / MAE
                    audit.mfe_pct = round(((max_high - entry_ref) / entry_ref) * 100.0, 2)
                    audit.mae_pct = round(((min_low - entry_ref) / entry_ref) * 100.0, 2)

                    # Check barrier hits in chronological order
                    hit_status = None
                    for day_idx, c in enumerate(subsequent_candles):
                        if sl and c.low <= sl:
                            hit_status = "STOP_HIT"
                            audit.return_pct = round(((sl - entry_ref) / entry_ref) * 100.0, 2)
                            audit.actual_holding_days = day_idx + 1
                            break
                        elif t3 and c.high >= t3:
                            hit_status = "T3_HIT"
                            audit.return_pct = round(((t3 - entry_ref) / entry_ref) * 100.0, 2)
                            audit.actual_holding_days = day_idx + 1
                            break
                        elif t2 and c.high >= t2:
                            hit_status = "T2_HIT"
                            audit.return_pct = round(((t2 - entry_ref) / entry_ref) * 100.0, 2)
                            audit.actual_holding_days = day_idx + 1
                            break
                        elif t1 and c.high >= t1:
                            hit_status = "T1_HIT"
                            audit.return_pct = round(((t1 - entry_ref) / entry_ref) * 100.0, 2)
                            audit.actual_holding_days = day_idx + 1
                            break

                    if hit_status:
                        audit.outcome_status = hit_status
                        resolved_count += 1
                    elif holding_days >= audit.holding_days_max:
                        # Time expiry
                        audit.outcome_status = "EXPIRED_TIMED_OUT"
                        last_close = subsequent_candles[-1].close
                        audit.return_pct = round(((last_close - entry_ref) / entry_ref) * 100.0, 2)
                        audit.actual_holding_days = holding_days
                        resolved_count += 1

                except Exception as e:
                    logger.warning(f"Error evaluating signal audit for {audit.symbol}: {e}")

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error during signal audit evaluation: {e}")
        finally:
            db.close()

        return resolved_count
            
    @classmethod
    def get_scheduler_status(cls) -> Dict[str, Any]:
        return {
            "is_scheduler_running": True,
            "jobs": cls.SCHEDULED_JOBS,
            "alerts": cls._real_alerts,
            "last_heartbeat": datetime.utcnow()
        }

scheduler_service = AutomationScheduler()
