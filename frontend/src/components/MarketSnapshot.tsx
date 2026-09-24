import React from 'react';
import { Layers, ArrowUpRight, ArrowDownRight, Newspaper, BarChart2 } from 'lucide-react';
import { MarketStatusResponse } from '../types';

interface MarketSnapshotProps {
  marketStatus: MarketStatusResponse | null;
  onStockSelect: (symbol: string) => void;
}

export const MarketSnapshot: React.FC<MarketSnapshotProps> = ({ marketStatus, onStockSelect }) => {
  if (!marketStatus) return null;

  const breadth = marketStatus.breadth || {
    advances: 0,
    declines: 0,
    unchanged: 0,
    ad_ratio: 1.0,
    pct_above_20_ema: 50.0,
    pct_above_50_ema: 50.0,
    pct_above_200_ema: 50.0,
    highs_52w_count: 0,
    lows_52w_count: 0
  };
  const strong_sectors = marketStatus.strong_sectors || [];
  const weak_sectors = marketStatus.weak_sectors || [];
  const major_events = marketStatus.major_events || [];

  const totalBreadth = (breadth.advances || 0) + (breadth.declines || 0);
  const advPct = totalBreadth > 0 ? ((breadth.advances || 0) / totalBreadth) * 100 : 50;

  return (
    <div className="space-y-4 my-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-2">
          <Layers className="w-4 h-4" />
          <span>Market Snapshot & Sector Breadth</span>
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Market Breadth Card */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center justify-between pb-2 border-b border-border-light dark:border-border-dark mb-3">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Market Breadth (Liquid Universe)
            </span>
            <span className="text-xs font-mono text-slate-500">
              A/D: <strong className="text-slate-800 dark:text-slate-200">{breadth.ad_ratio || 1.0}x</strong>
            </span>
          </div>

          <div className="space-y-3">
            {/* Advances vs Declines Bar */}
            <div>
              <div className="flex justify-between text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{breadth.advances || 0} Advances</span>
                <span className="text-rose-600 dark:text-rose-400 font-semibold">{breadth.declines || 0} Declines</span>
              </div>
              <div className="w-full h-2 bg-rose-500/20 rounded-full overflow-hidden flex">
                <div 
                  className="h-full bg-emerald-500" 
                  style={{ width: `${advPct}%` }}
                ></div>
              </div>
            </div>

            {/* EMA Percentage Gauges */}
            <div className="grid grid-cols-3 gap-2 pt-2 text-center font-mono">
              <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Above 20 EMA</div>
                <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{breadth.pct_above_20_ema || 0}%</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Above 50 EMA</div>
                <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{breadth.pct_above_50_ema || 0}%</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Above 200 EMA</div>
                <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{breadth.pct_above_200_ema || 0}%</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sector Strength & Weakness Card */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center justify-between pb-2 border-b border-border-light dark:border-border-dark mb-3">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Sector Rotation & Leadership
            </span>
            <span className="text-[11px] text-blue-500 font-medium">Relative vs Nifty</span>
          </div>

          <div className="space-y-2">
            {/* Strong Sectors */}
            {strong_sectors.slice(0, 2).map((sec) => (
              <div 
                key={sec.symbol} 
                className="flex items-center justify-between p-2 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-800/30 text-xs"
              >
                <div className="flex items-center space-x-2">
                  <ArrowUpRight className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{sec.sector_name}</span>
                  {sec.top_driver && (
                    <button
                      onClick={() => onStockSelect(sec.top_driver!)}
                      className="px-1.5 py-0.2 rounded bg-emerald-100 dark:bg-emerald-900/50 text-[10px] font-mono text-emerald-700 dark:text-emerald-300 hover:underline"
                    >
                      {sec.top_driver}
                    </button>
                  )}
                </div>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                  +{((sec.change_percent_1d ?? (sec as any).change_percent) || 0).toFixed(2)}%
                </span>
              </div>
            ))}

            {/* Weak Sectors */}
            {weak_sectors.slice(0, 2).map((sec) => (
              <div 
                key={sec.symbol} 
                className="flex items-center justify-between p-2 rounded-lg bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/50 dark:border-rose-800/30 text-xs"
              >
                <div className="flex items-center space-x-2">
                  <ArrowDownRight className="w-3.5 h-3.5 text-rose-500" />
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{sec.sector_name}</span>
                  {sec.top_driver && (
                    <button
                      onClick={() => onStockSelect(sec.top_driver!)}
                      className="px-1.5 py-0.2 rounded bg-rose-100 dark:bg-rose-900/50 text-[10px] font-mono text-rose-700 dark:text-rose-300 hover:underline"
                    >
                      {sec.top_driver}
                    </button>
                  )}
                </div>
                <span className="font-mono font-bold text-rose-600 dark:text-rose-400">
                  {((sec.change_percent_1d ?? (sec as any).change_percent) || 0).toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Major Macro & Market Events */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <div className="flex items-center justify-between pb-2 border-b border-border-light dark:border-border-dark mb-3">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center space-x-1.5">
              <Newspaper className="w-3.5 h-3.5 text-blue-500" />
              <span>Key Catalysts & Flow Intelligence</span>
            </span>
          </div>

          <div className="space-y-2">
            {major_events.map((event, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-xs text-slate-600 dark:text-slate-400">
                <span className="text-blue-500 mt-0.5">•</span>
                <span className="leading-relaxed">{event}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
