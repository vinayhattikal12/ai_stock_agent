import {
  MarketStatusResponse,
  ScannerScanResponse,
  PortfolioSummaryResponse,
  StockFullAnalysisResponse,
  HoldingAnalysis,
  HistoricalScanSummary
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, '') : '';
const API_BASE = `${BASE_URL}/api`;

async function handleResponse<T>(res: Response, fallbackError: string): Promise<T> {
  if (!res.ok) {
    let errMsg = fallbackError;
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch {
      errMsg = `${fallbackError} (${res.status} ${res.statusText})`;
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  async getMarketStatus(): Promise<MarketStatusResponse> {
    const res = await fetch(`${API_BASE}/market/status`);
    return handleResponse<MarketStatusResponse>(res, 'Failed to fetch market status');
  },

  async getUniverse(): Promise<{ symbol: string; name: string; sector: string; market_cap_category?: string }[]> {
    const res = await fetch(`${API_BASE}/stocks/universe`);
    return handleResponse<{ symbol: string; name: string; sector: string; market_cap_category?: string }[]>(res, 'Failed to fetch stock universe');
  },

  async runScanner(): Promise<ScannerScanResponse> {
    const res = await fetch(`${API_BASE}/scanner/scan`);
    return handleResponse<ScannerScanResponse>(res, 'Failed to run scanner');
  },

  async getLatestScan(): Promise<ScannerScanResponse> {
    const res = await fetch(`${API_BASE}/scanner/latest`);
    return handleResponse<ScannerScanResponse>(res, 'Failed to fetch latest scan');
  },

  async getScanHistory(): Promise<HistoricalScanSummary[]> {
    const res = await fetch(`${API_BASE}/scanner/history`);
    return handleResponse<HistoricalScanSummary[]>(res, 'Failed to fetch scan history');
  },

  async getScanByDate(dateOrId: string): Promise<ScannerScanResponse> {
    const res = await fetch(`${API_BASE}/scanner/history/${dateOrId}`);
    return handleResponse<ScannerScanResponse>(res, `Failed to fetch scan for ${dateOrId}`);
  },

  async getPortfolio(): Promise<PortfolioSummaryResponse> {
    const res = await fetch(`${API_BASE}/portfolio`);
    return handleResponse<PortfolioSummaryResponse>(res, 'Failed to fetch portfolio');
  },

  async addHolding(data: {
    symbol: string;
    quantity: number;
    buy_price: number;
    purchase_date: string;
    notes?: string;
  }): Promise<HoldingAnalysis> {
    const res = await fetch(`${API_BASE}/portfolio/holdings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<HoldingAnalysis>(res, 'Failed to add holding');
  },

  async deleteHolding(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/portfolio/holdings/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res, 'Failed to delete holding');
  },

  async getQuote(symbol: string): Promise<{ symbol: string; price: number; change: number; change_percent: number }> {
    const res = await fetch(`${API_BASE}/stocks/${symbol}/quote`);
    return handleResponse<{ symbol: string; price: number; change: number; change_percent: number }>(res, `Failed to fetch quote for ${symbol}`);
  },

  async getStockAnalysis(symbol: string): Promise<StockFullAnalysisResponse> {
    const res = await fetch(`${API_BASE}/stocks/${symbol}/analysis`);
    return handleResponse<StockFullAnalysisResponse>(res, `Failed to fetch analysis for ${symbol}`);
  },

  async getPerformanceAudit(): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/performance`);
    return handleResponse<any>(res, 'Failed to fetch performance audit');
  },

  async getAlerts(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/audit/alerts`);
    return handleResponse<any[]>(res, 'Failed to fetch alerts');
  },

  async getSystemStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/settings/status`);
    return handleResponse<any>(res, 'Failed to fetch settings status');
  },

  async updateUpstoxToken(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/settings/upstox-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });
    return handleResponse<any>(res, 'Failed to update Upstox token');
  }
};

