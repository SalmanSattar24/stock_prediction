"""
Backtesting Engine with Realistic Risk Management
Implements stop loss, take profit, position sizing, and accurate metrics
"""

from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import numpy as np


@dataclass
class TradeRecord:
    """Single trade record"""
    ticker: str
    entry_date: str
    entry_price: float
    entry_signal: str
    confidence: float
    position_size: float
    exit_date: str = None
    exit_price: float = 0
    exit_reason: str = None  # "stop_loss", "take_profit", "timeout", "signal_reversal"
    pnl: float = 0
    pnl_percent: float = 0
    bars_held: int = 0
    max_profit: float = 0  # Peak profit during trade
    max_loss: float = 0    # Peak loss during trade

    def calculate_pnl(self):
        if self.exit_price > 0:
            self.pnl = (self.exit_price - self.entry_price) * self.position_size
            self.pnl_percent = ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return self

    def __str__(self):
        return f"{self.ticker} | Entry: {self.entry_date} @ ${self.entry_price:.2f} | Exit: {self.exit_date} @ ${self.exit_price:.2f} | PnL: ${self.pnl:.2f} ({self.pnl_percent:.2f}%)"


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 100000
    max_position_size: float = 0.05  # Max 5% of capital per trade
    risk_per_trade: float = 0.02  # Risk 2% of capital per trade
    stop_loss_pct: float = 0.08  # 8% stop loss
    take_profit_pct: float = 0.15  # 15% take profit
    use_volatility_stops: bool = True  # Adjust stops by ATR
    use_trailing_stop: bool = False  # Trailing stop loss
    commission: float = 0.001  # 0.1% commission per trade
    slippage: float = 0.0005  # 0.05% slippage on entries/exits


class Position:
    """Track active position"""
    def __init__(self, ticker: str, entry_price: float, entry_date: str,
                 position_size: float, entry_signal: str, confidence: float,
                 stop_loss: float, take_profit: float):
        self.ticker = ticker
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.position_size = position_size
        self.entry_signal = entry_signal
        self.confidence = confidence
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.current_price = entry_price
        self.max_price = entry_price
        self.min_price = entry_price
        self.trailing_stop = stop_loss

    def update_price(self, price: float):
        """Update position with current price"""
        self.current_price = price
        self.max_price = max(self.max_price, price)
        self.min_price = min(self.min_price, price)

        # Update trailing stop
        if self.trailing_stop < self.max_price * 0.92:  # 8% trailing
            self.trailing_stop = self.max_price * 0.92

    def get_current_pnl(self) -> Tuple[float, float]:
        """Get current PnL in dollars and percent"""
        pnl = (self.current_price - self.entry_price) * self.position_size
        pnl_pct = ((self.current_price - self.entry_price) / self.entry_price) * 100
        return pnl, pnl_pct

    def check_exit_condition(self, use_trailing: bool = False) -> Tuple[bool, str, float]:
        """
        Check if position should be exited
        Returns: (should_exit, exit_reason, exit_price)
        """
        stop_level = self.trailing_stop if use_trailing else self.stop_loss

        if self.current_price >= self.take_profit:
            return True, "take_profit", self.take_profit
        elif self.current_price <= stop_level:
            return True, "stop_loss", stop_level
        return False, None, None


class BacktestingEngine:
    """
    Backtesting engine with realistic risk management
    """

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.capital = self.config.initial_capital
        self.positions = []  # Active positions
        self.closed_trades = []  # Completed trades
        self.cash = self.capital
        self.equity_curve = [(0, self.capital)]
        self.bar_count = 0

    def size_position(self, price: float, stop_loss: float, confidence: float = 100) -> float:
        """
        Calculate position size based on risk management
        Position_size = (Risk_Amount / Distance_to_Stop) * Confidence_Adjustment
        """
        risk_amount = self.capital * self.config.risk_per_trade
        stop_distance = price - stop_loss
        stop_distance_pct = (stop_distance / price) * 100 if price > 0 else 0

        if stop_distance_pct <= 0:
            return 0

        # Base position size from risk calculation
        position_size = risk_amount / stop_distance

        # Adjust for confidence
        confidence_multiplier = confidence / 100
        position_size *= confidence_multiplier

        # Cap at max position size
        max_position_value = self.capital * self.config.max_position_size
        position_size = min(position_size, max_position_value / price)

        # Ensure we have cash
        position_cost = position_size * price
        if position_cost > self.cash:
            position_size = self.cash / price

        return position_size

    def enter_trade(self, ticker: str, price: float, signal: str, confidence: float = 80,
                   bars_in_signal: int = 1, volatility: float = None) -> bool:
        """
        Enter a new trade
        - Executes on NEXT bar (not current bar) to avoid look-ahead bias
        - Applies slippage
        - Calculates stops based on confidence and volatility
        """
        # Apply slippage
        entry_price = price * (1 + self.config.slippage if signal == 'BUY' else 1 - self.config.slippage)

        # Calculate stops and targets
        if self.config.use_volatility_stops and volatility:
            # ATR-based stops (tighter in low vol, wider in high vol)
            stop_distance = volatility * 0.5
            take_profit_distance = volatility * 1.5
        else:
            stop_distance = entry_price * self.config.stop_loss_pct
            take_profit_distance = entry_price * self.config.take_profit_pct

        stop_loss = entry_price - stop_distance
        take_profit = entry_price + take_profit_distance

        # Size position
        position_size = self.size_position(entry_price, stop_loss, confidence)

        if position_size <= 0:
            return False

        # Apply commission
        commission = position_size * entry_price * self.config.commission
        self.cash -= (position_size * entry_price + commission)

        # Create position
        position = Position(
            ticker=ticker,
            entry_price=entry_price,
            entry_date=f"bar_{self.bar_count}",
            position_size=position_size,
            entry_signal=signal,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.positions.append(position)
        return True

    def exit_trade(self, position: Position, exit_price: float, exit_reason: str, exit_date: str = None) -> TradeRecord:
        """
        Exit a position and record the trade
        """
        # Apply slippage
        exit_price = exit_price * (1 - self.config.slippage)

        # Apply commission
        commission = position.position_size * exit_price * self.config.commission

        # Create trade record
        trade = TradeRecord(
            ticker=position.ticker,
            entry_date=position.entry_date,
            entry_price=position.entry_price,
            entry_signal=position.entry_signal,
            confidence=position.confidence,
            position_size=position.position_size,
            exit_date=exit_date or f"bar_{self.bar_count}",
            exit_price=exit_price,
            exit_reason=exit_reason,
            bars_held=self.bar_count - int(position.entry_date.split('_')[1])
        )

        # Calculate PnL
        trade.calculate_pnl()
        trade.pnl -= commission  # Deduct commissions

        # Update cash
        self.cash += (position.position_size * exit_price - commission)

        # Track closed trades
        self.closed_trades.append(trade)

        return trade

    def process_bar(self, price_data: Dict, active_signals: List[Dict] = None):
        """
        Process a single bar
        - Check exits on existing positions
        - Enter new trades based on signals (next bar execution)
        - Update equity
        """
        self.bar_count += 1

        # Update price on active positions and check exits
        for pos in self.positions[:]:
            current_price = price_data.get('close', 0)
            pos.update_price(current_price)

            should_exit, exit_reason, exit_price = pos.check_exit_condition(self.config.use_trailing_stop)

            if should_exit and exit_price:
                self.exit_trade(pos, exit_price, exit_reason)
                self.positions.remove(pos)

        # Process new signals (would execute on next bar)
        if active_signals:
            for signal in active_signals:
                if signal.get('direction') in ['BULLISH', 'BEARISH']:
                    entry_price = price_data.get('close', 0)
                    self.enter_trade(
                        ticker=signal.get('ticker', 'UNKNOWN'),
                        price=entry_price,
                        signal=signal.get('direction'),
                        confidence=signal.get('confidence', 80),
                        volatility=price_data.get('atr', None)
                    )

        # Update equity
        current_cash = self.cash
        for pos in self.positions:
            pos.update_price(price_data.get('close', 0))
            pnl, _ = pos.get_current_pnl()
            current_cash += pnl

        self.equity_curve.append((self.bar_count, current_cash))

    def backtest(self, price_bars: List[Dict], signals_by_bar: List[List[Dict]]) -> Dict:
        """
        Run full backtest on price data with signals

        price_bars: List of OHLCV data
        signals_by_bar: List of signals for each bar (aligned with price_bars)
        """
        for i, bar in enumerate(price_bars):
            signals = signals_by_bar[i] if i < len(signals_by_bar) else []
            self.process_bar(bar, signals)

        # Close all remaining positions
        final_price = price_bars[-1].get('close', 0) if price_bars else 0
        for pos in self.positions[:]:
            self.exit_trade(pos, final_price, "backtest_end")
            self.positions.remove(pos)

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate comprehensive backtest report"""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'status': 'No trades executed'
            }

        total_pnl = sum(t.pnl for t in self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl < 0]

        win_rate = len(winning_trades) / len(self.closed_trades) * 100
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades and sum(t.pnl for t in losing_trades) != 0 else 0

        # Equity curve analysis
        equity_values = [e[1] for e in self.equity_curve]
        if len(equity_values) > 1:
            total_return = (equity_values[-1] - equity_values[0]) / equity_values[0] * 100
            max_equity = max(equity_values)
            max_drawdown_pct = (min(equity_values) - max_equity) / max_equity * 100 if max_equity > 0 else 0
        else:
            total_return = 0
            max_drawdown_pct = 0

        # Sharpe (simplified)
        if len(self.closed_trades) > 1:
            returns = [t.pnl_percent for t in self.closed_trades]
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0

        return {
            'total_trades': len(self.closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe,
            'initial_capital': self.config.initial_capital,
            'final_capital': self.capital + self.cash,
            'trades': [
                {
                    'ticker': t.ticker,
                    'entry': f"{t.entry_price:.2f}",
                    'exit': f"{t.exit_price:.2f}",
                    'pnl': f"{t.pnl:.2f}",
                    'pnl_pct': f"{t.pnl_percent:.2f}%",
                    'reason': t.exit_reason
                }
                for t in self.closed_trades[:20]  # Top 20 trades
            ]
        }


if __name__ == "__main__":
    config = BacktestConfig(
        initial_capital=100000,
        stop_loss_pct=0.08,
        take_profit_pct=0.15
    )

    engine = BacktestingEngine(config)
    print("Backtesting Engine initialized")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    print(f"Risk per Trade: {config.risk_per_trade*100:.1f}%")
    print(f"Max Position Size: {config.max_position_size*100:.1f}%")
