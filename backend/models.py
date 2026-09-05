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

class POCPlan(BaseModel):
    objective: str
    success_criteria: list[str]
    scope_in: list[str]
    scope_out: list[str]
    templates_used: list[str]
    template_changes: list[str]
    integrations_required: list[str]
    weekly_plan: list[str]
    risks: list[str]
    people_needed: list[str]

class DeliveryHandoff(BaseModel):
    customer_context: str
    solution_summary: str
    systems_and_integrations: list[str]
    deployment_assumptions: list[str]
    acceptance_criteria: list[str]
    open_questions: list[str]

class AgentDraft(BaseModel):
    poc_plan: POCPlan
    delivery_handoff: DeliveryHandoff
    assumptions: list[str] = Field(default_factory=list)

class Event(BaseModel):
    id: str
    type: str
    occurred_at: str
    owner: str
    brief_id: str | None = None
    account: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

