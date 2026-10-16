import pytest

from app.graph.claim_graph import claim_graph
from app.models.claim import ClaimRequest
from app.models.enums import ClaimDecision


class FakeLLMResult:
    decision = ClaimDecision.APPROVE
    approved_amount = 190.0
    reason = "Eligible expenses under delayed baggage policy."
    confidence = 0.95
    input_tokens = 100
    output_tokens = 50


@pytest.mark.asyncio
async def test_full_delayed_claim_workflow(monkeypatch):
    async def mock_lookup_booking(pnr):
        return {
            "pnr": "ABC123",
            "passenger_id": "P001",
            "bag_tag": "BG001",
        }

    async def mock_lookup_baggage(bag_tag):
        return {
            "bag_tag": "BG001",
            "events": [
                {"event": "CHECKED_IN"},
                {"event": "LOADED"},
                {"event": "MISSING"},
            ],
        }

    def mock_search_policy(query):
        return {
            "text": "Basic clothing and toiletries are eligible.",
            "source": "delayed_baggage.md",
        }

    def mock_llm(*args, **kwargs):
        return FakeLLMResult()

    monkeypatch.setattr(
        "app.graph.claim_graph.lookup_booking_info",
        mock_lookup_booking,
    )

    monkeypatch.setattr(
        "app.graph.claim_graph.lookup_baggage_info",
        mock_lookup_baggage,
    )

    monkeypatch.setattr(
        "app.graph.claim_graph.search_policies",
        mock_search_policy,
    )

    monkeypatch.setattr(
        "app.graph.claim_graph.evaluate_claim_with_llm",
        mock_llm,
    )

    claim = ClaimRequest(
        pnr="ABC123",
        bag_tag="BG001",
        claim_type="DELAYED_BAGGAGE",
        expenses=[
            {
                "category": "clothing",
                "amount": 150,
            },
            {
                "category": "toiletries",
                "amount": 40,
            },
        ],
    )

    result = await claim_graph.ainvoke(
        claim.model_dump()
    )

    assert result["decision"] == ClaimDecision.APPROVE
    assert result["approved_amount"] == 190.0
    assert result["policy_source"] == "delayed_baggage.md"
    assert result["confidence"] == 0.95