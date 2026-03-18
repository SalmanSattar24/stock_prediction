# API Key Usage Mapping

This document shows exactly which API keys are used by which modules and functions.

---

## 🔑 API Keys Overview

| Key | Provider | Used By | Purpose |
|-----|----------|---------|---------|
| `FINNHUB_API_KEY` | Finnhub | Technical signals, regime detection | Real-time stock quotes |
| `NEWSAPI_KEY` | NewsAPI | Sentiment analysis | Financial news sentiment |
| `REDDIT_CLIENT_ID` | Reddit | Social sentiment | r/wallstreetbets, r/stocks analysis |
| `REDDIT_CLIENT_SECRET` | Reddit | Social sentiment | Reddit API authentication |
| `REDDIT_USER_AGENT` | Reddit | Social sentiment | Reddit API user identification |
| `ALPHAVANTAGE_KEY` | Alpha Vantage | Earnings data | Company earnings information (optional) |
| `EODHD_KEY` | EODHD | Historical data | End-of-day data (optional) |

---

## 📍 Module Usage Details

### 1. Technical Signals (`signals/technical_signals.py`)

**API Used**: `FINNHUB_API_KEY`

**Functions**:
```python
def get_quote_data(self, ticker: str) -> Dict:
    # Uses FINNHUB_API_KEY
    params = {'symbol': ticker, 'token': self.api_key}
    response = requests.get(url, params=params)
```

**Called By**:
- `analyze_ticker_signals()` - Get real-time quotes
- Any backtesting with live data

**Data Retrieved**:
- `c` - Current price
- `h` - Daily high
- `l` - Daily low
- `pc` - Previous close
- `bid` / `ask` - Current bid/ask
- `bidV` / `askV` - Bid/ask volume

---

### 2. Market Regime Detection (`signals/regime_detection.py`)

**API Used**: `FINNHUB_API_KEY`

**Functions**:
```python
def get_quote_data(self, ticker: str) -> Dict:
    # Uses FINNHUB_API_KEY (same as technical signals)
```

**Purpose**: Get current price data for ATR and ADX calculations

---

### 3. Multi-Timeframe Signals (`signals/multi_timeframe_signals.py`)

**APIs Used**:
- `FINNHUB_API_KEY` (in `TechnicalSignals`, `RegimeDetector`)

**Internal Classes**:
- Uses `TechnicalSignals()` - needs Finnhub
- Uses `RegimeDetector()` - needs Finnhub

---

### 4. Sentiment Fetcher (`data/sentiment_fetcher.py`)

**APIs Used**:
- `NEWSAPI_KEY` (required)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` (optional)

**NewsAPI Usage**:
```python
class SentimentFetcher:
    def get_newsapi_sentiment(self, ticker: str, days: int = 7) -> Dict:
        params = {
            'q': ticker,
            'sortBy': 'publishedAt',
            'language': 'en',
            'from': date,
            'apiKey': self.newsapi_key  # ← NEWSAPI_KEY
        }
        url = f"{self.newsapi_url}/everything"
        response = requests.get(url, params=params, timeout=10)
```

**Reddit Usage**:
```python
class RedditSentimentOptional:
    def _initialize_reddit(self):
        self.reddit = self.praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'StockScreener/1.0')
        )
```

**Called By**:
- `ComprehensiveSignalSystem.generate_integrated_signal()`

---

### 5. Integration System (`integration.py`)

**APIs Used**: ALL (indirectly through component modules)

**Structure**:
```python
class ComprehensiveSignalSystem:
    def __init__(self, config: BacktestConfig = None):
        self.technical = TechnicalSignals()          # Uses FINNHUB
        self.multitimeframe = MultiTimeframeSignals()  # Uses FINNHUB
        self.ml = MLSignalGenerator()                # No API
        self.regime = RegimeDetector()               # Uses FINNHUB
        self.sentiment = SentimentFetcher()          # Uses NEWSAPI, REDDIT
        self.backtester = BacktestingEngine()        # No API
        self.sizer = PositionSizer()                 # No API
```

**Main Flow**:
```python
def generate_integrated_signal(self, ticker: str, account_size: float = 100000):
    quote = self.technical.get_quote_data(ticker)
    # → Requires FINNHUB_API_KEY

    tech_signal = self.technical.analyze_ticker_signals(ticker)
    # → Requires FINNHUB_API_KEY

    mtf_signal = self.multitimeframe.analyze_ticker_multitimeframe(ticker)
    # → Requires FINNHUB_API_KEY

    sentiment = self.sentiment.aggregate_sentiment(ticker)
    # → Requires NEWSAPI_KEY (REDDIT optional)
```

---

## 🔄 API Call Flow

```
generate_integrated_signal('AAPL')
├── get_quote_data('AAPL')
│   └── FINNHUB_API_KEY → Real-time price
├── analyze_ticker_signals('AAPL')
│   └── FINNHUB_API_KEY → Technical signals
├── multitime_frame_analysis('AAPL')
│   ├── FINNHUB_API_KEY → Daily signals
│   └── FINNHUB_API_KEY → Weekly signals
├── detect_regime('AAPL')
│   └── FINNHUB_API_KEY → ATR/ADX calculation
└── aggregate_sentiment('AAPL')
    ├── NEWSAPI_KEY → News sentiment
    └── REDDIT (optional) → Social sentiment
```

---

## 📊 API Call Frequency

### Finnhub (Real-time Quotes)
- **Rate Limit**: 60 calls/minute (free tier)
- **Calls per Ticker**: 2-4 calls (quote + technical + regime)
- **Formula**: N_tickers × 4 = N_calls per screening

**Example**: 500 tickers = ~2,000 calls = ~33 seconds at 60/min

### NewsAPI (News Sentiment)
- **Rate Limit**: 100 calls/day (free tier)
- **Calls per Ticker**: 1 call
- **Use**: Only when updating sentiment (not real-time trading)

### Reddit (Social Sentiment)
- **Rate Limit**: Unlimited with proper rate limiting
- **Calls per Ticker**: 4 (one per subreddit: WSB, investing, stocks, crypto)
- **Use**: Optional, for social sentiment signals

---

## ⚙️ How to Load API Keys

### Automatic (Recommended)

The system automatically loads from `.env`:

```python
# config.py does this automatically
from dotenv import load_dotenv
load_dotenv()

# Then access anywhere
import os
api_key = os.getenv('FINNHUB_API_KEY')
```

### Manual (If Needed)

```python
import os
from config import get_api_key

finnhub_key = get_api_key('FINNHUB_API_KEY')
newsapi_key = get_api_key('NEWSAPI_KEY')
```

### Check What's Loaded

```bash
python config.py --show
```

---

## 🧪 Testing API Keys

### Test Finnhub

```python
from signals import TechnicalSignals

tech = TechnicalSignals()
quote = tech.get_quote_data('AAPL')
print(f"Current price: ${quote.get('c')}")  # Should show price
```

### Test NewsAPI

```python
from data import SentimentFetcher

fetcher = SentimentFetcher()
sentiment = fetcher.get_newsapi_sentiment('AAPL')
print(f"Sentiment: {sentiment.get('avg_sentiment')}")
```

### Test Reddit

```python
from data import RedditSentimentOptional

reddit = RedditSentimentOptional()
result = reddit.get_subreddit_sentiment('NVDA')
print(f"Reddit mentions: {result.get('mentions')}")
```

---

## 🚨 API Failures & Recovery

### If Finnhub Fails

```python
# Technical analysis returns None
quote = tech.get_quote_data('AAPL')
if quote is None:
    print("Finnhub API unavailable")
    # System gracefully degrades
```

**Impact**:
- ❌ No technical signals
- ❌ No regime detection
- ✓ Sentiment still works (if NewsAPI available)

### If NewsAPI Fails

```python
# Sentiment returns error status
sentiment = fetcher.aggregate_sentiment('AAPL')
if sentiment.get('status') == 'error':
    print(f"News sentiment unavailable: {sentiment.get('message')}")
```

**Impact**:
- ✓ Technical signals still work
- ❌ News sentiment unavailable
- ✓ ML signals still work

### If Reddit Fails

```python
# Reddit is optional, system continues
reddit_result = reddit.get_subreddit_sentiment('NVDA')
if reddit_result.get('status') == 'error':
    print("Reddit API unavailable (optional)")
```

**Impact**:
- ✓ All other signals work
- ❌ Social sentiment unavailable
- ✓ System still functional

---

## 📊 Recommended API Key Strategy

### Development / Testing
```
FINNHUB_API_KEY=your_dev_key
NEWSAPI_KEY=your_dev_key
# Others optional
```

### Production / Live Trading
```
FINNHUB_API_KEY=your_prod_key (with higher rate limit)
NEWSAPI_KEY=your_prod_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
# Rotate keys regularly
```

### Paper Trading
```
Same as development, but test with larger universes
```

---

## ⚡ API Performance Optimization

### 1. Request Caching
```python
# Finnhub data doesn't change every second
# Cache for 5 seconds to avoid duplicate calls
```

### 2. Batch Screening
```python
# Screen 500 stocks = 2000 Finnhub calls
# Takes ~33 seconds (60 calls/min)
# Plan accordingly!
```

### 3. Rate Limiting
```python
# Built-in request_delay = 0.1 seconds
# Prevents rate limit errors
```

### 4. Async Requests (Optional)
```python
# For production: use aiohttp for parallel requests
# Would reduce 500-ticker screening to ~5 seconds
```

---

## ✅ Configuration Checklist

Before running production:

- [ ] FINNHUB_API_KEY is valid and loaded
- [ ] NEWSAPI_KEY is valid and loaded
- [ ] .env file is in .gitignore
- [ ] Test script runs without errors
- [ ] Integration test passes
- [ ] API call limits verified
- [ ] Error handling tested
- [ ] Rate limiting verified

---

## 📞 API Status Pages

Monitor these if you have issues:

- Finnhub: https://finnhub.io/
- NewsAPI: https://newsapi.org/
- Reddit: https://www.reddit.com/status/

---

This document is the definitive guide to how API keys are used in the system. Refer to the module docstrings for more technical details.
