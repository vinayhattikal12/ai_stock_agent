import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.models.schemas import MarketMoverItem, TodaysMoversResponse, MarketBreadth
from backend.services.market_data.data_service import data_service
from backend.services.news.event_tracker import news_engine
from backend.services.quant.sector_engine import sector_engine

logger = logging.getLogger("movers_engine")


class TodaysMoversEngine:
    """
    Real-Time Market Movers & Anomaly Detection Engine (Detection, Not Prediction).
    
    Identifies:
    1. Top Intraday Gainers & Losers across full NSE equities.
    2. Opening Gap-ups & Gap-downs.
    3. Unusual Relative Volume & Turnover Surges.
    4. Auto-attaches verified Exchange Corporate Announcements ("Why It Moved").
    5. Classifies Stock-Specific Catalysts vs. Sector Thematic Momentum.
    """

    @classmethod
    async def get_todays_movers(cls) -> TodaysMoversResponse:
        scan_time = datetime.utcnow()
        universe = data_service.get_supported_universe()
        symbols = [u["symbol"] for u in universe]

        # 1. Fetch live quotes for universe in rate-safe batches
        quotes = await data_service.provider.get_live_quote(symbols)

        # 2. Fetch sector rotation matrix for sector-vs-stock decoupling
        sector_matrix = await sector_engine.evaluate_sector_rotation()
        sector_chg_map = {
            s.sector_name.lower(): (s.change_percent_1d or 0.0) for s in sector_matrix
        }

        all_movers: List[Dict[str, Any]] = []

        for u in universe:
            sym = u["symbol"]
            q = quotes.get(sym)
            if not q or q.get("price", 0) <= 0:
                continue

            price = float(q.get("price", 0.0))
            prev_close = float(q.get("prev_close", 0.0)) or price
            open_price = float(q.get("open", 0.0)) or price
            chg_pct = float(q.get("change_percent", 0.0))
            vol = int(q.get("volume", 0))

            gap_pct = round(((open_price - prev_close) / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

            sector_name = u.get("sector", "Diversified")
            sec_chg = sector_chg_map.get(sector_name.lower(), 0.0)

            # Check corporate catalysts
            catalysts = news_engine.get_events_for_symbol(sym)
            top_cat = catalysts[0] if catalysts else None
            cat_headline = top_cat.headline if top_cat else None

            # Determine Catalyst Type (Stock-Specific vs Sector Theme)
            if abs(chg_pct) >= 2.5 and abs(sec_chg) <= 0.6:
                catalyst_type = "STOCK_SPECIFIC"
                if cat_headline:
                    why_moved = f"Company-Specific Catalyst: {cat_headline} (Moving independently from {sector_name} sector at {sec_chg:+.1f}%)."
                else:
                    why_moved = f"Stock-Specific Outperformance: Moving independently from {sector_name} sector ({sec_chg:+.1f}%)."
            elif abs(chg_pct) >= 2.0 and abs(sec_chg) >= 1.0 and (chg_pct * sec_chg > 0):
                catalyst_type = "SECTOR_THEME"
                why_moved = f"Sector Thematic Momentum: Moving in tandem with strong {sector_name} sector trend ({sec_chg:+.1f}%)."
            elif cat_headline:
                catalyst_type = "STOCK_SPECIFIC"
                why_moved = f"Exchange Disclosure: {cat_headline}"
            else:
                catalyst_type = "BROAD_MARKET"
                why_moved = f"Standard market price discovery in {sector_name} sector ({sec_chg:+.1f}%)."

            all_movers.append({
                "symbol": sym,
                "company_name": u.get("name", sym),
                "sector": sector_name,
                "price": price,
                "change_percent": chg_pct,
                "gap_percent": gap_pct,
                "volume": vol,
                "rvol": None,
                "catalyst_type": catalyst_type,
                "catalyst_headline": cat_headline,
                "sector_change_percent": sec_chg,
                "why_moved": why_moved
            })

        # 3. Categorize and Rank
        # Top Gainers
        gainers_sorted = sorted([m for m in all_movers if m["change_percent"] > 0], key=lambda x: x["change_percent"], reverse=True)
        top_gainers = [
            MarketMoverItem(**dict(m, movement_type="TOP_GAINER")) for m in gainers_sorted[:15]
        ]

        # Top Losers
        losers_sorted = sorted([m for m in all_movers if m["change_percent"] < 0], key=lambda x: x["change_percent"])
        top_losers = [
            MarketMoverItem(**dict(m, movement_type="TOP_LOSER")) for m in losers_sorted[:15]
        ]

        # Gap Movers (Opening gap magnitude >= 1.2%)
        gap_sorted = sorted(all_movers, key=lambda x: abs(x["gap_percent"]), reverse=True)
        gap_movers = [
            MarketMoverItem(
                **dict(
                    m,
                    movement_type="GAP_UP" if m["gap_percent"] > 0 else "GAP_DOWN"
                )
            ) for m in gap_sorted if abs(m["gap_percent"]) >= 1.0
        ][:15]

        # Unusual Volume Movers (Ranked by raw volume / liquidity)
        vol_sorted = sorted(all_movers, key=lambda x: x["volume"] * x["price"], reverse=True)
        unusual_volume = [
            MarketMoverItem(**dict(m, movement_type="UNUSUAL_VOLUME")) for m in vol_sorted[:15]
        ]

        # Market Breadth
        adv = sum(1 for m in all_movers if m["change_percent"] > 0)
        dec = sum(1 for m in all_movers if m["change_percent"] < 0)
        unc = sum(1 for m in all_movers if m["change_percent"] == 0)
        ad_r = round(adv / (dec or 1), 2)

        breadth_summary = MarketBreadth(
            breadth_type="UNIVERSE_EQUITY_BREADTH",
            advances=adv,
            declines=dec,
            unchanged=unc,
            ad_ratio=ad_r,
            pct_above_20_ema=None,
            pct_above_50_ema=None,
            pct_above_200_ema=None,
            highs_52w_count=None,
            lows_52w_count=None
        )

        return TodaysMoversResponse(
            scan_timestamp=scan_time,
            total_market_scanned=len(all_movers),
            top_gainers=top_gainers,
            top_losers=top_losers,
            unusual_volume=unusual_volume,
            gap_movers=gap_movers,
            market_breadth_summary=breadth_summary
        )

todays_movers_engine = TodaysMoversEngine()
