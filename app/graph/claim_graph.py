from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from app.mcp.client import lookup_booking_info, lookup_baggage_info
from app.services.policy_service import search_policies
from app.services.llm_service import evaluate_claim_with_llm
from app.models.enums import ClaimType, ClaimDecision

class ClaimState(TypedDict):
    pnr: str
    bag_tag: str
    claim_type: ClaimType
    expenses: list

    reason: str
    booking: Optional[dict]
    baggage: Optional[dict]
    decision: ClaimDecision
    claim_amount: float

    policy_text: str
    policy_source: str

    approved_amount: Optional[float]
    confidence: Optional[float]

async def verify_booking(state: ClaimState):
    booking = await lookup_booking_info(state["pnr"])

    if not booking:
        return {"decision": ClaimDecision.REJECT, "reason": "Booking not found"}

    if booking["bag_tag"] != state["bag_tag"]:
        return {"decision": ClaimDecision.REJECT, "reason": "Bag tag does not match booking"}

    return {"booking": booking}

async def check_baggage(state: ClaimState):
    if state.get("decision"):
        return {}

    baggage = await lookup_baggage_info(state["bag_tag"])
    if not baggage:
        return {
            "decision": ClaimDecision.MANUAL_REVIEW,
            "reason": "Baggage tracking data unavailable",
        }

    return {"baggage": baggage}

def validate_delayed_claim(state: ClaimState):
    events = [event["event"] for event in state["baggage"]["events"]]

    if "MISSING" not in events:
        return {
            "decision": ClaimDecision.REJECT,
            "reason": "Baggage tracking does not show evidence of delay."
        }

    return {}

def validate_lost_claim(state: ClaimState):
    events = [event["event"] for event in state["baggage"]["events"]]

    if "CONFIRMED_LOST" in events:
        return {}

    if "LOST" in events:
        return {
            "decision": ClaimDecision.MANUAL_REVIEW,
            "reason": "Baggage is marked lost but has not been formally confirmed as unrecoverable."
        }

    return {
        "decision": ClaimDecision.REJECT,
        "reason": "Baggage tracking does not indicate that the bag is lost."
    }

def validate_damaged_claim(state: ClaimState):
    events = [event["event"] for event in state["baggage"]["events"]]

    if "DAMAGED" not in events:
        return {
            "decision": ClaimDecision.REJECT,
            "reason": "Baggage tracking does not indicate reported damage"
        }

    return {}

def retrieve_policy(state: ClaimState):
    query = (
        f"Airline baggage claim type: {state['claim_type'].value}. "
        f"Claimed expenses: {state['expenses']}. "
        f"Retrieve the policy governing eligibility, reimbursement limits, "
        f"documentation requirements, exclusions, and manual-review rules."
    )

    result = search_policies(query)

    if not result:
        return {
            "decision": ClaimDecision.MANUAL_REVIEW,
            "reason": "Relevant policy could not be retrieved"
        }

    return {
        "policy_text": result["text"],
        "policy_source": result["source"]
    }

def make_decision(state: ClaimState):
    if state.get("decision"):
        return {}

    result = evaluate_claim_with_llm(
        claim_type=state["claim_type"],
        expenses=state["expenses"],
        baggage=state["baggage"],
        policy_text=state["policy_text"],
    )
    
    return {
        "decision": result.decision,
        "reason": result.reason,
        "claim_amount": sum(
            expense["amount"]
            for expense in state["expenses"]
        ),
        "approved_amount": result.approved_amount,
        "confidence": result.confidence,
    }

def apply_guardrails(state: ClaimState):
    decision = state.get("decision")
    approved_amount = state.get("approved_amount")
    confidence = state.get("confidence")

    if decision == ClaimDecision.APPROVE and approved_amount > 500:
        return {
            "decision": ClaimDecision.MANUAL_REVIEW,
            "reason": "Approved amount exceeds automatic approval threshold."
        }
    if confidence < 0.75:
        return {
            "decision": ClaimDecision.MANUAL_REVIEW,
            "reason": "Model confidence below automatic decision threshold."
        }

    return {}

def route_after_booking(state: ClaimState):
    if state.get("decision"):
        return "end"
    return "continue"

def route_claim_type(state: ClaimState):
    if state.get("decision"):
        return "end"
    claim_type = state["claim_type"]
    if claim_type == ClaimType.DELAYED_BAGGAGE:
        return "delayed"

    if claim_type == ClaimType.LOST_BAGGAGE:
        return "lost"

    if claim_type == ClaimType.DAMAGED_BAGGAGE:
        return "damaged"

    return "unsupported"

def route_if_decision_exists(state: ClaimState):
    if state.get("decision"):
        return "end"
    return "continue"

builder = StateGraph(ClaimState)

builder.add_node("verify_booking", verify_booking)
builder.add_node("check_baggage", check_baggage)
builder.add_node("validate_delayed_claim", validate_delayed_claim)
builder.add_node("validate_lost_claim", validate_lost_claim)
builder.add_node("validate_damaged_claim", validate_damaged_claim)
builder.add_node("retrieve_policy", retrieve_policy)
builder.add_node("make_decision", make_decision)
builder.add_node("apply_guardrails", apply_guardrails)

builder.add_edge(START, "verify_booking")
builder.add_conditional_edges("verify_booking", route_after_booking, {"continue": "check_baggage", "end": END})
builder.add_conditional_edges("check_baggage", route_claim_type, {
    "delayed": "validate_delayed_claim",
    "lost": "validate_lost_claim",
    "damaged": "validate_damaged_claim",
    "unsupported": END,
    "end": END,
    })
builder.add_conditional_edges("validate_delayed_claim", route_if_decision_exists, {"continue": "retrieve_policy", "end": END})
builder.add_conditional_edges("validate_lost_claim", route_if_decision_exists, {"continue": "retrieve_policy", "end": END})
builder.add_conditional_edges("validate_damaged_claim", route_if_decision_exists, {"continue": "retrieve_policy", "end": END})
builder.add_conditional_edges("retrieve_policy", route_if_decision_exists, { "continue": "make_decision", "end": END})
builder.add_edge("make_decision", "apply_guardrails")
builder.add_edge("apply_guardrails", END)

claim_graph = builder.compile()
