# API Setup & Configuration Guide

## Step 1: Create Your .env File

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

**IMPORTANT:** Never commit `.env` to version control. It's in `.gitignore` for a reason.

---

## Step 2: Reddit API Setup (Complete Instructions)

### 2A: Create Reddit Application

1. **Log in to Reddit** (create account if needed)
2. **Go to**: https://www.reddit.com/prefs/apps
3. **Scroll down** to "Authorized applications" section
4. **Click**: "Create an app" or "Create another app"

### 2B: Fill App Details

```
Application name:    QuantSignalSystem
App type:            ✓ script (for personal use)
Description:         Stock signal analysis and sentiment tracking
About URL:           (leave blank or enter your website)
Redirect URI:        http://localhost:8080
Permissions:         Read (default is fine)
```

### 2C: Get Your Credentials

After creating, you'll see:

```
personal use script
─────────────────
your_app_name

Client ID:     (the identifier under your app name)
Client Secret: (long random string - KEEP SECRET!)
```

### 2D: Update Your .env File

```bash
REDDIT_CLIENT_ID=abc123xyz...         # Copy from "Client ID"
REDDIT_CLIENT_SECRET=xyz789abc...     # Copy from "Client Secret"
REDDIT_USER_AGENT=QuantSignalSystem/1.0 by YourRedditUsername
```

**Replace `YourRedditUsername` with your actual Reddit username.**

---

## Step 3: Other API Keys

### Finnhub (Real-time Stock Data)
1. Go to: https://finnhub.io/register
2. Sign up (free tier available)
3. Copy your API key
4. Add to `.env`:
```bash
FINNHUB_API_KEY=your_key_here
```

### NewsAPI (Financial News)
1. Go to: https://newsapi.org/
2. Sign up (free tier: 100 requests/day)
3. Copy your API key
4. Add to `.env`:
```bash
NEWSAPI_KEY=your_key_here
```

### Alpha Vantage (Earnings Data)
1. Go to: https://www.alphavantage.co/
2. Sign up (free tier: 5 calls/minute)
3. Copy your API key
4. Add to `.env`:
```bash
ALPHAVANTAGE_KEY=your_key_here
```

---

## Step 4: Verify Your Setup

Run this test script to verify all API keys are working:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Check all keys are set
keys_to_check = [
    'FINNHUB_API_KEY',
    'NEWSAPI_KEY',
    'REDDIT_CLIENT_ID',
    'REDDIT_CLIENT_SECRET',
    'REDDIT_USER_AGENT'
]

for key in keys_to_check:
    value = os.getenv(key)
    status = "✓ SET" if value else "✗ MISSING"
    print(f"{key}: {status}")
    if value:
        # Show masked value (first 4 chars)
        masked = value[:4] + "*" * (len(value) - 4)
        print(f"  Value: {masked}")
```

---

## Step 5: Test Reddit Integration

Once you have Reddit credentials, test with:

```python
from data.sentiment_fetcher import RedditSentimentOptional

reddit = RedditSentimentOptional()
result = reddit.get_subreddit_sentiment('NVDA', subreddit_names=['wallstreetbets'])
print(result)
```

---

## Security Best Practices

### ✅ DO:
- ✓ Keep `.env` in `.gitignore`
- ✓ Use environment variables for all secrets
- ✓ Rotate keys periodically
- ✓ Use different keys for dev vs production
- ✓ Restrict key permissions to minimum needed
- ✓ Monitor API usage for unusual activity

### ❌ DON'T:
- ✗ Commit `.env` to git/GitHub
- ✗ Hardcode secrets in source code
- ✗ Share API keys via email/chat
- ✗ Use same key across multiple environments
- ✗ Log or print API keys
- ✗ Push secret keys to public repositories

---

## Free Tier API Limits

| API | Calls/Min | Calls/Day | Cost |
|-----|-----------|-----------|------|
| Finnhub | 60 | - | Free |
| NewsAPI | - | 100 | Free |
| Alpha Vantage | 5 | 500 | Free |
| Reddit | - | Unlimited | Free |
| EODHD | - | 20 | Free |

---

## Troubleshooting API Issues

### "FINNHUB_API_KEY not found"
```bash
# Verify .env file exists and contains key
cat .env | grep FINNHUB

# Ensure you're loading dotenv in your script
from dotenv import load_dotenv
load_dotenv()
```

### "Reddit authentication failed"
```bash
# Verify credentials:
# 1. Client ID is correct (under your app name)
# 2. Client Secret is correct (not the password!)
# 3. User agent includes your Reddit username
# 4. .env values don't have extra spaces
```

### "Rate limit exceeded"
- Finnhub: Wait 1 minute before next request
- NewsAPI: Limited to 100/day on free tier
- Alpha Vantage: Limited to 5 calls/minute
- Reddit: Generally unlimited but be respectful

---

## Production Deployment

For production, use a secrets manager instead of `.env`:

### Option 1: Environment Variables (Docker)
```dockerfile
ENV FINNHUB_API_KEY=value_from_secret
ENV REDDIT_CLIENT_ID=value_from_secret
```

### Option 2: AWS Secrets Manager
```python
import json
import boto3

def get_secrets():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='stocks-keys')
    return json.loads(secret['SecretString'])
```

### Option 3: HashiCorp Vault
```python
import hvac

client = hvac.Client(url='http://vault.example.com:8200')
secret = client.secrets.kv.read_secret_version(path='stocks-api-keys')
```

---

## Final Checklist

Before starting trading:

- [ ] `.env` file created with all API keys
- [ ] `.env` added to `.gitignore`
- [ ] All API keys verified (run test script)
- [ ] Reddit app created and credentials added
- [ ] Finnhub key working
- [ ] NewsAPI key working
- [ ] `requirements.txt` installed (`pip install -r requirements.txt`)
- [ ] `test_system.py` runs successfully
- [ ] Sentiment analysis can fetch data
- [ ] Ready for signal generation!

---

## Need Help?

If you have issues:

1. **Check .env file**: `cat .env`
2. **Verify key format**: Should be actual string, not `your_key_here`
3. **Check for spaces**: Keys shouldn't have leading/trailing whitespace
4. **Run tests**: `python test_system.py`
5. **Check API status**: Visit provider's status page
