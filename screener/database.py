"""
Database layer for stock screening results
Caches fundamentals and tracks candidate performance
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class ScreenerDatabase:
    """SQLite database for storing candidates and tracking performance"""

    def __init__(self, db_path: str = "screener_results.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Screened candidates
        c.execute('''CREATE TABLE IF NOT EXISTS candidates
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      ticker TEXT,
                      name TEXT,
                      sector TEXT,
                      price REAL,
                      pe_ratio REAL,
                      pb_ratio REAL,
                      dividend_yield REAL,
                      valuation_score REAL,
                      growth_score REAL,
                      combined_score REAL,
                      momentum_30d REAL,
                      momentum_5d REAL,
                      UNIQUE(date, ticker))''')

        # Email alerts sent
        c.execute('''CREATE TABLE IF NOT EXISTS alerts_sent
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      top_n INTEGER,
                      candidate_count INTEGER,
                      recipients TEXT)''')

        # Performance tracking (for backtesting)
        c.execute('''CREATE TABLE IF NOT EXISTS picks_performance
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      pick_date TEXT,
                      ticker TEXT,
                      entry_price REAL,
                      entry_valuation_score REAL,
                      entry_growth_score REAL,
                      current_price REAL,
                      return_pct REAL,
                      days_held INTEGER,
                      status TEXT)''')  # status: active, closed (profit/loss)

        conn.commit()
        conn.close()

    def add_candidates(self, df: pd.DataFrame):
        """Store screening results"""
        if df.empty:
            logger.warning("No candidates to store")
            return

        conn = sqlite3.connect(self.db_path)

        date_str = datetime.now().strftime("%Y-%m-%d")

        records = []
        for _, row in df.iterrows():
            records.append((
                date_str,
                row['ticker'],
                row.get('name', ''),
                row.get('sector', ''),
                row.get('price', 0),
                row.get('pe_ratio', None),
                row.get('pb_ratio', None),
                row.get('dividend_yield', 0),
                row.get('valuation_score', 0),
                row.get('growth_score', 0),
                row.get('combined_score', 0),
                row.get('momentum_30d', 0),
                row.get('momentum_5d', 0),
            ))

        try:
            conn.executemany('''INSERT OR IGNORE INTO candidates
                              (date, ticker, name, sector, price, pe_ratio, pb_ratio,
                               dividend_yield, valuation_score, growth_score, combined_score,
                               momentum_30d, momentum_5d)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            records)
            conn.commit()
            logger.info(f"Stored {len(records)} candidates")
        except Exception as e:
            logger.error(f"Error storing candidates: {e}")
        finally:
            conn.close()

    def get_latest_candidates(self, limit: int = 50) -> pd.DataFrame:
        """Get most recent candidates"""
        conn = sqlite3.connect(self.db_path)

        query = f'''SELECT * FROM candidates
                   WHERE date = (SELECT MAX(date) FROM candidates)
                   ORDER BY combined_score DESC
                   LIMIT {limit}'''

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def get_candidates_since(self, days: int = 7) -> pd.DataFrame:
        """Get candidates from last N days"""
        conn = sqlite3.connect(self.db_path)

        query = f'''SELECT * FROM candidates
                   WHERE date >= date('now', '-{days} days')
                   ORDER BY date DESC, combined_score DESC'''

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def get_top_candidates_by_date(self, date: str = None, limit: int = 50) -> pd.DataFrame:
        """Get top candidates for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)

        query = f'''SELECT * FROM candidates
                   WHERE date = ?
                   ORDER BY combined_score DESC
                   LIMIT {limit}'''

        df = pd.read_sql_query(query, conn, params=[date])
        conn.close()

        return df

    def add_alert_sent(self, top_n: int, candidate_count: int, recipients: str):
        """Log that alert was sent"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute('''INSERT INTO alerts_sent (date, top_n, candidate_count, recipients)
                     VALUES (?, ?, ?, ?)''',
                 (date_str, top_n, candidate_count, recipients))

        conn.commit()
        conn.close()

    def get_alert_history(self, days: int = 30) -> pd.DataFrame:
        """Get history of alerts sent"""
        conn = sqlite3.connect(self.db_path)

        query = f'''SELECT * FROM alerts_sent
                   WHERE date >= datetime('now', '-{days} days')
                   ORDER BY date DESC'''

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def add_pick(self, ticker: str, entry_price: float,
                 valuation_score: float, growth_score: float):
        """Track a stock pick when we recommend it"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        pick_date = datetime.now().strftime("%Y-%m-%d")

        c.execute('''INSERT INTO picks_performance
                     (pick_date, ticker, entry_price, entry_valuation_score,
                      entry_growth_score, status)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                 (pick_date, ticker, entry_price, valuation_score, growth_score, 'active'))

        conn.commit()
        conn.close()

    def get_picks_performance(self, status: str = None) -> pd.DataFrame:
        """Get performance of past recommendations"""
        conn = sqlite3.connect(self.db_path)

        if status:
            query = f'''SELECT * FROM picks_performance WHERE status = '{status}' '''
        else:
            query = '''SELECT * FROM picks_performance'''

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def update_pick_performance(self, ticker: str, current_price: float):
        """Update current performance of a pick"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''SELECT entry_price, pick_date FROM picks_performance
                     WHERE ticker = ? AND status = 'active'
                     ORDER BY pick_date DESC LIMIT 1''',
                 (ticker,))

        row = c.fetchone()
        if row:
            entry_price, pick_date = row
            return_pct = ((current_price - entry_price) / entry_price) * 100
            days_held = (datetime.now() - datetime.strptime(pick_date, "%Y-%m-%d")).days

            c.execute('''UPDATE picks_performance
                        SET current_price = ?, return_pct = ?, days_held = ?
                        WHERE ticker = ? AND status = 'active'
                        ORDER BY pick_date DESC LIMIT 1''',
                     (current_price, return_pct, days_held, ticker))

            conn.commit()

        conn.close()

    def close_pick(self, ticker: str):
        """Mark a pick as closed"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''UPDATE picks_performance SET status = 'closed'
                     WHERE ticker = ? AND status = 'active'
                     ORDER BY pick_date DESC LIMIT 1''',
                 (ticker,))

        conn.commit()
        conn.close()

    def get_screening_statistics(self) -> Dict:
        """Get statistics on screenings"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT COUNT(DISTINCT date) FROM candidates")
        total_screenings = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM alerts_sent")
        total_alerts = c.fetchone()[0]

        picks_df = self.get_picks_performance()
        total_picks = len(picks_df)
        winning_picks = len(picks_df[picks_df['return_pct'] > 0]) if not picks_df.empty else 0
        avg_return = picks_df['return_pct'].mean() if not picks_df.empty else 0

        conn.close()

        return {
            'total_screenings': total_screenings,
            'avg_candidates_per_screening': total_candidates / max(total_screenings, 1),
            'total_alerts': total_alerts,
            'total_picks': total_picks,
            'winning_picks': winning_picks,
            'win_rate': (winning_picks / total_picks * 100) if total_picks > 0 else 0,
            'avg_return_pct': avg_return
        }
