import React, { useEffect, useState } from 'react';
import { Flame, TrendingUp, TrendingDown, Zap, ArrowUpRight, ArrowDownRight, Compass, Sparkles, RefreshCw, Eye } from 'lucide-react';
import { api } from '../services/api';
import { MarketMoverItem, TodaysMoversResponse } from '../types';

interface TodaysMoversViewProps {
  onSelectStock?: (symbol: string) => void;
}

export const TodaysMoversView: React.FC<TodaysMoversViewProps> = ({ onSelectStock }) => {
  const [moversData, setMoversData] = useState<TodaysMoversResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'GAINERS' | 'LOSERS' | 'VOLUME' | 'GAPS'>('GAINERS');

  const fetchMovers = () => {
    setLoading(true);
    api.getTodaysMovers()
      .then((data) => {
        setMoversData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMovers();
  }, []);

  if (loading || !moversData) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        </div>
      </div>
    );
  }

  const itemsMap: Record<string, MarketMoverItem[]> = {
    GAINERS: moversData.top_gainers || [],
    LOSERS: moversData.top_losers || [],
    VOLUME: moversData.unusual_volume || [],
    GAPS: moversData.gap_movers || [],
  };

  const currentItems = itemsMap[activeTab] || [];

  return (
    <div className="space-y-6">
      {/* Header & Subtitle */}
      <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Flame className="w-5 h-5 text-amber-500" />
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Today's Market Movers
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
              Detection Mode (Unscored)
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Real-time detection of intraday momentum, unusual volume bursts, opening gaps, and verified corporate disclosures.
          </p>
        </div>

        <button
          onClick={fetchMovers}
          className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-all cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Live Feeds</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border-light dark:border-border-dark pb-3">
        <button
          onClick={() => setActiveTab('GAINERS')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'GAINERS'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-background-cardLight dark:bg-background-cardDark text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Top Gainers ({moversData.top_gainers.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('LOSERS')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'LOSERS'
              ? 'bg-rose-600 text-white shadow-lg shadow-rose-500/20'
              : 'bg-background-cardLight dark:bg-background-cardDark text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <TrendingDown className="w-4 h-4" />
          <span>Top Losers ({moversData.top_losers.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('VOLUME')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'VOLUME'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              : 'bg-background-cardLight dark:bg-background-cardDark text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Turnover & Volume Surges ({moversData.unusual_volume.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('GAPS')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'GAPS'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
              : 'bg-background-cardLight dark:bg-background-cardDark text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Opening Gaps ({moversData.gap_movers.length})</span>
        </button>
      </div>

      {/* Mover Cards Grid */}
      {currentItems.length === 0 ? (
        <div className="p-8 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark text-center space-y-2">
          <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">
            No active movers currently detected in this category.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {currentItems.map((mover) => {
            const isPositive = mover.change_percent >= 0;
            const isStockSpecific = mover.catalyst_type === 'STOCK_SPECIFIC';
            const isSectorTheme = mover.catalyst_type === 'SECTOR_THEME';

            return (
              <div
                key={mover.symbol}
                className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle hover:border-blue-500/40 transition-all flex flex-col justify-between space-y-4"
              >
                {/* Header: Symbol, Name & Price */}
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-base font-bold text-slate-900 dark:text-white font-mono tracking-tight">
                          {mover.symbol}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-medium">
                          {mover.sector}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 truncate max-w-[200px] mt-0.5">
                        {mover.company_name}
                      </p>
                    </div>

                    <div className="text-right font-mono">
                      <div className="text-base font-bold text-slate-900 dark:text-white">
                        ₹{mover.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className={`text-xs font-bold flex items-center justify-end space-x-0.5 ${
                        isPositive ? 'text-emerald-500' : 'text-rose-500'
                      }`}>
                        {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                        <span>{isPositive ? `+${mover.change_percent.toFixed(2)}%` : `${mover.change_percent.toFixed(2)}%`}</span>
                      </div>
                    </div>
                  </div>

                  {/* Catalyst Badge (Stock-Specific vs Sector Theme) */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {isStockSpecific && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center space-x-1">
                        <Zap className="w-3 h-3" />
                        <span>Company Catalyst (Decoupled)</span>
                      </span>
                    )}
                    {isSectorTheme && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center space-x-1">
                        <Compass className="w-3 h-3" />
                        <span>Sector Theme Trade</span>
                      </span>
                    )}
                    {mover.gap_percent !== undefined && Math.abs(mover.gap_percent) >= 1.0 && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        Gap: {mover.gap_percent > 0 ? `+${mover.gap_percent.toFixed(1)}%` : `${mover.gap_percent.toFixed(1)}%`}
                      </span>
                    )}
                  </div>
                </div>

                {/* Why It Moved Explanation */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-border-light dark:border-border-dark text-xs space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                    Why It Moved
                  </span>
                  <p className="text-slate-700 dark:text-slate-300 leading-relaxed line-clamp-2">
                    {mover.why_moved}
                  </p>
                </div>

                {/* Footer Action: Open In-Depth Quant Analysis */}
                <div className="pt-1 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-mono">
                    Sector: {mover.sector_change_percent !== undefined ? `${mover.sector_change_percent > 0 ? '+' : ''}${mover.sector_change_percent.toFixed(1)}%` : 'N/A'}
                  </span>

                  {onSelectStock && (
                    <button
                      onClick={() => onSelectStock(mover.symbol)}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-xs font-semibold transition-all cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Full Analysis</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
