# High-Quality Trading Signal System
## Comprehensive Stock, Crypto & Forex Analysis

### System Overview

This is a production-grade quantitative trading signal system that combines:
- **Multi-Timeframe Technical Analysis** - Daily + Weekly signal confirmation
- **Machine Learning Predictions** - XGBoost + Random Forest ensemble voting
- **Market Regime Detection** - Adapt strategy to trending vs ranging markets
- **Sentiment Analysis** - News and social media sentiment scoring
- **Advanced Backtesting** - Realistic position sizing, stops, and metrics
- **Professional Risk Management** - Kelly Criterion, volatility-adjusted sizing

---

## Project Structure

```
stocks/
├── signals/                          # Signal Generation
│   ├── technical_signals.py         # Core technical indicators
│   ├── multi_timeframe_signals.py   # Daily + Weekly confirmation
│   ├── regime_detection.py          # Trending vs Ranging detection
│   ├── ml_signals.py                # XGBoost + RF ensemble
│   └── __init__.py
│
├── backtesting/                     # Backtesting Framework
│   ├── engine.py                    # Core backtesting logic
│   ├── metrics.py                   # Sortino, Calmar, Profit Factor
│   ├── position_sizing.py           # Kelly, ATR-based, volatility sizing
│   └── __init__.py
│
├── data/                            # Data Fetchers
│   ├── sentiment_fetcher.py         # News + Reddit sentiment
│   └── __init__.py
│
├── screener/                        # Legacy screener (existing)
│   ├── simple_momentum_screener.py
│   ├── catalyst_detector.py
│   └── ...
│
├── integration.py                   # Complete system integration
├── requirements.txt                 # Dependencies
└── README.md

```

---

## Key Components

### 1. **Technical Signals** (`signals/technical_signals.py`)
Generates 40+ technical signals with confidence scoring:
- Gap Up/Down detection
- Intraday volatility analysis
- Momentum signals (price position in daily range)
- Bid-Ask imbalance detection
- Confidence scoring based on indicator agreement

**Features:**
- Signal agreement scoring (higher when multiple indicators agree)
- Volatility-adjusted thresholds
- Real-time quote data from Finnhub

### 2. **Multi-Timeframe Analysis** (`signals/multi_timeframe_signals.py`)
Combines daily and weekly signals for confirmation:
- Daily signals for entry timing
- Weekly signals for confirmation (stronger reliability)
- Timeframe agreement scoring
- Regime-adjusted signal weighting

**Why it works:**
- Weekly signals filter out noise from daily moves
- Prevents false signals during choppy consolidations
- Medium-term trades (1-4 weeks) benefit most

### 3. **Market Regime Detection** (`signals/regime_detection.py`)
Identifies whether market is trending or ranging:
- **TRENDING Mode**: Use momentum strategies, relax stops
- **RANGING Mode**: Use mean reversion, tighter stops
- Based on ADX-like scoring and volatility levels

**Benefits:**
- Adapts strategy to market conditions
- Improves stop loss placement
- Adjusts signal confidence thresholds

### 4. **ML Signal Generator** (`signals/ml_signals.py`)
Ensemble voting with XGBoost + Random Forest:
- Automatic feature engineering from price action
- Walk-forward validation to prevent overfitting
- Probability-based predictions
- Model status tracking

**Features:**
- 10 engineered features (gaps, ranges, volatility, trends)
- RF + XGBoost consensus voting
- Adjustable confidence levels

### 5. **Backtesting Engine** (`backtesting/engine.py`)
Realistic backtesting with proper risk management:
- Stop loss and take profit implementation
- Position sizing based on risk
- Commission and slippage modeling
- No look-ahead bias (next-bar execution)
- Trailing stops support

### 6. **Advanced Metrics** (`backtesting/metrics.py`)
Professional trading metrics:
- **Sortino Ratio**: Risk-adj return (downside volatility only)
- **Calmar Ratio**: Return per unit of max drawdown
- **Profit Factor**: Gross Profits / Gross Losses
- **Win Rate**: % of profitable trades
- **Recovery Factor**: Profit recovery from drawdowns
- **Trade Efficiency**: Profit per bar held

### 7. **Position Sizing** (`backtesting/position_sizing.py`)
Smart position size calculation:
- **Kelly Criterion**: Optimal sizing based on win rate
- **ATR-Based**: Adjusted by volatility
- **Confidence-Weighted**: Larger positions for higher confidence signals
- **Max Position Caps**: Prevent overexposure

### 8. **Sentiment Analysis** (`data/sentiment_fetcher.py`)
Multi-source sentiment aggregation:
- **NewsAPI**: Financial news sentiment
- **Reddit**: Social media sentiment (optional setup)
- Keyword-based sentiment scoring
- Aggregated sentiment weighting

---

## Usage Examples

### Basic Signal Generation

```python
from signals import TechnicalSignals, MultiTimeframeSignals

# Single-timeframe analysis
tech = TechnicalSignals()
signal = tech.analyze_ticker_signals('AAPL')

# Multi-timeframe analysis (more reliable)
mtf = MultiTimeframeSignals()
signals = mtf.analyze_ticker_multitimeframe('AAPL')
```

### Backtesting a Strategy

```python
from backtesting import BacktestingEngine, BacktestConfig
from backtesting import BacktestMetrics

config = BacktestConfig(
    initial_capital=100000,
    risk_per_trade=0.02,  # 2% risk per trade
    stop_loss_pct=0.08,   # 8% stop loss
    take_profit_pct=0.15  # 15% take profit
)

engine = BacktestingEngine(config)
report = engine.backtest(price_bars, signals_by_bar)

# View results
metrics = BacktestMetrics.calculate_all_metrics(
    engine.equity_curve,
    engine.closed_trades
)
print(f"Sortino: {metrics.sortino_ratio:.2f}")
print(f"Win Rate: {metrics.win_rate:.1f}%")
print(f"Profit Factor: {metrics.profit_factor:.2f}")
```

### Complete Integration

```python
from integration import ComprehensiveSignalSystem
from backtesting import BacktestConfig

system = ComprehensiveSignalSystem(
    config=BacktestConfig(initial_capital=100000)
)

# Generate integrated signal for single ticker
signal = system.generate_integrated_signal('NVDA')
print(f"Recommendation: {signal.final_recommendation}")
print(f"Position Size: {signal.position_size:.0f} shares")

# Screen entire universe
from screener.ticker_universe import TickerUniverse
tickers = TickerUniverse.get_all_tickers()[:500]
candidates = system.screen_universe(tickers, min_score=0.65)
```

---

## Installation & Setup

### Requirements
```bash
pip install -r requirements.txt
```

### Environment Variables (API Keys)

```bash
# Finnhub (Real-time quotes, technical data)
export FINNHUB_API_KEY="your_key"

# NewsAPI (Financial news)
export NEWSAPI_KEY="your_key"

# Alpha Vantage (Earnings data)
export ALPHAVANTAGE_KEY="your_key"

# EODHD (Alternative earnings data)
export EODHD_KEY="your_key"

# Reddit (Optional, for social sentiment)
export REDDIT_CLIENT_ID="your_id"
export REDDIT_CLIENT_SECRET="your_secret"
export REDDIT_USER_AGENT="StockScreener/1.0"
```

### Reddit Sentiment Setup (Optional)

To enable full Reddit sentiment analysis:

```bash
# Install PRAW
pip install praw

# Create Reddit app: https://www.reddit.com/prefs/apps
# Select "script" application type
# Set environment variables above
```

---

## Signal Weights (Integration System)

The comprehensive system weights components as follows:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Technical | 25% | Real-time price action signals |
| Multi-Timeframe | 25% | Daily/weekly confirmation |
| ML (Ensemble) | 20% | Pattern recognition from historical data |
| Sentiment | 15% | News/social media momentum |
| Regime Adjustment | 15% | Market condition adaptation |

Final Score = Weighted combination (0-1 scale)

---

## Key Metrics Explained

### Sortino Ratio
- **Formula**: (Return - Risk_Free) / Downside_Volatility × √252
- **Interpretation**:
  - > 2.0 = Excellent
  - > 1.0 = Good
  - < 0 = Losing strategy
- **Why**: Only penalizes losses, better for traders than Sharpe

### Calmar Ratio
- **Formula**: Annual_Return / Max_Drawdown%
- **Interpretation**:
  - > 1.0 = Excellent
  - > 0.5 = Good
  - < 0 = Underwater
- **Why**: Directly measures return per unit of drawdown risk

### Profit Factor
- **Formula**: Gross_Profit / Gross_Loss
- **Interpretation**:
  - > 2.0 = Excellent
  - > 1.5 = Good
  - < 1.0 = Losing
- **Why**: Fundamental measure of strategy profitability

---

## Backtesting Parameters

### Stop Loss Configuration
- **Trending Market**: 5-8% (wider, let winners run)
- **Ranging Market**: 3-5% (tighter, catch breakouts)
- **Volatile Stock**: 6-10% based on ATR
- **Low Vol Stock**: 4-6% based on ATR

### Take Profit Targets
- **Trend Following**: 12-20% (let profits run)
- **Mean Reversion**: 5-10% (quick wins)
- **Medium-Term**: 8-15% (3-4 week holds)

### Position Sizing
- **Risk per Trade**: 1-2% of account
- **Max Position**: 5% of account
- **Kelly Criterion**: Optimal based on win rate (capped 25%)

---

## Signal Quality Checklist

A good signal should have:
- ✅ Confidence Score > 60%
- ✅ Multi-timeframe agreement (daily + weekly)
- ✅ Regime adaptation (trending/ranging)
- ✅ News sentiment confirmation
- ✅ Position size matched to confidence
- ✅ Historical win rate > 50%
- ✅ Profit factor > 1.5
- ✅ Sortino ratio > 1.0

---

## Performance Expectations

### Based on System Components:

| Metric | Target | Notes |
|--------|--------|-------|
| Win Rate | 52-56% | Achievable with confirmation |
| Profit Factor | 1.5-2.0+ | Excellent with proper stops |
| Sortino Ratio | 1.0-2.0+ | Risk-adjusted outperformance |
| Maximum Drawdown | -15% to -25% | Depends on position sizing |
| Recovery Factor | 2.0+ | Profits exceed drawdowns |

---

## Advanced Features

### Walk-Forward Validation (`ml_signals.py`)
Prevents ML model overfitting:
- Train on 252-day rolling window
- Test on 28-day forward period
- Roll window forward each period
- Only validate on unseen data

### Regime Adaptation (`regime_detection.py`)
Automatically switches between strategies:
```
Trending (ADX > 25):
  - Momentum weight: 70%
  - Mean reversion weight: 30%
  - Stops: Wider (8%)
  - Profit targets: Longer (15%+)

Ranging (ADX < 20):
  - Mean reversion weight: 70%
  - Momentum weight: 30%
  - Stops: Tighter (5%)
  - Profit targets: Shorter (5-8%)
```

### Multi-Timeframe Confirmation
Real edge from combining timeframes:
- Daily trade setup (faster signal)
- Weekly confirmation (stronger signal)
- Max probability at confluence

---

## Troubleshooting

### "API rate limit exceeded"
- Check spacing in `simple_momentum_screener.py` (0.1s delay)
- Catalyst detector has built-in throttling
- Use caching for repeated tickers

### "ML model not trained"
- Call `train_ensemble_models()` with historical data
- Use walk-forward validation to prevent overfitting
- Requires at least 250 training samples

### "Signals not appearing"
- Check minimum confidence threshold (default 60%)
- Verify Finnhub API key is valid
- Check price data for gaps or missing values

---

## Next Steps for Production

1. **Integrate real data**: Use live feeds instead of API samples
2. **Add order execution**: Connect to broker API
3. **Risk monitoring**: Real-time portfolio monitoring
4. **Paper trading**: Test signals before real capital
5. **Performance tracking**: Ongoing strategy analytics
6. **Feature engineering**: Expand to 50+ indicators
7. **Deep learning**: Add LSTM/transformer models

---

## License & Disclaimer

**Disclaimer**: This is educational software for learning quantitative trading. Past performance doesn't guarantee future results. Use with proper risk management and only trade capital you can afford to lose.

**Backtesting Bias**: Backtests are subject to look-ahead bias, overfitting, and data issues. Forward testing on paper accounts is essential before real trading.

---

This system is designed for:
- ✅ Short-to-medium term swing trading (3-30 days)
- ✅ Technical analysis focus with ML confirmation
- ✅ Multiple asset classes (stocks, crypto, forex)
- ✅ Quantitative approach with rule-based signals
- ✅ Risk management and position sizing

**Not designed for:**
- ❌ Long-term buy-and-hold investing
- ❌ Fundamental analysis focus
- ❌ High-frequency trading
- ❌ Single-signal strategies

