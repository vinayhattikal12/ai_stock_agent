export interface MarketIndexQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
}

export interface MarketBreadth {
  advances: number;
  declines: number;
  unchanged: number;
  ad_ratio: number;
  pct_above_20_ema: number;
  pct_above_50_ema: number;
  pct_above_200_ema: number;
  highs_52w_count?: number;
  lows_52w_count?: number;
}

export interface SectorPerformance {
  sector_name: string;
  symbol: string;
  change_percent_1d: number;
  change_percent_5d: number;
  change_percent_20d: number;
  change_percent_50d: number;
  change_percent_100d: number;
  change_percent_6m: number;
  momentum_score: number;
  relative_strength_vs_nifty: number;
  trend: string;
  sector_breadth_pct_above_50ema: number;
  top_driver?: string;
  rank: number;
}

export interface MarketRegimePolicy {
  regime: string;
  status_label: string;
  description: string;
  min_probability_threshold: number;
  min_risk_reward_ratio: number;
  max_opportunities: number;
  position_size_multiplier: number;
  setup_quality_requirement: string;
  allow_new_longs: boolean;
}

export interface MarketMoverItem {
  symbol: string;
  company_name: string;
  sector: string;
  price: number;
  change_percent: number;
  gap_percent?: number;
  volume: number;
  rvol?: number;
  movement_type: 'TOP_GAINER' | 'TOP_LOSER' | 'UNUSUAL_VOLUME' | 'GAP_UP' | 'GAP_DOWN';
  catalyst_type: 'STOCK_SPECIFIC' | 'SECTOR_THEME' | 'BROAD_MARKET' | 'UNCLASSIFIED';
  catalyst_headline?: string;
  sector_change_percent?: number;
  why_moved: string;
  status: string;
}

export interface TodaysMoversResponse {
  scan_timestamp: string;
  total_market_scanned: number;
  top_gainers: MarketMoverItem[];
  top_losers: MarketMoverItem[];
  unusual_volume: MarketMoverItem[];
  gap_movers: MarketMoverItem[];
  market_breadth_summary?: MarketBreadth;
}

export interface MarketStatusResponse {
  status_label: string;
  regime: 'STRONG_BULL' | 'BULL' | 'NEUTRAL' | 'RECOVERY' | 'BEAR' | 'STRESS';
  regime_policy: MarketRegimePolicy;
  nifty: MarketIndexQuote;
  bank_nifty: MarketIndexQuote;
  india_vix: MarketIndexQuote;
  breadth: MarketBreadth;
  strong_sectors: SectorPerformance[];
  weak_sectors: SectorPerformance[];
  sector_rotation_matrix: SectorPerformance[];
  major_events: string[];
  last_updated: string;
  is_live_data: boolean;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  open_interest?: number;
}

export interface CandlestickPattern {
  name: string;
  pattern_type: 'BULLISH' | 'BEARISH' | 'INDECISION';
  reliability: 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  confirmation_score?: number;
}

export interface DataQualityReport {
  is_valid: boolean;
  status: 'AVAILABLE' | 'PARTIAL' | 'UNAVAILABLE' | 'INVALID' | 'STALE';
  rejection_reason?: string;
  candle_count: number;
  min_required_candles: number;
  first_candle_date?: string;
  last_candle_date?: string;
  exchange: string;
  instrument_key?: string;
  isin?: string;
  validated_at: string;
}

export interface TechnicalIndicators {
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  ema_20?: number;
  ema_50?: number;
  ema_200?: number;
  rsi_14?: number;
  macd_line?: number;
  macd_signal?: number;
  macd_hist?: number;
  atr_14?: number;
  adx_14?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  supertrend?: number;
  supertrend_direction?: string;
  support_levels?: number[];
  resistance_levels?: number[];
  status?: string;
}

export interface MarketDataSnapshot {
  symbol: string;
  exchange: string;
  instrument_key: string;
  isin?: string;
  quote_price?: number;
  previous_close?: number;
  open?: number;
  high?: number;
  low?: number;
  volume?: number;
  quote_timestamp?: string;
  latest_candle_timestamp?: string;
  historical_candle_count: number;
  data_source: string;
  data_freshness: string;
  data_quality_status: string;
  provenance_note?: string;
}

export interface FactorContributionItem {
  factor_name: string;
  raw_value?: string;
  normalized_score?: number;
  weight_pct: number;
  weighted_contribution?: number;
  rationale?: string;
}

export interface FactorScores {
  momentum_score?: number;
  relative_strength_score?: number;
  trend_score?: number;
  setup_quality_score?: number;
  volume_score?: number;
  quality_score?: number;
  catalyst_score?: number;
  volatility_score?: number;
  value_score?: number;
  liquidity_score?: number;
  overall_factor_rank?: number;
  factor_breakdown?: FactorContributionItem[];
  status?: string;
}

export interface RelativeStrengthMetrics {
  excess_return_5d?: number;
  excess_return_20d?: number;
  excess_return_50d?: number;
  excess_return_100d?: number;
  mansfield_rs_20d?: number;
  mansfield_rs_50d?: number;
  mansfield_rs_100d?: number;
  sector_relative_strength_20d?: number;
  market_relative_strength_20d?: number;
  rs_trend: 'EXPANDING' | 'FLAT' | 'DETERIORATING';
  status?: string;
}

export interface VolumeProfileMetrics {
  rvol_20d?: number;
  volume_5d_vs_20d_ratio?: number;
  breakout_volume_surge?: number;
  volume_trend: 'ACCUMULATION' | 'DISTRIBUTION' | 'CONTRACTION' | 'NEUTRAL';
  avg_turnover_cr_20d?: number;
  is_volume_confirmed: boolean;
  status?: string;
}

export interface MLProbabilityMetrics {
  p_t1_before_sl?: number;
  p_t2_before_sl?: number;
  p_t3_before_sl?: number;
  raw_probability?: number;
  confidence_score?: number;
  reliability_score?: number;
  expected_days_min?: number;
  expected_days_max?: number;
  prediction_horizon_days: number;
  horizon_label?: string;
  prediction_label?: string;
  model_version: string;
  calibration_method?: string;
  training_period: string;
  validation_period: string;
  calibration_status: string;
  brier_score_calibration?: number;
  status?: string;
  reason?: string;
}

export interface TradeLevels {
  current_price?: number;
  reference_entry?: number;
  entry_low?: number;
  entry_high?: number;
  entry_range_display?: string;
  target_1?: number;
  target_2?: number;
  target_3?: number;
  target_1_display?: string;
  target_2_display?: string;
  target_3_display?: string;
  target_1_method?: string;
  target_2_method?: string;
  target_3_method?: string;
  target_3_reason?: string;
  target_1_r_multiple?: number;
  target_2_r_multiple?: number;
  target_3_r_multiple?: number;
  risk_reward_ratio_t1?: number;
  risk_reward_ratio_t2?: number;
  risk_reward_ratio_t3?: number;
  stop_loss?: number;
  stop_loss_display?: string;
  risk_reward_ratio?: number;
  risk_per_share?: number;
  reward_t1_per_share?: number;
  target_derivation_method?: string;
  stop_method: string;
  stop_reason: string;
  levels_reasoning: string[];
  status?: string;
}


export interface StagedExitPlan {
  current_stage: string;
  stage_label: string;
  recommended_action: string;
  trailing_stop_price?: number;
  trailing_stop_display?: string;
  trailing_stop_type: string;
  is_risk_free: boolean;
  booked_profit_pct: number;
  partial_exit_guidance: string;
  next_milestone_price?: number;
  next_milestone_label?: string;
  time_stop_days_remaining: number;
  time_stop_triggered: boolean;
  time_decay_guidance?: string;
}

export interface RiskManagementMetrics {
  account_capital: number;
  risk_per_trade_pct: number;
  max_rupees_at_risk: number;
  reference_entry_price?: number;
  stop_loss_price?: number;
  risk_per_share?: number;
  suggested_shares: number;
  allocated_capital: number;
  portfolio_allocation_pct: number;
  max_single_position_pct: number;
  is_allocation_capped: boolean;
  expected_value_inr?: number;
  expected_value_r_multiple?: number;
  kelly_criterion_pct?: number;
  kelly_suggested_shares?: number;
  portfolio_heat_contribution_pct: number;
}

export interface PortfolioHeatSummary {
  total_account_equity: number;
  total_invested_capital: number;
  total_open_risk_inr: number;
  portfolio_heat_pct: number;
  heat_status: 'OPTIMAL' | 'MODERATE' | 'DANGEROUS_OVEREXPOSURE';
  max_recommended_heat_pct: number;
  available_risk_budget_pct: number;
  correlated_sector_warnings: string[];
  risk_summary_note: string;
}

export interface InstitutionalVolumeQuality {
  delivery_volume_pct_estimate?: number;
  accumulation_distribution_score: number;
  is_institutional_accumulation: boolean;
  volume_dry_up_on_pullback: boolean;
  pocket_pivot_volume_surge: boolean;
  event_risk_warning?: string;
  earnings_days_away?: number;
  status?: string;
}

export interface PositionSizingSuggestion {
  portfolio_capital: number;
  risk_per_trade_pct: number;
  risk_amount_inr: number;
  suggested_quantity: number;
  allocated_capital_inr: number;
  portfolio_allocation_pct: number;
  max_sector_exposure_pct: number;
  expected_value_inr?: number;
}

export interface StructuredCatalyst {
  symbol: string;
  event_type: string;
  direction: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  materiality: 'HIGH' | 'MEDIUM' | 'LOW';
  time_horizon: 'SHORT' | 'MEDIUM' | 'LONG';
  recency?: string;
  confidence?: number;
  headline: string;
  source: string;
  published_at: string;
  days_away?: number;
}

export interface StockOpportunity {
  symbol: string;
  company_name: string;
  sector: string;
  signal: 'BUY CANDIDATE' | 'WATCH' | 'NO TRADE' | 'BUY MORE' | 'HOLD' | 'REDUCE' | 'SELL' | 'INSUFFICIENT DATA';
  market_cap_category: 'LARGE_CAP' | 'MID_CAP' | 'SMALL_CAP';
  market_cap_rank?: number;
  classification_source?: string;
  classification_date?: string;
  opportunity_score?: number;
  portfolio_fit_score?: number;
  current_price?: number;
  daily_change_pct?: number;
  setup_type: string;
  setup_quality_score?: number;
  levels: TradeLevels;
  ml_probability: MLProbabilityMetrics;
  factor_scores: FactorScores;
  relative_strength: RelativeStrengthMetrics;
  volume_metrics: VolumeProfileMetrics;
  candle_confirmation_score?: number;
  catalysts: StructuredCatalyst[];
  catalyst_score?: number;
  position_sizing?: PositionSizingSuggestion;
  risk_metrics?: RiskManagementMetrics;
  volume_quality?: InstitutionalVolumeQuality;
  composite_rank_score?: number;
  ranking_version: string;
  invalidation_condition?: string;
  why_this_setup: string[];
  watch_reasons: string[];
  failure_reasons: string[];
  risks: string[];
  scan_streak_days?: number;
  is_multi_day_runner?: boolean;
  streak_description?: string;
  data_quality?: DataQualityReport;
  data_timestamp?: string;
  created_at: string;
}

export interface MarketCapCategoryResult {
  category: 'LARGE_CAP' | 'MID_CAP' | 'SMALL_CAP';
  label: string;
  market_cap_rank_range: string;
  classification_source: string;
  classification_date?: string;
  total_scanned: number;
  qualified_count: number;
  near_misses_count: number;
  survivors_by_stage: Record<string, number>;
  primary_bottleneck?: string;
  candidates: StockOpportunity[];
  near_misses: StockOpportunity[];
}

export interface NearMissesGroup {
  large_cap: StockOpportunity[];
  mid_cap: StockOpportunity[];
  small_cap: StockOpportunity[];
}

export interface ScannerScanResponse {
  large_cap: MarketCapCategoryResult;
  mid_cap: MarketCapCategoryResult;
  small_cap: MarketCapCategoryResult;
  near_misses: NearMissesGroup;
  total_qualified_count: number;
  total_near_misses_count: number;
  top_conviction_picks?: StockOpportunity[];
  opportunities: StockOpportunity[];
  buy_candidates_count: number;
  near_misses_count: number;
  scan_timestamp: string;
  total_universe_scanned: number;
  survivors_by_stage: Record<string, number>;
  primary_bottleneck?: string;
  secondary_rejection_summary?: Record<string, number>;
  passed_liquidity_filter: number;
  passed_technical_filter: number;
  passed_ml_filter: number;
  market_regime: string;
  market_regime_policy: MarketRegimePolicy;
  is_abstention: boolean;
  abstention_reason?: string;
  ranking_version: string;
  configured_weights: Record<string, number>;
  configured_probability_threshold: number;
  configured_min_rr: number;
}

export interface HoldingAnalysis {
  id: number;
  symbol: string;
  company_name: string;
  sector: string;
  quantity: number;
  buy_price: number;
  purchase_date: string;
  current_price?: number;
  total_invested: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  signal: string;
  thesis_status: string;
  thesis_points: string[];
  invalidation_triggers: string[];
  time_decay_warning?: string;
  holding_days_elapsed: number;
  expected_holding_period: string;
  risks: string[];
  levels: TradeLevels;
  ml_probability: MLProbabilityMetrics;
  staged_exit_plan?: StagedExitPlan;
  risk_metrics?: RiskManagementMetrics;
  volume_quality?: InstitutionalVolumeQuality;
  factor_scores?: FactorScores;
  relative_strength_20d?: number;
  volume_condition: string;
  data_quality?: DataQualityReport;
  last_evaluated_at: string;
}

export interface PortfolioSummaryResponse {
  total_invested: number;
  current_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  holdings_count: number;
  strengthening_count: number;
  stable_count: number;
  weakening_count: number;
  broken_count: number;
  sector_exposure_breakdown: Record<string, number>;
  holdings: HoldingAnalysis[];
  portfolio_heat?: PortfolioHeatSummary;
  what_changed_feed: string[];
  last_updated: string;
}

export interface StockFullAnalysisResponse {
  symbol: string;
  company_name: string;
  sector: string;
  current_price?: number;
  daily_change?: number;
  daily_change_pct?: number;
  signal: string;
  market_regime: string;
  setup_type: string;
  reference_entry_rule?: string;
  levels: TradeLevels;
  ml_probability: MLProbabilityMetrics;
  staged_exit_plan?: StagedExitPlan;
  risk_metrics?: RiskManagementMetrics;
  volume_quality?: InstitutionalVolumeQuality;
  position_sizing?: PositionSizingSuggestion;
  factor_scores: FactorScores;
  volume_metrics: VolumeProfileMetrics;
  technical_indicators: TechnicalIndicators;
  candles: Candle[];
  candle_patterns: CandlestickPattern[];
  candle_confirmation_score?: number;
  why_this_setup: string[];
  risks: string[];
  catalysts: StructuredCatalyst[];
  catalyst_score?: number;
  relative_strength: RelativeStrengthMetrics;
  fundamental_snapshot: Record<string, any>;
  invalidation_condition?: string;
  snapshot?: MarketDataSnapshot;
  data_quality: DataQualityReport;
  data_source: string;
  is_live: boolean;
  evaluated_at: string;
}


export interface SignalAuditRecord {
  id: number;
  timestamp: string;
  symbol: string;
  signal: string;
  setup_type: string;
  entry_low?: number;
  entry_high?: number;
  target_1?: number;
  target_2?: number;
  target_3?: number;
  stop_loss?: number;
  probability_t1?: number;
  market_regime: string;
  sector: string;
  model_version: string;
  ranking_version: string;
  holding_days_max: number;
  outcome_status: string;
  mfe_pct: number;
  mae_pct: number;
  actual_holding_days?: number;
  return_pct?: number;
  first_hit_barrier?: string;
}

export interface HistoricalScanSummary {
  id: number;
  scan_date: string;
  created_at: string;
  market_regime: string;
  total_qualified_count: number;
  large_cap_count: number;
  mid_cap_count: number;
  small_cap_count: number;
  total_scanned: number;
  top_symbols: string[];
}
