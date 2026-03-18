"""
Institutional-style free swing trading pipeline (3-30 days, +10% target).

Pipeline:
1) Download/cache historical data
2) Engineer features
3) Triple-barrier labels (+10% / stop / 30 days)
4) Walk-forward model training
5) Rank latest opportunities by calibrated probability
6) Optional Alpaca paper execution with portfolio risk checks
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd
from dotenv import load_dotenv

from data.historical_fetcher import HistoricalDataFetcher
from features import FeatureEngineer
from portfolio_manager import PortfolioRiskManager
from position_manager import AutonomousPositionManager
from screener.ticker_universe import TickerUniverse
from signals.triple_barrier import TripleBarrierConfig, TripleBarrierLabeler
from signals.walk_forward_pipeline import WalkForwardStockModel


@dataclass
class InstitutionalConfig:
    universe_size: int = 300
    min_rows_per_ticker: int = 260
    min_probability: float = 0.57
    risk_per_trade: float = 0.01
    top_n_execute: int = 5


class InstitutionalSwingSystem:
    def __init__(self, config: InstitutionalConfig | None = None):
        load_dotenv()
        self.config = config or InstitutionalConfig()

        self.fetcher = HistoricalDataFetcher()
        self.fe = FeatureEngineer()
        self.labeler = TripleBarrierLabeler(TripleBarrierConfig(take_profit=0.10, stop_loss=0.05, max_holding_days=30))
        self.model = WalkForwardStockModel()
        self.risk = PortfolioRiskManager()

    def _build_feature_and_label_maps(self, tickers: List[str]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        history = self.fetcher.fetch_universe(tickers, refresh=False, min_rows=self.config.min_rows_per_ticker)
        feature_map: Dict[str, pd.DataFrame] = {}
        label_map: Dict[str, pd.DataFrame] = {}

        for ticker, ohlcv in history.items():
            features = self.fe.build_features(ohlcv)
            labels = self.labeler.label(ohlcv)

            merged_idx = features.index.intersection(labels.index)
            if len(merged_idx) < 150:
                continue

            feature_map[ticker] = features.loc[merged_idx]
            label_map[ticker] = labels.loc[merged_idx]

        return feature_map, label_map

    def train_and_rank(self, tickers: List[str] | None = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if not tickers:
            tickers = TickerUniverse.get_all_tickers()[: self.config.universe_size]

        feature_map, label_map = self._build_feature_and_label_maps(tickers)
        dataset = self.model.assemble_dataset(feature_map, label_map)

        if dataset.empty:
            return pd.DataFrame(), pd.DataFrame()

        validation = pd.DataFrame(self.model.walk_forward_train(dataset))
        ranked = self.model.rank_latest(feature_map, min_probability=self.config.min_probability)

        if not ranked.empty:
            ranked.to_csv("institutional_ranked_signals.csv", index=False)
        if not validation.empty:
            validation.to_csv("institutional_validation_report.csv", index=False)

        return ranked, validation

    def execute_paper_trades(self, ranked: pd.DataFrame, account_equity: float = 100000, dry_run: bool = True) -> List[Dict]:
        if ranked.empty:
            return []

        actions = []
        manager = None
        open_positions = {}

        if not dry_run:
            manager = AutonomousPositionManager()
            open_positions = manager.get_active_positions()

        for _, row in ranked.head(self.config.top_n_execute).iterrows():
            ticker = row["ticker"]
            p = float(row["prob_hit_10pct"])

            # Use latest close from cache as proxy entry price
            ohlcv = self.fetcher.fetch_ticker(ticker, refresh=False)
            if ohlcv.empty:
                continue

            entry = float(ohlcv["close"].iloc[-1])
            atr_pct = float(((ohlcv["high"] - ohlcv["low"]) / ohlcv["close"]).rolling(14).mean().iloc[-1] or 0.03)
            stop = entry * (1 - max(0.04, min(0.10, atr_pct * 1.5)))
            take = entry * 1.10

            qty = self.risk.compute_position_size(
                account_equity=account_equity,
                entry_price=entry,
                stop_price=stop,
                risk_per_trade=self.config.risk_per_trade,
                max_notional_pct=self.risk.config.max_position_notional_pct,
            )

            allowed, reason = self.risk.evaluate_candidate(
                ticker=ticker,
                entry_price=entry,
                proposed_qty=qty,
                account_equity=account_equity,
                open_positions=open_positions,
            )

            action = {
                "ticker": ticker,
                "probability": round(p, 4),
                "entry_price": round(entry, 4),
                "stop_loss": round(stop, 4),
                "take_profit": round(take, 4),
                "qty": int(qty),
                "allowed": allowed,
                "reason": reason,
                "executed": False,
            }

            if allowed and qty > 0 and not dry_run and manager is not None:
                ok = manager.enter_trade(
                    ticker=ticker,
                    entry_price=entry,
                    qty=int(qty),
                    stop_loss=stop,
                    take_profit=take,
                )
                action["executed"] = bool(ok)

                # track as open for subsequent risk checks in same batch
                if ok:
                    open_positions[ticker] = {
                        "qty": qty,
                        "current_price": entry,
                    }

            actions.append(action)

        pd.DataFrame(actions).to_csv("institutional_execution_plan.csv", index=False)
        return actions


def run_system(dry_run: bool = True):
    system = InstitutionalSwingSystem()

    ranked, validation = system.train_and_rank()
    if ranked.empty:
        print("No ranked signals generated. Try increasing universe_size or refreshing cache.")
        return

    print("\nTop ranked signals:")
    print(ranked.head(15).to_string(index=False))

    actions = system.execute_paper_trades(ranked, dry_run=dry_run)
    print("\nExecution plan:")
    print(pd.DataFrame(actions).head(15).to_string(index=False))


if __name__ == "__main__":
    dry_run_env = os.getenv("DRY_RUN", "true").lower()
    run_system(dry_run=dry_run_env != "false")
