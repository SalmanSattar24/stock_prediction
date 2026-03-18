"""
Comprehensive US Stock Ticker Universe
Automatically fetches from SEC, NASDAQ, NYSE, Russell 2000, S&P 500
Falls back to cached list for speed
"""

import logging
from typing import List
import pandas as pd
import yfinance as yf
from pathlib import Path

logger = logging.getLogger(__name__)


class TickerUniverse:
    """Manage comprehensive stock ticker lists from official sources"""

    @staticmethod
    def get_cached_comprehensive_tickers() -> List[str]:
        """Load previously built comprehensive ticker list from cache"""
        cache_file = Path(__file__).parent.parent / "comprehensive_tickers.txt"
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    tickers = [line.strip() for line in f.readlines() if line.strip()]
                if len(tickers) > 100:
                    logger.info(f"Loaded {len(tickers)} cached comprehensive tickers")
                    return tickers
        except Exception as e:
            logger.warning(f"Could not load comprehensive cache: {e}")
        return []

    @staticmethod
    def fetch_comprehensive_tickers() -> List[str]:
        """
        Fetch comprehensive ticker universe from multiple official sources
        Sources:
        - SEC Edgar (all public companies)
        - S&P 500
        - NASDAQ
        - NYSE
        - Russell 2000
        """
        try:
            from screener.comprehensive_ticker_fetcher import ComprehensiveTickerFetcher
            tickers = ComprehensiveTickerFetcher.get_comprehensive_universe(validate=False)

            if len(tickers) > 100:
                logger.info(f"Fetched {len(tickers)} comprehensive tickers")
                # Save to cache for next time
                TickerUniverse.save_tickers_to_cache(tickers)
                return tickers
        except Exception as e:
            logger.warning(f"Comprehensive fetch failed: {e}")

        return []

    @staticmethod
    def save_tickers_to_cache(tickers: List[str]):
        """Save tickers to cache file"""
        cache_file = Path(__file__).parent.parent / "comprehensive_tickers.txt"
        try:
            with open(cache_file, 'w') as f:
                f.write('\n'.join(sorted(set(tickers))))
            logger.info(f"Saved {len(tickers)} tickers to cache")
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")

    @staticmethod
    def get_all_tickers() -> List[str]:
        """
        Get comprehensive stock ticker list with fallback strategy:

        Priority:
        1. Comprehensive cache (if exists and valid)
        2. Fetch from official sources (SEC, NASDAQ, NYSE, Russell, S&P 500)
        3. Fall back to hardcoded verified list

        Returns ~1000-3000+ real stocks depending on data availability
        """
        # Try comprehensive cache first
        cached = TickerUniverse.get_cached_comprehensive_tickers()
        if cached and len(cached) > 200:
            return cached

        # Try to fetch from official sources
        logger.info("No valid cache, attempting to fetch from official sources...")
        fetched = TickerUniverse.fetch_comprehensive_tickers()
        if fetched and len(fetched) > 200:
            return fetched

        # Fall back to hardcoded verified list
        logger.warning("Official source fetch failed, using hardcoded list")
        return TickerUniverse._get_fallback_tickers()

    @staticmethod
    def _get_fallback_tickers() -> List[str]:
        """Fallback list of 150+ verified real stocks"""
        return sorted([
            # Mega Cap Tech (10)
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "INTC", "AMD", "CSCO",
            # Large Cap Tech (15)
            "CRM", "ORCL", "ADBE", "INTU", "SNPS", "CDNS", "MU", "NFLX", "PYPL", "SQ",
            "ASML", "AVGO", "MSTR", "NOW", "VEEV",
            # Large Cap Healthcare (15)
            "JNJ", "UNH", "PFE", "ABBV", "LLY", "MRK", "AMGN", "ABT", "TMO", "BIIB",
            "REGN", "VRTX", "ILMN", "GILD", "ISRG",
            # Large Cap Finance (15)
            "JPM", "BAC", "WFC", "GS", "MS", "BLK", "BK", "SCHW", "IBKR", "COF",
            "AXP", "CB", "CBOE", "CME", "ICE",
            # Large Cap Energy (10)
            "XOM", "CVX", "COP", "SLB", "MPC", "PSX", "VLO", "EOG", "FANG", "EQNR",
            # Industrials (12)
            "BA", "CAT", "GE", "HON", "LMT", "NOC", "RTX", "TT", "MTR", "GDI", "ITW", "MMM",
            # Materials (10)
            "FCX", "NEM", "KL", "AU", "ABX", "STLD", "CLF", "AA", "VMC", "LPX",
            # Utilities (10)
            "NEE", "DUK", "SO", "EXC", "AEP", "XEL", "AWK", "PPL", "EVRG", "NRG",
            # REITs/Finance (15)
            "AGNC", "NRZ", "ARR", "DX", "NLY", "MFA", "TWO", "MITT", "CMO", "STAG",
            "O", "VICI", "PLD", "DLR", "EQIX",
            # Communications (10)
            "VZ", "T", "TMUS", "CHTR", "CPNG", "DIS", "FOXA", "TMDX", "VIACA", "MRVI",
            # Consumer Staples (12)
            "PG", "KO", "PEP", "MO", "PM", "EL", "CL", "GIS", "K", "CAG", "ADM", "MDLZ",
            # Consumer Discretionary (12)
            "WMT", "TGT", "COST", "MCD", "SBUX", "YUM", "NKE", "LULU", "ULTA", "DLTR",
            "FIVE", "ROST",
            # Additional Blue Chips (20)
            "TJX", "DHI", "KBH", "LEN", "PHM", "TOL", "BLDR", "RYI", "JBLU", "ALK",
            "DAL", "UAL", "CCL", "RCL", "NCLH", "BRK.B", "CHWY", "ZTS", "RH", "POOL",
        ])

    @staticmethod
    def is_valid_ticker(ticker: str) -> bool:
        """Check if ticker is in our universe"""
        all_tickers = TickerUniverse.get_all_tickers()
        return ticker.upper() in [t.upper() for t in all_tickers]
