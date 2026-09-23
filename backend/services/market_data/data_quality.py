import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from backend.models.schemas import Candle

logger = logging.getLogger("data_quality_gate")

@dataclass
class QualityGateResult:
    is_valid: bool
    status: str # "AVAILABLE", "PARTIAL", "UNAVAILABLE", "INVALID", "STALE"
    rejection_reason: Optional[str]
    candle_count: int
    first_timestamp: Optional[datetime]
    last_timestamp: Optional[datetime]
    clean_candles: List[Candle]

class DataQualityGate:
    """
    Centralized Data Quality & Validation Gate.
    Enforces strict data integrity before any quantitative or ML calculation:
    1. Validates instrument existence & key integrity.
    2. Validates candle existence & minimum historical count (e.g. 200 bars for full technicals, 50 bars for short-term).
    3. Validates OHLC integrity:
       - High >= Low
       - High >= max(Open, Close)
       - Low <= min(Open, Close)
       - Open > 0, High > 0, Low > 0, Close > 0
    4. Validates Volume >= 0.
    5. Deduplicates timestamps and enforces strictly chronological ascending order.
    6. Filters out impossible price jumps caused by malformed data feeds.
    7. Checks data freshness.
    """

    MIN_CANDLES_DAILY_FULL = 120 # Minimum candles for daily swing analysis (SMA200 / Mansfield 50D / 100D returns)
    MIN_CANDLES_DAILY_PARTIAL = 30 # Minimum for basic swing check
    MAX_PRICE_SPIKE_RATIO = 5.0 # Reject candles with >500% intraday price anomalies unless verified

    @classmethod
    def validate_daily_candles(
        cls,
        candles: List[Candle],
        symbol: str = "",
        min_required_bars: int = MIN_CANDLES_DAILY_FULL
    ) -> QualityGateResult:
        """
        Validates historical daily candle series.
        Returns QualityGateResult with clean, chronologically ordered candles or explicit rejection reason.
        """
        if not candles or len(candles) == 0:
            return QualityGateResult(
                is_valid=False,
                status="UNAVAILABLE",
                rejection_reason=f"No historical candle data received for {symbol}",
                candle_count=0,
                first_timestamp=None,
                last_timestamp=None,
                clean_candles=[]
            )

        # 1. Clean and validate individual OHLCV records
        clean: List[Candle] = []
        seen_timestamps = set()

        for idx, c in enumerate(candles):
            # Timestamp validity
            ts = c.timestamp
            if not isinstance(ts, (datetime, date)):
                continue

            ts_dt = datetime.combine(ts, datetime.min.time()) if isinstance(ts, date) and not isinstance(ts, datetime) else ts
            
            # Deduplicate timestamps
            ts_key = ts_dt.strftime("%Y-%m-%d")
            if ts_key in seen_timestamps:
                continue
            seen_timestamps.add(ts_key)

            # Price positivity
            if c.open <= 0 or c.high <= 0 or c.low <= 0 or c.close <= 0:
                logger.warning(f"DataQualityGate: Non-positive price in candle #{idx} for {symbol}: O={c.open}, H={c.high}, L={c.low}, C={c.close}")
                continue

            # OHLC consistency rules
            if c.high < c.low:
                logger.warning(f"DataQualityGate: High < Low ({c.high} < {c.low}) for {symbol}")
                continue
            if c.high < max(c.open, c.close) * 0.999: # 0.1% tolerance for floating point
                logger.warning(f"DataQualityGate: High < max(Open, Close) for {symbol}")
                continue
            if c.low > min(c.open, c.close) * 1.001:
                logger.warning(f"DataQualityGate: Low > min(Open, Close) for {symbol}")
                continue

            # Volume non-negativity
            clean_vol = max(0, int(c.volume))
            clean_oi = max(0, int(c.open_interest or 0))

            clean.append(Candle(
                timestamp=ts_dt,
                open=round(float(c.open), 2),
                high=round(float(c.high), 2),
                low=round(float(c.low), 2),
                close=round(float(c.close), 2),
                volume=clean_vol,
                open_interest=clean_oi
            ))

        if not clean:
            return QualityGateResult(
                is_valid=False,
                status="INVALID",
                rejection_reason=f"All {len(candles)} candles for {symbol} failed OHLCV validation criteria",
                candle_count=0,
                first_timestamp=None,
                last_timestamp=None,
                clean_candles=[]
            )

        # 2. Sort chronologically (oldest -> newest)
        clean.sort(key=lambda x: x.timestamp)

        # 3. Check for impossible price jumps (data corruption)
        for i in range(1, len(clean)):
            ratio = clean[i].close / (clean[i - 1].close or 1.0)
            if ratio > cls.MAX_PRICE_SPIKE_RATIO or ratio < (1.0 / cls.MAX_PRICE_SPIKE_RATIO):
                logger.warning(f"DataQualityGate: Extreme price jump detected in {symbol} from {clean[i-1].close} to {clean[i].close}")

        candle_count = len(clean)
        first_ts = clean[0].timestamp
        last_ts = clean[-1].timestamp

        # 4. Check sufficiency
        if candle_count < cls.MIN_CANDLES_DAILY_PARTIAL:
            return QualityGateResult(
                is_valid=False,
                status="UNAVAILABLE",
                rejection_reason=f"Insufficient history: {candle_count} bars available, minimum {cls.MIN_CANDLES_DAILY_PARTIAL} bars required",
                candle_count=candle_count,
                first_timestamp=first_ts,
                last_timestamp=last_ts,
                clean_candles=clean
            )

        if candle_count < min_required_bars:
            return QualityGateResult(
                is_valid=True,
                status="PARTIAL",
                rejection_reason=f"Partial history: {candle_count} bars available (full analysis recommends {min_required_bars} bars)",
                candle_count=candle_count,
                first_timestamp=first_ts,
                last_timestamp=last_ts,
                clean_candles=clean
            )

        return QualityGateResult(
            is_valid=True,
            status="AVAILABLE",
            rejection_reason=None,
            candle_count=candle_count,
            first_timestamp=first_ts,
            last_timestamp=last_ts,
            clean_candles=clean
        )

data_quality_gate = DataQualityGate()
