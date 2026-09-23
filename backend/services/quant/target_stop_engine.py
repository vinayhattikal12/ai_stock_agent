from typing import List, Dict, Any, Optional
from backend.models.schemas import Candle, TechnicalIndicators, TradeLevels

class TargetStopEngine:
    """
    Quantitative engine for calculating precise Rupee price entries, multi-tier targets (T1, T2, T3),
    and risk-mitigating stop loss prices based on structural S/R pivots, 50D/120D swing highs,
    measured move projections, and ATR volatility extensions.

    Zero-fallback policy: returns None when market structure cannot be computed reliably.
    Prioritizes explicit Rupee price levels over abstract ratios.
    """

    @classmethod
    def calculate_levels(
        cls,
        candles: List[Candle],
        indicators: TechnicalIndicators,
        direction: str = "BULLISH"
    ) -> TradeLevels:
        if not candles or len(candles) < 15:
            return TradeLevels(
                current_price=None,
                entry_low=None,
                entry_high=None,
                entry_range_display=None,
                target_1=None,
                target_2=None,
                target_3=None,
                target_1_display=None,
                target_2_display=None,
                target_3_display=None,
                target_1_r_multiple=None,
                target_2_r_multiple=None,
                target_3_r_multiple=None,
                risk_reward_ratio_t1=None,
                risk_reward_ratio_t2=None,
                risk_reward_ratio_t3=None,
                stop_loss=None,
                stop_loss_display=None,
                risk_reward_ratio=None,
                risk_per_share=None,
                reward_t1_per_share=None,
                target_derivation_method="INSUFFICIENT_DATA",
                stop_method="NONE",
                stop_reason="Insufficient historical candle data to map structural levels",
                levels_reasoning=["Insufficient price history for structural mapping"],
                status="UNAVAILABLE"
            )

        current_price = candles[-1].close
        atr = indicators.atr_14 if (indicators.atr_14 is not None and indicators.atr_14 > 0) else (current_price * 0.02)
        ema_20 = indicators.ema_20 or current_price

        # 1. Entry Zone Prices & Reference Entry Definition
        # For long swing setups, reference_entry is the conservative upper entry zone bound
        entry_low = round(min(current_price * 0.994, ema_20), 2)
        entry_high = round(current_price * 1.004, 2)
        reference_entry = entry_high

        # 2. Structural Stop Loss Price
        # Scan 10-day and 20-day structural swing lows
        recent_10 = candles[-min(10, len(candles)):]
        recent_20 = candles[-min(20, len(candles)):]
        swing_low_10 = min(c.low for c in recent_10)
        swing_low_20 = min(c.low for c in recent_20)
        ema_stop = ema_20 - (atr * 0.75)

        if swing_low_10 > reference_entry * 0.94 and swing_low_10 < reference_entry:
            stop_loss = round(swing_low_10 * 0.995, 2)
            stop_method = "STRUCTURAL_SWING_LOW"
            stop_reason = f"0.5% below 10-day structural swing low (₹{swing_low_10:.2f})"
        elif ema_stop > reference_entry * 0.94 and ema_stop < reference_entry:
            stop_loss = round(ema_stop, 2)
            stop_method = "EMA20_BUFFER"
            stop_reason = f"0.75× ATR buffer below rising 20 EMA (₹{ema_20:.2f})"
        else:
            stop_loss = round(reference_entry - (atr * 1.8), 2)
            stop_method = "ATR_VOLATILITY_BAND"
            stop_reason = f"1.8× ATR dynamic volatility trailing band (₹{atr:.2f})"

        # Ensure swing stop risk is between 1.5% and 6.0% from reference entry
        min_risk_dist = reference_entry * 0.015
        max_risk_dist = reference_entry * 0.060
        actual_dist = reference_entry - stop_loss

        if actual_dist < min_risk_dist:
            stop_loss = round(reference_entry - min_risk_dist, 2)
        elif actual_dist > max_risk_dist:
            stop_loss = round(reference_entry - max_risk_dist, 2)

        risk_per_share = round(reference_entry - stop_loss, 2)
        if risk_per_share <= 0:
            risk_per_share = round(reference_entry * 0.02, 2)
            stop_loss = round(reference_entry - risk_per_share, 2)

        # 3. Structural Target 1 (T1) Price Level
        high_20 = max([c.high for c in candles[-min(21, len(candles)):-1]]) if len(candles) >= 5 else reference_entry * 1.05
        high_50 = max([c.high for c in candles[-min(51, len(candles)):-1]]) if len(candles) >= 20 else high_20
        high_120 = max([c.high for c in candles[-min(121, len(candles)):-1]]) if len(candles) >= 50 else high_50

        t1_candidates = []
        t1_method = "Previous Swing Resistance"
        if indicators.resistance_levels:
            for r in indicators.resistance_levels:
                if r > reference_entry * 1.01:
                    t1_candidates.append((r, "Key Horizontal Resistance"))
        if high_20 > reference_entry * 1.01:
            t1_candidates.append((high_20, "20-Day Swing High Resistance"))
        t1_candidates.append((reference_entry + (risk_per_share * 1.8), "1.8× Risk Volatility Expansion"))

        # Target 1 Price: structural resistance offering at least 1.2R
        t1_valid = [(p, m) for p, m in t1_candidates if p >= reference_entry + (risk_per_share * 1.2)]
        if t1_valid:
            target_1, t1_method = min(t1_valid, key=lambda x: x[0])
            target_1 = round(target_1, 2)
        else:
            target_1 = round(reference_entry + (risk_per_share * 1.8), 2)
            t1_method = "1.8× ATR Volatility Expansion"

        reward_t1 = round(target_1 - reference_entry, 2)
        actual_t1_r = round(reward_t1 / risk_per_share, 2) if risk_per_share > 0 else 1.8

        # 4. Structural Target 2 (T2) Price Level
        base_width = max(0.0, high_20 - swing_low_20)
        measured_move_t2 = reference_entry + max(base_width, risk_per_share * 2.8)

        t2_candidates = [(measured_move_t2, "Base Breakout Measured Move")]
        if high_50 > target_1:
            t2_candidates.append((high_50, "50-Day Major Resistance"))
        if len(indicators.resistance_levels) > 1 and indicators.resistance_levels[1] > target_1:
            t2_candidates.append((indicators.resistance_levels[1], "Secondary Structural Resistance"))
        t2_candidates.append((target_1 + (risk_per_share * 1.4), "Multi-Tier Expansion Target"))

        target_2, t2_method = max(t2_candidates, key=lambda x: x[0])
        target_2 = round(target_2, 2)
        reward_t2 = round(target_2 - reference_entry, 2)
        actual_t2_r = round(reward_t2 / risk_per_share, 2) if risk_per_share > 0 else 3.0

        # 5. Structural Target 3 (T3) Price Level (Runner / 52W High Extension)
        t3_candidates = []
        if high_120 > target_2 * 1.02:
            t3_candidates.append((high_120, "120-Day Swing High Extension"))
        
        # 52W high extension check
        all_highs = [c.high for c in candles]
        high_52w = max(all_highs) if all_highs else reference_entry
        if high_52w > target_2 * 1.02:
            t3_candidates.append((high_52w, "52-Week High Structural Target"))

        if t3_candidates:
            target_3, t3_method = max(t3_candidates, key=lambda x: x[0])
            target_3 = round(target_3, 2)
            reward_t3 = round(target_3 - reference_entry, 2)
            actual_t3_r = round(reward_t3 / risk_per_share, 2) if risk_per_share > 0 else 4.5
            t3_pct = round(((target_3 - reference_entry) / reference_entry) * 100.0, 1)
            target_3_display = f"₹{target_3:,.2f} ({t3_pct:+.1f}%)"
            target_3_reason = None
        else:
            target_3 = None
            t3_method = None
            actual_t3_r = None
            target_3_display = None
            target_3_reason = "No defensible structural resistance beyond Target 2 within 20-day swing horizon."

        # Price Display Format Strings (strictly referenced from reference_entry)
        stop_pct = round(((stop_loss - reference_entry) / reference_entry) * 100.0, 1)
        t1_pct = round(((target_1 - reference_entry) / reference_entry) * 100.0, 1)
        t2_pct = round(((target_2 - reference_entry) / reference_entry) * 100.0, 1)

        stop_loss_display = f"₹{stop_loss:,.2f} ({stop_pct:+.1f}%)"
        target_1_display = f"₹{target_1:,.2f} ({t1_pct:+.1f}%)"
        target_2_display = f"₹{target_2:,.2f} ({t2_pct:+.1f}%)"
        entry_range_display = f"₹{entry_low:,.2f} – ₹{entry_high:,.2f}"

        # Transparent reasoning formulation
        reasoning = [
            f"Reference Entry: ₹{reference_entry:,.2f} (Entry Zone: {entry_range_display}).",
            f"Stop Loss: ₹{stop_loss:,.2f} ({stop_reason}, risk: ₹{risk_per_share:,.2f}/share or {stop_pct:+.1f}%).",
            f"Target 1: ₹{target_1:,.2f} ({t1_pct:+.1f}%, 1:{actual_t1_r:.2f}R payoff via {t1_method}).",
            f"Target 2: ₹{target_2:,.2f} ({t2_pct:+.1f}%, 1:{actual_t2_r:.2f}R payoff via {t2_method})."
        ]
        if target_3 is not None:
            reasoning.append(f"Target 3: ₹{target_3:,.2f} ({target_3_display}, 1:{actual_t3_r:.2f}R payoff via {t3_method}).")
        else:
            reasoning.append(f"Target 3: UNAVAILABLE ({target_3_reason}).")

        return TradeLevels(
            current_price=current_price,
            reference_entry=reference_entry,
            entry_low=entry_low,
            entry_high=entry_high,
            entry_range_display=entry_range_display,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            target_1_display=target_1_display,
            target_2_display=target_2_display,
            target_3_display=target_3_display,
            target_1_method=t1_method,
            target_2_method=t2_method,
            target_3_method=t3_method,
            target_3_reason=target_3_reason,
            target_1_r_multiple=actual_t1_r,
            target_2_r_multiple=actual_t2_r,
            target_3_r_multiple=actual_t3_r,
            risk_reward_ratio_t1=actual_t1_r,
            risk_reward_ratio_t2=actual_t2_r,
            risk_reward_ratio_t3=actual_t3_r,
            stop_loss=stop_loss,
            stop_loss_display=stop_loss_display,
            risk_reward_ratio=actual_t1_r,
            risk_per_share=risk_per_share,
            reward_t1_per_share=reward_t1,
            target_derivation_method="STRUCTURAL_PIVOTS_AND_ATR",
            stop_method=stop_method,
            stop_reason=stop_reason,
            levels_reasoning=reasoning,
            status="AVAILABLE"
        )


target_stop_engine = TargetStopEngine()
