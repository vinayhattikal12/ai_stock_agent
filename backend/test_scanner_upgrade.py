import asyncio
from datetime import datetime
from backend.services.quant.scanner import staged_scanner
from backend.services.quant.market_engine import market_engine
from backend.services.quant.factor_engine import factor_engine
from backend.services.quant.setup_engine import setup_engine
from backend.services.quant.target_stop_engine import target_stop_engine
from backend.services.ml.classifier import ml_classifier

async def test_scanner():
    print("=== TESTING UPGRADED MULTI-FACTOR SCANNER PIPELINE ===")
    
    # 1. Test Market Regime & Policy
    market_status = await market_engine.evaluate_market_regime()
    print(f"Market Regime: {market_status.regime} (Policy: {market_status.regime_policy.status_label})")
    print(f"Policy: Min ML Prob={market_status.regime_policy.min_probability_threshold}, Min R:R={market_status.regime_policy.min_risk_reward_ratio}")
    
    # 2. Test Staged Scan
    scan_res = await staged_scanner.run_scan()
    print(f"\nScan Timestamp: {scan_res.scan_timestamp}")
    print(f"Total Universe Scanned: {scan_res.total_universe_scanned}")
    print(f"Pipeline Stage Survivors: {scan_res.survivors_by_stage}")
    print(f"BUY Candidates Count: {scan_res.buy_candidates_count}")
    print(f"Near Misses Count: {scan_res.near_misses_count}")
    print(f"Total Shortlisted Opportunities: {len(scan_res.opportunities)}")
    print(f"Is Abstention: {scan_res.is_abstention}")
    if scan_res.is_abstention:
        print(f"Abstention Reason: {scan_res.abstention_reason}")
        print(f"Primary Bottleneck: {scan_res.primary_bottleneck}")
        
    print("\n--- SHORTLISTED TOP OPPORTUNITIES ---")
    for idx, opp in enumerate(scan_res.opportunities, 1):
        print(f"#{idx} {opp.symbol} ({opp.sector})")
        print(f"   Signal: {opp.signal} | Opportunity Score: {opp.opportunity_score:.1f}/100")
        print(f"   Setup: {opp.setup_type} (Quality: {opp.setup_quality_score:.1f})")
        print(f"   Levels: Entry ₹{opp.levels.entry_low}-₹{opp.levels.entry_high} | T1 ₹{opp.levels.target_1} ({opp.levels.target_1_r_multiple:.2f}R) | SL ₹{opp.levels.stop_loss}")
        print(f"   ML Prob(T1 before SL in 10D): {int(opp.ml_probability.p_t1_before_sl * 100)}%")
        print(f"   RVOL: {opp.volume_metrics.rvol_20d:.2f}x | Mansfield RS: {opp.relative_strength.mansfield_rs_50d:+.1f}%")
        if opp.signal != "BUY CANDIDATE" and opp.watch_reasons:
            print(f"   Watch Reason: {opp.watch_reasons[0]}")
        print()

    print("=== SCANNER TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(test_scanner())
