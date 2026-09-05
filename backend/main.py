import os, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .models import Brief, Provider
from .services.json_store import read_briefs, DATA, read_json, write_json
from .services.events import append_event
from .services.sla import health
from .services.retrieval import RetrievalService
from .services.llm import generate, ProviderError
from .services.feedback import update, reuse_rate

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = FastAPI(title="RevenueOS Brief-to-POC API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
retrieval = RetrievalService()

class GenerateRequest(BaseModel): provider: Provider
class DecisionRequest(BaseModel): decision: str; draft: dict; rejection_reason: str | None = None

def briefs(): return [Brief(**x) for x in read_briefs()]
def find_brief(brief_id: str):
    for b in briefs():
        if b.id == brief_id: return b
    raise HTTPException(404, "Brief not found")

def maybe_trigger(brief: Brief, item_health: dict, draft: dict | None):
    if item_health["status"] != "RED": return None
    events = read_json(DATA / "events.json", [])
    if any(e.get("type") == "seam.breached" and e.get("brief_id") == brief.id for e in events): return None
    event = append_event("seam.breached", "US Solution Architect", brief.id, brief.account, {"health": item_health, "draft": draft})
    triggers = read_json(DATA / "triggers.json", [])
    trigger = {"id": f"TR-{len(triggers)+1:03d}", "brief_id": brief.id, "created_at": event["occurred_at"], "owner": "US Solution Architect", "reason": "two_business_day_sla_breach", "health": "RED", "draft": draft, "context": {"account": brief.account, "elapsed_business_days": item_health["elapsed_business_days"]}, "status": "open"}
    triggers.append(trigger); write_json(DATA / "triggers.json", triggers)
    append_event("trigger.created", "US Solution Architect", brief.id, brief.account, {"trigger_id": trigger["id"]})
    return trigger

@app.get("/api/health")
def api_health(): return {"ok": True}

@app.get("/api/briefs")
def list_briefs():
    output = []
    for b in briefs():
        h = health(b.received_at)
        draft_path = DATA / "drafts" / f"{b.id}.json"
        draft = read_json(draft_path, None) if draft_path.exists() else None
        trigger = maybe_trigger(b, h, draft)
        output.append({"brief": b.model_dump(), "health": h, "draft": draft, "trigger": trigger})
    return {"items": output, "reuse_rate": reuse_rate()}

@app.post("/api/briefs")
def create_brief(brief: Brief):
    existing = read_briefs()
    if any(x["id"] == brief.id for x in existing): raise HTTPException(409, "Brief already exists")
    path = DATA / "briefs" / f"{brief.id}.json"; write_json(path, brief.model_dump())
    append_event("opportunity.won", brief.owner, brief.id, brief.account, {"source":"synthetic_hubspot_webhook", "stage":"closed_won"})
    return {"brief": brief}

@app.post("/api/briefs/{brief_id}/generate")
async def generate_draft(brief_id: str, request: GenerateRequest):
    brief = find_brief(brief_id); matches = retrieval.search(brief)
    try: draft, provider = await generate(request.provider, brief, matches)
    except ProviderError as exc: raise HTTPException(exc.status_code, {"code":"LLM_PROVIDER_UNAVAILABLE", "provider":exc.provider, "message":exc.message})
    path = DATA / "drafts" / f"{brief_id}.json"; write_json(path, {"draft":draft.model_dump(), "matches":[m.model_dump() for m in matches], "provider":provider, "generated_at":datetime.now().isoformat()})
    append_event("draft.generated", "US Solution Architect", brief_id, brief.account, {"provider":provider, "template_ids":[m.template.id for m in matches]})
    return {"draft":draft.model_dump(), "matches":[m.model_dump() for m in matches], "provider":provider}

@app.post("/api/briefs/{brief_id}/decision")
def decision(brief_id: str, request: DecisionRequest):
    brief = find_brief(brief_id)
    if request.decision not in ("accepted", "rejected"): raise HTTPException(400, "decision must be accepted or rejected")
    if request.decision == "rejected" and not request.rejection_reason: raise HTTPException(400, "rejection_reason is required")
    path = DATA / "drafts" / f"{brief_id}.json"; existing = read_json(path, {})
    write_json(path, {**existing, "draft":request.draft, "status":request.decision})
    template_ids = [x.get("template", {}).get("id") for x in existing.get("matches", []) if x.get("template", {}).get("id")]
    update(template_ids, request.decision, edited=True)
    append_event(f"draft.{request.decision}", "US Solution Architect", brief_id, brief.account, {"template_ids":template_ids, "rejection_reason":request.rejection_reason})
    return {"ok":True, "reuse_rate":reuse_rate()}

@app.get("/api/triggers")
def triggers(): return {"items": read_json(DATA / "triggers.json", [])}

