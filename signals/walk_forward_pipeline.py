"""
Walk-forward training and ranking pipeline for +10%/30-day swing outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, precision_score, recall_score


@dataclass
class WalkForwardConfig:
    min_train_rows: int = 800
    test_window_rows: int = 120
    step_rows: int = 120
    random_state: int = 42


class WalkForwardStockModel:
    """Binary model: probability of hitting +10% before stop/timeout."""

    def __init__(self, config: WalkForwardConfig | None = None):
        self.config = config or WalkForwardConfig()
        self.feature_columns: List[str] = []
        self.model = None
        self.validation_report: List[Dict] = []

    @staticmethod
    def _build_binary_target(label_series: pd.Series) -> pd.Series:
        return (label_series == 1).astype(int)

    def assemble_dataset(
        self,
        feature_map: Dict[str, pd.DataFrame],
        label_map: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        frames = []

        for ticker, fdf in feature_map.items():
            ldf = label_map.get(ticker)
            if ldf is None or fdf.empty or ldf.empty:
                continue

            merged = fdf.join(ldf[["label", "realized_return", "time_to_event"]], how="inner")
            merged["ticker"] = ticker
            merged["date"] = merged.index
            merged = merged.dropna()
            frames.append(merged)

        if not frames:
            return pd.DataFrame()

        full = pd.concat(frames).sort_values("date")
        self.feature_columns = [c for c in full.columns if c not in {"label", "realized_return", "time_to_event", "ticker", "date"}]
        return full

    def _new_model(self):
        base = RandomForestClassifier(
            n_estimators=350,
            max_depth=10,
            min_samples_leaf=10,
            random_state=self.config.random_state,
            n_jobs=-1,
            class_weight="balanced_subsample",
        )
        return CalibratedClassifierCV(base, method="sigmoid", cv=3)

    def walk_forward_train(self, dataset: pd.DataFrame) -> List[Dict]:
        if dataset.empty:
            return []

        data = dataset.sort_values("date").reset_index(drop=True)
        y_all = self._build_binary_target(data["label"])
        X_all = data[self.feature_columns]

        n = len(data)
        report: List[Dict] = []

        train_end = self.config.min_train_rows
        while train_end + self.config.test_window_rows <= n:
            test_end = train_end + self.config.test_window_rows

            X_train = X_all.iloc[:train_end]
            y_train = y_all.iloc[:train_end]
            X_test = X_all.iloc[train_end:test_end]
            y_test = y_all.iloc[train_end:test_end]

            model = self._new_model()
            model.fit(X_train, y_train)

            prob = model.predict_proba(X_test)[:, 1]
            pred = (prob >= 0.55).astype(int)

            report.append(
                {
                    "train_rows": int(len(X_train)),
                    "test_rows": int(len(X_test)),
                    "positive_rate": float(y_test.mean()) if len(y_test) else 0.0,
                    "precision": float(precision_score(y_test, pred, zero_division=0)),
                    "recall": float(recall_score(y_test, pred, zero_division=0)),
                    "brier": float(brier_score_loss(y_test, prob)) if len(y_test) else 0.0,
                }
            )

            train_end += self.config.step_rows

        self.validation_report = report

        self.model = self._new_model()
        self.model.fit(X_all, y_all)

        return report

    def rank_latest(self, feature_map: Dict[str, pd.DataFrame], min_probability: float = 0.55) -> pd.DataFrame:
        if self.model is None:
            return pd.DataFrame()

        rows = []
        for ticker, fdf in feature_map.items():
            if fdf.empty:
                continue

            latest = fdf.iloc[[-1]]
            missing_cols = [c for c in self.feature_columns if c not in latest.columns]
            if missing_cols:
                continue

            x = latest[self.feature_columns]
            p_hit = float(self.model.predict_proba(x)[0, 1])

            # Simple expectancy model for screening
            expected_return = (p_hit * 0.10) - ((1 - p_hit) * 0.05)
            score = p_hit * max(expected_return, 0)

            rows.append(
                {
                    "ticker": ticker,
                    "date": latest.index[-1],
                    "prob_hit_10pct": p_hit,
                    "expected_return": expected_return,
                    "score": score,
                }
            )

        out = pd.DataFrame(rows)
        if out.empty:
            return out

        out = out[out["prob_hit_10pct"] >= min_probability].sort_values("score", ascending=False).reset_index(drop=True)
        return out
