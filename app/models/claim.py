from pydantic import BaseModel
from typing import List
from app.models.enums import ClaimType

class Expense(BaseModel):
    category: str
    amount: float

class ClaimRequest(BaseModel):
    pnr: str
    bag_tag: str
    claim_type: ClaimType
    expenses: List[Expense]