import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

def read_json(path: Path, default: Any):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")

def read_briefs():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "briefs").glob("*.json"))]

def read_templates():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "templates").glob("*.json"))]

