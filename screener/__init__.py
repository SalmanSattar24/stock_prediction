"""
Explosive Move Stock Screener Package
"""

from .database import ScreenerDatabase
from .email_alerts import EmailAlerter

__version__ = "2.0.0"
__all__ = [
    "ScreenerDatabase",
    "EmailAlerter"
]
