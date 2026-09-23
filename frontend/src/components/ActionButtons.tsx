import React from 'react';
import { Search, Briefcase, Sparkles, ArrowRight } from 'lucide-react';

interface ActionButtonsProps {
  onSearchClick: () => void;
  onPortfolioClick: () => void;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onSearchClick,
  onPortfolioClick,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-6">
      {/* Primary Action 1: Search New Stocks */}
      <button
        onClick={onSearchClick}
        className="group relative flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-premium hover:shadow-glow-blue transition-all duration-200 transform hover:-translate-y-0.5 text-left overflow-hidden"
      >
        <div className="flex items-center space-x-4 z-10">
          <div className="w-12 h-12 rounded-xl bg-white/15 backdrop-blur-sm flex items-center justify-center text-white">
            <Search className="w-6 h-6 group-hover:scale-110 transition-transform" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight">Search New Stocks</span>
              <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
            </div>
            <p className="text-xs text-blue-100 font-medium mt-0.5">
              Autonomous multi-stage quant scan for Top swing setups
            </p>
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center group-hover:translate-x-1 transition-transform">
          <ArrowRight className="w-4 h-4 text-white" />
        </div>
      </button>

      {/* Primary Action 2: Analyse My Investments */}
      <button
        onClick={onPortfolioClick}
        className="group relative flex items-center justify-between p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark hover:border-blue-500/50 dark:hover:border-blue-500/50 shadow-subtle hover:shadow-premium transition-all duration-200 transform hover:-translate-y-0.5 text-left"
      >
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-800 dark:text-slate-100 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            <Briefcase className="w-6 h-6 group-hover:scale-110 transition-transform" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
              Analyse My Investments
            </span>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
              Review holdings, dynamic actions & thesis health
            </p>
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:translate-x-1 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 transition-all">
          <ArrowRight className="w-4 h-4 text-slate-600 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400" />
        </div>
      </button>
    </div>
  );
};
