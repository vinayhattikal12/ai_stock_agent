import React from 'react';
import { ShieldAlert, TrendingUp, TrendingDown, Clock, ShieldCheck, Zap, RefreshCw } from 'lucide-react';
import { MarketStatusResponse } from '../types';

interface MarketHeaderProps {
  marketStatus: MarketStatusResponse | null;
  loading: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const MarketHeader: React.FC<MarketHeaderProps> = ({ 
  marketStatus, 
  loading,
  onRefresh,
  isRefreshing 
}) => {
  if (loading && !marketStatus) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-24 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-24 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        </div>
      </div>
    );
  }

  const regime = marketStatus?.regime || 'NEUTRAL';
  const status_label = marketStatus?.status_label || 'Indian Equities Market';
  const regime_description = marketStatus?.regime_policy?.description || 'Deterministic Decision-Support & Quantitative Swing Trading Intelligence';
  const last_updated = marketStatus?.last_updated || new Date().toISOString();

  const nifty = marketStatus?.nifty;
  const bank_nifty = marketStatus?.bank_nifty;
  const india_vix = marketStatus?.india_vix;

  // Determine regime visual styling
  const getRegimeBadge = () => {
    switch (regime as string) {
      case 'STRONG_BULL':
      case 'BULL':
        return {
          bg: 'bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-500',
          icon: TrendingUp,
        };
      case 'BULL_HIGH_VOLATILITY':
        return {
          bg: 'bg-blue-500/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/30',
          dot: 'bg-blue-500',
          icon: Zap,
        };
      case 'SIDEWAYS':
      case 'RECOVERY':
      case 'NEUTRAL':
        return {
          bg: 'bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/30',
          dot: 'bg-amber-500',
          icon: Clock,
        };
      case 'BEAR':
      case 'STRESS':
      default:
        return {
          bg: 'bg-rose-500/10 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 border-rose-500/30',
          dot: 'bg-rose-500',
          icon: ShieldAlert,
        };
    }
  };

  const badge = getRegimeBadge();

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
    } catch {
      return 'Live';
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Banner: AI Equity Intelligence + Market Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border-light dark:border-border-dark">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              AI Equity Intelligence
            </h1>
            <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${badge.bg}`}>
              <span className={`w-2 h-2 rounded-full ${badge.dot} animate-pulse`}></span>
              <span>{status_label}</span>
            </div>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {regime_description}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
            <Clock className="w-3.5 h-3.5" />
            <span>Last Updated: {formatTime(last_updated)}</span>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing || loading}
              title="Refresh live market data and quotes now"
              className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-900/30 text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 border border-border-light dark:border-border-dark transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-blue-500' : ''}`} />
              <span>{isRefreshing ? 'Updating...' : 'Update Data'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Index Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {/* NIFTY 50 */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">NIFTY 50</span>
            {nifty && nifty.price > 0 ? (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                (nifty.change || 0) >= 0 
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' 
                  : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
              }`}>
                {(nifty.change || 0) >= 0 ? '+' : ''}{(nifty.change_percent || 0).toFixed(2)}%
              </span>
            ) : (
              <span className="text-[10px] text-slate-400 font-mono">Syncing...</span>
            )}
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
              {nifty && nifty.price > 0 
                ? `₹${nifty.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : '—'}
            </span>
            {nifty && nifty.price > 0 && (
              <span className={`text-xs font-mono ${(nifty.change || 0) >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                {(nifty.change || 0) >= 0 ? '+' : ''}{(nifty.change || 0).toFixed(2)}
              </span>
            )}
          </div>
        </div>

        {/* BANK NIFTY */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Bank NIFTY</span>
            {bank_nifty && bank_nifty.price > 0 ? (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                (bank_nifty.change || 0) >= 0 
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' 
                  : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
              }`}>
                {(bank_nifty.change || 0) >= 0 ? '+' : ''}{(bank_nifty.change_percent || 0).toFixed(2)}%
              </span>
            ) : (
              <span className="text-[10px] text-slate-400 font-mono">Syncing...</span>
            )}
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
              {bank_nifty && bank_nifty.price > 0 
                ? `₹${bank_nifty.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : '—'}
            </span>
            {bank_nifty && bank_nifty.price > 0 && (
              <span className={`text-xs font-mono ${(bank_nifty.change || 0) >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                {(bank_nifty.change || 0) >= 0 ? '+' : ''}{(bank_nifty.change || 0).toFixed(2)}
              </span>
            )}
          </div>
        </div>

        {/* INDIA VIX */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">India VIX</span>
            {india_vix && india_vix.price > 0 ? (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                (india_vix.price || 0) < 15 
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' 
                  : ((india_vix.price || 0) > 20 ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400' : 'bg-amber-500/10 text-amber-600 dark:text-amber-400')
              }`}>
                {(india_vix.price || 0) < 15 ? 'Low Volatility' : ((india_vix.price || 0) > 20 ? 'High Volatility' : 'Moderate')}
              </span>
            ) : (
              <span className="text-[10px] text-slate-400 font-mono">Syncing...</span>
            )}
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
              {india_vix && india_vix.price > 0 ? (india_vix.price || 0).toFixed(2) : '—'}
            </span>
            {india_vix && india_vix.price > 0 && (
              <span className={`text-xs font-mono ${(india_vix.change || 0) <= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                {(india_vix.change || 0) >= 0 ? '+' : ''}{(india_vix.change || 0).toFixed(2)} ({(india_vix.change_percent || 0).toFixed(1)}%)
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

