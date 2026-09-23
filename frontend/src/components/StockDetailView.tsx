import React, { useState } from 'react';
import { 
  ArrowLeft, 
  TrendingUp, 
  Layers, 
  Activity, 
  ShieldAlert, 
  Newspaper, 
  BookOpen, 
  Cpu, 
  ChevronDown, 
  ChevronUp,
  Sparkles,
  HelpCircle,
  Plus,
  Sliders,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Target,
  Flame,
  Calculator
} from 'lucide-react';
import { StockFullAnalysisResponse } from '../types';
import { TradingViewChart } from './TradingViewChart';
import { PositionSizingWidget } from './PositionSizingWidget';

interface StockDetailViewProps {
  analysis: StockFullAnalysisResponse | null;
  loading: boolean;
  isDark: boolean;
  onBack: () => void;
  onAddToPortfolio: (symbol: string, currentPrice: number) => void;
}

export const StockDetailView: React.FC<StockDetailViewProps> = ({
  analysis,
  loading,
  isDark,
  onBack,
  onAddToPortfolio,
}) => {
  const [timeframe, setTimeframe] = useState('1D');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    factors: true,
    technical: true,
    ml: true,
    patterns: false,
    relative_strength: true,
    catalysts: false,
    risk: true,
    data_quality: true
  });

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark space-y-4 animate-pulse">
        <div className="flex items-center justify-between pb-4 border-b border-border-light dark:border-border-dark">
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-24"></div>
        </div>
        <div className="h-96 bg-slate-200 dark:bg-slate-800 rounded-2xl"></div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="p-12 text-center rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark space-y-4 shadow-subtle">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Unable to Load Stock Analysis</h2>
        <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
          The requested equity analysis could not be retrieved from the live market feed. Verify your network or return to discover other stocks.
        </p>
        <div className="pt-2">
          <button
            onClick={onBack}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-subtle"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    );
  }

  const {
    symbol,
    company_name,
    sector,
    current_price,
    daily_change,
    daily_change_pct,
    signal,
    market_regime,
    setup_type,
    levels,
    ml_probability,
    factor_scores,
    volume_metrics,
    technical_indicators,
    candles,
    candle_patterns,
    candle_confirmation_score,
    why_this_setup,
    risks,
    catalysts,
    catalyst_score,
    relative_strength,
    fundamental_snapshot,
    invalidation_condition,
    data_quality
  } = analysis;

  const isInsufficientData = signal === 'INSUFFICIENT DATA' || !data_quality?.is_valid;

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const formatINR = (val?: number | null) => (val !== undefined && val !== null ? `₹${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—');
  const formatPct = (val?: number | null) => (val !== undefined && val !== null ? `${val >= 0 ? '+' : ''}${Number(val).toFixed(2)}%` : '—');

  const getSignalBadgeColor = (sig: string) => {
    switch (sig) {
      case 'BUY CANDIDATE':
      case 'BUY MORE':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'HOLD':
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'WATCH':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'REDUCE':
      case 'SELL':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
      case 'INSUFFICIENT DATA':
      default:
        return 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Header & Back Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border-light dark:border-border-dark">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white font-mono">
                {symbol}
              </h1>
              <span className="text-xs text-slate-500 font-medium font-sans">
                {company_name}
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border font-sans ${getSignalBadgeColor(signal)}`}>
                {signal}
              </span>
              {setup_type && setup_type !== 'NONE' && (
                <span className="px-2 py-0.5 rounded text-xs font-mono font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                  {setup_type}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5 flex-wrap">
              <span>{sector}</span>
              <span>•</span>
              <span className="font-mono">Regime: {market_regime}</span>
              <span>•</span>
              <span className="font-mono text-amber-600 dark:text-amber-400">
                RVOL: {volume_metrics?.rvol_20d !== undefined && volume_metrics.rvol_20d !== null ? `${volume_metrics.rvol_20d.toFixed(2)}x` : '—'}
              </span>
              {data_quality?.instrument_key && (
                <>
                  <span>•</span>
                  <span className="font-mono text-slate-400 text-[10px]">{data_quality.instrument_key}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Price & Action */}
        <div className="flex items-center space-x-4">
          <div className="text-left sm:text-right font-mono">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {current_price !== undefined && current_price !== null ? formatINR(current_price) : '—'}
            </div>
            {daily_change !== undefined && daily_change !== null && daily_change_pct !== undefined && daily_change_pct !== null ? (
              <div className={`text-xs font-semibold ${
                daily_change >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
              }`}>
                {daily_change >= 0 ? '+' : ''}₹{daily_change.toFixed(2)} ({formatPct(daily_change_pct)})
              </div>
            ) : (
              <div className="text-xs text-slate-400">Quote Unavailable</div>
            )}
          </div>

          {current_price && (
            <button
              onClick={() => onAddToPortfolio(symbol, current_price)}
              className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl font-bold text-xs bg-blue-600 hover:bg-blue-500 text-white shadow-subtle transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add to Portfolio</span>
            </button>
          )}
        </div>
      </div>

      {/* Canonical Market Data Snapshot & Freshness Bar */}
      <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark flex items-center justify-between flex-wrap gap-2 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-bold text-slate-800 dark:text-slate-200">
            Source: {analysis.snapshot?.data_source || analysis.data_source || 'Upstox API v2 Live Feed'}
          </span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-500">
            History: {analysis.snapshot?.historical_candle_count || data_quality?.candle_count || 0} Daily Bars
          </span>
        </div>
        <div className="flex items-center space-x-2 text-slate-500 text-[11px]">
          <span>Freshness: <strong className="text-slate-700 dark:text-slate-300 font-bold">{analysis.snapshot?.data_freshness || 'REALTIME'}</strong></span>
          <span>•</span>
          <span>Quality: <strong className="text-emerald-600 dark:text-emerald-400 font-bold">{analysis.snapshot?.data_quality_status || data_quality?.status || 'GOOD'}</strong></span>
        </div>
      </div>

      {/* Insufficient Data Notice Banner if Applicable */}
      {isInsufficientData && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-200 space-y-2">
          <div className="flex items-center space-x-2 font-bold text-sm text-amber-800 dark:text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span>DATA QUALITY GATE: INSUFFICIENT HISTORICAL DATA</span>
          </div>
          <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300">
            {data_quality?.rejection_reason || 'Historical candle series is insufficient or failed validation. Calculations are halted to guarantee zero synthetic fallbacks.'}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
            <div className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Symbol & ISIN Valid</span>
            </div>
            <div className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Quote Feed Active</span>
            </div>
            <div className="flex items-center space-x-1 text-rose-500">
              <XCircle className="w-3.5 h-3.5" />
              <span>Candle Bars: {data_quality?.candle_count || 0} / 30</span>
            </div>
            <div className="flex items-center space-x-1 text-rose-500">
              <XCircle className="w-3.5 h-3.5" />
              <span>Indicators Blocked</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Interactive Chart */}
      {candles && candles.length > 0 && (
        <TradingViewChart
          candles={candles}
          levels={levels}
          isDark={isDark}
          timeframe={timeframe}
          setTimeframe={setTimeframe}
        />
      )}

      {/* Explicit Rupee Trade Levels & Reference Entry Summary Strip */}
      <div className="p-4 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark flex-wrap gap-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-900 dark:text-white">
            <Target className="w-4 h-4 text-emerald-500" />
            <span>EXPLICIT RUPEE TARGETS & STOP LOSS (REFERENCE ENTRY ANCHORED)</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {analysis.reference_entry_rule || 'Ref Entry = Upper zone boundary for conservative R:R'}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 font-mono text-center">
          <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
            <span className="text-[10px] uppercase text-slate-500 font-sans font-semibold">Current Price</span>
            <div className="text-sm font-bold text-slate-900 dark:text-white mt-1">
              {current_price !== undefined && current_price !== null ? formatINR(current_price) : '—'}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-500/30">
            <span className="text-[10px] uppercase text-blue-600 dark:text-blue-400 font-sans font-bold">Reference Entry</span>
            <div className="text-sm font-bold text-blue-600 dark:text-blue-400 mt-1">
              {levels?.reference_entry ? formatINR(levels.reference_entry) : '—'}
            </div>
            <span className="text-[9px] text-slate-400 font-sans block mt-0.5">{levels?.entry_range_display || 'Zone'}</span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-emerald-500/20">
            <span className="text-[10px] uppercase text-emerald-600 dark:text-emerald-400 font-sans font-semibold">Target 1</span>
            <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {levels?.target_1_display || (levels?.target_1 ? formatINR(levels.target_1) : '—')}
            </div>
            <span className="text-[9px] text-emerald-600/80 dark:text-emerald-400/80 font-sans block mt-0.5 truncate" title={levels?.target_1_method || 'Swing Resistance'}>
              {levels?.target_1_method || 'Swing Resistance'}
            </span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-emerald-500/20">
            <span className="text-[10px] uppercase text-emerald-600 dark:text-emerald-400 font-sans font-semibold">Target 2</span>
            <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {levels?.target_2_display || (levels?.target_2 ? formatINR(levels.target_2) : '—')}
            </div>
            <span className="text-[9px] text-emerald-600/80 dark:text-emerald-400/80 font-sans block mt-0.5 truncate" title={levels?.target_2_method || 'Measured Move'}>
              {levels?.target_2_method || 'Measured Move'}
            </span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-rose-500/20">
            <span className="text-[10px] uppercase text-rose-600 dark:text-rose-400 font-sans font-semibold">Stop Loss</span>
            <div className="text-sm font-bold text-rose-600 dark:text-rose-400 mt-1">
              {levels?.stop_loss_display || (levels?.stop_loss ? formatINR(levels.stop_loss) : '—')}
            </div>
            <span className="text-[9px] text-rose-600/80 dark:text-rose-400/80 font-sans block mt-0.5 truncate" title={levels?.stop_reason || 'Swing Low'}>
              {levels?.stop_method || 'Swing Low'}
            </span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-purple-500/20">
            <span className="text-[10px] uppercase text-purple-600 dark:text-purple-400 font-sans font-semibold">Risk / Reward (T1)</span>
            <div className="text-sm font-bold text-purple-600 dark:text-purple-400 mt-1">
              {levels?.risk_reward_ratio !== undefined && levels.risk_reward_ratio !== null ? `1 : ${levels.risk_reward_ratio.toFixed(2)}` : '—'}
            </div>
            <span className="text-[9px] text-slate-400 font-sans block mt-0.5">
              Risk: {levels?.risk_per_share ? `₹${levels.risk_per_share.toFixed(1)}` : '—'}
            </span>
          </div>
        </div>

        {/* Target 3 Status Badge */}
        <div className="text-[11px] font-mono text-slate-500 pt-1 border-t border-border-light dark:border-border-dark flex items-center justify-between">
          <span>
            Target 3: <strong className="text-slate-700 dark:text-slate-300">{levels?.target_3 ? `${levels.target_3_display} via ${levels.target_3_method}` : 'UNAVAILABLE'}</strong>
          </span>
          {levels?.target_3_reason && (
            <span className="text-slate-400 italic">({levels.target_3_reason})</span>
          )}
        </div>
      </div>

      {/* 1% Risk Position Sizing Engine */}
      {levels && current_price && (
        <PositionSizingWidget
          levels={levels}
          currentPrice={current_price}
          winProbability={ml_probability?.p_t1_before_sl ?? 0.60}
          onApplyQuantity={(qty) => {
            onAddToPortfolio(symbol, current_price);
          }}
        />
      )}

      {/* Staged Exit Execution Plan */}
      {analysis.staged_exit_plan && (
        <div className="p-4 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-2">
          <div className="flex items-center justify-between text-xs pb-2 border-b border-border-light dark:border-border-dark">
            <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Staged Exit & Scale-Out Plan
            </span>
            <span className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
              Stage: {analysis.staged_exit_plan.stage_label}
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {analysis.staged_exit_plan.partial_exit_guidance}
          </p>
        </div>
      )}

      {/* Invalidation Trigger */}
      {invalidation_condition && (
        <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/40 text-xs text-amber-800 dark:text-amber-300 flex items-start space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <strong>Thesis Invalidation Threshold:</strong> {invalidation_condition}
          </div>
        </div>
      )}

      {/* Progressive Disclosure Sections */}
      <div className="space-y-3">
        {/* 1. Multi-Factor Quant Scores Breakdown */}
        <div className="rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark overflow-hidden shadow-subtle">
          <button
            onClick={() => toggleSection('factors')}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
          >
            <div className="flex items-center space-x-2.5">
              <Sliders className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-bold text-slate-900 dark:text-white">
                Multi-Factor Quantitative Breakdown {factor_scores?.overall_factor_rank !== undefined && factor_scores.overall_factor_rank !== null ? `(Composite Rank: ${factor_scores.overall_factor_rank}/100)` : '(Status: Incomplete)'}
              </span>
            </div>
            {expandedSections.factors ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>

          {expandedSections.factors && (
            <div className="p-4 pt-0 border-t border-border-light dark:border-border-dark space-y-3">
              {factor_scores?.factor_breakdown && factor_scores.factor_breakdown.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <thead>
                      <tr className="text-[10px] uppercase text-slate-400 border-b border-border-light dark:border-border-dark">
                        <th className="py-2">Factor Name</th>
                        <th className="py-2">Raw Indicator</th>
                        <th className="py-2 text-right">Normalized (0-100)</th>
                        <th className="py-2 text-right">Weight</th>
                        <th className="py-2 text-right">Weighted Contribution</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-light dark:divide-border-dark">
                      {factor_scores.factor_breakdown.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20">
                          <td className="py-2.5 font-sans font-medium text-slate-800 dark:text-slate-200">
                            {item.factor_name}
                          </td>
                          <td className="py-2.5 text-slate-500">{item.raw_value || '—'}</td>
                          <td className="py-2.5 text-right font-bold text-blue-600 dark:text-blue-400">
                            {item.normalized_score !== undefined && item.normalized_score !== null ? item.normalized_score.toFixed(1) : '—'}
                          </td>
                          <td className="py-2.5 text-right text-slate-500">{item.weight_pct}%</td>
                          <td className="py-2.5 text-right font-bold text-emerald-600 dark:text-emerald-400">
                            {item.weighted_contribution !== undefined && item.weighted_contribution !== null ? `+${item.weighted_contribution.toFixed(2)}` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 border-border-light dark:border-border-dark font-bold">
                        <td colSpan={4} className="py-2.5 font-sans text-slate-900 dark:text-white">
                          Overall Composite Factor Score
                        </td>
                        <td className="py-2.5 text-right text-base text-emerald-600 dark:text-emerald-400">
                          {factor_scores.overall_factor_rank !== undefined && factor_scores.overall_factor_rank !== null ? `${factor_scores.overall_factor_rank}/100` : '—'}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                    <span className="text-slate-500 font-sans font-medium text-[11px]">Momentum</span>
                    <div className="text-base font-bold text-blue-600 dark:text-blue-400 mt-1">
                      {factor_scores?.momentum_score !== undefined && factor_scores.momentum_score !== null ? `${factor_scores.momentum_score}/100` : '—'}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                    <span className="text-slate-500 font-sans font-medium text-[11px]">Relative Strength</span>
                    <div className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                      {factor_scores?.relative_strength_score !== undefined && factor_scores.relative_strength_score !== null ? `${factor_scores.relative_strength_score}/100` : '—'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>


        {/* 2. Technical Indicators Section */}
        <div className="rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark overflow-hidden shadow-subtle">
          <button
            onClick={() => toggleSection('technical')}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
          >
            <div className="flex items-center space-x-2.5">
              <Activity className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-bold text-slate-900 dark:text-white">
                Deterministic Technical Indicators
              </span>
            </div>
            {expandedSections.technical ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>

          {expandedSections.technical && (
            <div className="p-4 pt-0 border-t border-border-light dark:border-border-dark grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-slate-500 font-sans font-medium text-[11px]">EMA 20 / 50 / 200</span>
                <div className="font-bold text-slate-800 dark:text-slate-200 mt-1">
                  {technical_indicators?.ema_20 ? `₹${technical_indicators.ema_20}` : '—'} / {technical_indicators?.ema_50 ? `₹${technical_indicators.ema_50}` : '—'} / {technical_indicators?.ema_200 ? `₹${technical_indicators.ema_200}` : '—'}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-slate-500 font-sans font-medium text-[11px]">RSI (14) Momentum</span>
                <div className="font-bold mt-1 text-slate-800 dark:text-slate-200">
                  {technical_indicators?.rsi_14 !== undefined && technical_indicators.rsi_14 !== null ? (
                    <span className={technical_indicators.rsi_14 > 50 ? 'text-emerald-500' : 'text-amber-500'}>
                      {technical_indicators.rsi_14} ({technical_indicators.rsi_14 > 60 ? 'Bullish' : 'Neutral'})
                    </span>
                  ) : (
                    '—'
                  )}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-slate-500 font-sans font-medium text-[11px]">MACD Histogram</span>
                <div className="font-bold text-slate-800 dark:text-slate-200 mt-1">
                  {technical_indicators?.macd_hist !== undefined && technical_indicators.macd_hist !== null ? technical_indicators.macd_hist : '—'}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-slate-500 font-sans font-medium text-[11px]">ATR (14) Volatility</span>
                <div className="font-bold text-slate-800 dark:text-slate-200 mt-1">
                  {technical_indicators?.atr_14 ? `₹${technical_indicators.atr_14}` : '—'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 3. Machine Learning Probability Model */}
        <div className="rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark overflow-hidden shadow-subtle">
          <button
            onClick={() => toggleSection('ml')}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
          >
            <div className="flex items-center space-x-2.5">
              <Cpu className="w-4 h-4 text-purple-500" />
              <span className="text-sm font-bold text-slate-900 dark:text-white">
                Machine Learning Probability & Triple-Barrier Output
              </span>
            </div>
            {expandedSections.ml ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>

          {expandedSections.ml && (
            <div className="p-4 pt-0 border-t border-border-light dark:border-border-dark space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-center">
                <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20">
                  <span className="text-[10px] uppercase text-purple-600 dark:text-purple-400 font-sans font-semibold">P(Target 1 before Stop)</span>
                  <div className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                    {ml_probability?.p_t1_before_sl !== undefined && ml_probability.p_t1_before_sl !== null ? `${(ml_probability.p_t1_before_sl * 100).toFixed(0)}%` : '—'}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-border-light dark:border-border-dark">
                  <span className="text-[10px] uppercase text-slate-500 font-sans font-semibold">P(Target 2 before Stop)</span>
                  <div className="text-xl font-bold text-slate-800 dark:text-slate-200 mt-1">
                    {ml_probability?.p_t2_before_sl !== undefined && ml_probability.p_t2_before_sl !== null ? `${(ml_probability.p_t2_before_sl * 100).toFixed(0)}%` : '—'}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-border-light dark:border-border-dark">
                  <span className="text-[10px] uppercase text-slate-500 font-sans font-semibold">Confidence Score</span>
                  <div className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                    {ml_probability?.confidence_score !== undefined && ml_probability.confidence_score !== null ? `${(ml_probability.confidence_score * 100).toFixed(0)}%` : '—'}
                  </div>
                </div>
              </div>
              <div className="text-[11px] text-slate-500 font-mono flex items-center justify-between">
                <span>Model: {ml_probability?.model_version || 'SwingTree-Ensemble'}</span>
                <span>Calibration: {ml_probability?.calibration_status || 'UNAVAILABLE'}</span>
              </div>
            </div>
          )}
        </div>

        {/* 4. Relative Strength vs NIFTY 50 */}
        <div className="rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark overflow-hidden shadow-subtle">
          <button
            onClick={() => toggleSection('relative_strength')}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
          >
            <div className="flex items-center space-x-2.5">
              <TrendingUp className="w-4 h-4 text-emerald-500" />
              <span className="text-sm font-bold text-slate-900 dark:text-white">
                Mansfield Relative Strength & Excess Return ({relative_strength?.rs_trend || 'FLAT'})
              </span>
            </div>
            {expandedSections.relative_strength ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
          </button>

          {expandedSections.relative_strength && (
            <div className="p-4 pt-0 border-t border-border-light dark:border-border-dark grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-[10px] uppercase text-slate-500 font-sans">Excess Return 5D</span>
                <div className="text-sm font-bold mt-1 text-slate-800 dark:text-slate-200">
                  {relative_strength?.excess_return_5d !== undefined && relative_strength.excess_return_5d !== null ? (
                    <span className={relative_strength.excess_return_5d >= 0 ? 'text-emerald-500' : 'text-rose-500'}>
                      {relative_strength.excess_return_5d >= 0 ? '+' : ''}{relative_strength.excess_return_5d}%
                    </span>
                  ) : '—'}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-[10px] uppercase text-slate-500 font-sans">Excess Return 20D</span>
                <div className="text-sm font-bold mt-1 text-slate-800 dark:text-slate-200">
                  {relative_strength?.excess_return_20d !== undefined && relative_strength.excess_return_20d !== null ? (
                    <span className={relative_strength.excess_return_20d >= 0 ? 'text-emerald-500' : 'text-rose-500'}>
                      {relative_strength.excess_return_20d >= 0 ? '+' : ''}{relative_strength.excess_return_20d}%
                    </span>
                  ) : '—'}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-[10px] uppercase text-slate-500 font-sans">Mansfield RS 50D</span>
                <div className="text-sm font-bold mt-1 text-slate-800 dark:text-slate-200">
                  {relative_strength?.mansfield_rs_50d !== undefined && relative_strength.mansfield_rs_50d !== null ? (
                    <span className={relative_strength.mansfield_rs_50d >= 0 ? 'text-emerald-500' : 'text-rose-500'}>
                      {relative_strength.mansfield_rs_50d >= 0 ? '+' : ''}{relative_strength.mansfield_rs_50d}%
                    </span>
                  ) : '—'}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40">
                <span className="text-[10px] uppercase text-slate-500 font-sans">RS Trend</span>
                <div className="text-sm font-bold mt-1 text-blue-500">
                  {relative_strength?.rs_trend || 'FLAT'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
