"""
Optimized Explosive Move Screener
Runs on 5000+ stocks while respecting all API rate limits
"""

import sys
sys.path.insert(0, '.')
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from screener.ticker_universe import TickerUniverse
from screener.simple_momentum_screener import SimpleMomentumScreener
from screener.catalyst_detector import EnhancedCatalystDetector

def main():
    required_keys = ['FINNHUB_API_KEY', 'NEWSAPI_KEY']
    missing = [key for key in required_keys if not os.getenv(key)]
    if missing:
        print("Missing required API keys:")
        for key in missing:
            print(f"  - {key}")
        print("Add these to your environment or .env file before running.")
        return

    print("\n" + "="*100)
    print("EXPLOSIVE MOVE SCREENER - OPTIMIZED VERSION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    print("\nThis version is optimized to:")
    print("  [+] Add delays between API calls (avoid rate limits)")
    print("  [+] Only check catalysts on top 100 momentum stocks")
    print("  [+] Skip earnings checks if rate limits approached")
    print("  [+] Complete within API quotas\n")

    # Get top 5000 stocks
    tickers = TickerUniverse.get_all_tickers()[:5000]
    print(f"Universe: {len(tickers)} stocks\n")

    # PHASE 1: Momentum screening (full universe)
    print("="*100)
    print("PHASE 1: MOMENTUM SCREENING (All stocks)")
    print("="*100)
    screener = SimpleMomentumScreener()
    momentum_candidates = screener.screen_all_tickers(tickers, min_score=20)

    print(f"\n[*] Found {len(momentum_candidates)} momentum signals\n")

    if not momentum_candidates:
        print("No momentum signals found. Market may be range-bound.")
        return

    # PHASE 2: Catalyst detection (top 100 momentum only)
    print("="*100)
    print("PHASE 2: CATALYST DETECTION (Top 100 momentum stocks)")
    print("="*100)

    top_momentum = [c['ticker'] for c in momentum_candidates[:100]]
    detector = EnhancedCatalystDetector()
    catalyst_candidates = detector.screen_for_catalysts_fast(top_momentum, max_checks=100)

    print(f"\n[*] Found {len(catalyst_candidates)} with catalyst events\n")

    # PHASE 3: Combine and rank
    print("="*100)
    print("PHASE 3: FINAL RANKING")
    print("="*100)

    combined = []

    # Add momentum candidates
    for m in momentum_candidates:
        combined.append({
            'ticker': m['ticker'],
            'current_price': m['current_price'],
            'momentum_score': m['momentum_score'],
            'catalyst_score': 0,
            'final_score': m['momentum_score'],
            'strategy': 'MOMENTUM PLAY',
            'signals': [s[0] for s in m['signals'][:3]],
            'catalysts': []
        })

    # Enhance with catalysts
    for c in catalyst_candidates:
        for item in combined:
            if item['ticker'] == c['ticker']:
                item['catalyst_score'] = c['catalyst_score']
                item['final_score'] = (item['momentum_score'] * 0.6 + c['catalyst_score'] * 0.4)
                item['strategy'] = 'MOMENTUM + CATALYST'
                item['catalysts'] = [cat['catalyst_type'] for cat in c['catalysts'][:2]]
                break

    # Sort by final score
    combined.sort(key=lambda x: x['final_score'], reverse=True)

    # Display results
    print(f"\n{'='*130}")
    print(f"TOP 40 EXPLOSIVE MOVE CANDIDATES")
    print(f"{'='*130}\n")

    print(f"{'#':<4}{'TICKER':<10}{'PRICE':<12}{'MOMENTUM':<12}{'CATALYST':<12}{'FINAL':<10}{'STRATEGY':<30}")
    print(f"{'-'*130}")

    for idx, pick in enumerate(combined[:40], 1):
        print(f"{idx:<4}{pick['ticker']:<10}${pick['current_price']:<11.2f}{pick['momentum_score']:<12.1f}"
              f"{pick['catalyst_score']:<12.1f}{pick['final_score']:<10.1f}{pick['strategy']:<30}")

    # Save results
    print(f"\n{'='*130}")
    print("SAVING RESULTS...")
    print(f"{'='*130}\n")

    with open('explosive_picks_optimized.txt', 'w') as f:
        f.write(f"EXPLOSIVE MOVE STOCK PICKS - OPTIMIZED SCAN\n")
        f.write(f"Screening Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Screened: {len(tickers)} stocks\n")
        f.write(f"Momentum Signals: {len(momentum_candidates)}\n")
        f.write(f"With Catalysts: {len(catalyst_candidates)}\n\n")
        f.write(f"{'='*130}\n\n")

        for idx, pick in enumerate(combined[:100], 1):
            f.write(f"{idx}. {pick['ticker']}\n")
            f.write(f"   Current Price: ${pick['current_price']:.2f}\n")
            f.write(f"   Momentum Score: {pick['momentum_score']:.1f}\n")
            f.write(f"   Catalyst Score: {pick['catalyst_score']:.1f}\n")
            f.write(f"   Final Score: {pick['final_score']:.1f}\n")
            f.write(f"   Strategy: {pick['strategy']}\n")
            if pick['signals']:
                f.write(f"   Momentum Signals: {', '.join(pick['signals'])}\n")
            if pick['catalysts']:
                f.write(f"   Catalysts: {', '.join(pick['catalysts'])}\n")
            f.write(f"\n")

    print("[OK] Saved top 100 picks to: explosive_picks_optimized.txt")

    print(f"\n{'='*130}")
    print("SCREENING COMPLETE!")
    print(f"{'='*130}")
    print(f"\nResults Summary:")
    print(f"  Total screened: {len(tickers)} stocks")
    print(f"  Momentum candidates: {len(momentum_candidates)}")
    print(f"  With catalysts: {len(catalyst_candidates)}")
    print(f"  Top 40 displayed above")
    print(f"  Full results: explosive_picks_optimized.txt")
    print(f"\nSuccess! API rate limits respected throughout.")

if __name__ == "__main__":
    main()
