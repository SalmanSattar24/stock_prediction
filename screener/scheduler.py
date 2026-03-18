"""
Background scheduler for continuous stock screening
Runs scanning every 4 hours, sends daily email alerts
"""

import schedule
import time
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from screener.fundamental_screener import FundamentalScreener
from screener.database import ScreenerDatabase
from screener.email_alerts import DailyAlertScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlphaDiscoveryScheduler:
    """Background scheduler for alpha discovery screening"""

    def __init__(self, gmail_address: str, recipients: List[str],
                 app_password: str = None, db_path: str = "screener_results.db"):
        """
        Initialize scheduler

        Args:
            gmail_address: Gmail address for sending alerts
            recipients: List of email recipients
            app_password: Gmail app password
            db_path: Path to SQLite database
        """
        self.gmail_address = gmail_address
        self.recipients = recipients
        self.app_password = app_password
        self.db = ScreenerDatabase(db_path)

        self.email_scheduler = DailyAlertScheduler(
            gmail_address, recipients, app_password
        )

        self.last_alert_sent = None
        self.tickers = []

    def load_tickers(self):
        """Load tickers to screen"""
        logger.info("Loading tickers...")
        self.tickers = FundamentalScreener.get_sp500_tickers()
        # Note: get_sp500_tickers() now returns comprehensive US stock universe
        # including S&P 500, NASDAQ, and other major stocks (~2000-3000 total)
        self.tickers = list(set(self.tickers))  # Remove duplicates
        logger.info(f"Loaded {len(self.tickers)} tickers")

    def run_screening(self):
        """Run screening and store results"""
        logger.info("=" * 80)
        logger.info(f"Starting screening run at {datetime.now()}")
        logger.info("=" * 80)

        if not self.tickers:
            self.load_tickers()

        try:
            # Screen stocks
            candidates_df = FundamentalScreener.screen_stocks(
                self.tickers,
                min_valuation_score=60,
                min_growth_score=40,
                min_market_cap=500_000_000
            )

            if not candidates_df.empty:
                # Add momentum
                logger.info("Calculating momentum indicators...")
                candidates_df = FundamentalScreener.enhance_with_momentum(candidates_df)

                # Store results
                self.db.add_candidates(candidates_df)

                logger.info(f"Screening complete: {len(candidates_df)} candidates found")
                logger.info(f"Top 5 candidates:")
                for idx, (_, row) in enumerate(candidates_df.head(5).iterrows(), 1):
                    logger.info(f"  {idx}. {row['ticker']:6s} - Score: {row['combined_score']:.0f} "
                               f"| P/E: {row.get('pe_ratio', 0):.1f} | P/B: {row.get('pb_ratio', 0):.2f}")
            else:
                logger.warning("No candidates found in screening")

        except Exception as e:
            logger.error(f"Screening failed: {e}", exc_info=True)

    def send_daily_alert(self):
        """Send daily email alert"""
        logger.info("Sending daily alert...")

        try:
            # Get today's candidates
            candidates = self.db.get_top_candidates_by_date(limit=50)

            if candidates.empty:
                logger.warning("No candidates to send in daily alert")
                return False

            # Send alert
            success = self.email_scheduler.send_daily_alert(candidates, top_n=20)

            if success:
                self.db.add_alert_sent(top_n=20, candidate_count=len(candidates),
                                      recipients=', '.join(self.recipients))
                self.last_alert_sent = datetime.now()
                logger.info(f"Daily alert sent to {self.recipients}")
            else:
                logger.warning("Failed to send daily alert")

            return success

        except Exception as e:
            logger.error(f"Failed to send daily alert: {e}", exc_info=True)
            return False

    def schedule_jobs(self):
        """Schedule screening and alert jobs"""
        # Run screening every 4 hours
        schedule.every(4).hours.do(self.run_screening)

        # Send alert daily at 8 AM
        schedule.every().day.at("08:00").do(self.send_daily_alert)

        logger.info("Jobs scheduled:")
        logger.info("  - Screening: Every 4 hours")
        logger.info("  - Daily alert: 08:00 AM")

    def start_background(self):
        """
        Start background scheduler loop

        This runs forever until interrupted (Ctrl+C)
        """
        logger.info("Starting Alpha Discovery Scheduler")
        logger.info("Press Ctrl+C to stop")

        self.load_tickers()
        self.schedule_jobs()

        # Run one screening immediately
        self.run_screening()

        # Then start scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if a job needs to run
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

    def show_status(self):
        """Show current screening status"""
        stats = self.db.get_screening_statistics()

        logger.info("=" * 80)
        logger.info("ALPHA DISCOVERY SYSTEM STATUS")
        logger.info("=" * 80)
        logger.info(f"Total screenings run:        {stats['total_screenings']}")
        logger.info(f"Avg candidates per scan:     {stats['avg_candidates_per_screening']:.0f}")
        logger.info(f"Total alerts sent:           {stats['total_alerts']}")
        logger.info(f"Total recommendations:       {stats['total_picks']}")
        logger.info(f"Winning recommendations:     {stats['winning_picks']}")
        logger.info(f"Win rate:                    {stats['win_rate']:.1f}%")
        logger.info(f"Average return:              {stats['avg_return_pct']:.2f}%")
        logger.info("=" * 80)

        # Show latest candidates
        logger.info("\nLatest Top 10 Candidates:")
        latest = self.db.get_latest_candidates(limit=10)
        if not latest.empty:
            for idx, (_, row) in enumerate(latest.iterrows(), 1):
                logger.info(f"  {idx:2d}. {row['ticker']:6s} - "
                           f"Score: {row['combined_score']:6.0f} | "
                           f"P/E: {row['pe_ratio']:6.1f} | "
                           f"Div Yield: {row['dividend_yield']:5.2f}% | "
                           f"30d Mom: {row['momentum_30d']:6.1f}%")
        else:
            logger.info("  No candidates yet")
