"""
Test Alpaca Connection
Verify your API keys are working
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API keys from .env
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

print("=" * 60)
print("ALPACA API TEST")
print("=" * 60)

# Check if keys exist
if not api_key:
    print("\n❌ ERROR: ALPACA_API_KEY not found in .env")
    print("   Add this to .env:")
    print("   ALPACA_API_KEY=your_key_here")
    exit(1)

if not secret_key:
    print("\n❌ ERROR: ALPACA_SECRET_KEY not found in .env")
    print("   Add this to .env:")
    print("   ALPACA_SECRET_KEY=your_secret_here")
    exit(1)

print("\n✓ API Keys found in .env")
print(f"  API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"  Secret: {secret_key[:10]}...{secret_key[-4:]}")

# Try to connect
try:
    from alpaca.trading.client import TradingClient

    print("\n⏳ Connecting to Alpaca...")
    client = TradingClient(api_key=api_key, secret_key=secret_key, paper=True)

    # Get account info
    account = client.get_account()

    print("\n✅ CONNECTION SUCCESSFUL!")
    print("\nAccount Info:")
    print(f"  Account Status: {account.status}")
    print(f"  Cash: ${float(account.cash):,.2f}")
    print(f"  Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"  Buying Power: ${float(account.buying_power):,.2f}")
    print(f"  Trading Mode: Paper Trading (Sandbox)")

    print("\n✅ You're ready to trade!")
    print("\nYour paper trading account has $100,000 to test with!")
    print("You can now:")
    print("  1. Generate signals with your system")
    print("  2. Execute them automatically")
    print("  3. See performance in real-time")

except ImportError:
    print("\n⚠️  ERROR: alpaca-py not installed")
    print("   Install with: pip install alpaca-py")
    exit(1)

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
    print("\n   Troubleshooting:")
    print("   1. Check your API Key is correct (should start with 'PK')")
    print("   2. Check your Secret Key is correct")
    print("   3. Make sure you're using PAPER trading keys (not live)")
    print("   4. Wait a few minutes after creating keys")
    exit(1)
