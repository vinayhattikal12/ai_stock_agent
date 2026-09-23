# Upstox API V2 Integration & Normalization Guide

This document details the Upstox API V2 integration layer implemented in `backend/services/market_data/`.

---

## 1. Upstox API Architecture

```
                                      +-----------------------------------------+
                                      |            Upstox API V2                |
                                      |  (api.upstox.com/v2 / assets.upstox.com)|
                                      +--------------------+--------------------+
                                                           |
                                                           v
                                              +------------------------+
                                              |     UpstoxProvider     |
                                              | (Bearer Auth, Retries) |
                                              +-----------+------------+
                                                          |
                                                          v
                                              +------------------------+
                                              |     DataNormalizer     |
                                              | (Standard Candle/Quote)|
                                              +-----------+------------+
                                                          |
                                                          v
                                              +------------------------+
                                              |   MarketDataService    |
                                              | (Cache + Seed Fallback)|
                                              +-----------+------------+
                                                          |
                                                          v
                               +--------------------------+--------------------------+
                               |                                                     |
                               v                                                     v
                     +-------------------+                                 +-------------------+
                     | Technical Engine  |                                 | Staged Scanner    |
                     +-------------------+                                 +-------------------+
```

---

## 2. API Endpoints Utilized

| Feature | Upstox Endpoint | Parameters | Normalization |
|---|---|---|---|
| **Quotes & LTP** | `GET /v2/market-quote/quotes` | `instrument_key=NSE_EQ\|TCS,NSE_INDEX\|Nifty 50` | Formats into `MarketIndexQuote` and `Quote` |
| **Historical Candles** | `GET /v2/historical-candle/{key}/{interval}/{to_date}/{from_date}` | `interval=day`, `from_date=2025-09-01` | Normalizes timestamp and converts `[ts, o, h, l, c, v, oi]` arrays to `Candle` objects |
| **Intraday Candles** | `GET /v2/historical-candle/intraday/{key}/{interval}` | `interval=1minute` | Real-time session monitoring |
| **Instrument Master** | `GET https://assets.upstox.com/market-quote/instruments/exchange/NSE_EQ.json.gz` | `exchange=NSE_EQ` | Caches ISIN codes and lot sizes |

---

## 3. Configuration & Security

The Upstox token is securely loaded on the backend via `.env`:
```bash
UPSTOX_ACCESS_TOKEN=eyJ0eXAiOiJKV1Qi...
UPSTOX_API_VERSION=v2
```

- Tokens are **never** exposed in frontend bundles or responses.
- If an access token expires (Upstox tokens expire daily at 03:30 AM IST), the system falls back to normalized cached historical feeds and alerts the user on the Settings screen.
