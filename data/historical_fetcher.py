"""
Historical market data fetcher with local caching.
Uses free Yahoo Finance data and stores normalized OHLCV data for model training.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd
import yfinance as yf


@dataclass
class HistoricalFetchConfig:
    cache_dir: str = "market_cache"
    period: str = "3y"
    interval: str = "1d"
    auto_adjust: bool = True


class HistoricalDataFetcher:
    """Fetches and caches OHLCV data for a ticker universe."""

    def __init__(self, config: Optional[HistoricalFetchConfig] = None):
        self.config = config or HistoricalFetchConfig()
        self.cache_path = Path(self.config.cache_dir)
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def _file_path(self, ticker: str) -> Path:
        safe_ticker = ticker.replace("/", "_").replace(".", "_")
        return self.cache_path / f"{safe_ticker}_{self.config.interval}.csv"

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()

        data = df.copy()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]

        data = data.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )

        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in data.columns:
                data[col] = pd.NA

        data = data[required].dropna()
        data.index = pd.to_datetime(data.index)
        data = data[~data.index.duplicated(keep="last")]
        data = data.sort_index()
        return data

    def fetch_ticker(self, ticker: str, refresh: bool = False) -> pd.DataFrame:
        """Fetch one ticker from cache or Yahoo Finance."""
        file_path = self._file_path(ticker)

        if file_path.exists() and not refresh:
            cached = pd.read_csv(file_path, index_col=0, parse_dates=True)
            if not cached.empty:
                return cached

        df = yf.download(
            ticker,
            period=self.config.period,
            interval=self.config.interval,
            auto_adjust=self.config.auto_adjust,
            progress=False,
            threads=False,
        )
        data = self._normalize(df)

        if not data.empty:
            data.to_csv(file_path)

        return data

    def fetch_universe(
        self,
        tickers: Iterable[str],
        refresh: bool = False,
        min_rows: int = 200,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch and return validated historical data for many tickers."""
        result: Dict[str, pd.DataFrame] = {}

        for ticker in tickers:
            try:
                df = self.fetch_ticker(ticker, refresh=refresh)
                if len(df) >= min_rows:
                    result[ticker] = df
            except Exception:
                continue

        return result
