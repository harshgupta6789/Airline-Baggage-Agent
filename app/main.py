import os
import time

from fastapi import FastAPI, HTTPException

from app.services.data_service import get_booking, get_baggage_events
from app.models.claim import ClaimRequest
from app.services.claim_validator import validate_claim
from app.graph.claim_graph import claim_graph
from app.services.observability import log_claim_result

print("Tracing:", os.getenv("LANGSMITH_TRACING"))
print("Project:", os.getenv("LANGSMITH_PROJECT"))
print("API Key exists:", bool(os.getenv("LANGSMITH_API_KEY")))

app = FastAPI(title="Airline Baggage Claim Validation Agent", version="1.0.0")

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/bookings/{pnr}")
def booking(pnr: str):
    result = get_booking(pnr)
    if not result:
        raise HTTPException(status_code = 404, detail="Booking not found")
    
    return result

@app.get("/baggage/{bag_tag}")
def baggage(bag_tag: str):
    result = get_baggage_events(bag_tag)
    if not result:
        raise HTTPException(status_code = 404, detail="Baggage record not found")
    
    return result

@app.post("/claims")
async def submit_claim(claim: ClaimRequest):

    start_time = time.perf_counter()

    result = await claim_graph.ainvoke(claim.model_dump())

    latency = time.perf_counter() - start_time
    decision = result.get("decision")
    if hasattr(decision, "value"):
        decision = decision.value

    log_claim_result(
        pnr=claim.pnr,
        claim_type=claim.claim_type,
        decision=decision,
        latency=latency
    )
    
    return result