from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from app.mcp.client import lookup_booking_info, lookup_baggage_info
from app.services.policy_service import search_policies
from app.services.llm_service import evaluate_claim_with_llm

class ClaimState(TypedDict):
    pnr: str
    bag_tag: str
    claim_type: str
    expenses: list

    reason: str
    booking: Optional[dict]
    baggage: Optional[dict]
    decision: str
    claim_amount: float

    policy_text: str
    policy_source: str

    approved_amount: Optional[float]
    confidence: Optional[float]

async def verify_booking(state: ClaimState):
    booking = await lookup_booking_info(state["pnr"])

    if not booking:
        return {"decision": "REJECT", "reason": "Booking not found"}

    if booking["bag_tag"] != state["bag_tag"]:
        return {"decision": "REJECT", "reason": "Bag tag does not match booking"}

    return {"booking": booking}

async def check_baggage(state: ClaimState):
    if state.get("decision"):
        return {}

    baggage = await lookup_baggage_info(state["bag_tag"])
    if not baggage:
        return {
            "decision": "MANUAL_REVIEW",
            "reason": "Baggage tracking data unavailable",
        }

    return {"baggage": baggage}

def retrieve_policy(state: ClaimState):
    query = (
        f"Claim state: {state["claim_type"]}"
        f"Expenses: {state["expenses"]}"
    )

    result = search_policies(query)

    if not result:
        return {
            "decision": "MANUAL_REVIEW",
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
        "claimed_amount": sum(
            expense["amount"]
            for expense in state["expenses"]
        ),
        "approved_amount": result.approved_amount,
        "confidence": result.confidence,
    }

def route_after_booking(state: ClaimState):
    if state.get("decision"):
        return "end"
    return "continue"

def route_after_baggage(state: ClaimState):
    if state.get("decision"):
        return "end"
    return "continue"

builder = StateGraph(ClaimState)

builder.add_node("verify_booking", verify_booking)
builder.add_node("check_baggage", check_baggage)
builder.add_node("retrieve_policy", retrieve_policy)
builder.add_node("make_decision", make_decision)

builder.add_edge(START, "verify_booking")
builder.add_conditional_edges("verify_booking", route_after_booking, {"continue": "check_baggage", "end": END})
builder.add_conditional_edges("check_baggage", route_after_baggage, {"continue": "retrieve_policy", "end": END})
builder.add_edge("retrieve_policy", "make_decision")
builder.add_edge("make_decision", END)

claim_graph = builder.compile()
