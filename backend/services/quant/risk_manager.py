import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from backend.models.schemas import RiskManagementMetrics, PortfolioHeatSummary, HoldingAnalysis, TradeLevels

logger = logging.getLogger("risk_manager")

class RiskManager:
    """
    Institutional Risk & Position Sizing Engine.
    Enforces strict 1% Account Risk rules, Portfolio Heat limits (<= 6%), Expected Value (EV) evaluation,
    and Half-Kelly optimal capital allocation for Indian equities.
    """

    DEFAULT_ACCOUNT_CAPITAL = 500000.0  # ₹5,00,000 baseline
    DEFAULT_RISK_PER_TRADE_PCT = 1.0     # 1.0% risk per trade
    MAX_POSITION_ALLOCATION_PCT = 20.0  # Maximum 20% of portfolio in a single stock
    MAX_PORTFOLIO_HEAT_PCT = 6.0        # Maximum 6% total concurrent risk

    @classmethod
    def calculate_position_risk(
        cls,
        entry_price: float,
        stop_loss_price: float,
        target_1_price: Optional[float] = None,
        win_probability: Optional[float] = None,
        account_capital: float = DEFAULT_ACCOUNT_CAPITAL,
        risk_per_trade_pct: float = DEFAULT_RISK_PER_TRADE_PCT,
        max_single_position_pct: float = MAX_POSITION_ALLOCATION_PCT
    ) -> RiskManagementMetrics:
        """
        Calculates exact share sizing, Rupee allocation, Expected Value (EV), and Kelly sizing.
        """
        if entry_price <= 0 or stop_loss_price <= 0 or stop_loss_price >= entry_price:
            return RiskManagementMetrics(
                account_capital=account_capital,
                risk_per_trade_pct=risk_per_trade_pct,
                max_rupees_at_risk=round(account_capital * (risk_per_trade_pct / 100.0), 2),
                reference_entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                risk_per_share=0.0,
                suggested_shares=0,
                allocated_capital=0.0,
                portfolio_allocation_pct=0.0
            )

        max_risk_inr = round(account_capital * (risk_per_trade_pct / 100.0), 2)
        risk_per_share = round(entry_price - stop_loss_price, 2)

        # Base shares from risk rule
        raw_shares = math.floor(max_risk_inr / risk_per_share) if risk_per_share > 0 else 0
        allocated_capital = round(raw_shares * entry_price, 2)

        # Cap by maximum portfolio single position allocation (e.g. 20%)
        max_capital_for_stock = account_capital * (max_single_position_pct / 100.0)
        is_capped = False
        if allocated_capital > max_capital_for_stock:
            raw_shares = math.floor(max_capital_for_stock / entry_price)
            allocated_capital = round(raw_shares * entry_price, 2)
            is_capped = True

        actual_shares = max(0, raw_shares)
        portfolio_alloc_pct = round((allocated_capital / account_capital) * 100.0, 2) if account_capital > 0 else 0.0

        # Expected Value ($EV$) and Kelly calculation
        p_win = win_probability if (win_probability is not None and 0.0 < win_probability < 1.0) else 0.60
        p_loss = 1.0 - p_win
        reward_t1 = round((target_1_price - entry_price), 2) if (target_1_price and target_1_price > entry_price) else round(risk_per_share * 1.5, 2)

        # EV per share in ₹
        ev_per_share = (p_win * reward_t1) - (p_loss * risk_per_share)
        total_ev_inr = round(ev_per_share * actual_shares, 2)
        ev_r_multiple = round(ev_per_share / risk_per_share, 2) if risk_per_share > 0 else None

        # Kelly Criterion: f* = (p*b - q)/b where b = reward/risk
        b_ratio = (reward_t1 / risk_per_share) if risk_per_share > 0 else 1.5
        kelly_fraction = max(0.0, (p_win * b_ratio - p_loss) / b_ratio) if b_ratio > 0 else 0.0
        # Apply Half-Kelly for realistic drawdowns
        half_kelly_pct = round((kelly_fraction / 2.0) * 100.0, 2)
        kelly_capital = account_capital * (half_kelly_pct / 100.0)
        kelly_shares = max(0, math.floor(kelly_capital / entry_price))

        actual_risk_inr = round(actual_shares * risk_per_share, 2)
        heat_contrib_pct = round((actual_risk_inr / account_capital) * 100.0, 2) if account_capital > 0 else 0.0

        return RiskManagementMetrics(
            account_capital=account_capital,
            risk_per_trade_pct=risk_per_trade_pct,
            max_rupees_at_risk=max_risk_inr,
            reference_entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            risk_per_share=risk_per_share,
            suggested_shares=actual_shares,
            allocated_capital=allocated_capital,
            portfolio_allocation_pct=portfolio_alloc_pct,
            max_single_position_pct=max_single_position_pct,
            is_allocation_capped=is_capped,
            expected_value_inr=total_ev_inr,
            expected_value_r_multiple=ev_r_multiple,
            kelly_criterion_pct=half_kelly_pct,
            kelly_suggested_shares=kelly_shares,
            portfolio_heat_contribution_pct=heat_contrib_pct
        )

    @classmethod
    def evaluate_portfolio_heat(
        cls,
        holdings: List[HoldingAnalysis],
        account_capital: float = DEFAULT_ACCOUNT_CAPITAL,
        max_allowed_heat_pct: float = MAX_PORTFOLIO_HEAT_PCT
    ) -> PortfolioHeatSummary:
        """
        Aggregates open risk across all holdings to evaluate overall Portfolio Heat.
        """
        total_open_risk_inr = 0.0
        total_invested = 0.0
        sector_counts: Dict[str, int] = {}

        for h in holdings:
            total_invested += float(h.total_invested)
            sec = h.sector or "Diversified"
            sector_counts[sec] = sector_counts.get(sec, 0) + 1

            # Determine open risk per holding:
            # If current_price > buy_price and trailing stop is at or above breakeven, open risk is 0 (risk-free!)
            sl_price = h.levels.stop_loss if (h.levels and h.levels.stop_loss) else (h.buy_price * 0.96)
            
            # Check if staged exit is active with trailing stop
            if h.staged_exit_plan and h.staged_exit_plan.trailing_stop_price:
                sl_price = h.staged_exit_plan.trailing_stop_price

            if sl_price and sl_price < h.buy_price:
                risk_per_share = max(0.0, h.buy_price - sl_price)
                holding_risk = risk_per_share * h.quantity
                total_open_risk_inr += holding_risk
            elif sl_price and sl_price >= h.buy_price:
                # Risk is locked in or eliminated (breakeven)
                total_open_risk_inr += 0.0

        portfolio_heat_pct = round((total_open_risk_inr / (account_capital or 1.0)) * 100.0, 2)
        available_budget_pct = max(0.0, round(max_allowed_heat_pct - portfolio_heat_pct, 2))

        # Check correlated sector concentration
        correlated_warnings = []
        for sec, count in sector_counts.items():
            if count >= 3:
                correlated_warnings.append(f"High Sector Correlation: {count} active positions in {sec} sector simultaneously.")

        # Determine heat status
        if portfolio_heat_pct > max_allowed_heat_pct:
            heat_status = "DANGEROUS_OVEREXPOSURE"
            note = f"ALERT: Total open portfolio risk ({portfolio_heat_pct}%) exceeds max safe limit ({max_allowed_heat_pct}%). Do not open new positions until stops are trailed to breakeven."
        elif portfolio_heat_pct >= 4.0:
            heat_status = "MODERATE"
            note = f"Portfolio risk is moderate ({portfolio_heat_pct}%). You have {available_budget_pct}% risk budget remaining."
        else:
            heat_status = "OPTIMAL"
            note = f"Portfolio heat is optimal ({portfolio_heat_pct}%). Safe risk capacity available for new setups."

        return PortfolioHeatSummary(
            total_account_equity=account_capital,
            total_invested_capital=round(total_invested, 2),
            total_open_risk_inr=round(total_open_risk_inr, 2),
            portfolio_heat_pct=portfolio_heat_pct,
            heat_status=heat_status,
            max_recommended_heat_pct=max_allowed_heat_pct,
            available_risk_budget_pct=available_budget_pct,
            correlated_sector_warnings=correlated_warnings,
            risk_summary_note=note
        )

risk_manager = RiskManager()
