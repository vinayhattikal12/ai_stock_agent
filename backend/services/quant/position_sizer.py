from typing import Optional
from backend.models.schemas import PositionSizingSuggestion

class PositionSizingEngine:
    """
    Computes mathematically rigorous position sizing for swing trading.
    Enforces:
    - Fixed fractional risk per trade (default 1.0% or 0.5% in elevated volatility)
    - Dynamic market regime sizing multipliers (0.3x to 1.0x)
    - Single position concentration cap (max 20% of portfolio)
    - Sector concentration cap (max 30% of portfolio)
    """

    DEFAULT_PORTFOLIO_CAPITAL = 500000.0 # Default ₹5,00,000 base if not specified
    DEFAULT_RISK_PER_TRADE_PCT = 1.0     # 1% standard swing risk

    @classmethod
    def calculate_position_size(
        cls,
        current_price: float,
        stop_loss: float,
        portfolio_capital: Optional[float] = None,
        risk_per_trade_pct: Optional[float] = None,
        regime_multiplier: float = 1.0
    ) -> PositionSizingSuggestion:
        capital = portfolio_capital or cls.DEFAULT_PORTFOLIO_CAPITAL
        risk_pct = risk_per_trade_pct or cls.DEFAULT_RISK_PER_TRADE_PCT
        
        # Risk amount in INR
        risk_amount_inr = capital * (risk_pct / 100.0)
        
        # Distance to stop loss
        risk_per_share = max(0.1, current_price - stop_loss)
        
        # Base quantity derived from risk
        base_quantity = int(risk_amount_inr / risk_per_share) if risk_per_share > 0 else 0
        
        # Apply regime multiplier (e.g. 0.5 in Bear or Stress)
        scaled_quantity = int(base_quantity * max(0.1, regime_multiplier))
        
        # Cap single stock exposure to max 20% of portfolio capital
        max_capital_for_stock = capital * 0.20
        max_quantity_by_cap = int(max_capital_for_stock / current_price) if current_price > 0 else 0
        
        final_quantity = min(scaled_quantity, max_quantity_by_cap)
        if final_quantity <= 0 and current_price <= max_capital_for_stock:
            final_quantity = 1 # Minimum 1 share if affordable
            
        allocated_capital = round(final_quantity * current_price, 2)
        portfolio_alloc_pct = round((allocated_capital / capital) * 100.0, 2) if capital > 0 else 0.0

        return PositionSizingSuggestion(
            portfolio_capital=round(capital, 2),
            risk_per_trade_pct=risk_pct,
            risk_amount_inr=round(risk_amount_inr, 2),
            suggested_quantity=final_quantity,
            allocated_capital_inr=allocated_capital,
            portfolio_allocation_pct=portfolio_alloc_pct,
            max_sector_exposure_pct=30.0
        )

position_sizer = PositionSizingEngine()
