"""
Backtesting Engine Package
Complete toolkit for testing trading strategies
"""

from .engine import BacktestingEngine, BacktestConfig, Position, TradeRecord
from .metrics import BacktestMetrics, MetricsResult, MetricsInterpreter
from .position_sizing import PositionSizer

__version__ = "1.0.0"
__all__ = [
    "BacktestingEngine",
    "BacktestConfig",
    "Position",
    "TradeRecord",
    "BacktestMetrics",
    "MetricsResult",
    "MetricsInterpreter",
    "PositionSizer"
]
