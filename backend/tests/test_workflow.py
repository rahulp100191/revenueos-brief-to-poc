from backend.services.retrieval import RetrievalService
from backend.services.workflow import build_workflow

def test_workflow_contains_human_review_interrupt_node():
    graph = build_workflow(RetrievalService())
    assert "human_review" in graph.nodes
    assert "apply_decision" in graph.nodes

