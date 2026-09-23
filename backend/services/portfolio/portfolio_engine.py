import logging
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from backend.models.database import DBHolding
from backend.models.schemas import (
    HoldingAnalysis, PortfolioSummaryResponse, HoldingCreate, TradeLevels, FactorScores, Candle
)
from backend.services.market_data.data_service import data_service
from backend.services.market_data.data_quality import data_quality_gate
from backend.services.quant.technical_engine import TechnicalEngine
from backend.services.quant.volume_engine import volume_engine
from backend.services.quant.factor_engine import factor_engine
from backend.services.quant.target_stop_engine import TargetStopEngine
from backend.services.quant.relative_strength import RelativeStrengthEngine
from backend.services.quant.market_engine import market_engine
from backend.services.portfolio.thesis_engine import thesis_engine
from backend.services.ml.feature_pipeline import FeaturePipeline
from backend.services.ml.classifier import ml_classifier

logger = logging.getLogger("portfolio_engine")

class PortfolioEngine:
    """
    Analyzes user-entered stock investments using real Upstox market data.
    Evaluates thesis health, dynamic support/resistance levels, factor ranks, and quantitative swing actions.
    Never injects fake holdings.
    """
    
    @classmethod
    async def analyze_holding(
        cls, 
        holding: DBHolding, 
        market_regime: str = "BULL",
        nifty_candles: Optional[List[Candle]] = None,
        sectors_data: Optional[List[Dict[str, Any]]] = None,
        candles: Optional[List[Candle]] = None
    ) -> HoldingAnalysis:
        symbol = holding.symbol.upper().strip()
        universe = data_service.get_supported_universe()
        match = next((s for s in universe if s["symbol"] == symbol), None)
        company_name = match["name"] if match else f"{symbol} Ltd"
        sector = match["sector"] if match else "Diversified"
        
        # 1. Ingest Canonical MarketDataSnapshot & Verified Clean Candles (400-day lookback)
        snapshot, clean_candles, dq_report = await data_service.get_canonical_snapshot(symbol)

        if nifty_candles is None:
            nifty_raw = await data_service.get_historical_candles_cached("NIFTY 50", interval="day", days=400)
            nifty_dq = data_quality_gate.validate_daily_candles(nifty_raw, symbol="NIFTY 50", min_required_bars=30)
            nifty_candles = nifty_dq.clean_candles if nifty_dq.is_valid else []

        indicators = TechnicalEngine.evaluate_indicators(clean_candles)
        vol_metrics = volume_engine.calculate_volume_metrics(clean_candles)
        
        # Real quote / current price from canonical snapshot
        current_price = snapshot.quote_price if (snapshot and snapshot.quote_price) else (
            clean_candles[-1].close if clean_candles else float(holding.buy_price)
        )
        
        # Real P&L Calculation
        total_invested = round(float(holding.buy_price) * holding.quantity, 2)
        current_val = round(current_price * holding.quantity, 2)
        pnl = round(current_val - total_invested, 2)
        pnl_pct = round((pnl / total_invested * 100.0), 2) if total_invested > 0 else 0.0
        
        # Relative Strength
        rs_20d = RelativeStrengthEngine.calculate_excess_return(clean_candles, nifty_candles, 20) if (clean_candles and nifty_candles) else None
        
        # Explicit Rupee Target and Stop Levels
        levels = TargetStopEngine.calculate_levels(clean_candles, indicators)
        
        # ML Probabilities & Features
        features = FeaturePipeline.extract_features(
            candles=clean_candles,
            indicators=indicators,
            rs_20d=rs_20d,
            mansfield_rs=rs_20d,
            sector_momentum=50.0,
            candle_score=50.0,
            rvol=vol_metrics.rvol_20d,
            market_regime=market_regime
        ) if clean_candles else {}
        ml_prob = ml_classifier.predict_probabilities(features)
        
        # Factor scores
        factor_scores = factor_engine.calculate_factors(
            candles=clean_candles,
            indicators=indicators,
            volume_metrics=vol_metrics,
            mansfield_rs=rs_20d,
            sector_momentum=50.0
        )
        
        # Sector trend
        if sectors_data is None:
            sectors_data = await data_service.get_sector_indices_data()
        sec_match = next((s for s in sectors_data if sector.lower() in s["name"].lower()), None)
        sector_trend = sec_match["trend"] if sec_match else "NEUTRAL"
        
        # Thesis evaluation
        thesis_status, thesis_points = thesis_engine.evaluate_thesis(
            clean_candles, indicators, float(holding.buy_price), rs_20d or 0.0, sector_trend
        ) if clean_candles else ("STABLE", ["Awaiting verified market session data feed."])
        
        # Dynamic Action Classifier with Pyramiding Guardrails & Staged Exits
        from backend.services.quant.staged_exit_engine import staged_exit_engine
        from backend.services.quant.risk_manager import risk_manager

        staged_plan = staged_exit_engine.evaluate_staged_exit(
            buy_price=float(holding.buy_price),
            current_price=current_price,
            purchase_date=parsed_purchase_date,
            levels=levels,
            indicators=indicators,
            candles=clean_candles
        )

        p_t1 = ml_prob.p_t1_before_sl
        sl_price = levels.stop_loss
        t1_price = levels.target_1
        t2_price = levels.target_2

        # Pyramiding guardrail: Can only "BUY MORE" if price is pulling back near 20 EMA / entry base
        ema_20 = indicators.ema_20 if (indicators and indicators.ema_20) else float(holding.buy_price)
        is_pullback_entry_zone = (current_price <= ema_20 * 1.025) or (current_price <= float(holding.buy_price) * 1.03)

        if not clean_candles:
            signal = "INSUFFICIENT DATA"
        elif thesis_status == "BROKEN" or staged_plan.current_stage == "STOP_LOSS_EXIT" or (sl_price is not None and current_price <= sl_price):
            signal = "SELL"
        elif staged_plan.current_stage == "TIME_DECAY_EXIT_TRIGGERED":
            signal = "REDUCE"
        elif staged_plan.current_stage in ["T1_PROFIT_TAKEN_BREAKEVEN_ACTIVE", "T2_PROFIT_TAKEN_RUNNER_ACTIVE", "T3_COMPLETED"]:
            signal = "REDUCE"
        elif thesis_status == "WEAKENING" and pnl_pct < -2.5:
            signal = "REDUCE"
        elif thesis_status == "STRENGTHENING" and p_t1 is not None and p_t1 >= 0.70 and is_pullback_entry_zone and (t1_price is None or current_price <= t1_price * 0.96):
            signal = "BUY MORE"
        elif thesis_status == "WEAKENING":
            signal = "WATCH"
        else:
            signal = "HOLD"
            
        risks = []
        if sl_price is not None:
            risks.append(f"Protective Stop Loss Price: ₹{sl_price:,.2f} ({levels.stop_reason})")
        if t1_price is not None:
            risks.append(f"Overhead Target 1 Price: ₹{t1_price:,.2f}")
        if staged_plan.is_risk_free:
            risks.append("Risk Status: 100% Risk-Free (Trailing Stop at Breakeven)")
        
        invalidation_triggers = []
        if staged_plan.trailing_stop_price:
            invalidation_triggers.append(f"Daily close below active trailing stop at ₹{staged_plan.trailing_stop_price:,.2f}")
        invalidation_triggers.append("Mansfield RS declining below zero on above-average volume")

        time_decay_warning = staged_plan.time_decay_guidance

        if clean_candles and len(clean_candles) >= 5:
            vol_20 = sum(c.volume for c in clean_candles[-20:]) / min(len(clean_candles), 20)
            vol_ratio = round(clean_candles[-1].volume / (vol_20 or 1), 2)
            volume_desc = f"Active ({vol_ratio}× 20D average volume)" if vol_ratio >= 1.0 else f"Light volume ({vol_ratio}× avg)"
        else:
            volume_desc = "Awaiting volume feed"

        exp_days_str = f"{ml_prob.expected_days_min}–{ml_prob.expected_days_max} trading days" if ml_prob.expected_days_min else "5–10 trading days"

        # Risk Management Metrics
        risk_metrics = risk_manager.calculate_position_risk(
            entry_price=float(holding.buy_price),
            stop_loss_price=sl_price or (float(holding.buy_price) * 0.965),
            target_1_price=t1_price,
            win_probability=p_t1
        )

        return HoldingAnalysis(
            id=holding.id or 0,
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            quantity=int(holding.quantity),
            buy_price=float(holding.buy_price),
            purchase_date=parsed_purchase_date,
            current_price=current_price,
            total_invested=total_invested,
            current_value=current_val,
            unrealized_pnl=pnl,
            unrealized_pnl_pct=pnl_pct,
            signal=signal,
            thesis_status=thesis_status,
            thesis_points=thesis_points,
            invalidation_triggers=invalidation_triggers,
            time_decay_warning=time_decay_warning,
            holding_days_elapsed=holding_days,
            expected_holding_period=exp_days_str,
            risks=risks,
            levels=levels,
            ml_probability=ml_prob,
            staged_exit_plan=staged_plan,
            risk_metrics=risk_metrics,
            factor_scores=factor_scores,
            relative_strength_20d=rs_20d,
            volume_condition=volume_desc,
            last_evaluated_at=datetime.utcnow()
        )

    @classmethod
    async def get_portfolio_summary(cls, db: Session) -> PortfolioSummaryResponse:
        from backend.services.quant.risk_manager import risk_manager
        holdings = db.query(DBHolding).all()
        
        if not holdings:
            return PortfolioSummaryResponse(
                total_invested=0.0,
                current_value=0.0,
                total_pnl=0.0,
                total_pnl_pct=0.0,
                holdings_count=0,
                strengthening_count=0,
                stable_count=0,
                weakening_count=0,
                broken_count=0,
                sector_exposure_breakdown={},
                holdings=[],
                portfolio_heat=risk_manager.evaluate_portfolio_heat([]),
                what_changed_feed=["No active holdings in personal portfolio. Add your stock positions to begin continuous thesis tracking."],
                last_updated=datetime.utcnow()
            )
            
        market_status = await market_engine.evaluate_market_regime()
        nifty_candles = await data_service.get_historical_candles_cached("NIFTY 50", interval="day", days=120)
        sectors = await data_service.get_sector_indices_data()
        
        holding_symbols = [h.symbol.upper().strip() for h in holdings]
        candles_map = await data_service.get_multiple_candles_parallel(holding_symbols, interval="day", days=180, concurrency=10)
        
        holding_analyses: List[HoldingAnalysis] = []
        what_changed: List[str] = []
        
        for h in holdings:
            try:
                sym = h.symbol.upper().strip()
                h_candles = candles_map.get(sym) or []
                analysis = await cls.analyze_holding(
                    h, 
                    market_regime=market_status.regime,
                    nifty_candles=nifty_candles,
                    sectors_data=sectors,
                    candles=h_candles
                )
                holding_analyses.append(analysis)
                
                if analysis.thesis_status == "STRENGTHENING":
                    rs_str = f"+{analysis.relative_strength_20d:.1f}%" if analysis.relative_strength_20d is not None else "positive"
                    what_changed.append(f"{analysis.symbol}: Thesis strengthened with {rs_str} relative strength vs NIFTY 50.")
                elif analysis.thesis_status == "BROKEN":
                    what_changed.append(f"ALERT: {analysis.symbol} thesis is broken. Review risk/exit.")
                elif analysis.thesis_status == "WEAKENING":
                    what_changed.append(f"{analysis.symbol}: Momentum decelerating near key benchmark moving averages.")
            except Exception as e:
                logger.error(f"Error analyzing holding {h.symbol}: {e}")
                
        total_invested = round(sum(h.total_invested for h in holding_analyses), 2)
        current_value = round(sum(h.current_value for h in holding_analyses), 2)
        total_pnl = round(current_value - total_invested, 2)
        total_pnl_pct = round((total_pnl / total_invested * 100.0), 2) if total_invested > 0 else 0.0
        
        strengthening = sum(1 for h in holding_analyses if h.thesis_status == "STRENGTHENING")
        stable = sum(1 for h in holding_analyses if h.thesis_status == "STABLE")
        weakening = sum(1 for h in holding_analyses if h.thesis_status == "WEAKENING")
        broken = sum(1 for h in holding_analyses if h.thesis_status == "BROKEN")

        # Sector exposure breakdown
        sector_exp: Dict[str, float] = {}
        for h in holding_analyses:
            sec = h.sector or "Diversified"
            sector_exp[sec] = sector_exp.get(sec, 0.0) + h.current_value

        portfolio_heat_summary = risk_manager.evaluate_portfolio_heat(holding_analyses)

        return PortfolioSummaryResponse(
            total_invested=total_invested,
            current_value=current_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            holdings_count=len(holding_analyses),
            strengthening_count=strengthening,
            stable_count=stable,
            weakening_count=weakening,
            broken_count=broken,
            sector_exposure_breakdown=sector_exp,
            holdings=holding_analyses,
            portfolio_heat=portfolio_heat_summary,
            what_changed_feed=what_changed or ["Holdings are tracking steadily within quantitative risk parameters."],
            last_updated=datetime.utcnow()
        )

portfolio_engine = PortfolioEngine()
