# config/trading_hours.py
# AKUFIN - Intelligence for Wealth Accrual
# Complete Trading Session Management
from datetime import datetime
import pytz
from monitoring.logger import get_logger

logger = get_logger(__name__)
eastern = pytz.timezone("US/Eastern")


def get_current_session() -> str:
    """
    Returns current market session.
    AKUFIN uses all 3 sessions differently.
    """
    now = datetime.now(eastern)

    if now.weekday() >= 5:
        return "WEEKEND"

    hour = now.hour
    minute = now.minute
    time_decimal = hour + minute / 60

    if 4.0 <= time_decimal < 9.5:
        return "PRE_MARKET"
    elif 9.5 <= time_decimal < 9.583:
        return "OPENING_BELL"
    elif 9.583 <= time_decimal < 12.0:
        return "MORNING_SESSION"
    elif 12.0 <= time_decimal < 14.0:
        return "LUNCH_LULL"
    elif 14.0 <= time_decimal < 16.0:
        return "AFTERNOON_SESSION"
    elif 16.0 <= time_decimal < 20.0:
        return "AFTER_HOURS"
    else:
        return "MARKET_CLOSED"


def is_market_open() -> bool:
    """Regular session only 9:30 AM - 4:00 PM"""
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    hour = now.hour
    minute = now.minute
    time_decimal = hour + minute / 60
    return 9.5 <= time_decimal < 16.0


def is_pre_market() -> bool:
    """Pre-market 4:00 AM - 9:30 AM"""
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    hour = now.hour
    minute = now.minute
    time_decimal = hour + minute / 60
    return 4.0 <= time_decimal < 9.5


def is_after_hours() -> bool:
    """After-hours 4:00 PM - 8:00 PM"""
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    hour = now.hour
    minute = now.minute
    time_decimal = hour + minute / 60
    return 16.0 <= time_decimal < 20.0


def is_tradeable() -> bool:
    """
    Can we execute trades right now?
    Regular + Extended hours = Yes
    Pre-market after 4 AM = Yes (with caution)
    After-hours = Yes (with caution)
    Weekend = No
    """
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    hour = now.hour
    minute = now.minute
    time_decimal = hour + minute / 60
    return 4.0 <= time_decimal < 20.0


def is_safe_to_trade() -> bool:
    """
    Safe trading window only.
    Avoids opening chaos and pre/after volatility.
    9:35 AM - 3:55 PM only.
    """
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    hour = now.hour
    minute = now.minute
    time_decimal = hour + minute / 60
    return 9.583 <= time_decimal < 15.917


def get_session_strategy(session: str) -> dict:
    """
    Returns what AKUFIN should do in each session.
    """
    strategies = {
        "PRE_MARKET": {
            "scan": True,
            "execute": False,
            "strategy": "SCAN_ONLY",
            "description": "Scan for gaps and news",
            "risk_level": "HIGH",
            "akufin_action": (
                "Scan watchlist for gaps. "
                "Prepare signals for market open. "
                "No execution yet."
            )
        },
        "OPENING_BELL": {
            "scan": True,
            "execute": False,
            "strategy": "WAIT",
            "description": "Wait for chaos to settle",
            "risk_level": "EXTREME",
            "akufin_action": (
                "Market just opened. "
                "Waiting 5 minutes for chaos to settle. "
                "Do not trade opening bell."
            )
        },
        "MORNING_SESSION": {
            "scan": True,
            "execute": True,
            "strategy": "SNIPER_ACTIVE",
            "description": "Best time for SNIPER trades",
            "risk_level": "MEDIUM",
            "akufin_action": (
                "Primary SNIPER window. "
                "High volume, good spreads. "
                "Execute momentum trades."
            )
        },
        "LUNCH_LULL": {
            "scan": True,
            "execute": False,
            "strategy": "REDUCE",
            "description": "Low volume lunch period",
            "risk_level": "MEDIUM",
            "akufin_action": (
                "Volume drops at lunch. "
                "Avoid new entries. "
                "Manage existing positions only."
            )
        },
        "AFTERNOON_SESSION": {
            "scan": True,
            "execute": True,
            "strategy": "BOTH_ACTIVE",
            "description": "Good for both portfolios",
            "risk_level": "MEDIUM",
            "akufin_action": (
                "Strong afternoon session. "
                "Both SNIPER and FORTRESS trades. "
                "Watch for power hour momentum."
            )
        },
        "AFTER_HOURS": {
            "scan": True,
            "execute": True,
            "strategy": "EARNINGS_ONLY",
            "description": "Earnings and news trades",
            "risk_level": "HIGH",
            "akufin_action": (
                "After-hours active. "
                "EARNINGS plays only. "
                "Wide spreads - use limit orders. "
                "FORTRESS positions only."
            )
        },
        "MARKET_CLOSED": {
            "scan": False,
            "execute": False,
            "strategy": "CLOSED",
            "description": "Market closed",
            "risk_level": "N/A",
            "akufin_action": (
                "Market closed. "
                "Running analysis for tomorrow. "
                "Preparing watchlist."
            )
        },
        "WEEKEND": {
            "scan": False,
            "execute": False,
            "strategy": "CLOSED",
            "description": "Weekend",
            "risk_level": "N/A",
            "akufin_action": (
                "Weekend. Market closed. "
                "Review weekly performance. "
                "Plan next week strategy."
            )
        }
    }
    return strategies.get(
        session,
        strategies["MARKET_CLOSED"]
    )


def get_current_market_session() -> str:
    """Alias for backward compatibility"""
    return get_current_session()