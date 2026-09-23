import React from 'react';
import { 
  TrendingUp, 
  Search, 
  Briefcase, 
  BarChart3, 
  Settings, 
  Sun, 
  Moon, 
  Activity,
  ShieldCheck
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isDark: boolean;
  setIsDark: (dark: boolean) => void;
  isUpstoxConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isDark,
  setIsDark,
  isUpstoxConnected,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
    { id: 'discover', label: 'Discover', icon: Search },
    { id: 'portfolio', label: 'My Investments', icon: Briefcase },
    { id: 'audit', label: 'Audit & Models', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <>
      {/* Desktop Top Navigation */}
      <header className="sticky top-0 z-40 w-full border-b border-border-light dark:border-border-dark bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo & Platform Name */}
          <div 
            onClick={() => setActiveTab('dashboard')} 
            className="flex items-center space-x-3 cursor-pointer select-none group"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-subtle group-hover:scale-105 transition-transform">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
                  Antigravity Equity
                </span>
                <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40">
                  NSE/BSE
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                Personal Swing Intelligence
              </p>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-slate-200/70 dark:bg-background-subtleDark text-slate-900 dark:text-white shadow-subtle'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Controls & Status */}
          <div className="flex items-center space-x-3">
            {/* Live Upstox Data Indicator */}
            <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-[11px] tracking-tight font-mono">Upstox v2 Live</span>
            </div>

            {/* Dark / Light Toggle */}
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors"
              aria-label="Toggle Theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-background-light/95 dark:bg-background-dark/95 border-t border-border-light dark:border-border-dark backdrop-blur-lg px-3 py-2 flex items-center justify-around">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg transition-colors ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400 font-semibold'
                  : 'text-slate-500 dark:text-slate-400'
              }`}
            >
              <Icon className="w-5 h-5 mb-0.5" />
              <span className="text-[10px] tracking-tight">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
};
