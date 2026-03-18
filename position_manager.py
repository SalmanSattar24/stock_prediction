"""
Autonomous Position Manager
Handles entry, stop loss, take profit, and exit for all open positions
Manages the complete trade lifecycle automatically
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from typing import Dict

load_dotenv()


class Position:
    """Track a single open position"""

    def __init__(self, ticker: str, entry_price: float, qty: int, stop_loss: float, take_profit: float):
        self.ticker = ticker
        self.entry_price = entry_price
        self.qty = qty
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_time = datetime.now()
        self.entry_order_id = None
        self.stop_order_id = None
        self.profit_order_id = None
        self.status = "PENDING_ENTRY"  # PENDING_ENTRY, OPEN, STOPPED, PROFIT, CLOSED

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'entry_price': self.entry_price,
            'qty': self.qty,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'entry_time': self.entry_time.isoformat(),
            'status': self.status,
            'entry_order_id': self.entry_order_id,
            'stop_order_id': self.stop_order_id,
            'profit_order_id': self.profit_order_id
        }


class AutonomousPositionManager:
    """
    Manages all open positions autonomously
    Handles:
    - Entry order placement
    - Stop loss order placement
    - Take profit order placement
    - Position monitoring
    - Automatic exits
    """

    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.client = TradingClient(api_key=self.api_key, secret_key=self.secret_key, paper=True)
        self.positions = {}  # ticker -> Position object
        self.trade_log = []
        self.load_positions()

    def load_positions(self):
        """Load saved positions from file"""
        try:
            if os.path.exists('open_positions.json'):
                with open('open_positions.json', 'r') as f:
                    data = json.load(f)
                    for ticker, pos_data in data.items():
                        pos = Position(
                            ticker=ticker,
                            entry_price=pos_data['entry_price'],
                            qty=pos_data['qty'],
                            stop_loss=pos_data['stop_loss'],
                            take_profit=pos_data['take_profit']
                        )
                        pos.status = pos_data['status']
                        pos.entry_order_id = pos_data.get('entry_order_id')
                        pos.stop_order_id = pos_data.get('stop_order_id')
                        pos.profit_order_id = pos_data.get('profit_order_id')
                        self.positions[ticker] = pos
                print(f"✓ Loaded {len(self.positions)} open positions")
        except Exception as e:
            print(f"Note: No saved positions found ({e})")

    def save_positions(self):
        """Save positions to file for persistence"""
        data = {ticker: pos.to_dict() for ticker, pos in self.positions.items()}
        with open('open_positions.json', 'w') as f:
            json.dump(data, f, indent=2)

    def enter_trade(self, ticker: str, entry_price: float, qty: int,
                   stop_loss: float, take_profit: float) -> bool:
        """
        Enter a new trade with entry + stop + profit orders

        Returns: True if all orders placed successfully
        """
        print(f"\n{'='*60}")
        print(f"ENTERING POSITION: {ticker}")
        print(f"{'='*60}")

        try:
            # Create position object
            position = Position(ticker, entry_price, qty, stop_loss, take_profit)

            # Step 1: Place entry order
            print(f"\n1️⃣  Placing ENTRY order...")
            entry_order = MarketOrderRequest(
                symbol=ticker,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            entry_result = self.client.submit_order(entry_order)
            position.entry_order_id = entry_result.id
            position.status = "PENDING_ENTRY"

            print(f"   ✓ Entry Order ID: {entry_result.id}")
            print(f"   ✓ Symbol: {ticker}")
            print(f"   ✓ Quantity: {qty}")
            print(f"   ✓ Status: {entry_result.status}")

            # Step 2: Place STOP LOSS order
            print(f"\n2️⃣  Placing STOP LOSS order...")
            stop_order = StopOrderRequest(
                symbol=ticker,
                qty=qty,
                side=OrderSide.SELL,
                stop_price=stop_loss,
                time_in_force=TimeInForce.GTC  # Good-til-cancelled
            )
            stop_result = self.client.submit_order(stop_order)
            position.stop_order_id = stop_result.id
            position.status = "OPEN"

            print(f"   ✓ Stop Loss Order ID: {stop_result.id}")
            print(f"   ✓ Stop Price: ${stop_loss:.2f}")
            print(f"   ✓ Qty: {qty}")
            print(f"   ✓ Status: {stop_result.status}")

            # Step 3: Place TAKE PROFIT order (limit order)
            print(f"\n3️⃣  Placing TAKE PROFIT order...")
            profit_order = LimitOrderRequest(
                symbol=ticker,
                qty=qty,
                side=OrderSide.SELL,
                limit_price=take_profit,
                time_in_force=TimeInForce.GTC  # Good-til-cancelled
            )
            profit_result = self.client.submit_order(profit_order)
            position.profit_order_id = profit_result.id

            print(f"   ✓ Take Profit Order ID: {profit_result.id}")
            print(f"   ✓ Target Price: ${take_profit:.2f}")
            print(f"   ✓ Qty: {qty}")
            print(f"   ✓ Status: {profit_result.status}")

            # Save position
            self.positions[ticker] = position
            self.save_positions()

            # Log trade
            self.log_trade('ENTRY', ticker, qty, entry_price, stop_loss, take_profit)

            print(f"\n✅ POSITION OPENED!")
            print(f"   Entry: ${entry_price:.2f}")
            print(f"   Stop Loss: ${stop_loss:.2f}")
            print(f"   Take Profit: ${take_profit:.2f}")
            print(f"   Risk: ${(entry_price - stop_loss) * qty:.2f}")
            print(f"   Reward: ${(take_profit - entry_price) * qty:.2f}")
            print(f"   Risk/Reward Ratio: {(take_profit - entry_price) / (entry_price - stop_loss):.2f}:1")

            return True

        except Exception as e:
            print(f"\n❌ ERROR entering trade: {e}")
            return False

    def monitor_positions(self):
        """Monitor all open positions and check for exits"""
        if not self.positions:
            print("No open positions to monitor")
            return

        print(f"\n{'='*60}")
        print(f"MONITORING {len(self.positions)} OPEN POSITIONS")
        print(f"{'='*60}")

        for ticker, position in self.positions.items():
            try:
                # Get current price
                quote = self.client.get_latest_bar(ticker)
                current_price = quote.c if quote else 0

                if not current_price:
                    print(f"\n⚠️  {ticker}: Could not get current price")
                    continue

                # Calculate P&L
                entry_value = position.entry_price * position.qty
                current_value = current_price * position.qty
                pnl = current_value - entry_value
                pnl_pct = (pnl / entry_value) * 100

                print(f"\n📊 {ticker}")
                print(f"   Entry Price: ${position.entry_price:.2f}")
                print(f"   Current Price: ${current_price:.2f}")
                print(f"   P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
                print(f"   Qty: {position.qty}")
                print(f"   Stop Loss: ${position.stop_loss:.2f}")
                print(f"   Take Profit: ${position.take_profit:.2f}")

                # Check if position should have exited
                if current_price <= position.stop_loss:
                    print(f"   ⚠️  STOP LOSS HIT! (Target: ${position.stop_loss:.2f})")
                    self.close_position(ticker, current_price, 'STOP_LOSS')
                elif current_price >= position.take_profit:
                    print(f"   ✅ TAKE PROFIT HIT! (Target: ${position.take_profit:.2f})")
                    self.close_position(ticker, current_price, 'TAKE_PROFIT')

            except Exception as e:
                print(f"\n❌ Error monitoring {ticker}: {e}")

    def close_position(self, ticker: str, exit_price: float, reason: str):
        """Close an open position"""
        if ticker not in self.positions:
            print(f"Position {ticker} not found")
            return False

        position = self.positions[ticker]

        try:
            print(f"\n🔴 CLOSING POSITION: {ticker}")
            print(f"   Reason: {reason}")
            print(f"   Exit Price: ${exit_price:.2f}")

            # Place market sell order to close position
            sell_order = MarketOrderRequest(
                symbol=ticker,
                qty=position.qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            result = self.client.submit_order(sell_order)

            # Calculate P&L
            entry_value = position.entry_price * position.qty
            exit_value = exit_price * position.qty
            pnl = exit_value - entry_value
            pnl_pct = (pnl / entry_value) * 100

            # Log trade
            self.log_trade('EXIT', ticker, position.qty, exit_price,
                         position.stop_loss, position.take_profit,
                         reason=reason, pnl=pnl, pnl_pct=pnl_pct)

            print(f"   ✓ Exit Order ID: {result.id}")
            print(f"   ✓ P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")

            # Remove from open positions
            del self.positions[ticker]
            self.save_positions()

            print(f"✅ POSITION CLOSED!")
            return True

        except Exception as e:
            print(f"❌ ERROR closing position: {e}")
            return False

    def get_active_positions(self) -> Dict:
        """Get all active positions from Alpaca"""
        try:
            positions = self.client.get_all_positions()
            result = {}
            for pos in positions:
                result[pos.symbol] = {
                    'qty': float(pos.qty),
                    'avg_fill_price': float(pos.avg_fill_price),
                    'current_price': float(pos.current_price),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc) * 100
                }
            return result
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {}

    def log_trade(self, trade_type: str, ticker: str, qty: int, price: float,
                 stop_loss: float, take_profit: float, reason: str = "",
                 pnl: float = 0, pnl_pct: float = 0):
        """Log all trades to file"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'type': trade_type,
            'ticker': ticker,
            'qty': qty,
            'price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
        self.trade_log.append(trade)

        # Save to file
        with open('trade_log.json', 'a') as f:
            f.write(json.dumps(trade) + '\n')

    def get_performance(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trade_log:
            return {}

        exits = [t for t in self.trade_log if t['type'] == 'EXIT']
        if not exits:
            return {'trades': 0}

        pnls = [t['pnl'] for t in exits]
        pnl_pcts = [t['pnl_pct'] for t in exits]

        wins = sum(1 for p in pnls if p > 0)
        losses = sum(1 for p in pnls if p < 0)
        total_pnl = sum(pnls)

        return {
            'total_trades': len(exits),
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': (wins / len(exits) * 100) if exits else 0,
            'total_pnl': total_pnl,
            'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
            'avg_pnl_pct': sum(pnl_pcts) / len(pnl_pcts) if pnl_pcts else 0
        }


def main():
    """Demo: Enter and monitor a position"""
    print("\n" + "="*60)
    print("AUTONOMOUS POSITION MANAGER - DEMO")
    print("="*60)

    manager = AutonomousPositionManager()

    # Example: Enter a position (uncomment to use)
    # manager.enter_trade(
    #     ticker='AAPL',
    #     entry_price=150.00,
    #     qty=1,
    #     stop_loss=145.00,
    #     take_profit=160.00
    # )

    # Monitor all open positions
    manager.monitor_positions()

    # Show performance
    perf = manager.get_performance()
    if perf:
        print(f"\n{'='*60}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Total Trades: {perf.get('total_trades', 0)}")
        print(f"Wins: {perf.get('winning_trades', 0)}")
        print(f"Losses: {perf.get('losing_trades', 0)}")
        print(f"Win Rate: {perf.get('win_rate', 0):.1f}%")
        print(f"Total P&L: ${perf.get('total_pnl', 0):.2f}")
        print(f"Avg P&L: ${perf.get('avg_pnl', 0):.2f}")
        print(f"Avg P&L %: {perf.get('avg_pnl_pct', 0):.2f}%")


if __name__ == "__main__":
    main()
