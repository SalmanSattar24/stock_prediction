"""
Advanced Signal Generation Package
Multi-timeframe, regime-aware, confidence-scored trade signals
ML-based predictions with ensemble voting
"""

from .technical_signals import TechnicalSignals
from .regime_detection import RegimeDetector, MarketRegime
from .multi_timeframe_signals import MultiTimeframeSignals
from .ml_signals import MLSignalGenerator, WalkForwardValidator

__version__ = "1.0.0"
__all__ = [
    "TechnicalSignals",
    "RegimeDetector",
    "MarketRegime",
    "MultiTimeframeSignals",
    "MLSignalGenerator",
    "WalkForwardValidator"
]
