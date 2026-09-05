from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
START_HOUR, END_HOUR = 9, 17

def _local(value: datetime) -> datetime:
    return value.astimezone(TZ) if value.tzinfo else value.replace(tzinfo=TZ)

def business_hours_between(start: datetime, end: datetime) -> float:
    start, end = _local(start), _local(end)
    if end <= start: return 0.0
    total, cursor = 0.0, start
    while cursor.date() <= end.date():
        if cursor.weekday() < 5:
            day_start = cursor.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
            day_end = cursor.replace(hour=END_HOUR, minute=0, second=0, microsecond=0)
            left, right = max(start, day_start), min(end, day_end)
            if right > left: total += (right - left).total_seconds() / 3600
        cursor = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return round(total, 2)

def health(received_at: str, now: datetime | None = None) -> dict:
    start = datetime.fromisoformat(received_at)
    end = now or datetime.now(TZ)
    hours = business_hours_between(start, end)
    ratio = hours / 16
    status = "GREEN" if ratio <= 0.5 else "AMBER" if ratio <= 1 else "RED"
    return {"status": status, "elapsed_business_hours": hours, "elapsed_business_days": round(hours / 8, 2), "sla_hours": 16}

