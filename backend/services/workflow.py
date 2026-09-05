from typing import Any, TypedDict
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt
from ..models import Brief, Match, AgentDraft
from .retrieval import RetrievalService
from .llm import generate
from .events import append_event
from .feedback import update
from .json_store import DATA, read_json, write_json

class WorkflowState(TypedDict, total=False):
    brief: Brief
    provider: str
    matches: list[Match]
    draft: AgentDraft
    decision: dict[str, Any]

def build_workflow(retrieval: RetrievalService):
    async def retrieve_node(state: WorkflowState):
        return {"matches": retrieval.search(state["brief"])}

    async def generate_node(state: WorkflowState):
        draft, _ = await generate(state["provider"], state["brief"], state["matches"])
        return {"draft": draft}

    def review_node(state: WorkflowState):
        decision = interrupt({
            "type": "human_review",
            "reviewer": "US Solution Architect",
            "brief_id": state["brief"].id,
            "draft": state["draft"].model_dump(),
        })
        return {"decision": decision}

    def decision_node(state: WorkflowState):
        decision = state["decision"]
        brief = state["brief"]
        draft = AgentDraft.model_validate(decision["draft"])
        existing = read_json(DATA / "drafts" / f"{brief.id}.json", {})
        write_json(DATA / "drafts" / f"{brief.id}.json", {**existing, "draft": draft.model_dump(), "status": decision["decision"]})
        template_ids = [m.template.id for m in state["matches"]]
        if decision.get("edited", False):
            append_event("draft.edited", "US Solution Architect", brief.id, brief.account, {"template_ids": template_ids})
        update(template_ids, decision["decision"], edited=decision.get("edited", False))
        append_event(f"draft.{decision['decision']}", "US Solution Architect", brief.id, brief.account, {"template_ids": template_ids, "rejection_reason": decision.get("rejection_reason")})
        return {"decision": decision}

    graph = StateGraph(WorkflowState)
    graph.add_node("retrieve_templates", retrieve_node)
    graph.add_node("generate_draft", generate_node)
    graph.add_node("human_review", review_node)
    graph.add_node("apply_decision", decision_node)
    graph.set_entry_point("retrieve_templates")
    graph.add_edge("retrieve_templates", "generate_draft")
    graph.add_edge("generate_draft", "human_review")
    graph.add_edge("human_review", "apply_decision")
    graph.add_edge("apply_decision", END)
    from langgraph.checkpoint.memory import MemorySaver
    return graph.compile(checkpointer=MemorySaver())
