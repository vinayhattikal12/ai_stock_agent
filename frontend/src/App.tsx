import React, { useEffect, useState, Component, ErrorInfo, ReactNode } from 'react';
import { Navbar } from './components/Navbar';
import { MarketHeader } from './components/MarketHeader';
import { ActionButtons } from './components/ActionButtons';
import { MarketSnapshot } from './components/MarketSnapshot';
import { PortfolioWidget } from './components/PortfolioWidget';
import { WhatChangedFeed } from './components/WhatChangedFeed';
import { ScannerView } from './components/ScannerView';
import { PortfolioView } from './components/PortfolioView';
import { StockDetailView } from './components/StockDetailView';
import { AuditView } from './components/AuditView';
import { SettingsView } from './components/SettingsView';
import { api } from './services/api';
import { 
  MarketStatusResponse, 
  PortfolioSummaryResponse, 
  ScannerScanResponse, 
  StockFullAnalysisResponse 
} from './types';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Platform Render Error caught by ErrorBoundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6 text-center">
          <div className="max-w-md p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto text-xl font-bold">
              !
            </div>
            <h2 className="text-lg font-bold text-slate-100">Interface Recovery</h2>
            <p className="text-xs text-slate-400">
              An unexpected render issue occurred: {this.state.error?.message || 'Unknown error'}.
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all shadow-lg"
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export function MainApp() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [previousTab, setPreviousTab] = useState<string>('dashboard');
  const [isDark, setIsDark] = useState<boolean>(true);

  const [marketStatus, setMarketStatus] = useState<MarketStatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioSummaryResponse | null>(null);
  const [scanResult, setScanResult] = useState<ScannerScanResponse | null>(null);
  const [isScanning, setIsScanning] = useState<boolean>(false);

  const [selectedStockSymbol, setSelectedStockSymbol] = useState<string | null>(null);
  const [stockAnalysis, setStockAnalysis] = useState<StockFullAnalysisResponse | null>(null);
  const [isStockLoading, setIsStockLoading] = useState<boolean>(false);

  const [loadingInitial, setLoadingInitial] = useState<boolean>(true);

  // Sync theme class to <html>
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  // Initial load
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [marketRes, portRes, scanRes] = await Promise.allSettled([
        api.getMarketStatus(),
        api.getPortfolio(),
        api.getLatestScan(),
      ]);
      if (marketRes.status === 'fulfilled') setMarketStatus(marketRes.value);
      if (portRes.status === 'fulfilled') setPortfolio(portRes.value);
      if (scanRes.status === 'fulfilled' && scanRes.value) {
        setScanResult(scanRes.value);
      }
    } catch (e) {
      console.error('Error fetching initial platform data:', e);
    } finally {
      setLoadingInitial(false);
    }
  };

  const handleNavigateToPortfolio = async () => {
    setPreviousTab(activeTab);
    setActiveTab('portfolio');
    try {
      const portRes = await api.getPortfolio();
      setPortfolio(portRes);
    } catch (e) {
      console.error('Error refreshing portfolio:', e);
    }
  };

  const handleRunScanner = async () => {
    setPreviousTab(activeTab);
    setActiveTab('discover');
    setIsScanning(true);
    try {
      const result = await api.runScanner();
      setScanResult(result);
    } catch (e) {
      console.error('Error running scanner:', e);
    } finally {
      setIsScanning(false);
    }
  };

  const handleSelectHistoricalScan = async (dateOrId: string) => {
    setIsScanning(true);
    try {
      const result = await api.getScanByDate(dateOrId);
      setScanResult(result);
    } catch (e) {
      console.error(`Error loading historical scan for ${dateOrId}:`, e);
    } finally {
      setIsScanning(false);
    }
  };

  const handleViewStock = async (symbol: string) => {
    setSelectedStockSymbol(symbol);
    setPreviousTab(activeTab === 'stock_detail' ? 'dashboard' : activeTab);
    setActiveTab('stock_detail');
    setIsStockLoading(true);
    setStockAnalysis(null);
    try {
      const detail = await api.getStockAnalysis(symbol);
      setStockAnalysis(detail);
    } catch (e) {
      console.error(`Error loading analysis for ${symbol}:`, e);
    } finally {
      setIsStockLoading(false);
    }
  };

  const handleAddHolding = async (holdingData: {
    symbol: string;
    quantity: number;
    buy_price: number;
    purchase_date: string;
    notes?: string;
  }) => {
    try {
      await api.addHolding(holdingData);
      const updatedPort = await api.getPortfolio();
      setPortfolio(updatedPort);
    } catch (e: any) {
      alert(`Error adding holding: ${e.message}`);
    }
  };

  const handleDeleteHolding = async (id: number) => {
    if (!confirm('Remove this holding from personal swing tracking?')) return;
    try {
      await api.deleteHolding(id);
      const updatedPort = await api.getPortfolio();
      setPortfolio(updatedPort);
    } catch (e: any) {
      alert(`Error removing holding: ${e.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white pb-20 md:pb-8">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setPreviousTab(activeTab);
          setActiveTab(tab);
          if (tab === 'portfolio') {
            api.getPortfolio().then(setPortfolio).catch(console.error);
          }
        }}
        isDark={isDark}
        setIsDark={setIsDark}
        isUpstoxConnected={true}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* DASHBOARD TAB */}
        {activeTab === 'dashboard' && (
          <div className="space-y-2">
            {/* Top Market Status Banner & Index Quotes */}
            <MarketHeader marketStatus={marketStatus} loading={loadingInitial} />

            {/* Two Primary Prominent Actions */}
            <ActionButtons
              onSearchClick={handleRunScanner}
              onPortfolioClick={handleNavigateToPortfolio}
            />

            {/* Market Snapshot & Breadth */}
            <MarketSnapshot
              marketStatus={marketStatus}
              onStockSelect={handleViewStock}
            />

            {/* My Portfolio Snapshot */}
            <PortfolioWidget
              portfolio={portfolio}
              onViewAllClick={handleNavigateToPortfolio}
              onStockClick={handleViewStock}
            />

            {/* WHAT CHANGED? Delta Feed */}
            <WhatChangedFeed feed={portfolio?.what_changed_feed || []} />
          </div>
        )}

        {/* DISCOVER / SCANNER TAB */}
        {activeTab === 'discover' && (
          <ScannerView
            scanResult={scanResult}
            isScanning={isScanning}
            onTriggerScan={handleRunScanner}
            onSelectHistoricalScan={handleSelectHistoricalScan}
            onViewAnalysis={handleViewStock}
            onAddToPortfolio={(sym, price) => {
              handleAddHolding({
                symbol: sym,
                quantity: 10,
                buy_price: price,
                purchase_date: new Date().toISOString().split('T')[0],
              });
              alert(`Added ${sym} to your investments.`);
            }}
          />
        )}

        {/* MY INVESTMENTS / PORTFOLIO TAB */}
        {activeTab === 'portfolio' && (
          <PortfolioView
            portfolio={portfolio}
            loading={loadingInitial}
            onAddHolding={handleAddHolding}
            onDeleteHolding={handleDeleteHolding}
            onStockClick={handleViewStock}
          />
        )}

        {/* STOCK DETAIL VIEW */}
        {activeTab === 'stock_detail' && (
          <StockDetailView
            analysis={stockAnalysis}
            loading={isStockLoading}
            isDark={isDark}
            onBack={() => setActiveTab(previousTab === 'stock_detail' ? 'dashboard' : previousTab)}
            onAddToPortfolio={(sym, price) => {
              handleAddHolding({
                symbol: sym,
                quantity: 10,
                buy_price: price,
                purchase_date: new Date().toISOString().split('T')[0],
              });
              alert(`Added ${sym} to your investments.`);
            }}
          />
        )}

        {/* AUDIT & PERFORMANCE TAB */}
        {activeTab === 'audit' && <AuditView />}

        {/* SETTINGS TAB */}
        {activeTab === 'settings' && <SettingsView />}
      </main>
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <MainApp />
    </ErrorBoundary>
  );
}

export default App;

