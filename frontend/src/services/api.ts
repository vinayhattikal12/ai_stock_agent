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

async function fetchWithRetry(url: string, options?: RequestInit, maxRetries: number = 2): Promise<Response> {
  let lastError: any;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (res.status === 429 && attempt < maxRetries) {
        // Wait and retry on 429
        const delay = 1000 * (attempt + 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
        continue;
      }
      return res;
    } catch (err) {
      lastError = err;
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 800 * (attempt + 1)));
      }
    }
  }
  throw lastError || new Error('Network request failed after retries');
}

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
    const res = await fetchWithRetry(`${API_BASE}/market/status`);
    return handleResponse<MarketStatusResponse>(res, 'Failed to fetch market status');
  },

  async getTodaysMovers(): Promise<any> {
    const res = await fetchWithRetry(`${API_BASE}/market/movers`);
    return handleResponse<any>(res, 'Failed to fetch today\'s movers');
  },

  async getUniverse(): Promise<{ symbol: string; name: string; sector: string; market_cap_category?: string }[]> {
    const res = await fetchWithRetry(`${API_BASE}/stocks/universe`);
    return handleResponse<{ symbol: string; name: string; sector: string; market_cap_category?: string }[]>(res, 'Failed to fetch stock universe');
  },

  async runScanner(): Promise<ScannerScanResponse> {
    const res = await fetchWithRetry(`${API_BASE}/scanner/scan`);
    return handleResponse<ScannerScanResponse>(res, 'Failed to run scanner');
  },

  async getLatestScan(): Promise<ScannerScanResponse> {
    const res = await fetchWithRetry(`${API_BASE}/scanner/latest`);
    return handleResponse<ScannerScanResponse>(res, 'Failed to fetch latest scan');
  },

  async getScanHistory(): Promise<HistoricalScanSummary[]> {
    const res = await fetchWithRetry(`${API_BASE}/scanner/history`);
    return handleResponse<HistoricalScanSummary[]>(res, 'Failed to fetch scan history');
  },

  async getScanByDate(dateOrId: string): Promise<ScannerScanResponse> {
    const res = await fetchWithRetry(`${API_BASE}/scanner/history/${dateOrId}`);
    return handleResponse<ScannerScanResponse>(res, `Failed to fetch scan for ${dateOrId}`);
  },

  async getPortfolio(): Promise<PortfolioSummaryResponse> {
    const res = await fetchWithRetry(`${API_BASE}/portfolio`);
    return handleResponse<PortfolioSummaryResponse>(res, 'Failed to fetch portfolio');
  },

  async addHolding(data: {
    symbol: string;
    quantity: number;
    buy_price: number;
    purchase_date: string;
    notes?: string;
  }): Promise<HoldingAnalysis> {
    const res = await fetchWithRetry(`${API_BASE}/portfolio/holdings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<HoldingAnalysis>(res, 'Failed to add holding');
  },

  async deleteHolding(id: number): Promise<void> {
    const res = await fetchWithRetry(`${API_BASE}/portfolio/holdings/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res, 'Failed to delete holding');
  },

  async getQuote(symbol: string): Promise<{ symbol: string; price: number; change: number; change_percent: number }> {
    const res = await fetchWithRetry(`${API_BASE}/stocks/${symbol}/quote`);
    return handleResponse<{ symbol: string; price: number; change: number; change_percent: number }>(res, `Failed to fetch quote for ${symbol}`);
  },

  async getStockAnalysis(symbol: string): Promise<StockFullAnalysisResponse> {
    const res = await fetchWithRetry(`${API_BASE}/stocks/${symbol}/analysis`);
    return handleResponse<StockFullAnalysisResponse>(res, `Failed to fetch analysis for ${symbol}`);
  },

  async getPerformanceAudit(): Promise<any> {
    const res = await fetchWithRetry(`${API_BASE}/audit/performance`);
    return handleResponse<any>(res, 'Failed to fetch performance audit');
  },

  async runHistoricalBacktest(): Promise<any> {
    const res = await fetchWithRetry(`${API_BASE}/audit/backtest/run`, {
      method: 'POST'
    });
    return handleResponse<any>(res, 'Failed to execute historical backtest replay');
  },

  async trainMLModel(): Promise<any> {
    const res = await fetchWithRetry(`${API_BASE}/audit/model/train`, {
      method: 'POST'
    });
    return handleResponse<any>(res, 'Failed to train ML model');
  },

  async getAlerts(): Promise<any[]> {
    const res = await fetchWithRetry(`${API_BASE}/audit/alerts`);
    return handleResponse<any[]>(res, 'Failed to fetch alerts');
  },

  async getSystemStatus(): Promise<any> {
    const res = await fetchWithRetry(`${API_BASE}/settings/status`);
    return handleResponse<any>(res, 'Failed to fetch settings status');
  },

  async updateUpstoxToken(token: string): Promise<any> {
    const res = await fetchWithRetry(`${API_BASE}/settings/upstox-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });
    return handleResponse<any>(res, 'Failed to update Upstox token');
  }
};
