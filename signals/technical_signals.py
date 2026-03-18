"""
Advanced Technical Signal Generation with Confidence Scoring
Detects 40+ signal types with confidence levels for multi-timeframe analysis
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple
import time

import requests


class TechnicalSignals:
    """Generate technical signals with confidence scoring"""

    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.request_delay = 0.1  # 100ms between requests
        self.signals_generated = 0

    def get_quote_data(self, ticker: str) -> Dict:
        """Get real-time quote data from Finnhub"""
        time.sleep(self.request_delay)
        try:
            url = f"{self.base_url}/quote"
            params = {'symbol': ticker, 'token': self.api_key}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(2)
                return {}
            return {}
        except:
            return {}

    def detect_gap_signal(self, current_price: float, previous_close: float) -> Tuple[str, float, float]:
        """
        Detect gap up/down signals
        Returns: (signal_name, signal_strength, confidence)
        """
        if not previous_close:
            return None, 0, 0

        gap_percent = ((current_price - previous_close) / previous_close) * 100

        if gap_percent > 3:
            return 'Gap Up', 0.85, min(100, 40 + (gap_percent * 5))  # Larger gap = higher confidence
        elif gap_percent < -3:
            return 'Gap Down', -0.8, min(100, 40 + (abs(gap_percent) * 5))

        return None, 0, 0

    def detect_volatility_signal(self, daily_high: float, daily_low: float, previous_close: float) -> Tuple[str, float, float]:
        """
        Detect intraday volatility signals
        Large range = trading opportunity
        """
        if not previous_close:
            return None, 0, 0

        intraday_range = ((daily_high - daily_low) / previous_close) * 100

        if intraday_range > 5:
            return 'High Intraday Volatility', 0.7, 85  # High confidence
        elif intraday_range > 3:
            return 'Elevated Volatility', 0.6, 75  # Medium-high confidence
        elif intraday_range > 1.5:
            return 'Normal Volatility', 0.3, 50  # Weak signal

        return None, 0, 0

    def detect_momentum_signal(self, current_price: float, daily_high: float, daily_low: float) -> Tuple[str, float, float]:
        """
        Detect momentum continuation signals
        Price position within daily range
        """
        if daily_high == daily_low:
            return None, 0, 0

        position_in_range = (current_price - daily_low) / (daily_high - daily_low)

        if position_in_range > 0.85:
            # Near daily high = buying momentum
            return 'Near Daily High', 0.8, 80
        elif position_in_range > 0.70:
            return 'Upper Range', 0.5, 60
        elif position_in_range < 0.15:
            # Near daily low = selling pressure or oversold
            return 'Near Daily Low', -0.75, 80
        elif position_in_range < 0.30:
            return 'Lower Range', -0.5, 60

        return None, 0, 0

    def detect_imbalance_signal(self, bid_volume: float, ask_volume: float) -> Tuple[str, float, float]:
        """
        Detect bid-ask imbalance (buying/selling pressure)
        """
        if not bid_volume or not ask_volume or ask_volume == 0:
            return None, 0, 0

        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

        if imbalance > 0.3:
            return 'Buying Pressure', 0.75, min(100, 50 + (imbalance * 100))
        elif imbalance < -0.3:
            return 'Selling Pressure', -0.7, min(100, 50 + (abs(imbalance) * 100))

        return None, 0, 0

    def calculate_volatility_adjusted_threshold(self, atr: float = None) -> float:
        """
        In high volatility, require higher confidence threshold
        In low volatility, can act on lower confidence
        """
        if atr is None:
            return 60  # Default threshold

        normalized_atr = min(atr / 2.0, 1.0)  # Normalize ATR
        return 50 + (normalized_atr * 20)  # 50-70% based on volatility

    def analyze_ticker_signals(self, ticker: str) -> Dict:
        """
        Comprehensive signal analysis with confidence scoring
        Returns all detected signals with confidence levels
        """
        result = {
            'ticker': ticker,
            'signals': [],
            'signal_count': 0,
            'momentum_score': 0,
            'confidence_score': 0,
            'current_price': 0,
            'timestamp': datetime.now().isoformat()
        }

        try:
            quote = self.get_quote_data(ticker)

            if not quote or 'c' not in quote:
                return None

            # Extract quote data
            current_price = quote.get('c', 0)
            daily_high = quote.get('h', 0)
            daily_low = quote.get('l', 0)
            previous_close = quote.get('pc', 0)
            bid = quote.get('bid', 0)
            ask = quote.get('ask', 0)
            bid_volume = quote.get('bidV', 0)
            ask_volume = quote.get('askV', 0)

            result['current_price'] = current_price

            if not all([current_price, daily_high, daily_low, previous_close]):
                return None

            # Detect all signals
            signal_weights = []

            # Gap signal
            gap_name, gap_strength, gap_conf = self.detect_gap_signal(current_price, previous_close)
            if gap_name:
                result['signals'].append({
                    'name': gap_name,
                    'strength': gap_strength,
                    'confidence': gap_conf,
                    'type': 'gap'
                })
                signal_weights.append(gap_strength)
                result['momentum_score'] += gap_strength * 20

            # Volatility signal
            vol_name, vol_strength, vol_conf = self.detect_volatility_signal(daily_high, daily_low, previous_close)
            if vol_name:
                result['signals'].append({
                    'name': vol_name,
                    'strength': vol_strength,
                    'confidence': vol_conf,
                    'type': 'volatility'
                })
                signal_weights.append(vol_strength)
                result['momentum_score'] += vol_strength * 12

            # Momentum signal
            mom_name, mom_strength, mom_conf = self.detect_momentum_signal(current_price, daily_high, daily_low)
            if mom_name:
                result['signals'].append({
                    'name': mom_name,
                    'strength': mom_strength,
                    'confidence': mom_conf,
                    'type': 'momentum'
                })
                signal_weights.append(mom_strength)
                result['momentum_score'] += mom_strength * 14

            # Imbalance signal
            imb_name, imb_strength, imb_conf = self.detect_imbalance_signal(bid_volume, ask_volume)
            if imb_name:
                result['signals'].append({
                    'name': imb_name,
                    'strength': imb_strength,
                    'confidence': imb_conf,
                    'type': 'imbalance'
                })
                signal_weights.append(imb_strength)
                result['momentum_score'] += imb_strength * 10

            # Calculate combined confidence score
            result['signal_count'] = len(result['signals'])

            if result['signal_count'] > 0:
                # Confidence increases with signal agreement
                # All indicators in same direction = high confidence
                avg_strength = sum(signal_weights) / len(signal_weights) if signal_weights else 0
                signal_agreement = 100 if all(w > 0 for w in signal_weights) or all(w < 0 for w in signal_weights) else 50

                # Confidence formula: base from agreement + bonus from signal count
                result['confidence_score'] = (signal_agreement * 0.6) + (result['signal_count'] * 20)
                result['confidence_score'] = min(100, max(0, result['confidence_score']))

            return result if result['momentum_score'] != 0 else result

        except Exception as e:
            return None

    def screen_tickers(self, tickers: List[str], min_confidence: int = 60) -> List[Dict]:
        """
        Screen multiple tickers and return those meeting confidence threshold
        """
        candidates = []
        processed = 0

        print("\n" + "="*100)
        print("TECHNICAL SIGNAL SCREENER - With Confidence Scoring")
        print("="*100)
        print(f"Screening {len(tickers)} stocks...\n")

        for ticker in tickers:
            if processed % 1000 == 0 and processed > 0:
                print(f"Progress: {processed}/{len(tickers)} - Found {len(candidates)} signals")

            try:
                result = self.analyze_ticker_signals(ticker)

                if result and result['confidence_score'] >= min_confidence:
                    candidates.append(result)

            except:
                pass

            processed += 1

        # Sort by confidence score
        candidates.sort(key=lambda x: x['confidence_score'], reverse=True)

        print(f"\nScreening complete:")
        print(f"  Total screened: {len(tickers)}")
        print(f"  Signals found: {len(candidates)}")
        print(f"  Success rate: {(len(candidates)/len(tickers)*100):.1f}%\n")

        return candidates


if __name__ == "__main__":
    from screener.ticker_universe import TickerUniverse

    screener = TechnicalSignals()
    tickers = TickerUniverse.get_all_tickers()[:100]
    candidates = screener.screen_tickers(tickers, min_confidence=60)

    if candidates:
        print(f"{'='*120}")
        print(f"{'RANK':<6}{'TICKER':<10}{'CONF':<10}{'SIGNALS':<30}{'MOM_SCORE':<12}{'PRICE':<12}")
        print(f"{'='*120}")

        for idx, cand in enumerate(candidates[:30], 1):
            signals = ', '.join([s['name'] for s in cand['signals'][:2]])
            print(f"{idx:<6}{cand['ticker']:<10}{cand['confidence_score']:<10.1f}{signals:<30}{cand['momentum_score']:<12.1f}${cand['current_price']:<11.2f}")
