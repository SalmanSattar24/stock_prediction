"""
Comprehensive Signal Integration System
Combines technical signals, ML predictions, sentiment analysis, and backtesting
"""

from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass

from signals import TechnicalSignals, MultiTimeframeSignals, MLSignalGenerator, RegimeDetector
from backtesting import BacktestingEngine, BacktestConfig, PositionSizer
from data import SentimentFetcher


@dataclass
class IntegratedSignal:
    """Complete signal with all components"""
    ticker: str
    timestamp: str
    technical_score: float
    technical_confidence: float
    regime: str
    ml_direction: str
    ml_confidence: float
    sentiment_score: float
    sentiment_source: str
    weighted_score: float
    final_recommendation: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float


class ComprehensiveSignalSystem:
    """
    Integrated trading signal system
    Combines all data sources and analysis
    """

    def __init__(self, config: BacktestConfig = None):
        self.technical = TechnicalSignals()
        self.multitimeframe = MultiTimeframeSignals()
        self.ml = MLSignalGenerator()
        self.regime = RegimeDetector()
        self.sentiment = SentimentFetcher()
        self.backtester = BacktestingEngine(config or BacktestConfig())
        self.sizer = PositionSizer()

        # Signal weights (how much each component contributes)
        self.weights = {
            'technical': 0.25,
            'multitimeframe': 0.25,
            'ml': 0.20,
            'sentiment': 0.15,
            'regime_adjustment': 0.15
        }

    def generate_integrated_signal(self, ticker: str, account_size: float = 100000) -> IntegratedSignal:
        """
        Generate fully integrated trading signal
        Combines technical, ML, and sentiment analysis
        """
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        try:
            # Get current quote
            quote = self.technical.get_quote_data(ticker)
            if not quote or 'c' not in quote:
                return None

            current_price = quote.get('c', 0)

            # 1. Technical Signals
            tech_signal = self.technical.analyze_ticker_signals(ticker)
            if tech_signal:
                result['components']['technical'] = {
                    'confidence': tech_signal.get('confidence_score', 0),
                    'momentum': tech_signal.get('momentum_score', 0),
                    'signal_count': tech_signal.get('signal_count', 0)
                }

            # 2. Multi-Timeframe Analysis
            mtf_signal = self.multitimeframe.analyze_ticker_multitimeframe(ticker)
            if mtf_signal:
                result['components']['multitimeframe'] = {
                    'confidence': mtf_signal.get('combined', {}).get('combined_confidence', 0),
                    'timeframe_agreement': mtf_signal.get('combined', {}).get('timeframe_agreement', 0),
                    'overall_score': mtf_signal.get('overall_score', 0)
                }

            # 3. Market Regime
            regime_type, regime_details = self.regime.detect_regime(
                ticker,
                current_price=current_price,
                daily_high=quote.get('h', 0),
                daily_low=quote.get('l', 0),
                previous_close=quote.get('pc', 0)
            )
            result['components']['regime'] = {
                'type': regime_type.value,
                'adjustment': regime_details.get('signal_adjustment', 1.0),
                'suggested_strategy': regime_details.get('suggested_strategy', 'BALANCED')
            }

            # 4. ML Prediction
            features = self.ml.engineer_features(quote)
            if features is not None and self.ml.is_trained:
                ml_pred = self.ml.predict_ensemble(features)
                result['components']['ml'] = {
                    'direction': ml_pred.get('direction', 'UNKNOWN'),
                    'confidence': ml_pred.get('confidence', 0),
                    'consensus': ml_pred.get('consensus', 0)
                }
            else:
                result['components']['ml'] = {
                    'direction': 'UNKNOWN',
                    'confidence': 0,
                    'consensus': 0
                }

            # 5. Sentiment Analysis
            sentiment = self.sentiment.aggregate_sentiment(ticker)
            result['components']['sentiment'] = {
                'score': sentiment.get('aggregate_sentiment', 0),
                'overall': sentiment.get('overall_sentiment', 'NEUTRAL'),
                'articles': sentiment.get('newsapi_articles', 0)
            }

            # 6. Calculate weighted combined score
            combined_score = self._calculate_weighted_score(result['components'])
            result['combined_score'] = combined_score

            # 7. Calculate stops and targets
            stop_loss_pct = 0.08 if regime_type.value == 'TRENDING' else 0.06
            take_profit_pct = 0.15 if regime_type.value == 'TRENDING' else 0.12

            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + take_profit_pct)

            # 8. Position sizing
            position_size = self.sizer.calculate_optimal_position(
                account_size=account_size,
                risk_per_trade=0.02,
                entry_price=current_price,
                stop_loss=stop_loss,
                confidence=min(100, combined_score * 100)
            )

            # 9. Final recommendation
            recommendation = self._generate_recommendation(combined_score, result['components'])

            return IntegratedSignal(
                ticker=ticker,
                timestamp=result['timestamp'],
                technical_score=result['components']['technical'].get('confidence', 0),
                technical_confidence=result['components']['technical'].get('confidence', 0),
                regime=result['components']['regime']['type'],
                ml_direction=result['components']['ml'].get('direction', 'UNKNOWN'),
                ml_confidence=result['components']['ml'].get('confidence', 0),
                sentiment_score=result['components']['sentiment'].get('score', 0),
                sentiment_source='NewsAPI',
                weighted_score=combined_score,
                final_recommendation=recommendation,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size.get('position_size', 0)
            )

        except Exception as e:
            print(f"Error generating signal for {ticker}: {e}")
            return None

    def _calculate_weighted_score(self, components: Dict) -> float:
        """
        Calculate weighted score from all components
        Range: 0 to 1 (0 = worst, 1 = best)
        """
        try:
            total_weight = 0
            weighted_sum = 0

            # Technical score
            tech_conf = components.get('technical', {}).get('confidence', 0) / 100
            weighted_sum += tech_conf * self.weights['technical']
            total_weight += self.weights['technical']

            # Multi-timeframe score
            mtf_conf = components.get('multitimeframe', {}).get('confidence', 0) / 100
            weighted_sum += mtf_conf * self.weights['multitimeframe']
            total_weight += self.weights['multitimeframe']

            # ML score
            ml_conf = components.get('ml', {}).get('confidence', 0) / 100
            weighted_sum += ml_conf * self.weights['ml']
            total_weight += self.weights['ml']

            # Sentiment score (normalize from -1 to 1 range to 0 to 1)
            sentiment = components.get('sentiment', {}).get('score', 0)
            sentiment_normalized = (sentiment + 1) / 2  # Convert -1..1 to 0..1
            weighted_sum += sentiment_normalized * self.weights['sentiment']
            total_weight += self.weights['sentiment']

            # Regime adjustment
            regime_adjustment = components.get('regime', {}).get('adjustment', 1.0)
            weighted_sum += (regime_adjustment / 1.1) * self.weights['regime_adjustment']  # Normalize 0.9-1.1 range
            total_weight += self.weights['regime_adjustment']

            return weighted_sum / total_weight if total_weight > 0 else 0.5

        except:
            return 0.5

    def _generate_recommendation(self, score: float, components: Dict) -> str:
        """Generate BUY/SELL/HOLD recommendation based on score and components"""
        ml_direction = components.get('ml', {}).get('direction', 'NEUTRAL')
        sentiment = components.get('sentiment', {}).get('overall', 'NEUTRAL')
        regime = components.get('regime', {}).get('type', 'UNKNOWN')

        # High score + bullish signals = STRONG BUY
        if score > 0.75 and ml_direction == 'BULLISH' and sentiment == 'POSITIVE':
            return 'STRONG_BUY'
        elif score > 0.65 and ml_direction in ['BULLISH', 'NEUTRAL']:
            return 'BUY'

        # Low score + bearish signals = STRONG SELL
        elif score < 0.25 and ml_direction == 'BEARISH' and sentiment == 'NEGATIVE':
            return 'STRONG_SELL'
        elif score < 0.35 and ml_direction in ['BEARISH', 'NEUTRAL']:
            return 'SELL'

        else:
            return 'HOLD'

    def screen_universe(self, tickers: List[str], min_score: float = 0.6) -> List[IntegratedSignal]:
        """
        Screen entire universe and return high-signal candidates
        """
        candidates = []
        processed = 0

        print("\n" + "="*100)
        print("COMPREHENSIVE SIGNAL SYSTEM - Full Universe Scan")
        print("="*100)
        print(f"Scanning {len(tickers)} stocks...\n")

        for ticker in tickers:
            if processed % 500 == 0 and processed > 0:
                print(f"Progress: {processed}/{len(tickers)} - Found {len(candidates)} strong signals")

            try:
                signal = self.generate_integrated_signal(ticker)
                if signal and signal.weighted_score >= min_score:
                    candidates.append(signal)
            except:
                pass

            processed += 1

        # Sort by score
        candidates.sort(key=lambda x: x.weighted_score, reverse=True)

        print(f"\nScan complete:")
        print(f"  Total screened: {len(tickers)}")
        print(f"  Signals found: {len(candidates)}")
        print(f"  Success rate: {(len(candidates)/len(tickers)*100):.2f}%\n")

        return candidates


if __name__ == "__main__":
    config = BacktestConfig(
        initial_capital=100000,
        risk_per_trade=0.02,
        stop_loss_pct=0.08
    )

    system = ComprehensiveSignalSystem(config)
    print("Comprehensive Signal System initialized")
    print(f"Signal weights: {system.weights}")
