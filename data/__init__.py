"""
Data Fetching Package
Aggregates data from multiple sources
"""

from .sentiment_fetcher import SentimentFetcher, RedditSentimentOptional
from .historical_fetcher import HistoricalDataFetcher, HistoricalFetchConfig

__version__ = "1.0.0"
__all__ = [
    "SentimentFetcher",
    "RedditSentimentOptional",
    "HistoricalDataFetcher",
    "HistoricalFetchConfig",
]
