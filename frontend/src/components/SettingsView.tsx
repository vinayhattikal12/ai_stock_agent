import React, { useEffect, useState } from 'react';
import { Settings, ShieldCheck, Key, Clock, Bell, RefreshCw, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export const SettingsView: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [tokenInput, setTokenInput] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = () => {
    api.getSystemStatus().then(setStatus).catch(console.error);
    api.getAlerts().then(setAlerts).catch(console.error);
  };

  const handleUpdateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;
    setIsUpdating(true);
    try {
      await api.updateUpstoxToken(tokenInput.trim());
      setSuccessMsg('Upstox Access Token updated successfully.');
      setTokenInput('');
      loadStatus();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setIsUpdating(false);
    }
  };

  if (!status) {
    return <div className="animate-pulse h-64 bg-slate-200 dark:bg-slate-800 rounded-2xl"></div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-blue-500" />
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            System Connectivity & Automation Settings
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Configure real-time Upstox data provider credentials and monitor autonomous background synchronization schedules.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upstox API Configuration */}
        <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
            <span className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Key className="w-4 h-4 text-blue-500" />
              <span>Upstox API v2 Integration</span>
            </span>
            <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Connected</span>
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800 font-mono">
              <span className="text-slate-500 font-sans">Active Token:</span>
              <span className="text-slate-800 dark:text-slate-200">{status.token_masked}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800 font-mono">
              <span className="text-slate-500 font-sans">Data Normalization:</span>
              <span className="text-emerald-500 font-bold">ACTIVE (NSE/BSE v2)</span>
            </div>
            <div className="flex justify-between py-1 font-mono">
              <span className="text-slate-500 font-sans">Environment:</span>
              <span className="text-slate-800 dark:text-slate-200 uppercase">{status.environment}</span>
            </div>
          </div>

          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-600 dark:text-emerald-400 font-semibold flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleUpdateToken} className="space-y-3 pt-2">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Update Upstox Access Token
            </label>
            <input
              type="text"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="Paste new daily JWT access token..."
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-border-light dark:border-border-dark text-xs font-mono focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={isUpdating || !tokenInput.trim()}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 transition-all"
            >
              {isUpdating ? 'Updating...' : 'Save & Reconnect'}
            </button>
          </form>
        </div>

        {/* Autonomous Scheduled Background Tasks */}
        <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
            <span className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Clock className="w-4 h-4 text-blue-500" />
              <span>Scheduled Autonomous Jobs</span>
            </span>
            <span className="text-xs text-slate-500 font-mono">Runs without browser open</span>
          </div>

          <div className="space-y-2.5">
            {status.scheduler?.jobs?.map((job: any, idx: number) => (
              <div key={idx} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/40 flex items-start justify-between gap-2 text-xs">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{job.time}</span>
                    <span className="font-semibold text-slate-900 dark:text-white">{job.job_name}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{job.detail}</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  job.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-500' : 
                  (job.status === 'ACTIVE' ? 'bg-blue-500/10 text-blue-500 animate-pulse' : 'bg-slate-500/10 text-slate-500')
                }`}>
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Alert Stream */}
      <div className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
        <div className="flex items-center space-x-2">
          <Bell className="w-4 h-4 text-amber-500" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Autonomous Alert Logs
          </h2>
        </div>

        {alerts.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 dark:text-slate-400">
            No active alert triggers recorded yet in current session. Alerts are generated dynamically during live market monitoring.
          </div>
        ) : (
          <div className="divide-y divide-border-light dark:divide-border-dark text-xs">
            {alerts.map((a: any) => (
              <div key={a.id} className="py-2.5 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="font-mono font-semibold text-slate-500">{a.timestamp}</span>
                  <span className="font-mono font-bold text-slate-900 dark:text-white">[{a.symbol}]</span>
                  <span className="text-slate-700 dark:text-slate-300">{a.message}</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono">
                  {a.type}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
