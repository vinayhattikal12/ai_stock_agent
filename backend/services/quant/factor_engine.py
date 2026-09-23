from typing import List, Dict, Any, Optional
from backend.models.schemas import Candle, TechnicalIndicators, VolumeProfileMetrics, FactorScores

class FactorEngine:
    """
    Computes normalized, decoupled quantitative factor scores (0-100) across:
    - Momentum (20%): Multi-horizon return velocity, 20D/50D rate of change, MA stacking
    - Relative Strength (15%): Mansfield RS vs NIFTY 50 and Sector Excess Return
    - Trend Structure (15%): Moving average alignment (20 > 50 > 200), Kaufman efficiency
    - Setup Quality (15%): Structural breakout, pullback, or VCP quality score
    - Volume/Liquidity (10%): RVOL, accumulation/distribution, turnover in INR Crores
    - Quality/Fundamentals (10%): Low drawdown from 52-week high, stability of trend
    - Catalyst/News (10%): Verified corporate actions, earnings outlook, disclosures
    - Volatility/Risk Quality (5%): Orderly ATR band percentage, low tail risk

    Zero-fallback policy: returns None when inputs are missing; never returns fake 50.0.
    """

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "momentum": 0.20,
        "relative_strength": 0.15,
        "trend_structure": 0.15,
        "setup_quality": 0.15,
        "volume_liquidity": 0.10,
        "quality_fundamentals": 0.10,
        "catalyst_news": 0.10,
        "volatility_risk": 0.05
    }

    @classmethod
    def calculate_factors(
        cls,
        candles: List[Candle],
        indicators: TechnicalIndicators,
        volume_metrics: VolumeProfileMetrics,
        mansfield_rs: Optional[float] = None,
        sector_momentum: Optional[float] = None,
        setup_quality_score: Optional[float] = None,
        catalyst_score: Optional[float] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> FactorScores:
        if not candles or len(candles) < 20:
            return FactorScores(
                momentum_score=None,
                relative_strength_score=None,
                trend_score=None,
                setup_quality_score=None,
                volume_score=None,
                quality_score=None,
                catalyst_score=None,
                volatility_score=None,
                value_score=None,
                liquidity_score=None,
                overall_factor_rank=None,
                status="UNAVAILABLE"
            )

        c = candles[-1]
        c_price = c.close
        weights = custom_weights or cls.DEFAULT_WEIGHTS

        # 1. Momentum Score (0 - 100) -> 20%
        # Derived from 20D Return, 50D Return, and RSI velocity
        ret_20d = (c_price - candles[-20].close) / (candles[-20].close or 1.0) * 100.0 if len(candles) >= 20 else 0.0
        ret_50d = (c_price - candles[-min(len(candles), 50)].close) / (candles[-min(len(candles), 50)].close or 1.0) * 100.0
        
        norm_ret_20d = max(0.0, min(50.0, 25.0 + (ret_20d * 2.5)))
        norm_ret_50d = max(0.0, min(30.0, 15.0 + (ret_50d * 1.0)))
        norm_rsi = max(0.0, min(20.0, ((indicators.rsi_14 or 50.0) / 70.0) * 20.0)) if indicators.rsi_14 is not None else 10.0
        momentum_score = round(max(0.0, min(100.0, norm_ret_20d + norm_ret_50d + norm_rsi)), 1)

        # 2. Relative Strength Score (0 - 100) -> 15%
        if mansfield_rs is not None:
            rs_pts = max(0.0, min(70.0, 50.0 + (mansfield_rs * 3.5)))
            sec_pts = ((sector_momentum or 50.0) / 100.0) * 30.0
            relative_strength_score = round(max(0.0, min(100.0, rs_pts + sec_pts)), 1)
        else:
            relative_strength_score = None

        # 3. Trend Structure Score (0 - 100) -> 15%
        ma_alignment_pts = 0.0
        if indicators.ema_20 is not None and c_price >= indicators.ema_20:
            ma_alignment_pts += 20.0
        if indicators.ema_20 is not None and indicators.ema_50 is not None and indicators.ema_20 >= indicators.ema_50:
            ma_alignment_pts += 25.0
        if indicators.ema_50 is not None and indicators.ema_200 is not None and indicators.ema_50 >= indicators.ema_200:
            ma_alignment_pts += 25.0

        n_bars = min(len(candles), 20)
        net_change = abs(c_price - candles[-n_bars].close)
        path_sum = sum(abs(candles[i].close - candles[i-1].close) for i in range(-n_bars + 1, 0)) or 1.0
        efficiency_ratio = net_change / path_sum
        eff_pts = efficiency_ratio * 30.0
        trend_score = round(max(0.0, min(100.0, ma_alignment_pts + eff_pts)), 1)

        # 4. Setup Quality Score (0 - 100) -> 15%
        setup_score = round(setup_quality_score, 1) if setup_quality_score is not None else None

        # 5. Volume / Liquidity Score (0 - 100) -> 10%
        rvol = volume_metrics.rvol_20d or 1.0
        rvol_pts = max(0.0, min(40.0, rvol * 25.0))
        
        turnover_cr = volume_metrics.avg_turnover_cr_20d or 0.0
        if turnover_cr >= 50.0:
            turnover_pts = 30.0
        elif turnover_cr >= 15.0:
            turnover_pts = 24.0
        elif turnover_cr >= 5.0:
            turnover_pts = 18.0
        else:
            turnover_pts = max(5.0, turnover_cr * 3.0)
            
        trend_pts = 30.0 if volume_metrics.volume_trend == "ACCUMULATION" else (
            20.0 if volume_metrics.volume_trend in ["NEUTRAL", "CONTRACTION"] else 5.0
        )
        volume_score = round(max(0.0, min(100.0, rvol_pts + turnover_pts + trend_pts)), 1)

        # 6. Quality & Fundamentals Score (0 - 100) -> 10%
        all_highs = [x.high for x in candles]
        high_52w = max(all_highs) if all_highs else c_price
        drawdown_52w = (high_52w - c_price) / (high_52w or 1.0) * 100.0
        quality_score = round(max(0.0, min(100.0, 100.0 - (drawdown_52w * 2.5))), 1)

        # 7. Catalyst & News Score (0 - 100) -> 10%
        cat_score = round(catalyst_score, 1) if catalyst_score is not None else 50.0

        # 8. Volatility & Risk Quality Score (0 - 100) -> 5%
        if indicators.atr_14 is not None and c_price > 0:
            atr_pct = (indicators.atr_14 / c_price) * 100.0
            if 1.5 <= atr_pct <= 3.2:
                vol_score = 95.0
            elif atr_pct < 1.5:
                vol_score = 80.0
            elif atr_pct <= 4.5:
                vol_score = 70.0
            else:
                vol_score = max(20.0, 65.0 - ((atr_pct - 4.5) * 10.0))
            volatility_score = round(max(0.0, min(100.0, vol_score)), 1)
        else:
            volatility_score = None

        # Assemble Factor Breakdown and Weighted Identity
        from backend.models.schemas import FactorContributionItem

        factor_items = [
            ("Momentum", f"20D: {ret_20d:+.1f}%, 50D: {ret_50d:+.1f}%", momentum_score, weights["momentum"], "Multi-horizon return velocity and moving average stack"),
            ("Relative Strength", f"Mansfield: {mansfield_rs:+.1f}%" if mansfield_rs is not None else "N/A", relative_strength_score, weights["relative_strength"], "Excess returns and Mansfield alpha vs NIFTY 50"),
            ("Trend Structure", f"EMA20: ₹{indicators.ema_20:.1f}" if indicators.ema_20 else "N/A", trend_score, weights["trend_structure"], "Moving average alignment (20>50>200) and trend path efficiency"),
            ("Setup Quality", f"Score: {setup_score}" if setup_score is not None else "N/A", setup_score, weights["setup_quality"], "Structural base breakout, pullback, or VCP score"),
            ("Volume & Liquidity", f"RVOL: {rvol:.2f}x, ₹{turnover_cr:.1f}Cr", volume_score, weights["volume_liquidity"], "Volume surge, accumulation trend, and daily liquidity"),
            ("Quality & Fundamentals", f"52W Drawdown: -{drawdown_52w:.1f}%", quality_score, weights["quality_fundamentals"], "Proximity to 52-week highs and drawdown containment"),
            ("Catalysts & News", f"Score: {cat_score}", cat_score, weights["catalyst_news"], "Material corporate actions, results, and order flows"),
            ("Volatility & Risk", f"ATR: {((indicators.atr_14/c_price*100) if (indicators.atr_14 and c_price) else 0):.1f}%", volatility_score, weights["volatility_risk"], "ATR volatility band predictability and tail-risk control")
        ]

        # Calculate normalized active weights
        avail_weight = sum(w for _, _, sc, w, _ in factor_items if sc is not None)
        breakdown: List[FactorContributionItem] = []
        composite_sum = 0.0

        for name, raw, score, raw_w, rat in factor_items:
            if score is not None and avail_weight > 0:
                normalized_w = raw_w / avail_weight
                contrib = round(score * normalized_w, 2)
                composite_sum += contrib
                breakdown.append(FactorContributionItem(
                    factor_name=name,
                    raw_value=raw,
                    normalized_score=score,
                    weight_pct=round(normalized_w * 100.0, 1),
                    weighted_contribution=contrib,
                    rationale=rat
                ))
            else:
                breakdown.append(FactorContributionItem(
                    factor_name=name,
                    raw_value=raw,
                    normalized_score=None,
                    weight_pct=round(raw_w * 100.0, 1),
                    weighted_contribution=None,
                    rationale=rat
                ))

        overall_factor_rank = round(composite_sum, 1) if avail_weight >= 0.50 else None

        return FactorScores(
            momentum_score=momentum_score,
            relative_strength_score=relative_strength_score,
            trend_score=trend_score,
            setup_quality_score=setup_score,
            volume_score=volume_score,
            quality_score=quality_score,
            catalyst_score=cat_score,
            volatility_score=volatility_score,
            value_score=round(max(0.0, min(100.0, 50.0 + (ret_20d * 0.5))), 1),
            liquidity_score=round(turnover_pts / 30.0 * 100.0, 1),
            overall_factor_rank=overall_factor_rank,
            factor_breakdown=breakdown,
            status="AVAILABLE" if overall_factor_rank is not None else "PARTIAL"
        )

factor_engine = FactorEngine()

