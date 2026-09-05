import json
import os
import httpx
from ..models import AgentDraft, Brief, Match, POCPlan, DeliveryHandoff

class ProviderError(Exception):
    def __init__(self, provider: str, message: str, status_code: int = 503):
        self.provider, self.message, self.status_code = provider, message, status_code

def prompt_for(brief: Brief, matches: list[Match]) -> str:
    context = [{"id": m.template.id, "name": m.template.name, "problem": m.template.problem_solved, "capabilities": m.template.capabilities, "integrations": m.template.integrations, "reasons": m.reasons} for m in matches]
    return f"""Return ONLY valid JSON matching this schema: {{poc_plan: {{objective:string, success_criteria:string[], scope_in:string[], scope_out:string[], templates_used:string[], template_changes:string[], integrations_required:string[], weekly_plan:string[], risks:string[], people_needed:string[]}}, delivery_handoff: {{customer_context:string, solution_summary:string, systems_and_integrations:string[], deployment_assumptions:string[], acceptance_criteria:string[], open_questions:string[]}}, assumptions:string[]}}. Do not invent customer facts. Use the supplied brief and matched templates. Create an actionable editable POC plan, not a summary.\nBRIEF:\n{brief.model_dump_json()}\nMATCHED TEMPLATES:\n{json.dumps(context)}"""

def fallback(brief: Brief, matches: list[Match]) -> AgentDraft:
    ids = [m.template.id for m in matches]
    names = [m.template.name for m in matches]
    integrations = sorted({i for m in matches for i in m.template.integrations if i in brief.systems or i.lower() in brief.problem.lower()}) or brief.systems
    return AgentDraft(poc_plan=POCPlan(objective=f"Prove an assisted workflow for {brief.problem}", success_criteria=brief.success_criteria, scope_in=["Ingest synthetic brief", "Retrieve prior solution patterns", "Human review of generated output"], scope_out=["Autonomous production decisions", "Production deployment"], templates_used=names, template_changes=[f"Adapt {names[0]} to {brief.regulator} context"], integrations_required=integrations, weekly_plan=["Week 1: confirm data and baseline", "Week 2: configure retrieval and draft workflow", "Week 3: run test cases and review", "Week 4: harden acceptance criteria"], risks=["Synthetic data may not represent production edge cases", "Human review remains required"], people_needed=["US Solution Architect", "Customer subject-matter expert"]), delivery_handoff=DeliveryHandoff(customer_context=f"{brief.account} operates in {brief.region} under {brief.regulator}.", solution_summary=f"Use {names[0]} as the starting pattern and adapt it to the stated problem.", systems_and_integrations=brief.systems, deployment_assumptions=["Synthetic data only", "Customer retains final decision authority"], acceptance_criteria=brief.success_criteria, open_questions=["Which production data source owns the initial event?", "Who approves the final rollout?"]), assumptions=["Template matches are advisory and require human approval."])

async def generate(provider: str, brief: Brief, matches: list[Match]) -> tuple[AgentDraft, str]:
    prompt = prompt_for(brief, matches)
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key: raise ProviderError(provider, "Gemini API key is not configured. Add GEMINI_API_KEY to .env.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{os.getenv('GEMINI_MODEL','gemini-flash-latest')}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, headers={"Content-Type":"application/json","X-goog-api-key":key}, json={"contents":[{"parts":[{"text":prompt}]}]})
            response.raise_for_status(); text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc: raise ProviderError(provider, f"Gemini did not respond: {exc}") from exc
    elif provider == "lm_studio":
        url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234").rstrip("/") + "/api/v1/chat"
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(url, headers={"Content-Type":"application/json"}, json={"model":os.getenv("LM_STUDIO_MODEL","google/gemma-3-1b"),"system_prompt":"You produce only valid JSON for a POC plan.","input":prompt})
            response.raise_for_status(); body = response.json(); text = body.get("output") or body.get("response") or body.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as exc: raise ProviderError(provider, f"LM Studio did not respond: {exc}") from exc
    else: raise ProviderError(provider, "Unsupported LLM provider.", 400)
    try:
        cleaned = text.strip().removeprefix("```json").removesuffix("```").strip()
        return AgentDraft.model_validate_json(cleaned), provider
    except Exception as exc: raise ProviderError(provider, f"{provider} returned invalid draft JSON: {exc}") from exc

