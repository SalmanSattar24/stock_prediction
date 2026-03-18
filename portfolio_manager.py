"""
Portfolio-level risk constraints for swing trading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import yfinance as yf


@dataclass
class PortfolioRiskConfig:
    max_positions: int = 8
    max_sector_positions: int = 2
    max_position_notional_pct: float = 0.10
    max_total_notional_pct: float = 0.80


@dataclass
class PortfolioRiskManager:
    config: PortfolioRiskConfig = field(default_factory=PortfolioRiskConfig)

    def __post_init__(self):
        self._sector_cache: Dict[str, str] = {}

    def get_sector(self, ticker: str) -> str:
        if ticker in self._sector_cache:
            return self._sector_cache[ticker]

        sector = "UNKNOWN"
        try:
            info = yf.Ticker(ticker).info
            sector = (info or {}).get("sector", "UNKNOWN") or "UNKNOWN"
        except Exception:
            sector = "UNKNOWN"

        self._sector_cache[ticker] = sector
        return sector

    @staticmethod
    def compute_position_size(
        account_equity: float,
        entry_price: float,
        stop_price: float,
        risk_per_trade: float = 0.01,
        max_notional_pct: float = 0.10,
    ) -> int:
        if entry_price <= 0 or stop_price <= 0 or account_equity <= 0:
            return 0

        risk_amount = account_equity * risk_per_trade
        per_share_risk = max(entry_price - stop_price, 1e-6)
        qty_risk = int(risk_amount / per_share_risk)

        max_notional = account_equity * max_notional_pct
        qty_notional = int(max_notional / entry_price)

        return max(0, min(qty_risk, qty_notional))

    def evaluate_candidate(
        self,
        ticker: str,
        entry_price: float,
        proposed_qty: int,
        account_equity: float,
        open_positions: Dict,
    ) -> Tuple[bool, str]:
        if proposed_qty <= 0:
            return False, "invalid position size"

        if len(open_positions) >= self.config.max_positions:
            return False, "max positions reached"

        proposed_notional = proposed_qty * entry_price
        if proposed_notional > account_equity * self.config.max_position_notional_pct:
            return False, "position notional exceeds cap"

        total_notional = 0.0
        for _, pos in open_positions.items():
            qty = float(pos.get("qty", 0))
            px = float(pos.get("current_price", pos.get("avg_fill_price", 0)) or 0)
            total_notional += qty * px

        if (total_notional + proposed_notional) > account_equity * self.config.max_total_notional_pct:
            return False, "portfolio notional exceeds cap"

        sector = self.get_sector(ticker)
        if sector != "UNKNOWN":
            same_sector = 0
            for t in open_positions.keys():
                if self.get_sector(t) == sector:
                    same_sector += 1
            if same_sector >= self.config.max_sector_positions:
                return False, f"sector cap reached for {sector}"

        return True, "ok"
