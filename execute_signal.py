"""
Execute Trading Signals on Alpaca (AUTONOMOUSLY)
Automatically:
1. Place entry orders
2. Place stop loss orders
3. Place take profit orders
4. Monitor positions
5. Close on exit conditions
"""

from dotenv import load_dotenv
from position_manager import AutonomousPositionManager
from integration import ComprehensiveSignalSystem

load_dotenv()

print("=" * 70)
print("AUTONOMOUS TRADING SYSTEM - FULL LIFECYCLE")
print("=" * 70)

# Initialize
manager = AutonomousPositionManager()
system = ComprehensiveSignalSystem()

# Example: Generate and execute a signal
ticker = 'AAPL'
print(f"\n📍 Generating signal for: {ticker}")

try:
    signal = system.generate_integrated_signal(ticker)

    if not signal:
        print(f"❌ Could not generate signal for {ticker}")
        exit(1)

    print(f"\n✓ Signal Generated:")
    print(f"  Price: ${signal.entry_price:.2f}")
    print(f"  Recommendation: {signal.final_recommendation}")
    print(f"  Confidence: {signal.weighted_score:.2%}")
    print(f"  Position Size: {signal.position_size:.0f} shares")
    print(f"  Stop Loss: ${signal.stop_loss:.2f}")
    print(f"  Take Profit: ${signal.take_profit:.2f}")

    # Only execute strong signals
    if signal.final_recommendation not in ['STRONG_BUY', 'BUY']:
        print(f"\n⏭️  Signal not strong enough (recommendation: {signal.final_recommendation})")
        print("    Skipping execution")
    else:
        print(f"\n✅ Signal is strong! Executing full trade lifecycle...\n")

        # THIS WILL ACTUALLY EXECUTE - uncomment to enable
        print("⚠️  TEST MODE - Not actually executing")
        print("   To execute uncomment the code below:\n")

        """
        # Enter trade with automatic stop loss and take profit
        success = manager.enter_trade(
            ticker=ticker,
            entry_price=signal.entry_price,
            qty=int(signal.position_size),
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit
        )

        if success:
            print("\n✅ Trade entered successfully!")
            print("   - Entry order placed")
            print("   - Stop loss order placed")
            print("   - Take profit order placed")
            print("   - Position is now being monitored automatically")
        """

        print("\nTo activate live trading:")
        print("1. Uncomment the manager.enter_trade() block above")
        print("2. Run this script again")
        print("3. Orders will be placed on Alpaca")
        print("4. Stops and targets will execute automatically")

    # Monitor all open positions
    print(f"\n{'='*70}")
    print("MONITORING ALL OPEN POSITIONS")
    print(f"{'='*70}")
    manager.monitor_positions()

    # Show performance
    perf = manager.get_performance()
    if perf and perf.get('total_trades', 0) > 0:
        print(f"\n{'='*70}")
        print("SYSTEM PERFORMANCE")
        print(f"{'='*70}")
        print(f"Total Trades: {perf.get('total_trades', 0)}")
        print(f"Wins: {perf.get('winning_trades', 0)}")
        print(f"Losses: {perf.get('losing_trades', 0)}")
        print(f"Win Rate: {perf.get('win_rate', 0):.1f}%")
        print(f"Total P&L: ${perf.get('total_pnl', 0):.2f}")
        print(f"Avg P&L: ${perf.get('avg_pnl', 0):.2f}")
        print(f"Avg P&L %: {perf.get('avg_pnl_pct', 0):.2f}%")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

