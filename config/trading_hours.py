# config/trading_hours.py
from datetime import datetime
import pytz


def is_market_open() -> bool:
    """
    Is the US stock market open right now?
    No API call needed. Pure logic.
    """
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)

    # Weekend
    if now.weekday() >= 5:
        return False

    market_open = now.replace(
        hour=9, minute=35, second=0, microsecond=0
    )
    market_close = now.replace(
        hour=15, minute=55, second=0, microsecond=0
    )

    return market_open <= now <= market_close


def get_current_market_session() -> str:
    """
    Returns the current trading session name.
    """
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    hour = now.hour
    minute = now.minute

    if now.weekday() >= 5:
        return "WEEKEND"
    if hour < 9 or (hour == 9 and minute < 30):
        return "PRE_MARKET"
    if hour == 9 and 30 <= minute < 35:
        return "OPENING_CHAOS"
    if hour == 9 and minute >= 35 or (10 <= hour < 12):
        return "MORNING_SESSION"
    if 12 <= hour < 14:
        return "LUNCH_LULL"
    if 14 <= hour <= 15 and minute <= 55:
        return "AFTERNOON_SESSION"
    return "AFTER_HOURS"