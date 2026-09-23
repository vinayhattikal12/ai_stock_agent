from datetime import datetime, date
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

# --- Data Provenance & Quality Gate Schemas ---
class MetricProvenance(BaseModel):
    value: Optional[Any] = None
    status: str = "AVAILABLE"  # AVAILABLE, PARTIAL, UNAVAILABLE, INVALID, STALE
    reason: Optional[str] = None
    as_of: Optional[datetime] = None
    source: str = "Upstox API v2"

class DataQualityReport(BaseModel):
    is_valid: bool
    status: str  # AVAILABLE, PARTIAL, UNAVAILABLE, INVALID, STALE
    rejection_reason: Optional[str] = None
    candle_count: int = 0
    min_required_candles: int = 120
    first_candle_date: Optional[str] = None
    last_candle_date: Optional[str] = None
    exchange: str = "NSE_EQ"
    instrument_key: Optional[str] = None
    isin: Optional[str] = None
    validated_at: datetime = Field(default_factory=datetime.utcnow)

# --- Market Models ---
class MarketIndexQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    high: float
    low: float
    open: float
    prev_close: float

class MarketBreadth(BaseModel):
    advances: int
    declines: int
    unchanged: int
    ad_ratio: float
    pct_above_20_ema: float
    pct_above_50_ema: float
    pct_above_200_ema: float
    highs_52w_count: Optional[int] = 0
    lows_52w_count: Optional[int] = 0

class SectorPerformance(BaseModel):
    sector_name: str
    symbol: str
    change_percent_1d: float
    change_percent_5d: float
    change_percent_20d: float
    change_percent_50d: float
    change_percent_100d: float
    change_percent_6m: float
    momentum_score: float  # 0 to 100
    relative_strength_vs_nifty: float
    trend: str  # STRONG_BULLISH, BULLISH, NEUTRAL, BEARISH, STRONG_BEARISH
    sector_breadth_pct_above_50ema: float
    top_driver: Optional[str] = None
    rank: int = 1

class MarketRegimePolicy(BaseModel):
    regime: str  # STRONG_BULL, BULL, NEUTRAL, RECOVERY, BEAR, STRESS
    status_label: str
    description: str
    min_probability_threshold: float  # e.g. 0.55 in Strong Bull, 0.65 in Neutral, 0.72 in Bear
    min_risk_reward_ratio: float  # e.g. 1.5 in Bull, 2.0 in Bear
    max_opportunities: int  # e.g. 5 in Bull, 2 in Bear, 0 in Stress
    position_size_multiplier: float  # 1.0 down to 0.0
    setup_quality_requirement: str  # STANDARD, STRICT, HIGHEST_CONVICTION
    allow_new_longs: bool

class MarketStatusResponse(BaseModel):
    status_label: str
    regime: str  # STRONG_BULL, BULL, NEUTRAL, RECOVERY, BEAR, STRESS
    regime_policy: MarketRegimePolicy
    nifty: MarketIndexQuote
    bank_nifty: MarketIndexQuote
    india_vix: MarketIndexQuote
    breadth: MarketBreadth
    strong_sectors: List[SectorPerformance]
    weak_sectors: List[SectorPerformance]
    sector_rotation_matrix: List[SectorPerformance]
    major_events: List[str]
    last_updated: datetime
    is_live_data: bool

# --- Candle & Chart Models ---
class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: Optional[int] = 0

class CandlestickPattern(BaseModel):
    name: str
    pattern_type: str  # BULLISH, BEARISH, INDECISION
    reliability: str  # HIGH, MEDIUM, LOW
    description: str
    confirmation_score: Optional[float] = 75.0

class TechnicalIndicators(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr_14: Optional[float] = None
    adx_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    supertrend: Optional[float] = None
    supertrend_direction: Optional[str] = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    support_levels: List[float] = []
    resistance_levels: List[float] = []
    status: str = "AVAILABLE"  # AVAILABLE, PARTIAL, UNAVAILABLE

# --- Market Data Snapshot ---
class MarketDataSnapshot(BaseModel):
    symbol: str
    exchange: str = "NSE_EQ"
    instrument_key: str
    isin: Optional[str] = None
    quote_price: Optional[float] = None
    previous_close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    quote_timestamp: Optional[datetime] = None
    latest_candle_timestamp: Optional[datetime] = None
    historical_candle_count: int = 0
    data_source: str = "Upstox API v2 Live Feed"
    data_freshness: str = "REALTIME"  # REALTIME, DELAYED, EOD, UNAVAILABLE
    data_quality_status: str = "GOOD"  # GOOD, DEGRADED, INSUFFICIENT
    provenance_note: Optional[str] = None

# --- Factor Engine Models ---
class FactorContributionItem(BaseModel):
    factor_name: str
    raw_value: Optional[str] = None
    normalized_score: Optional[float] = None  # 0 to 100
    weight_pct: float  # e.g. 20.0 for 20%
    weighted_contribution: Optional[float] = None  # normalized_score * (weight_pct / 100)
    rationale: Optional[str] = None

class FactorScores(BaseModel):
    momentum_score: Optional[float] = None        # 20% (Multi-horizon returns, MA stacking)
    relative_strength_score: Optional[float] = None # 15% (Mansfield RS vs NIFTY & Sector)
    trend_score: Optional[float] = None           # 15% (Trend alignment & efficiency)
    setup_quality_score: Optional[float] = None   # 15% (Setup pattern quality)
    volume_score: Optional[float] = None          # 10% (RVOL, accumulation, turnover)
    quality_score: Optional[float] = None         # 10% (52W drawdown, consistency)
    catalyst_score: Optional[float] = None        # 10% (Corporate actions, disclosures)
    volatility_score: Optional[float] = None      # 5% (ATR risk stability)
    value_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    overall_factor_rank: Optional[float] = None   # 0 to 100 Normalized Composite
    factor_breakdown: List[FactorContributionItem] = []
    status: str = "AVAILABLE"  # AVAILABLE, PARTIAL, UNAVAILABLE

class RelativeStrengthMetrics(BaseModel):
    excess_return_5d: Optional[float] = None
    excess_return_20d: Optional[float] = None
    excess_return_50d: Optional[float] = None
    excess_return_100d: Optional[float] = None
    mansfield_rs_20d: Optional[float] = None
    mansfield_rs_50d: Optional[float] = None
    mansfield_rs_100d: Optional[float] = None
    sector_relative_strength_20d: Optional[float] = None
    market_relative_strength_20d: Optional[float] = None
    rs_trend: str = "FLAT"  # EXPANDING, FLAT, DETERIORATING
    status: str = "AVAILABLE"

class VolumeProfileMetrics(BaseModel):
    rvol_20d: Optional[float] = None  # Relative Volume vs 20D average
    volume_5d_vs_20d_ratio: Optional[float] = None
    breakout_volume_surge: Optional[float] = None
    volume_trend: str = "NEUTRAL"  # ACCUMULATION, DISTRIBUTION, NEUTRAL, CONTRACTION
    avg_turnover_cr_20d: Optional[float] = None
    is_volume_confirmed: bool = False
    status: str = "AVAILABLE"

# --- ML & Opportunity Models ---
class MLProbabilityMetrics(BaseModel):
    p_t1_before_sl: Optional[float] = None  # e.g. 0.68 (68%)
    p_t2_before_sl: Optional[float] = None  # e.g. 0.52
    p_t3_before_sl: Optional[float] = None  # e.g. 0.36
    raw_probability: Optional[float] = None
    confidence_score: Optional[float] = None  # 0 to 1.0 (decoupled reliability/calibration quality)
    reliability_score: Optional[float] = None # Distinct calibration quality score
    expected_days_min: Optional[int] = None  # e.g. 5
    expected_days_max: Optional[int] = None  # e.g. 10
    prediction_horizon_days: int = 10
    horizon_label: str = "10 trading days"
    prediction_label: str = "P(T1 before SL within 10 trading days)"
    model_version: str = "SwingTree-Ensemble-v2.5-Calibrated"
    calibration_method: str = "Isotonic Regression"
    training_period: str = "2021-01 to 2024-12 Walk-Forward"
    validation_period: str = "2025-01 to Present Out-of-Sample"
    calibration_status: str = "CALIBRATED_ISOTONIC"  # CALIBRATED_ISOTONIC, UNAVAILABLE
    brier_score_calibration: Optional[float] = 0.164
    status: str = "AVAILABLE"  # AVAILABLE, UNAVAILABLE
    reason: Optional[str] = None

class TradeLevels(BaseModel):
    current_price: Optional[float] = None
    reference_entry: Optional[float] = None    # Deterministic reference price for risk/reward calculations
    entry_low: Optional[float] = None
    entry_high: Optional[float] = None
    entry_range_display: Optional[str] = None  # e.g. "₹2,205.00 – ₹2,225.00"
    target_1: Optional[float] = None           # e.g. 2350.00
    target_2: Optional[float] = None           # e.g. 2480.00
    target_3: Optional[float] = None           # e.g. 2620.00
    target_1_display: Optional[str] = None     # e.g. "₹2,350.00 (+6.2%)"
    target_2_display: Optional[str] = None     # e.g. "₹2,480.00 (+12.1%)"
    target_3_display: Optional[str] = None     # e.g. "₹2,620.00 (+18.4%)"
    target_1_method: Optional[str] = "Previous Swing Resistance"
    target_2_method: Optional[str] = "Base Measured Move"
    target_3_method: Optional[str] = None
    target_3_reason: Optional[str] = None
    target_1_r_multiple: Optional[float] = None
    target_2_r_multiple: Optional[float] = None
    target_3_r_multiple: Optional[float] = None
    risk_reward_ratio_t1: Optional[float] = None
    risk_reward_ratio_t2: Optional[float] = None
    risk_reward_ratio_t3: Optional[float] = None
    stop_loss: Optional[float] = None          # e.g. 2145.00
    stop_loss_display: Optional[str] = None    # e.g. "₹2,145.00 (-3.1%)"
    risk_reward_ratio: Optional[float] = None  # Primary R:R (Target 1 vs Stop from Reference Entry)
    risk_per_share: Optional[float] = None     # in ₹
    reward_t1_per_share: Optional[float] = None # in ₹
    target_derivation_method: str = "STRUCTURAL_PIVOTS_AND_ATR"
    stop_method: str = "STRUCTURAL_SWING_LOW"
    stop_reason: str = "Structural swing low"
    levels_reasoning: List[str] = []
    status: str = "AVAILABLE"  # AVAILABLE, UNAVAILABLE


# --- Institutional Risk & Staged Exit Models ---
class StagedExitPlan(BaseModel):
    current_stage: str = "PRE_T1_ACCUMULATION"  # PRE_T1_ACCUMULATION, T1_PROFIT_TAKEN_BREAKEVEN_ACTIVE, T2_PROFIT_TAKEN_RUNNER_ACTIVE, T3_COMPLETED, TIME_DECAY_EXIT_TRIGGERED, STOP_LOSS_EXIT
    stage_label: str = "Pre-Target 1 (Active Accumulation)"
    recommended_action: str = "Hold position. Protective stop active."
    trailing_stop_price: Optional[float] = None
    trailing_stop_display: Optional[str] = None
    trailing_stop_type: str = "INITIAL_SWING_LOW"  # INITIAL_SWING_LOW, BREAKEVEN_BUFFER, EMA_9_TRAIL, EMA_20_TRAIL
    is_risk_free: bool = False
    booked_profit_pct: float = 0.0
    partial_exit_guidance: str = "Target 1 (+4-8%): Book 50% shares -> Shift SL to Breakeven (+0.3% buffer). Target 2 (+8-15%): Book 25% -> Trail 25% with 9 EMA."
    next_milestone_price: Optional[float] = None
    next_milestone_label: Optional[str] = None
    time_stop_days_remaining: int = 10
    time_stop_triggered: bool = False
    time_decay_guidance: Optional[str] = None

class RiskManagementMetrics(BaseModel):
    account_capital: float = 500000.0  # Configurable total capital in ₹
    risk_per_trade_pct: float = 1.0     # 1.0% default risk
    max_rupees_at_risk: float = 5000.0  # in ₹
    reference_entry_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    risk_per_share: Optional[float] = None
    suggested_shares: int = 0
    allocated_capital: float = 0.0
    portfolio_allocation_pct: float = 0.0
    max_single_position_pct: float = 20.0
    is_allocation_capped: bool = False
    expected_value_inr: Optional[float] = None  # (P(Win)*Reward - P(Loss)*Risk)*Shares
    expected_value_r_multiple: Optional[float] = None
    kelly_criterion_pct: Optional[float] = None
    kelly_suggested_shares: Optional[int] = None
    portfolio_heat_contribution_pct: float = 1.0

class PortfolioHeatSummary(BaseModel):
    total_account_equity: float = 500000.0
    total_invested_capital: float = 0.0
    total_open_risk_inr: float = 0.0
    portfolio_heat_pct: float = 0.0  # Sum of % risk across active holdings
    heat_status: str = "OPTIMAL"     # OPTIMAL (<4%), MODERATE (4-6%), DANGEROUS_OVEREXPOSURE (>6%)
    max_recommended_heat_pct: float = 6.0
    available_risk_budget_pct: float = 5.0
    correlated_sector_warnings: List[str] = []
    risk_summary_note: str = "Portfolio heat is within optimal safety boundary (<6%)."

class InstitutionalVolumeQuality(BaseModel):
    delivery_volume_pct_estimate: Optional[float] = None  # Estimated % delivery
    accumulation_distribution_score: float = 50.0        # 0 to 100
    is_institutional_accumulation: bool = False
    volume_dry_up_on_pullback: bool = False
    pocket_pivot_volume_surge: bool = False
    event_risk_warning: Optional[str] = None
    earnings_days_away: Optional[int] = None
    status: str = "AVAILABLE"

class PositionSizingSuggestion(BaseModel):
    portfolio_capital: float
    risk_per_trade_pct: float
    risk_amount_inr: float
    suggested_quantity: int
    allocated_capital_inr: float
    portfolio_allocation_pct: float
    max_sector_exposure_pct: float
    expected_value_inr: Optional[float] = None

class StructuredCatalyst(BaseModel):
    symbol: str
    event_type: str
    direction: str
    materiality: str
    time_horizon: str
    recency: str = "RECENT"
    confidence: float = 0.85
    headline: str
    source: str
    published_at: str
    days_away: Optional[int] = None

class StockOpportunity(BaseModel):
    symbol: str
    company_name: str
    sector: str
    signal: str  # BUY CANDIDATE, WATCH, NO TRADE, BUY MORE, HOLD, REDUCE, SELL, INSUFFICIENT DATA
    market_cap_category: str = "LARGE_CAP"  # LARGE_CAP, MID_CAP, SMALL_CAP
    market_cap_rank: Optional[int] = None
    classification_source: str = "SEBI/AMFI Semiannual Framework"
    classification_date: Optional[str] = "2024-12-31"
    opportunity_score: Optional[float] = None  # 0 to 100 Normalized Score
    portfolio_fit_score: Optional[float] = None  # 0 to 100
    current_price: Optional[float] = None
    daily_change_pct: Optional[float] = None
    setup_type: str = "NONE"
    setup_quality_score: Optional[float] = None
    levels: TradeLevels
    ml_probability: MLProbabilityMetrics
    factor_scores: FactorScores
    relative_strength: RelativeStrengthMetrics
    volume_metrics: VolumeProfileMetrics
    candle_confirmation_score: Optional[float] = None
    catalysts: List[StructuredCatalyst] = []
    catalyst_score: Optional[float] = None
    position_sizing: Optional[PositionSizingSuggestion] = None
    risk_metrics: Optional[RiskManagementMetrics] = None
    volume_quality: Optional[InstitutionalVolumeQuality] = None
    composite_rank_score: Optional[float] = None
    ranking_version: str = "MF-MultiCap-Quant-v4.0"
    invalidation_condition: Optional[str] = None
    why_this_setup: List[str] = []
    watch_reasons: List[str] = []
    failure_reasons: List[str] = []
    risks: List[str] = []
    data_quality: Optional[DataQualityReport] = None
    data_timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketCapCategoryResult(BaseModel):
    category: str  # LARGE_CAP, MID_CAP, SMALL_CAP
    label: str
    market_cap_rank_range: str  # "1-100", "101-250", "251+"
    classification_source: str = "SEBI/AMFI Semiannual Framework"
    classification_date: Optional[str] = "2024-12-31"
    total_scanned: int = 0
    qualified_count: int = 0
    near_misses_count: int = 0
    survivors_by_stage: Dict[str, int] = {}
    primary_bottleneck: Optional[str] = None
    candidates: List[StockOpportunity] = []  # Top 0 to 5 qualified BUY opportunities
    near_misses: List[StockOpportunity] = []  # Top near-misses for watchlist

class NearMissesGroup(BaseModel):
    large_cap: List[StockOpportunity] = []
    mid_cap: List[StockOpportunity] = []
    small_cap: List[StockOpportunity] = []

class ScannerScanResponse(BaseModel):
    large_cap: MarketCapCategoryResult
    mid_cap: MarketCapCategoryResult
    small_cap: MarketCapCategoryResult
    near_misses: NearMissesGroup
    total_qualified_count: int = 0  # Total BUY Candidates across all categories (max 15)
    total_near_misses_count: int = 0
    opportunities: List[StockOpportunity] = []  # Flattened top recommendations (max 15)
    buy_candidates_count: int = 0
    near_misses_count: int = 0
    scan_timestamp: datetime
    total_universe_scanned: int
    survivors_by_stage: Dict[str, int] = {}
    primary_bottleneck: Optional[str] = None
    secondary_rejection_summary: Optional[Dict[str, int]] = None
    passed_liquidity_filter: int = 0
    passed_technical_filter: int = 0
    passed_ml_filter: int = 0
    market_regime: str
    market_regime_policy: MarketRegimePolicy
    is_abstention: bool  # True if total_qualified_count == 0 or regime prohibits new longs
    abstention_reason: Optional[str] = None
    ranking_version: str = "MF-MultiCap-Quant-v4.0"
    configured_weights: Dict[str, float] = {}
    configured_probability_threshold: float = 0.58
    configured_min_rr: float = 1.8

# --- Portfolio & Thesis Models ---
class HoldingCreate(BaseModel):
    symbol: str
    quantity: int
    buy_price: float
    purchase_date: date
    notes: Optional[str] = None

class HoldingUpdate(BaseModel):
    quantity: Optional[int] = None
    buy_price: Optional[float] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None

class HoldingAnalysis(BaseModel):
    id: int
    symbol: str
    company_name: str
    sector: str
    quantity: int
    buy_price: float
    purchase_date: date
    current_price: Optional[float] = None
    total_invested: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    signal: str  # BUY MORE, HOLD, WATCH, REDUCE, SELL, INSUFFICIENT DATA
    thesis_status: str  # STRENGTHENING, STABLE, WEAKENING, BROKEN
    thesis_points: List[str] = []
    invalidation_triggers: List[str] = []
    time_decay_warning: Optional[str] = None
    holding_days_elapsed: int = 0
    expected_holding_period: str = "5–10 trading days"
    risks: List[str] = []
    levels: TradeLevels
    ml_probability: MLProbabilityMetrics
    staged_exit_plan: Optional[StagedExitPlan] = None
    risk_metrics: Optional[RiskManagementMetrics] = None
    volume_quality: Optional[InstitutionalVolumeQuality] = None
    factor_scores: Optional[FactorScores] = None
    relative_strength_20d: Optional[float] = None
    volume_condition: str = "Normal"
    data_quality: Optional[DataQualityReport] = None
    last_evaluated_at: datetime

class PortfolioSummaryResponse(BaseModel):
    total_invested: float
    current_value: float
    total_pnl: float
    total_pnl_pct: float
    holdings_count: int
    strengthening_count: int
    stable_count: int
    weakening_count: int
    broken_count: int
    sector_exposure_breakdown: Dict[str, float]
    holdings: List[HoldingAnalysis]
    portfolio_heat: Optional[PortfolioHeatSummary] = None
    what_changed_feed: List[str]
    last_updated: datetime

# --- Stock Detail Analysis ---
class StockFullAnalysisResponse(BaseModel):
    symbol: str
    company_name: str
    sector: str
    current_price: Optional[float] = None
    daily_change: Optional[float] = None
    daily_change_pct: Optional[float] = None
    signal: str  # BUY CANDIDATE, WATCH, HOLD, REDUCE, SELL, INSUFFICIENT DATA, NO TRADE
    market_regime: str
    setup_type: str
    reference_entry_rule: str = "Conservative upper boundary of recommended entry zone for long swings"
    levels: TradeLevels
    ml_probability: MLProbabilityMetrics
    staged_exit_plan: Optional[StagedExitPlan] = None
    risk_metrics: Optional[RiskManagementMetrics] = None
    volume_quality: Optional[InstitutionalVolumeQuality] = None
    position_sizing: Optional[PositionSizingSuggestion] = None
    factor_scores: FactorScores
    volume_metrics: VolumeProfileMetrics
    technical_indicators: TechnicalIndicators
    candles: List[Candle] = []
    candle_patterns: List[CandlestickPattern] = []
    candle_confirmation_score: Optional[float] = None
    why_this_setup: List[str] = []
    risks: List[str] = []
    catalysts: List[StructuredCatalyst] = []
    catalyst_score: Optional[float] = None
    relative_strength: RelativeStrengthMetrics
    fundamental_snapshot: Dict[str, Any] = {}
    invalidation_condition: Optional[str] = None
    snapshot: Optional[MarketDataSnapshot] = None
    data_quality: DataQualityReport
    data_source: str = "Upstox API v2 Live Feed"
    is_live: bool = True
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Prediction Journal & Audit Models ---
class SignalAuditRecord(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    signal: str
    setup_type: str
    entry_low: Optional[float] = None
    entry_high: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    target_3: Optional[float] = None
    stop_loss: Optional[float] = None
    probability_t1: Optional[float] = None
    market_regime: str
    sector: str
    model_version: str
    ranking_version: str
    holding_days_max: int
    outcome_status: str  # ACTIVE, T1_HIT, T2_HIT, T3_HIT, STOP_HIT, EXPIRED_TIMED_OUT
    mfe_pct: float
    mae_pct: float
    actual_holding_days: Optional[int] = None
    return_pct: Optional[float] = None
    first_hit_barrier: Optional[str] = None

class HistoricalScanSummary(BaseModel):
    id: int
    scan_date: date
    created_at: datetime
    market_regime: str
    total_qualified_count: int
    large_cap_count: int
    mid_cap_count: int
    small_cap_count: int
    total_scanned: int
    top_symbols: List[str] = []
