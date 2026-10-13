from app.services.data_service import get_booking, get_baggage_events

def validate_claim(claim):
    booking = get_booking(claim.pnr)
    if not booking:
        return {
            "decision": "REJECT",
            "reason": "Booking not found"
        }

    if booking["bag_tag"] != claim.bag_tag:
        return {
            "decision": "REJECT",
            "reason": "Bag tag does not match booking"
        }

    baggage = get_baggage_events(claim.bag_tag)

    if not baggage:
        return {
            "decision": "MANUAL_REVIEW",
            "reason": "Baggage record not found"
        }

    events = [event["event"] for event in baggage["events"]]

    if claim.claim_type == "DELAYED_BAGGAGE":
        if "MISSING" not in events:
            return {
                "decision": "REJECT",
                "reason": "Baggage tracking does not indicate a delay"
            }

    total_amount = sum(expense.amount for expense in claim.expenses)

    return {
        "decision": "APPROVE",
        "total_amount": total_amount,
        "reason": "Claim passed initial validation"
    }

