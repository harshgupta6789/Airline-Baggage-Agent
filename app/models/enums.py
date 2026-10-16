from enum import Enum

class ClaimType(str, Enum):
    DELAYED_BAGGAGE = "DELAYED_BAGGAGE"
    LOST_BAGGAGE = "LOST_BAGGAGE"
    DAMAGED_BAGGAGE = "DAMAGED_BAGGAGE"

class ClaimDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"