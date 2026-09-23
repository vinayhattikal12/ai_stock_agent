import React, { useState } from 'react';
import { Calculator, ShieldAlert, TrendingUp, DollarSign, Percent } from 'lucide-react';
import { TradeLevels, RiskManagementMetrics } from '../types';

interface PositionSizingWidgetProps {
  levels: TradeLevels;
  currentPrice: number;
  winProbability?: number;
  initialCapital?: number;
  initialRiskPct?: number;
  onApplyQuantity?: (qty: number) => void;
}

export const PositionSizingWidget: React.FC<PositionSizingWidgetProps> = ({
  levels,
  currentPrice,
  winProbability = 0.60,
  initialCapital = 500000,
  initialRiskPct = 1.0,
  onApplyQuantity
}) => {
  const [capital, setCapital] = useState<number>(initialCapital);
  const [riskPct, setRiskPct] = useState<number>(initialRiskPct);

  const entryPrice = levels.reference_entry || currentPrice;
  const stopLossPrice = levels.stop_loss || (entryPrice * 0.965);
  const target1Price = levels.target_1 || (entryPrice * 1.06);

  const riskPerShare = Math.max(0.1, entryPrice - stopLossPrice);
  const maxRiskInr = Math.round(capital * (riskPct / 100.0));
  
  // Sizing formula
  const rawShares = Math.floor(maxRiskInr / riskPerShare);
  const maxCapitalForStock = capital * 0.20; // 20% cap
  const maxSharesByCap = Math.floor(maxCapitalForStock / entryPrice);
  const suggestedShares = Math.min(rawShares, maxSharesByCap);
  const isCapped = rawShares > maxSharesByCap;

  const allocatedCapital = Math.round(suggestedShares * entryPrice);
  const portfolioAllocPct = capital > 0 ? ((allocatedCapital / capital) * 100).toFixed(1) : '0.0';
  const actualRiskInr = Math.round(suggestedShares * riskPerShare);

  // Expected Value Calculation
  const pWin = winProbability;
  const pLoss = 1.0 - pWin;
  const rewardT1 = Math.max(0.1, target1Price - entryPrice);
  const evPerShare = (pWin * rewardT1) - (pLoss * riskPerShare);
  const totalEvInr = Math.round(evPerShare * suggestedShares);

  // Kelly Fraction (Half-Kelly)
  const bRatio = rewardT1 / riskPerShare;
  const kellyFraction = Math.max(0, (pWin * bRatio - pLoss) / bRatio);
  const halfKellyPct = (kellyFraction / 2.0 * 100).toFixed(1);

  const formatINR = (val: number) => val.toLocaleString('en-IN', { maximumFractionDigits: 2 });

  return (
    <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 text-white shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
            <Calculator className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight">1% Account Risk Position Sizer</h3>
            <p className="text-[11px] text-slate-400">Institutional capital preservation formula</p>
          </div>
        </div>

        <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          EV: {totalEvInr >= 0 ? '+' : ''}₹{formatINR(totalEvInr)}
        </span>
      </div>

      {/* Input controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] font-semibold uppercase text-slate-400 mb-1">
            Trading Capital (₹)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-2 text-xs font-mono text-slate-500">₹</span>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Math.max(10000, Number(e.target.value)))}
              className="w-full pl-7 pr-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-sm font-mono text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex gap-1 mt-1">
            {[100000, 250000, 500000, 1000000].map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCapital(c)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${
                  capital === c ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                ₹{c / 100000}L
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="block text-[11px] font-semibold uppercase text-slate-400">
              Risk Per Trade ({riskPct}%)
            </label>
            <span className="text-[10px] font-mono text-rose-400 font-bold">
              Max Risk: ₹{formatINR(maxRiskInr)}
            </span>
          </div>
          <div className="flex gap-1.5 pt-0.5">
            {[0.5, 1.0, 1.5, 2.0].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRiskPct(r)}
                className={`flex-1 py-1.5 rounded-xl text-xs font-mono font-bold transition-colors border ${
                  riskPct === r
                    ? 'bg-blue-600 text-white border-blue-500 shadow-sm'
                    : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700'
                }`}
              >
                {r}%
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Calculated Results Box */}
      <div className="grid grid-cols-3 gap-2 p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 font-mono text-center">
        <div>
          <span className="text-[10px] uppercase font-sans text-slate-400 block">Suggested Shares</span>
          <div className="text-lg font-bold text-blue-400 mt-0.5">
            {suggestedShares} <span className="text-xs font-normal text-slate-400">shares</span>
          </div>
        </div>

        <div>
          <span className="text-[10px] uppercase font-sans text-slate-400 block">Position Value</span>
          <div className="text-lg font-bold text-white mt-0.5">
            ₹{formatINR(allocatedCapital)}
          </div>
        </div>

        <div>
          <span className="text-[10px] uppercase font-sans text-slate-400 block">Total Risk</span>
          <div className="text-lg font-bold text-rose-400 mt-0.5">
            ₹{formatINR(actualRiskInr)}
          </div>
        </div>
      </div>

      {/* Footer Notes & Action */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] pt-1">
        <div className="text-slate-400 space-y-0.5">
          <div>
            Allocation: <strong className="text-slate-200">{portfolioAllocPct}%</strong> of portfolio
            {isCapped && <span className="text-amber-400 font-semibold ml-1">(20% Single-Stock Cap)</span>}
          </div>
          <div>
            Half-Kelly Optimal: <strong className="text-slate-200">{halfKellyPct}%</strong> of capital
          </div>
        </div>

        {onApplyQuantity && (
          <button
            type="button"
            onClick={() => onApplyQuantity(suggestedShares)}
            className="w-full sm:w-auto px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-md"
          >
            Apply {suggestedShares} Shares
          </button>
        )}
      </div>
    </div>
  );
};
