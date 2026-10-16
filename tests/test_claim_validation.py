from app.graph.claim_graph import (
    validate_delayed_claim,
    validate_lost_claim,
    validate_damaged_claim,
)
from app.models.enums import ClaimDecision

def test_delayed_claim_rejected_without_missing_event():
    state = {
        "baggage": {
            "events": [
                {"event": "CHECKED_IN"},
                {"event": "LOADED"},
                {"event": "DELIVERED"},
            ]
        }
    }

    result = validate_delayed_claim(state)

    assert result["decision"] == ClaimDecision.REJECT

def test_confirmed_lost_claim_continues():
    state = {
        "baggage": {
            "events": [
                {"event": "LOST"},
                {"event": "CONFIRMED_LOST"},
            ]
        }
    }

    result = validate_lost_claim(state)

    assert result == {}


def test_unconfirmed_lost_claim_requires_manual_review():
    state = {
        "baggage": {
            "events": [
                {"event": "LOST"}
            ]
        }
    }

    result = validate_lost_claim(state)

    assert result["decision"] == ClaimDecision.MANUAL_REVIEW


def test_damaged_claim_rejected_without_damage_event():
    state = {
        "baggage": {
            "events": [
                {"event": "CHECKED_IN"},
                {"event": "DELIVERED"},
            ]
        }
    }

    result = validate_damaged_claim(state)

    assert result["decision"] == ClaimDecision.REJECT