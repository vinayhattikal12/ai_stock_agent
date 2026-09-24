import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  ArrowRight, 
  ShieldAlert, 
  Info, 
  TrendingUp, 
  Plus, 
  BarChart2, 
  HelpCircle, 
  Activity, 
  Layers, 
  Percent, 
  Sliders, 
  AlertTriangle, 
  Filter, 
  Eye, 
  ChevronDown, 
  ChevronUp, 
  Target, 
  Award, 
  Zap, 
  Briefcase, 
  Calendar, 
  History,
  Flame 
} from 'lucide-react';
import { ScannerScanResponse, StockOpportunity, MarketCapCategoryResult, HistoricalScanSummary } from '../types';
import { api } from '../services/api';

interface ScannerViewProps {
  scanResult: ScannerScanResponse | null;
  isScanning: boolean;
  onTriggerScan: () => void;
  onSelectHistoricalScan?: (date: string) => void;
  onViewAnalysis: (symbol: string) => void;
  onAddToPortfolio: (symbol: string, currentPrice: number) => void;
}

export const ScannerView: React.FC<ScannerViewProps> = ({
  scanResult,
  isScanning,
  onTriggerScan,
  onSelectHistoricalScan,
  onViewAnalysis,
  onAddToPortfolio,
}) => {
  const [selectedWhyStock, setSelectedWhyStock] = useState<StockOpportunity | null>(null);
  const [selectedFailureStock, setSelectedFailureStock] = useState<StockOpportunity | null>(null);
  const [showFunnelDetails, setShowFunnelDetails] = useState<boolean>(true);
  const [activeCategoryTab, setActiveCategoryTab] = useState<'ALL' | 'LARGE_CAP' | 'MID_CAP' | 'SMALL_CAP'>('ALL');
  const [expandedNearMisses, setExpandedNearMisses] = useState<Record<string, boolean>>({
    LARGE_CAP: false,
    MID_CAP: false,
    SMALL_CAP: false
  });
  const [historyList, setHistoryList] = useState<HistoricalScanSummary[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getScanHistory()
      .then((data) => {
        if (isMounted && data) {
          setHistoryList(data);
        }
      })
      .catch((err) => console.warn('Could not load scan history:', err));
    return () => {
      isMounted = false;
    };
  }, [scanResult]);

  useEffect(() => {
    if (scanResult?.scan_timestamp) {
      const scanDateStr = typeof scanResult.scan_timestamp === 'string' 
        ? scanResult.scan_timestamp.split('T')[0] 
        : new Date(scanResult.scan_timestamp).toISOString().split('T')[0];
      setSelectedDate(scanDateStr);
    }
  }, [scanResult]);

  const scanSteps = [
    { label: 'Data Quality & OHLCV Validation', icon: CheckCircle2 },
    { label: 'Market regime policy alignment', icon: CheckCircle2 },
    { label: 'Sector momentum & rotation scoring', icon: CheckCircle2 },
    { label: 'Breakout, Pullback & VCP classification', icon: CheckCircle2 },
    { label: 'RVOL & institutional accumulation profiling', icon: CheckCircle2 },
    { label: 'Mansfield relative strength vs NIFTY', icon: CheckCircle2 },
    { label: 'Calibrated ML probability prediction (10D)', icon: CheckCircle2 },
    { label: 'SEBI/AMFI category independent ranking', icon: CheckCircle2 },
    { label: 'Structural pivots & explicit price levels', icon: CheckCircle2 },
  ];

  const toggleNearMissCategory = (cat: string) => {
    setExpandedNearMisses((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  const formatINR = (val?: number | null) => (val !== undefined && val !== null ? `₹${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—');

  const renderCategorySection = (catResult: MarketCapCategoryResult, colorTheme: { border: string, bg: string, text: string, badge: string }) => {
    const isExpanded = expandedNearMisses[catResult.category] || false;
    const candidates = catResult.candidates || [];
    const nearMisses = catResult.near_misses || [];

    return (
      <div key={catResult.category} className="space-y-4 pt-2">
        {/* Category Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center space-x-3">
            <div className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold ${colorTheme.badge}`}>
              {catResult.label.toUpperCase()}
            </div>
            <span className="text-xs font-mono text-slate-500">
              SEBI Ranks {catResult.market_cap_rank_range} • {catResult.classification_source}
            </span>
          </div>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <span className="text-slate-500">Scanned: <strong>{catResult.total_scanned}</strong></span>
            <span>•</span>
            <span className={candidates.length > 0 ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-500'}>
              Qualified BUYs: <strong>{candidates.length} / 5</strong>
            </span>
            <span>•</span>
            <span className="text-purple-600 dark:text-purple-400">
              Watchlist: <strong>{nearMisses.length}</strong>
            </span>
          </div>
        </div>

        {/* Category-Level Bottleneck Notice if 0 Qualified */}
        {candidates.length === 0 && (
          <div className="p-4 rounded-xl bg-amber-500/5 dark:bg-amber-950/20 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-300 flex items-start space-x-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <strong>0 {catResult.label} Qualified as Strict BUYs.</strong> {catResult.primary_bottleneck ? `Primary Gate Filter: ${catResult.primary_bottleneck}.` : 'Secondary risk gates unfulfilled.'} Review near-misses below.
            </div>
          </div>
        )}

        {/* Qualified BUY Cards */}
        {candidates.length > 0 && (
          <div className="grid grid-cols-1 gap-4">
            {candidates.map((opp) => renderOpportunityCard(opp, true))}
          </div>
        )}

        {/* Collapsible Near-Misses / Watchlist */}
        {nearMisses.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-border-light dark:border-border-dark space-y-3">
            <button
              onClick={() => toggleNearMissCategory(catResult.category)}
              className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              <div className="flex items-center space-x-2">
                <Eye className="w-4 h-4 text-purple-500" />
                <span>{catResult.label} Near-Misses / Watchlist ({nearMisses.length})</span>
                <span className="text-[11px] font-mono text-slate-500 font-normal">
                  — High factor rank; missed 1 secondary condition
                </span>
              </div>
              <div className="flex items-center space-x-1 text-purple-600 dark:text-purple-400 font-mono text-[11px]">
                <span>{isExpanded ? 'Hide' : 'Show Watchlist'}</span>
                {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </div>
            </button>

            {isExpanded && (
              <div className="grid grid-cols-1 gap-3 pt-2">
                {nearMisses.map((opp) => renderOpportunityCard(opp, false))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderOpportunityCard = (opp: StockOpportunity, isBuyCandidate: boolean) => {
    const isSmallCap = opp.market_cap_category === 'SMALL_CAP';
    const isMidCap = opp.market_cap_category === 'MID_CAP';

    return (
      <div
        key={opp.symbol}
        className={`p-5 rounded-2xl transition-all border ${
          isBuyCandidate
            ? 'bg-background-cardLight dark:bg-background-cardDark border-emerald-500/30 dark:border-emerald-500/30 shadow-subtle hover:border-emerald-500/50'
            : 'bg-background-cardLight/70 dark:bg-background-cardDark/70 border-border-light dark:border-border-dark hover:border-purple-500/30'
        }`}
      >
        {/* Top Stock Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3">
          <div className="flex items-start space-x-3">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                <span className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                  {opp.symbol}
                </span>
                
                {/* Market Cap Badge */}
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  isSmallCap
                    ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                    : isMidCap
                    ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                    : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                }`}>
                  {opp.market_cap_category.replace('_', ' ')} {opp.market_cap_rank ? `(#${opp.market_cap_rank})` : ''}
                </span>

                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold flex items-center space-x-1 ${
                    isBuyCandidate
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                      : 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/30'
                  }`}
                >
                  {isBuyCandidate ? <CheckCircle2 className="w-3 h-3 inline mr-1" /> : <Eye className="w-3 h-3 inline mr-1" />}
                  <span>{opp.signal}</span>
                </span>

                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  {opp.setup_type}
                </span>

                {/* Multi-Day Persistent Leader Streak Badge */}
                {(opp.is_multi_day_runner || (opp.scan_streak_days && opp.scan_streak_days >= 2)) && (
                  <span 
                    title={opp.streak_description || `Appeared in Top Quantitative Setups for ${opp.scan_streak_days} consecutive days with strong institutional accumulation.`}
                    className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 animate-pulse"
                  >
                    <Flame className="w-3 h-3 text-amber-500" />
                    <span>{opp.scan_streak_days}-Day Streak (Persistent Leader)</span>
                  </span>
                )}

                {opp.portfolio_fit_score !== undefined && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/30">
                    Fit: {opp.portfolio_fit_score.toFixed(0)}/100
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-2 text-xs text-slate-500 flex-wrap">
                <span>{opp.company_name}</span>
                <span>•</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">{opp.sector}</span>
                <span>•</span>
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                  Mansfield RS: {opp.relative_strength?.mansfield_rs_50d !== undefined && opp.relative_strength.mansfield_rs_50d !== null ? `${opp.relative_strength.mansfield_rs_50d > 0 ? '+' : ''}${opp.relative_strength.mansfield_rs_50d.toFixed(1)}%` : '—'}
                </span>
                <span>•</span>
                <span className="font-mono text-amber-600 dark:text-amber-400">
                  RVOL: {opp.volume_metrics?.rvol_20d !== undefined && opp.volume_metrics.rvol_20d !== null ? `${opp.volume_metrics.rvol_20d.toFixed(2)}x` : '—'} ({opp.volume_metrics?.volume_trend || 'ACCUMULATION'})
                </span>
              </div>
            </div>
          </div>

          <div className="text-left sm:text-right">
            <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
              {opp.current_price ? formatINR(opp.current_price) : '—'}
            </div>
            {opp.daily_change_pct !== undefined && opp.daily_change_pct !== null && (
              <div className={`text-xs font-mono font-semibold ${opp.daily_change_pct >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                {opp.daily_change_pct >= 0 ? '+' : ''}{opp.daily_change_pct.toFixed(2)}% today
              </div>
            )}
          </div>
        </div>

        {/* Multi-Factor Badges */}
        {opp.factor_scores && (
          <div className="flex items-center gap-2 py-2.5 overflow-x-auto text-[11px] font-mono">
            <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
              Momentum: <strong className="text-blue-600 dark:text-blue-400">{opp.factor_scores.momentum_score ?? '—'}</strong>
            </span>
            <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
              RS: <strong className="text-emerald-600 dark:text-emerald-400">{opp.factor_scores.relative_strength_score ?? '—'}</strong>
            </span>
            <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
              Trend: <strong className="text-purple-600 dark:text-purple-400">{opp.factor_scores.trend_score ?? '—'}</strong>
            </span>
            <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
              Setup: <strong className="text-amber-600 dark:text-amber-400">{opp.factor_scores.setup_quality_score ?? '—'}</strong>
            </span>
            <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
              Turnover: <strong className="text-cyan-600 dark:text-cyan-400">{opp.volume_metrics?.avg_turnover_cr_20d ? `₹${opp.volume_metrics.avg_turnover_cr_20d.toFixed(1)} Cr/day` : '—'}</strong>
            </span>
          </div>
        )}

        {/* Watch Condition Callout if in WATCH */}
        {!isBuyCandidate && opp.watch_reasons && opp.watch_reasons.length > 0 && (
          <div className="p-3 my-2 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/40 text-xs text-amber-800 dark:text-amber-300 flex items-start justify-between">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <strong>Watchlist Notice:</strong> {opp.watch_reasons[0]}
              </div>
            </div>
            <button
              onClick={() => setSelectedFailureStock(opp)}
              className="ml-2 font-semibold underline text-amber-700 dark:text-amber-400 text-[11px] whitespace-nowrap"
            >
              Details
            </button>
          </div>
        )}

        {/* Explicit Rupee Price Levels Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 py-4 border-y border-border-light dark:border-border-dark font-mono">
          {/* Entry Zone */}
          <div>
            <span className="text-[10px] uppercase text-slate-500 font-sans font-semibold">Entry Price Zone</span>
            <div className="text-sm font-bold text-slate-800 dark:text-slate-200 mt-1">
              {opp.levels?.entry_range_display || (opp.levels?.entry_low ? `${formatINR(opp.levels.entry_low)} – ${formatINR(opp.levels.entry_high)}` : '—')}
            </div>
          </div>

          {/* Target 1 Price */}
          <div>
            <span className="text-[10px] uppercase text-emerald-600 dark:text-emerald-400 font-sans font-semibold">Target 1 Price</span>
            <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {opp.levels?.target_1_display || (opp.levels?.target_1 ? formatINR(opp.levels.target_1) : '—')}
            </div>
            {opp.levels?.target_2_display && (
              <span className="text-[10px] text-slate-500 font-sans block mt-0.5">
                T2: {opp.levels.target_2_display}
              </span>
            )}
          </div>

          {/* Stop Loss Price */}
          <div>
            <span className="text-[10px] uppercase text-rose-600 dark:text-rose-400 font-sans font-semibold">Stop Loss Price</span>
            <div className="text-sm font-bold text-rose-600 dark:text-rose-400 mt-1">
              {opp.levels?.stop_loss_display || (opp.levels?.stop_loss ? formatINR(opp.levels.stop_loss) : '—')}
            </div>
            <span className="text-[10px] text-slate-500 font-sans block truncate" title={opp.levels?.stop_reason}>
              {opp.levels?.stop_method || 'STRUCTURAL'}
            </span>
          </div>

          {/* Probability */}
          <div>
            <span className="text-[10px] uppercase text-slate-500 font-sans font-semibold">P(T1 before SL)</span>
            <div className="text-sm font-bold text-blue-600 dark:text-blue-400 mt-1 flex items-center space-x-1">
              <span>{opp.ml_probability?.p_t1_before_sl !== undefined && opp.ml_probability.p_t1_before_sl !== null ? `${Math.round(opp.ml_probability.p_t1_before_sl * 100)}%` : '—'}</span>
            </div>
            <span className="text-[10px] text-slate-500 font-sans">
              Horizon: {opp.ml_probability?.expected_days_min || 5}–{opp.ml_probability?.expected_days_max || 10} days
            </span>
          </div>

          {/* Sizing & R:R */}
          <div>
            <span className="text-[10px] uppercase text-slate-500 font-sans font-semibold">R:R & Sizing</span>
            <div className="text-sm font-bold text-purple-600 dark:text-purple-400 mt-1">
              {opp.levels?.risk_reward_ratio ? `1 : ${opp.levels.risk_reward_ratio.toFixed(2)}` : '—'}
            </div>
            {opp.position_sizing && (
              <span className="text-[10px] text-slate-500 font-sans block font-semibold text-emerald-600 dark:text-emerald-400">
                Qty: {opp.position_sizing.suggested_quantity} (₹{opp.position_sizing.allocated_capital_inr?.toLocaleString('en-IN')})
              </span>
            )}
          </div>
        </div>

        {/* Card Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-border-light dark:border-border-dark">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedWhyStock(opp)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Why Qualified?</span>
            </button>
            {opp.current_price && (
              <button
                onClick={() => onAddToPortfolio(opp.symbol, opp.current_price!)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add to Portfolio</span>
              </button>
            )}
          </div>

          <button
            onClick={() => onViewAnalysis(opp.symbol)}
            className="flex items-center space-x-1 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-subtle transition-all"
          >
            <span>View Full Analysis</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header & Scan Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-br from-blue-950/20 via-background-cardLight to-background-cardLight dark:from-blue-950/40 dark:via-background-cardDark dark:to-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Systematic Swing Scanner
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              Multi-Cap Tri-Category Engine
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Independently scans and ranks Top 5 Large-Cap (Ranks 1–100), Top 5 Mid-Cap (Ranks 101–250), and Top 5 Small-Cap (Ranks 251+) opportunities based on authoritative SEBI/AMFI classifications. Max 15 opportunities per scan.
          </p>
        </div>

        <button
          onClick={onTriggerScan}
          disabled={isScanning}
          className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-bold text-sm shadow-premium transition-all ${
            isScanning
              ? 'bg-slate-300 dark:bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-glow-blue'
          }`}
        >
          <Sparkles className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
          <span>{isScanning ? 'Scanning Multi-Cap Universe...' : 'Run Quantitative Scan'}</span>
        </button>
      </div>

      {/* Subtle Animated Progress Interface during Scan */}
      {isScanning && (
        <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-blue-500/30 shadow-glow-blue animate-pulse space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
            <span className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
              </span>
              <span>Scanning Large, Mid & Small Cap Equities with Upstox API v2 Live Feed</span>
            </span>
            <span className="text-xs font-mono text-blue-500 font-semibold">Tri-Category Funnel</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {scanSteps.map((step, idx) => (
              <div key={idx} className="flex items-center space-x-2 text-xs font-medium text-slate-700 dark:text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span>{step.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 15-Day Date-Wise Historical Scan Navigation Bar */}
      {historyList.length > 0 && (
        <div className="p-4 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <History className="w-4 h-4 text-blue-500" />
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                Discovery Archive (Last 15 Days)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 font-semibold border border-blue-200 dark:border-blue-800/40">
                {historyList.length} Stored Scans
              </span>
            </div>
            <span className="text-[11px] text-slate-400">
              Preserved date-wise. Click any date to review past swing setups. Max 15 days maintained.
            </span>
          </div>

          <div className="flex items-center space-x-2 overflow-x-auto pb-1 pt-0.5">
            {historyList.map((hist) => {
              const histDateStr = String(hist.scan_date);
              const isSelected = selectedDate === histDateStr;
              const dateInfo = formatDateBadge(histDateStr);

              return (
                <button
                  key={hist.id || histDateStr}
                  type="button"
                  onClick={() => {
                    if (onSelectHistoricalScan) {
                      onSelectHistoricalScan(histDateStr);
                    }
                  }}
                  className={`flex-shrink-0 flex items-center space-x-2 px-3.5 py-2 rounded-xl border text-xs transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-600 shadow-glow-blue font-bold'
                      : 'bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 border-border-light dark:border-border-dark'
                  }`}
                >
                  <Calendar className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                  <div className="text-left">
                    <span className="block leading-tight font-mono">{dateInfo.label}</span>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                    isSelected 
                      ? 'bg-white/20 text-white' 
                      : hist.total_qualified_count > 0 
                      ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' 
                      : 'bg-slate-200 dark:bg-slate-800 text-slate-500'
                  }`}>
                    {hist.total_qualified_count} BUYs
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Historical Date Notice Banner */}
      {selectedDate && selectedDate !== new Date().toISOString().split('T')[0] && (
        <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-700 dark:text-purple-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-purple-500 flex-shrink-0" />
            <span>
              Viewing archived historical discovery for <strong>{selectedDate}</strong> ({scanResult?.total_qualified_count || 0} qualified BUYs, {scanResult?.near_misses_count || 0} watchlist candidates).
            </span>
          </div>
          <button
            onClick={onTriggerScan}
            className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-colors flex items-center space-x-1.5 self-start sm:self-auto"
          >
            <Sparkles className="w-3 h-3" />
            <span>Run Fresh Live Scan</span>
          </button>
        </div>
      )}

      {/* Results Section */}
      {scanResult && !isScanning && (
        <div className="space-y-6">
          {/* Market Regime & Multi-Cap Overview Card */}
          <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border-light dark:border-border-dark">
              <div className="flex items-center space-x-3">
                <span className="px-3 py-1 rounded-lg text-xs font-mono font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                  Regime: {scanResult.market_regime}
                </span>
                <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  {scanResult.market_regime_policy.status_label} — {scanResult.market_regime_policy.description}
                </span>
              </div>
              <div className="flex items-center space-x-3 text-xs font-mono text-slate-500">
                <span>Min ML: <strong>{Math.round(scanResult.configured_probability_threshold * 100)}%</strong></span>
                <span>•</span>
                <span>Min R:R: <strong>1:{scanResult.configured_min_rr.toFixed(1)}</strong></span>
                <span>•</span>
                <span>Total Qualified: <strong className="text-emerald-600 dark:text-emerald-400">{scanResult.total_qualified_count || 0} / 15</strong></span>
              </div>
            </div>

            {/* Category Quick Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-800/30 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-blue-700 dark:text-blue-300 uppercase tracking-wider block">
                    Large-Cap (1–100)
                  </span>
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    {scanResult.large_cap?.candidates?.length || 0} BUYs • {scanResult.large_cap?.near_misses?.length || 0} Watchlist
                  </span>
                </div>
                <div className="text-lg font-bold font-mono text-blue-600 dark:text-blue-400">
                  {scanResult.large_cap?.candidates?.length || 0}/5
                </div>
              </div>

              <div className="p-3 rounded-xl bg-cyan-50/50 dark:bg-cyan-950/20 border border-cyan-200/60 dark:border-cyan-800/30 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-cyan-700 dark:text-cyan-300 uppercase tracking-wider block">
                    Mid-Cap (101–250)
                  </span>
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    {scanResult.mid_cap?.candidates?.length || 0} BUYs • {scanResult.mid_cap?.near_misses?.length || 0} Watchlist
                  </span>
                </div>
                <div className="text-lg font-bold font-mono text-cyan-600 dark:text-cyan-400">
                  {scanResult.mid_cap?.candidates?.length || 0}/5
                </div>
              </div>

              <div className="p-3 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/30 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider block">
                    Small-Cap (251+)
                  </span>
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    {scanResult.small_cap?.candidates?.length || 0} BUYs • {scanResult.small_cap?.near_misses?.length || 0} Watchlist
                  </span>
                </div>
                <div className="text-lg font-bold font-mono text-amber-600 dark:text-amber-400">
                  {scanResult.small_cap?.candidates?.length || 0}/5
                </div>
              </div>
            </div>

            {/* Funnel Survival Bar */}
            {scanResult.survivors_by_stage && Object.keys(scanResult.survivors_by_stage).length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <span className="flex items-center space-x-1.5">
                    <Filter className="w-3.5 h-3.5 text-blue-500" />
                    <span>Global Funnel Survival Across Categories</span>
                  </span>
                  <button 
                    onClick={() => setShowFunnelDetails(!showFunnelDetails)}
                    className="text-[11px] text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
                  >
                    <span>{showFunnelDetails ? 'Collapse' : 'Show Details'}</span>
                    {showFunnelDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                </div>

                {showFunnelDetails && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 font-mono text-[11px] text-center">
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">Universe</span>
                      <strong className="text-slate-800 dark:text-slate-200">{scanResult.total_universe_scanned}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">Data Valid</span>
                      <strong className="text-slate-800 dark:text-slate-200">{scanResult.survivors_by_stage.data_valid}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">Liquid</span>
                      <strong className="text-slate-800 dark:text-slate-200">{scanResult.survivors_by_stage.liquid}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">Factors</span>
                      <strong className="text-slate-800 dark:text-slate-200">{scanResult.survivors_by_stage.strong_factors}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">Setups</span>
                      <strong className="text-slate-800 dark:text-slate-200">{scanResult.survivors_by_stage.valid_setups}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">ML Evaluated</span>
                      <strong className="text-slate-800 dark:text-slate-200">{scanResult.survivors_by_stage.ml_evaluated}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark">
                      <span className="text-slate-500 block text-[9px] uppercase font-sans">Risk Valid</span>
                      <strong className="text-emerald-600 dark:text-emerald-400">{scanResult.survivors_by_stage.risk_valid}</strong>
                    </div>
                    <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-500/20">
                      <span className="text-blue-600 dark:text-blue-400 block text-[9px] uppercase font-sans">Qualified BUYs</span>
                      <strong className="text-blue-600 dark:text-blue-400">{scanResult.total_qualified_count || 0}</strong>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* If Full Global Abstention State */}
          {scanResult.is_abstention && (
            <div className="p-6 rounded-2xl bg-amber-500/5 dark:bg-amber-950/20 border border-amber-500/30 space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center flex-shrink-0">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                    NO TRADE TODAY (0 QUALIFIED BUY OPPORTUNITIES)
                  </h2>
                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                    {scanResult.abstention_reason}
                  </p>
                  {scanResult.primary_bottleneck && (
                    <div className="mt-2 inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-300 font-mono">
                      <strong>Primary Blocker:</strong> <span>{scanResult.primary_bottleneck}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Top 2 High-Conviction Alpha Picks Hero Banner */}
          {scanResult.top_conviction_picks && scanResult.top_conviction_picks.length > 0 && activeCategoryTab === 'ALL' && (
            <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-500/10 via-blue-500/10 to-indigo-500/10 border-2 border-emerald-500/30 dark:border-emerald-500/40 shadow-premium space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-emerald-500/20">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-400 to-emerald-500 text-slate-950 flex items-center justify-center font-bold shadow-subtle">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                      <span>Model's Top 2 High-Conviction Alpha Picks</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500 text-white uppercase tracking-wider">
                        Highest Win Potential
                      </span>
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-300">
                      Ranked #1 & #2 across all 15 candidates based on calibrated ML probability, asymmetric R:R (&ge;1.8R), and institutional volume confirmation.
                    </p>
                  </div>
                </div>

                <div className="text-xs font-mono text-emerald-700 dark:text-emerald-400 font-semibold flex items-center space-x-1 self-start sm:self-auto">
                  <Target className="w-3.5 h-3.5" />
                  <span>Immediate Swing Focus</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scanResult.top_conviction_picks.map((opp, idx) => (
                  <div 
                    key={opp.symbol}
                    className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-emerald-500/40 hover:border-emerald-500 shadow-subtle transition-all space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold text-xs font-mono flex items-center justify-center border border-emerald-500/30">
                          #{idx + 1}
                        </span>
                        <span 
                          onClick={() => onViewAnalysis(opp.symbol)}
                          className="text-lg font-bold font-mono text-slate-900 dark:text-white hover:text-blue-500 cursor-pointer"
                        >
                          {opp.symbol}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-bold">
                          {opp.market_cap_category.replace('_', ' ')}
                        </span>
                        {opp.is_multi_day_runner && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-500 font-bold flex items-center space-x-0.5">
                            <Flame className="w-2.5 h-2.5" />
                            <span>{opp.scan_streak_days}D Streak</span>
                          </span>
                        )}
                      </div>

                      <div className="text-right font-mono">
                        <div className="text-base font-bold text-slate-900 dark:text-white">
                          {formatINR(opp.current_price)}
                        </div>
                        <div className={`text-xs font-semibold ${
                          (opp.daily_change_pct || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                        }`}>
                          {(opp.daily_change_pct || 0) >= 0 ? '+' : ''}{(opp.daily_change_pct || 0).toFixed(2)}%
                        </div>
                      </div>
                    </div>

                    {/* Key Metrics Pill Grid */}
                    <div className="grid grid-cols-3 gap-2 font-mono text-xs text-center">
                      <div className="p-2 rounded-lg bg-emerald-500/5 dark:bg-emerald-950/20 border border-emerald-500/20">
                        <span className="text-[10px] font-sans text-slate-500 uppercase block">ML Win Prob</span>
                        <strong className="text-emerald-600 dark:text-emerald-400 text-sm">
                          {opp.ml_probability?.p_t1_before_sl ? `${Math.round(opp.ml_probability.p_t1_before_sl * 100)}%` : '—'}
                        </strong>
                      </div>
                      <div className="p-2 rounded-lg bg-blue-500/5 dark:bg-blue-950/20 border border-blue-500/20">
                        <span className="text-[10px] font-sans text-slate-500 uppercase block">Target 1 (R:R)</span>
                        <strong className="text-blue-600 dark:text-blue-400 text-sm">
                          1:{opp.levels?.risk_reward_ratio_t1 ? opp.levels.risk_reward_ratio_t1.toFixed(1) : '1.8'}R
                        </strong>
                      </div>
                      <div className="p-2 rounded-lg bg-purple-500/5 dark:bg-purple-950/20 border border-purple-500/20">
                        <span className="text-[10px] font-sans text-slate-500 uppercase block">Entry Zone</span>
                        <strong className="text-purple-600 dark:text-purple-400 text-xs">
                          {opp.levels?.entry_range_display || 'Near market'}
                        </strong>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-1 text-xs">
                      <button
                        onClick={() => onAddToPortfolio(opp.symbol, opp.current_price || 0)}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-all shadow-subtle cursor-pointer"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add to Investments</span>
                      </button>

                      <button
                        onClick={() => onViewAnalysis(opp.symbol)}
                        className="text-blue-600 dark:text-blue-400 font-semibold hover:underline flex items-center space-x-1 cursor-pointer"
                      >
                        <span>Full Quant Breakdown</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Category Tabs */}
          <div className="flex items-center space-x-2 border-b border-border-light dark:border-border-dark pb-2 overflow-x-auto">
            <button
              onClick={() => setActiveCategoryTab('ALL')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
                activeCategoryTab === 'ALL'
                  ? 'bg-blue-600 text-white shadow-subtle'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              All Categories ({scanResult.total_qualified_count || 0} Qualified / 15 Max)
            </button>
            <button
              onClick={() => setActiveCategoryTab('LARGE_CAP')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
                activeCategoryTab === 'LARGE_CAP'
                  ? 'bg-blue-600 text-white shadow-subtle'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              Top Large-Cap ({scanResult.large_cap?.candidates?.length || 0}/5)
            </button>
            <button
              onClick={() => setActiveCategoryTab('MID_CAP')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
                activeCategoryTab === 'MID_CAP'
                  ? 'bg-blue-600 text-white shadow-subtle'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              Top Mid-Cap ({scanResult.mid_cap?.candidates?.length || 0}/5)
            </button>
            <button
              onClick={() => setActiveCategoryTab('SMALL_CAP')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
                activeCategoryTab === 'SMALL_CAP'
                  ? 'bg-blue-600 text-white shadow-subtle'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              Top Small-Cap ({scanResult.small_cap?.candidates?.length || 0}/5)
            </button>
          </div>

          {/* Render Sections Based on Selected Tab */}
          {(activeCategoryTab === 'ALL' || activeCategoryTab === 'LARGE_CAP') && scanResult.large_cap && (
            renderCategorySection(scanResult.large_cap, {
              border: 'border-blue-500/30',
              bg: 'bg-blue-500/10',
              text: 'text-blue-600 dark:text-blue-400',
              badge: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30'
            })
          )}

          {(activeCategoryTab === 'ALL' || activeCategoryTab === 'MID_CAP') && scanResult.mid_cap && (
            renderCategorySection(scanResult.mid_cap, {
              border: 'border-cyan-500/30',
              bg: 'bg-cyan-500/10',
              text: 'text-cyan-600 dark:text-cyan-400',
              badge: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30'
            })
          )}

          {(activeCategoryTab === 'ALL' || activeCategoryTab === 'SMALL_CAP') && scanResult.small_cap && (
            renderCategorySection(scanResult.small_cap, {
              border: 'border-amber-500/30',
              bg: 'bg-amber-500/10',
              text: 'text-amber-600 dark:text-amber-400',
              badge: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30'
            })
          )}
        </div>
      )}

      {/* Modal: Why did this qualify? */}
      {selectedWhyStock && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark p-6 space-y-4 shadow-premium">
            <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
              <h3 className="text-base font-bold text-slate-900 dark:text-white font-mono flex items-center space-x-2">
                <span>{selectedWhyStock.symbol}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-sans">
                  {selectedWhyStock.market_cap_category.replace('_', ' ')} (#{selectedWhyStock.market_cap_rank || 'N/A'})
                </span>
              </h3>
              <button
                onClick={() => setSelectedWhyStock(null)}
                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300 font-sans">
              <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800/30 space-y-1">
                <strong className="text-blue-700 dark:text-blue-300 font-semibold block">Target & Stop Price Derivations:</strong>
                {selectedWhyStock.levels?.levels_reasoning?.map((r, idx) => (
                  <div key={idx} className="text-[11px] leading-relaxed">• {r}</div>
                ))}
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-1">
                <strong className="text-slate-800 dark:text-slate-200 font-semibold block">Qualification Drivers:</strong>
                {selectedWhyStock.why_this_setup.map((w, idx) => (
                  <div key={idx} className="text-[11px] leading-relaxed">• {w}</div>
                ))}
              </div>

              {selectedWhyStock.portfolio_fit_score !== undefined && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/30 text-[11px] text-emerald-800 dark:text-emerald-300">
                  <strong>Portfolio Fit Score: {selectedWhyStock.portfolio_fit_score.toFixed(0)}/100</strong> — Evaluated against sector concentration cap and existing holdings.
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedWhyStock(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Why is this in Watch / What failed? */}
      {selectedFailureStock && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark p-6 space-y-4 shadow-premium">
            <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
              <h3 className="text-base font-bold text-slate-900 dark:text-white font-mono flex items-center space-x-2">
                <span>{selectedFailureStock.symbol}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-sans">
                  Watchlist Diagnostic
                </span>
              </h3>
              <button
                onClick={() => setSelectedFailureStock(null)}
                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300 font-sans">
              <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/40 space-y-1.5">
                <strong className="text-amber-800 dark:text-amber-300 font-semibold flex items-center space-x-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <span>Unsatisfied BUY Gate Criteria:</span>
                </strong>
                {selectedFailureStock.watch_reasons && selectedFailureStock.watch_reasons.length > 0 ? (
                  selectedFailureStock.watch_reasons.map((r, idx) => (
                    <div key={idx} className="text-amber-900 dark:text-amber-200 text-[11px] leading-relaxed">
                      • {r}
                    </div>
                  ))
                ) : (
                  <div className="text-[11px]">Ranked in category watchlist priority.</div>
                )}
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-1">
                <strong className="text-slate-800 dark:text-slate-200 font-semibold block">Setup Highlights:</strong>
                {selectedFailureStock.why_this_setup.slice(0, 3).map((w, idx) => (
                  <div key={idx} className="text-[11px] leading-relaxed">• {w}</div>
                ))}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedFailureStock(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function formatDateBadge(dateStr: string): { label: string; subLabel: string; isToday: boolean } {
  try {
    const todayStr = new Date().toISOString().split('T')[0];
    const isToday = dateStr === todayStr;
    const d = new Date(dateStr + 'T00:00:00');
    const dayName = d.toLocaleDateString('en-US', { weekday: 'short' });
    const monthDay = d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
    
    return {
      label: isToday ? 'Today' : `${dayName}, ${monthDay}`,
      subLabel: isToday ? monthDay : dateStr,
      isToday
    };
  } catch {
    return {
      label: dateStr,
      subLabel: dateStr,
      isToday: false
    };
  }
}
