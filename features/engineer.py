"""
Feature engineering for 3-30 day swing predictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass
class FeatureConfig:
    rsi_period: int = 14
    atr_period: int = 14
    vol_short: int = 5
    vol_long: int = 20


class FeatureEngineer:
    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = -delta.clip(upper=0).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                (df["high"] - df["low"]).abs(),
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return tr.rolling(period).mean()

    def build_features(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """Create model features from OHLCV."""
        if ohlcv is None or ohlcv.empty:
            return pd.DataFrame()

        df = ohlcv.copy().sort_index()

        df["ret_1d"] = df["close"].pct_change(1)
        df["ret_3d"] = df["close"].pct_change(3)
        df["ret_5d"] = df["close"].pct_change(5)
        df["ret_10d"] = df["close"].pct_change(10)
        df["ret_20d"] = df["close"].pct_change(20)

        df["sma_10"] = df["close"].rolling(10).mean()
        df["sma_20"] = df["close"].rolling(20).mean()
        df["sma_50"] = df["close"].rolling(50).mean()

        df["price_vs_sma10"] = df["close"] / df["sma_10"] - 1
        df["price_vs_sma20"] = df["close"] / df["sma_20"] - 1
        df["sma10_vs_sma50"] = df["sma_10"] / df["sma_50"] - 1

        df["vol_5d"] = df["ret_1d"].rolling(self.config.vol_short).std()
        df["vol_20d"] = df["ret_1d"].rolling(self.config.vol_long).std()
        df["vol_regime"] = df["vol_5d"] / df["vol_20d"].replace(0, np.nan)

        df["rsi_14"] = self._rsi(df["close"], self.config.rsi_period)

        df["atr_14"] = self._atr(df, self.config.atr_period)
        df["atr_pct"] = df["atr_14"] / df["close"]

        df["range_pct"] = (df["high"] - df["low"]) / df["close"]
        df["close_pos_day"] = (df["close"] - df["low"]) / (df["high"] - df["low"]).replace(0, np.nan)

        df["vol_mean_20"] = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["vol_mean_20"].replace(0, np.nan)

        feature_cols = [
            "ret_1d",
            "ret_3d",
            "ret_5d",
            "ret_10d",
            "ret_20d",
            "price_vs_sma10",
            "price_vs_sma20",
            "sma10_vs_sma50",
            "vol_5d",
            "vol_20d",
            "vol_regime",
            "rsi_14",
            "atr_pct",
            "range_pct",
            "close_pos_day",
            "volume_ratio",
        ]

        out = df[feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
        return out

    @staticmethod
    def feature_columns() -> List[str]:
        return [
            "ret_1d",
            "ret_3d",
            "ret_5d",
            "ret_10d",
            "ret_20d",
            "price_vs_sma10",
            "price_vs_sma20",
            "sma10_vs_sma50",
            "vol_5d",
            "vol_20d",
            "vol_regime",
            "rsi_14",
            "atr_pct",
            "range_pct",
            "close_pos_day",
            "volume_ratio",
        ]
