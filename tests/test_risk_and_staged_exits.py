import pytest
from datetime import date, timedelta
from backend.models.schemas import TradeLevels, Candle, TechnicalIndicators, HoldingAnalysis
from backend.services.quant.risk_manager import risk_manager
from backend.services.quant.staged_exit_engine import staged_exit_engine

# --- 1. Test 1% Account Risk Sizing Identity ---
def test_1_pct_risk_sizing_identity():
    """
    Capital = ₹5,00,000, Risk = 1.0% (₹5,000).
    Entry = ₹2,113.42, Stop Loss = ₹2,064.92 -> Risk per share = ₹48.50.
    Expected shares = floor(5000 / 48.50) = 103 shares.
    Allocated capital = 103 * 2113.42 = ₹2,17,682.26.
    """
    capital = 500000.0
    risk_pct = 1.0
    entry = 2113.42
    stop = 2064.92
    target_1 = 2177.14

    risk_metrics = risk_manager.calculate_position_risk(
        entry_price=entry,
        stop_loss_price=stop,
        target_1_price=target_1,
        win_probability=0.65,
        account_capital=capital,
        risk_per_trade_pct=risk_pct
    )

    assert risk_metrics.max_rupees_at_risk == 5000.0
    assert risk_metrics.risk_per_share == 48.50
    # 20% cap on 5L is 1L (47 shares). Let's test with 50% cap to test raw risk formula
    risk_metrics_uncapped = risk_manager.calculate_position_risk(
        entry_price=entry,
        stop_loss_price=stop,
        target_1_price=target_1,
        win_probability=0.65,
        account_capital=capital,
        risk_per_trade_pct=risk_pct,
        max_single_position_pct=50.0
    )
    assert risk_metrics_uncapped.suggested_shares == 103
    assert risk_metrics_uncapped.allocated_capital == round(103 * 2113.42, 2)
    assert risk_metrics_uncapped.expected_value_inr is not None
    assert risk_metrics_uncapped.expected_value_inr > 0

# --- 2. Test Staged Exit Engine: Pre-T1 -> T1 Breakeven Shift ---
def test_staged_exit_pre_t1_and_t1_hit():
    levels = TradeLevels(
        current_price=2100.0,
        reference_entry=2100.0,
        stop_loss=2050.0,
        target_1=2200.0,
        target_2=2300.0,
        target_3=2400.0,
        stop_method="SWING_LOW",
        stop_reason="Structural support",
        levels_reasoning=[]
    )

    # 1. Pre-T1
    plan_pre = staged_exit_engine.evaluate_staged_exit(
        buy_price=2100.0,
        current_price=2140.0,
        purchase_date=date.today(),
        levels=levels
    )
    assert plan_pre.current_stage == "PRE_T1_ACCUMULATION"
    assert plan_pre.is_risk_free is False
    assert plan_pre.trailing_stop_price == 2050.0

    # 2. T1 Hit: Trailing Stop must move to Breakeven (+0.3% buffer = ₹2,106.30)
    plan_t1 = staged_exit_engine.evaluate_staged_exit(
        buy_price=2100.0,
        current_price=2205.0, # Above T1
        purchase_date=date.today(),
        levels=levels
    )
    assert plan_t1.current_stage == "T1_PROFIT_TAKEN_BREAKEVEN_ACTIVE"
    assert plan_t1.is_risk_free is True
    assert plan_t1.booked_profit_pct == 50.0
    assert plan_t1.trailing_stop_price == 2106.30 # Breakeven buffer

# --- 3. Test Time-Decay Stagnation Exit ---
def test_staged_exit_time_decay_stagnation():
    levels = TradeLevels(
        current_price=2110.0,
        reference_entry=2100.0,
        stop_loss=2050.0,
        target_1=2200.0,
        target_2=2300.0,
        stop_method="SWING_LOW",
        stop_reason="Structural support",
        levels_reasoning=[]
    )
    # 15 days elapsed with only +0.47% return
    old_date = date.today() - timedelta(days=15)
    plan_stagnant = staged_exit_engine.evaluate_staged_exit(
        buy_price=2100.0,
        current_price=2110.0,
        purchase_date=old_date,
        levels=levels
    )
    assert plan_stagnant.current_stage == "TIME_DECAY_EXIT_TRIGGERED"
    assert plan_stagnant.time_stop_triggered is True
    assert "TIME-STOP EXIT" in plan_stagnant.recommended_action

# --- 4. Test Portfolio Heat Calculation ---
def test_portfolio_heat_aggregation():
    # 3 active holdings with defined risk
    levels_1 = TradeLevels(current_price=2100.0, stop_loss=2000.0, stop_method="SWING_LOW", stop_reason="SL", levels_reasoning=[])
    levels_2 = TradeLevels(current_price=1000.0, stop_loss=950.0, stop_method="SWING_LOW", stop_reason="SL", levels_reasoning=[])

    h1 = HoldingAnalysis(
        id=1, symbol="TCS", company_name="TCS", sector="IT", quantity=50, buy_price=2100.0,
        purchase_date=date.today(), current_price=2100.0, total_invested=105000.0, current_value=105000.0,
        unrealized_pnl=0.0, unrealized_pnl_pct=0.0, signal="HOLD", thesis_status="STABLE",
        levels=levels_1, ml_probability=None, last_evaluated_at=date.today()
    ) # Open risk: 50 * (2100 - 2000) = ₹5,000

    h2 = HoldingAnalysis(
        id=2, symbol="INFY", company_name="INFY", sector="IT", quantity=100, buy_price=1000.0,
        purchase_date=date.today(), current_price=1000.0, total_invested=100000.0, current_value=100000.0,
        unrealized_pnl=0.0, unrealized_pnl_pct=0.0, signal="HOLD", thesis_status="STABLE",
        levels=levels_2, ml_probability=None, last_evaluated_at=date.today()
    ) # Open risk: 100 * (1000 - 950) = ₹5,000

    heat = risk_manager.evaluate_portfolio_heat([h1, h2], account_capital=500000.0)
    assert heat.total_open_risk_inr == 10000.0 # ₹10,000 total open risk
    assert heat.portfolio_heat_pct == 2.0      # 10,000 / 5,00,000 = 2.0%
    assert heat.heat_status == "OPTIMAL"
    assert heat.available_risk_budget_pct == 4.0 # 6.0 - 2.0 = 4.0%
