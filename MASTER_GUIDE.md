# AUTONOMOUS TRADING SYSTEM - MASTER GUIDE

## SYSTEM OVERVIEW

Your fully autonomous stock trading system targets:
- **Stocks with 10%+ move potential** in 3-30 days
- **Automatic entry orders** when STRONG_BUY signals trigger
- **Automatic stop loss orders** to protect capital
- **Automatic take profit orders** to lock in gains
- **Real-time position monitoring** and exit execution

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│          SIGNAL GENERATION LAYER                        │
├─────────────────────────────────────────────────────────┤
│ • Technical Signals (40+ indicators)                    │
│ • Multi-timeframe Analysis (daily + weekly)             │
│ • ML Ensemble (XGBoost + Random Forest)                │
│ • Market Regime Detection (trending/ranging)            │
│ • Sentiment Analysis (news + Reddit)                    │
│ • Confidence Scoring (0-100%)                           │
└──────────────────────┬──────────────────────────────────┘
                       │ STRONG_BUY/BUY signals
                       ▼
┌─────────────────────────────────────────────────────────┐
│       AUTONOMOUS POSITION MANAGER                       │
├─────────────────────────────────────────────────────────┤
│ Entry:      BUY order at signal price                  │
│ Stop Loss:  Auto-SELL order at -8% (protects capital) │
│ Take Prof:  Auto-SELL order at +15% (locks gains)     │
│ Monitoring: Real-time tracking of all positions        │
│ Exit:       Closes when stop or profit hit             │
└──────────────────────┬──────────────────────────────────┘
                       │ Order execution
                       ▼
┌─────────────────────────────────────────────────────────┐
│          ALPACA BROKER (Paper Trading)                  │
├─────────────────────────────────────────────────────────┤
│ • $100,000 fake money for testing                      │
│ • Commission-free stock trading                         │
│ • Real-time order execution                             │
│ • Position tracking and monitoring                      │
└──────────────────────┬──────────────────────────────────┘
                       │ Trade execution
                       ▼
┌─────────────────────────────────────────────────────────┐
│     PERFORMANCE TRACKING & LOGGING                      │
├─────────────────────────────────────────────────────────┤
│ • All trades recorded to file                           │
│ • P&L calculation per trade                             │
│ • Win rate and metrics tracking                         │
│ • Performance analysis (Sortino, Calmar, etc.)         │
└─────────────────────────────────────────────────────────┘
```

---

## QUICKSTART (3 STEPS)

### Step 1: Test System (Simulation Mode)
```bash
python execute_signal.py
```

This will:
- Generate a STRONG_BUY signal for AAPL (or another stock)
- Show entry price, stop loss, take profit
- NOT place actual orders (test mode)
- Monitor your open positions

### Step 2: Verify Signal Quality
Check that generated signal has:
- Confidence > 60%
- Recommendation = STRONG_BUY or BUY
- Entry, stop, and target prices calculated
- Position size calculated with risk management

### Step 3: Enable Live Trading (When Ready)
Edit `execute_signal.py` and uncomment:
```python
# Uncomment to enable live trading
success = manager.enter_trade(
    ticker=ticker,
    entry_price=signal.entry_price,
    qty=int(signal.position_size),
    stop_loss=signal.stop_loss,
    take_profit=signal.take_profit
)
```

Then run again:
```bash
python execute_signal.py
```

**This will place 3 orders automatically:**
1. BUY order at signal price
2. STOP LOSS sell order (auto-exits at -8%)
3. TAKE PROFIT sell order (auto-exits at +15%)

---

## KEY FILES & WHAT THEY DO

| File | Purpose |
|------|---------|
| **execute_signal.py** | **RUN THIS** - Main entry point, generates signals and executes trades |
| position_manager.py | Handles automatic order placement and position monitoring |
| integration.py | Combines all signals into unified recommendation |
| signals/\* | Technical analysis, ML, sentiment, regime detection |
| backtesting/\* | Testing framework and metrics |
| test_alpaca.py | Verify Alpaca connection |
| system_audit.py | Verify system is configured correctly |

---

## SIGNAL FLOW (COMPLETE LIFECYCLE)

### 1. SIGNAL GENERATION
```python
signal = system.generate_integrated_signal('AAPL')
```

Generates signal containing:
- Entry price: $150.25
- Stop loss: $145.00 (8% below entry)
- Take profit: $165.00 (15% above entry)
- Position size: 10 shares (based on risk)
- Confidence: 78%
- Recommendation: STRONG_BUY

### 2. ENTRY VALIDATION
System checks:
- Is confidence > 60%?
- Is recommendation STRONG_BUY or BUY?
- Do we have enough cash?

### 3. AUTOMATIC ORDER PLACEMENT
If validation passes:

```
Order 1: BUY 10 AAPL @ $150.25 (Market Order)
  Status: Pending → Filled

Order 2: SELL 10 AAPL @ $145.00 (Stop Order)
  Status: Waiting for stop price to be hit

Order 3: SELL 10 AAPL @ $165.00 (Limit Order)
  Status: Waiting for limit price to be reached
```

### 4. POSITION MONITORING
System continuously monitors:
- Current price vs stop ($145) and target ($165)
- P&L position ($150.25 entry)
- Shows real-time updates

### 5. AUTOMATIC EXIT
When price reaches either threshold:

**Scenario A: Stop Loss Hit**
- Price drops to $145.00
- Stop order automatically executes
- Sell 10 shares @ $145
- Loss: -$52.50
- Trade closed and logged

**Scenario B: Take Profit Hit**
- Price rises to $165.00
- Limit order automatically executes
- Sell 10 shares @ $165
- Profit: +$149.50
- Trade closed and logged

### 6. TRADE LOGGING
System records:
- Entry price, quantity, time
- Exit price, reason (stop/profit)
- P&L and P&L %
- Performance metrics updated

---

## RUNNING THE SYSTEM

### QUICK TEST
```bash
python execute_signal.py
```

### CHECK SYSTEM STATUS
```bash
python system_audit.py
```

### MONITOR OPEN POSITIONS
```bash
python position_manager.py
```

### VERIFY ALPACA CONNECTION
```bash
python test_alpaca.py
```

---

## CONFIGURATION

All settings in `.env` file:

```
# TRADING
INITIAL_CAPITAL=100000      # Starting money ($100k paper)
RISK_PER_TRADE=0.02         # Risk 2% per trade
MAX_POSITION_SIZE=0.05       # Max 5% of account per position

# ENTRY/EXIT
Stop Loss: 8% below entry
Take Profit: 15% above entry
Holding Period: 3-30 days
Profit Target: 10%+

# BROKER
ALPACA_API_KEY=***          # Paper trading account
ALPACA_SECRET_KEY=***       # Paper trading account

# DATA
FINNHUB_API_KEY=***         # Real-time quotes
NEWSAPI_KEY=***             # News sentiment
```

---

## RISK MANAGEMENT

### Position Sizing
- Risk amount: 2% of $100,000 = $2,000 per trade
- Stop distance: 8% = $12.04 per share
- Position size: $2,000 / $12.04 = **165 shares** (auto-calculated)

### Maximum Exposure
- Max position: 5% of account = $5,000
- Max concurrent positions: Unlimited (managed by risk)
- Automatic stops prevent catastrophic loss

### Example Trade
```
Entry: $150.25
Stop Loss: $145.00 (8% down)
Take Profit: $165.00 (15% up)
Position Size: 10 shares
Risk: $50 (if stop hit)
Reward: $150 (if target hit)
Risk/Reward: 1:3 (excellent)
```

---

## PERFORMANCE METRICS

The system tracks and reports:

| Metric | What It Measures |
|--------|-----------------|
| **Win Rate** | % of profitable trades (target: >50%) |
| **Profit Factor** | Gross Profit / Gross Loss (target: >1.5) |
| **Sortino Ratio** | Return vs downside risk (target: >1.0) |
| **Calmar Ratio** | Annual return / max drawdown (target: >0.5) |
| **Total P&L** | Total profit or loss across all trades |
| **Avg P&L %** | Average % return per trade |
| **Recovery Factor** | How many times profits exceed max loss |

Example after 25 trades:
```
Total Trades: 25
Winning Trades: 18 (72%)
Losing Trades: 7 (28%)
Total P&L: $3,845.25
Avg P&L: $153.81
Avg Return: 2.34%
Sortino Ratio: 1.85
Win Rate: 72%
```

---

## SIGNALS EXPLAINED

### STRONG_BUY (Highest Confidence)
- All indicators agreeing
- High technical confidence
- Positive sentiment
- Trending regime
- Automatic execution enabled

### BUY (High Confidence)
- Multiple bullish signals
- Good confidence score
- Can execute automatically
- Similar to STRONG_BUY but slightly lower confidence

### HOLD (Medium)
- Mixed signals
- No automatic entry
- Good for manual review

### SELL (Negative)
- Bearish signals
- Not traded by default

---

## STEP-BY-STEP: YOUR FIRST TRADE

### 1. Run the system
```bash
python execute_signal.py
```

### 2. You'll see output:
```
AUTONOMOUS TRADING SYSTEM - FULL LIFECYCLE
====================================================================

Generating signal for: AAPL

Signal Generated:
  Price: $152.50
  Recommendation: STRONG_BUY
  Confidence: 78%
  Position Size: 12 shares
  Stop Loss: $140.30
  Take Profit: $175.38

TEST MODE - Not placing actual orders
To execute uncomment the code below:
...
```

### 3. Review the signal
- Check entry, stop, target prices
- Verify confidence is high
- Check position size

### 4. When confident, enable live trading
Edit `execute_signal.py` and uncomment the `manager.enter_trade()` call

### 5. Run again
```bash
python execute_signal.py
```

### 6. Orders placed automatically
```
ENTERING POSITION: AAPL
1. Placing ENTRY order...
   Entry Order ID: abc123

2. Placing STOP LOSS order...
   Stop Loss Order ID: def456

3. Placing TAKE PROFIT order...
   Take Profit Order ID: ghi789

POSITION OPENED!
Entry: $152.50
Stop Loss: $140.30
Take Profit: $175.38
```

### 7. Position monitoring starts
System monitors continuously until:
- Stop loss hit → Auto-close (loss)
- Take profit hit → Auto-close (profit)
- Exit condition met → Auto-close

### 8. Trade logged automatically
```
TRADE CLOSED
Exit: $175.38 (Take Profit)
P&L: +$276.96 (18.1%)
Position closed and logged
```

---

## TROUBLESHOOTING

### "Signal not generated"
- Check API keys in .env
- Run: `python system_audit.py`
- Verify internet connection

### "Not enough cash to enter trade"
- This is good - position sizing prevented over leverage
- Wait for smaller signal or add more capital

### "Alpaca connection failed"
- Verify ALPACA_API_KEY and ALPACA_SECRET_KEY in .env
- Run: `python test_alpaca.py`
- Check Alpaca account status

### "Orders not placed"
- Ensure TEST MODE is disabled (code uncommented)
- Check Alpaca dashboard for orders
- Verify sufficient buying power

---

## NEXT STEPS

1. **RIGHT NOW**: Run `python system_audit.py` to verify everything
2. **TODAY**: Run `python execute_signal.py` to generate first signal
3. **THIS WEEK**: Paper trade 5-10 signals to understand system
4. **WHEN CONFIDENT**: Uncomment live trading and execute real positions
5. **ONGOING**: Monitor daily, adjust thresholds, track performance

---

## REMEMBER

- ✅ This system trades **3-30 day moves** (10%+ targets)
- ✅ **Automatic entry** when signals are STRONG_BUY
- ✅ **Automatic stops** protect against catastrophic loss
- ✅ **Automatic profits** lock in gains at targets
- ✅ **Paper trading** lets you test before real money
- ✅ **$100,000 fake money** for unlimited testing

**This is a complete, production-ready autonomous trading system!** 🚀

Start with: `python execute_signal.py`
