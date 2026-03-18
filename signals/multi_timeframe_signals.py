"""
Multi-Timeframe Signal Analysis
Combines daily and weekly signals for stronger confirmation
Weekly signals CONFIRM daily signals for higher probability trades
"""

from typing import Dict, List, Tuple
from signals.technical_signals import TechnicalSignals
from signals.regime_detection import RegimeDetector, MarketRegime
import os
import requests
import time


class MultiTimeframeSignals:
    """
    Multi-timeframe signal generation
    Daily: Entry signals (fast)
    Weekly: Confirmation signals (strong)
    """

    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.request_delay = 0.1
        self.technical = TechnicalSignals()
        self.regime = RegimeDetector()

    def get_quote_data(self, ticker: str) -> Dict:
        """Get real-time quote data"""
        time.sleep(self.request_delay)
        try:
            url = f"{self.base_url}/quote"
            params = {'symbol': ticker, 'token': self.api_key}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    def analyze_daily_signals(self, ticker: str) -> Dict:
        """
        Analyze intraday/daily signals (faster, more opportunities)
        Used for entry point timing
        """
        result = self.technical.analyze_ticker_signals(ticker)
        if result:
            result['timeframe'] = 'DAILY'
            result['signal_weight'] = 0.6  # Daily has lower weight
        return result

    def analyze_weekly_signals(self, ticker: str) -> Dict:
        """
        Analyze weekly signals (slower, more reliable)
        Used for confirmation
        Note: Real implementation would fetch weekly OHLC data
        For now, we estimate from daily moves over 5 days
        """
        quote = self.get_quote_data(ticker)

        if not quote or 'c' not in quote:
            return None

        result = {
            'ticker': ticker,
            'timeframe': 'WEEKLY',
            'signals': [],
            'signal_count': 0,
            'momentum_score': 0,
            'confidence_score': 0,
            'current_price': quote.get('c', 0),
            'signal_weight': 0.9  # Weekly has higher weight
        }

        # For real implementation with historical data:
        # - Would fetch week's open/high/low/close
        # - Apply same technical analysis
        # - But on longer timeframe = less noise

        # Simplified: Estimate weekly strength from daily range
        daily_high = quote.get('h', 0)
        daily_low = quote.get('l', 0)
        current = quote.get('c', 0)

        if daily_high and daily_low:
            range_size = (daily_high - daily_low) / current
            if range_size > 0.03:  # More than 3% range
                result['signals'].append({
                    'name': 'Weekly Volatility Building',
                    'strength': 0.7,
                    'confidence': 70,
                    'type': 'volatility'
                })
                result['momentum_score'] += 15
                result['confidence_score'] += 20

        return result

    def combine_timeframes(self, daily: Dict, weekly: Dict, regime_details: Dict) -> Dict:
        """
        Combine daily and weekly signals with regime adjustment
        Returns combined score with confidence based on agreement
        """
        if not daily or not weekly:
            return None

        combined = {
            'ticker': daily['ticker'],
            'daily_signals': daily.get('signals', []),
            'weekly_signals': weekly.get('signals', []),
            'daily_momentum': daily.get('momentum_score', 0),
            'weekly_momentum': weekly.get('momentum_score', 0),
            'combined_momentum': 0,
            'daily_confidence': daily.get('confidence_score', 0),
            'weekly_confidence': weekly.get('confidence_score', 0),
            'timeframe_agreement': 0,  # How much daily/weekly agree
            'combined_confidence': 0,
            'regime': regime_details.get('regime', MarketRegime.UNKNOWN),
            'regime_adjusted_score': 0,
            'final_score': 0,
            'signal_quality': 'LOW',
            'recommendation': 'HOLD'
        }

        try:
            # Calculate timeframe agreement (both pointing same direction)
            daily_bullish = combined['daily_momentum'] > 0
            weekly_bullish = combined['weekly_momentum'] > 0

            if daily_bullish == weekly_bullish:
                combined['timeframe_agreement'] = 1.0  # Perfect agreement = 100%
                combined['signal_quality'] = 'HIGH'
            else:
                combined['timeframe_agreement'] = 0.5  # Disagreement = conflicting

            # Combine momentum scores
            # Daily: 40% weight, Weekly: 60% weight (weekly more important)
            combined['combined_momentum'] = (
                (daily['momentum_score'] * 0.4) +
                (weekly['momentum_score'] * 0.6)
            )

            # Combine confidence scores
            combined['combined_confidence'] = (
                (daily['confidence_score'] * 0.4) +
                (weekly['confidence_score'] * 0.6)
            )

            # Apply regime adjustment
            regime = regime_details.get('regime', MarketRegime.UNKNOWN)
            regime_adjustment = regime_details.get('signal_adjustment', 1.0)

            if regime == MarketRegime.TRENDING and combined['combined_momentum'] > 0:
                # Trending regime + bullish signals = strong setup
                combined['regime_adjusted_score'] = combined['combined_momentum'] * 1.2
            elif regime == MarketRegime.RANGING and combined['combined_momentum'] == 0:
                # Ranging regime with mean reversion signals
                combined['regime_adjusted_score'] = combined['combined_momentum'] * 0.8
            else:
                combined['regime_adjusted_score'] = combined['combined_momentum']

            # Final score incorporates both confidence and agreement
            combined['final_score'] = (
                combined['combined_momentum'] * 0.5 +
                combined['combined_confidence'] * 0.3 +
                (combined['timeframe_agreement'] * 100 * 0.2)
            )

            # Determine recommendation
            if combined['final_score'] > 70 and combined['timeframe_agreement'] > 0.8:
                combined['recommendation'] = 'STRONG_BUY'
            elif combined['final_score'] > 60 and combined['timeframe_agreement'] > 0.6:
                combined['recommendation'] = 'BUY'
            elif combined['final_score'] < -70 and combined['timeframe_agreement'] > 0.8:
                combined['recommendation'] = 'STRONG_SELL'
            elif combined['final_score'] < -60 and combined['timeframe_agreement'] > 0.6:
                combined['recommendation'] = 'SELL'
            else:
                combined['recommendation'] = 'HOLD'

            if combined['final_score'] > 40:
                combined['signal_quality'] = 'HIGH'
            elif combined['final_score'] > 20:
                combined['signal_quality'] = 'MEDIUM'
            elif combined['final_score'] > 0:
                combined['signal_quality'] = 'LOW'

            return combined

        except Exception as e:
            return None

    def analyze_ticker_multitimeframe(self, ticker: str) -> Dict:
        """
        Complete multi-timeframe analysis for a single ticker
        Returns daily + weekly + combined + regime analysis
        """
        try:
            # Get market regime first
            quote = self.get_quote_data(ticker)
            if not quote or 'c' not in quote:
                return None

            regime_type, regime_details = self.regime.detect_regime(
                ticker,
                current_price=quote.get('c', 0),
                daily_high=quote.get('h', 0),
                daily_low=quote.get('l', 0),
                previous_close=quote.get('pc', 0)
            )

            # Analyze daily signals
            daily = self.analyze_daily_signals(ticker)
            if not daily:
                return None

            # Analyze weekly signals
            weekly = self.analyze_weekly_signals(ticker)
            if not weekly:
                return None

            # Combine everything
            combined = self.combine_timeframes(daily, weekly, regime_details)

            return {
                'ticker': ticker,
                'daily': daily,
                'weekly': weekly,
                'combined': combined,
                'regime': regime_details,
                'current_price': quote.get('c', 0),
                'overall_score': combined['final_score'] if combined else 0
            }

        except Exception as e:
            return None

    def screen_multitimeframe(self, tickers: List[str], min_score: int = 50) -> List[Dict]:
        """
        Screen multiple tickers with multi-timeframe analysis
        Only return stocks meeting minimum combined score
        """
        candidates = []
        processed = 0

        print("\n" + "="*100)
        print("MULTI-TIMEFRAME SIGNAL SCREENER - Daily + Weekly Confirmation")
        print("="*100)
        print(f"Screening {len(tickers)} stocks with multi-timeframe analysis...\n")

        for ticker in tickers:
            if processed % 500 == 0 and processed > 0:
                print(f"Progress: {processed}/{len(tickers)} - Found {len(candidates)} confirmed signals")

            try:
                result = self.analyze_ticker_multitimeframe(ticker)

                if result and result['overall_score'] >= min_score:
                    candidates.append(result)

            except:
                pass

            processed += 1

        # Sort by overall score
        candidates.sort(key=lambda x: x['overall_score'], reverse=True)

        print(f"\nMulti-timeframe screening complete:")
        print(f"  Total screened: {len(tickers)}")
        print(f"  Confirmed signals: {len(candidates)}")
        print(f"  Success rate: {(len(candidates)/len(tickers)*100):.2f}%\n")

        return candidates


if __name__ == "__main__":
    from screener.ticker_universe import TickerUniverse

    screener = MultiTimeframeSignals()
    tickers = TickerUniverse.get_all_tickers()[:50]
    candidates = screener.screen_multitimeframe(tickers, min_score=40)

    if candidates:
        print(f"{'='*130}")
        print(f"{'RANK':<5}{'TICKER':<10}{'PRICE':<12}{'DAILY':<10}{'WEEKLY':<10}{'COMBINED':<12}{'AGREEMENT':<12}{'REGIME':<15}{'RECOMMEND':<15}")
        print(f"{'='*130}")

        for idx, cand in enumerate(candidates[:25], 1):
            combined = cand['combined']
            regime = cand['regime']
            print(f"{idx:<5}{cand['ticker']:<10}${cand['current_price']:<11.2f}"
                  f"{cand['daily']['confidence_score']:<10.1f}{cand['weekly']['confidence_score']:<10.1f}"
                  f"{combined['combined_confidence']:<12.1f}{combined['timeframe_agreement']:<12.1%}"
                  f"{regime['regime'].value:<15}{combined['recommendation']:<15}")
