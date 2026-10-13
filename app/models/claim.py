from pydantic import BaseModel
from typing import List

class Expense(BaseModel):
    category: str
    amount: float

class ClaimRequest(BaseModel):
    pnr: str
    bag_tag: str
    claim_type: str
    expenses: List[Expense]