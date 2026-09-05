from datetime import datetime, timezone
from .json_store import DATA, read_json, write_json

PATH = DATA / "feedback.json"

def feedback() -> list[dict]: return read_json(PATH, [])

def update(template_ids: list[str], decision: str, edited: bool = False):
    rows = feedback(); ids = set(template_ids)
    for row in rows:
        if row["template_id"] in ids:
            if decision == "accepted": row["accepted_count"] += 1
            if decision == "rejected": row["rejected_count"] += 1
            if edited: row["edited_count"] += 1
            row["last_feedback_at"] = datetime.now(timezone.utc).isoformat()
    write_json(PATH, rows)
    return rows

def reuse_rate() -> float:
    rows = feedback()
    accepted = sum(r["accepted_count"] for r in rows)
    rejected = sum(r["rejected_count"] for r in rows)
    total = accepted + rejected
    return round(accepted / total, 2) if total else 0.0

