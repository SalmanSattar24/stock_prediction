# Explosive Move Stock Screener 🚀

**Find stocks with 10%+ move potential in 3-30 days**

## What It Does

Screens 23,065 real US stocks for explosive move catalysts by combining:
- **Momentum Signals** (gap ups, volatility spikes, resistance breakouts)
- **Catalyst Detection** (earnings announcements, news spikes, events)
- **Real-Time Data** from Finnhub, NewsAPI, AlphaVantage, EODHD

## Quick Start

### 1. Set Environment Variables

```bash
set FINNHUB_API_KEY=your_finnhub_api_key_here
set NEWSAPI_KEY=your_newsapi_key_here
set ALPHAVANTAGE_KEY=your_alphavantage_key_here
set EODHD_KEY=your_eodhd_key_here
set GMAIL_APP_PASSWORD=your_16_char_gmail_password
```

### 2. Run the Screener

```bash
cd c:\All-Code\Stocks
python screener/run_explosive_screener.py
```

**Output:** `explosive_picks.txt` with top 100 candidates

## File Structure

```
screener/
├── run_explosive_screener.py    ← MAIN ENTRY POINT
├── simple_momentum_screener.py  ← Detects momentum signals
├── catalyst_detector.py         ← Finds catalysts (earnings, news)
├── ticker_universe.py           ← Loads 23,065 stocks from cache
├── database.py                  ← Stores results in SQLite
├── email_alerts.py              ← Email notifications
├── scheduler.py                 ← Automated 4-hour screening
└── __init__.py

screener_dashboard.py            ← View results in web UI
explosive_picks.txt              ← Output: Top candidates
comprehensive_tickers.txt        ← 23,065 stocks cache
screener_results.db              ← SQLite database
```

## Key Features

### Momentum Signals
- **Gap Up/Down**: Price jumped overnight (3%+ move)
- **High Intraday Volatility**: Large daily range (5%+ swings)
- **Resistance Breakouts**: Price breaking key levels
- **Bid-Ask Imbalance**: Buying/selling pressure

### Catalysts
- **Earnings Announcements**: Upcoming reports (within 30 days)
- **News Spikes**: Unusual news volume/sentiment changes
- **Economic Events**: Fed decisions, macro announcements
- **Insider Activity**: Buy/sell signals from insiders

## Performance

- **Speed**: ~15-30 minutes to screen all 23,065 stocks
- **Accuracy**: Real-time data from authoritative sources
- **Best Timeframe**: 3-30 days (short-term trades)
- **Expected Gain**: 10%+ per pick

## How to Use Results

1. Review top candidates in `explosive_picks.txt`
2. Check company news and verify chart
3. Set price alerts on your broker
4. Trade with stop losses (8% below entry)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "API Key not found" | Set environment variables (see above) |
| 0 candidates found | Adjust threshold lower (min_score=10) |
| Errors on specific stock | Stock may be delisted - safe to skip |

---

**Last Updated**: March 15, 2026  
**Stocks Covered**: 23,065 US stocks  
**Timeframe Target**: 3-30 days
