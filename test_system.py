"""
Comprehensive Test Suite and Examples
Demonstrates all system components working together
"""

import sys
sys.path.insert(0, '.')

from signals import TechnicalSignals, MultiTimeframeSignals, RegimeDetector, MLSignalGenerator
from backtesting import BacktestingEngine, BacktestConfig, BacktestMetrics, PositionSizer
from data import SentimentFetcher
from integration import ComprehensiveSignalSystem
from datetime import datetime


def test_technical_signals():
    """Test basic technical signal generation"""
    print("\n" + "="*80)
    print("TEST 1: Technical Signals")
    print("="*80)

    screener = TechnicalSignals()

    # Test on a few stocks
    test_tickers = ['AAPL', 'MSFT', 'NVDA']

    for ticker in test_tickers:
        signal = screener.analyze_ticker_signals(ticker)
        if signal:
            print(f"\n{ticker}:")
            print(f"  Price: ${signal['current_price']:.2f}")
            print(f"  Confidence: {signal['confidence_score']:.1f}%")
            print(f"  Momentum Score: {signal['momentum_score']:.1f}")
            print(f"  Signal Count: {signal['signal_count']}")
            if signal['signals']:
                print(f"  Signals: {', '.join([s['name'] for s in signal['signals']])}")
        else:
            print(f"\n{ticker}: No data")


def test_market_regime():
    """Test market regime detection"""
    print("\n" + "="*80)
    print("TEST 2: Market Regime Detection")
    print("="*80)

    detector = RegimeDetector()

    # Simulated price data
    test_cases = [
        {
            'ticker': 'TRENDING_UP',
            'price': 100,
            'high': 102,
            'low': 98,
            'prev_close': 99,
            'description': 'Strong uptrend'
        },
        {
            'ticker': 'RANGING',
            'price': 100,
            'high': 100.5,
            'low': 99.5,
            'prev_close': 100,
            'description': 'Low volatility ranging'
        }
    ]

    for test in test_cases:
        regime, details = detector.detect_regime(
            test['ticker'],
            current_price=test['price'],
            daily_high=test['high'],
            daily_low=test['low'],
            previous_close=test['prev_close']
        )

        print(f"\n{test['description']}:")
        print(f"  Regime: {details['regime'].value}")
        print(f"  ATR %: {details['atr_percent']:.2f}%")
        print(f"  ADX Score: {details['adx_score']:.1f}")
        print(f"  Strategy: {details['suggested_strategy']}")
        print(f"  Signal Adjustment: {details['signal_adjustment']:.2f}x")


def test_multi_timeframe():
    """Test multi-timeframe signal analysis"""
    print("\n" + "="*80)
    print("TEST 3: Multi-Timeframe Signals")
    print("="*80)

    screener = MultiTimeframeSignals()

    test_ticker = 'AAPL'
    signal = screener.analyze_ticker_multitimeframe(test_ticker)

    if signal:
        print(f"\n{test_ticker}:")
        print(f"  Price: ${signal['current_price']:.2f}")

        combined = signal['combined']
        print(f"\n  Combined Analysis:")
        print(f"    Momentum: {combined['combined_momentum']:.1f}")
        print(f"    Confidence: {combined['combined_confidence']:.1f}%")
        print(f"    Timeframe Agreement: {combined['timeframe_agreement']:.1%}")
        print(f"    Final Score: {combined['final_score']:.1f}")
        print(f"    Recommendation: {combined['recommendation']}")

        regime = signal['regime']
        print(f"\n  Regime:")
        print(f"    Type: {regime['regime'].value}")
        print(f"    Strategy: {regime['suggested_strategy']}")
    else:
        print(f"\n{test_ticker}: No data")


def test_position_sizing():
    """Test position sizing calculations"""
    print("\n" + "="*80)
    print("TEST 4: Position Sizing")
    print("="*80)

    sizer = PositionSizer()

    # Test Kelly Criterion
    kelly_f = sizer.kelly_criterion(win_rate=0.55, avg_win=2.0, avg_loss=1.0)
    print(f"\nKelly Criterion (55% win rate, 2:1 payoff):")
    print(f"  Kelly Fraction: {kelly_f:.4f}")
    print(f"  Recommended Risk: {kelly_f*100:.2f}% of account")

    # Test optimal position sizing
    position = sizer.calculate_optimal_position(
        account_size=100000,
        risk_per_trade=0.02,
        entry_price=100,
        stop_loss=92,
        confidence=85  # 85% confidence
    )

    print(f"\nOptimal Position (85% confidence):")
    print(f"  Entry Price: ${position['entry_price']:.2f}")
    print(f"  Stop Loss: ${position['stop_loss']:.2f}")
    print(f"  Position Size: {position['position_size']:.0f} shares")
    print(f"  Position Value: ${position['position_value']:.0f}")
    print(f"  Risk Amount: ${position['risk_amount']:.0f}")
    print(f"  Risk % Account: {position['risk_pct_account']:.2f}%")


def test_backtesting_metrics():
    """Test backtesting metrics calculation"""
    print("\n" + "="*80)
    print("TEST 5: Backtesting Metrics")
    print("="*80)

    # Simulated equity curve
    equity_curve = [
        (0, 100000),
        (10, 102000),   # +2%
        (20, 101000),   # -1%
        (30, 105000),   # +4%
        (40, 103000),   # -2%
        (50, 108000),   # +5%
        (60, 106000),   # -2%
    ]

    # Simulated trades
    trades = [
        {'pnl': 1000, 'pnl_pct': 1.0, 'bars_held': 5},
        {'pnl': -500, 'pnl_pct': -0.5, 'bars_held': 3},
        {'pnl': 3000, 'pnl_pct': 3.0, 'bars_held': 10},
        {'pnl': 1000, 'pnl_pct': 1.0, 'bars_held': 5},
        {'pnl': -200, 'pnl_pct': -0.2, 'bars_held': 2},
        {'pnl': 2000, 'pnl_pct': 2.0, 'bars_held': 8},
    ]

    metrics = BacktestMetrics.calculate_all_metrics(equity_curve, trades, 100000)

    print(f"\nBacktest Results (Simulated):")
    print(f"  Total Return: {metrics.total_return:.2f}%")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"  Sortino Ratio: {metrics.sortino_ratio:.2f}")
    print(f"  Calmar Ratio: {metrics.calmar_ratio:.2f}")
    print(f"  Max Drawdown: {metrics.max_drawdown:.2f}%")
    print(f"  Win Rate: {metrics.win_rate:.1f}%")
    print(f"  Profit Factor: {metrics.profit_factor:.2f}")
    print(f"  Recovery Factor: {metrics.recovery_factor:.2f}")

    print(f"\n  Analysis:")
    print(f"    Sortino Interpretation: {BacktestMetrics.interpret_sortino(metrics.sortino_ratio)}")
    print(f"    Profit Factor Interpretation: {BacktestMetrics.interpret_profit_factor(metrics.profit_factor)}")


def test_sentiment_analysis():
    """Test sentiment analysis"""
    print("\n" + "="*80)
    print("TEST 6: Sentiment Analysis")
    print("="*80)

    fetcher = SentimentFetcher()

    test_ticker = 'APPLE'
    print(f"\nFetching sentiment for {test_ticker}...")

    sentiment = fetcher.aggregate_sentiment(test_ticker)

    if sentiment.get('status') != 'error':
        print(f"\nSentiment Results:")
        print(f"  Overall Sentiment: {sentiment.get('overall_sentiment')}")
        print(f"  Aggregate Score: {sentiment.get('aggregate_sentiment', 0):.2f}")
        if sentiment.get('newsapi_score'):
            print(f"  News API Score: {sentiment.get('newsapi_score', 0):.2f}")
            print(f"  Article Count: {sentiment.get('newsapi_articles', 0)}")
    else:
        print(f"\nNote: {sentiment.get('message', 'Sentiment fetch failed')}")
        print("  Set NEWSAPI_KEY environment variable to enable news sentiment")


def test_ml_signal_generation():
    """Test ML signal generation"""
    print("\n" + "="*80)
    print("TEST 7: ML Signal Generation")
    print("="*80)

    ml = MLSignalGenerator(lookback_days=60)

    print(f"\nML Model Status:")
    status = ml.model_status()
    for key, val in status.items():
        print(f"  {key}: {val}")

    # Test feature engineering
    sample_quote = {
        'c': 100.0,
        'h': 102.0,
        'l': 98.0,
        'pc': 99.0,
        'bidV': 1000,
        'askV': 800
    }

    features = ml.engineer_features(sample_quote)
    if features is not None:
        print(f"\nFeature Engineering:")
        print(f"  Features Shape: {features.shape}")
        print(f"  Sample Features: {features[0][:5]}")  # First 5 features
    else:
        print("  Could not engineer features (missing data)")


def test_comprehensive_integration():
    """Test complete integrated system"""
    print("\n" + "="*80)
    print("TEST 8: Comprehensive System Integration")
    print("="*80)

    config = BacktestConfig(
        initial_capital=100000,
        risk_per_trade=0.02,
        stop_loss_pct=0.08,
        take_profit_pct=0.15
    )

    system = ComprehensiveSignalSystem(config)

    # Test single signal generation
    test_ticker = 'NVDA'
    print(f"\nGenerating integrated signal for {test_ticker}...")

    signal = system.generate_integrated_signal(test_ticker, account_size=100000)

    if signal:
        print(f"\nIntegrated Signal Results:")
        print(f"  Ticker: {signal.ticker}")
        print(f"  Current Price: ${signal.entry_price:.2f}")
        print(f"  Technical Confidence: {signal.technical_confidence:.1f}%")
        print(f"  ML Direction: {signal.ml_direction}")
        print(f"  ML Confidence: {signal.ml_confidence:.1f}%")
        print(f"  Sentiment Score: {signal.sentiment_score:.2f}")
        print(f"  Weighted Score: {signal.weighted_score:.2f}")
        print(f"  Final Recommendation: {signal.final_recommendation}")
        print(f"\n  Risk Management:")
        print(f"    Entry: ${signal.entry_price:.2f}")
        print(f"    Stop Loss: ${signal.stop_loss:.2f}")
        print(f"    Take Profit: ${signal.take_profit:.2f}")
        print(f"    Position Size: {signal.position_size:.0f} shares")
    else:
        print(f"  Could not generate signal (data unavailable)")


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*100)
    print("COMPREHENSIVE TRADING SYSTEM - TEST SUITE")
    print("="*100)

    try:
        test_technical_signals()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_market_regime()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_multi_timeframe()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_position_sizing()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_backtesting_metrics()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_sentiment_analysis()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_ml_signal_generation()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        test_comprehensive_integration()
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "="*100)
    print("TEST SUITE COMPLETE")
    print("="*100)
    print("\nNext Steps:")
    print("  1. Review all test outputs above")
    print("  2. Set up API keys (.env or environment variables)")
    print("  3. Run backtests on historical data")
    print("  4. Paper trade before real capital")
    print("  5. Monitor performance in production")


if __name__ == "__main__":
    run_all_tests()
