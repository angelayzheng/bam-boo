"""The calendar's definition of "today".

The frontend uses the same zone (CALENDAR_TIME_ZONE in calendarEntry.ts), so the
highlighted day and the available day always agree. Keep the two in sync.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

CALENDAR_TIME_ZONE = ZoneInfo("America/Toronto")


def calendar_today(now: datetime | None = None) -> date:
    """The current date in the calendar time zone (injectable for tests)."""
    moment = now if now is not None else datetime.now(CALENDAR_TIME_ZONE)
    return moment.astimezone(CALENDAR_TIME_ZONE).date()
