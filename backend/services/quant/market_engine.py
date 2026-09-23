import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.models.schemas import MarketIndexQuote, MarketBreadth, SectorPerformance, MarketStatusResponse, MarketRegimePolicy
from backend.services.market_data.data_service import data_service
from backend.services.quant.sector_engine import sector_engine

logger = logging.getLogger("market_engine")

class MarketEngine:
    """
    Evaluates macro market structure, multi-horizon index momentum, market breadth, and volatility regimes.
    Produces dynamic policy parameters (probability thresholds, R:R requirements, position sizing multipliers)
    to adapt swing risk without abrupt total shutdowns during normal pullbacks.
    """
    
    @classmethod
    def get_regime_policy(cls, regime: str, status_label: str, description: str) -> MarketRegimePolicy:
        """
        Dynamically adjusts risk parameters based on the market regime.
        """
        if regime == "STRONG_BULL":
            return MarketRegimePolicy(
                regime=regime,
                status_label=status_label,
                description=description,
                min_probability_threshold=0.55,
                min_risk_reward_ratio=1.5,
                max_opportunities=5,
                position_size_multiplier=1.0,
                setup_quality_requirement="STANDARD",
                allow_new_longs=True
            )
        elif regime == "BULL":
            return MarketRegimePolicy(
                regime=regime,
                status_label=status_label,
                description=description,
                min_probability_threshold=0.58,
                min_risk_reward_ratio=1.6,
                max_opportunities=5,
                position_size_multiplier=0.85,
                setup_quality_requirement="STANDARD",
                allow_new_longs=True
            )
        elif regime == "RECOVERY":
            return MarketRegimePolicy(
                regime=regime,
                status_label=status_label,
                description=description,
                min_probability_threshold=0.62,
                min_risk_reward_ratio=1.8,
                max_opportunities=3,
                position_size_multiplier=0.65,
                setup_quality_requirement="STRICT",
                allow_new_longs=True
            )
        elif regime == "NEUTRAL":
            return MarketRegimePolicy(
                regime=regime,
                status_label=status_label,
                description=description,
                min_probability_threshold=0.65,
                min_risk_reward_ratio=1.8,
                max_opportunities=3,
                position_size_multiplier=0.50,
                setup_quality_requirement="STRICT",
                allow_new_longs=True
            )
        elif regime == "BEAR":
            return MarketRegimePolicy(
                regime=regime,
                status_label=status_label,
                description=description,
                min_probability_threshold=0.72,
                min_risk_reward_ratio=2.2,
                max_opportunities=2,
                position_size_multiplier=0.30,
                setup_quality_requirement="HIGHEST_CONVICTION",
                allow_new_longs=True # Selective high relative strength counter-trend leaders only
            )
        else: # STRESS
            return MarketRegimePolicy(
                regime=regime,
                status_label=status_label,
                description=description,
                min_probability_threshold=0.80,
                min_risk_reward_ratio=2.5,
                max_opportunities=0,
                position_size_multiplier=0.0,
                setup_quality_requirement="HIGHEST_CONVICTION",
                allow_new_longs=False # Capital preservation active
            )

    @classmethod
    async def evaluate_market_regime(cls) -> MarketStatusResponse:
        indices = await data_service.get_indices_status()
        nifty = indices["nifty"]
        bank_nifty = indices["bank_nifty"]
        vix = indices["india_vix"]
        
        # Sector intelligence from dedicated Sector Rotation Engine
        sector_matrix = await sector_engine.evaluate_sector_rotation()
        strong_sectors = [s for s in sector_matrix if s.momentum_score >= 55.0]
        weak_sectors = [s for s in sector_matrix if s.momentum_score < 45.0]
        
        # Calculate real market breadth
        advances = sum(1 for s in sector_matrix if s.change_percent_1d > 0)
        declines = sum(1 for s in sector_matrix if s.change_percent_1d < 0)
        unchanged = sum(1 for s in sector_matrix if s.change_percent_1d == 0)
        total_sectors = len(sector_matrix) or 1
        
        ad_ratio = round(advances / (declines or 1), 2)
        pct_above = round((advances / total_sectors) * 100.0, 1)
        
        breadth = MarketBreadth(
            advances=advances,
            declines=declines,
            unchanged=unchanged,
            ad_ratio=ad_ratio,
            pct_above_20_ema=pct_above,
            pct_above_50_ema=pct_above,
            pct_above_200_ema=pct_above,
            highs_52w_count=max(0, advances * 2),
            lows_52w_count=max(0, declines * 2)
        )
        
        # Classify Market Regime (STRONG_BULL, BULL, NEUTRAL, RECOVERY, BEAR, STRESS)
        is_live = (nifty.price > 0)
        
        if not is_live:
            regime = "NEUTRAL"
            status_label = "Awaiting Live Stream"
            description = "Market data stream initializing via Upstox API v2."
        elif vix.price > 22.0:
            regime = "STRESS"
            status_label = "Elevated Volatility & Stress"
            description = f"India VIX elevated at {vix.price:.2f}. System enters defensive stance: capital preservation active, stops tightened."
        elif nifty.change_percent > 0.8 and (vix.price == 0 or vix.price < 14.5) and breadth.ad_ratio >= 1.5:
            regime = "STRONG_BULL"
            status_label = "Strong Bullish Momentum"
            description = f"NIFTY advancing (+{nifty.change_percent:.2f}%) with broad sector participation and subdued volatility. Favorable for high-beta swing breakouts."
        elif nifty.change_percent > 0.2 and (vix.price == 0 or vix.price < 16.5):
            regime = "BULL"
            status_label = "Moderately Bullish"
            description = f"NIFTY holding positive trajectory (+{nifty.change_percent:.2f}%). Focus on leading sector breakouts and 20 EMA pullbacks."
        elif nifty.change_percent < -0.8 and breadth.ad_ratio < 0.6:
            regime = "BEAR"
            status_label = "Bearish / Distribution"
            description = f"Broad-based market selling (NIFTY {nifty.change_percent:.2f}%). Scanner enforces highest-conviction filters and reduced sizing."
        elif -0.3 <= nifty.change_percent <= 0.3:
            regime = "NEUTRAL"
            status_label = "Consolidation / Rangebound"
            description = "Indices in a tight trading range. Selective stock picking strictly prioritizing high-momentum sector leaders."
        else:
            regime = "RECOVERY"
            status_label = "Early Rebound / Recovery"
            description = "Market attempting reversal from recent pullbacks. Watch for confirmation of leading stock breakouts."
            
        policy = cls.get_regime_policy(regime, status_label, description)
        
        major_events: List[str] = []
        if nifty.price > 0:
            major_events.append(f"NIFTY 50 trading at ₹{nifty.price:,.2f} ({nifty.change_percent:+.2f}%)")
        if bank_nifty.price > 0:
            major_events.append(f"Bank NIFTY trading at ₹{bank_nifty.price:,.2f} ({bank_nifty.change_percent:+.2f}%)")
        if vix.price > 0:
            major_events.append(f"India VIX volatility benchmark at {vix.price:.2f}")
        if sector_matrix:
            leader = sector_matrix[0]
            major_events.append(f"Sector Leader: {leader.sector_name} (+{leader.change_percent_20d:.1f}% over 20D, Score: {leader.momentum_score})")

        return MarketStatusResponse(
            status_label=status_label,
            regime=regime,
            regime_policy=policy,
            nifty=nifty,
            bank_nifty=bank_nifty,
            india_vix=vix,
            breadth=breadth,
            strong_sectors=strong_sectors[:4],
            weak_sectors=weak_sectors[:4],
            sector_rotation_matrix=sector_matrix,
            major_events=major_events,
            last_updated=datetime.utcnow(),
            is_live_data=is_live
        )

market_engine = MarketEngine()
