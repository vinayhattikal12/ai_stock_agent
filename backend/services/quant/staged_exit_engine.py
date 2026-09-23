import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
from backend.models.schemas import StagedExitPlan, TradeLevels, Candle, TechnicalIndicators

logger = logging.getLogger("staged_exit_engine")

class StagedExitEngine:
    """
    Professional Swing Staged Exit & Trailing Stop Engine.
    Executes disciplined partial scale-outs:
      1. Entry -> T1: Hold position with initial structural stop.
      2. T1 Hit: Book 50% profits, shift trailing stop to Breakeven (+0.3% buffer). Zero open risk.
      3. T2 Hit: Book 25% profits, trail remaining 25% runner under 9-day EMA.
      4. T3 Hit / Reversal: Book final 25% quantity.
      5. Time-Decay: If held > 10 trading days without progress, trigger capital reallocation exit.
    """

    MAX_HOLDING_DAYS_BEFORE_STAGNATION = 10
    BREAKEVEN_BUFFER_PCT = 0.3  # 0.3% above buy price to cover STT & exchange fees

    @classmethod
    def evaluate_staged_exit(
        cls,
        buy_price: float,
        current_price: float,
        purchase_date: Optional[date],
        levels: TradeLevels,
        indicators: Optional[TechnicalIndicators] = None,
        candles: Optional[List[Candle]] = None
    ) -> StagedExitPlan:
        """
        Determines the current exit stage, exact Rupee trailing stop, and partial exit recommendation.
        """
        if buy_price <= 0 or current_price <= 0:
            return StagedExitPlan()

        t1 = levels.target_1 if (levels and levels.target_1) else round(buy_price * 1.06, 2)
        t2 = levels.target_2 if (levels and levels.target_2) else round(buy_price * 1.12, 2)
        t3 = levels.target_3 if (levels and levels.target_3) else round(buy_price * 1.18, 2)
        initial_sl = levels.stop_loss if (levels and levels.stop_loss) else round(buy_price * 0.965, 2)

        # Calculate holding days
        days_elapsed = 0
        if purchase_date:
            try:
                p_date = purchase_date if isinstance(purchase_date, date) else datetime.strptime(str(purchase_date), "%Y-%m-%d").date()
                days_elapsed = max(0, (date.today() - p_date).days)
            except Exception:
                days_elapsed = 0

        pnl_pct = round(((current_price - buy_price) / buy_price) * 100.0, 2)
        breakeven_price = round(buy_price * (1.0 + cls.BREAKEVEN_BUFFER_PCT / 100.0), 2)
        ema_9 = indicators.ema_20 if (indicators and indicators.ema_20) else breakeven_price
        
        # Get highest price achieved since purchase if candles available
        highest_price = current_price
        if candles and len(candles) >= 5:
            highest_price = max(c.high for c in candles[-min(len(candles), max(5, days_elapsed + 2)):])

        # 1. Check Stop Loss Violation
        if current_price <= initial_sl and highest_price < t1:
            return StagedExitPlan(
                current_stage="STOP_LOSS_EXIT",
                stage_label="Protective Stop Loss Violated",
                recommended_action=f"SELL FULL POSITION: Current price ₹{current_price:,.2f} has breached initial stop loss (₹{initial_sl:,.2f}). Cut loss immediately.",
                trailing_stop_price=initial_sl,
                trailing_stop_display=f"₹{initial_sl:,.2f} (Breached)",
                trailing_stop_type="INITIAL_SWING_LOW",
                is_risk_free=False,
                booked_profit_pct=0.0,
                next_milestone_price=None,
                next_milestone_label="N/A - Stop Hit",
                time_stop_days_remaining=0,
                time_stop_triggered=False
            )

        # 2. Check Stage 3: Target 3 Reached
        if highest_price >= t3 or current_price >= t3:
            trail_sl = round(max(breakeven_price, current_price * 0.965), 2)
            return StagedExitPlan(
                current_stage="T3_COMPLETED",
                stage_label="Target 3 Achieved (+15–20% Swing Run)",
                recommended_action=f"CLOSE FINAL 25% RUNNER: Target 3 (₹{t3:,.2f}) achieved. Book remaining position or trail tight at ₹{trail_sl:,.2f}.",
                trailing_stop_price=trail_sl,
                trailing_stop_display=f"₹{trail_sl:,.2f} (Runner Stop)",
                trailing_stop_type="EMA_9_TRAIL",
                is_risk_free=True,
                booked_profit_pct=75.0,
                next_milestone_price=t3,
                next_milestone_label="T3 Milestone Reached",
                time_stop_days_remaining=0,
                time_stop_triggered=False
            )

        # 3. Check Stage 2: Target 2 Reached
        if highest_price >= t2 or current_price >= t2:
            trail_sl = round(max(breakeven_price, (ema_9 if ema_9 > breakeven_price else t1)), 2)
            return StagedExitPlan(
                current_stage="T2_PROFIT_TAKEN_RUNNER_ACTIVE",
                stage_label="Target 2 Hit — 75% Total Profit Realized",
                recommended_action=f"BOOK 25% QUANTITY: Target 2 (₹{t2:,.2f}) achieved. Book 25% shares now (75% total booked). Trail remaining 25% runner with SL at ₹{trail_sl:,.2f}.",
                trailing_stop_price=trail_sl,
                trailing_stop_display=f"₹{trail_sl:,.2f} (9 EMA Trail)",
                trailing_stop_type="EMA_9_TRAIL",
                is_risk_free=True,
                booked_profit_pct=75.0,
                next_milestone_price=t3,
                next_milestone_label=f"Target 3 at ₹{t3:,.2f}",
                time_stop_days_remaining=0,
                time_stop_triggered=False
            )

        # 4. Check Stage 1: Target 1 Reached
        if highest_price >= t1 or current_price >= t1:
            return StagedExitPlan(
                current_stage="T1_PROFIT_TAKEN_BREAKEVEN_ACTIVE",
                stage_label="Target 1 Hit — Breakeven Stop Active",
                recommended_action=f"BOOK 50% QUANTITY: Target 1 (₹{t1:,.2f}) reached. Sell 50% of your shares to lock in gains. Trailing Stop is now moved to Breakeven at ₹{breakeven_price:,.2f}. Trade is 100% Risk-Free!",
                trailing_stop_price=breakeven_price,
                trailing_stop_display=f"₹{breakeven_price:,.2f} (Cost + STT)",
                trailing_stop_type="BREAKEVEN_BUFFER",
                is_risk_free=True,
                booked_profit_pct=50.0,
                next_milestone_price=t2,
                next_milestone_label=f"Target 2 at ₹{t2:,.2f}",
                time_stop_days_remaining=max(0, 10 - days_elapsed),
                time_stop_triggered=False
            )

        # 5. Check Time Decay / Stagnation Exit
        time_remaining = max(0, cls.MAX_HOLDING_DAYS_BEFORE_STAGNATION - days_elapsed)
        if days_elapsed >= cls.MAX_HOLDING_DAYS_BEFORE_STAGNATION and pnl_pct < 2.0:
            return StagedExitPlan(
                current_stage="TIME_DECAY_EXIT_TRIGGERED",
                stage_label="Time-Decay Stagnation Warning",
                recommended_action=f"TIME-STOP EXIT: Position has consolidated for {days_elapsed} days without reaching Target 1 (+{pnl_pct}% return). Exit on market open to redeploy capital into fresh momentum leaders.",
                trailing_stop_price=initial_sl,
                trailing_stop_display=f"₹{initial_sl:,.2f}",
                trailing_stop_type="INITIAL_SWING_LOW",
                is_risk_free=False,
                booked_profit_pct=0.0,
                next_milestone_price=t1,
                next_milestone_label=f"Target 1 at ₹{t1:,.2f}",
                time_stop_days_remaining=0,
                time_stop_triggered=True,
                time_decay_guidance=f"Stagnant for {days_elapsed} trading days. Free up capital."
            )

        # 6. Default: Pre-T1 Initial Stage
        return StagedExitPlan(
            current_stage="PRE_T1_ACCUMULATION",
            stage_label="Initial Accumulation Stage",
            recommended_action=f"HOLD: Target 1 overhead at ₹{t1:,.2f}. Protective Stop Loss active at ₹{initial_sl:,.2f}.",
            trailing_stop_price=initial_sl,
            trailing_stop_display=f"₹{initial_sl:,.2f} ({levels.stop_reason})",
            trailing_stop_type="INITIAL_SWING_LOW",
            is_risk_free=False,
            booked_profit_pct=0.0,
            next_milestone_price=t1,
            next_milestone_label=f"Target 1 at ₹{t1:,.2f} (+{round(((t1 - buy_price)/buy_price)*100, 1)}%)",
            time_stop_days_remaining=time_remaining,
            time_stop_triggered=False
        )

staged_exit_engine = StagedExitEngine()
