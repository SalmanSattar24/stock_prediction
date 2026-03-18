"""
Email alerter for sending daily screening results
Uses Gmail SMTP with app-specific password
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from datetime import datetime
from typing import List, Dict
import logging
import os

logger = logging.getLogger(__name__)


class EmailAlerter:
    """Send email alerts with screening results"""

    def __init__(self, gmail_address: str, app_password: str = None):
        """
        Initialize email alerter

        Args:
            gmail_address: Gmail address to send from
            app_password: Gmail app-specific password (see: https://myaccount.google.com/apppasswords)
                         If None, will look for GMAIL_APP_PASSWORD env variable
        """
        self.gmail_address = gmail_address

        # Get password from parameter or environment variable
        if app_password:
            self.app_password = app_password
        else:
            self.app_password = os.getenv('GMAIL_APP_PASSWORD', '')
            if not self.app_password:
                logger.warning("No Gmail app password provided. Email alerts will fail.")

    def send_alert(self, recipients: List[str], subject: str, html_content: str) -> bool:
        """
        Send email alert

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            html_content: HTML content for email body

        Returns:
            bool: True if sent successfully
        """
        if not self.app_password:
            logger.error("Gmail app password not configured. Set GMAIL_APP_PASSWORD env variable.")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.gmail_address
            msg['To'] = ', '.join(recipients)

            # Attach HTML
            part = MIMEText(html_content, 'html')
            msg.attach(part)

            # Send
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_address, self.app_password)
                server.sendmail(self.gmail_address, recipients, msg.as_string())

            logger.info(f"Email sent to {recipients}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def format_candidates_html(self, df: pd.DataFrame, title: str = "Alpha Discovery - Daily Picks",
                               top_n: int = 20) -> str:
        """
        Format screening results as HTML email

        Args:
            df: DataFrame with candidates
            title: Email title
            top_n: Number of candidates to include

        Returns:
            HTML string
        """
        if df.empty:
            return f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2>{title}</h2>
                    <p>No candidates found matching criteria.</p>
                    <p><small>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                </body>
            </html>
            """

        # Take top N
        df = df.head(top_n).copy()

        # Format table
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h2 {{ color: #1f77b4; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th {{ background-color: #1f77b4; color: white; padding: 10px; text-align: left; }}
                    td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .positive {{ color: green; font-weight: bold; }}
                    .negative {{ color: red; }}
                    .score {{ background-color: #e8f4f8; padding: 2px 6px; border-radius: 3px; }}
                    .metric {{ font-size: 12px; }}
                    .footer {{ margin-top: 30px; font-size: 11px; color: #666; }}
                </style>
            </head>
            <body>
                <h2>{title}</h2>
                <p>Top {min(top_n, len(df))} undervalued candidates as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Ticker</th>
                            <th>Company</th>
                            <th>Sector</th>
                            <th>Price</th>
                            <th>P/E</th>
                            <th>P/B</th>
                            <th>Div Yield</th>
                            <th>Val Score</th>
                            <th>Growth Score</th>
                            <th>Combined</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for idx, (_, row) in enumerate(df.iterrows(), 1):
            combined_score = row.get('combined_score', 0)
            combined_color = '#28a745' if combined_score > 75 else '#ffc107' if combined_score > 60 else '#666'

            pe_str = f"{row.get('pe_ratio', 0):.1f}" if row.get('pe_ratio') else "N/A"
            pb_str = f"{row.get('pb_ratio', 0):.2f}" if row.get('pb_ratio') else "N/A"
            div_str = f"{row.get('dividend_yield', 0)*100:.1f}%" if row.get('dividend_yield') else "0%"

            html += f"""
                        <tr>
                            <td><strong>{idx}</strong></td>
                            <td><strong>{row['ticker']}</strong></td>
                            <td><small>{row.get('name', '')[:30]}</small></td>
                            <td><small>{row.get('sector', 'N/A')}</small></td>
                            <td>${row.get('price', 0):.2f}</td>
                            <td class="metric">{pe_str}</td>
                            <td class="metric">{pb_str}</td>
                            <td class="metric">{div_str}</td>
                            <td><span class="score">{row.get('valuation_score', 0):.0f}</span></td>
                            <td><span class="score">{row.get('growth_score', 0):.0f}</span></td>
                            <td style="color: white; background-color: {combined_color}; padding: 5px; border-radius: 3px;">
                                <strong>{combined_score:.0f}</strong>
                            </td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>

                <div class="footer">
                    <h4>How to interpret:</h4>
                    <ul>
                        <li><strong>Val Score:</strong> Valuation attractiveness (0-100). Higher = cheaper relative to earnings/assets</li>
                        <li><strong>Growth Score:</strong> Growth/quality (0-100). Higher = better earnings/revenue growth, lower debt</li>
                        <li><strong>Combined:</strong> Weighted score (60% valuation, 40% growth). >75 = strong candidate</li>
                        <li><strong>P/E:</strong> Price-to-Earnings ratio. Lower is typically cheaper</li>
                        <li><strong>P/B:</strong> Price-to-Book ratio. <1.5 indicates value</li>
                    </ul>

                    <h4>Disclaimer:</h4>
                    <p>This is an automated stock screener showing statistical undervaluation. Not financial advice.
                    Always do your own research before investing. Past performance ≠ future results.</p>

                    <p>
                        <small>
                            Generated by Alpha Discovery System<br>
                            Next scan: 4 hours from {datetime.now().strftime('%H:%M:%S')}
                        </small>
                    </p>
                </div>
            </body>
        </html>
        """

        return html

    @staticmethod
    def setup_gmail_password():
        """
        Helper to guide user through Gmail app password setup

        Steps:
        1. Go to https://myaccount.google.com/apppasswords
        2. Select "Mail" and "Windows Computer"
        3. Copy the password shown
        4. Set environment variable or pass to EmailAlerter
        """
        instructions = """
        ====== SETUP GMAIL APP PASSWORD ======

        To use email alerts, you need a Gmail app-specific password (not your actual password):

        1. Go to: https://myaccount.google.com/apppasswords
        2. You may need to enable 2-factor authentication first
        3. Select "Mail" and "Windows Computer"
        4. Google will show a 16-character password
        5. Copy that password

        Then set it as an environment variable:
        Windows (Command Prompt):
            set GMAIL_APP_PASSWORD=your_16_char_password

        Or in Python:
            import os
            os.environ['GMAIL_APP_PASSWORD'] = 'your_16_char_password'

        =====================================
        """
        print(instructions)

        return input("Enter your Gmail app password: ").strip()


class DailyAlertScheduler:
    """Schedule and send daily email alerts"""

    def __init__(self, gmail_address: str, recipients: List[str], app_password: str = None):
        """
        Initialize scheduler

        Args:
            gmail_address: Gmail to send from
            recipients: Email addresses to send to
            app_password: Gmail app password
        """
        self.alerter = EmailAlerter(gmail_address, app_password)
        self.recipients = recipients

    def send_daily_alert(self, candidates_df: pd.DataFrame, top_n: int = 20) -> bool:
        """
        Send daily alert with top candidates

        Args:
            candidates_df: DataFrame with screened candidates
            top_n: Number of candidates to include

        Returns:
            bool: True if sent successfully
        """
        subject = f"Alpha Discovery - Daily Picks ({datetime.now().strftime('%Y-%m-%d')})"
        html = self.alerter.format_candidates_html(candidates_df, top_n=top_n)

        return self.alerter.send_alert(self.recipients, subject, html)
