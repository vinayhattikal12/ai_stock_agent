import React from 'react';
import { Briefcase, ArrowUpRight, ArrowDownRight, ChevronRight, Plus } from 'lucide-react';
import { PortfolioSummaryResponse } from '../types';

interface PortfolioWidgetProps {
  portfolio: PortfolioSummaryResponse | null;
  onViewAllClick: () => void;
  onStockClick: (symbol: string) => void;
}

export const PortfolioWidget: React.FC<PortfolioWidgetProps> = ({
  portfolio,
  onViewAllClick,
  onStockClick,
}) => {
  if (!portfolio) return null;

  const total_invested = portfolio.total_invested || 0;
  const current_value = portfolio.current_value || 0;
  const total_pnl = portfolio.total_pnl || 0;
  const total_pnl_pct = portfolio.total_pnl_pct || 0;
  const holdings = portfolio.holdings || [];

  const getSignalBadge = (signal?: string) => {
    switch (signal) {
      case 'BUY MORE':
        return 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'HOLD':
        return 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'WATCH':
        return 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'REDUCE':
      case 'SELL':
        return 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30';
    }
  };

  const formatINR = (val?: number) => (val !== undefined && val !== null ? Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00');

  return (
    <div className="space-y-3 my-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-2">
          <Briefcase className="w-4 h-4" />
          <span>My Portfolio</span>
        </h2>
        <button
          onClick={onViewAllClick}
          className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
        >
          <span>{holdings.length > 0 ? 'Manage Holdings' : '+ Add First Holding'}</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
        {/* Top Aggregates */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-4 border-b border-border-light dark:border-border-dark">
          <div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-medium">Total Invested</span>
            <div className="text-lg font-bold font-mono text-slate-900 dark:text-white mt-0.5">
              ₹{formatINR(total_invested)}
            </div>
          </div>
          <div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-medium">Current Value</span>
            <div className="text-lg font-bold font-mono text-slate-900 dark:text-white mt-0.5">
              ₹{formatINR(current_value)}
            </div>
          </div>
          <div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-medium">Total P&L</span>
            <div className={`text-lg font-bold font-mono mt-0.5 flex items-center space-x-1 ${
              total_pnl >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
            }`}>
              <span>{total_pnl >= 0 ? '+' : ''}₹{formatINR(Math.abs(total_pnl))}</span>
            </div>
          </div>
          <div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-medium">Overall Return</span>
            <div className={`text-lg font-bold font-mono mt-0.5 ${
              total_pnl >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
            }`}>
              {total_pnl >= 0 ? '+' : ''}{total_pnl_pct.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Holdings Quick Rows */}
        {holdings.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 dark:text-slate-400 space-y-2">
            <p>No active stock investments tracked yet.</p>
            <button
              onClick={onViewAllClick}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40 hover:bg-blue-100"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Your First Position</span>
            </button>
          </div>
        ) : (
          <div className="divide-y divide-border-light dark:divide-border-dark mt-2">
            {holdings.map((h) => (
              <div
                key={h.id}
                onClick={() => onStockClick(h.symbol)}
                className="py-3 px-2 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/40 rounded-lg cursor-pointer transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-300 font-mono">
                    {h.symbol.slice(0, 3)}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-bold text-slate-900 dark:text-white font-mono">{h.symbol}</span>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${getSignalBadge(h.signal)}`}>
                        {h.signal}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {h.quantity} shares @ ₹{formatINR(h.buy_price)}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm font-mono font-bold text-slate-900 dark:text-white">
                    ₹{formatINR(h.current_price)}
                  </div>
                  <div className={`text-xs font-mono font-semibold flex items-center justify-end space-x-0.5 ${
                    (h.unrealized_pnl || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                  }`}>
                    {(h.unrealized_pnl || 0) >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                    <span>{(h.unrealized_pnl || 0) >= 0 ? '+' : ''}{(h.unrealized_pnl_pct || 0).toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

