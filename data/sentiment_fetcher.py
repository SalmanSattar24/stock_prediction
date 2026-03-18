"""
Sentiment Analysis Data Fetcher
Aggregates sentiment from News, Reddit, and other sources
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time


class SentimentFetcher:
    """Fetch and analyze sentiment from multiple sources"""

    def __init__(self):
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.request_delay = 0.2
        self.newsapi_url = "https://newsapi.org/v2"

    def get_newsapi_sentiment(self, ticker: str, days: int = 7) -> Dict:
        """
        Get sentiment from financial news
        """
        if not self.newsapi_key:
            return {'status': 'error', 'message': 'NEWSAPI_KEY not set'}

        try:
            time.sleep(self.request_delay)

            params = {
                'q': ticker,
                'sortBy': 'publishedAt',
                'language': 'en',
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'apiKey': self.newsapi_key
            }

            url = f"{self.newsapi_url}/everything"
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])

                # Analyze sentiment from headlines
                sentiment_scores = []
                for article in articles[:30]:  # Process top 30
                    headline = article.get('title', '')
                    description = article.get('description', '')
                    source = article.get('source', {}).get('name', 'Unknown')

                    # Simple sentiment scoring from keywords
                    score = self._score_sentiment(headline + ' ' + description)
                    sentiment_scores.append(score)

                return {
                    'status': 'success',
                    'ticker': ticker,
                    'article_count': len(articles),
                    'avg_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                    'sentiment_scores': sentiment_scores,
                    'dominant_sentiment': 'POSITIVE' if sum(sentiment_scores) > 0 else ('NEGATIVE' if sum(sentiment_scores) < 0 else 'NEUTRAL'),
                    'source': 'NewsAPI',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'status': 'error', 'code': response.status_code}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _score_sentiment(self, text: str) -> float:
        """
        Simple sentiment scoring based on keywords
        Range: -1.0 (very negative) to 1.0 (very positive)
        """
        text = text.lower()

        positive_keywords = [
            'surge', 'jump', 'rally', 'bull', 'bullish', 'up', 'gain', 'profit',
            'soar', 'spike', 'breakout', 'upgrade', 'beat', 'strong', 'recovery',
            'momentum', 'boom', 'explosive', 'outperform', 'excellent', 'positive'
        ]

        negative_keywords = [
            'drop', 'fall', 'crash', 'bear', 'bearish', 'down', 'loss', 'plunge',
            'decline', 'downgrade', 'miss', 'weak', 'collapse', 'concern', 'risk',
            'trouble', 'negative', 'tumble', 'below', 'underperform'
        ]

        positive_count = sum(text.count(keyword) for keyword in positive_keywords)
        negative_count = sum(text.count(keyword) for keyword in negative_keywords)

        # Normalize to -1 to 1
        total = positive_count + negative_count
        if total == 0:
            return 0

        return (positive_count - negative_count) / total

    def get_reddit_sentiment_estimate(self, ticker: str) -> Dict:
        """
        Estimate Reddit sentiment (without API keys)
        In production, would use PRAW library with Reddit credentials

        Instructions for full implementation:
        1. Install: pip install praw
        2. Get Reddit API keys: https://www.reddit.com/prefs/apps
        3. Use PRAW to fetch r/wallstreetbets, r/investing, r/stocks posts
        4. Analyze sentiment and mention volume
        """
        return {
            'status': 'awaiting_setup',
            'ticker': ticker,
            'message': 'Reddit sentiment requires API setup',
            'setup_instructions': [
                '1. Install PRAW: pip install praw',
                '2. Create Reddit app: https://www.reddit.com/prefs/apps',
                '3. Set environment variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT',
                '4. Use fully_qualified implementation below'
            ],
            'implementation': 'See reddit_sentiment_full.py'
        }

    def aggregate_sentiment(self, ticker: str, include_reddit: bool = False) -> Dict:
        """
        Aggregate sentiment from all available sources
        """
        aggregated = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }

        # Get NewsAPI sentiment
        news_sentiment = self.get_newsapi_sentiment(ticker)
        if news_sentiment.get('status') == 'success':
            aggregated['sources']['newsapi'] = news_sentiment
            aggregated['newsapi_score'] = news_sentiment.get('avg_sentiment', 0)
            aggregated['newsapi_articles'] = news_sentiment.get('article_count', 0)

        # Get Reddit estimate (if include_reddit=True)
        if include_reddit:
            reddit_sentiment = self.get_reddit_sentiment_estimate(ticker)
            aggregated['sources']['reddit_estimate'] = reddit_sentiment

        # Calculate weighted average sentiment
        sentiment_values = [
            aggregated.get('newsapi_score', 0)  # NewsAPI contribution
        ]
        weights = [1.0]

        aggregate_score = sum(s * w for s, w in zip(sentiment_values, weights)) / sum(weights) if weights else 0
        aggregated['aggregate_sentiment'] = aggregate_score

        # Classify overall sentiment
        if aggregate_score > 0.2:
            aggregated['overall_sentiment'] = 'POSITIVE'
        elif aggregate_score < -0.2:
            aggregated['overall_sentiment'] = 'NEGATIVE'
        else:
            aggregated['overall_sentiment'] = 'NEUTRAL'

        return aggregated


class RedditSentimentOptional:
    """
    Full Reddit sentiment implementation
    Requires PRAW library and Reddit API credentials
    """

    def __init__(self):
        """Initialize Reddit API (requires credentials in environment)"""
        try:
            import praw
            self.praw = praw
            self.reddit = None
            self._initialize_reddit()
        except ImportError:
            self.praw = None
            self.reddit = None
            print("PRAW not installed. Install with: pip install praw")

    def _initialize_reddit(self):
        """Initialize Reddit API connection"""
        if not self.praw:
            return

        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'StockScreener/1.0')

            if not client_id or not client_secret:
                print("Missing Reddit credentials: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET")
                return

            self.reddit = self.praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
        except Exception as e:
            print(f"Failed to initialize Reddit API: {e}")

    def get_subreddit_sentiment(self, ticker: str, subreddit_names: List[str] = None,
                               limit: int = 50) -> Dict:
        """
        Get sentiment from Reddit subreddits
        """
        if not self.reddit:
            return {'status': 'error', 'message': 'Reddit API not initialized'}

        if not subreddit_names:
            subreddit_names = ['wallstreetbets', 'investing', 'stocks', 'cryptocurrency']

        results = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'subreddits': {}
        }

        try:
            for sub_name in subreddit_names:
                try:
                    subreddit = self.reddit.subreddit(sub_name)
                    posts = list(subreddit.search(f'{ticker}', time_filter='day', limit=limit))

                    if not posts:
                        continue

                    # Analyze posts
                    total_score = sum(p.score for p in posts)
                    avg_score = total_score / len(posts) if posts else 0
                    mentions = len(posts)

                    # Sentiment from titles
                    sentiments = []
                    for post in posts:
                        sentiment = self._analyze_text_sentiment(post.title)
                        sentiments.append(sentiment)

                    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

                    results['subreddits'][sub_name] = {
                        'mentions': mentions,
                        'avg_upvotes': avg_score,
                        'avg_sentiment': avg_sentiment,
                        'sentiment_label': 'POSITIVE' if avg_sentiment > 0.1 else ('NEGATIVE' if avg_sentiment < -0.1 else 'NEUTRAL')
                    }

                except Exception as e:
                    results['subreddits'][sub_name] = {'error': str(e)}

            # Aggregate
            overall_sentiment = sum(
                r.get('avg_sentiment', 0) for r in results['subreddits'].values()
            ) / len(results['subreddits']) if results['subreddits'] else 0

            results['overall_sentiment'] = overall_sentiment
            results['status'] = 'success'

            return results

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of a text string"""
        # Simple keyword-based sentiment (in production, use VADER or transformer models)
        positive = ['bull', 'buy', 'long', 'gain', 'moon', 'to the moon', 'lambo', 'squeeze']
        negative = ['bear', 'sell', 'short', 'loss', 'crash', 'dump', 'bearish']

        text_lower = text.lower()
        pos_count = sum(text_lower.count(word) for word in positive)
        neg_count = sum(text_lower.count(word) for word in negative)

        total = pos_count + neg_count
        if total == 0:
            return 0

        return (pos_count - neg_count) / total


if __name__ == "__main__":
    fetcher = SentimentFetcher()

    # Test NewsAPI sentiment
    sentiment = fetcher.aggregate_sentiment('APPLE', include_reddit=False)
    print(f"Sentiment for APPLE:")
    print(f"  Overall: {sentiment.get('overall_sentiment')}")
    print(f"  Score: {sentiment.get('aggregate_sentiment', 0):.2f}")
    print(f"  Articles: {sentiment.get('newsapi_articles', 0)}")

    # For Reddit setup:
    print("\nReddit Setup Instructions:")
    reddit_example = RedditSentimentOptional()
    print(reddit_example.get_subreddit_sentiment('NVDA'))
