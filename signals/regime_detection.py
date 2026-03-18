"""
Market Regime Detection
Identifies whether market is in trending or ranging mode
Uses ADX, ATR, and moving average analysis
"""

from enum import Enum
from typing import Dict, Tuple
import requests
import os
import time


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING = "TRENDING"           # Strong trend, use momentum strategies
    RANGING = "RANGING"             # Choppy/range-bound, use mean reversion
    TRANSITION = "TRANSITION"       # Moving between regimes
    UNKNOWN = "UNKNOWN"             # Not enough data


class RegimeDetector:
    """Detect market regime from technical indicators"""

    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.request_delay = 0.1

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

    def calculate_atr(self, high: float, low: float, close: float, prev_close: float, lookback: int = 14) -> float:
        """
        Calculate Average True Range
        ATR > 2% of price = high volatility (trending environment)
        ATR < 1% of price = low volatility (ranging environment)
        """
        true_range = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        # Simplified ATR for single bar (in real use, use rolling average)
        atr_percent = (true_range / close * 100) if close else 0
        return atr_percent

    def calculate_adx_component(self, current_price: float, prev_price: float,
                               daily_high: float, daily_low: float, prev_high: float, prev_low: float) -> float:
        """
        Simplified ADX calculation (Average Directional Index)
        Measures trend strength
        ADX > 25 = Strong trend
        ADX 20-25 = Moderate trend
        ADX < 20 = Weak/No trend
        """
        # Directional Movement
        up_move = daily_high - prev_high if daily_high > prev_high else 0
        down_move = prev_low - daily_low if prev_low > daily_low else 0

        # True Range
        true_range = max(
            daily_high - daily_low,
            abs(daily_high - prev_price),
            abs(daily_low - prev_price)
        )

        if true_range == 0:
            return 0

        # +DM and -DM
        plus_dm = up_move if up_move > down_move else 0
        minus_dm = down_move if down_move > up_move else 0

        # +DI and -DI (simplified)
        plus_di = (plus_dm / true_range) * 100 if true_range > 0 else 0
        minus_di = (minus_dm / true_range) * 100 if true_range > 0 else 0

        # Simplified ADX (real ADX uses 14-period smoothing)
        adx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0

        return min(adx, 100)  # Cap at 100

    def detect_regime_from_price_action(self, prices: list, lookback: int = 20) -> Tuple[MarketRegime, float]:
        """
        Detect regime from price action
        Trending: Price making higher highs and higher lows (or lower highs/lows)
        Ranging: Price bouncing between support/resistance
        """
        if len(prices) < lookback:
            return MarketRegime.UNKNOWN, 0.5

        recent = prices[-lookback:]

        # Look for trend pattern
        highs = [p.get('high', 0) for p in recent if isinstance(p, dict)]
        lows = [p.get('low', 0) for p in recent if isinstance(p, dict)]

        if len(highs) < 3 or len(lows) < 3:
            return MarketRegime.UNKNOWN, 0.5

        # Check for higher highs/lows (uptrend) or lower highs/lows (downtrend)
        higher_high_count = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
        higher_low_count = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])

        uptrend_strength = (higher_high_count + higher_low_count) / (2 * (len(highs) - 1))

        if uptrend_strength > 0.65:
            return MarketRegime.TRENDING, uptrend_strength
        elif uptrend_strength < 0.35:
            return MarketRegime.TRENDING, 1 - uptrend_strength  # Downtrend
        else:
            return MarketRegime.RANGING, 0.5  # Mixed = ranging

    def detect_regime(self, ticker: str, current_price: float, daily_high: float, daily_low: float,
                     previous_close: float, prev_high: float = None, prev_low: float = None) -> Tuple[MarketRegime, Dict]:
        """
        Comprehensive regime detection
        Returns: (regime_type, regime_details)
        """
        details = {
            'ticker': ticker,
            'regime': MarketRegime.UNKNOWN,
            'regime_strength': 0,
            'atr_percent': 0,
            'adx_score': 0,
            'volatility_level': 'unknown',
            'signal_adjustment': 1.0,  # Multiplier for signal threshold
            'suggested_strategy': 'BALANCED'
        }

        try:
            if prev_high is None:
                prev_high = daily_high * 0.98
            if prev_low is None:
                prev_low = daily_low * 0.98

            # Calculate ATR (volatility)
            atr_pct = self.calculate_atr(daily_high, daily_low, current_price, previous_close)
            details['atr_percent'] = atr_pct

            # Determine volatility level
            if atr_pct > 2.0:
                details['volatility_level'] = 'HIGH'
                volatility_regime = MarketRegime.TRENDING
                volatility_confidence = 0.8
            elif atr_pct > 1.0:
                details['volatility_level'] = 'NORMAL'
                volatility_regime = MarketRegime.TRANSITION
                volatility_confidence = 0.6
            else:
                details['volatility_level'] = 'LOW'
                volatility_regime = MarketRegime.RANGING
                volatility_confidence = 0.7

            # Calculate ADX-like score
            adx_score = self.calculate_adx_component(current_price, previous_close, daily_high, daily_low, prev_high, prev_low)
            details['adx_score'] = adx_score

            # Determine regime from ADX
            if adx_score > 25:
                adx_regime = MarketRegime.TRENDING
                adx_confidence = 0.8
            elif adx_score > 20:
                adx_regime = MarketRegime.TRANSITION
                adx_confidence = 0.6
            else:
                adx_regime = MarketRegime.RANGING
                adx_confidence = 0.7

            # Combine regime signals (average confidence)
            if volatility_regime == adx_regime:
                details['regime'] = volatility_regime
                details['regime_strength'] = (volatility_confidence + adx_confidence) / 2
            elif volatility_regime == MarketRegime.TRANSITION or adx_regime == MarketRegime.TRANSITION:
                details['regime'] = MarketRegime.TRANSITION
                details['regime_strength'] = ((volatility_confidence + adx_confidence) / 2) * 0.8
            else:
                # Conflicting signals
                details['regime'] = MarketRegime.RANGING
                details['regime_strength'] = 0.5

            # Set signal adjustment based on regime
            if details['regime'] == MarketRegime.TRENDING:
                details['signal_adjustment'] = 0.9  # Relax threshold in trending
                details['suggested_strategy'] = 'TREND_FOLLOWING'
            elif details['regime'] == MarketRegime.RANGING:
                details['signal_adjustment'] = 1.1  # Tighten threshold in ranging
                details['suggested_strategy'] = 'MEAN_REVERSION'
            else:
                details['signal_adjustment'] = 1.0  # Neutral in transition
                details['suggested_strategy'] = 'BALANCED'

            return details['regime'], details

        except Exception as e:
            return MarketRegime.UNKNOWN, details

    def get_adjusted_confidence_threshold(self, regime: MarketRegime, base_threshold: float = 60) -> float:
        """
        Adjust confidence threshold based on market regime
        Trending: Can use lower threshold (more opportunities)
        Ranging: Need higher threshold (avoid false breaks)
        """
        if regime == MarketRegime.TRENDING:
            return max(50, base_threshold - 5)  # Lower threshold
        elif regime == MarketRegime.RANGING:
            return min(80, base_threshold + 10)  # Higher threshold
        else:  # TRANSITION or UNKNOWN
            return base_threshold  # Use default


if __name__ == "__main__":
    detector = RegimeDetector()

    # Test
    regime, details = detector.detect_regime(
        'SPY',
        current_price=450.0,
        daily_high=452.0,
        daily_low=448.0,
        previous_close=449.0,
        prev_high=449.5,
        prev_low=447.5
    )

    print(f"Regime: {regime}")
    print(f"Details: {details}")
