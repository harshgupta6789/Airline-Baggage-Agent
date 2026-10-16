from app.services.llm_service import evaluate_claim_with_llm
from app.models.enums import ClaimDecision, ClaimType

result = evaluate_claim_with_llm(
    claim_type=ClaimType.DELAYED_BAGGAGE,
    expenses=[
        {"category": "clothing", "amount": 150},
        {"category": "toiletries", "amount": 40},
    ],
    baggage={
        "bag_tag": "BG001",
        "events": [
            {"airport": "DFW", "event": "CHECKED_IN"},
            {"airport": "DFW", "event": "LOADED"},
            {"airport": "JFK", "event": "MISSING"}
        ]
    },
    policy_text="""
Passengers may claim reasonable and necessary expenses while baggage is delayed.
Basic clothing and toiletries are eligible.
Luxury items and electronics are not eligible.
Claims above $500 require manual review.
""",
)

print(result)