import React, { useEffect, useState } from 'react';
import { BarChart3, Target, Info, Activity, Play, RefreshCw, Layers, CheckCircle2, ShieldCheck, Cpu, Sliders } from 'lucide-react';
import { api } from '../services/api';

export const AuditView: React.FC = () => {
  const [auditData, setAuditData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [runningBacktest, setRunningBacktest] = useState(false);
  const [trainingModel, setTrainingModel] = useState(false);
  const [trainResult, setTrainResult] = useState<any>(null);

  const loadAudit = () => {
    setLoading(true);
    api.getPerformanceAudit()
      .then((data) => {
        setAuditData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadAudit();
  }, []);

  const handleRunBacktest = async () => {
    setRunningBacktest(true);
    try {
      const res = await api.runHistoricalBacktest();
      setAuditData(res);
    } catch (err) {
      console.error("Backtest error:", err);
    } finally {
      setRunningBacktest(false);
    }
  };

  const handleTrainModel = async () => {
    setTrainingModel(true);
    try {
      const res = await api.trainMLModel();
      setTrainResult(res);
      loadAudit();
    } catch (err) {
      console.error("Training error:", err);
    } finally {
      setTrainingModel(false);
    }
  };

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

  const { overall_metrics, performance_by_regime, performance_by_setup, probability_bucket_calibration, folds, model_version, validation_methodology, status, message, dataset_summary } = auditData;
  const isInsufficient = status === "INSUFFICIENT_HISTORY" || !overall_metrics?.hit_rate_t1;
  const completedCount = overall_metrics?.total_evaluated_trades || 0;
  const activeCount = overall_metrics?.active_trades_in_progress || 0;
  const featureImportances = trainResult?.feature_importances;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Model Performance & Signal Audit
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            {validation_methodology || "Empirical evaluation from verified closed trades and multi-year walk-forward replays."}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-mono text-slate-500">
            <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold">
              {model_version}
            </span>
            <span>•</span>
            <span>{completedCount} Evaluated Trades</span>
            {activeCount > 0 && (
              <>
                <span>•</span>
                <span>{activeCount} Live Signals Active</span>
              </>
            )}
            {dataset_summary?.total_lookback_years && (
              <>
                <span>•</span>
                <span>{dataset_summary.total_lookback_years} Years Backtested</span>
              </>
            )}
          </div>
        </div>

        {/* Action Buttons: Run Backtest & Train ML Model */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleRunBacktest}
            disabled={runningBacktest}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold shadow-subtle disabled:opacity-50 transition-all cursor-pointer whitespace-nowrap"
          >
            {runningBacktest ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Replaying Bars...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Replay Historical Backtest</span>
              </>
            )}
          </button>

          <button
            onClick={handleTrainModel}
            disabled={trainingModel}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer whitespace-nowrap"
          >
            {trainingModel ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Fitting Calibrated Trees...</span>
              </>
            ) : (
              <>
                <Cpu className="w-4 h-4" />
                <span>Fit & Calibrate ML Models</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Training Result Notification */}
      {trainResult && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span className="font-semibold">
              Calibrated Gradient Boosting Models fitted successfully on {trainResult.total_samples} historical swing trades! (CV Brier Score: {trainResult.brier_score})
            </span>
          </div>
          <span className="font-mono text-slate-400">ROC-AUC: {trainResult.roc_auc}</span>
        </div>
      )}

      {/* Insufficient History Banner */}
      {isInsufficient ? (
        <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-amber-500/30 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-500 flex items-center justify-center mx-auto">
            <Activity className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Zero-Fallback Active: No Live Audit Metrics Yet
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xl mx-auto leading-relaxed">
              {message || "The platform enforces a strict Zero-Fallback Policy: No fabricated hit rates or synthetic metrics are displayed. Click 'Replay Historical Backtest' or 'Fit & Calibrate ML Models' above to compute genuine empirical performance."}
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Primary KPI Grid (Empirical Real Data) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
              <span className="text-xs uppercase font-medium text-slate-500">Target 1 Hit Rate</span>
              <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {(overall_metrics.hit_rate_t1 * 100).toFixed(1)}%
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">T1 reached before Stop Loss (10D)</span>
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
                {overall_metrics.expectancy_per_trade_pct > 0 ? `+${overall_metrics.expectancy_per_trade_pct}%` : `${overall_metrics.expectancy_per_trade_pct}%`}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Avg net swing return</span>
            </div>

            <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
              <span className="text-xs uppercase font-medium text-slate-500">Brier Score</span>
              <div className="text-2xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-1">
                {overall_metrics.brier_score ?? 'N/A'}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block font-mono">Empirical Probability Calibration</span>
            </div>
          </div>

          {/* Secondary KPIs (Sharpe, Sortino, Max Drawdown, Avg Holding) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark">
              <span className="text-[11px] text-slate-500 font-medium">Sharpe Ratio (Ann.)</span>
              <div className="text-lg font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                {overall_metrics.sharpe_ratio ?? 'N/A'}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark">
              <span className="text-[11px] text-slate-500 font-medium">Sortino Ratio</span>
              <div className="text-lg font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                {overall_metrics.sortino_ratio ?? 'N/A'}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark">
              <span className="text-[11px] text-slate-500 font-medium">Max Drawdown</span>
              <div className="text-lg font-bold font-mono text-rose-500 mt-0.5">
                {overall_metrics.max_drawdown_pct ? `-${overall_metrics.max_drawdown_pct}%` : 'N/A'}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark">
              <span className="text-[11px] text-slate-500 font-medium">Avg Holding Period</span>
              <div className="text-lg font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                {overall_metrics.avg_holding_days ? `${overall_metrics.avg_holding_days} Days` : 'N/A'}
              </div>
            </div>
          </div>

          {/* Feature Importance Section (if model fitted) */}
          {featureImportances && featureImportances.length > 0 && (
            <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-blue-500" />
                <span>Empirical Gini Feature Importances (Titted Gradient Boosting Trees)</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {featureImportances.slice(0, 8).map((f: any) => (
                  <div key={f.feature} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-border-light dark:border-border-dark space-y-1 text-xs">
                    <div className="flex justify-between font-mono">
                      <span className="text-slate-800 dark:text-slate-200 font-sans font-semibold">{f.feature}</span>
                      <span className="text-blue-500 font-bold">{f.weight_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, f.weight_pct * 4)}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Probability Calibration Table */}
          {probability_bucket_calibration && probability_bucket_calibration.length > 0 && (
            <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-purple-500" />
                <span>Empirical Probability Calibration (Predicted vs Actual OOS Hit Rate)</span>
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border-light dark:border-border-dark text-slate-500">
                      <th className="pb-2 font-medium">Predicted Probability Bucket</th>
                      <th className="pb-2 font-medium text-right">Sample Trades</th>
                      <th className="pb-2 font-medium text-right">Actual Historical Hit Rate</th>
                      <th className="pb-2 font-medium text-right">Bucket Brier Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-light dark:divide-border-dark font-mono">
                    {probability_bucket_calibration.map((b: any) => (
                      <tr key={b.predicted_bucket} className="py-2">
                        <td className="py-2 text-slate-800 dark:text-slate-200 font-sans font-medium">{b.predicted_bucket}</td>
                        <td className="py-2 text-right text-slate-500">{b.count}</td>
                        <td className="py-2 text-right text-emerald-500 font-bold">
                          {b.actual_hit_rate !== null ? `${(b.actual_hit_rate * 100).toFixed(1)}%` : 'N/A'}
                        </td>
                        <td className="py-2 text-right text-purple-400">{b.calibrated_brier ?? 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Walk-Forward Folds (Purged & Embargoed Cross-Validation) */}
          {folds && folds.length > 0 && (
            <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-blue-500" />
                <span>Purged & Embargoed Walk-Forward Cross-Validation Folds</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {folds.map((f: any) => (
                  <div key={f.fold_number} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-border-light dark:border-border-dark space-y-1.5 text-xs font-mono">
                    <div className="flex justify-between items-center text-slate-500 font-sans">
                      <span className="font-bold text-blue-600 dark:text-blue-400">Fold {f.fold_number}</span>
                      <span className="text-[10px]">{f.test_period}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-sans">OOS Win Rate:</span>
                      <span className="text-emerald-500 font-bold">{(f.hit_rate_t1 * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-sans">Profit Factor:</span>
                      <span>{f.profit_factor}x</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400 font-sans">
                      <span>Test Trades:</span>
                      <span>{f.test_samples}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
