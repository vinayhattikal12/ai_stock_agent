# AI-Powered Indian Equity Intelligence Platform

A personal swing-trading decision-support and market-intelligence platform for Indian Equities (NSE/BSE).

---

## Key Features

1. **Two Primary Actions (Zero Prompting Required)**:
   - **`[ Search New Stocks ]`**: Multi-stage quantitative funnel (5,000+ $\rightarrow$ Liquidity $\rightarrow$ Market Regime $\rightarrow$ Sector Strength $\rightarrow$ Breakout/Pullback Setups $\rightarrow$ Candlesticks $\rightarrow$ Relative Strength $\rightarrow$ ML Probabilities $\rightarrow$ **Top 1–5 Opportunities** or **NO TRADE TODAY**).
   - **`[ Analyse My Investments ]`**: Track holdings with automated signals (`BUY MORE`, `HOLD`, `WATCH`, `REDUCE`, `SELL`), live P&L, dynamic S/R & ATR levels, and continuous thesis health tracking (`STRENGTHENING`, `STABLE`, `WEAKENING`, `BROKEN`).
2. **Deterministic Quantitative Foundation**:
   - SMA/EMA (20, 50, 200), RSI (14), MACD (12, 26, 9), ATR (14), ADX (14), Bollinger Bands, SuperTrend, dynamic Pivot Support/Resistance zones.
   - Multi-candle pattern recognition with trend context validation (Hammer, Shooting Star, Engulfing, Morning/Evening Star, Marubozu, Pin Bar, Inside Bar, Doji).
   - Mansfield Relative Strength vs NIFTY 50 and Sector Benchmarks over 5D, 10D, 20D, 50D, 100D.
3. **Calibrated Machine Learning Engine**:
   - Triple-barrier probability modeling predicting $P(\text{Target 1 before Stop Loss})$ within 5–10 trading days.
   - Walk-forward chronological cross-validation with Brier calibration scores.
4. **Real Upstox Market Data Integration**:
   - Secure server-side Upstox API v2 provider (`UpstoxProvider`) with automated data normalization.
5. **Modern Minimalist Fintech UI (Linear / Apple / Stripe feel)**:
   - Built with React 18, Vite, TypeScript, Tailwind CSS, and TradingView Lightweight Charts.
   - Seamless Dark & Light themes with clean typography and progressive disclosure.

---

## Directory Structure

```
ai_stock/
├── backend/
│   ├── api/routes/          # FastAPI routers (market, scanner, portfolio, stocks, audit, settings)
│   ├── models/              # Pydantic schemas & SQLAlchemy DB models
│   ├── services/
│   │   ├── market_data/     # Upstox API v2 provider, normalizer, and seed cache
│   │   ├── quant/           # Technical, Candlestick, Liquidity, RS, Market, and Scanner engines
│   │   ├── ml/              # Feature pipeline, calibrated classifier, walk-forward validator
│   │   ├── portfolio/       # Portfolio & Thesis evaluation engines
│   │   ├── news/            # Corporate actions & event risk tracker
│   │   └── scheduler/       # Autonomous background jobs & alert feed
│   ├── config.py            # Environment configuration
│   └── main.py              # FastAPI application entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, MarketHeader, ActionButtons, TradingViewChart, Scanner, Portfolio, etc.
│   │   ├── services/        # Typed API client
│   │   ├── types/           # TypeScript domain definitions
│   │   ├── App.tsx          # Master application shell
│   │   └── main.tsx         # React entrypoint
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── tests/                   # Automated unit & integration tests
├── scripts/                 # Test runners and utilities
├── docs/                    # Architecture and Upstox guides
├── .env                     # Environment variables (Upstox token)
└── requirements.txt         # Python dependencies
```

---

---

## 🚀 Production Deployment Guide

### A. Push Project to GitHub

1. Open your terminal in the project root directory (`ai_stock`):
```bash
# Initialize git repository if not already initialized
git init

# Add all files (secrets and node_modules are automatically ignored by .gitignore)
git add .

# Create initial commit
git commit -m "feat: complete institutional AI equity swing intelligence platform"

# Set main branch
git branch -M main

# Add your GitHub remote repository
git remote add origin https://github.com/vinayhattikal12/ai_stock_agent.git

# Push to GitHub
git push -u origin main --force
```

---

---

### B. Deploy Backend to Render

1. Go to [Render.com](https://render.com) and sign in.
2. Click **"New +"** $\rightarrow$ **"Web Service"**.
3. Connect your GitHub repository: `vinayhattikal12/ai_stock_agent`.
4. Render will automatically detect [`render.yaml`](./render.yaml). Or configure manually:
   - **Name**: `ai-stock-backend`
   - **Language / Runtime**: `Python 3`
   - **Region**: `Singapore` (or nearest)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
5. In **Environment Variables**, add:
   - `UPSTOX_ACCESS_TOKEN` = *your_upstox_api_token*
   - `ENVIRONMENT` = `production`
   - `CORS_ORIGINS` = `*`
6. Click **"Create Web Service"**.
7. Once deployed, copy your Render URL (e.g. `https://ai-stock-backend.onrender.com`).
8. Verify the health check at `https://ai-stock-backend.onrender.com/health` (returns `{"status": "UP"}`).

---

### C. Deploy Frontend to Vercel

1. Go to [Vercel.com](https://vercel.com) and click **"Add New Project"**.
2. Import your GitHub repository: `vinayhattikal12/ai_stock_agent`.
3. Configure the Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select **`frontend`** *(Important!)*
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. In **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://ai-stock-backend.onrender.com` *(Your Render backend URL from Step B)*
5. Click **"Deploy"**. Vercel will build and launch your fintech dashboard globally in ~1 minute.

---

## 💻 Local Development Setup

### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API documentation live at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend

# Install Node modules
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Automated Test Verification
```bash
pytest tests/
```

