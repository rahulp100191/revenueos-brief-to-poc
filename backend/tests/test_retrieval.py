from backend.models import Brief
from backend.services.retrieval import RetrievalService

def test_retrieval_returns_explainable_matches():
    brief = Brief(id="TEST", account="Test Bank", owner="Owner", region="UK", segment="retail_bank", regulator="FCA", problem="KYC document review", systems=["Salesforce"], expected_timeline="6 weeks", success_criteria=["classify documents"], received_at="2026-09-05T13:00:00-04:00")
    results = RetrievalService().search(brief)
    assert len(results) == 3
    assert results[0].reasons

