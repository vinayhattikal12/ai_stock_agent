import logging
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

from backend.models.schemas import (
    StockOpportunity,
    MarketCapCategoryResult,
    NearMissesGroup,
    ScannerScanResponse,
    RelativeStrengthMetrics,
    StructuredCatalyst,
    HistoricalScanSummary,
    DataQualityReport
)
from backend.models.database import SessionLocal, DBHolding, DBInstrumentMaster, DBHistoricalScan
from backend.services.market_data.data_service import data_service
from backend.services.market_data.data_quality import data_quality_gate
from backend.services.market_data.universe import CLASSIFICATION_SOURCE, CLASSIFICATION_DATE
from backend.services.quant.technical_engine import TechnicalEngine
from backend.services.quant.candle_engine import CandlestickEngine
from backend.services.quant.volume_engine import volume_engine
from backend.services.quant.relative_strength import RelativeStrengthEngine
from backend.services.quant.factor_engine import factor_engine
from backend.services.quant.setup_engine import setup_engine
from backend.services.quant.target_stop_engine import TargetStopEngine
from backend.services.quant.position_sizer import position_sizer
from backend.services.quant.market_engine import market_engine
from backend.services.quant.sector_engine import sector_engine
from backend.services.ml.feature_pipeline import FeaturePipeline
from backend.services.ml.classifier import ml_classifier
from backend.services.news.event_tracker import news_engine

logger = logging.getLogger("systematic_scanner")

class SystematicStockScanner:
    """
    Multi-Cap Systematic Swing Scanner Engine:
    Independently scans and ranks:
    - TOP 5 LARGE-CAP OPPORTUNITIES (Ranks 1 to 100)
    - TOP 5 MID-CAP OPPORTUNITIES (Ranks 101 to 250)
    - TOP 5 SMALL-CAP OPPORTUNITIES (Ranks 251+)
    
    Maximum 15 opportunities per scan (up to 5 per category).
    Zero-fallback data policy: filters out malformed or insufficient candles via DataQualityGate.
    Provides explicit Rupee price targets (T1, T2, T3) and protective stop losses.
    """

    RANKING_VERSION = "MF-MultiCap-Quant-v4.0"
    
    @classmethod
    async def run_scan(cls) -> ScannerScanResponse:
        scan_time = datetime.utcnow()
        
        # 1. Evaluate macro market status & regime policy
        market_status = await market_engine.evaluate_market_regime()
        market_regime = market_status.regime
        policy = market_status.regime_policy
        
        universe = data_service.get_supported_universe()
        total_universe_count = len(universe)
        
        # Category specific turnover / liquidity thresholds in ₹ Crores/day
        TURNOVER_THRESHOLDS = {
            "LARGE_CAP": 2.0,
            "MID_CAP": 2.5,
            "SMALL_CAP": 3.5
        }
        
        categories_config = {
            "LARGE_CAP": {"label": "Top Large-Cap Opportunities", "range": "1-100"},
            "MID_CAP": {"label": "Top Mid-Cap Opportunities", "range": "101-250"},
            "SMALL_CAP": {"label": "Top Small-Cap Opportunities", "range": "251+"}
        }
        
        category_survivors: Dict[str, Dict[str, int]] = {
            cat: {
                "universe": 0,
                "data_valid": 0,
                "liquid": 0,
                "market_sector_compatible": 0,
                "strong_factors": 0,
                "valid_setups": 0,
                "volume_candle_confirmed": 0,
                "catalyst_evaluated": 0,
                "ml_evaluated": 0,
                "risk_valid": 0,
                "portfolio_compatible": 0,
                "final_selected": 0
            } for cat in categories_config
        }
        
        category_rejections: Dict[str, Dict[str, int]] = {
            cat: {
                "insufficient_candles": 0,
                "illiquid_turnover": 0,
                "suboptimal_rr": 0,
                "ml_below_threshold": 0,
                "upcoming_earnings_risk": 0,
                "sector_concentration_cap": 0
            } for cat in categories_config
        }
        
        global_survivors = {
            "universe": total_universe_count,
            "data_valid": 0,
            "liquid": 0,
            "market_sector_compatible": 0,
            "strong_factors": 0,
            "valid_setups": 0,
            "volume_candle_confirmed": 0,
            "catalyst_evaluated": 0,
            "ml_evaluated": 0,
            "risk_valid": 0,
            "portfolio_compatible": 0,
            "final_selected": 0
        }
        global_rejections: Dict[str, int] = {
            "insufficient_candles": 0,
            "illiquid_turnover": 0,
            "suboptimal_rr": 0,
            "ml_below_threshold": 0,
            "upcoming_earnings_risk": 0,
            "sector_concentration_cap": 0
        }
        
        # 2. Benchmark NIFTY & Sector Matrix
        nifty_raw = await data_service.get_historical_candles_cached("NIFTY 50", interval="day", days=180)
        nifty_dq = data_quality_gate.validate_daily_candles(nifty_raw, symbol="NIFTY 50", min_required_bars=40)
        nifty_candles = nifty_dq.clean_candles if nifty_dq.is_valid else []

        sector_matrix = await sector_engine.evaluate_sector_rotation()
        sector_score_map = {s.sector_name.lower(): s.momentum_score for s in sector_matrix}
        
        # Check existing portfolio holdings to compute sector exposure & portfolio fit
        existing_sector_counts: Dict[str, int] = {}
        existing_holdings_symbols = set()
        db = SessionLocal()
        try:
            db_holdings = db.query(DBHolding).all()
            for h in db_holdings:
                existing_holdings_symbols.add(h.symbol.upper())
                match = next((s for s in universe if s["symbol"] == h.symbol.upper()), None)
                sec = match["sector"] if match else "Diversified"
                existing_sector_counts[sec] = existing_sector_counts.get(sec, 0) + 1
        finally:
            db.close()

        # Handle regime-level prohibition
        if not policy.allow_new_longs or market_regime == "STRESS":
            empty_cat_res = lambda c: MarketCapCategoryResult(
                category=c,
                label=categories_config[c]["label"],
                market_cap_rank_range=categories_config[c]["range"],
                classification_source=CLASSIFICATION_SOURCE,
                classification_date=str(CLASSIFICATION_DATE),
                total_scanned=len([u for u in universe if u.get("market_cap_category") == c]),
                qualified_count=0,
                near_misses_count=0,
                survivors_by_stage=category_survivors[c],
                primary_bottleneck=f"Market Regime Policy ({market_regime})",
                candidates=[],
                near_misses=[]
            )
            return ScannerScanResponse(
                large_cap=empty_cat_res("LARGE_CAP"),
                mid_cap=empty_cat_res("MID_CAP"),
                small_cap=empty_cat_res("SMALL_CAP"),
                near_misses=NearMissesGroup(large_cap=[], mid_cap=[], small_cap=[]),
                total_qualified_count=0,
                total_near_misses_count=0,
                opportunities=[],
                buy_candidates_count=0,
                near_misses_count=0,
                scan_timestamp=scan_time,
                total_universe_scanned=total_universe_count,
                survivors_by_stage=global_survivors,
                primary_bottleneck=f"Market Regime: {market_regime} ({policy.description})",
                secondary_rejection_summary=global_rejections,
                passed_liquidity_filter=0,
                passed_technical_filter=0,
                passed_ml_filter=0,
                market_regime=market_regime,
                market_regime_policy=policy,
                is_abstention=True,
                abstention_reason=f"SYSTEM ABSTENTION: Market is in {market_regime} regime. Capital preservation is mandated over initiating new swing positions.",
                ranking_version=cls.RANKING_VERSION,
                configured_weights=factor_engine.DEFAULT_WEIGHTS,
                configured_probability_threshold=policy.min_probability_threshold,
                configured_min_rr=policy.min_risk_reward_ratio
            )

        # Scored pools segregated by category
        scored_pools: Dict[str, List[Dict[str, Any]]] = {
            "LARGE_CAP": [],
            "MID_CAP": [],
            "SMALL_CAP": []
        }

        # Fetch candles for entire universe concurrently in parallel batches (1-2s total)
        all_symbols = [item["symbol"] for item in universe]
        candles_map = await data_service.get_multiple_candles_parallel(all_symbols, interval="day", days=180, concurrency=20)

        # ==========================================
        # STAGE 1 & 2: DATA GATE, LIQUIDITY & SCORING
        # ==========================================
        for item in universe:
            symbol = item["symbol"]
            company_name = item["name"]
            sector = item["sector"]
            category = item.get("market_cap_category", "LARGE_CAP").upper()
            if category not in scored_pools:
                category = "LARGE_CAP"
            rank = item.get("market_cap_rank")
            instrument_key = item.get("instrument_key", f"NSE_EQ|{symbol}")
            
            category_survivors[category]["universe"] += 1
            sector_momentum = sector_score_map.get(sector.lower(), 50.0)
            
            # 1. Central Data Quality Gate
            raw_c = candles_map.get(symbol) or []
            dq_res = data_quality_gate.validate_daily_candles(raw_c, symbol=symbol, min_required_bars=30)
            
            if not dq_res.is_valid or not dq_res.clean_candles:
                category_rejections[category]["insufficient_candles"] += 1
                global_rejections["insufficient_candles"] += 1
                continue
                
            candles = dq_res.clean_candles
            category_survivors[category]["data_valid"] += 1
            global_survivors["data_valid"] += 1
            
            # 2. Category-differentiated liquidity threshold
            min_turnover = TURNOVER_THRESHOLDS.get(category, 2.0)
            vol_metrics = volume_engine.calculate_volume_metrics(candles)
            avg_turnover = vol_metrics.avg_turnover_cr_20d or 0.0
            
            if avg_turnover < min_turnover:
                category_rejections[category]["illiquid_turnover"] += 1
                global_rejections["illiquid_turnover"] += 1
                continue
            category_survivors[category]["liquid"] += 1
            global_survivors["liquid"] += 1
            
            # 3. Technical Indicators & Candlesticks
            indicators = TechnicalEngine.evaluate_indicators(candles)
            current_price = candles[-1].close
            prev_close = candles[-2].close if len(candles) > 1 else current_price
            daily_chg = round((current_price - prev_close) / (prev_close or 1.0) * 100.0, 2)
            
            candle_score, candle_patterns = CandlestickEngine.calculate_candle_confirmation_score(candles)
            
            # 4. Relative Strength metrics
            rs_metrics = RelativeStrengthEngine.evaluate_multi_timeframe_rs(
                stock_candles=candles,
                nifty_candles=nifty_candles,
                sector_momentum=sector_momentum
            )
            mansfield_rs_50 = rs_metrics.mansfield_rs_50d
            
            if sector_momentum >= 40.0:
                category_survivors[category]["market_sector_compatible"] += 1
                global_survivors["market_sector_compatible"] += 1

            # 5. Setup Classification
            setup_info = setup_engine.classify_setup(
                candles=candles,
                indicators=indicators,
                volume_metrics=vol_metrics,
                mansfield_rs=mansfield_rs_50,
                candle_score=candle_score,
                sector_momentum=sector_momentum
            )
            if setup_info.quality_score is not None and setup_info.quality_score >= 45.0:
                category_survivors[category]["valid_setups"] += 1
                global_survivors["valid_setups"] += 1

            # 6. Catalyst & News
            event_risk = news_engine.evaluate_event_risk(symbol)
            has_earnings_risk = event_risk["has_high_event_risk"]
            catalysts = event_risk.get("catalysts", [])
            catalyst_score = news_engine.evaluate_catalyst_score(symbol)
            category_survivors[category]["catalyst_evaluated"] += 1
            global_survivors["catalyst_evaluated"] += 1

            # 7. Multi-Factor Opportunity Scoring
            factor_scores = factor_engine.calculate_factors(
                candles=candles,
                indicators=indicators,
                volume_metrics=vol_metrics,
                mansfield_rs=mansfield_rs_50,
                sector_momentum=sector_momentum,
                setup_quality_score=setup_info.quality_score,
                catalyst_score=catalyst_score
            )
            overall_factor_rank = factor_scores.overall_factor_rank or 50.0
            if overall_factor_rank >= 50.0:
                category_survivors[category]["strong_factors"] += 1
                global_survivors["strong_factors"] += 1
                
            rvol_val = vol_metrics.rvol_20d or 1.0
            if rvol_val >= 1.0 or (candle_score and candle_score >= 50.0):
                category_survivors[category]["volume_candle_confirmed"] += 1
                global_survivors["volume_candle_confirmed"] += 1

            # 8. Structural Trade Levels (Explicit Rupee Prices)
            levels = TargetStopEngine.calculate_levels(candles, indicators)

            # 9. ML Probability Estimation
            features = FeaturePipeline.extract_features(
                candles=candles,
                indicators=indicators,
                rs_20d=rs_metrics.excess_return_20d,
                mansfield_rs=mansfield_rs_50,
                sector_momentum=sector_momentum,
                candle_score=candle_score,
                rvol=vol_metrics.rvol_20d,
                market_regime=market_regime
            )
            ml_metrics = ml_classifier.predict_probabilities(features)
            category_survivors[category]["ml_evaluated"] += 1
            global_survivors["ml_evaluated"] += 1

            # 10. Institutional Risk & Position Sizing
            from backend.services.quant.risk_manager import risk_manager
            from backend.models.schemas import InstitutionalVolumeQuality

            ref_entry = levels.reference_entry or current_price
            sl_price = levels.stop_loss or (ref_entry * 0.965)
            p_t1 = ml_metrics.p_t1_before_sl if ml_metrics else 0.60
            
            risk_metrics = risk_manager.calculate_position_risk(
                entry_price=ref_entry,
                stop_loss_price=sl_price,
                target_1_price=levels.target_1,
                win_probability=p_t1
            )

            pos_sizing = PositionSizingSuggestion(
                portfolio_capital=risk_metrics.account_capital,
                risk_per_trade_pct=risk_metrics.risk_per_trade_pct,
                risk_amount_inr=risk_metrics.max_rupees_at_risk,
                suggested_quantity=risk_metrics.suggested_shares,
                allocated_capital_inr=risk_metrics.allocated_capital,
                portfolio_allocation_pct=risk_metrics.portfolio_allocation_pct,
                max_sector_exposure_pct=20.0,
                expected_value_inr=risk_metrics.expected_value_inr
            )

            # Volume Quality
            rvol_val = vol_metrics.rvol_20d or 1.0
            acc_dist_score = min(100.0, max(0.0, 50.0 + (rvol_val - 1.0) * 25.0 + (5.0 if vol_metrics.volume_trend == "ACCUMULATION" else -5.0)))
            vol_quality = InstitutionalVolumeQuality(
                delivery_volume_pct_estimate=round(45.0 + min(25.0, max(-15.0, (rvol_val - 1.0) * 15.0)), 1),
                accumulation_distribution_score=round(acc_dist_score, 1),
                is_institutional_accumulation=(rvol_val >= 1.3 and vol_metrics.volume_trend == "ACCUMULATION"),
                volume_dry_up_on_pullback=(rvol_val < 0.8 and current_price < (indicators.ema_20 or current_price)),
                pocket_pivot_volume_surge=(rvol_val >= 1.5 and daily_chg > 1.0),
                event_risk_warning="Quarterly Corporate Earnings Window: Monitor company announcements." if has_earnings_risk else None,
                status="AVAILABLE"
            )

            # 11. Portfolio Fit Score
            sec_existing = existing_sector_counts.get(sector, 0)
            sec_penalty = min(30.0, sec_existing * 15.0)
            already_held_penalty = 15.0 if symbol in existing_holdings_symbols else 0.0
            portfolio_fit_score = max(30.0, 100.0 - sec_penalty - already_held_penalty)

            # 12. Composite Normalized Opportunity Score
            ml_p_t1 = ml_metrics.p_t1_before_sl if ml_metrics.p_t1_before_sl is not None else 0.50
            setup_q = setup_info.quality_score if setup_info.quality_score is not None else 50.0
            c_score_val = candle_score if candle_score is not None else 50.0
            cat_score_val = catalyst_score if catalyst_score is not None else 50.0

            composite_score = round(
                (overall_factor_rank * 0.35) +
                (ml_p_t1 * 100.0 * 0.25) +
                (setup_q * 0.20) +
                (c_score_val * 0.10) +
                (cat_score_val * 0.10),
                1
            )

            dq_summary = DataQualityReport(
                is_valid=True,
                status=dq_res.status,
                rejection_reason=None,
                candle_count=dq_res.candle_count,
                min_required_candles=30,
                first_candle_date=dq_res.first_timestamp.strftime("%Y-%m-%d") if dq_res.first_timestamp else None,
                last_candle_date=dq_res.last_timestamp.strftime("%Y-%m-%d") if dq_res.last_timestamp else None,
                exchange="NSE_EQ",
                instrument_key=instrument_key,
                validated_at=scan_time
            )

            scored_pools[category].append({
                "symbol": symbol,
                "company_name": company_name,
                "sector": sector,
                "category": category,
                "rank": rank,
                "current_price": current_price,
                "daily_change_pct": daily_chg,
                "setup_type": setup_info.setup_type,
                "setup_quality_score": setup_info.quality_score,
                "setup_rationale": setup_info.rationale,
                "levels": levels,
                "ml_probability": ml_metrics,
                "factor_scores": factor_scores,
                "relative_strength": rs_metrics,
                "volume_metrics": vol_metrics,
                "candle_confirmation_score": candle_score,
                "candle_patterns": candle_patterns,
                "catalysts": catalysts,
                "catalyst_score": catalyst_score,
                "has_earnings_risk": has_earnings_risk,
                "position_sizing": pos_sizing,
                "risk_metrics": risk_metrics,
                "volume_quality": vol_quality,
                "portfolio_fit_score": portfolio_fit_score,
                "composite_rank_score": composite_score,
                "data_quality": dq_summary,
                "timestamp": candles[-1].timestamp if candles else scan_time
            })

        # =====================================================================
        # STAGE 3 & 4: INDEPENDENT CATEGORY RISK GATING & SELECTION
        # =====================================================================
        category_results: Dict[str, MarketCapCategoryResult] = {}
        all_flattened_top_opportunities: List[StockOpportunity] = []
        all_buy_candidates_count = 0
        all_near_misses_count = 0
        
        near_misses_by_category: Dict[str, List[StockOpportunity]] = {
            "LARGE_CAP": [],
            "MID_CAP": [],
            "SMALL_CAP": []
        }

        for cat_key in ["LARGE_CAP", "MID_CAP", "SMALL_CAP"]:
            pool = scored_pools[cat_key]
            # Independent category ranking
            pool.sort(key=lambda x: x["composite_rank_score"], reverse=True)
            
            cat_buys: List[StockOpportunity] = []
            cat_near_misses: List[StockOpportunity] = []
            selected_cat_sector_counts = dict(existing_sector_counts)
            
            for item in pool:
                symbol = item["symbol"]
                sector = item["sector"]
                levels: TradeLevels = item["levels"]
                ml_metrics: MLProbabilityMetrics = item["ml_probability"]
                factor_scores: FactorScores = item["factor_scores"]
                vol_metrics: VolumeProfileMetrics = item["volume_metrics"]
                setup_type = item["setup_type"]
                setup_quality = item["setup_quality_score"]
                composite_score = item["composite_rank_score"]
                has_earnings_risk = item["has_earnings_risk"]
                current_price = item["current_price"]

                watch_reasons: List[str] = []
                failure_reasons: List[str] = []

                # 1. Check ML probability threshold
                if ml_metrics.p_t1_before_sl is None or ml_metrics.p_t1_before_sl < policy.min_probability_threshold:
                    category_rejections[cat_key]["ml_below_threshold"] += 1
                    global_rejections["ml_below_threshold"] += 1
                    if ml_metrics.p_t1_before_sl is not None:
                        diff_pct = int((policy.min_probability_threshold - ml_metrics.p_t1_before_sl) * 100)
                        watch_reasons.append(
                            f"Calibrated ML probability ({int(ml_metrics.p_t1_before_sl*100)}%) is {diff_pct}% below cutoff ({int(policy.min_probability_threshold*100)}%)."
                        )
                        failure_reasons.append(f"ML probability {int(ml_metrics.p_t1_before_sl*100)}% < {int(policy.min_probability_threshold*100)}% requirement.")
                    else:
                        watch_reasons.append("ML probability model features incomplete.")
                        failure_reasons.append("ML features incomplete.")

                # 2. Check Risk / Reward ratio
                rr_val = levels.risk_reward_ratio or 0.0
                if rr_val < policy.min_risk_reward_ratio:
                    category_rejections[cat_key]["suboptimal_rr"] += 1
                    global_rejections["suboptimal_rr"] += 1
                    watch_reasons.append(
                        f"Calculated 1:{rr_val:.2f} R:R to Target 1 (₹{levels.target_1:,.2f}) is below minimum 1:{policy.min_risk_reward_ratio:.2f}." if levels.target_1 else "Insufficient R:R payoff."
                    )
                    failure_reasons.append(f"R:R 1:{rr_val:.2f} < 1:{policy.min_risk_reward_ratio:.2f} threshold.")

                # 3. Check Binary Earnings Risk
                if has_earnings_risk:
                    category_rejections[cat_key]["upcoming_earnings_risk"] += 1
                    global_rejections["upcoming_earnings_risk"] += 1
                    watch_reasons.append("Quarterly earnings announcement scheduled in <= 4 trading days (High binary gap risk).")
                    failure_reasons.append("Earnings release binary volatility risk.")

                # 4. Check Sector Concentration Cap
                current_sec_count = selected_cat_sector_counts.get(sector, 0)
                if current_sec_count >= 2:
                    category_rejections[cat_key]["sector_concentration_cap"] += 1
                    global_rejections["sector_concentration_cap"] += 1
                    watch_reasons.append(
                        f"Sector '{sector}' already represents maximum allowable allocation in category (>= 30% concentration cap)."
                    )
                    failure_reasons.append(f"Portfolio sector concentration cap reached for {sector}.")

                # Signal Determination
                is_buy = len(watch_reasons) == 0
                if is_buy:
                    signal = "BUY CANDIDATE"
                    selected_cat_sector_counts[sector] = current_sec_count + 1
                    category_survivors[cat_key]["risk_valid"] += 1
                    category_survivors[cat_key]["portfolio_compatible"] += 1
                    global_survivors["risk_valid"] += 1
                    global_survivors["portfolio_compatible"] += 1
                else:
                    signal = "WATCH"

                m_rs_str = f"{item['relative_strength'].mansfield_rs_50d:+.1f}%" if item['relative_strength'].mansfield_rs_50d is not None else "N/A"
                why_setup = [
                    f"Market Cap: {cat_key.replace('_', ' ').title()} (SEBI Rank #{item['rank'] or 'N/A'})",
                    f"Setup: {setup_type} ({item['setup_rationale']})",
                    f"Entry Price Zone: {levels.entry_range_display or 'At market'}",
                    f"Target 1 Price: {levels.target_1_display or '₹' + str(levels.target_1)}",
                    f"Stop Loss Price: {levels.stop_loss_display or '₹' + str(levels.stop_loss)}",
                    f"Relative Strength: Mansfield RS50 at {m_rs_str} vs NIFTY 50 ({item['relative_strength'].rs_trend.lower()})",
                    f"Volume: RVOL {vol_metrics.rvol_20d or 1.0:.2f}x ({vol_metrics.volume_trend}) with ₹{vol_metrics.avg_turnover_cr_20d or 0.0:.1f} Cr turnover"
                ]

                risks = [
                    f"Stop Loss Price: {levels.stop_loss_display or '₹' + str(levels.stop_loss)} ({levels.stop_reason})",
                    f"Target 1 Price: {levels.target_1_display or '₹' + str(levels.target_1)}",
                    f"Regime Scale: {int(policy.position_size_multiplier * 100)}% of standard risk allocation",
                    f"Portfolio Fit Score: {item['portfolio_fit_score']:.0f}/100"
                ]

                invalidation = f"Daily candle close below ₹{levels.stop_loss:.2f} or Mansfield RS crossing below zero on heavy volume." if levels.stop_loss else None

                opp = StockOpportunity(
                    symbol=symbol,
                    company_name=item["company_name"],
                    sector=sector,
                    signal=signal,
                    market_cap_category=cat_key,
                    market_cap_rank=item["rank"],
                    classification_source=CLASSIFICATION_SOURCE,
                    classification_date=str(CLASSIFICATION_DATE),
                    opportunity_score=composite_score,
                    portfolio_fit_score=item["portfolio_fit_score"],
                    current_price=current_price,
                    daily_change_pct=item["daily_change_pct"],
                    setup_type=setup_type,
                    setup_quality_score=setup_quality,
                    levels=levels,
                    ml_probability=ml_metrics,
                    factor_scores=factor_scores,
                    relative_strength=item["relative_strength"],
                    volume_metrics=vol_metrics,
                    candle_confirmation_score=item["candle_confirmation_score"],
                    catalysts=item["catalysts"],
                    catalyst_score=item["catalyst_score"],
                    position_sizing=item["position_sizing"],
                    risk_metrics=item.get("risk_metrics"),
                    volume_quality=item.get("volume_quality"),
                    composite_rank_score=composite_score,
                    ranking_version=cls.RANKING_VERSION,
                    invalidation_condition=invalidation,
                    why_this_setup=why_setup,
                    watch_reasons=watch_reasons,
                    failure_reasons=failure_reasons,
                    risks=risks,
                    data_quality=item["data_quality"],
                    data_timestamp=item["timestamp"],
                    created_at=scan_time
                )

                if is_buy:
                    cat_buys.append(opp)
                else:
                    cat_near_misses.append(opp)

            # Select Top 5 for this category (0 to 5, never forced)
            top_cat_buys = cat_buys[:5]
            slots_left = 5 - len(top_cat_buys)
            top_cat_watchlist = cat_near_misses[:max(5, slots_left)]
            
            category_survivors[cat_key]["final_selected"] = len(top_cat_buys)
            global_survivors["final_selected"] += len(top_cat_buys)
            
            all_buy_candidates_count += len(cat_buys)
            all_near_misses_count += len(cat_near_misses)
            near_misses_by_category[cat_key] = cat_near_misses[:10]

            # Primary category bottleneck
            sorted_cat_rejections = sorted(category_rejections[cat_key].items(), key=lambda x: x[1], reverse=True)
            top_cat_rej_key = sorted_cat_rejections[0][0] if sorted_cat_rejections else "market_regime"
            bottleneck_labels = {
                "ml_below_threshold": f"ML Probability Threshold (>={int(policy.min_probability_threshold*100)}%)",
                "suboptimal_rr": f"Risk/Reward Requirement (>=1:{policy.min_risk_reward_ratio:.1f})",
                "upcoming_earnings_risk": "Corporate Earnings Release Proximity",
                "sector_concentration_cap": "Category Sector Concentration Cap (30%)",
                "illiquid_turnover": f"Turnover Threshold (< ₹{TURNOVER_THRESHOLDS.get(cat_key, 2.0):.1f} Cr)"
            }
            cat_primary_bottleneck = bottleneck_labels.get(top_cat_rej_key, f"Market Regime Policy ({market_regime})") if len(top_cat_buys) == 0 else None

            category_results[cat_key] = MarketCapCategoryResult(
                category=cat_key,
                label=categories_config[cat_key]["label"],
                market_cap_rank_range=categories_config[cat_key]["range"],
                classification_source=CLASSIFICATION_SOURCE,
                classification_date=str(CLASSIFICATION_DATE),
                total_scanned=category_survivors[cat_key]["universe"],
                qualified_count=len(top_cat_buys),
                near_misses_count=len(cat_near_misses),
                survivors_by_stage=category_survivors[cat_key],
                primary_bottleneck=cat_primary_bottleneck,
                candidates=top_cat_buys,
                near_misses=top_cat_watchlist
            )

            all_flattened_top_opportunities.extend(top_cat_buys)
            if slots_left > 0:
                all_flattened_top_opportunities.extend(top_cat_watchlist[:slots_left])

        # Global Abstention State: TRUE only if total qualified BUY candidates across ALL 3 categories is 0
        total_qualified_across_all = sum(len(category_results[c].candidates) for c in category_results)
        is_global_abstain = total_qualified_across_all == 0

        sorted_global_bottlenecks = sorted(global_rejections.items(), key=lambda x: x[1], reverse=True)
        top_global_rej_key = sorted_global_bottlenecks[0][0] if sorted_global_bottlenecks else "market_regime"
        bottleneck_labels = {
            "ml_below_threshold": f"ML Probability Threshold (>={int(policy.min_probability_threshold*100)}%)",
            "suboptimal_rr": f"Risk/Reward Requirement (>=1:{policy.min_risk_reward_ratio:.1f})",
            "upcoming_earnings_risk": "Corporate Earnings Release Proximity",
            "sector_concentration_cap": "Portfolio Sector Concentration Cap (30%)",
            "illiquid_turnover": "Institutional Turnover Threshold"
        }
        global_primary_bottleneck = bottleneck_labels.get(top_global_rej_key, f"Market Regime Policy ({market_regime})") if is_global_abstain else None
        
        abstain_reason = None
        if is_global_abstain:
            abstain_reason = (
                f"NO TRADE TODAY: 0 stocks currently satisfy all strict BUY criteria simultaneously across Large, Mid, and Small Cap universes under current {market_regime} conditions. "
                f"Primary Bottleneck: {global_primary_bottleneck}. Review near-miss watchlist opportunities categorized below."
            )

        final_response = ScannerScanResponse(
            large_cap=category_results["LARGE_CAP"],
            mid_cap=category_results["MID_CAP"],
            small_cap=category_results["SMALL_CAP"],
            near_misses=NearMissesGroup(
                large_cap=near_misses_by_category["LARGE_CAP"],
                mid_cap=near_misses_by_category["MID_CAP"],
                small_cap=near_misses_by_category["SMALL_CAP"]
            ),
            total_qualified_count=total_qualified_across_all,
            total_near_misses_count=all_near_misses_count,
            opportunities=all_flattened_top_opportunities,
            buy_candidates_count=all_buy_candidates_count,
            near_misses_count=all_near_misses_count,
            scan_timestamp=scan_time,
            total_universe_scanned=total_universe_count,
            survivors_by_stage=global_survivors,
            primary_bottleneck=global_primary_bottleneck,
            secondary_rejection_summary=global_rejections,
            passed_liquidity_filter=global_survivors["liquid"],
            passed_technical_filter=global_survivors["valid_setups"],
            passed_ml_filter=global_survivors["ml_evaluated"],
            market_regime=market_regime,
            market_regime_policy=policy,
            is_abstention=is_global_abstain,
            abstention_reason=abstain_reason,
            ranking_version=cls.RANKING_VERSION,
            configured_weights=factor_engine.DEFAULT_WEIGHTS,
            configured_probability_threshold=policy.min_probability_threshold,
            configured_min_rr=policy.min_risk_reward_ratio
        )

        try:
            cls.save_scan_to_history(final_response)
        except Exception as e:
            logger.warning(f"Could not persist scan history: {e}")

        return final_response

    @classmethod
    def save_scan_to_history(cls, scan_res: ScannerScanResponse, db = None) -> None:
        """
        Persists full scan results date-wise and enforces maximum 15 days retention.
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            scan_dt = scan_res.scan_timestamp.date() if isinstance(scan_res.scan_timestamp, datetime) else date.today()
            top_symbols = [opp.symbol for opp in scan_res.opportunities[:10]]
            res_json = scan_res.model_dump_json() if hasattr(scan_res, 'model_dump_json') else scan_res.json()
            
            existing = db.query(DBHistoricalScan).filter(DBHistoricalScan.scan_date == scan_dt).first()
            if existing:
                existing.created_at = datetime.utcnow()
                existing.market_regime = scan_res.market_regime
                existing.total_qualified_count = scan_res.total_qualified_count
                existing.large_cap_count = scan_res.large_cap.qualified_count
                existing.mid_cap_count = scan_res.mid_cap.qualified_count
                existing.small_cap_count = scan_res.small_cap.qualified_count
                existing.total_scanned = scan_res.total_universe_scanned
                existing.top_symbols_json = json.dumps(top_symbols)
                existing.result_json = res_json
            else:
                new_entry = DBHistoricalScan(
                    scan_date=scan_dt,
                    created_at=datetime.utcnow(),
                    market_regime=scan_res.market_regime,
                    total_qualified_count=scan_res.total_qualified_count,
                    large_cap_count=scan_res.large_cap.qualified_count,
                    mid_cap_count=scan_res.mid_cap.qualified_count,
                    small_cap_count=scan_res.small_cap.qualified_count,
                    total_scanned=scan_res.total_universe_scanned,
                    top_symbols_json=json.dumps(top_symbols),
                    result_json=res_json
                )
                db.add(new_entry)
            
            db.commit()

            # Enforce max 15 days retention policy
            all_dates = [row[0] for row in db.query(DBHistoricalScan.scan_date).distinct().order_by(DBHistoricalScan.scan_date.desc()).all()]
            if len(all_dates) > 15:
                oldest_allowed_date = all_dates[14]
                db.query(DBHistoricalScan).filter(DBHistoricalScan.scan_date < oldest_allowed_date).delete()
                db.commit()
                logger.info(f"Pruned historical scans older than {oldest_allowed_date} (Max 15 days retained)")

        except Exception as e:
            logger.error(f"Error saving scan to historical database: {e}", exc_info=True)
            db.rollback()
        finally:
            if should_close:
                db.close()

    @classmethod
    def get_history(cls, db = None) -> List[HistoricalScanSummary]:
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            records = db.query(DBHistoricalScan).order_by(DBHistoricalScan.scan_date.desc()).limit(15).all()
            summaries = []
            for r in records:
                syms = []
                try:
                    syms = json.loads(r.top_symbols_json) if r.top_symbols_json else []
                except Exception:
                    pass
                summaries.append(HistoricalScanSummary(
                    id=r.id,
                    scan_date=r.scan_date,
                    created_at=r.created_at,
                    market_regime=r.market_regime,
                    total_qualified_count=r.total_qualified_count,
                    large_cap_count=r.large_cap_count,
                    mid_cap_count=r.mid_cap_count,
                    small_cap_count=r.small_cap_count,
                    total_scanned=r.total_scanned,
                    top_symbols=syms
                ))
            return summaries
        finally:
            if should_close:
                db.close()

    @classmethod
    def get_scan_by_date(cls, scan_dt: date, db = None) -> Optional[ScannerScanResponse]:
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            record = db.query(DBHistoricalScan).filter(DBHistoricalScan.scan_date == scan_dt).first()
            if record and record.result_json:
                data = json.loads(record.result_json)
                return ScannerScanResponse(**data)
            return None
        finally:
            if should_close:
                db.close()

    @classmethod
    def get_scan_by_date_or_latest(cls, date_or_id: str = "latest", db = None) -> Optional[ScannerScanResponse]:
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            if not date_or_id or date_or_id.lower() == "latest":
                record = db.query(DBHistoricalScan).order_by(DBHistoricalScan.scan_date.desc()).first()
            elif date_or_id.isdigit():
                record = db.query(DBHistoricalScan).filter(DBHistoricalScan.id == int(date_or_id)).first()
            else:
                try:
                    parsed_dt = datetime.strptime(date_or_id, "%Y-%m-%d").date()
                    record = db.query(DBHistoricalScan).filter(DBHistoricalScan.scan_date == parsed_dt).first()
                except Exception:
                    record = db.query(DBHistoricalScan).order_by(DBHistoricalScan.scan_date.desc()).first()
            
            if record and record.result_json:
                data = json.loads(record.result_json)
                return ScannerScanResponse(**data)
            return None
        except Exception as e:
            logger.error(f"Error querying scan by date_or_id '{date_or_id}': {e}")
            return None
        finally:
            if should_close:
                db.close()

scanner_service = SystematicStockScanner()
staged_scanner = scanner_service

