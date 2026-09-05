from typing import Any, Literal
from pydantic import BaseModel, Field

Provider = Literal["gemini", "lm_studio"]

class Brief(BaseModel):
    id: str
    account: str
    owner: str
    region: str
    segment: str
    regulator: str
    problem: str
    systems: list[str]
    expected_timeline: str
    success_criteria: list[str]
    received_at: str

class Template(BaseModel):
    id: str
    name: str
    region: str
    segment: str
    regulators: list[str]
    problem_solved: str
    capabilities: list[str]
    integrations: list[str]
    effort_weeks: int
    outcome: str
    last_used: str
    owner: str
    document_path: str

class Match(BaseModel):
    template: Template
    score: float
    reasons: list[str]
    vector_similarity: float = 0.0
    structured_components: dict[str, float] = Field(default_factory=dict)
    citation: dict[str, str] = Field(default_factory=dict)

class TemplateAnalysis(BaseModel):
    template_id: str
    recommendation: Literal["reuse", "adapt", "do_not_reuse"]
    match_reasons: list[str]
    mismatches: list[str]
    required_changes: list[str]

class RecommendedTemplate(BaseModel):
    template_id: str
    reuse_type: Literal["primary", "supporting"]
    reason: str

class TemplateReuse(BaseModel):
    template_id: str
    changes_required: list[str]

class WeekPlan(BaseModel):
    week: int
    activities: list[str]

class Risk(BaseModel):
    risk: str
    mitigation: str

class POCPlan(BaseModel):
    objective: str
    success_criteria: list[str]
    scope_in: list[str]
    scope_out: list[str]
    templates_reused: list[TemplateReuse]
    integrations_required: list[str]
    weekly_plan: list[WeekPlan]
    risks: list[Risk]
    people_required: list[str]

class DeliveryHandoff(BaseModel):
    account: str
    business_problem: str
    solution_summary: str
    approved_scope: list[str]
    integrations: list[str]
    dependencies: list[str]
    risks: list[str]
    open_questions: list[str]

class AgentDraft(BaseModel):
    template_analysis: list[TemplateAnalysis]
    recommended_templates: list[RecommendedTemplate]
    poc_plan: POCPlan
    delivery_handoff: DeliveryHandoff
    open_questions: list[str] = Field(default_factory=list)

class Event(BaseModel):
    id: str
    type: str
    occurred_at: str
    owner: str
    brief_id: str | None = None
    account: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
