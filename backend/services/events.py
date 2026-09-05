from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .json_store import DATA, read_json, write_json
from ..models import Event

EVENTS = DATA / "events.json"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def all_events() -> list[dict]:
    return read_json(EVENTS, [])

def append_event(event_type: str, owner: str, brief_id: str | None = None, account: str | None = None, payload: dict | None = None) -> dict:
    event = Event(id=f"EV-{uuid4().hex[:8]}", type=event_type, occurred_at=now_iso(), owner=owner, brief_id=brief_id, account=account, payload=payload or {})
    events = all_events()
    events.append(event.model_dump())
    write_json(EVENTS, events)
    return event.model_dump()

