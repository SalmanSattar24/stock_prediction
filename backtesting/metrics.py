"""
Advanced Backtesting Metrics
Sortino, Calmar, Profit Factor, and more
"""

from typing import List, Dict, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class MetricsResult:
    """Complete metrics result set"""
    total_return: float  # % return
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    profit_factor: float
    win_rate: float
    max_drawdown: float
    consecutive_losses: int
    recovery_factor: float
    trade_efficiency: float  # Profit per bar held


class BacktestMetrics:
    """Calculate comprehensive trading metrics"""

    @staticmethod
    def calculate_returns(equity_curve: List[Tuple[int, float]]) -> np.ndarray:
        """Calculate daily returns from equity curve"""
        if len(equity_curve) < 2:
            return np.array([])

        values = np.array([e[1] for e in equity_curve])
        returns = np.diff(values) / values[:-1]
        return returns

    @staticmethod
    def sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Sharpe Ratio = (Return - Risk_Free_Rate) / Volatility
        Annualized: Sharpe * sqrt(252)
        """
        if len(returns) < 2 or np.std(returns) == 0:
            return 0

        excess_return = np.mean(returns) - (risk_free_rate / 252)
        volatility = np.std(returns)
        return (excess_return / volatility) * np.sqrt(252) if volatility > 0 else 0

    @staticmethod
    def sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Sortino Ratio = (Return - Risk_Free_Rate) / Downside_Volatility
        Only penalizes downside volatility, better for trading
        """
        if len(returns) < 2:
            return 0

        excess_return = np.mean(returns) - (risk_free_rate / 252)
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return 100  # All positive returns

        downside_volatility = np.std(downside_returns)
        return (excess_return / downside_volatility) * np.sqrt(252) if downside_volatility > 0 else 0

    @staticmethod
    def calmar_ratio(total_return: float, max_drawdown: float) -> float:
        """
        Calmar Ratio = Annual_Return / Max_Drawdown
        Directly measures return per unit of risk
        Good for comparing trading strategies
        """
        if max_drawdown == 0 or abs(max_drawdown) < 0.001:
            return 0

        annual_return = total_return / 1  # Simplified, actual would need period
        return annual_return / abs(max_drawdown)

    @staticmethod
    def max_drawdown(equity_curve: List[Tuple[int, float]]) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown and recovery period
        Returns: (max_drawdown_pct, bars_to_max_dd, bars_to_recovery)
        """
        if len(equity_curve) < 2:
            return 0, 0, 0

        values = np.array([e[1] for e in equity_curve])
        cumulative_max = np.maximum.accumulate(values)
        drawdown = (values - cumulative_max) / cumulative_max

        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)

        # Find recovery point
        recovered_idx = max_dd_idx
        for i in range(max_dd_idx + 1, len(values)):
            if values[i] >= cumulative_max[max_dd_idx]:
                recovered_idx = i
                break

        return float(max_dd) * 100, max_dd_idx, recovered_idx - max_dd_idx

    @staticmethod
    def win_rate(trades: List[Dict]) -> Tuple[float, int, int]:
        """Calculate win rate (% of profitable trades)"""
        if not trades:
            return 0, 0, 0

        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losses = sum(1 for t in trades if t.get('pnl', 0) < 0)

        win_rate = (wins / len(trades) * 100) if trades else 0
        return win_rate, wins, losses

    @staticmethod
    def profit_factor(trades: List[Dict]) -> float:
        """
        Profit Factor = Gross_Profit / Gross_Loss
        > 2.0 is excellent, > 1.5 is good, < 1.0 is losing
        """
        if not trades:
            return 0

        profits = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        losses = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0)

        if losses == 0:
            return float('inf') if profits > 0 else 0

        return abs(profits / losses)

    @staticmethod
    def payoff_ratio(trades: List[Dict]) -> float:
        """
        Payoff Ratio = Avg_Win / Avg_Loss
        How much you win vs lose per trade
        """
        if not trades:
            return 0

        wins = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
        losses = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]

        if not losses or not wins:
            return 0

        avg_win = np.mean(wins)
        avg_loss = np.mean(losses)

        return abs(avg_win / avg_loss) if avg_loss != 0 else 0

    @staticmethod
    def consecutive_losses(trades: List[Dict]) -> int:
        """Maximum consecutive losing trades"""
        if not trades:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            if trade.get('pnl', 0) < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    @staticmethod
    def recovery_factor(gross_profit: float, max_drawdown: float) -> float:
        """
        Recovery Factor = Gross_Profit / Max_Drawdown
        How many times you recover drawdown from profits
        """
        if max_drawdown == 0:
            return float('inf') if gross_profit > 0 else 0

        return gross_profit / abs(max_drawdown)

    @staticmethod
    def trade_efficiency(trades: List[Dict], total_bars: int = 1) -> float:
        """
        Profit per bar held average
        Higher is better (faster profits with less time in market)
        """
        if not trades or total_bars == 0:
            return 0

        total_pnl = sum(t.get('pnl', 0) for t in trades)
        bars_held = sum(t.get('bars_held', 1) for t in trades)

        return total_pnl / bars_held if bars_held > 0 else 0

    @staticmethod
    def calculate_all_metrics(equity_curve: List[Tuple[int, float]], trades: List[Dict],
                            initial_capital: float = 100000, trading_days: int = 252) -> MetricsResult:
        """
        Calculate all metrics at once
        """
        # Returns analysis
        returns = BacktestMetrics.calculate_returns(equity_curve)
        total_return = (equity_curve[-1][1] - initial_capital) / initial_capital if equity_curve else 0
        annual_return = total_return * (trading_days / len(equity_curve)) if equity_curve else 0

        # Risk metrics
        sharpe = BacktestMetrics.sharpe_ratio(returns)
        sortino = BacktestMetrics.sortino_ratio(returns)
        max_dd, _, _ = BacktestMetrics.max_drawdown(equity_curve)
        calmar = BacktestMetrics.calmar_ratio(annual_return, max_dd)

        # Trade metrics
        profit_factor = BacktestMetrics.profit_factor(trades)
        win_rate, _, _ = BacktestMetrics.win_rate(trades)
        max_consecutive = BacktestMetrics.consecutive_losses(trades)

        # Profit metrics
        gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        recovery = BacktestMetrics.recovery_factor(gross_profit, max_dd)
        efficiency = BacktestMetrics.trade_efficiency(trades)

        return MetricsResult(
            total_return=total_return * 100,
            annual_return=annual_return * 100,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            profit_factor=profit_factor,
            win_rate=win_rate,
            max_drawdown=max_dd,
            consecutive_losses=max_consecutive,
            recovery_factor=recovery,
            trade_efficiency=efficiency
        )


class MetricsInterpreter:
    """Interpret metric results and provide insights"""

    @staticmethod
    def interpret_sortino(sortino: float) -> str:
        if sortino > 2.0:
            return "EXCELLENT (>2.0) - Outstanding risk-adjusted returns"
        elif sortino > 1.0:
            return "GOOD (>1.0) - Solid risk-adjusted performance"
        elif sortino > 0:
            return "FAIR (>0) - Positive but vulnerable to downside"
        else:
            return "POOR (≤0) - Negative after adjusting for risk"

    @staticmethod
    def interpret_profit_factor(pf: float) -> str:
        if pf > 2.0:
            return "EXCELLENT (>2.0) - Profits significantly exceed losses"
        elif pf > 1.5:
            return "GOOD (>1.5) - Solid profitability"
        elif pf > 1.0:
            return "FAIR (>1.0) - Profitable but tight margins"
        else:
            return "POOR (≤1.0) - Losing strategy"

    @staticmethod
    def interpret_calmar(calmar: float) -> str:
        if calmar > 1.0:
            return "EXCELLENT (>1.0) - Outstanding return per unit risk"
        elif calmar > 0.5:
            return "GOOD (>0.5) - Solid risk-adjusted returns"
        elif calmar > 0:
            return "FAIR (>0) - Reasonable but could be optimized"
        else:
            return "POOR (≤0) - Losses exceed drawdown recovery"

    @staticmethod
    def interpret_win_rate(win_rate: float, profit_factor: float) -> str:
        if win_rate > 55 and profit_factor > 1.5:
            return "EXCELLENT - High win rate with good payoff"
        elif win_rate > 50 and profit_factor > 1.0:
            return "GOOD - Profitable mix of winners and losers"
        elif win_rate > 45:
            return "FAIR - Below 50% but can profit with good risk management"
        else:
            return "POOR - Win rate too low to be profitable long-term"

    @staticmethod
    def get_strategy_health(metrics: MetricsResult) -> Dict[str, str]:
        """Overall health assessment of trading strategy"""
        return {
            'profitability': "PROFITABLE" if metrics.total_return > 5 else "UNPROFITABLE",
            'risk_adjusted': BacktestMetrics.interpret_sortino(metrics.sortino_ratio),
            'drawdown_management': "GOOD" if metrics.max_drawdown > -20 else "NEEDS_IMPROVEMENT",
            'consistency': "CONSISTENT" if metrics.consecutive_losses < 5 else "VOLATILE",
            'recovery': "STRONG" if metrics.recovery_factor > 2.0 else "WEAK",
            'efficiency': "FAST" if metrics.trade_efficiency > 0 else "SLOW"
        }


if __name__ == "__main__":
    # Example metrics
    sample_equity = [(0, 100000), (10, 101000), (20, 99500), (30, 103000)]
    sample_trades = [
        {'pnl': 1000, 'pnl_pct': 1.0, 'bars_held': 5},
        {'pnl': -500, 'pnl_pct': -0.5, 'bars_held': 3},
        {'pnl': 3000, 'pnl_pct': 3.0, 'bars_held': 10},
    ]

    metrics = BacktestMetrics.calculate_all_metrics(sample_equity, sample_trades,100000)
    print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
    print(f"Sortino: {metrics.sortino_ratio:.2f}")
    print(f"Calmar: {metrics.calmar_ratio:.2f}")
    print(f"Profit Factor: {metrics.profit_factor:.2f}")
