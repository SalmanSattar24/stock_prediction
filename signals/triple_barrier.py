"""
Triple-barrier labeling for 3-30 day swing outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class TripleBarrierConfig:
    take_profit: float = 0.10
    stop_loss: float = 0.05
    max_holding_days: int = 30


class TripleBarrierLabeler:
    def __init__(self, config: TripleBarrierConfig | None = None):
        self.config = config or TripleBarrierConfig()

    def label(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        if ohlcv is None or ohlcv.empty:
            return pd.DataFrame()

        close = ohlcv["close"].astype(float).values
        n = len(close)

        labels = np.zeros(n, dtype=int)
        time_to_event = np.full(n, np.nan)
        realized_return = np.full(n, np.nan)
        hit_type = np.array(["none"] * n, dtype=object)

        for i in range(n - 1):
            entry = close[i]
            if entry <= 0:
                continue

            tp = entry * (1 + self.config.take_profit)
            sl = entry * (1 - self.config.stop_loss)
            end_idx = min(n - 1, i + self.config.max_holding_days)

            future = close[i + 1 : end_idx + 1]
            if future.size == 0:
                continue

            up_hits = np.where(future >= tp)[0]
            dn_hits = np.where(future <= sl)[0]

            first_up = up_hits[0] if up_hits.size > 0 else np.inf
            first_dn = dn_hits[0] if dn_hits.size > 0 else np.inf

            if first_up < first_dn:
                j = i + 1 + int(first_up)
                labels[i] = 1
                hit_type[i] = "take_profit"
            elif first_dn < first_up:
                j = i + 1 + int(first_dn)
                labels[i] = -1
                hit_type[i] = "stop_loss"
            else:
                j = end_idx
                labels[i] = 0
                hit_type[i] = "timeout"

            time_to_event[i] = j - i
            realized_return[i] = (close[j] / entry) - 1

        result = pd.DataFrame(
            {
                "label": labels,
                "time_to_event": time_to_event,
                "realized_return": realized_return,
                "hit_type": hit_type,
            },
            index=ohlcv.index,
        )

        return result
