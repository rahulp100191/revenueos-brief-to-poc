import json
import os
import httpx
from json_repair import repair_json
from ..models import AgentDraft, Brief, Match, POCPlan, DeliveryHandoff, TemplateAnalysis, RecommendedTemplate, TemplateReuse, WeekPlan, Risk

class ProviderError(Exception):
    def __init__(self, provider: str, message: str, status_code: int = 503):
        self.provider, self.message, self.status_code = provider, message, status_code

def prompt_for(brief: Brief, matches: list[Match]) -> str:
    candidates = [{"template_id": m.template.id, "name": m.template.name, "region": m.template.region, "segment": m.template.segment, "regulators": m.template.regulators, "problem_solved": m.template.problem_solved, "capabilities": m.template.capabilities, "integrations": m.template.integrations, "outcome": m.template.outcome, "retrieval_reasons": m.reasons} for m in matches[:3]]
    return f"""You are a senior enterprise Solution Architect specializing in financial-services POCs. You assist a US Solution Architect after Sales has won an enterprise opportunity. Analyze the normalized customer brief against ONLY the three retrieved solution templates below. Explain relevance, mismatches, reuse recommendations, required changes, an actionable POC plan, and a Delivery handoff skeleton. Use only supplied facts. Never invent customer facts, regulatory requirements, systems, integrations, capabilities, or additional templates. Do not modify retrieval scores. Clearly label recommendations and missing information. If no candidate is suitable, return an empty recommended_templates array. Return ONLY valid JSON matching the supplied schema.\n\nCUSTOMER BRIEF (normalized JSON):\n{brief.model_dump_json()}\n\nTOP 3 RETRIEVED SOLUTION TEMPLATES (JSON):\n{json.dumps(candidates)}\n\nRequired JSON keys: template_analysis (template_id, recommendation, match_reasons, mismatches, required_changes), recommended_templates (template_id, reuse_type, reason), poc_plan (objective, success_criteria, scope_in, scope_out, templates_reused with template_id and changes_required, integrations_required, weekly_plan with week and activities, risks with risk and mitigation, people_required), delivery_handoff (account, business_problem, solution_summary, approved_scope, integrations, dependencies, risks, open_questions), open_questions."""

def fallback(brief: Brief, matches: list[Match]) -> AgentDraft:
    names = [m.template.name for m in matches]
    template_ids = [m.template.id for m in matches]
    integrations = sorted({i for m in matches for i in m.template.integrations if i in brief.systems or i.lower() in brief.problem.lower()}) or brief.systems
    analysis = [TemplateAnalysis(template_id=m.template.id, recommendation="adapt" if m.template.region != brief.region or brief.regulator not in m.template.regulators else "reuse", match_reasons=m.reasons, mismatches=[f"Regulator context differs from {brief.regulator}"] if brief.regulator not in m.template.regulators else [], required_changes=[f"Validate the workflow against {brief.regulator} requirements"] if brief.regulator not in m.template.regulators else []) for m in matches]
    recommended = [RecommendedTemplate(template_id=template_ids[0], reuse_type="primary", reason="Strongest retrieved overlap in the supplied problem and segment.")] if template_ids else []
    return AgentDraft(template_analysis=analysis, recommended_templates=recommended, poc_plan=POCPlan(objective=f"Prove an assisted workflow for {brief.problem}", success_criteria=brief.success_criteria, scope_in=["Ingest synthetic brief", "Retrieve prior solution patterns", "Human review of generated output"], scope_out=["Autonomous production decisions", "Production deployment"], templates_reused=[TemplateReuse(template_id=template_ids[0], changes_required=[f"Adapt to {brief.regulator} context"]) ] if template_ids else [], integrations_required=integrations, weekly_plan=[WeekPlan(week=1, activities=["Confirm requirements", "Validate sample data", "Confirm integration interfaces"]), WeekPlan(week=2, activities=["Configure retrieval and draft workflow"]), WeekPlan(week=3, activities=["Run test cases and human review"])], risks=[Risk(risk="Regulatory workflow may differ from the retrieved template.", mitigation=f"Validate requirements with {brief.regulator} stakeholders.")], people_required=["US Solution Architect", "Customer technical stakeholder"]), delivery_handoff=DeliveryHandoff(account=brief.account, business_problem=brief.problem, solution_summary=f"Use {names[0] if names else 'retrieved solution patterns'} as the starting point and adapt it to the brief.", approved_scope=["Brief ingestion", "Template retrieval", "Human-reviewed POC workflow"], integrations=brief.systems, dependencies=["Customer sample data", "Access to agreed integration interfaces"], risks=[f"The {brief.regulator} workflow requires customer validation."], open_questions=["Which specific controls must the POC demonstrate?"]), open_questions=["Which specific controls must the POC demonstrate?", "Which document or transaction types are in scope?"])

def _list_value(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None or str(value).strip().lower() in {"", "none", "n/a", "null"}:
        return []
    return [part.strip(" -•") for part in str(value).replace(";", "\n").splitlines() if part.strip()]

def _analysis_value(value, default):
    if isinstance(value, dict):
        value = [{"template_id": key, **(item if isinstance(item, dict) else {})} for key, item in value.items()]
    if not isinstance(value, list): return default
    normalized = []
    for item in value:
        if not isinstance(item, dict): continue
        row = {**item}
        recommendation = str(row.get("recommendation", "adapt")).lower().replace(" ", "_")
        row["recommendation"] = recommendation if recommendation in {"reuse", "adapt", "do_not_reuse"} else "adapt"
        row["match_reasons"] = _list_value(row.get("match_reasons"))
        row["mismatches"] = _list_value(row.get("mismatches"))
        row["required_changes"] = _list_value(row.get("required_changes"))
        normalized.append(row)
    return normalized or default

def _recommended_value(value, default):
    if isinstance(value, dict):
        value = [{"template_id": key, **(item if isinstance(item, dict) else {})} for key, item in value.items()]
    if not isinstance(value, list): return default
    normalized = []
    for item in value:
        if not isinstance(item, dict): continue
        row = {**item}
        row["reuse_type"] = "primary" if str(row.get("reuse_type", "supporting")).lower() == "primary" else "supporting"
        row["reason"] = str(row.get("reason", "Recommended based on retrieved evidence."))
        normalized.append(row)
    return normalized

def normalize_draft(payload: dict, brief: Brief, matches: list[Match]) -> AgentDraft:
    """Repair common small-local-model formatting drift without changing its content."""
    base = fallback(brief, matches).model_dump()
    poc = {**base["poc_plan"], **(payload.get("poc_plan") or {})}
    delivery = {**base["delivery_handoff"], **(payload.get("delivery_handoff") or {})}
    for key in poc:
        if key in {"templates_reused", "weekly_plan", "risks"}:
            if not isinstance(poc.get(key), list) or any(not isinstance(item, dict) for item in poc.get(key, [])):
                poc[key] = base["poc_plan"][key]
        elif isinstance(base["poc_plan"].get(key), list):
            poc[key] = _list_value(poc.get(key))
    for key in delivery:
        if isinstance(base["delivery_handoff"].get(key), list): delivery[key] = _list_value(delivery.get(key))
    return AgentDraft.model_validate({
        "template_analysis": _analysis_value(payload.get("template_analysis"), base["template_analysis"]),
        "recommended_templates": _recommended_value(payload.get("recommended_templates"), base["recommended_templates"]),
        "poc_plan": poc,
        "delivery_handoff": delivery,
        "open_questions": _list_value(payload.get("open_questions")) or base["open_questions"],
    })

async def generate(provider: str, brief: Brief, matches: list[Match]) -> tuple[AgentDraft, str]:
    prompt = prompt_for(brief, matches)
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key: raise ProviderError(provider, "Gemini API key is not configured. Add GEMINI_API_KEY to .env.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{os.getenv('GEMINI_MODEL','gemini-flash-latest')}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=float(os.getenv("GEMINI_TIMEOUT_SECONDS", "600"))) as client:
                response = await client.post(url, headers={"Content-Type":"application/json","X-goog-api-key":key}, json={"contents":[{"parts":[{"text":prompt}]}]})
            response.raise_for_status(); text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc: raise ProviderError(provider, f"Gemini did not respond ({type(exc).__name__}): {exc or 'request timed out or connection failed'}") from exc
    elif provider == "lm_studio":
        url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234").rstrip("/") + "/api/v1/chat"
        try:
            async with httpx.AsyncClient(timeout=float(os.getenv("LM_STUDIO_TIMEOUT_SECONDS", "600"))) as client:
                response = await client.post(url, headers={"Content-Type":"application/json"}, json={"model":os.getenv("LM_STUDIO_MODEL","google/gemma-3-1b"),"system_prompt":"You produce only valid JSON for a POC plan. Keep every array short. Do not use markdown fences.","input":prompt,"temperature":0.1,"max_output_tokens":1200})
            response.raise_for_status(); body = response.json()
            output = body.get("output")
            if isinstance(output, list):
                text = "".join(item.get("content", "") for item in output if isinstance(item, dict) and item.get("type") == "message")
            else:
                text = output or body.get("response") or body.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as exc: raise ProviderError(provider, f"LM Studio did not respond ({type(exc).__name__}): {exc or 'request timed out or connection failed'}") from exc
    else: raise ProviderError(provider, "Unsupported LLM provider.", 400)
    try:
        cleaned = text.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = repair_json(cleaned, return_objects=True)
        return normalize_draft(parsed, brief, matches), provider
    except Exception as exc: raise ProviderError(provider, f"{provider} returned invalid draft JSON: {exc}") from exc
