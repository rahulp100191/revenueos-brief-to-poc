from datetime import datetime
from backend.services.sla import health

def test_green_at_one_business_day():
    result = health("2026-09-04T09:00:00-04:00", datetime.fromisoformat("2026-09-04T17:00:00-04:00"))
    assert result["status"] == "GREEN"

def test_amber_after_one_day_before_two():
    result = health("2026-09-03T09:00:00-04:00", datetime.fromisoformat("2026-09-04T13:00:00-04:00"))
    assert result["status"] == "AMBER"

def test_red_after_two_business_days():
    result = health("2026-09-01T09:00:00-04:00", datetime.fromisoformat("2026-09-03T09:01:00-04:00"))
    assert result["status"] == "RED"

