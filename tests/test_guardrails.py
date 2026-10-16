from app.graph.claim_graph import apply_guardrails
from app.models.enums import ClaimDecision


def test_high_value_approval_requires_manual_review():
    state = {
        "decision": ClaimDecision.APPROVE,
        "approved_amount": 700,
        "confidence": 0.90,
    }

    result = apply_guardrails(state)

    assert result["decision"] == ClaimDecision.MANUAL_REVIEW


def test_low_confidence_requires_manual_review():
    state = {
        "decision": ClaimDecision.APPROVE,
        "approved_amount": 200,
        "confidence": 0.60,
    }

    result = apply_guardrails(state)

    assert result["decision"] == ClaimDecision.MANUAL_REVIEW


def test_valid_approval_passes_guardrails():
    state = {
        "decision": ClaimDecision.APPROVE,
        "approved_amount": 200,
        "confidence": 0.90,
    }

    result = apply_guardrails(state)

    assert result == {}