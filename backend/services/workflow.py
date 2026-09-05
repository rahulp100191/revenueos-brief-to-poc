from typing import TypedDict
from langgraph.graph import END, StateGraph
from ..models import Brief, Match, AgentDraft
from .retrieval import RetrievalService
from .llm import generate

class WorkflowState(TypedDict, total=False):
    brief: Brief
    provider: str
    matches: list[Match]
    draft: AgentDraft

def build_workflow(retrieval: RetrievalService):
    async def retrieve_node(state: WorkflowState):
        return {"matches": retrieval.search(state["brief"])}

    async def generate_node(state: WorkflowState):
        draft, _ = await generate(state["provider"], state["brief"], state["matches"])
        return {"draft": draft}

    graph = StateGraph(WorkflowState)
    graph.add_node("retrieve_templates", retrieve_node)
    graph.add_node("generate_draft", generate_node)
    graph.set_entry_point("retrieve_templates")
    graph.add_edge("retrieve_templates", "generate_draft")
    graph.add_edge("generate_draft", END)
    return graph.compile()

