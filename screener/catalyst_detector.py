"""
Optimized Catalyst Detector with Rate Limiting
Identifies near-term catalysts while respecting API rate limits
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import time

logging.disable(logging.WARNING)

class EnhancedCatalystDetector:
    """Detect catalysts using multiple APIs with rate limiting"""

    def __init__(self):
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.alphavantage_key = os.getenv('ALPHAVANTAGE_KEY')
        self.eodhd_key = os.getenv('EODHD_KEY')

        self.finnhub_url = "https://finnhub.io/api/v1"
        self.newsapi_url = "https://newsapi.org/v2"
        self.alphavantage_url = "https://www.alphavantage.co/query"
        self.eodhd_url = "https://eodhd.com/api"

        # Rate limiting tracking
        self.request_count = 0
        self.rate_limit_pause = 0.2  # 200ms between requests

    def _throttle_request(self):
        """Add delay between API requests to respect rate limits"""
        time.sleep(self.rate_limit_pause)

    def _safe_request(self, url: str, params: dict, timeout: int = 5) -> dict:
        """Make API request with error handling and rate limiting"""
        self._throttle_request()
        self.request_count += 1

        try:
            response = requests.get(url, params=params, timeout=timeout)

            if response.status_code == 429:  # Rate limited
                return {'error': 'rate_limited'}
            elif response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    def get_newsapi_sentiment(self, ticker: str, days: int = 7) -> Dict:
        """Get news sentiment from NewsAPI (with caching logic)"""
        if not self.newsapi_key:
            return {'news_count': 0}

        params = {
            'q': ticker,
            'sortBy': 'publishedAt',
            'language': 'en',
            'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
            'apiKey': self.newsapi_key
        }

        url = f"{self.newsapi_url}/everything"
        data = self._safe_request(url, params, timeout=10)

        if data.get('error') == 'rate_limited':
            return {'news_count': 0}

        articles = data.get('articles', [])

        if len(articles) > 10:
            return {
                'news_count': len(articles),
                'catalyst_type': 'High News Volume',
                'catalyst_strength': min(0.85, len(articles) / 20)
            }
        elif len(articles) > 3:
            return {
                'news_count': len(articles),
                'catalyst_type': 'News Coverage',
                'catalyst_strength': 0.5
            }

        return {'news_count': 0}

    def get_alphavantage_earnings(self, ticker: str) -> Dict:
        """Get earnings data from AlphaVantage (skip on rate limit)"""
        if not self.alphavantage_key:
            return {}

        params = {
            'function': 'EARNINGS',
            'symbol': ticker,
            'apikey': self.alphavantage_key
        }

        data = self._safe_request(self.alphavantage_url, params, timeout=10)

        if data.get('error') == 'rate_limited':
            return {}

        if 'quarterlyEarnings' in data:
            earnings = data['quarterlyEarnings'][0]
            report_date = earnings.get('reportedDate', '')

            if report_date:
                try:
                    days_until = (datetime.strptime(report_date, '%Y-%m-%d') - datetime.now()).days

                    if 0 <= days_until <= 30:
                        return {
                            'catalyst_type': 'Upcoming Earnings',
                            'days_until': days_until,
                            'catalyst_strength': 0.9 if days_until <= 14 else 0.6,
                            'report_date': report_date
                        }
                except:
                    pass

        return {}

    def get_eodhd_earnings(self, ticker: str) -> Dict:
        """Get earnings calendar from EODHD (skip on rate limit)"""
        if not self.eodhd_key:
            return {}

        params = {
            'symbols': ticker,
            'api_token': self.eodhd_key
        }

        url = f"{self.eodhd_url}/calendar/earnings"
        data = self._safe_request(url, params, timeout=10)

        if data.get('error') == 'rate_limited':
            return {}

        if isinstance(data, list) and len(data) > 0:
            event = data[0]
            event_date = event.get('report_date', '')

            if event_date:
                try:
                    days_until = (datetime.strptime(event_date, '%Y-%m-%d') - datetime.now()).days

                    if 0 <= days_until <= 30:
                        return {
                            'catalyst_type': 'Earnings Report',
                            'days_until': days_until,
                            'catalyst_strength': 0.85,
                            'report_date': event_date
                        }
                except:
                    pass

        return {}

    def analyze_catalyst_fast(self, ticker: str) -> Dict:
        """Quick catalyst analysis (skip earnings on rate limit)"""
        result = {
            'ticker': ticker,
            'catalysts': [],
            'catalyst_score': 0,
            'risk_level': 'low'
        }

        # Check NewsAPI
        news = self.get_newsapi_sentiment(ticker)
        if news.get('news_count', 0) > 0 and news.get('error') != 'rate_limited':
            result['catalysts'].append(news)
            result['catalyst_score'] += news.get('catalyst_strength', 0) * 100

        # Only check earnings if we haven't hit rate limits
        if self.request_count < 100:  # Limit catalyst API calls
            av = self.get_alphavantage_earnings(ticker)
            if av:
                result['catalysts'].append(av)
                result['catalyst_score'] += av.get('catalyst_strength', 0) * 100

        # Normalize score
        result['catalyst_score'] = min(100, result['catalyst_score'])

        return result

    def screen_for_catalysts_fast(self, tickers: List[str], max_checks: int = 100) -> List[Dict]:
        """Screen top tickers only (not all) to respect rate limits"""
        candidates = []
        processed = 0
        checks_done = 0

        print("\n" + "="*80)
        print("CATALYST DETECTOR - Selective screening (top momentum only)")
        print("="*80)
        print(f"Scanning {min(len(tickers), max_checks)} top stocks for catalysts...\n")

        # Only check top N tickers to avoid rate limits
        for ticker in tickers[:max_checks]:
            if processed % 25 == 0 and processed > 0:
                print(f"Progress: {processed}/{min(len(tickers), max_checks)} - Found {len(candidates)}")

            try:
                result = self.analyze_catalyst_fast(ticker)

                if result['catalysts'] and result['catalyst_score'] > 20:
                    candidates.append(result)

                checks_done += 1
            except:
                pass

            processed += 1

        candidates.sort(key=lambda x: x['catalyst_score'], reverse=True)

        print(f"\n" + "="*80)
        print(f"CATALYST SCAN COMPLETE")
        print(f"Checked: {checks_done}")
        print(f"With catalysts: {len(candidates)}")
        print(f"API requests made: {self.request_count}")
        print("="*80)

        return candidates
