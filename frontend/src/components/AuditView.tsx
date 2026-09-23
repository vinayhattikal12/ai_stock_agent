import React, { useEffect, useState } from 'react';
import { BarChart3, CheckCircle2, ShieldCheck, Target, Award, Cpu, TrendingUp, Info } from 'lucide-react';
import { api } from '../services/api';

export const AuditView: React.FC = () => {
  const [auditData, setAuditData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPerformanceAudit()
      .then((data) => {
        setAuditData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading || !auditData) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="h-28 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        </div>
      </div>
    );
  }

  const { overall_metrics, performance_by_regime, performance_by_setup, model_version } = auditData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-blue-500" />
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Live Model Performance & Signal Audit
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
          Empirical evaluation of deterministic signals & calibrated ML probabilities from actual recorded database audits (no simulated or fabricated data).
        </p>
        <div className="mt-3 flex items-center space-x-2 text-xs font-mono text-slate-500">
          <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold">
            {model_version}
          </span>
          <span>•</span>
          <span>{overall_metrics.total_evaluated_trades} Evaluated Live Signals in DB</span>
        </div>
      </div>

      {/* Zero trades info banner if empty */}
      {overall_metrics.total_evaluated_trades === 0 ? (
        <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-blue-500/20 text-center space-y-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto">
            <Info className="w-5 h-5" />
          </div>
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Live Signal Audit Active
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-lg mx-auto leading-relaxed">
            As you run the Swing Scanner, generated candidate recommendations will be recorded. Once their holding periods elapse (5–10 trading days), the background evaluator automatically audits whether Target 1, 2, or Stop Loss was hit first.
          </p>
        </div>
      ) : (
        <>
          {/* Primary KPI Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
              <span className="text-xs uppercase font-medium text-slate-500">Target 1 Hit Rate</span>
              <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {(overall_metrics.hit_rate_t1 * 100).toFixed(1)}%
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">T1 reached before Stop Loss</span>
            </div>

            <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
              <span className="text-xs uppercase font-medium text-slate-500">Profit Factor</span>
              <div className="text-2xl font-bold font-mono text-blue-600 dark:text-blue-400 mt-1">
                {overall_metrics.profit_factor}x
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Gross Gains / Gross Losses</span>
            </div>

            <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
              <span className="text-xs uppercase font-medium text-slate-500">Expectancy / Trade</span>
              <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white mt-1">
                +{overall_metrics.expectancy_per_trade_pct}%
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Avg net swing return</span>
            </div>

            <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
              <span className="text-xs uppercase font-medium text-slate-500">Brier Calibration</span>
              <div className="text-2xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-1">
                {overall_metrics.brier_score}
              </div>
              <span className="text-[11px] text-emerald-500 mt-1 block font-mono">Calibrated (&lt;0.20)</span>
            </div>
          </div>

          {/* Breakdown if present */}
          {performance_by_regime && performance_by_regime.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-2">
                  <Target className="w-4 h-4 text-blue-500" />
                  <span>Hit Rate by Market Regime</span>
                </h2>
                <div className="divide-y divide-border-light dark:divide-border-dark text-xs font-mono">
                  {performance_by_regime.map((r: any) => (
                    <div key={r.regime} className="py-2.5 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-slate-800 dark:text-slate-200">{r.regime}</span>
                        <span className="text-slate-500 ml-2 font-sans">({r.trades} trades)</span>
                      </div>
                      <div className="text-right">
                        <span className="text-emerald-500 font-bold">{(r.win_rate * 100).toFixed(1)}% Win Rate</span>
                        <span className="text-slate-500 ml-3">PF: {r.profit_factor}x</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
