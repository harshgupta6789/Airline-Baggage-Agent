import os

from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from app.models.enums import ClaimDecision

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ClaimDecision(BaseModel):
    decision: Literal[ClaimDecision.APPROVE, ClaimDecision.REJECT, ClaimDecision.MANUAL_REVIEW]
    approved_amount: float
    reason: str
    confidence: float

    input_tokens: int = 0
    output_tokens: int = 0

def evaluate_claim_with_llm(
        claim_type: str,
        expenses: list,
        baggage: dict,
        policy_text: str
):
    prompt = f"""
You are validating an airline baggage claim.

Claim type:
{claim_type}

Expenses:
{expenses}

Baggage tracking data:
{baggage}

Applicable policy:
{policy_text}

Determine whether the claim should be APPROVE, REJECT or MANUAL_REVIEW

Rules:
- Base the decision only on the supplied data and policy.
- Do not invent facts.
- approved_amount must be 0 for rejected claims.
- Use MANUAL_REVIEW when the available evidence is insufficient or ambiguous.
- confidence must be between 0 and 1.
"""

    response = client.responses.parse(
        model="gpt-6-luna",
        input=prompt,
        text_format=ClaimDecision,
    )

    parsed = response.output_parsed

    parsed.input_tokens = response.usage.input_tokens
    parsed.output_tokens = response.usage.output_tokens

    return parsed