from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from app.services.data_service import get_booking, get_baggage_events

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

def verify_booking(state: ClaimState):
    booking = get_booking(state["pnr"])

    if not booking:
        return {"decision": "REJECT", "reason": "Booking not found"}

    if booking["bag_tag"] != state["bag_tag"]:
        return {"decision": "REJECT", "reason": "Bag tag does not match booking"}

    return {"booking": booking}

def check_baggage(state: ClaimState):
    if state.get("decision"):
        return {}

    baggage = get_baggage_events(state["bag_tag"])
    if not baggage:
        return {
            "decision": "MANUAL_REVIEW",
            "reason": "Baggage tracking data unavailable",
        }

    return {"baggage": baggage}

def make_decision(state: ClaimState):
    if state.get("decision"):
        return {}

    events = [event["event"] for event in state["baggage"]["events"]]

    if state["claim_type"] == "DELAYED_BAGGAGE" and "MISSING" not in events:
        return {"decision": "REJECT", "reason": "Baggage was not reported missing"}

    total_amount = sum([expense["amount"] for expense in state["expenses"]])

    return {"decision": "APPROVE", "reason": "Claim passed initial validation", "claim_amount": total_amount}

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
builder.add_node("make_decision", make_decision)

builder.add_edge(START, "verify_booking")
builder.add_conditional_edges("verify_booking", route_after_booking, {"continue": "check_baggage", "end": END})
builder.add_conditional_edges("check_baggage", route_after_baggage, {"continue": "make_decision", "end": END})

builder.add_edge("make_decision", END)

claim_graph = builder.compile()
