"""
Simple Fast Momentum Screener using Finnhub Real-Time Data
Screens for explosive potential using price action + volume
Optimized with rate limiting to respect API quotas
"""

import requests
import os
from datetime import datetime
from typing import Dict, List
import time

class SimpleMomentumScreener:
    """Fast momentum screener with rate limiting"""

    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.request_delay = 0.1  # 100ms between requests to stay under 60 req/min limit

    def get_quote_data(self, ticker: str) -> Dict:
        """Get real-time quote data from Finnhub with rate limiting"""
        time.sleep(self.request_delay)  # Respect rate limits

        try:
            url = f"{self.base_url}/quote"
            params = {'symbol': ticker, 'token': self.api_key}

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                time.sleep(2)  # Wait 2 seconds on rate limit
                return {}
            return {}
        except:
            return {}

    def analyze_ticker_momentum(self, ticker: str) -> Dict:
        """
        Analyze momentum signals from Finnhub quote data
        Returns momentum score and signals
        """
        result = {
            'ticker': ticker,
            'momentum_score': 0,
            'signals': [],
            'confidence': 0,
            'current_price': 0
        }

        try:
            quote = self.get_quote_data(ticker)

            if not quote or 'c' not in quote:
                return None

            # Extract data
            current_price = quote.get('c', 0)  # Current price
            daily_high = quote.get('h', 0)  # Daily high
            daily_low = quote.get('l', 0)  # Daily low
            previous_close = quote.get('pc', 0)  # Previous close
            bid = quote.get('bid', 0)
            ask = quote.get('ask', 0)
            bid_volume = quote.get('bidV', 0)
            ask_volume = quote.get('askV', 0)

            result['current_price'] = current_price

            if not all([current_price, daily_high, daily_low, previous_close]):
                return None

            # SIGNAL 1: Gap up (strong reversal signal)
            gap_percent = ((current_price - previous_close) / previous_close) * 100

            if gap_percent > 3:
                result['signals'].append(('Gap Up', 0.85))
                result['momentum_score'] += 20
            elif gap_percent < -3:
                result['signals'].append(('Gap Down', -0.8))
                result['momentum_score'] -= 15

            # SIGNAL 2: Intraday range (large swings = volatility)
            intraday_range = ((daily_high - daily_low) / previous_close) * 100

            if intraday_range > 5:
                result['signals'].append(('High Intraday Volatility', 0.7))
                result['momentum_score'] += 12
            elif intraday_range > 3:
                result['signals'].append(('Elevated Volatility', 0.6))
                result['momentum_score'] += 8

            #  SIGNAL 3: Price near daily high (momentum continuation)
            position_in_range = ((current_price - daily_low) / (daily_high - daily_low)) if (daily_high - daily_low) != 0 else 0.5

            if position_in_range > 0.85:
                result['signals'].append(('Near Daily High', 0.8))
                result['momentum_score'] += 14
            elif position_in_range < 0.15:
                result['signals'].append(('Near Daily Low', -0.75))
                result['momentum_score'] -= 12

            # SIGNAL 4: Bid-Ask imbalance (buying/selling pressure)
            if bid_volume and ask_volume and ask_volume > 0:
                imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

                if imbalance > 0.3:
                    result['signals'].append(('Buying Pressure', 0.75))
                    result['momentum_score'] += 10
                elif imbalance < -0.3:
                    result['signals'].append(('Selling Pressure', -0.7))
                    result['momentum_score'] -= 8

            # Calculate confidence (higher with more signals)
            result['confidence'] = min(100, max(20, len(result['signals']) * 20))

            # Set targets if momentum is positive
            if result['momentum_score'] > 30:
                result['targets'] = {
                    'conservative_10pct': current_price * 1.10,
                    'aggressive_15pct': current_price * 1.15,
                    'stop_loss': current_price * 0.93
                }

            return result if result['momentum_score'] > 0 else result

        except Exception as e:
            return None

    def screen_all_tickers(self, tickers: List[str], min_score: int = 20) -> List[Dict]:
        """Screen all tickers for momentum"""
        candidates = []
        processed = 0

        print("\n" + "="*80)
        print("SIMPLE MOMENTUM SCREENER - Using Finnhub Real-Time Data")
        print("="*80)
        print(f"Screening {len(tickers)} stocks...\n")

        for ticker in tickers:
            if processed % 2000 == 0 and processed > 0:
                print(f"Progress: {processed}/{len(tickers)} - Found {len(candidates)} momentum candidates")

            try:
                result = self.analyze_ticker_momentum(ticker)

                if result and result['momentum_score'] >= min_score:
                    candidates.append(result)
            except:
                pass

            processed += 1

        # Sort by momentum score
        candidates.sort(key=lambda x: x['momentum_score'], reverse=True)

        print(f"\nScreening complete:")
        print(f"  Total screened: {len(tickers)}")
        print(f"  Candidates found: {len(candidates)}")
        print(f"  Success rate: {(len(candidates)/len(tickers)*100):.1f}%\n")

        return candidates


def main():
    """Quick test"""
    from screener.ticker_universe import TickerUniverse

    screener = SimpleMomentumScreener()

    # Test on first 1000 stocks
    tickers = TickerUniverse.get_all_tickers()[:1000]
    candidates = screener.screen_all_tickers(tickers, min_score=20)

    if candidates:
        print(f"{'='*100}")
        print(f"{'RANK':<6}{'TICKER':<10}{'SCORE':<12}{'PRICE':<12}{'SIGNALS':<50}{'10%_TARGET'}")
        print(f"{'='*100}")

        for idx, cand in enumerate(candidates[:30], 1):
            signals = ', '.join([s[0] for s in cand['signals'][:2]])
            target = cand['targets']['conservative_10pct'] if cand.get('targets') else 0
            target_str = f"${target:.2f}" if target else "N/A"

            print(f"{idx:<6}{cand['ticker']:<10}{cand['momentum_score']:<12.1f}${cand['current_price']:<11.2f}{signals:<50}{target_str}")

        # Save results
        with open('momentum_candidates.txt', 'w') as f:
            f.write(f"Momentum Candidates - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for idx, cand in enumerate(candidates[:100], 1):
                f.write(f"{idx}. {cand['ticker']}\n")
                f.write(f"   Score: {cand['momentum_score']:.1f}\n")
                f.write(f"   Price: ${cand['current_price']:.2f}\n")
                if cand.get('targets'):
                    f.write(f"   10% Target: ${cand['targets']['conservative_10pct']:.2f}\n")
                f.write(f"   Signals: {', '.join([s[0] for s in cand['signals']])}\n\n")

        print(f"\n[OK] Saved top 100 to momentum_candidates.txt")


if __name__ == "__main__":
    main()
