from backend.models import Brief
from backend.services.retrieval import RetrievalService

def test_retrieval_returns_explainable_matches():
    brief = Brief(id="TEST", account="Test Bank", owner="Owner", region="UK", segment="retail_bank", regulator="FCA", problem="KYC document review", systems=["Salesforce"], expected_timeline="6 weeks", success_criteria=["classify documents"], received_at="2026-09-05T13:00:00-04:00")
    service = RetrievalService()
    service.initialize()
    assert service.status()["ready"] is True
    assert service.status()["template_count"] == 8
    assert len(service._collection.get(include=[])["ids"]) == 8
    results = service.search(brief)
    assert len(results) == 3
    assert results[0].reasons
    assert results[0].vector_similarity >= 0
    assert results[0].structured_components["segment_match"] == 1.0
    assert results[0].citation["document_path"]
    assert results[0].score >= results[1].score >= results[2].score

    second = RetrievalService()
    second.initialize()
    assert len(second._collection.get(include=[])["ids"]) == 8
