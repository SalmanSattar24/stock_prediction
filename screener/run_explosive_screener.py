"""
FINAL: Explosive Move Finder
Combines momentum + catalysts to find 10%+ opportunities in 3-30 days
Uses all APIs: Finnhub, NewsAPI, AlphaVantage, EODHD
"""

import sys
sys.path.insert(0, '.')

from screener.ticker_universe import TickerUniverse
from screener.simple_momentum_screener import SimpleMomentumScreener
from screener.catalyst_detector import EnhancedCatalystDetector
from datetime import datetime
from typing import List, Dict
import time

class FinalExplosiveMoveScreener:
    """Combined screener: Momentum + Catalysts"""

    def __init__(self):
        self.momentum = SimpleMomentumScreener()
        self.catalysts = EnhancedCatalystDetector()

    def run_explosive_scan(self, tickers: List[str] = None, sample_size: int = 2000):
        """
        Run full scan on universe
        Phase 1: Fast momentum screen (all tickers)
        Phase 2: Catalyst detection (top candidates)
        Phase 3: Combine and rank
        """
        if tickers is None:
            tickers = TickerUniverse.get_all_tickers()

        print("\n" + "="*100)
        print("EXPLOSIVE 10%+ MOVE FINDER")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)

        # PHASE 1: Momentum screening (FAST - all stocks)
        print(f"\nPHASE 1: Momentum screening {len(tickers)} stocks...")
        print("(Looking for gap ups, intraday volatility, near-term breakouts)")

        start_time = time.time()
        momentum_candidates = self.momentum.screen_all_tickers(tickers, min_score=25)
        phase1_time = time.time() - start_time

        print(f"\nPhase 1 Complete: {len(momentum_candidates)} momentum signals found in {phase1_time:.0f}s")

        # PHASE 2: Catalyst detection (on top momentum candidates)
        print(f"\nPHASE 2: Catalyst scanning...")
        print("(Checking for earnings, news, events)")

        # Limit catalyst scan to top 500 momentum candidates (saves API calls)
        top_momentum = momentum_candidates[:min(500, len(momentum_candidates))]
        top_tickers = [c['ticker'] for c in top_momentum]

        start_time = time.time()
        catalyst_candidates = self.catalysts.screen_for_catalysts_fast(top_tickers)
        phase2_time = time.time() - start_time

        print(f"\nPhase 2 Complete: {len(catalyst_candidates)} catalysts found in {phase2_time:.0f}s")

        # PHASE 3: Combine results
        print(f"\nPHASE 3: Combining momentum + catalysts...")

        combined = self._combine_results(momentum_candidates, catalyst_candidates)

        print(f"\n" + "="*100)
        print("SCREENING COMPLETE")
        print("="*100)
        print(f"Total tickers screened: {len(tickers)}")
        print(f"Momentum signals: {len(momentum_candidates)}")
        print(f"With catalysts: {len(catalyst_candidates)}")
        print(f"Combined high-confidence picks: {len(combined)}")
        print(f"Total time: {phase1_time + phase2_time:.0f}s")

        return {
            'momentum_candidates': momentum_candidates,
            'catalyst_candidates': catalyst_candidates,
            'combined': combined,
            'timestamp': datetime.now().isoformat()
        }

    def _combine_results(self, momentum_list: List[Dict], catalyst_list: List[Dict]) -> List[Dict]:
        """Combine momentum and catalyst scores"""
        combined = {}

        # Start with all momentum candidates
        for m in momentum_list:
            ticker = m['ticker']
            combined[ticker] = {
                'ticker': ticker,
                'momentum_score': m['momentum_score'],
                'signals': m['signals'][:3],  # Top 3 signals
                'current_price': m['current_price'],
                'targets': m.get('targets', {}),
                'catalyst_score': 0,
                'catalysts': [],
                'final_score': m['momentum_score'],
                'strategy': 'MOMENTUM PLAY'
            }

        # Boost with catalysts
        for c in catalyst_list:
            ticker = c['ticker']
            if ticker in combined:
                combined[ticker]['catalyst_score'] = c['catalyst_score']
                combined[ticker]['catalysts'] = c['catalysts'][:2]
                # Boost score significantly if both momentum AND catalyst
                combined[ticker]['final_score'] = (
                    combined[ticker]['momentum_score'] * 0.5 +
                    c['catalyst_score'] * 0.5
                )
                combined[ticker]['strategy'] = 'MOMENTUM + CATALYST'

        # Sort by final score
        result_list = list(combined.values())
        result_list.sort(key=lambda x: x['final_score'], reverse=True)

        return result_list

    def display_results(self, results: Dict):
        """Display top picks"""
        combined = results['combined']

        if not combined:
            print("\nNo candidates found")
            return

        print(f"\n" + "="*140)
        print(f"TOP 50 EXPLOSIVE MOVE CANDIDATES")
        print(f"Target: 10%+ gain in 3-30 days")
        print(f"="*140)

        print(f"\n{'#':<5}{'TICKER':<10}{'PRICE':<12}{'MOMENTUM':<12}{'CATALYST':<12}{'FINAL_SCORE':<15}{'STRATEGY':<25}{'10%_TARGET':<12}")
        print(f"{'-'*140}")

        for idx, pick in enumerate(combined[:50], 1):
            price = pick['current_price']
            mom_score = pick['momentum_score']
            cat_score = pick['catalyst_score']
            final = pick['final_score']
            strategy = pick['strategy'][:24]

            target = pick['targets'].get('conservative_10pct', price * 1.10)
            target_str = f"${target:.2f}"

            print(f"{idx:<5}{pick['ticker']:<10}${price:<11.2f}{mom_score:<12.1f}{cat_score:<12.1f}"
                  f"{final:<15.1f}{strategy:<25}{target_str:<12}")

        # Save to file
        print(f"\n" + "="*140)
        print("Saving detailed results to explosive_picks.txt...")

        with open('explosive_picks.txt', 'w') as f:
            f.write(f"EXPLOSIVE 10%+ MOVE PICKS\n")
            f.write(f"Screening Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Target Timeframe: 3-30 days\n")
            f.write("="*140 + "\n\n")

            for idx, pick in enumerate(combined[:100], 1):
                f.write(f"{idx}. {pick['ticker']}\n")
                f.write(f"   Current Price: ${pick['current_price']:.2f}\n")
                f.write(f"   Momentum Score: {pick['momentum_score']:.1f}\n")
                f.write(f"   Catalyst Score: {pick['catalyst_score']:.1f}\n")
                f.write(f"   Final Score: {pick['final_score']:.1f}\n")
                f.write(f"   Strategy: {pick['strategy']}\n")

                if pick['targets']:
                    f.write(f"   10% Target: ${pick['targets'].get('conservative_10pct', 'N/A')}\n")

                if pick['signals']:
                    f.write(f"   Momentum Signals:\n")
                    for signal, strength in pick['signals']:
                        f.write(f"     • {signal} ({strength:.2f})\n")

                if pick['catalysts']:
                    f.write(f"   Catalysts:\n")
                    for cat in pick['catalysts']:
                        cat_type = cat.get('catalyst_type', 'Unknown')
                        days = cat.get('days_until', 'N/A')
                        f.write(f"     • {cat_type}: {days} days\n")

                f.write("\n")

        print("[OK] Saved top 100 picks to explosive_picks.txt")


if __name__ == "__main__":
    screener = FinalExplosiveMoveScreener()

    # Get tickers
    tickers = TickerUniverse.get_all_tickers()
    print(f"\nLoaded {len(tickers)} stocks")

    # Run full scan
    results = screener.run_explosive_scan(tickers)

    # Display results
    screener.display_results(results)

    print("\n[SUCCESS] Screening complete!")
