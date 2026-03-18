# Quick Start Guide - Stock Signal System

## ⚡ 5-Minute Setup

### 1️⃣ Clone/Download Project
```bash
cd c:/All-Code/Stocks
```

### 2️⃣ Run Setup Script

**On Windows:**
```bash
setup.bat
```

**On Mac/Linux:**
```bash
bash setup.sh
```

**Or manually:**
```bash
pip install -r requirements.txt
python config.py --setup
```

### 3️⃣ Add Your API Keys

Edit `.env` file and add:

```bash
FINNHUB_API_KEY=your_key_here
NEWSAPI_KEY=your_key_here
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=QuantSignalSystem/1.0 by YourUsername
```

### 4️⃣ Test Your Setup
```bash
python test_system.py
```

---

## 📌 Find Your API Keys

### Quick Links:

| Service | Sign Up | Free Tier | Get Key |
|---------|---------|-----------|---------|
| **Finnhub** | [finnhub.io](https://finnhub.io/register) | 60 calls/min | ✓ Instant after signup |
| **NewsAPI** | [newsapi.org](https://newsapi.org/) | 100/day | ✓ Instant after signup |
| **Alpha Vantage** | [alphavantage.co](https://www.alphavantage.co/) | 5/min | ✓ Instant after signup |
| **Reddit** | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | Unlimited | [See instructions below](#reddit-setup) |

---

## 🤖 Reddit Setup (Detailed)

### Step A: Go to Reddit App Page
Click: https://www.reddit.com/prefs/apps

### Step B: Create New App
- Click **"Create an app"** or **"Create another app"**
- **Name**: `QuantSignalSystem`
- **Type**: Choose **"script"** ← IMPORTANT
- **Description**: Stock signal analysis
- **Redirect URI**: `http://localhost:8080`
- Click **"Create app"**

### Step C: Copy Your Keys

You'll see two important values:

```
personal use script
─────────────────────
your_app_name

[Client ID]      ← Copy this → REDDIT_CLIENT_ID
[Client Secret]  ← Copy this → REDDIT_CLIENT_SECRET
```

### Step D: Update .env

```bash
REDDIT_CLIENT_ID=abc123def456...
REDDIT_CLIENT_SECRET=xyz789abc123...
REDDIT_USER_AGENT=QuantSignalSystem/1.0 by YourRedditUsername
```

Replace `YourRedditUsername` with your actual Reddit username!

---

## ✅ Verification

After setup, verify everything works:

```bash
# Check all keys are configured
python config.py --validate

# Run full test suite
python test_system.py

# View current config
python config.py --show
```

You should see:
```
✓ FINNHUB_API_KEY          [****...****]
✓ NEWSAPI_KEY              [****...****]
```

---

## 📚 Next Steps

### 1. **Understand the System**
```bash
cat SYSTEM_GUIDE.md
```

### 2. **Generate Your First Signal**
```python
from integration import ComprehensiveSignalSystem

system = ComprehensiveSignalSystem()
signal = system.generate_integrated_signal('AAPL')
print(signal.final_recommendation)
```

### 3. **Screen Universe**
```python
from screener.ticker_universe import TickerUniverse

tickers = TickerUniverse.get_all_tickers()[:100]
candidates = system.screen_universe(tickers, min_score=0.65)
```

### 4. **Backtest Strategy**
```python
from backtesting import BacktestingEngine, BacktestConfig

config = BacktestConfig(initial_capital=100000)
engine = BacktestingEngine(config)
results = engine.backtest(price_data, signals)
```

---

## 🐛 Troubleshooting

### Error: "FINNHUB_API_KEY not found"
```bash
# 1. Check .env exists
ls -la .env

# 2. Check it has your key
grep FINNHUB .env

# 3. Verify format (no extra spaces or quotes)
FINNHUB_API_KEY=abc123xyz  ✓ Correct
FINNHUB_API_KEY="abc123xyz"  ✗ Wrong (has quotes)
FINNHUB_API_KEY= abc123xyz  ✗ Wrong (space)
```

### Error: "Reddit authentication failed"
```bash
# 1. Verify Client ID is correct (not your password!)
# 2. Verify Client Secret is correct
# 3. Check Reddit username matches
REDDIT_USER_AGENT=QuantSignalSystem/1.0 by correct_username
```

### Error: "Rate limit exceeded"
- Wait 60 seconds and retry
- Check free tier limits (Finnhub: 60/min, NewsAPI: 100/day, etc.)

---

## 🔐 Security Reminder

⚠️ **NEVER:**
- Commit `.env` to GitHub
- Share your API keys with anyone
- Post your keys in public forums
- Log or print your API keys

✅ **DO:**
- Keep `.env` in `.gitignore` (already done)
- Rotate keys periodically
- Use different keys for dev/prod
- Monitor API usage for unusual activity

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| **SYSTEM_GUIDE.md** | Complete system overview, components, features |
| **SETUP_INSTRUCTIONS.md** | Detailed setup for each API service |
| **IMPLEMENTATION_SUMMARY.md** | What was built and why |
| **.env.example** | Template for API keys |
| **config.py** | Environment configuration utility |

---

## 🚀 You're All Set!

Run this to verify everything is working:

```bash
python -c "from integration import ComprehensiveSignalSystem; s = ComprehensiveSignalSystem(); print('✓ System ready!')"
```

Then:
```bash
python test_system.py
```

---

## 💡 Pro Tips

### Use Environment Variables Instead of .env (Production)
```python
import os
api_key = os.getenv('FINNHUB_API_KEY')
```

### Validate Before Using
```python
from config import EnvironmentConfig
config = EnvironmentConfig()
config.get_summary()
```

### Monitor API Usage
```python
# Check how many API calls you've made
python config.py --show
```

---

## Need Help?

1. **Setup issues?** → See `SETUP_INSTRUCTIONS.md`
2. **System questions?** → See `SYSTEM_GUIDE.md`
3. **Code questions?** → See docstrings in modules
4. **API keys?** → Check the links table above

---

## Ready to Trade!

After setup + API keys, your system can:

✅ Generate multi-timeframe trading signals
✅ Backtest strategies with realistic metrics
✅ Analyze sector/market sentiment
✅ Size positions for risk management
✅ Screen entire universes for opportunities

Start with `test_system.py` to see it in action!
