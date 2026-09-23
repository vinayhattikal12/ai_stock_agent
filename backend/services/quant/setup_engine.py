from typing import List, Dict, Any, Optional
from backend.models.schemas import Candle, TechnicalIndicators, VolumeProfileMetrics

class SetupClassification:
    def __init__(
        self,
        setup_type: str,
        quality_score: Optional[float],
        trigger_price: Optional[float],
        invalidation_price: Optional[float],
        rationale: str,
        setup_attributes: Optional[Dict[str, Any]] = None
    ):
        self.setup_type = setup_type # BREAKOUT, PULLBACK, MOMENTUM_CONTINUATION, VOLATILITY_CONTRACTION, BASE_BREAKOUT, OTHER_VALID_SETUP, NONE
        self.quality_score = quality_score
        self.trigger_price = trigger_price
        self.invalidation_price = invalidation_price
        self.rationale = rationale
        self.setup_attributes = setup_attributes or {}

class SetupEngine:
    """
    Classifies systematic swing trading setups and evaluates their pattern quality score (0–100):
    1. BREAKOUT (Range / Multi-week high breakout with volume expansion)
    2. PULLBACK (Dip to rising 20 EMA or 50 SMA with volume dry-up and support hold)
    3. VOLATILITY_CONTRACTION (VCP / Squeeze coiling for expansion)
    4. BASE_BREAKOUT (40-60 day structural base breakout with expanding ATR)
    5. MOMENTUM_CONTINUATION (High RS, steady trending staircase above moving averages)
    6. OTHER_VALID_SETUP (Constructive technical structure holding key trend benchmarks)
    7. NONE (Insufficient observations or structure)
    """

    @classmethod
    def classify_setup(
        cls,
        candles: List[Candle],
        indicators: TechnicalIndicators,
        volume_metrics: VolumeProfileMetrics,
        mansfield_rs: Optional[float] = None,
        candle_score: Optional[float] = None,
        sector_momentum: Optional[float] = None
    ) -> SetupClassification:
        if not candles or len(candles) < 20:
            return SetupClassification(
                setup_type="NONE",
                quality_score=None,
                trigger_price=None,
                invalidation_price=None,
                rationale="Insufficient historical daily candle data to classify structural setup."
            )

        c = candles[-1]
        c_price = c.close
        highs_20 = [x.high for x in candles[-21:-1]] if len(candles) >= 21 else [x.high for x in candles[:-1]]
        highest_20 = max(highs_20) if highs_20 else c_price
        lows_20 = [x.low for x in candles[-21:-1]] if len(candles) >= 21 else [x.low for x in candles[:-1]]
        lowest_20 = min(lows_20) if lows_20 else c_price

        # Close Location in Candle (CLV)
        c_range = max(0.001, c.high - c.low)
        clv = (c.close - c.low) / c_range
        rvol = volume_metrics.rvol_20d if volume_metrics.rvol_20d is not None else 1.0
        m_rs = mansfield_rs if mansfield_rs is not None else 0.0
        sec_mom = sector_momentum if sector_momentum is not None else 50.0
        c_score = candle_score if candle_score is not None else 50.0

        ema_20 = indicators.ema_20 or c_price
        ema_50 = indicators.ema_50 or c_price
        sma_50 = indicators.sma_50 or c_price
        rsi = indicators.rsi_14 or 50.0
        adx = indicators.adx_14 or 20.0

        # 1. Base Breakout Check (40 to 60 day base)
        if len(candles) >= 45:
            highs_45 = [x.high for x in candles[-46:-1]]
            highest_45 = max(highs_45) if highs_45 else highest_20
            if c_price >= highest_45 * 0.995 and rvol >= 1.15:
                base_score = 50.0 + min(25.0, rvol * 12.0) + (clv * 15.0) + (10.0 if m_rs > 0 else 0.0)
                quality = round(max(0.0, min(100.0, base_score)), 1)
                return SetupClassification(
                    setup_type="BASE_BREAKOUT",
                    quality_score=quality,
                    trigger_price=round(highest_45 * 1.002, 2),
                    invalidation_price=round(min(c.low, ema_20 * 0.99), 2),
                    rationale=f"Multi-week base breakout clearing ₹{highest_45:.2f} pivot with {rvol:.2f}x RVOL and strong close.",
                    setup_attributes={"pivot_level": highest_45, "base_length_bars": 45}
                )

        # 2. Standard 20-Day Range Breakout Check
        is_breaking_20d_high = c.close >= highest_20 or (c.high >= highest_20 and c.close > candles[-2].close)
        if is_breaking_20d_high and c_price > ema_20:
            breakout_score = (
                40.0 +
                min(25.0, rvol * 12.0) +
                (clv * 15.0) +
                min(10.0, max(0.0, m_rs * 1.5)) +
                (sec_mom / 100.0 * 10.0)
            )
            quality = round(max(0.0, min(100.0, breakout_score)), 1)
            return SetupClassification(
                setup_type="BREAKOUT",
                quality_score=quality,
                trigger_price=round(highest_20 * 1.002, 2),
                invalidation_price=round(min(c.low, ema_20 * 0.99), 2),
                rationale=f"Decisive 20-day resistance breakout at ₹{highest_20:.2f} confirmed by RVOL {rvol:.2f}x and top {int(clv*100)}% close.",
                setup_attributes={"pivot_level": highest_20, "rvol": rvol}
            )

        # 3. Pullback to Moving Average / Support Check
        is_uptrend = ema_20 > sma_50 and c_price > sma_50
        dist_to_ema20 = abs(c_price - ema_20) / (ema_20 or 1.0) * 100.0
        
        if is_uptrend and dist_to_ema20 <= 2.5 and c_price >= ema_20 * 0.985:
            vol_ratio = volume_metrics.volume_5d_vs_20d_ratio if volume_metrics.volume_5d_vs_20d_ratio is not None else 1.0
            is_volume_dry = vol_ratio <= 0.90 or rvol <= 0.95
            pullback_score = (
                45.0 +
                (15.0 if is_volume_dry else 5.0) +
                (c_score * 0.20) +
                (10.0 if c_price >= ema_20 else 5.0) +
                min(10.0, max(0.0, m_rs * 1.5))
            )
            quality = round(max(0.0, min(100.0, pullback_score)), 1)
            return SetupClassification(
                setup_type="PULLBACK",
                quality_score=quality,
                trigger_price=round(c.high * 1.002, 2),
                invalidation_price=round(min([x.low for x in candles[-3:]]) * 0.995, 2),
                rationale=f"Orderly pullback to rising 20 EMA (₹{ema_20:.2f}) with volume dry-up ({vol_ratio:.2f}x 20D avg) and support hold.",
                setup_attributes={"ema_support": ema_20, "volume_dry_up": is_volume_dry}
            )

        # 4. Volatility Contraction Pattern (VCP / Squeeze)
        range_5 = max(x.high for x in candles[-5:]) - min(x.low for x in candles[-5:])
        range_prior_10 = max(x.high for x in candles[-15:-5]) - min(x.low for x in candles[-15:-5]) if len(candles) >= 15 else range_5 * 2.0
        
        is_contracting = range_5 < (range_prior_10 * 0.65) and rvol < 0.95
        if is_contracting and c_price > sma_50:
            vcp_score = 55.0 + (15.0 if m_rs > 0 else 5.0) + (c_score * 0.20) + (10.0 if ema_20 > sma_50 else 0.0)
            quality = round(max(0.0, min(100.0, vcp_score)), 1)
            recent_high_5 = max(x.high for x in candles[-5:])
            return SetupClassification(
                setup_type="VOLATILITY_CONTRACTION",
                quality_score=quality,
                trigger_price=round(recent_high_5 * 1.002, 2),
                invalidation_price=round(min(x.low for x in candles[-5:]) * 0.995, 2),
                rationale=f"Tight volatility contraction (VCP) with {range_5/c_price*100:.1f}% base width and quiet volume; coiling for expansion.",
                setup_attributes={"contraction_ratio": round(range_5 / (range_prior_10 or 1.0), 2)}
            )

        # 5. Momentum Continuation Setup
        if (ema_20 > sma_50 and
            c_price > ema_20 and
            52.0 <= rsi <= 74.0 and
            adx >= 18.0):
            mom_score = 50.0 + min(20.0, max(0.0, m_rs * 2.5)) + (adx * 0.6) + (10.0 if clv > 0.6 else 0.0)
            quality = round(max(0.0, min(100.0, mom_score)), 1)
            return SetupClassification(
                setup_type="MOMENTUM_CONTINUATION",
                quality_score=quality,
                trigger_price=round(c.high * 1.002, 2),
                invalidation_price=round(ema_20 * 0.985, 2),
                rationale=f"Trending momentum continuation with RSI {rsi:.1f}, ADX {adx:.1f}, and positive RS (+{m_rs:.1f}%).",
                setup_attributes={"adx": adx, "rsi": rsi}
            )

        # 6. Unclassified / Non-Standard Structure
        unclassified_score = 35.0 + (10.0 if c_price > ema_50 else 0.0) + (10.0 if m_rs > 0 else 0.0)
        quality = round(max(0.0, min(100.0, unclassified_score)), 1)
        return SetupClassification(
            setup_type="UNCLASSIFIED",
            quality_score=quality,
            trigger_price=round(c.high * 1.004, 2),
            invalidation_price=round(min(c.low, ema_50 * 0.98), 2),
            rationale=f"Structure does not meet high-conviction swing pattern criteria; holding secondary benchmark (EMA 50: ₹{ema_50:.2f}).",
            setup_attributes={"support_level": ema_50}
        )

setup_engine = SetupEngine()

